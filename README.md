# The Crowd Is Wrong

*Everyone says to buy when there's blood in the streets. I tested it, along with euphoria, market washouts and the phases of the moon, against up to 75 years of data.*

By [Bella Marco](https://bellamarco.co). Part of a series with [Resonance Lab](https://github.com/isabellarosemarco-collab/resonance-lab) and [Market Anomalies](https://github.com/isabellarosemarco-collab/market-anomalies).

## The idea

The feed pulls everyone the same way. If the crowd is most wrong at its extremes, then buying when everyone is terrified and stepping aside when everyone is calm should beat simply holding the market.

## What happened

Eight tests, all written down before they were run ([round 2's plan](docs/round2_preregistration.md) was committed before round 2 ran). None cleared the bar.

| Test | Each trade vs. random | Luck p | Last 3 years (locked until the end) |
|---|---|---|---|
| **Buy when VIX closes above 30** (SPY, QQQ, IWM) | +1.3% | 0.013 | +7.9% on 9 trades |
| The same rule on 16 funds, including sectors and international | +1.0% | 0.018 | +5.7% on 48 trades |
| Buy only the first day VIX crosses 30 | +0.2% | 0.43 | +5.7% |
| Fear spike: VIX jumps 30%+ in a few days | +0.3% | 0.24 | +0.05% |
| Washout: under 20% of big stocks above their 50-day average | +0.2% | 0.39 | +12.0% on 6 trades |
| S&P 500 down 20%+ (since 1950) | +0.4% | 0.21 | no signals |
| Euphoria: VIX at a one-year low (should lag) | −0.2% | 0.42 | +3.6% (the wrong way) |
| New moon vs. full moon | 0.0% | 0.23 | 0.0% |

*The bar was p < 0.01 for round 1 and p < 0.00625 for round 2, because eight tests were run in total.*

**Buying panic leans positive, but it isn't reliable enough to prove.** There have only been a few dozen separate panics since the 1990s, and a handful of them (2008, 2020, April 2025) carry most of the gains. That's why the signal keeps looking good without ever clearing the bar. The last three years looked great for it, but that's mostly one episode. Adding more funds didn't help, because they all panic on the same days. And buying the first day of a panic did much worse than buying deep into one.

The moon did nothing. Calm, confident markets didn't lag either.

## How the testing works

Same harness as Resonance Lab. Every trade buys at the next morning's open and sells at a later open, after costs. Its return is compared with a random trade in the same fund held for the same time. The luck test slides every trade date by the same random offset 2,000 times, which keeps the fact that markets move together inside the test instead of pretending each fund is an independent bet. The last three years stayed locked until every test was final.

## Run it

```bash
pip install -r requirements.txt
pytest                 # including a no-peeking-at-the-future check for every signal
python run_crowd.py    # round 1
python run_round2.py   # round 2
```

All prices come from Yahoo Finance. Moon phases are computed from the mean lunar cycle, accurate to about half a day.

*Not investment advice. It's an experiment, and nothing in it passed.*
