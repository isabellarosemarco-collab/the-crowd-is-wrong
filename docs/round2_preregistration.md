# Round 2 pre-registration (written 2026-10-26, before any round-2 run)

Round 1 (C1-C5) found no survivor. The closest miss was C2, buying when VIX closes above 30 (+131 bp vs random, p = 0.013 against a 0.01 bar). The likely cause is too little evidence: VIX is above 30 on only a handful of episodes. Round 2 adds evidence. It does not tune the rule.

The Bonferroni family is now 8 tests (C1-C5 + R1-R3), so round-2 tests must clear **p < 0.05/8 = 0.00625**. The holdout (2023-11 →) is still unopened and is used once, at the end, for all eight.

- **R1 · C2 unchanged, wider market.** The same rule (VIX close > 30 → buy at the next open, hold 21 days, one position per fund) traded on 16 funds: SPY, QQQ, IWM, DIA, the nine SPDR sector funds (XLK XLF XLE XLV XLI XLY XLP XLU XLB) and the international funds EFA, EEM and EWJ.
- **R2 · First cross only.** Same funds, but enter only on the first close above 30 after at least 21 days at or below 30. One clean entry per panic episode instead of repeated daily entries.
- **R3 · Crowd panic without VIX, 75 years.** The S&P 500 index (^GSPC) from 1950: when it closes 20%+ below its 252-day high, buy and hold 21 days. Before 1962 Yahoo's index "open" equals the close, so this test uses close-to-close returns (entry at the next day's close).

Same luck test (calendar shifts), consistency, cost and holdout rules as round 1. The lab Sharpe criterion is kept as specified even though it penalizes rare signals.
