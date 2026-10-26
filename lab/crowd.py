"""Measures of the crowd (fear, euphoria, breadth), the moon, and the five pre-registered signals.

A trade is (entry bar, hold): buy at the OPEN of `entry`, sell at the OPEN of `entry + hold`.
Signals known at a bar's close enter on the next bar; calendar signals enter on the day itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

import numpy as np
import pandas as pd

SYNODIC_MONTH = 29.530588853                       # days, new moon to new moon
REF_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)


@dataclass(frozen=True)
class Trade:
    entry: int
    hold: int


@dataclass
class Signal:
    trades: list[Trade]
    twin: list[Trade] = field(default_factory=list)


@dataclass(frozen=True)
class Context:
    """Crowd measures aligned to the traded symbol's dates (NaN where unavailable)."""
    vix: pd.Series
    breadth: pd.Series


@dataclass(frozen=True)
class Hypothesis:
    code: str
    name: str
    fn: Callable[[pd.DataFrame, Context], Signal]
    direction: int = 1        # +1: signal days should beat random; -1: they should lag


def after_close(mask: np.ndarray, hold: int) -> list[Trade]:
    return [Trade(int(t) + 1, hold) for t in np.flatnonzero(mask) if t + 1 < len(mask)]


def on_day(mask: np.ndarray, hold: int) -> list[Trade]:
    return [Trade(int(t), hold) for t in np.flatnonzero(mask)]


def drop_overlaps(trades: list[Trade]) -> list[Trade]:
    out, free_at = [], -1
    for tr in sorted(trades, key=lambda x: x.entry):
        if tr.entry >= free_at:
            out.append(tr)
            free_at = tr.entry + tr.hold
    return out


# ------------------------------------------------------------------ crowd measures

def breadth(stocks: dict[str, pd.DataFrame], dates: pd.DatetimeIndex, window: int = 50,
            min_names: int = 30) -> pd.Series:
    """Share of the stock universe closing above its own 50-day average. NaN if too few names."""
    above, count = pd.Series(0.0, index=dates), pd.Series(0.0, index=dates)
    for df in stocks.values():
        c = df["close"]
        a = (c > c.rolling(window).mean()).astype(float).where(c.rolling(window).count() == window)
        a = a.reindex(dates)
        above += a.fillna(0)
        count += a.notna().astype(float)
    return (above / count).where(count >= min_names)


def moon_age(d: pd.Timestamp) -> float:
    """Days since the last new moon, from the mean synodic month (within about half a day)."""
    t = datetime(d.year, d.month, d.day, 16, tzinfo=timezone.utc)      # ~US market close
    return ((t - REF_NEW_MOON).total_seconds() / 86400) % SYNODIC_MONTH


# ------------------------------------------------------------------ the five signals

def c1_fear_spike(df: pd.DataFrame, ctx: Context) -> Signal:
    v = ctx.vix
    spike = (v / v.rolling(20).mean() - 1 >= 0.30).to_numpy()
    new = spike & ~np.r_[False, spike[:-1]]            # first day of a spike
    return Signal(after_close(new, 10))


def c2_panic_level(df: pd.DataFrame, ctx: Context) -> Signal:
    return Signal(after_close((ctx.vix > 30).to_numpy(), 21))


def c3_washout(df: pd.DataFrame, ctx: Context) -> Signal:
    return Signal(after_close((ctx.breadth < 0.20).to_numpy(), 21))


def c4_euphoria(df: pd.DataFrame, ctx: Context) -> Signal:
    v = ctx.vix
    low = (v <= v.rolling(252).min()).to_numpy() & (v.rolling(252).count() == 252).to_numpy()
    return Signal(after_close(low, 21))


def c5_new_moon(df: pd.DataFrame, ctx: Context) -> Signal:
    age = np.array([moon_age(d) for d in df.index])
    new = (age <= 3) | (age >= SYNODIC_MONTH - 3)
    full = np.abs(age - SYNODIC_MONTH / 2) <= 3
    return Signal(on_day(new, 1), on_day(full, 1))


HYPOTHESES: list[Hypothesis] = [
    Hypothesis("C1", "Fear spike (VIX jumps 30%+)", c1_fear_spike),
    Hypothesis("C2", "Panic level (VIX above 30)", c2_panic_level),
    Hypothesis("C3", "Washout (under 20% of stocks above 50-day avg)", c3_washout),
    Hypothesis("C4", "Euphoria (VIX at 1-year low)", c4_euphoria, direction=-1),
    Hypothesis("C5", "New moon vs full moon", c5_new_moon),
]
