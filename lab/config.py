"""Pre-registered constants for The Crowd Is Wrong. Changing anything here after a run invalidates it."""
from __future__ import annotations

INDEXES = ["SPY", "QQQ", "IWM"]          # what the signals trade
# Breadth universe (same 56 large caps as Resonance Lab), used only to measure the crowd.
STOCKS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "JPM", "V", "MA",
    "UNH", "JNJ", "XOM", "CVX", "PG", "KO", "PEP", "WMT", "HD", "COST",
    "MRK", "ABBV", "LLY", "PFE", "ORCL", "CSCO", "INTC", "ADBE", "CRM", "AMD",
    "QCOM", "TXN", "IBM", "BAC", "WFC", "GS", "MS", "C", "T", "VZ",
    "DIS", "NKE", "MCD", "SBUX", "BA", "CAT", "GE", "MMM", "HON", "AVGO",
    "NFLX", "TSLA", "LOW", "UPS", "AMGN", "GILD",
]
VIX = "^VIX"

START = "1993-01-01"                     # SPY's first full year
BREADTH_START = "1999-01-01"             # the stock cache starts here
DISCOVERY_END = "2023-10-31"             # everything after is the locked holdout
HOLDOUT_START = "2023-11-01"
VOO_INCEPTION = "2010-09-09"


def cost_bp(symbol: str) -> float:
    return 2.0                           # round trip; all traded symbols are ETFs


N_TESTS = 5                              # C1-C5, pre-registered
BAR = 0.05 / N_TESTS                     # Bonferroni: p < 0.01
N_SHIFTS = 2000
MIN_SHIFT = 30
SEED = 20261026

LAB_CAPITAL = 1000.0
SLOTS = 3                                # one slot per index
SLOT_SIZE = LAB_CAPITAL / SLOTS
