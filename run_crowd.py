"""Run The Crowd Is Wrong battery. Writes results/scoreboard_<stage>.csv and report_<stage>.md.

    python run_crowd.py                    # discovery period only (default)
    python run_crowd.py --unlock-holdout   # one-time look at 2023-11 onward
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from lab import config as C
from lab.crowd import HYPOTHESES, Context, drop_overlaps, breadth
from lab.data import load_daily
from lab.portfolio import cagr, sharpe, simulate
from lab.stats import Market, Trades, block_consistency, shift_p, summarize

RESULTS = Path(__file__).resolve().parent / "results"
LOCK = RESULTS / "HOLDOUT_UNLOCKED"


def load() -> tuple[dict[str, pd.DataFrame], pd.Series, pd.Series, pd.Series]:
    idx = {s: load_daily(s, C.START) for s in C.INDEXES}
    dates = idx["SPY"].index
    vix = load_daily(C.VIX, C.START)["close"].reindex(dates)
    stocks = {}
    for s in C.STOCKS:
        try:
            stocks[s] = load_daily(s, C.BREADTH_START)
        except Exception as e:
            print(f"  {s}: skipped ({e})")
    b = breadth(stocks, dates)
    spy = idx["SPY"]["close"]
    voo = load_daily("VOO", C.START)["close"].reindex(dates)
    r = spy.pct_change()
    after = dates >= pd.Timestamp(C.VOO_INCEPTION)
    r[after] = voo.pct_change()[after]
    bench = 1000 * (1 + r.fillna(0)).cumprod()
    return idx, vix, b, bench


def build(idx: dict[str, pd.DataFrame]) -> tuple[Market, np.ndarray]:
    syms = list(idx)
    dates = idx["SPY"].index
    op = np.vstack([idx[s]["open"].reindex(dates).to_numpy() for s in syms])
    cl = np.vstack([idx[s]["close"].reindex(dates).to_numpy() for s in syms])
    cost = np.array([C.cost_bp(s) / 1e4 for s in syms])
    disc_end = int(np.searchsorted(dates, pd.Timestamp(C.DISCOVERY_END), side="right") - 1)
    return Market(dates, syms, op, cost, disc_end), cl


def collect(h, idx, vix, b, mkt) -> tuple[Trades, Trades]:
    out = {"trades": ([], [], []), "twin": ([], [], [])}
    for si, s in enumerate(mkt.symbols):
        df = idx[s]
        sig = h.fn(df, Context(vix.reindex(df.index), b.reindex(df.index)))
        for key, trades in (("trades", sig.trades), ("twin", sig.twin)):
            trades = [t for t in drop_overlaps(trades) if t.entry < len(df)]
            if not trades:
                continue
            pos = mkt.dates.get_indexer(df.index[[t.entry for t in trades]])
            keep = pos >= 0
            out[key][0].extend([si] * int(keep.sum()))
            out[key][1].extend(pos[keep].tolist())
            out[key][2].extend(np.array([t.hold for t in trades])[keep].tolist())
    mk = lambda k: Trades(*(np.asarray(a, dtype=int) for a in out[k]))
    return mk("trades"), mk("twin")


def step_aside(mkt: Market, tr: Trades, end: int) -> pd.Series:
    """Hold SPY, but sit in cash during the signal's windows. Used for the euphoria (avoid) signal."""
    spy = mkt.symbols.index("SPY")
    op = mkt.open[spy, :end + 1]
    r = np.r_[op[1:] / op[:-1] - 1, 0.0]
    exposure = np.ones(len(op))
    for p, h in zip(tr.pos[tr.sym == spy], tr.hold[tr.sym == spy]):
        if p <= end:
            exposure[p:min(p + h, end + 1)] = 0.0
    switches = np.abs(np.diff(np.r_[1.0, exposure]))
    daily = exposure * r - switches * mkt.cost[spy] / 2
    return pd.Series(1000 * np.cumprod(1 + np.nan_to_num(daily)), index=mkt.dates[:end + 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unlock-holdout", action="store_true")
    args = ap.parse_args()
    if args.unlock_holdout and LOCK.exists():
        print(f"Holdout already unlocked on {LOCK.read_text().strip()}. It is used once.")
        return 1
    RESULTS.mkdir(exist_ok=True)

    idx, vix, b, bench = load()
    mkt, close = build(idx)
    rows = []
    for h in HYPOTHESES:
        print(f"  {h.code} {h.name}...", flush=True)
        tr_all, twin_all = collect(h, idx, vix, b, mkt)
        tr = tr_all.subset(tr_all.pos + tr_all.hold <= mkt.disc_end)
        row = {"code": h.code, "hypothesis": h.name,
               "bet": "beats random" if h.direction > 0 else "lags random"}
        if len(tr) < 20:
            rows.append({**row, "trades": len(tr), "status": "TOO FEW TRADES"})
            continue
        s = summarize(mkt, tr, False)
        exc = s.pop("_exc")
        row.update(s)
        row["luck_p"] = round(shift_p(mkt, tr, 0, mkt.disc_end, C.N_SHIFTS, C.MIN_SHIFT, C.SEED,
                                      direction=h.direction), 4)
        row["consistency_pct"] = round(100 * block_consistency(mkt, tr, exc, direction=h.direction), 0)
        twin = twin_all.subset(twin_all.pos + twin_all.hold <= mkt.disc_end)
        if len(twin) >= 20:
            row["twin_excess_bp"] = summarize(mkt, twin, False)["excess_bp"]

        end = mkt.disc_end if not args.unlock_holdout else len(mkt.dates) - 1
        sub = tr_all.subset(tr_all.pos + tr_all.hold <= end)
        if h.direction > 0:
            eq = simulate(mkt.dates[:end + 1], mkt.open[:, :end + 1], close[:, :end + 1],
                          mkt.cost, sub.sym, sub.pos, sub.hold)
        else:
            eq = step_aside(mkt, sub, end)
        row["lab_cagr_pct"] = round(100 * cagr(eq), 2)
        row["lab_sharpe"] = round(sharpe(eq), 2)
        row["voo_cagr_pct"] = round(100 * cagr(bench.iloc[:end + 1]), 2)
        row["voo_sharpe"] = round(sharpe(bench.iloc[:end + 1]), 2)

        passed = [row["luck_p"] < C.BAR, row["consistency_pct"] > 50,
                  row["lab_sharpe"] > row["voo_sharpe"]]
        if h.direction > 0:
            passed.append(row["avg_net_pct"] > 0)
        if args.unlock_holdout:
            ho = tr_all.subset((tr_all.pos > mkt.disc_end) & (tr_all.pos + tr_all.hold < len(mkt.dates)))
            if len(ho) >= 5:
                hs = summarize(mkt, ho, False)
                row["holdout_trades"] = hs["trades"]
                row["holdout_excess_bp"] = hs["excess_bp"]
                passed.append(np.sign(hs["excess_bp"]) == np.sign(row["excess_bp"])
                              and abs(hs["excess_bp"]) >= 0.5 * abs(row["excess_bp"]))
            else:
                row["holdout_trades"] = len(ho)
                passed.append(False)
            row["status"] = "PASS" if all(passed) else "FAIL"
        else:
            row["status"] = "CANDIDATE" if all(passed) else "FAIL"
        rows.append(row)

    board = pd.DataFrame(rows)
    stage = "holdout" if args.unlock_holdout else "discovery"
    board.to_csv(RESULTS / f"scoreboard_{stage}.csv", index=False)
    (RESULTS / f"report_{stage}.md").write_text(report(board, stage))
    if args.unlock_holdout:
        LOCK.write_text(datetime.now().isoformat(timespec="seconds"))
    cols = ["code", "hypothesis", "trades", "trades_per_yr", "avg_net_pct", "excess_bp", "twin_excess_bp",
            "luck_p", "consistency_pct", "lab_cagr_pct", "lab_sharpe", "voo_cagr_pct", "voo_sharpe",
            "holdout_trades", "holdout_excess_bp", "status"]
    print(board[[c for c in cols if c in board]].to_string(index=False))
    return 0


def report(board: pd.DataFrame, stage: str) -> str:
    lines = [f"# The Crowd Is Wrong — {stage} results",
             f"_Generated {datetime.now():%Y-%m-%d %H:%M}. Luck bar: p < {C.BAR:.3f}. "
             f"Discovery ends {C.DISCOVERY_END}._", "",
             "| Signal | Bet | Trades | Avg trade | vs random | Luck p | Consistent | Strategy Sharpe | VOO Sharpe | Result |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in board.iterrows():
        g = lambda k, f="{}": (f.format(r[k]) if k in r and pd.notna(r[k]) else "–")
        lines.append(f"| {r['code']} {r['hypothesis']} | {r['bet']} | {g('trades')} | {g('avg_net_pct', '{:+.2f}%')} "
                     f"| {g('excess_bp', '{:+.1f} bp')} | {g('luck_p')} | {g('consistency_pct', '{:.0f}%')} "
                     f"| {g('lab_sharpe')} | {g('voo_sharpe')} | **{r['status']}** |")
    lines += ["", "*vs random* is how much better (or worse) each trade did than a random trade in the same",
              "index held for the same time (1 bp = 0.01%). *Luck p* is the chance a random calendar would",
              "have looked this good. For the euphoria signal the strategy holds SPY and steps aside to cash",
              "during the signal; for the others it buys only on the signal."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
