# The Crowd Is Wrong — discovery results
_Generated 2026-10-26 10:59. Luck bar: p < 0.010. Discovery ends 2023-10-31._

| Signal | Bet | Trades | Avg trade | vs random | Luck p | Consistent | Strategy Sharpe | VOO Sharpe | Result |
|---|---|---|---|---|---|---|---|---|---|
| C1 Fear spike (VIX jumps 30%+) | beats random | 188 | +0.72% | +31.4 bp | 0.2389 | 71% | 0.18 | 0.58 | **FAIL** |
| C2 Panic level (VIX above 30) | beats random | 166 | +2.17% | +131.0 bp | 0.013 | 86% | 0.31 | 0.58 | **FAIL** |
| C3 Washout (under 20% of stocks above 50-day avg) | beats random | 159 | +1.07% | +20.4 bp | 0.3888 | 50% | 0.16 | 0.58 | **FAIL** |
| C4 Euphoria (VIX at 1-year low) | lags random | 149 | +0.71% | -15.4 bp | 0.4228 | 50% | 0.52 | 0.58 | **FAIL** |
| C5 New moon vs full moon | beats random | 4044 | +0.05% | +0.6 bp | 0.2314 | 56% | 0.26 | 0.58 | **FAIL** |

*vs random* is how much better (or worse) each trade did than a random trade in the same
index held for the same time (1 bp = 0.01%). *Luck p* is the chance a random calendar would
have looked this good. For the euphoria signal the strategy holds SPY and steps aside to cash
during the signal; for the others it buys only on the signal.
