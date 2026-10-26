"""Round 2 (see docs/round2_preregistration.md): more evidence for the panic signal.

    python run_round2.py                    # discovery only
    python run_round2.py --unlock-holdout   # one-time look, together with round 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lab import config as C
from lab.crowd import Context, Hypothesis, Signal, after_close, drop_overlaps
from lab.data import load_daily
from lab.stats import Market, Trades, block_consistency, shift_p, summarize

RESULTS = Path(__file__).resolve().parent / "results"
FUNDS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB",
         "EFA", "EEM", "EWJ"]
N_FAMILY = 8
BAR = 0.05 / N_FAMILY


def r1_panic(df: pd.DataFrame, ctx: Context) -> Signal:
    return Signal(after_close((ctx.vix > 30).to_numpy(), 21))


def r2_first_cross(df: pd.DataFrame, ctx: Context) -> Signal:
    v = ctx.vix
    calm_before = (v.shift(1).rolling(21).max() <= 30).to_numpy()
    return Signal(after_close((v > 30).to_numpy() & calm_before, 21))


def r3_drawdown(df: pd.DataFrame, ctx: Context) -> Signal:
    c = df["close"]
    dd = (c / c.rolling(252).max() - 1).to_numpy()
    return Signal(after_close((dd <= -0.20) & (c.rolling(252).count() == 252).to_numpy(), 21))


def market(frames: dict[str, pd.DataFrame], master: str, price: str = "open") -> Market:
    syms = list(frames)
    dates = frames[master].index
    px = np.vstack([frames[s][price].reindex(dates).to_numpy() for s in syms])
    disc_end = int(np.searchsorted(dates, pd.Timestamp(C.DISCOVERY_END), side="right") - 1)
    return Market(dates, syms, px, np.full(len(syms), 2e-4), disc_end)


def collect(h: Hypothesis, frames, ctxs, mkt: Market) -> Trades:
    S, P, H = [], [], []
    for si, s in enumerate(mkt.symbols):
        df = frames[s]
        tr = [t for t in drop_overlaps(h.fn(df, ctxs[s]).trades) if t.entry < len(df)]
        if not tr:
            continue
        pos = mkt.dates.get_indexer(df.index[[t.entry for t in tr]])
        k = pos >= 0
        S += [si] * int(k.sum()); P += pos[k].tolist(); H += [t.hold for t in np.array(tr)[k]]
    return Trades(np.array(S, dtype=int), np.array(P, dtype=int), np.array(H, dtype=int))


def score(code: str, name: str, mkt: Market, tr_all: Trades, unlock: bool) -> dict:
    tr = tr_all.subset(tr_all.pos + tr_all.hold <= mkt.disc_end)
    s = summarize(mkt, tr, False)
    exc = s.pop("_exc")
    row = {"code": code, "hypothesis": name, **s,
           "episodes": int(len(np.unique(mkt.dates[tr.pos].to_period("M")))),
           "luck_p": round(shift_p(mkt, tr, 0, mkt.disc_end, C.N_SHIFTS, C.MIN_SHIFT, C.SEED), 4),
           "consistency_pct": round(100 * block_consistency(mkt, tr, exc), 0)}
    passed = [row["avg_net_pct"] > 0, row["luck_p"] < BAR, row["consistency_pct"] > 50]
    if unlock:
        ho = tr_all.subset((tr_all.pos > mkt.disc_end) & (tr_all.pos + tr_all.hold < len(mkt.dates)))
        if len(ho):
            hs = summarize(mkt, ho, False)
            row["holdout_trades"], row["holdout_excess_bp"] = hs["trades"], hs["excess_bp"]
            passed.append(np.sign(hs["excess_bp"]) == np.sign(row["excess_bp"])
                          and abs(hs["excess_bp"]) >= 0.5 * abs(row["excess_bp"]))
        else:
            row["holdout_trades"] = 0
            passed.append(False)
    row["status"] = ("PASS" if unlock else "CANDIDATE") if all(passed) else "FAIL"
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unlock-holdout", action="store_true")
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)

    funds = {s: load_daily(s, C.START) for s in FUNDS}
    vix = load_daily(C.VIX, C.START)["close"]
    ctxs = {s: Context(vix.reindex(df.index), pd.Series(np.nan, index=df.index)) for s, df in funds.items()}
    mkt = market(funds, "SPY")
    rows = [score("R1", "Panic (VIX > 30), 16 funds", mkt,
                  collect(Hypothesis("R1", "", r1_panic), funds, ctxs, mkt), args.unlock_holdout),
            score("R2", "Panic, first cross only, 16 funds", mkt,
                  collect(Hypothesis("R2", "", r2_first_cross), funds, ctxs, mkt), args.unlock_holdout)]

    spx = load_daily("^GSPC", "1950-01-01")
    spx_frames = {"^GSPC": spx}
    smkt = market(spx_frames, "^GSPC", price="close")          # close-to-close, see prereg
    sctx = {"^GSPC": Context(pd.Series(np.nan, index=spx.index), pd.Series(np.nan, index=spx.index))}
    rows.append(score("R3", "S&P 500 down 20%+, since 1950", smkt,
                      collect(Hypothesis("R3", "", r3_drawdown), spx_frames, sctx, smkt), args.unlock_holdout))

    board = pd.DataFrame(rows)
    stage = "holdout" if args.unlock_holdout else "discovery"
    board.to_csv(RESULTS / f"round2_{stage}.csv", index=False)
    print(f"bar p < {BAR:.5f}")
    print(board.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
