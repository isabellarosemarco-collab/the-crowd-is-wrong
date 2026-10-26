import numpy as np
import pandas as pd
import pytest

from lab.crowd import (HYPOTHESES, Context, Trade, breadth, c1_fear_spike, c4_euphoria,
                       drop_overlaps, moon_age)


def frame(close, start="2020-01-01"):
    close = np.asarray(close, dtype=float)
    idx = pd.bdate_range(start, periods=len(close))
    return pd.DataFrame({"open": close, "high": close, "low": close, "close": close,
                         "volume": 1e6, "raw_close": close}, index=idx)


def test_moon_age_matches_known_phases():
    assert min(moon_age(pd.Timestamp("2024-04-08")), 29.53 - moon_age(pd.Timestamp("2024-04-08"))) < 1.0
    assert abs(moon_age(pd.Timestamp("2024-04-23")) - 14.77) < 1.0     # full moon


def test_breadth_counts_names_above_average():
    up = frame(np.arange(1, 81))            # rising: above its 50-day average
    down = frame(np.arange(80, 0, -1))      # falling: below it
    b = breadth({"A": up, "B": down}, up.index, window=50, min_names=2)
    assert np.isnan(b.iloc[10]) and b.iloc[-1] == 0.5


def test_fear_spike_fires_once_per_spike():
    df = frame(np.full(40, 100.0))
    v = pd.Series(15.0, index=df.index)
    v.iloc[25:28] = 25.0                    # one 3-day spike
    sig = c1_fear_spike(df, Context(v, pd.Series(np.nan, index=df.index)))
    assert sig.trades == [Trade(26, 10)]


def test_euphoria_needs_a_full_year():
    df = frame(np.full(300, 100.0))
    v = pd.Series(np.linspace(30, 10, 300), index=df.index)   # new lows every day
    entries = [t.entry for t in c4_euphoria(df, Context(v, pd.Series(np.nan, index=df.index))).trades]
    assert min(entries) == 252


def test_drop_overlaps():
    assert drop_overlaps([Trade(0, 3), Trade(1, 3), Trade(3, 1)]) == [Trade(0, 3), Trade(3, 1)]


@pytest.mark.parametrize("h", HYPOTHESES, ids=lambda h: h.code)
def test_no_lookahead(h):
    rng = np.random.default_rng(0)
    df = frame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 900))))
    ctx = Context(pd.Series(20 * np.exp(np.cumsum(rng.normal(0, 0.05, 900))), index=df.index),
                  pd.Series(rng.uniform(0, 1, 900), index=df.index))
    m = 700
    cut = Context(ctx.vix.iloc[:m], ctx.breadth.iloc[:m])
    full = {t.entry for t in h.fn(df, ctx).trades if t.entry < m}
    part = {t.entry for t in h.fn(df.iloc[:m], cut).trades if t.entry < m}
    assert full == part
