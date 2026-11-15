# Final research report: crypto listing announcements

This report is generated. `scripts/20_final_z_report.py` fills every number from the CSV files in `analysis/`, and those come from the `scripts/20_final_*.py` scripts run on `data/`. Edit `scripts/final_report_template.md`, not this file.

**This is research, not investment advice.** No orders were placed and no funds were used. Past listing behaviour does not guarantee future results, and every strategy below can lose money.

## Words used in this report

- **Long**: buying a coin to profit if its price rises.
- **Short**: selling a coin you do not own (here, through a perp) to profit if its price falls. A short loses if the price rises, and the loss has no fixed limit.
- **Perp** (perpetual futures contract): a contract that tracks a coin's price, never expires, and can be shorted. This report uses USDT-margined perps on Binance (USD-M) and Bybit, and Hyperliquid in section F.
- **Funding**: a payment exchanged every few hours between longs and shorts on a perp. A positive rate means longs pay shorts, so the short receives it. A negative rate means the short pays.
- **Stop** (stop-loss): an order that closes a position once the price moves a set amount against it. A +20% stop on a short closes it when the price is 20% above the entry.
- **Median**: the middle result when all results are sorted. Half the trades did better and half did worse. The **mean** is the plain average, which a few very large trades can pull up or down.
- **Win rate**: the share of trades with a positive net result. **p10** and **p90**: the result that 10% of trades fall below, and the one that 10% of trades are above. **Worst**: the single worst trade.
- **Measured** means the number comes straight from the data. **Inferred** means it is a judgment built on measured numbers. Every n below 20 is marked "(n<20)".

All returns are in percent and net of a 0.6% round-trip cost unless the text says gross.

## 1. Verdict

1. Trade, in paper first: the fast long on Upbit KRW listing notices, only if the order reaches Binance within 1 s of the notice (median 9.1% at 1 s, 1.0% at 2 s).
2. Trade, in paper first: the 24 h short after the Upbit KRW trading open, always with a +20% stop (median 5.5%, mean 3.1%, positive in both periods).
3. Do not trade: any long entered a minute or more after an announcement, any long at a trading open, any short without a stop, and shorts on newly listed Binance perps.
4. Bithumb's fast long and stopped short, and the Binance spot fast long, are candidates with reservations: one period only, a weak period, or a small sample.
5. Reasonable maximum size (inferred): about 10k USD per event for the Upbit KRW fast long and 15k USD notional for the Upbit KRW short. That is half of the thinner of the 2026 order-book depth and the measured early flow (section 4D).

## 2. Recommendations, ranked

Each card gives the period tested, the main reason it could fail, and the numbers behind it. v1 is November 2025 to November 2026. v2+v3 is January 2024 to October 2025, plus 11 v2 Binance-spot and Coinbase events dated after October 2025. "Survives" means the median and the mean are both positive in v1 and in v2+v3, with n ≥ 20 in each.

### Supported in both periods

**1. Fast long on Upbit KRW notices (Binance spot, else perp, entry 1 s after the notice, exit after 5 min).**
- What happens (measured): the price on Binance moves a median 15.0% in the first 2 s and 18.8% by 60 s. Half the 60 s move is done after 1.05 s. A buyer at 1 s still catches part of it.
- Why (inferred): Upbit KRW listings bring new Korean demand, and the fastest traders buy the coin wherever it already trades.
- Results: 

| n | Win % | Median | Mean | p10 | p90 | Worst | v1 n | v1 median | v1 mean | v2+v3 n | v2+v3 median | v2+v3 mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 133 | 74.4 | 9.1 | 20.7 | -4.2 | 66.9 | -17.3 | 53 | 5.0 | 9.9 | 80 | 12.2 | 27.9 |

- Typical bad trade: p10 -4.2%. Worst: -17.3%.
- Needs: measured end-to-end latency under 1 s from the notice to a filled order. At 2 s the median is 1.0% overall and -0.6% in v1.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: our own latency is unmeasured on a real listing (section G). The edge is shrinking: the 1 s median is 13.3% in 2025 and 6.3% in 2026.
- Invalidated by: a paper-trading median below 5.0% (the v1 median) over at least 10 listings, or a measured latency above 1 s.

**2. Short after the Upbit KRW trading open (USDT perp on Binance, else Bybit, entry at the close of the minute after the open, 24 h hold, +20% stop).**
- What happens (measured): after the open, the coin tends to fall. A long on Upbit at the open has a median 24 h result of -17.8%. The short catches the same fall on the perp.
- Why (inferred): the announcement pump is already priced in by the open, and early buyers sell into the new Korean liquidity.
- Results, pessimistic stop fill: 

| n | Win % | Median | Mean | p10 | p90 | Worst | v1 n | v1 median | v1 mean | v2+v3 n | v2+v3 median | v2+v3 mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 138 | 62.3 | 5.5 | 3.1 | -21.2 | 21.4 | -33.5 | 59 | 2.9 | 1.8 | 79 | 5.7 | 4.2 |

- Typical bad trade: p10 -21.2%. Worst: -33.5%, because a 1-minute candle can close far above the stop.
- Needs: a USDT perp at the open, a stop placed on entry, and a funding check. The short paid a mean 3.4% in funding over 24 h, and paid funding in 80% of events.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: the result rests on a few big falls. The top 5 events are 37% of the total, and the mean without them is 2.1%. The worst run of losses cost 75 percentage points.
- Invalidated by: a paper-trading median below 2.9% (the v1 median), or funding regularly at the cap.

**3. Fast long on Binance spot listings of coins that already have a Binance perp (perp ticks, entry 1 s after releaseDate, 5 min hold).**
- What happens (measured): the perp moves a median 11.3% in the first 5 s. The first +2% print comes a median 2.3 s after releaseDate.
- Results: 

| n | Win % | Median | Mean | p10 | p90 | Worst | v1 n | v1 median | v2+v3 n | v2+v3 median |
|---|---|---|---|---|---|---|---|---|---|---|
| 66 | 83.3 | 7.5 | 14.5 | -3.7 | 39.4 | -14.7 | 20 | 6.5 | 46 | 7.8 |

- Typical bad trade: p10 -3.7%. Worst: -14.7%.
- Needs: detection of the catalog-48 post within about 1 s. At 3 s the median is 0.5%, and at 5 s -1.0%.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: v1 has exactly 20 events, the minimum for this label. The 2026 perp book is thin: ask depth within 1% has a p25 of 16.5k USD.

### Supported with reservations

**4. Short after the Bithumb trading open (24 h, +20% stop, pessimistic fill).** Results: 

| n | Win % | Median | Mean | p10 | Worst | v1 n | v1 median | v1 mean | v2+v3 n | v2+v3 median |
|---|---|---|---|---|---|---|---|---|---|---|
| 181 | 63.5 | 3.5 | 2.2 | -20.5 | -61.9 | 40 | 0.3 | 0.6 | 141 | 3.8 |

It survives, but v1 is weak (median 0.3%). The top 5 events are 46% of the total. The worst stopped trade returned -61.9%, because the price jumped through the stop inside one minute. Period tested: 2024-01 to 2026-11, pooling v1 and v3. Main reason it could fail: the v1 edge is close to zero.

**5. Fast long on Bithumb notices (official times, entry 1 s after the notice, 5 min hold).** Results: 

| n | Win % | Median | Mean | p10 | p90 | Worst |
|---|---|---|---|---|---|---|
| 129 | 71.3 | 2.2 | 4.3 | -2.3 | 13.4 | -14.0 |

By year: 2024 median 0.3% (n 46), 2025 median 4.3% (n 83). Official Bithumb times exist only for 2024–2025, so this cannot be checked across periods. Treat it as a paper-trade candidate only. Main reason it could fail: no official-time test after October 2025.

**6. Short on the Binance perp after a Binance spot open, for coins that already had a perp (24 h, +20% stop).** Results: 

| Subset | n | Win % | Median | Mean | Worst | v1 n | Label |
|---|---|---|---|---|---|---|---|
| Binance spot with prior perp | 58 | 58.6 | 7.6 | 4.9 | -25.6 | 17 (n<20) | n<20 in one period |
| Binance spot with prior perp [Binance Will List] | 33 | 51.5 | 0.2 | 2.8 | -25.4 | 17 (n<20) | n<20 in one period |
| Binance spot with prior perp [HODLer Airdrops] | 25 | 68.0 | 11.2 | 7.6 | -25.6 | 0 (n<20) | single period |

The HODLer Airdrops subset is stronger but exists only in v2. Main reason it could fail: small v1 sample.

### Watch, do not trade yet

**7. Short on the Binance perp after Coinbase full trading (24 h, no stop).** 

| Strategy | n | Median | Mean | v1 n | v1 median | v1 mean | Label |
|---|---|---|---|---|---|---|---|
| Coinbase | short | full trading +1m on Binance perp | 1440m | stop none | 72 | 3.5 | 1.5 | 21 | 1.5 | -4.0 | no |
| Coinbase | short | full trading +1m on Binance perp | 1440m | stop +20% pessimistic | 72 | 3.4 | 2.6 | 21 | -0.2 | -1.2 | no |

v1 is negative on the mean. The price barely reacts to the announcement itself (Binance perp 60 s move median 0.02%).

**8. Short on an external perp after an OKX spot open (24 h).** 

| n | Median | Mean | v1 n | v2+v3 n | Label |
|---|---|---|---|---|---|
| 22 | 7.8 | 5.6 | 11 (n<20) | 11 (n<20) | n<20 in one period |

The sample is too small in both periods.

### Not recommended



| Strategy | n | Median | Mean | Worst | Label |
|---|---|---|---|---|---|
| Binance perp listing | short | perp open +1m on listed perp | 1440m | stop +20% pessimistic | 164 | -0.1 | -1.9 | -29.7 | single period |
| Bithumb official | short | announcement +1m delayed on perp | until open | 141 | -1.3 | -2.8 | -86.3 | single period |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop none | 138 | 5.6 | 0.2 | -142.9 | no |
| Binance perp listing | short | perp open +1m on listed perp (events_metrics) | 1440m | stop none | 259 | 2.8 | -1.9 | -236.9 | no |
| Upbit KRW | long | announcement +1m delayed | 60m | 174 | -1.4 | 0.6 | -32.0 | no |
| Bybit spot | long | open +1m on listing exchange | 1440m | 267 | -13.3 | -13.7 | -85.1 | no |
| Upbit KRW | long | announcement +1m delayed | 1440m | 174 | -8.9 | -6.2 | -62.7 | negative in both |


- A long one minute late misses most of the Upbit KRW move. The median missed move is 21.4% (measured).
- New tokens fall harder after the open. The Upbit KRW 24 h long has a median of -37.3% (n 28), and Bithumb -28.8% (n 26). This favours the short, but only with a stop.
- A short without a stop has a good median and a very bad tail. On Upbit KRW, 8 of 138 trades lost more than 50%, and the worst returned -142.9%.

## 3. Data

- **Coverage (measured).** The dataset holds 1,494 listing announcements from 2024-01-03 to 2026-11-13:


| Group | v1 | v2 | v3 | Total |
|---|---|---|---|---|
| Binance perp | 93 | 0 | 168 | 261 |
| Binance spot | 30 | 46 | 0 | 76 |
| Bithumb spot | 64 | 0 | 209 | 273 |
| Bybit spot | 29 | 0 | 241 | 270 |
| Coinbase spot | 92 | 142 | 0 | 234 |
| OKX spot | 46 | 0 | 45 | 91 |
| Upbit BTC/USDT only | 28 | 57 | 0 | 85 |
| Upbit KRW | 85 | 119 | 0 | 204 |
| All groups | 467 | 364 | 663 | 1,494 |

- **The three collections.** v1 runs 2025-11-03 to 2026-11-13 and covers every group. v2 adds Upbit from 2024, plus Binance spot and Coinbase announcements from 2024 to today. v3 adds OKX, Bybit and Binance-perp listings, and Bithumb with official times, for 2024-01 to 2025-10. It also adds order-book depth, funding gaps, DEX swaps and the forward pollers. README.md describes the sources.
- **Known gaps.**
  - No Robinhood.
  - No spot order book. `book_snapshots` is USD-M perp depth only.
  - Hyperliquid has mostly 4 h candles before 2026.
  - No Solana swaps, and BSC swaps are partial.
  - Coinbase `ann_ext_` columns are empty by method: no external entry was taken at Coinbase announcements.
  - Delisted coins are under-represented (section E).
  - 563 events still have no funding rows. Where a perp short is priced on such an event, funding counts as zero, and the events are listed in `analysis/a_short_no_funding.csv` (4 Korean events).

## 4. Measurements

### Method

- **Costs:** 0.6% round trip on every trade. Returns are fractions in the data and percentages here.
- **Delayed entry:** the close of the 1-minute candle after the trigger minute, 60 to 120 s after the trigger. This is how `events_metrics` is built. Section 5 shows it reproduces the table exactly.
- **Tick entry at latency L:** the first Binance aggTrade at or after announcement + L, for L in 0, 0.5, 1, 2, 3, 5, 10, 30 and 60 s. The exit is the open of the 1-minute candle 5 or 60 minutes after the entry minute, on the same venue. Each event gets one row, from Binance spot ticks if there are any, else Binance perp.
- **Short:** −r − 0.6% + funding received, where r is the price return over the hold. Funding is summed over (entry, exit]. Only events with a USDT perp on Binance or Bybit at the entry count. A perp that is not listed yet has no candle at the entry minute.
- **Stops** at +10/+20/+50% come in two fills. The exact fill exits at the stop price. The pessimistic fill exits at the close of the first 1-minute candle whose high touches the stop.
- **Period split:** v1 against v2+v3 uses `collection_batch`. Year splits use the UTC calendar year of the announcement (or of the trading open, for the 8 Coinbase events without an announcement time).

### A. Korean listings

**Long at the announcement, delayed (1-minute candles, external venue).**


| Group | Measure | n | Median | Mean | Win % | p10 | p90 | Worst |
|---|---|---|---|---|---|---|---|---|
| Upbit KRW | n5 | 174 | -0.6 | 1.3 | 41.4 | -5.7 | 9.2 | -23.0 |
| Upbit KRW | n60 | 174 | -1.4 | 0.6 | 37.4 | -12.3 | 16.8 | -32.0 |
| Upbit KRW | n1440 | 174 | -8.9 | -6.2 | 23.0 | -32.6 | 14.4 | -62.7 |
| Upbit KRW | n60_hi | 174 | -4.7 | -3.3 | 27.0 | -15.6 | 13.8 | -42.0 |
| Upbit KRW | missed_move | 170 | 21.4 | 35.2 | 95.3 | 2.3 | 80.8 | -2.3 |
| Upbit BTC/USDT only | n5 | 77 | -1.3 | -1.0 | 20.8 | -6.8 | 1.5 | -18.6 |
| Upbit BTC/USDT only | n60 | 77 | -1.1 | -0.3 | 36.4 | -7.6 | 4.6 | -33.8 |
| Upbit BTC/USDT only | n1440 | 77 | -3.2 | 1.6 | 36.4 | -15.1 | 16.0 | -42.0 |
| Upbit BTC/USDT only | n60_hi | 77 | -3.1 | -3.4 | 14.3 | -15.1 | 1.3 | -35.7 |
| Upbit BTC/USDT only | missed_move | 75 | 3.7 | 8.9 | 90.7 | 0.2 | 20.2 | -12.3 |
| Bithumb official | n5 | 180 | -0.7 | -0.6 | 31.1 | -3.8 | 2.4 | -14.6 |
| Bithumb official | n60 | 180 | -0.8 | 0.7 | 45.0 | -6.1 | 7.8 | -27.9 |
| Bithumb official | n1440 | 180 | -5.0 | -1.5 | 29.4 | -18.2 | 19.9 | -60.0 |
| Bithumb official | n60_hi | 180 | -2.6 | -1.3 | 29.4 | -7.9 | 6.5 | -29.4 |
| Bithumb official | missed_move | 179 | 5.9 | 9.6 | 97.8 | 1.6 | 21.9 | -1.3 |
| Bithumb third-party | n5 | 60 | -0.6 | -0.9 | 33.3 | -5.0 | 4.0 | -11.3 |
| Bithumb third-party | n60 | 60 | -1.8 | -0.7 | 35.0 | -10.6 | 7.6 | -21.9 |
| Bithumb third-party | n1440 | 59 | -6.7 | -3.4 | 30.5 | -28.9 | 24.8 | -43.8 |
| Bithumb third-party | n60_hi | 60 | -3.0 | -2.9 | 28.3 | -13.1 | 5.0 | -25.7 |
| Bithumb third-party | missed_move | 58 | 6.1 | 8.7 | 87.9 | 0.0 | 21.1 | -3.8 |

`n60_hi` buys at the high of the entry candle. `missed_move` is the gross move from the last candle before the announcement to the delayed entry. All values are measured.

**Long at the announcement by latency (ticks, 5 min hold).**


| Group | Latency s | n | Median | Mean | Win % | p10 | p90 | Worst |
|---|---|---|---|---|---|---|---|---|
| Upbit KRW | 0.0 | 133 | 18.7 | 30.4 | 94.0 | 2.7 | 70.4 | -7.1 |
| Upbit KRW | 0.5 | 133 | 16.1 | 28.8 | 89.5 | -0.3 | 70.3 | -17.3 |
| Upbit KRW | 1.0 | 133 | 9.1 | 20.7 | 74.4 | -4.2 | 66.9 | -17.3 |
| Upbit KRW | 2.0 | 133 | 1.0 | 9.6 | 54.1 | -7.9 | 26.1 | -17.4 |
| Upbit KRW | 3.0 | 133 | -0.6 | 5.8 | 48.9 | -9.0 | 24.9 | -20.1 |
| Upbit KRW | 5.0 | 133 | -0.6 | 4.1 | 44.4 | -9.4 | 20.3 | -18.4 |
| Upbit KRW | 10.0 | 133 | -0.2 | 3.8 | 48.1 | -9.7 | 19.9 | -20.5 |
| Upbit KRW | 30.0 | 133 | -0.8 | 1.0 | 35.3 | -7.8 | 9.7 | -15.1 |
| Upbit KRW | 60.0 | 133 | -0.7 | -0.4 | 37.6 | -6.2 | 5.0 | -15.5 |
| Upbit BTC/USDT only | 0.0 | 60 | 1.5 | 4.2 | 73.3 | -1.1 | 15.6 | -12.5 |
| Upbit BTC/USDT only | 0.5 | 60 | 1.5 | 4.1 | 70.0 | -1.3 | 15.5 | -13.6 |
| Upbit BTC/USDT only | 1.0 | 60 | 0.3 | 1.9 | 53.3 | -3.2 | 13.0 | -14.8 |
| Upbit BTC/USDT only | 2.0 | 60 | -2.1 | -1.7 | 25.0 | -7.3 | 2.9 | -19.1 |
| Upbit BTC/USDT only | 3.0 | 60 | -2.3 | -3.5 | 18.3 | -9.4 | 0.7 | -22.2 |
| Upbit BTC/USDT only | 5.0 | 60 | -2.8 | -4.4 | 6.7 | -12.1 | -0.3 | -19.0 |
| Upbit BTC/USDT only | 10.0 | 60 | -1.7 | -3.3 | 16.7 | -9.4 | 1.3 | -19.2 |
| Upbit BTC/USDT only | 30.0 | 60 | -2.1 | -3.0 | 15.0 | -8.6 | 1.6 | -21.2 |
| Upbit BTC/USDT only | 60.0 | 60 | -1.6 | -1.0 | 13.3 | -7.2 | 0.9 | -14.5 |
| Bithumb third-party | 0.0 | 37 | 0.7 | 1.2 | 54.1 | -3.1 | 4.9 | -4.4 |
| Bithumb third-party | 0.5 | 37 | -0.6 | -0.4 | 43.2 | -5.1 | 4.1 | -9.4 |
| Bithumb third-party | 1.0 | 37 | -0.9 | -1.0 | 43.2 | -5.4 | 3.3 | -8.3 |
| Bithumb third-party | 2.0 | 37 | -0.6 | -0.9 | 40.5 | -5.9 | 3.0 | -11.3 |
| Bithumb third-party | 3.0 | 37 | 0.1 | -0.8 | 51.4 | -5.3 | 3.4 | -19.3 |
| Bithumb third-party | 5.0 | 37 | -0.6 | -0.6 | 45.9 | -5.4 | 3.3 | -7.1 |
| Bithumb third-party | 10.0 | 37 | -0.4 | -0.6 | 45.9 | -5.0 | 3.1 | -9.2 |
| Bithumb third-party | 30.0 | 37 | -0.4 | -1.1 | 40.5 | -5.3 | 1.7 | -8.2 |
| Bithumb third-party | 60.0 | 37 | -0.6 | -0.3 | 40.5 | -4.8 | 4.0 | -6.7 |
| Bithumb official | 0.0 | 129 | 5.6 | 6.9 | 94.6 | 0.8 | 17.8 | -2.3 |
| Bithumb official | 0.5 | 129 | 4.5 | 6.1 | 84.5 | -0.6 | 16.0 | -4.2 |
| Bithumb official | 1.0 | 129 | 2.2 | 4.3 | 71.3 | -2.3 | 13.4 | -14.0 |
| Bithumb official | 2.0 | 129 | 0.6 | 2.4 | 54.3 | -4.4 | 9.9 | -16.1 |
| Bithumb official | 3.0 | 129 | -0.7 | 0.3 | 39.5 | -5.0 | 9.3 | -29.7 |
| Bithumb official | 5.0 | 129 | -1.5 | -1.0 | 28.7 | -6.5 | 6.4 | -25.4 |
| Bithumb official | 10.0 | 129 | -0.8 | -0.2 | 36.4 | -4.6 | 5.5 | -20.7 |
| Bithumb official | 30.0 | 129 | -0.6 | -0.4 | 38.0 | -3.1 | 2.7 | -17.8 |
| Bithumb official | 60.0 | 129 | -0.6 | -0.4 | 34.9 | -3.0 | 2.0 | -6.4 |


By period and year at 1 s:


| Group | Split | n | Median | Mean | Win % |
|---|---|---|---|---|---|
| Upbit KRW | v1 | 53 | 5.0 | 9.9 | 67.9 |
| Upbit KRW | v2+v3 | 80 | 12.2 | 27.9 | 78.8 |
| Upbit KRW | 2024.0 | 24 | 8.3 | 12.5 | 75.0 |
| Upbit KRW | 2025.0 | 62 | 13.3 | 32.4 | 79.0 |
| Upbit KRW | 2026.0 | 47 | 6.3 | 9.6 | 68.1 |
| Upbit KRW | no_outlier | 130 | 9.1 | 20.6 | 74.6 |
| Upbit BTC/USDT only | v1 | 22 | -0.6 | -1.0 | 45.5 |
| Upbit BTC/USDT only | v2+v3 | 38 | 1.0 | 3.6 | 57.9 |
| Upbit BTC/USDT only | 2024.0 | 18 (n<20) | -0.1 | 2.3 | 50.0 |
| Upbit BTC/USDT only | 2025.0 | 21 | 4.6 | 4.7 | 66.7 |
| Upbit BTC/USDT only | 2026.0 | 21 | -0.6 | -1.3 | 42.9 |
| Upbit BTC/USDT only | no_outlier | 56 | 0.7 | 2.1 | 55.4 |
| Bithumb official | v2+v3 | 129 | 2.2 | 4.3 | 71.3 |
| Bithumb official | 2024.0 | 46 | 0.3 | 1.5 | 52.2 |
| Bithumb official | 2025.0 | 83 | 4.3 | 5.8 | 81.9 |
| Bithumb official | no_outlier | 126 | 2.1 | 4.3 | 71.4 |


The Upbit KRW 2 s result by year: 2024 6.1%, 2025 0.3%, 2026 0.0% (measured). Bithumb third-party times are v1 only and are not a fair test of speed (see below).

**Speed of the move (ticks).** Price relative to the last trade before the announcement, in percent (medians). The share columns use events whose 60 s move is above 2%.


| Group | Split | n | 1 s | 2 s | 5 s | 30 s | 60 s | Share at 1 s | Share at 2 s | Half move s | First +2% s | Drift before |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bithumb official | all | 125 | 0.0 | 3.5 | 6.5 | 5.1 | 5.6 | 0.2 | 81.1 | 1.4 | 1.2 | 0.0 |
| Bithumb official | v2+v3 | 125 | 0.0 | 3.5 | 6.5 | 5.1 | 5.6 | 0.2 | 81.1 | 1.4 | 1.2 | 0.0 |
| Bithumb third-party | all | 37 | 1.6 | 1.4 | 1.2 | 2.4 | 1.1 | 66.8 | 39.1 | 0.3 | 0.2 | 5.4 |
| Bithumb third-party | v1 | 37 | 1.6 | 1.4 | 1.2 | 2.4 | 1.1 | 66.8 | 39.1 | 0.3 | 0.2 | 5.4 |
| Upbit BTC/USDT only | all | 56 | 0.0 | 3.9 | 5.5 | 4.1 | 3.9 | 0.0 | 102.7 | 1.3 | 1.2 | 0.0 |
| Upbit BTC/USDT only | v1 | 19 (n<20) | 0.1 | 3.6 | 3.5 | 2.3 | 2.5 | 28.5 | 113.7 | 1.1 | 1.1 | 0.0 |
| Upbit BTC/USDT only | v2+v3 | 37 | 0.0 | 5.7 | 8.0 | 6.9 | 5.6 | 0.0 | 98.9 | 1.3 | 1.2 | 0.0 |
| Upbit KRW | all | 132 | 2.5 | 15.0 | 19.6 | 18.6 | 18.8 | 21.3 | 83.0 | 1.0 | 0.9 | 0.0 |
| Upbit KRW | v1 | 52 | 8.7 | 15.0 | 17.7 | 15.3 | 16.8 | 55.5 | 98.9 | 0.9 | 0.8 | 0.0 |
| Upbit KRW | v2+v3 | 80 | 1.2 | 15.1 | 22.4 | 24.1 | 21.6 | 5.0 | 77.0 | 1.3 | 1.0 | 0.0 |

- Upbit KRW against Bithumb on official times (measured): the median 60 s move is 18.8% on Upbit KRW and 5.6% on Bithumb. Upbit's first +2% print comes 0.94 s after the notice time, and Bithumb's 1.18 s after.
- Bithumb's v1 third-party times arrive after the move (measured). Prices already drifted a median 5.4% in the 60 s before those timestamps, against 0.00% before the official times. Official against third-party times: 54 of 64 v1 Bithumb events matched to an archived official notice; third-party minus official: median 1.35 s, p10 0.96 s, p90 1.85 s.

**Long at the trading open (`start_lst_` on the listing exchange, `start_ext_` on an external venue).**


| Group | Measure | Subset | n | Median | Mean | Win % | p10 | Worst |
|---|---|---|---|---|---|---|---|---|
| Upbit KRW | start_lst_n60 | all | 190 | -7.2 | -7.5 | 17.9 | -24.1 | -67.8 |
| Upbit KRW | start_lst_n60 | new_token | 29 | -13.0 | -11.7 | 13.8 | -48.3 | -67.8 |
| Upbit KRW | start_lst_n1440 | all | 189 | -17.8 | -17.8 | 12.7 | -42.5 | -86.2 |
| Upbit KRW | start_lst_n1440 | new_token | 28 | -37.3 | -36.5 | 3.6 | -64.7 | -86.2 |
| Upbit KRW | start_ext_n60 | all | 181 | -3.8 | -4.4 | 24.3 | -16.4 | -51.8 |
| Upbit KRW | start_ext_n60 | new_token | 21 | -12.3 | -10.9 | 14.3 | -33.3 | -51.8 |
| Upbit KRW | start_ext_n1440 | all | 181 | -12.3 | -11.2 | 16.0 | -32.8 | -81.6 |
| Upbit KRW | start_ext_n1440 | new_token | 21 | -26.1 | -27.0 | 0.0 | -44.4 | -81.6 |
| Upbit BTC/USDT only | start_lst_n60 | all | 49 | -3.8 | 16.0 | 18.4 | -39.5 | -100.6 |
| Upbit BTC/USDT only | start_lst_n60 | new_token | 2 (n<20) | -2.8 | -2.8 | 50.0 | -10.0 | -11.8 |
| Upbit BTC/USDT only | start_lst_n1440 | all | 49 | -8.7 | 106.3 | 26.5 | -44.8 | -100.6 |
| Upbit BTC/USDT only | start_lst_n1440 | new_token | 2 (n<20) | -18.7 | -18.7 | 0.0 | -26.6 | -28.6 |
| Upbit BTC/USDT only | start_ext_n60 | all | 70 | -1.5 | -1.7 | 22.9 | -6.1 | -24.0 |
| Upbit BTC/USDT only | start_ext_n60 | new_token | 1 (n<20) | -4.8 | -4.8 | 0.0 | -4.8 | -4.8 |
| Upbit BTC/USDT only | start_ext_n1440 | all | 70 | -3.7 | -0.2 | 31.4 | -13.1 | -45.1 |
| Upbit BTC/USDT only | start_ext_n1440 | new_token | 1 (n<20) | -22.6 | -22.6 | 0.0 | -22.6 | -22.6 |
| Bithumb | start_lst_n60 | all | 249 | -3.1 | -4.3 | 20.1 | -14.7 | -93.2 |
| Bithumb | start_lst_n60 | new_token | 26 | -7.7 | -12.3 | 30.8 | -58.6 | -93.2 |
| Bithumb | start_lst_n1440 | all | 248 | -8.9 | -9.8 | 20.6 | -32.2 | -95.1 |
| Bithumb | start_lst_n1440 | new_token | 26 | -28.8 | -35.0 | 7.7 | -78.7 | -95.1 |
| Bithumb | start_ext_n60 | all | 247 | -2.5 | -2.9 | 22.7 | -10.4 | -51.8 |
| Bithumb | start_ext_n60 | new_token | 24 | -4.8 | -6.3 | 25.0 | -19.2 | -51.8 |
| Bithumb | start_ext_n1440 | all | 246 | -7.1 | -5.9 | 23.6 | -26.1 | -81.6 |
| Bithumb | start_ext_n1440 | new_token | 24 | -23.4 | -18.6 | 12.5 | -43.1 | -81.6 |


**Bithumb's window between the announcement and the open, on the perp (official times).** The median lag is 254 minutes. The long and short run from the delayed entry after the announcement to the close of the minute before the open. Peak and trough are the highest high and lowest low inside the window, gross. The last hour is a long from about 60 minutes before the open to the open.


| Measure | Split | n | Median | Mean | Win % | p10 | p90 | Worst |
|---|---|---|---|---|---|---|---|---|
| long | all | 141 | -0.3 | 1.2 | 48.2 | -7.9 | 7.9 | -32.3 |
| long | 2024.0 | 54 | -0.6 | -0.3 | 44.4 | -6.1 | 4.6 | -13.4 |
| long | 2025.0 | 87 | 0.1 | 2.1 | 50.6 | -8.9 | 13.4 | -32.3 |
| short | all | 141 | -1.3 | -2.8 | 41.1 | -9.8 | 6.5 | -86.3 |
| short | 2024.0 | 54 | -0.6 | -1.0 | 42.6 | -5.8 | 4.5 | -23.1 |
| short | 2025.0 | 87 | -1.5 | -3.9 | 40.2 | -16.2 | 7.5 | -86.3 |
| peak | all | 141 | 5.5 | 9.6 | 98.6 | 0.6 | 19.0 | 0.0 |
| peak | 2024.0 | 54 | 5.3 | 7.2 | 96.3 | 0.5 | 13.4 | 0.0 |
| peak | 2025.0 | 87 | 5.9 | 11.2 | 100.0 | 1.0 | 27.6 | 0.0 |
| trough | all | 141 | -3.8 | -5.5 | 0.0 | -11.7 | -0.6 | -36.2 |
| trough | 2024.0 | 54 | -3.4 | -4.6 | 0.0 | -9.3 | -0.8 | -36.2 |
| trough | 2025.0 | 87 | -4.2 | -6.0 | 0.0 | -13.0 | -0.4 | -33.0 |
| last_hour_long | all | 141 | -0.8 | -0.9 | 32.6 | -4.8 | 3.2 | -25.0 |
| last_hour_long | 2024.0 | 54 | -0.6 | -1.4 | 27.8 | -4.3 | 1.3 | -20.6 |
| last_hour_long | 2025.0 | 87 | -1.0 | -0.6 | 35.6 | -5.2 | 3.6 | -25.0 |

Neither side of the window pays after costs (measured).

**Shorts after the open (perp, funding included).**


| Group | Hold min | Stop | Fill | n | Median | Mean | Win % | p10 | Worst |
|---|---|---|---|---|---|---|---|---|---|
| Upbit KRW | 60.0 | none | none | 138 | 0.9 | 0.5 | 58.0 | -8.9 | -62.2 |
| Upbit KRW | 60.0 | +20% | exact | 138 | 0.9 | 1.0 | 58.0 | -8.9 | -20.6 |
| Upbit KRW | 60.0 | +20% | pessimistic | 138 | 0.9 | 0.9 | 58.0 | -8.9 | -24.8 |
| Upbit KRW | 240.0 | none | none | 138 | 2.2 | 0.6 | 64.5 | -12.9 | -55.4 |
| Upbit KRW | 240.0 | +20% | exact | 138 | 2.2 | 1.3 | 64.5 | -12.9 | -27.5 |
| Upbit KRW | 240.0 | +20% | pessimistic | 138 | 2.2 | 1.3 | 64.5 | -12.9 | -26.2 |
| Upbit KRW | 1440.0 | none | none | 138 | 5.6 | 0.2 | 64.5 | -25.3 | -142.9 |
| Upbit KRW | 1440.0 | +20% | exact | 138 | 5.5 | 3.1 | 62.3 | -21.2 | -34.1 |
| Upbit KRW | 1440.0 | +20% | pessimistic | 138 | 5.5 | 3.1 | 62.3 | -21.2 | -33.5 |
| Bithumb | 60.0 | none | none | 182 | 0.7 | 0.8 | 61.0 | -4.5 | -54.2 |
| Bithumb | 60.0 | +20% | exact | 182 | 0.7 | 1.0 | 61.0 | -4.5 | -20.6 |
| Bithumb | 60.0 | +20% | pessimistic | 182 | 0.7 | 0.7 | 61.0 | -4.5 | -61.9 |
| Bithumb | 240.0 | none | none | 182 | 1.7 | 0.9 | 63.2 | -7.7 | -59.6 |
| Bithumb | 240.0 | +20% | exact | 182 | 1.5 | 1.1 | 62.1 | -9.3 | -24.0 |
| Bithumb | 240.0 | +20% | pessimistic | 182 | 1.5 | 0.8 | 62.1 | -9.3 | -61.9 |
| Bithumb | 1440.0 | none | none | 181 | 3.8 | 0.5 | 65.2 | -12.8 | -142.9 |
| Bithumb | 1440.0 | +20% | exact | 181 | 3.5 | 2.4 | 63.5 | -20.6 | -24.0 |
| Bithumb | 1440.0 | +20% | pessimistic | 181 | 3.5 | 2.2 | 63.5 | -20.5 | -61.9 |


By period and year, 24 h with a +20% pessimistic stop:


| Group | Split | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|
| Upbit KRW | v1 | 59 | 2.9 | 1.8 | 55.9 | -26.2 |
| Upbit KRW | v2+v3 | 79 | 5.7 | 4.2 | 67.1 | -33.5 |
| Upbit KRW | 2024.0 | 23 | 5.6 | 6.1 | 82.6 | -24.8 |
| Upbit KRW | 2025.0 | 62 | 7.6 | 3.7 | 61.3 | -33.5 |
| Upbit KRW | 2026.0 | 53 | 1.9 | 1.2 | 54.7 | -26.2 |
| Upbit KRW | no_outlier | 135 | 5.6 | 3.7 | 63.7 | -33.5 |
| Bithumb | v1 | 40 | 0.3 | 0.6 | 52.5 | -61.9 |
| Bithumb | v2+v3 | 141 | 3.8 | 2.6 | 66.7 | -32.5 |
| Bithumb | 2024.0 | 54 | 2.0 | 1.1 | 59.3 | -24.0 |
| Bithumb | 2025.0 | 87 | 4.1 | 3.5 | 71.3 | -32.5 |
| Bithumb | 2026.0 | 40 | 0.3 | 0.6 | 52.5 | -61.9 |
| Bithumb | no_outlier | 177 | 3.8 | 2.6 | 64.4 | -61.9 |


Funding and stop touches over the hold (no stop):


| Group | Hold min | n | Funding paid mean | Funding paid median | % short pays | % touch +10% | % touch +20% | % touch +50% | Losses beyond -50% |
|---|---|---|---|---|---|---|---|---|---|
| Bithumb | 60.0 | 182 | 0.1 | 0.0 | 18.1 | 7.1 | 2.7 | 1.1 | 1.0 |
| Bithumb | 240.0 | 182 | 0.4 | 0.0 | 57.1 | 16.5 | 6.6 | 2.2 | 1.0 |
| Bithumb | 1440.0 | 181 | 1.2 | 0.1 | 59.7 | 28.2 | 16.0 | 6.1 | 7.0 |
| Upbit BTC/USDT only | 60.0 | 57 | 0.1 | 0.0 | 10.5 | 7.0 | 3.5 | 0.0 | 0.0 |
| Upbit BTC/USDT only | 240.0 | 57 | 0.2 | 0.0 | 35.1 | 15.8 | 10.5 | 1.8 | 1.0 |
| Upbit BTC/USDT only | 1440.0 | 56 | 0.5 | 0.0 | 41.1 | 26.8 | 14.3 | 1.8 | 1.0 |
| Upbit KRW | 60.0 | 138 | 0.4 | 0.0 | 28.3 | 17.4 | 3.6 | 1.4 | 2.0 |
| Upbit KRW | 240.0 | 138 | 1.2 | 0.6 | 71.7 | 23.9 | 8.7 | 1.4 | 1.0 |
| Upbit KRW | 1440.0 | 138 | 3.4 | 1.3 | 79.7 | 34.1 | 18.8 | 5.8 | 8.0 |


Entry-time grid, 24 h short (an entry before the open must still be after the announcement):


| Group | Entry | Stop | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|---|
| Upbit KRW | announcement +0m | none | 149 | 3.4 | -2.1 | 59.7 | -168.1 |
| Upbit KRW | announcement +0m | +20% | 149 | 0.2 | -0.9 | 50.3 | -34.5 |
| Upbit KRW | announcement +15m | none | 149 | 4.6 | -1.1 | 61.1 | -144.5 |
| Upbit KRW | announcement +15m | +20% | 149 | 3.1 | 0.8 | 53.7 | -34.1 |
| Upbit KRW | announcement +60m | none | 149 | 4.6 | -1.2 | 61.1 | -144.7 |
| Upbit KRW | announcement +60m | +20% | 149 | 4.2 | 1.2 | 58.4 | -33.3 |
| Upbit KRW | open -60m | none | 106 | 3.5 | -2.8 | 59.4 | -139.6 |
| Upbit KRW | open -60m | +20% | 106 | 1.0 | -0.1 | 52.8 | -35.6 |
| Upbit KRW | open -15m | none | 137 | 5.4 | 0.1 | 63.5 | -132.6 |
| Upbit KRW | open -15m | +20% | 137 | 5.0 | 2.2 | 59.1 | -35.3 |
| Upbit KRW | open +0m | none | 138 | 5.6 | 0.2 | 64.5 | -142.9 |
| Upbit KRW | open +0m | +20% | 138 | 5.5 | 3.1 | 62.3 | -33.5 |
| Upbit KRW | open +15m | none | 138 | 4.5 | -0.1 | 62.3 | -147.2 |
| Upbit KRW | open +15m | +20% | 138 | 4.5 | 2.8 | 62.3 | -30.0 |
| Upbit KRW | open +60m | none | 138 | 4.1 | -0.9 | 63.0 | -134.4 |
| Upbit KRW | open +60m | +20% | 138 | 3.5 | 0.8 | 60.1 | -28.5 |
| Upbit KRW | open +240m | none | 138 | 3.4 | -0.3 | 60.1 | -116.6 |
| Upbit KRW | open +240m | +20% | 138 | 2.1 | 0.1 | 58.0 | -29.9 |
| Bithumb | announcement +0m | none | 197 | 3.1 | -1.1 | 61.9 | -383.3 |
| Bithumb | announcement +0m | +20% | 197 | 2.3 | 0.5 | 57.4 | -88.8 |
| Bithumb | announcement +15m | none | 197 | 2.6 | -1.1 | 59.9 | -368.0 |
| Bithumb | announcement +15m | +20% | 197 | 1.7 | -0.4 | 53.8 | -86.4 |
| Bithumb | announcement +60m | none | 197 | 2.7 | -0.6 | 57.9 | -340.7 |
| Bithumb | announcement +60m | +20% | 197 | 1.9 | 0.4 | 54.8 | -77.5 |
| Bithumb | open -60m | none | 181 | 3.1 | 0.3 | 61.9 | -139.6 |
| Bithumb | open -60m | +20% | 181 | 3.0 | 2.0 | 60.2 | -63.4 |
| Bithumb | open -15m | none | 181 | 3.9 | 0.6 | 64.6 | -132.6 |
| Bithumb | open -15m | +20% | 181 | 3.6 | 2.1 | 63.5 | -63.7 |
| Bithumb | open +0m | none | 181 | 3.8 | 0.5 | 65.2 | -142.9 |
| Bithumb | open +0m | +20% | 181 | 3.5 | 2.2 | 63.5 | -61.9 |
| Bithumb | open +15m | none | 181 | 3.0 | 0.0 | 61.9 | -147.2 |
| Bithumb | open +15m | +20% | 181 | 2.9 | 1.8 | 60.8 | -35.4 |
| Bithumb | open +60m | none | 181 | 2.6 | -0.5 | 60.8 | -134.4 |
| Bithumb | open +60m | +20% | 181 | 2.2 | 0.6 | 59.7 | -40.0 |
| Bithumb | open +240m | none | 181 | 2.2 | 0.1 | 61.9 | -116.6 |
| Bithumb | open +240m | +20% | 181 | 2.0 | 0.7 | 60.8 | -25.2 |

On Upbit KRW, entries from 15 minutes before the open to the open are best. Later entries and entries at the announcement are worse (measured).

**Perp limits (`perp_limits_snapshots`, a snapshot of today, not history).**


| Group | Venue | Date | Symbols listed now | Max leverage median | Position limit USD median | Position limit USD p10 | Funding cap % per interval | Funding interval h |
|---|---|---|---|---|---|---|---|---|
| Bithumb | binance_perp | 2026-11-13 | 202 | n/a | n/a | n/a | 2 | 4 |
| Bithumb | bybit_perp | 2026-11-13 | 192 | 25 | 2500000 | 2000000 | 2 | 4 |
| Upbit BTC/USDT only | binance_perp | 2026-11-13 | 64 | n/a | n/a | n/a | 2 | 4 |
| Upbit BTC/USDT only | bybit_perp | 2026-11-13 | 61 | 25 | 2500000 | 1250000 | 2 | 4 |
| Upbit KRW | binance_perp | 2026-11-13 | 166 | n/a | n/a | n/a | 2 | 4 |
| Upbit KRW | bybit_perp | 2026-11-13 | 164 | 25 | 2500000 | 2500000 | 2 | 4 |

Binance max leverage is missing because the endpoint is signed. Bybit's limits (inferred) are far above the sizes in section 4D, so the order book, not the exchange limit, is what binds.

**Robustness.**


| Strategy | Split by | Value | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|---|
| Upbit KRW tick long 1s 5m | new_token | not new | 133 | 9.1 | 20.7 | 74.4 | -17.3 |
| Upbit KRW tick long 1s 5m | ann_hour_kst | 09-15 | 95 | 7.7 | 14.8 | 70.5 | -17.3 |
| Upbit KRW tick long 1s 5m | ann_hour_kst | 16-23 | 38 | 14.9 | 35.7 | 84.2 | -11.1 |
| Upbit KRW tick long 1s 5m | relisting | first listing | 110 | 8.0 | 17.9 | 71.8 | -17.3 |
| Upbit KRW tick long 1s 5m | relisting | relisting | 23 | 13.4 | 34.3 | 87.0 | -4.5 |
| Upbit KRW tick long 1s 5m | year | 2024.0 | 24 | 8.3 | 12.5 | 75.0 | -17.3 |
| Upbit KRW tick long 1s 5m | year | 2025.0 | 62 | 13.3 | 32.4 | 79.0 | -10.0 |
| Upbit KRW tick long 1s 5m | year | 2026.0 | 47 | 6.3 | 9.6 | 68.1 | -11.1 |
| Upbit KRW tick long 1s 5m | venue | binance_perp | 44 | 6.8 | 11.6 | 70.5 | -10.0 |
| Upbit KRW tick long 1s 5m | venue | binance_spot | 89 | 11.5 | 25.3 | 76.4 | -17.3 |
| Bithumb official tick long 1s 5m | new_token | not new | 129 | 2.2 | 4.3 | 71.3 | -14.0 |
| Bithumb official tick long 1s 5m | ann_hour_kst | 09-15 | 109 | 2.0 | 4.4 | 67.9 | -14.0 |
| Bithumb official tick long 1s 5m | ann_hour_kst | 16-23 | 20 | 2.3 | 3.6 | 90.0 | -5.4 |
| Bithumb official tick long 1s 5m | relisting | first listing | 128 | 2.2 | 4.3 | 71.1 | -14.0 |
| Bithumb official tick long 1s 5m | relisting | relisting | 1 (n<20) | 0.9 | 0.9 | 100.0 | 0.9 |
| Bithumb official tick long 1s 5m | year | 2024.0 | 46 | 0.3 | 1.5 | 52.2 | -5.1 |
| Bithumb official tick long 1s 5m | year | 2025.0 | 83 | 4.3 | 5.8 | 81.9 | -14.0 |
| Bithumb official tick long 1s 5m | venue | binance_perp | 37 | 4.3 | 5.8 | 78.4 | -7.0 |
| Bithumb official tick long 1s 5m | venue | binance_spot | 92 | 1.9 | 3.7 | 68.5 | -14.0 |
| Upbit BTC/USDT only tick long 1s 5m | new_token | not new | 60 | 0.3 | 1.9 | 53.3 | -14.8 |
| Upbit BTC/USDT only tick long 1s 5m | ann_hour_kst | 09-15 | 46 | 0.3 | 1.8 | 52.2 | -14.8 |
| Upbit BTC/USDT only tick long 1s 5m | ann_hour_kst | 16-23 | 14 (n<20) | 0.9 | 2.2 | 57.1 | -13.6 |
| Upbit BTC/USDT only tick long 1s 5m | relisting | first listing | 60 | 0.3 | 1.9 | 53.3 | -14.8 |
| Upbit BTC/USDT only tick long 1s 5m | year | 2024.0 | 18 (n<20) | -0.1 | 2.3 | 50.0 | -1.8 |
| Upbit BTC/USDT only tick long 1s 5m | year | 2025.0 | 21 | 4.6 | 4.7 | 66.7 | -13.6 |
| Upbit BTC/USDT only tick long 1s 5m | year | 2026.0 | 21 | -0.6 | -1.3 | 42.9 | -14.8 |
| Upbit BTC/USDT only tick long 1s 5m | venue | binance_perp | 13 (n<20) | -1.2 | 1.1 | 46.2 | -14.8 |
| Upbit BTC/USDT only tick long 1s 5m | venue | binance_spot | 47 | 0.6 | 2.1 | 55.3 | -13.6 |
| Upbit KRW short open 24h +20% stop pessimistic | new_token | not new | 138 | 5.5 | 3.1 | 62.3 | -33.5 |
| Upbit KRW short open 24h +20% stop pessimistic | ann_hour_kst | 09-15 | 101 | 4.6 | 2.1 | 59.4 | -26.2 |
| Upbit KRW short open 24h +20% stop pessimistic | ann_hour_kst | 16-23 | 37 | 9.5 | 5.9 | 70.3 | -33.5 |
| Upbit KRW short open 24h +20% stop pessimistic | relisting | first listing | 114 | 4.6 | 2.2 | 60.5 | -33.5 |
| Upbit KRW short open 24h +20% stop pessimistic | relisting | relisting | 24 | 9.9 | 7.5 | 70.8 | -25.4 |
| Upbit KRW short open 24h +20% stop pessimistic | year | 2024.0 | 23 | 5.6 | 6.1 | 82.6 | -24.8 |
| Upbit KRW short open 24h +20% stop pessimistic | year | 2025.0 | 62 | 7.6 | 3.7 | 61.3 | -33.5 |
| Upbit KRW short open 24h +20% stop pessimistic | year | 2026.0 | 53 | 1.9 | 1.2 | 54.7 | -26.2 |
| Upbit KRW short open 24h +20% stop pessimistic | venue | binance_perp | 121 | 5.5 | 2.9 | 62.8 | -26.2 |
| Upbit KRW short open 24h +20% stop pessimistic | venue | bybit_perp | 17 (n<20) | 4.2 | 5.1 | 58.8 | -33.5 |
| Bithumb short open 24h +20% stop pessimistic | new_token | not new | 181 | 3.5 | 2.2 | 63.5 | -61.9 |
| Bithumb short open 24h +20% stop pessimistic | ann_hour_kst | 09-15 | 153 | 2.8 | 1.8 | 64.7 | -61.9 |
| Bithumb short open 24h +20% stop pessimistic | ann_hour_kst | 16-23 | 28 | 5.3 | 4.0 | 57.1 | -22.7 |
| Bithumb short open 24h +20% stop pessimistic | relisting | first listing | 180 | 3.7 | 2.2 | 63.9 | -61.9 |
| Bithumb short open 24h +20% stop pessimistic | relisting | relisting | 1 (n<20) | -8.9 | -8.9 | 0.0 | -8.9 |
| Bithumb short open 24h +20% stop pessimistic | year | 2024.0 | 54 | 2.0 | 1.1 | 59.3 | -24.0 |
| Bithumb short open 24h +20% stop pessimistic | year | 2025.0 | 87 | 4.1 | 3.5 | 71.3 | -32.5 |
| Bithumb short open 24h +20% stop pessimistic | year | 2026.0 | 40 | 0.3 | 0.6 | 52.5 | -61.9 |
| Bithumb short open 24h +20% stop pessimistic | venue | binance_perp | 143 | 3.8 | 2.1 | 66.4 | -61.9 |
| Bithumb short open 24h +20% stop pessimistic | venue | bybit_perp | 38 | 0.4 | 2.4 | 52.6 | -24.0 |
| Bithumb short open 24h no stop | excess over BTC (short minus short BTC) | 40 of 181 events have BTC candles | 40 | 2.7 | -1.9 | 55.0 | -112.6 |
| Bithumb short open 24h no stop | same events, raw | 40 events | 40 | 2.2 | -1.5 | 57.5 | -115.6 |
| Upbit KRW short open 24h no stop | excess over BTC (short minus short BTC) | 138 of 138 events have BTC candles | 138 | 5.3 | 0.3 | 69.6 | -136.9 |
| Upbit KRW short open 24h no stop | same events, raw | 138 events | 138 | 5.6 | 0.2 | 64.5 | -142.9 |

BTC candles exist only for v2 Korean events, so the excess-over-BTC rows cover part of the sample (stated in the Value column).

### B. Other exchanges

**Delayed entries from `events_metrics`.**


| Group | Measure | n | Median | Mean | Win % | p10 | Worst |
|---|---|---|---|---|---|---|---|
| Binance spot with prior perp | ann_ext_n5 | 66 | -1.7 | -1.6 | 39.4 | -8.7 | -28.2 |
| Binance spot with prior perp | ann_ext_n60 | 66 | -1.2 | 2.1 | 42.4 | -14.5 | -39.2 |
| Binance spot with prior perp | ann_ext_n1440 | 66 | -10.8 | -2.8 | 37.9 | -37.1 | -64.2 |
| Binance spot with prior perp | start_lst_n60 | 65 | -6.9 | -6.7 | 20.0 | -23.2 | -34.4 |
| Binance spot with prior perp | start_lst_n1440 | 65 | -14.8 | -9.8 | 27.7 | -40.7 | -52.7 |
| Binance spot with prior perp | start_ext_n60 | 65 | -4.8 | -4.3 | 21.5 | -17.4 | -33.7 |
| Binance spot with prior perp | start_ext_n1440 | 65 | -10.8 | -6.5 | 30.8 | -32.7 | -49.3 |
| Binance perp listing | ann_ext_n5 | 154 | -1.5 | -1.5 | 33.1 | -7.1 | -27.4 |
| Binance perp listing | ann_ext_n60 | 154 | -2.4 | -1.7 | 33.8 | -13.4 | -26.1 |
| Binance perp listing | ann_ext_n1440 | 154 | -6.5 | 0.1 | 33.1 | -27.4 | -70.6 |
| Binance perp listing | start_lst_n60 | 259 | -1.0 | 0.2 | 41.3 | -9.4 | -25.3 |
| Binance perp listing | start_lst_n1440 | 259 | -3.7 | 0.3 | 36.7 | -25.6 | -57.1 |
| Binance perp listing | start_ext_n60 | 153 | -1.3 | 0.3 | 40.5 | -7.7 | -14.1 |
| Binance perp listing | start_ext_n1440 | 153 | -7.0 | 0.4 | 34.0 | -23.3 | -56.8 |
| OKX spot | ann_ext_n5 | 38 | -0.8 | -1.4 | 18.4 | -2.7 | -25.5 |
| OKX spot | ann_ext_n60 | 38 | -0.6 | 0.3 | 36.8 | -4.1 | -6.7 |
| OKX spot | ann_ext_n1440 | 38 | -2.3 | -2.2 | 28.9 | -19.5 | -47.5 |
| OKX spot | start_lst_n60 | 85 | -1.5 | -2.6 | 25.9 | -24.1 | -54.6 |
| OKX spot | start_lst_n1440 | 81 | -5.5 | -6.3 | 25.9 | -43.2 | -70.1 |
| OKX spot | start_ext_n60 | 46 | -3.3 | -2.6 | 23.9 | -12.9 | -30.1 |
| OKX spot | start_ext_n1440 | 46 | -8.6 | -7.6 | 21.7 | -34.3 | -47.9 |
| Bybit spot | ann_ext_n5 | 69 | -0.6 | -0.3 | 33.3 | -1.7 | -4.9 |
| Bybit spot | ann_ext_n60 | 69 | -0.4 | -0.3 | 37.7 | -4.6 | -14.0 |
| Bybit spot | ann_ext_n1440 | 69 | -0.4 | 0.8 | 47.8 | -25.4 | -47.6 |
| Bybit spot | start_lst_n60 | 267 | -7.6 | -13.9 | 22.1 | -54.4 | -92.9 |
| Bybit spot | start_lst_n1440 | 267 | -13.3 | -13.7 | 27.7 | -64.5 | -85.1 |
| Bybit spot | start_ext_n60 | 76 | -1.3 | -2.6 | 27.6 | -14.7 | -40.6 |
| Bybit spot | start_ext_n1440 | 76 | -3.0 | 4.4 | 38.2 | -26.6 | -40.9 |
| Coinbase | start_lst_n60 | 225 | -0.2 | 3.6 | 48.4 | -9.3 | -33.3 |
| Coinbase | start_lst_n1440 | 225 | -5.1 | 0.3 | 36.4 | -27.5 | -65.7 |
| Coinbase | start_ext_n60 | 158 | 0.3 | 1.7 | 54.4 | -3.9 | -15.6 |
| Coinbase | start_ext_n1440 | 158 | -2.4 | 4.8 | 40.5 | -19.9 | -54.6 |
| Coinbase [delisted now] | start_lst_n1440 | 11 (n<20) | -1.2 | -4.5 | 36.4 | -19.7 | -31.6 |
| Coinbase [not delisted] | start_lst_n1440 | 214 | -5.1 | 0.6 | 36.4 | -27.6 | -65.7 |


**Tick long by latency (5 min hold).**


| Group | Latency s | n | Median | Mean | Win % | p10 | Worst |
|---|---|---|---|---|---|---|---|
| Binance spot with prior perp | 0.5 | 66 | 7.5 | 14.5 | 83.3 | -3.7 | -14.7 |
| Binance spot with prior perp | 1.0 | 66 | 7.5 | 14.5 | 83.3 | -3.7 | -14.7 |
| Binance spot with prior perp | 2.0 | 66 | 7.5 | 14.3 | 81.8 | -4.2 | -14.7 |
| Binance spot with prior perp | 3.0 | 66 | 0.5 | 4.5 | 54.5 | -8.0 | -19.6 |
| Binance spot with prior perp | 5.0 | 66 | -1.0 | 2.5 | 47.0 | -8.8 | -22.8 |
| Binance spot with prior perp | 30.0 | 66 | -0.6 | -0.6 | 45.5 | -9.6 | -20.1 |
| Binance perp listing (spot ticks) | 0.5 | 36 | 9.9 | 14.7 | 91.7 | 0.9 | -0.5 |
| Binance perp listing (spot ticks) | 1.0 | 36 | 7.9 | 12.2 | 75.0 | -2.2 | -5.1 |
| Binance perp listing (spot ticks) | 2.0 | 36 | 2.6 | 9.2 | 58.3 | -5.1 | -9.4 |
| Binance perp listing (spot ticks) | 3.0 | 36 | -0.5 | 3.5 | 47.2 | -5.4 | -9.3 |
| Binance perp listing (spot ticks) | 5.0 | 36 | -0.5 | 3.3 | 44.4 | -5.2 | -9.7 |
| Binance perp listing (spot ticks) | 30.0 | 36 | -1.3 | 0.2 | 41.7 | -6.7 | -7.9 |
| Coinbase (Binance perp ticks) | 0.5 | 96 | -0.6 | -0.4 | 28.1 | -2.3 | -7.9 |
| Coinbase (Binance perp ticks) | 1.0 | 96 | -0.6 | -0.4 | 27.1 | -2.4 | -7.9 |
| Coinbase (Binance perp ticks) | 2.0 | 96 | -0.7 | -0.4 | 27.1 | -2.4 | -7.8 |
| Coinbase (Binance perp ticks) | 3.0 | 96 | -0.5 | -0.4 | 30.2 | -2.6 | -7.4 |
| Coinbase (Binance perp ticks) | 5.0 | 96 | -0.6 | -0.4 | 26.0 | -2.5 | -7.5 |
| Coinbase (Binance perp ticks) | 30.0 | 96 | -0.6 | -0.4 | 32.3 | -2.4 | -10.1 |


**Speed of the move.**


| Group | n | 1 s | 5 s | 60 s | Drift before | First +2% s | Half move s |
|---|---|---|---|---|---|---|---|
| Binance spot with prior perp | 66 | 0.0 | 11.3 | 9.3 | 0.0 | 2.3 | 2.3 |
| Binance perp listing (spot ticks) | 35 | 0.0 | 8.6 | 9.5 | 0.0 | 1.2 | 1.4 |
| Coinbase (Binance perp ticks) | 96 | 0.0 | 0.0 | 0.0 | 0.1 | 31.4 | 25.5 |

On Binance spot listings with a perp, the move starts a median 2.3 s after releaseDate (measured).

**Shorts (perp, funding included).** Rows marked "(events_metrics)" use the stored `events_metrics` returns, because v1 Binance-perp, OKX and Bybit events have no stored perp candles. They have no stops. Section 5 shows the two methods agree exactly where both exist.


| Group | Entry | Subset | Hold min | Stop | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|---|---|---|
| Binance spot with prior perp | announcement +1m on perp | all | 1440.0 | none | 66 | 9.3 | 0.7 | 60.6 | -138.8 |
| Binance spot with prior perp | announcement +1m on perp | all | 1440.0 | +20% | 66 | 2.7 | 4.7 | 54.5 | -26.2 |
| Binance spot with prior perp | announcement +1m on perp | Binance Will List | 1440.0 | none | 36 | 2.7 | -0.3 | 55.6 | -127.5 |
| Binance spot with prior perp | announcement +1m on perp | Binance Will List | 1440.0 | +20% | 36 | 2.7 | 4.8 | 55.6 | -22.0 |
| Binance spot with prior perp | announcement +1m on perp | HODLer Airdrops | 1440.0 | none | 26 | 10.5 | 0.4 | 65.4 | -138.8 |
| Binance spot with prior perp | announcement +1m on perp | HODLer Airdrops | 1440.0 | +20% | 26 | -2.0 | 3.3 | 50.0 | -26.2 |
| Binance spot with prior perp | announcement +1m on perp | Launchpool | 1440.0 | none | 4 (n<20) | 9.2 | 12.5 | 75.0 | -6.2 |
| Binance spot with prior perp | announcement +1m on perp | Launchpool | 1440.0 | +20% | 4 (n<20) | 9.2 | 12.5 | 75.0 | -6.2 |
| Binance spot with prior perp | spot open +1m on perp | all | 1440.0 | none | 58 | 7.6 | 2.6 | 63.8 | -145.0 |
| Binance spot with prior perp | spot open +1m on perp | all | 1440.0 | +20% | 58 | 7.6 | 4.9 | 58.6 | -25.6 |
| Binance spot with prior perp | spot open +1m on perp | Binance Will List | 1440.0 | none | 33 | 2.2 | 0.6 | 57.6 | -145.0 |
| Binance spot with prior perp | spot open +1m on perp | Binance Will List | 1440.0 | +20% | 33 | 0.2 | 2.8 | 51.5 | -25.4 |
| Binance spot with prior perp | spot open +1m on perp | HODLer Airdrops | 1440.0 | none | 25 | 11.2 | 5.3 | 72.0 | -73.8 |
| Binance spot with prior perp | spot open +1m on perp | HODLer Airdrops | 1440.0 | +20% | 25 | 11.2 | 7.6 | 68.0 | -25.6 |
| Binance perp listing | perp open +1m on listed perp | all | 1440.0 | none | 164 | 3.6 | -3.7 | 61.0 | -236.9 |
| Binance perp listing | perp open +1m on listed perp | all | 1440.0 | +20% | 164 | -0.1 | -1.9 | 50.0 | -29.7 |
| OKX spot | open +1m on external perp | all | 1440.0 | none | 12 (n<20) | 4.0 | 1.9 | 66.7 | -36.9 |
| OKX spot | open +1m on external perp | all | 1440.0 | +20% | 12 (n<20) | 4.0 | 1.2 | 66.7 | -23.5 |
| Bybit spot | open +1m on external perp | all | 1440.0 | none | 44 | 1.8 | 2.3 | 56.8 | -61.4 |
| Bybit spot | open +1m on external perp | all | 1440.0 | +20% | 44 | -1.6 | 1.1 | 47.7 | -22.8 |
| Binance perp listing | perp open +1m on listed perp (events_metrics) | all | 1440.0 | none | 259 | 2.8 | -1.9 | 59.8 | -236.9 |
| OKX spot | open +1m on external perp (events_metrics) | all | 1440.0 | none | 22 | 7.8 | 5.6 | 77.3 | -78.9 |
| Bybit spot | open +1m on external perp (events_metrics) | all | 1440.0 | none | 46 | 1.9 | -11.1 | 58.7 | -253.1 |
| Coinbase | full trading +1m on Binance perp | not delisted | 1440.0 | none | 72 | 3.5 | 1.5 | 65.3 | -99.1 |
| Coinbase | full trading +1m on Binance perp | not delisted | 1440.0 | +20% | 72 | 3.4 | 2.6 | 63.9 | -24.9 |
| Coinbase | full trading +1m on Binance perp | all | 1440.0 | none | 72 | 3.5 | 1.5 | 65.3 | -99.1 |
| Coinbase | full trading +1m on Binance perp | all | 1440.0 | +20% | 72 | 3.4 | 2.6 | 63.9 | -24.9 |
| Coinbase | announcement +1m on Binance perp | all | 1440.0 | none | 98 | 0.5 | -2.4 | 51.0 | -109.8 |


Funding and stop touches:


| Group | Entry | Subset | n | Funding paid mean | No funding rows | % touch +20% | % touch +50% | Losses beyond -50% |
|---|---|---|---|---|---|---|---|---|
| Binance perp listing | perp open +1m on listed perp | all | 164 | 0.4 | 0 (n<20) | 40.9 | 15.2 | 14.0 |
| Binance perp listing | perp open +1m on listed perp (events_metrics) | all | 259 | 0.4 | 17 (n<20) | 0.0 | 0.0 | 16.0 |
| Binance spot with prior perp | announcement +1m on perp | Binance Will List | 36 | 0.9 | 0 (n<20) | 33.3 | 16.7 | 2.0 |
| Binance spot with prior perp | announcement +1m on perp | HODLer Airdrops | 26 | 0.9 | 0 (n<20) | 38.5 | 19.2 | 2.0 |
| Binance spot with prior perp | announcement +1m on perp | Launchpool | 4 (n<20) | 0.0 | 0 (n<20) | 0.0 | 0.0 | 0.0 |
| Binance spot with prior perp | announcement +1m on perp | all | 66 | 0.8 | 0 (n<20) | 33.3 | 16.7 | 4.0 |
| Binance spot with prior perp | spot open +1m on perp | Binance Will List | 33 | 1.0 | 0 (n<20) | 24.2 | 9.1 | 1.0 |
| Binance spot with prior perp | spot open +1m on perp | HODLer Airdrops | 25 | 2.1 | 0 (n<20) | 28.0 | 12.0 | 2.0 |
| Binance spot with prior perp | spot open +1m on perp | all | 58 | 1.4 | 0 (n<20) | 25.9 | 10.3 | 3.0 |
| Bybit spot | open +1m on external perp | all | 44 | 0.4 | 0 (n<20) | 22.7 | 4.5 | 1.0 |
| Bybit spot | open +1m on external perp (events_metrics) | all | 46 | 0.4 | 6 (n<20) | 0.0 | 0.0 | 7.0 |
| Coinbase | announcement +1m on Binance perp | all | 98 | 0.7 | 2 (n<20) | 19.4 | 7.1 | 4.0 |
| Coinbase | full trading +1m on Binance perp | all | 72 | 0.5 | 1 (n<20) | 15.3 | 4.2 | 1.0 |
| Coinbase | full trading +1m on Binance perp | not delisted | 72 | 0.5 | 1 (n<20) | 15.3 | 4.2 | 1.0 |
| OKX spot | open +1m on external perp | all | 12 (n<20) | 0.8 | 0 (n<20) | 33.3 | 8.3 | 0.0 |
| OKX spot | open +1m on external perp (events_metrics) | all | 22 | 0.5 | 2 (n<20) | 0.0 | 0.0 | 1.0 |


- Binance perp listings: the newly listed perp is too volatile to short with a stop. 41% of them touch +20% and 15% touch +50% within 24 h (measured).
- OKX and Bybit: the long at the open loses in both periods. The Bybit 24 h long has a v1 median of -5.4% (n 29) and v2+v3 -16.1% (n 238). More history makes it clearer, not better.
- Coinbase: the Binance perp barely moves in the 60 s after the announcement, and coins that are delisted now are listed separately in the tables.

### C. Strategy table

The full table, 293 strategies with per-year results, concentration, drawdown and losing streak, is `analysis/strategy_table.csv`. It is sorted by robustness: survives, n<20 in one period, single period, no, negative in both, then by the weaker period's median. The strategies that survive:


| Strategy | n | Median | Mean | Win % | p10 | Worst | v1 median | v2+v3 median | Top-5 share % | Max drawdown pp | Longest losing streak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Upbit KRW | long | tick 0.5s | 60m | 133 | 15.1 | 27.4 | 83.5 | -1.8 | -19.6 | 13.6 | 19.5 | 22.2 | 21.7 | 3.0 |
| Upbit KRW | long | tick 0.5s | 5m | 133 | 16.1 | 28.8 | 89.5 | -0.3 | -17.3 | 12.4 | 19.8 | 21.7 | 17.3 | 2.0 |
| Binance spot with prior perp | long | tick 1s | 5m | 66 | 7.5 | 14.5 | 83.3 | -3.7 | -14.7 | 6.5 | 7.8 | 34.1 | 14.7 | 3.0 |
| Binance spot with prior perp | long | tick 1s | 60m | 66 | 11.1 | 19.4 | 72.7 | -9.8 | -22.0 | 5.5 | 11.4 | 46.7 | 31.2 | 3.0 |
| Upbit KRW | long | tick 1s | 60m | 133 | 8.5 | 19.5 | 69.2 | -7.5 | -19.6 | 5.0 | 9.5 | 30.0 | 43.8 | 5.0 |
| Upbit KRW | long | tick 1s | 5m | 133 | 9.1 | 20.7 | 74.4 | -4.2 | -17.3 | 5.0 | 12.2 | 29.7 | 24.6 | 3.0 |
| Binance spot with prior perp | short | announcement +1m on perp | 1440m | stop +50% pessimistic | 66 | 9.3 | 1.9 | 60.6 | -49.7 | -57.6 | 4.9 | 9.6 | 213.4 | 167.9 | 5.0 |
| Binance spot with prior perp | short | announcement +1m on perp | 1440m | stop none | 66 | 9.3 | 0.7 | 60.6 | -37.2 | -138.8 | 4.9 | 9.6 | 540.5 | 247.5 | 5.0 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop +50% pessimistic | 138 | 5.6 | 1.8 | 64.5 | -25.3 | -64.5 | 3.7 | 5.8 | 66.3 | 144.5 | 4.0 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic | 138 | 5.5 | 3.1 | 62.3 | -21.2 | -33.5 | 2.9 | 5.7 | 36.9 | 74.8 | 4.0 |
| Upbit KRW | short | open +15m +1m on perp | 1440m | stop +20% pessimistic | 138 | 4.5 | 2.8 | 62.3 | -21.3 | -30.0 | 2.9 | 4.9 | 39.6 | 87.1 | 5.0 |
| Upbit KRW | short | open +60m +1m on perp | 1440m | stop +20% pessimistic | 138 | 3.5 | 0.8 | 60.1 | -22.0 | -28.5 | 2.8 | 4.7 | 108.6 | 100.3 | 5.0 |
| Bithumb | short | announcement +0m +1m on perp | 1440m | stop +20% pessimistic | 197 | 2.3 | 0.5 | 57.4 | -21.2 | -88.8 | 3.4 | 2.2 | 168.8 | 234.9 | 8.0 |
| Bithumb | short | announcement +60m +1m on perp | 1440m | stop +20% pessimistic | 197 | 1.9 | 0.4 | 54.8 | -20.8 | -77.5 | 2.9 | 1.8 | 266.8 | 274.8 | 14.0 |
| Upbit KRW | short | announcement +60m +1m on perp | 1440m | stop +20% pessimistic | 149 | 4.2 | 1.2 | 58.4 | -21.3 | -33.3 | 1.5 | 4.6 | 91.8 | 116.1 | 4.0 |
| Bithumb | short | trading open +1m on perp | 240m | stop none | 182 | 1.7 | 0.9 | 63.2 | -7.7 | -59.6 | 2.4 | 1.5 | 74.4 | 90.8 | 6.0 |
| Bithumb | short | open +240m +1m on perp | 1440m | stop +20% pessimistic | 181 | 2.0 | 0.7 | 60.8 | -20.3 | -25.2 | 3.0 | 1.4 | 89.8 | 123.4 | 4.0 |
| Upbit BTC/USDT only | long | tick 0.5s | 5m | 60 | 1.5 | 4.1 | 70.0 | -1.3 | -13.6 | 1.3 | 1.8 | 35.3 | 19.0 | 6.0 |
| Bithumb | short | trading open +1m on perp | 240m | stop +10% pessimistic | 182 | 1.4 | 1.0 | 60.4 | -10.5 | -32.5 | 2.3 | 1.1 | 66.9 | 66.7 | 6.0 |
| Upbit BTC/USDT only | long | tick 0.5s | 60m | 60 | 2.5 | 6.2 | 66.7 | -2.5 | -32.9 | 0.8 | 3.0 | 65.0 | 39.6 | 4.0 |
| Binance spot with prior perp | short | announcement +1m on perp | 1440m | stop +20% pessimistic | 66 | 2.7 | 4.7 | 54.5 | -20.7 | -26.2 | 4.9 | 0.8 | 86.1 | 75.5 | 5.0 |
| Bithumb | short | open +15m +1m on perp | 1440m | stop +20% pessimistic | 181 | 2.9 | 1.8 | 60.8 | -20.5 | -35.4 | 0.6 | 3.0 | 51.9 | 160.1 | 8.0 |
| Upbit KRW | long | tick 2s | 60m | 133 | 1.2 | 8.6 | 54.9 | -12.2 | -23.7 | 0.5 | 1.4 | 51.4 | 89.1 | 9.0 |
| Bithumb | short | trading open +1m on perp | 60m | stop +20% pessimistic | 182 | 0.7 | 0.7 | 61.0 | -4.5 | -61.9 | 1.7 | 0.5 | 82.0 | 98.3 | 8.0 |
| Bithumb | short | trading open +1m on perp | 60m | stop +50% pessimistic | 182 | 0.7 | 0.6 | 61.0 | -4.5 | -61.9 | 1.7 | 0.5 | 106.1 | 107.3 | 8.0 |
| Bithumb | short | trading open +1m on perp | 60m | stop none | 182 | 0.7 | 0.8 | 61.0 | -4.5 | -54.2 | 1.7 | 0.5 | 72.6 | 58.3 | 8.0 |
| Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic | 181 | 3.5 | 2.2 | 63.5 | -20.5 | -61.9 | 0.3 | 3.8 | 45.6 | 209.4 | 8.0 |
| Coinbase | long | open +1m external | 60m | 158 | 0.3 | 1.7 | 54.4 | -3.9 | -15.6 | 0.4 | 0.3 | 36.4 | 34.4 | 8.0 |
| Bithumb | short | trading open +1m on perp | 60m | stop +10% pessimistic | 182 | 0.6 | 1.1 | 59.9 | -4.9 | -13.1 | 1.7 | 0.3 | 54.0 | 39.8 | 8.0 |
| Binance spot with prior perp | long | tick 3s | 5m | 66 | 0.5 | 4.5 | 54.5 | -8.0 | -19.6 | 0.2 | 0.9 | 72.0 | 51.1 | 7.0 |
| Upbit KRW | short | trading open +1m on perp | 240m | stop +20% pessimistic | 138 | 2.2 | 1.3 | 64.5 | -12.9 | -26.2 | 0.0 | 3.5 | 58.1 | 101.2 | 6.0 |
| Upbit KRW | short | trading open +1m on perp | 240m | stop +50% pessimistic | 138 | 2.2 | 0.7 | 64.5 | -12.9 | -51.9 | 0.0 | 3.5 | 109.4 | 136.0 | 6.0 |
| Upbit KRW | short | trading open +1m on perp | 240m | stop none | 138 | 2.2 | 0.6 | 64.5 | -12.9 | -55.4 | 0.0 | 3.5 | 114.4 | 136.6 | 6.0 |
| Upbit KRW | short | trading open +1m on perp | 240m | stop +10% pessimistic | 138 | 1.4 | 1.1 | 59.4 | -11.1 | -16.6 | 0.0 | 2.4 | 69.4 | 68.8 | 6.0 |


**Where only a long or only a short is possible (at the announcement).** "Long" means the coin already trades on an external spot venue. "Short" means a Binance or Bybit USDT perp exists. The spot side is inferred from the first external venue found, so a coin with both a perp and spot elsewhere can show as short only.


| Group | Long and short | Long only | Short only | Neither | n |
|---|---|---|---|---|---|
| Binance perp | 60 | 50 | 44 | 107 | 261 |
| Binance spot | 0 | 4 | 66 | 6 | 76 |
| Bithumb spot | 125 | 42 | 73 | 33 | 273 |
| Bybit spot | 18 | 11 | 40 | 201 | 270 |
| Coinbase spot | 0 | 0 | 0 | 234 | 234 |
| OKX spot | 5 | 12 | 21 | 53 | 91 |
| Upbit BTC/USDT only | 48 | 14 | 15 | 8 | 85 |
| Upbit KRW | 98 | 25 | 51 | 30 | 204 |


### D. Liquidity and size

**Order-book depth (USD-M perp, cumulative depth within the band, USD thousands).** The depth is the last snapshot at or before the announcement. The changes compare the first three snapshots after it. Treat depth as an upper bound on size, not as an impact model.


| Group | Period | n | Median | p25 | p10 | 1st after s | Change % | 2nd after s | Change % | 3rd after s | Change % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Binance spot | all | 65 | 65.4 | 26.4 | 15.5 | 13.6 | -22.1 | 45.3 | -41.2 | 74.6 | -22.4 |
| Bithumb official | all | 114 | 194.5 | 119.1 | 74.4 | 15.0 | -39.3 | 45.0 | -40.1 | 76.0 | -32.1 |
| Bithumb third-party | all | 33 | 36.1 | 18.4 | 12.9 | 16.2 | -23.7 | 45.5 | -12.7 | 76.3 | -4.1 |
| Bybit spot | all | 35 | 186.2 | 74.5 | 22.5 | 12.0 | 0.2 | 47.0 | 0.7 | 74.0 | 1.5 |
| Coinbase spot | all | 95 | 148.0 | 80.4 | 31.5 | 14.0 | 1.1 | 44.8 | 2.1 | 74.3 | 3.9 |
| OKX spot | all | 22 | 170.7 | 43.2 | 30.7 | 20.9 | -1.1 | 50.6 | -3.1 | 79.4 | -4.6 |
| Upbit BTC/USDT only | all | 54 | 103.3 | 43.5 | 20.6 | 7.0 | 0.0 | 36.5 | -26.8 | 66.0 | -27.5 |
| Upbit KRW | all | 123 | 128.1 | 57.3 | 27.8 | 8.0 | -8.0 | 44.0 | -63.6 | 68.0 | -49.3 |
| Binance spot | 2024-2025 | 44 | 95.6 | 42.0 | 21.0 | 13.7 | -14.5 | 44.7 | -42.4 | 74.6 | -33.8 |
| Binance spot | 2026.0 | 21 | 31.5 | 16.5 | 11.3 | 12.7 | -23.8 | 46.8 | -36.4 | 74.5 | -4.7 |
| Bithumb official | 2024-2025 | 114 | 194.5 | 119.1 | 74.4 | 15.0 | -39.3 | 45.0 | -40.1 | 76.0 | -32.1 |
| Bithumb third-party | 2026.0 | 33 | 36.1 | 18.4 | 12.9 | 16.2 | -23.7 | 45.5 | -12.7 | 76.3 | -4.1 |
| Bybit spot | 2024-2025 | 29 | 190.9 | 111.3 | 31.0 | 10.0 | 0.2 | 45.5 | 0.7 | 72.0 | 2.0 |
| Bybit spot | 2026.0 | 6 (n<20) | 69.6 | 30.8 | 19.5 | 26.5 | 4.2 | 51.5 | -0.3 | 79.0 | -4.2 |
| Coinbase spot | 2024-2025 | 75 | 187.9 | 90.7 | 43.1 | 13.2 | 4.8 | 44.8 | 6.5 | 74.2 | 8.4 |
| Coinbase spot | 2026.0 | 20 | 83.9 | 31.8 | 19.6 | 14.6 | -6.2 | 43.7 | -5.0 | 74.5 | -0.5 |
| OKX spot | 2024-2025 | 11 (n<20) | 421.4 | 257.3 | 44.9 | 4.4 | -1.8 | 40.2 | -28.2 | 60.2 | -17.1 |
| OKX spot | 2026.0 | 11 (n<20) | 54.1 | 35.3 | 30.6 | 26.1 | -0.6 | 51.7 | 8.1 | 81.0 | -0.1 |
| Upbit BTC/USDT only | 2024-2025 | 36 | 127.0 | 94.8 | 52.0 | 7.5 | -1.1 | 44.0 | -36.0 | 70.0 | -37.0 |
| Upbit BTC/USDT only | 2026.0 | 18 (n<20) | 29.9 | 19.1 | 9.4 | 5.0 | 0.8 | 35.0 | -18.2 | 66.0 | -14.9 |
| Upbit KRW | 2024-2025 | 80 | 195.5 | 110.9 | 55.9 | 10.0 | -6.2 | 45.0 | -67.0 | 69.0 | -54.3 |
| Upbit KRW | 2026.0 | 43 | 57.3 | 27.8 | 20.7 | 6.0 | -8.0 | 44.0 | -55.0 | 65.0 | -46.2 |

Within ±2% and ±5%, and the bid side, are in `analysis/d_book.csv`. On Upbit KRW, ask depth within 1% changes a median -64% by the second snapshot, about 44 s after the notice (measured). Coinbase and Bybit books do not change. The 2026 books are thinner than 2024–2025 for every Korean group (measured).

**Fillable size from ticks (USD thousands).** This is the whole market's flow, not one participant's fill: USD traded in the first 5 s from the first trade at or after announcement + L, until price first exceeds that trade's price by 2%.


| Group | Venue | Latency s | n | Median | p25 | p10 |
|---|---|---|---|---|---|---|
| Binance spot | binance_perp | 0.0 | 66 | 131.8 | 76.4 | 41.8 |
| Binance spot | binance_perp | 1.0 | 66 | 129.9 | 76.6 | 43.8 |
| Bithumb official | binance_perp | 0.0 | 119 | 340.2 | 172.3 | 107.6 |
| Bithumb official | binance_perp | 1.0 | 119 | 387.0 | 165.6 | 76.6 |
| Bithumb official | binance_spot | 0.0 | 92 | 175.8 | 92.0 | 55.2 |
| Bithumb official | binance_spot | 1.0 | 92 | 150.0 | 74.7 | 19.8 |
| Coinbase spot | binance_perp | 0.0 | 96 | 93.3 | 30.0 | 4.3 |
| Coinbase spot | binance_perp | 1.0 | 96 | 81.1 | 29.1 | 4.1 |
| Coinbase spot | binance_spot | 0.0 | 72 | 25.9 | 8.0 | 4.5 |
| Coinbase spot | binance_spot | 1.0 | 72 | 31.6 | 9.0 | 2.8 |
| Upbit BTC/USDT only | binance_perp | 0.0 | 54 | 159.5 | 85.8 | 42.3 |
| Upbit BTC/USDT only | binance_perp | 1.0 | 54 | 129.5 | 63.5 | 31.8 |
| Upbit BTC/USDT only | binance_spot | 0.0 | 47 | 94.6 | 37.2 | 20.1 |
| Upbit BTC/USDT only | binance_spot | 1.0 | 47 | 87.0 | 30.1 | 15.0 |
| Upbit KRW | binance_perp | 0.0 | 125 | 224.2 | 115.9 | 57.6 |
| Upbit KRW | binance_perp | 1.0 | 125 | 246.9 | 124.0 | 60.2 |
| Upbit KRW | binance_spot | 0.0 | 89 | 127.4 | 62.7 | 31.4 |
| Upbit KRW | binance_spot | 1.0 | 89 | 96.4 | 26.8 | 7.0 |

The 30 s window and the 1% and 5% caps are in `analysis/d_fillable.csv`.

**DEX swaps** (one pool per event, the one with the most swaps).


| Group | Events with swaps before and after | Years | Onset pairs | DEX onset minus Binance s | DEX after | DEX before | Volume first 60 s USD | Events with a 10k+ buy before |
|---|---|---|---|---|---|---|---|---|
| all | 31 | 2026 | 20 | 2 | 17 | 3 | 89012 | 4 |
| Bithumb third-party | 17 (n<20) | 2026 | 10 (n<20) | 1 | 8 | 2 | 89012 | 4 |
| Upbit BTC/USDT only | 4 (n<20) | 2026 | 3 (n<20) | 9 | 3 | 0 | 36423 | 0 |
| Upbit KRW | 10 (n<20) | 2026 | 7 (n<20) | 3 | 6 | 1 | 123033 | 0 |

- Timing (measured): the DEX +2% onset follows Binance's first +2% print by a median 2.1 s. All events with enough swaps are from 2026.
- Buys of 10k USD or more in the 2 minutes before the announcement (measured): none on Upbit events, and 4 of 17 Bithumb events. Those Bithumb times are third-party and arrive after the move (section A), so a "before" buy may really come after the notice. The test cannot tell an early buyer from a late timestamp (inferred).
- Measured buy impact against the constant-product estimate size / (liquidity_usd_at_ann / 2):


| Buy size USD | n | Measured impact % median | Constant-product estimate % median |
|---|---|---|---|
| <1k | 26,610 | 0.03 | 0.03 |
| 1k-5k | 2,573 | 0.19 | 0.33 |
| 5k-20k | 526 | 0.83 | 1.49 |
| 20k-100k | 96 | 2.86 | 4.13 |
| >=100k | 8 (n<20) | 4.08 | 13.90 |

Measured impact is 0.59 of the estimate for buys of 5k USD or more. Liquidity today is 0.87 of liquidity at the announcement (41 pools).
- Gross return to +5 min and the largest size still positive after costs. The cost is twice the measured median impact for that size plus gas for two swaps. Gas per swap is an assumption: 

| Chain | Gas USD per swap (assumed) |
|---|---|
| eth | 10.00 |
| base | 0.05 |
| bsc | 0.10 |



| Group | Entry s after the notice | n | Gross median | Net 1k | Net 5k | Net 20k | Net 100k | Largest positive size USD |
|---|---|---|---|---|---|---|---|---|
| Bithumb third-party | 0.0 | 17 (n<20) | 2.0 | 1.5 | 0.3 | -3.8 | -6.2 | 5000.0 |
| Bithumb third-party | 3.0 | 17 (n<20) | 0.0 | -0.4 | -1.7 | -5.7 | -8.2 | 0.0 |
| Bithumb third-party | 12.0 | 17 (n<20) | -1.1 | -1.5 | -2.7 | -6.8 | -9.2 | 0.0 |
| Upbit BTC/USDT only | 0.0 | 4 (n<20) | 0.5 | -1.9 | -1.6 | -5.3 | -7.7 | 0.0 |
| Upbit BTC/USDT only | 3.0 | 4 (n<20) | 0.5 | -1.9 | -1.6 | -5.3 | -7.7 | 0.0 |
| Upbit BTC/USDT only | 12.0 | 4 (n<20) | -1.7 | -4.1 | -3.7 | -7.5 | -9.9 | 0.0 |
| Upbit KRW | 0.0 | 10 (n<20) | 11.8 | 9.4 | 9.7 | 6.0 | 3.6 | 100000.0 |
| Upbit KRW | 3.0 | 10 (n<20) | 5.3 | 3.9 | 3.4 | -0.5 | -2.9 | 5000.0 |
| Upbit KRW | 12.0 | 10 (n<20) | 0.0 | -0.6 | -1.7 | -5.8 | -8.2 | 0.0 |

The Upbit KRW rows have n 10 (n<20). The DEX edge is gone within about 12 s (measured, small sample).

**Size caps (inferred rule).** The cap is half of the smaller of the 2026 depth within 1% (p25) and the 1-s-late 5 s flow (p25), rounded down to 5k USD.


| Strategy | Inputs | Cap USD k |
|---|---|---|
| Upbit KRW fast long | 2026 ask depth within 1%, p25 = 27.8k; 5 s flow at 1 s latency before +2%, Binance spot, p25 = 26.8k | 10 |
| Bithumb fast long (paper only) | 2024-2025 ask depth within 1%, p25 = 119.1k; 2026 ask depth within 1% (third-party-time events), p25 = 18.4k; 5 s flow at 1 s latency before +2%, Binance spot, p25 = 74.7k | 5 |
| Upbit KRW short after the open | 2026 bid depth within 1% before the announcement, p25 = 36.9k | 15 |
| Bithumb short after the open | 2026 bid depth within 1% before the announcement (third-party-time events), p25 = 27.8k | 10 |
| Binance spot with prior perp fast long | 2026 ask depth within 1%, p25 = 16.5k | 5 |


**Risks the data does not cover (checklist).**
- MEV: sandwiching and front-running of DEX buys raise the real cost above the measured impact.
- Token approvals and allowance transactions add latency and gas before the first DEX buy.
- Wrong contract: a fake token with the same ticker. Check the contract against the exchange's own notice.
- High-fee pools: one pool in the data (H0277) charges a fee far above the usual tiers. Check the pool fee before buying.
- Transfer taxes and honeypots: some tokens tax or block sells.
- Reverted transactions cost gas and time.
- Liquidation and auto-deleveraging (ADL) on perps: a short can be closed by the exchange during a spike.
- API outages and rate limits on the exchange, the notice feed, or both, at exactly the busy moment.

### E. Risk and bias

**Survivorship (daily candles, gross).** Excluded events with daily candles, from the announcement-day close (UTC) to later closes, against included events on the same daily calculation from their 1-minute candles:


| Source | Horizon | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|
| delisted_daily_candles | d1 | 39 | -0.6 | 0.2 | 46.2 | -10.8 |
| delisted_daily_candles | d7 | 38 | -10.8 | -2.5 | 28.9 | -46.0 |
| delisted_daily_candles | d30 | 37 | -18.6 | -4.3 | 35.1 | -60.8 |
| included, 1m candles | d1 | 847 | -3.1 | -2.2 | 33.9 | -71.6 |

Share of events with no opening candles on the listing market:


| Group | n | No opening candles | Share % |
|---|---|---|---|
| Binance perp | 261 | 2.0 | 0.8 |
| Binance spot | 76 | 2.0 | 2.6 |
| Bithumb spot | 273 | 24.0 | 8.8 |
| Bybit spot | 270 | 3.0 | 1.1 |
| Coinbase spot | 234 | 8.0 | 3.4 |
| OKX spot | 91 | 6.0 | 6.6 |
| Upbit BTC/USDT only | 85 | 14.0 | 16.5 |
| Upbit KRW | 204 | 14.0 | 6.9 |

Direction (inferred): the missing coins do not fall more on day one than the included coins, but they fall further over the following month. A short-side result is understated for them, and a long-side result overstated. The size is limited by how few they are, about 7% of Upbit KRW and 9% of Bithumb events.

**Concentration, drawdown and losing streaks.**


| Strategy | n | Median | Mean | Worst | Top-5 share % | Mean without top 5 | Median without top 5 | Max drawdown pp | Longest losing streak | Losses beyond -50% |
|---|---|---|---|---|---|---|---|---|---|---|
| Upbit KRW | long | tick 1s | 5m | 133 | 9.1 | 20.7 | -17.3 | 29.7 | 15.2 | 8.2 | 24.6 | 3.0 | 0.0 |
| Bithumb official | long | tick 1s | 5m | 129 | 2.2 | 4.3 | -14.0 | 24.8 | 3.4 | 2.0 | 24.9 | 5.0 | 0.0 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic | 138 | 5.5 | 3.1 | -33.5 | 36.9 | 2.1 | 4.8 | 74.8 | 4.0 | 0.0 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop none | 138 | 5.6 | 0.2 | -142.9 | 527.7 | -1.0 | 5.5 | 252.9 | 4.0 | 8.0 |
| Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic | 181 | 3.5 | 2.2 | -61.9 | 45.6 | 1.2 | 2.8 | 209.4 | 8.0 | 1.0 |
| Bithumb | short | trading open +1m on perp | 1440m | stop none | 181 | 3.8 | 0.5 | -142.9 | 187.8 | -0.5 | 3.4 | 267.4 | 7.0 | 7.0 |
| Binance perp listing | short | perp open +1m on listed perp (events_metrics) | 1440m | stop none | 259 | 2.8 | -1.9 | -236.9 | -45.9 | -2.8 | 2.2 | 802.3 | 7.0 | 16.0 |
| Binance spot with prior perp | short | spot open +1m on perp | 1440m | stop +20% pessimistic | 58 | 7.6 | 4.9 | -25.6 | 73.4 | 1.4 | 2.2 | 93.1 | 5.0 | 0.0 |

Drawdown is in percentage points of cumulative per-trade returns, one equal-size trade per event, in date order. The worst events:


| Strategy | Event | Symbol | Exchange | Year | Return % |
|---|---|---|---|---|---|
| Binance perp listing | short | perp open +1m on listed perp (events_metrics) | 1440m | stop none | V0716 | TRUMP | Binance | 2025.0 | -236.9 |
| Bithumb | short | trading open +1m on perp | 1440m | stop none | V1071 | HYPER | Bithumb | 2025.0 | -142.9 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop none | V0121 | HYPER | Upbit | 2025.0 | -142.9 |
| Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic | H0244 | BANK | Bithumb | 2026.0 | -61.9 |
| Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic | V0069 | VTHO | Upbit | 2025.0 | -33.5 |
| Binance spot with prior perp | short | spot open +1m on perp | 1440m | stop +20% pessimistic | V0444 | SAPIEN | Binance | 2025.0 | -25.6 |
| Upbit KRW | long | tick 1s | 5m | V0024 | JUP | Upbit | 2024.0 | -17.3 |
| Bithumb official | long | tick 1s | 5m | V1020 | GNO | Bithumb | 2025.0 | -14.0 |


### F. Hyperliquid as the only perp venue

**Coverage.** Hyperliquid perps at the announcement, for the 353 Korean events with an HL status (Upbit 2024–2026 and Bithumb v1). There is no HL status for Bithumb 2024–2025.


| Group | Year | n | HL perp at announcement | HL only (no Binance or Bybit perp) | Share % |
|---|---|---|---|---|---|
| Bithumb spot | 2026.0 | 64 | 5.0 | 0.0 | 7.8 |
| Upbit BTC/USDT only | 2024.0 | 26 | 10.0 | 2.0 | 38.5 |
| Upbit BTC/USDT only | 2025.0 | 33 | 8.0 | 0.0 | 24.2 |
| Upbit BTC/USDT only | 2026.0 | 26 | 6.0 | 0.0 | 23.1 |
| Upbit KRW | 2024.0 | 41 | 19.0 | 3.0 | 46.3 |
| Upbit KRW | 2025.0 | 85 | 30.0 | 1.0 | 35.3 |
| Upbit KRW | 2026.0 | 78 | 20.0 | 0.0 | 25.6 |
| Bithumb spot | all | 64 | 5.0 | 0.0 | 7.8 |
| Upbit BTC/USDT only | all | 85 | 24.0 | 2.0 | 28.2 |
| Upbit KRW | all | 204 | 69.0 | 4.0 | 33.8 |
| All Korean | all | 353 | 98.0 | 6.0 | 27.8 |


**Coarse short (24 h from the open).** HL candles are 5 min to 8 h, so the entry is the close of the HL candle containing the open, and the exit is the close of the HL candle containing entry + 24 h. The same timestamps are priced on Binance, and compared with the 1-minute Binance entry on the same events.


| Group | Measure | n | Median | Mean | Win % | Worst |
|---|---|---|---|---|---|---|
| Bithumb spot | HL coarse short, all with HL candles | 5 (n<20) | 10.0 | 4.9 | 80.0 | -14.4 |
| Bithumb spot | HL coarse short, events also on Binance | 4 (n<20) | 7.9 | 3.6 | 75.0 | -14.4 |
| Bithumb spot | Binance at the HL timestamps | 4 (n<20) | 7.7 | 3.5 | 75.0 | -14.5 |
| Bithumb spot | Binance 1m entry at the open | 4 (n<20) | 8.4 | 4.3 | 75.0 | -19.9 |
| Upbit BTC/USDT only | HL coarse short, all with HL candles | 22 | -0.7 | 0.0 | 45.5 | -9.6 |
| Upbit BTC/USDT only | HL coarse short, events also on Binance | 20 | -1.0 | -0.4 | 40.0 | -9.6 |
| Upbit BTC/USDT only | Binance at the HL timestamps | 20 | -1.0 | -0.4 | 40.0 | -9.6 |
| Upbit BTC/USDT only | Binance 1m entry at the open | 20 | 0.1 | 0.2 | 50.0 | -16.3 |
| Upbit KRW | HL coarse short, all with HL candles | 72 | 4.3 | 0.4 | 68.1 | -121.3 |
| Upbit KRW | HL coarse short, events also on Binance | 61 | 3.7 | -0.7 | 65.6 | -121.3 |
| Upbit KRW | Binance at the HL timestamps | 61 | 3.8 | -0.8 | 65.6 | -129.1 |
| Upbit KRW | Binance 1m entry at the open | 61 | 6.1 | 0.9 | 75.4 | -142.9 |



| Group | n | HL funding paid mean % | Binance funding paid mean % | HL 24 h volume / Binance | HL candle intervals |
|---|---|---|---|---|---|
| Bithumb spot | 4 (n<20) | -0.12 | 0.00 | 0.45 | 1h:2;15m:2;5m:1 |
| Upbit BTC/USDT only | 20 | -0.02 | 0.00 | 0.03 | 4h:14;1h:5;8h:3 |
| Upbit KRW | 61 | 1.54 | 1.74 | 0.06 | 4h:54;1h:8;8h:6;15m:3;5m:1 |

On the same timestamps, HL and Binance shorts give nearly the same result (measured). The gap to the 1-minute Binance entry comes from the coarse entry. HL volume is a small fraction of Binance, so HL is a fallback venue, not a primary one (inferred). Not measurable here: HL ticks, HL 1-minute candles, HL order books, and HL status for Bithumb 2024–2025.

### G. Own latency



| Log | Rows | Notice | Listing | Seen after official time s | Poll interval s | HTTP ms | Region |
|---|---|---|---|---|---|---|---|
| upbit_poll_log | 2 | 카바(KAVA) 입출금 일시 중단 안내 | False | 6.8 | 0.5 | 443 | South America, residential, laptop |
| upbit_poll_log | 2 | 카바(KAVA) 유의 촉구 안내 | False | 7.6 | 0.5 | 557 | South America, residential, laptop |
| bithumb_poll_log | 2 | 카바(KAVA) 입출금 일시 중지 안내 | False | 1359.5 | 1.0 | 1,133 | South America, residential, laptop |
| bithumb_poll_log | 2 | 카바(KAVA) 유의촉구 안내 | False | 2296.9 | 1.0 | 1,117 | South America, residential, laptop |
| binance_poll_log | 0 | n/a | n/a | n/a | n/a | n/a | n/a |

The logs settle nothing yet. They hold no listing notice, they were polled from South America, far from the exchanges, and `binance_poll_log` is empty. The first Upbit rows show the public API serving a notice several seconds after its `first_listed_at`. That delay would by itself use up the whole 1 s budget of the fast long (inferred). Settling it needs at least 10 real listing notices polled from Seoul or Tokyo, with the delay from the official time to the first sight measured on each.

### H. Other patterns and risks



| Pattern | Measure | Value | Source CSV |
|---|---|---|---|
| funding as large as the edge | Upbit KRW: funding paid by the short over 24 h, mean % | 3.4 | a_short_open_funding_touch |
| funding as large as the edge | Upbit KRW: 24 h short after funding, stop none, mean % | 0.2 | a_short_open |
| funding as large as the edge | Upbit KRW: 24 h short after funding, stop +20%, mean % | 3.1 | a_short_open |
| funding as large as the edge | Bithumb: funding paid by the short over 24 h, mean % | 1.2 | a_short_open_funding_touch |
| funding as large as the edge | Bithumb: 24 h short after funding, stop none, mean % | 0.5 | a_short_open |
| funding as large as the edge | Bithumb: 24 h short after funding, stop +20%, mean % | 2.2 | a_short_open |
| thinner books in 2026 | Upbit KRW: ask depth within 1% before the announcement, 2024-2025, median USD k | 195.5 | d_book |
| thinner books in 2026 | Upbit KRW: ask depth within 1% before the announcement, 2026, median USD k | 57.3 | d_book |
| thinner books in 2026 | Bithumb official: ask depth within 1% before the announcement, 2024-2025, median USD k | 194.5 | d_book |
| thinner books in 2026 | Upbit BTC/USDT only: ask depth within 1% before the announcement, 2024-2025, median USD k | 127.0 | d_book |
| thinner books in 2026 | Upbit BTC/USDT only: ask depth within 1% before the announcement, 2026, median USD k | 29.9 | d_book |
| the fast edge narrowing over time | Upbit KRW: tick long 1 s, 5 min, 2024, median % (n=24) | 8.3 | a_tick_long |
| the fast edge narrowing over time | Upbit KRW: tick long 1 s, 5 min, 2025, median % (n=62) | 13.3 | a_tick_long |
| the fast edge narrowing over time | Upbit KRW: tick long 1 s, 5 min, 2026, median % (n=47) | 6.3 | a_tick_long |
| the fast edge narrowing over time | Upbit KRW: tick long 2 s, 5 min, 2024, median % (n=24) | 6.1 | a_tick_long |
| the fast edge narrowing over time | Upbit KRW: tick long 2 s, 5 min, 2025, median % (n=62) | 0.3 | a_tick_long |
| the fast edge narrowing over time | Upbit KRW: tick long 2 s, 5 min, 2026, median % (n=47) | 0.0 | a_tick_long |
| the fast edge narrowing over time | Bithumb official: tick long 1 s, 5 min, 2024, median % (n=46) | 0.3 | a_tick_long |
| the fast edge narrowing over time | Bithumb official: tick long 1 s, 5 min, 2025, median % (n=83) | 4.3 | a_tick_long |
| the fast edge narrowing over time | Bithumb official: tick long 2 s, 5 min, 2024, median % (n=46) | -1.5 | a_tick_long |
| the fast edge narrowing over time | Bithumb official: tick long 2 s, 5 min, 2025, median % (n=83) | 2.1 | a_tick_long |
| when the move starts against the timestamp | Upbit KRW: first +2% print, 2024, median s after the timestamp | 0.9 | a_speed |
| when the move starts against the timestamp | Upbit KRW: first +2% print, 2025, median s after the timestamp | 1.0 | a_speed |
| when the move starts against the timestamp | Upbit KRW: first +2% print, 2026, median s after the timestamp | 0.8 | a_speed |
| when the move starts against the timestamp | Bithumb official: first +2% print, 2024, median s after the timestamp | 0.7 | a_speed |
| when the move starts against the timestamp | Bithumb official: first +2% print, 2025, median s after the timestamp | 2.5 | a_speed |
| when the move starts against the timestamp | Binance spot with prior perp: first +2% print, median s after releaseDate | 2.3 | b_speed |
| timestamps that arrive after the move | Bithumb v1 third-party times: drift in the 60 s before, median % | 5.4 | a_speed |
| timestamps that precede the visible post | Upbit API: our first sight minus first_listed_at, s (non-listing notices) | 6.8;7.6 | g_poll_logs |
| newly listed perps too volatile to short with a stop | Binance perp listings: share touching +20% within 24 h, % | 40.9 | b_short_funding_touch |
| newly listed perps too volatile to short with a stop | Binance perp listings: share touching +50% within 24 h, % | 15.2 | b_short_funding_touch |

- Funding is as large as the edge (measured). On Upbit KRW the 24 h short paid a mean 3.4% in funding. That is more than the unstopped mean result of 0.2% and about the size of the stopped mean of 3.1%.
- Books are thinner in 2026 (measured, section 4D).
- The fast edge is narrowing (measured). The Upbit KRW 2 s median went from 6.1% in 2024 to 0.0% in 2026.
- Timestamps may precede the visible post (inferred). On Bithumb's official 2025 times the first +2% print comes a median 2.5 s after the timestamp. On Binance it comes 2.3 s after releaseDate. A reader polling the page cannot act before the post is visible, so the usable window is shorter than the timestamp suggests.
- Newly listed perps spike too often to short with a stop (measured, section 4B).

## 5. Tests performed



| Test | Result | Detail |
|---|---|---|
| row counts against row_counts.json | pass | 56 tables compared; mismatches: none |
| events_metrics reproduction (delayed entry, close of the candle after the trigger minute) | pass | 1274 (event, entry) pairs with stored candles; 1256 covered by the stored window through +24 h (726 events, 7536 returns); 1256 match exactly (|diff| < 1e-9); mismatches: none; 18 not covered (trading open more than about 48 h after the announcement, beyond the stored +72 h window) |
| suspect ticks with and without | pass | 64 flagged ticks removed in the "without" run; 450 tick result rows compared; rows that changed: 0 |
| both stop versions computed | pass | mean of pessimistic minus exact fill, +20% stop, pp: Bithumb 60m -0.24; Bithumb 240m -0.28; Bithumb 1440m -0.29; Upbit BTC/USDT only 60m +0.07; Upbit BTC/USDT only 240m +0.15; Upbit BTC/USDT only 1440m +0.25; Upbit KRW 60m -0.07; Upbit KRW 240m -0.06; Upbit KRW 1440m +0.03 |
| period split (v1 against v2+v3, n >= 20 each) | pass | 293 strategies; 34 survive; labels: single period 96, no 85, n<20 in one period 55, survives 34, negative in both 23 |
| calendar-year split of survivors | pass | survivors with a non-positive median in a year with n >= 20: 3 of 34 |
| outlier removal | pass | survivors whose median or mean turns non-positive without outlier_flag: 0 of 34 |
| top-5 removal | pass | survivors whose mean turns non-positive without their 5 best events: 8 of 34 |
| Bithumb official against third-party times | pass | 54 of 64 v1 Bithumb events matched to an archived official notice; third-party minus official: median 1.35 s, p10 0.96 s, p90 1.85 s |
| reference values compared | pass | 93 reference values checked: 61 match within rounding, 32 differ (each explained in the appendix) |


Also run:
- `scripts/15_check_dataset.py` passes, so no data table and no v1/v2/v3 row changed.
- Every tick result was computed twice, with and without the 64 suspect ticks. The two runs match.
- The reference comparison is in the appendix.

## 6. How to execute (playbook, described, not built)

**Fast long on Upbit KRW notices.**
- Detection: poll the Upbit notice API from a server in Seoul or Tokyo every 0.5 s, within Upbit's published rate limits, with keep-alive connections. The open question is how long the public API takes to serve a new notice after its `first_listed_at`. The first non-listing rows took several seconds (section G).
- Path: notice JSON, then parse the title for "신규 거래지원" or "디지털 자산 추가" and the KRW market, then map the ticker, then a pre-signed order to the Binance spot API (else the USD-M perp).
- Latency budget, with a go/no-go threshold of 1 s total from `first_listed_at` to the fill: API visibility, then parse and decision under 5 ms, then order send and acknowledgement under 50 ms from Tokyo. If the measured median total is above 1 s, do not trade.
- Order: an IOC limit order at most 2% above the last trade, so a late fill does not chase the spike.
- Exit: market or IOC at 5 minutes.
- Size cap: 10k USD per event (section 4D).
- Log per event: `first_listed_at`, first sight, order send, acknowledgement, fill time and price, exit price, fees, and the Binance last trade at each step.

**Short after the trading open on Upbit KRW and Bithumb.**
- Entry: from 15 minutes before the open to the open, on the Binance USD-M perp, else Bybit.
- Stop: +20% above the entry, placed with the entry.
- Funding check before entry: skip if the current rate is at the venue's cap (2% per interval on Bybit today) or the next payment is against the short by more than 0.5%.
- Size: at most 15k USD notional on Upbit KRW and 10k USD on Bithumb. Keep the loss at the stop, about 20–35% of notional with gaps, under 1–2% of capital per trade.
- Skip when there is no perp, when funding is at the cap, or when the entry would be more than an hour after the open.

**Fast long on Bithumb notices.** Same path, polling Bithumb's feed, with a smaller edge (section 2, card 5) and the single-period caveat. Paper-trade only. Size cap 5k USD.

**Venue options.**
- **Binance or Bybit:** they have the perps for most events (section C), the ticks and books measured here, and Bybit's limits shown in section 4A. Unmeasured: our own order latency to them.
- **Hyperliquid with local signing:** HL perps covered 34% of Upbit KRW events. Volume is a fraction of Binance, and funding is similar (section F). Local signing avoids an exchange API key with withdrawal rights. Unmeasured: ticks, 1-minute prices, books and latency.

**Paper-trading protocol (4–8 weeks).**
- Record per event: every field in the latency log above, plus the would-be entry and exit prices from the live book and the funding at entry.
- Before any real size:
  - The fast long needs a measured end-to-end latency under 1 s on at least 10 real listings. It also needs a realised median of at least 5.0% and a win rate of at least 68%, the v1 values.
  - The short needs a realised median of at least 2.9% and a win rate of at least 56%, the v1 values.

**Position sizing.** Tie every size to the measured depth and flow in section 4D, and recompute them each month. The 2026 book is thinner than 2024–2025: Upbit KRW ask depth within 1% has a median of 57.3k USD in 2026, against 195.5k in 2024–2025.

## 7. What the data cannot answer, and the data still needed

In priority order:
1. Our own latency from Asia on real listing notices.
2. When each notice becomes visible against its official time, on Upbit, Bithumb and Binance.
3. Official Bithumb times for 2026.
4. A spot order book, and a tick-level book, around announcements.
5. Hyperliquid ticks and 1-minute candles.
6. Funding for the remaining events.
7. Solana swaps and full BSC swaps.
8. 1-minute candles for delisted coins.
9. Binance max leverage, and the history of the limits.

## 8. Reproduction

From a clean checkout with `data/` present (no network access is needed):

```
python3 -m venv .venv && .venv/bin/pip install pandas pyarrow numpy
for f in scripts/20_final_*.py; do .venv/bin/python "$f" || break; done
.venv/bin/python scripts/15_check_dataset.py
```

The scripts run in name order:
- `20_final_a_korean.py`, `20_final_b_other.py`, `20_final_c_strategy.py`, `20_final_d_liquidity.py`, `20_final_e_risk.py`, `20_final_f_hyperliquid.py`, `20_final_g_latency.py` and `20_final_h_patterns.py` write the section CSVs.
- `20_final_t_tests.py` runs the tests and the reference comparison.
- `20_final_z_report.py` writes this file and the `final_report` key of `data/summary.json`.

Data row counts are in `row_counts.json` and are checked in section 5. The expected analysis CSV row counts:


| File | Rows |
|---|---|
| a_bithumb_window.csv | 30 |
| a_bithumb_window_events.csv | 141 |
| a_delayed_long.csv | 200 |
| a_open_long.csv | 162 |
| a_perp_limits.csv | 6 |
| a_robust.csv | 52 |
| a_short_grid.csv | 756 |
| a_short_no_funding.csv | 4 |
| a_short_open.csv | 441 |
| a_short_open_funding_touch.csv | 9 |
| a_short_open_trades.csv | 7,903 |
| a_speed.csv | 23 |
| a_speed_events.csv | 350 |
| a_tick_long.csv | 900 |
| a_tick_long_trades.csv | 12,924 |
| b_delayed.csv | 238 |
| b_short.csv | 1,091 |
| b_short_funding_touch.csv | 50 |
| b_short_trades.csv | 9,193 |
| b_speed.csv | 19 |
| b_tick_long.csv | 360 |
| b_tick_long_trades.csv | 3,564 |
| c_long_short_availability.csv | 8 |
| d_book.csv | 132 |
| d_book_events.csv | 3,246 |
| d_dex_events.csv | 57 |
| d_dex_gross.csv | 9 |
| d_dex_gross_events.csv | 93 |
| d_dex_impact.csv | 5 |
| d_dex_impact_swaps.csv | 29,813 |
| d_dex_summary.csv | 4 |
| d_fillable.csv | 192 |
| d_fillable_events.csv | 11,136 |
| d_gas_assumptions.csv | 3 |
| d_size_caps.csv | 5 |
| e_concentration.csv | 8 |
| e_no_open_candles.csv | 8 |
| e_survivorship.csv | 4 |
| e_survivorship_events.csv | 886 |
| e_worst_events.csv | 8 |
| f_coverage.csv | 11 |
| f_funding_volume.csv | 3 |
| f_short.csv | 76 |
| f_short_events.csv | 99 |
| g_poll_logs.csv | 5 |
| h_patterns.csv | 31 |
| strategy_table.csv | 293 |
| t_bithumb_time_check.csv | 54 |
| t_data_coverage.csv | 9 |
| t_data_facts.csv | 11 |
| t_metrics_reproduction.csv | 1,274 |
| t_reference_diff.csv | 93 |
| t_tests.csv | 10 |
| trades_a.csv | 15,316 |
| trades_b.csv | 11,621 |


## Appendix: differences from the reference analysis

An independent analysis of the same data gave reference values, stored in `scripts/final_reference_values.csv`. They are used only as a check. The reference values are not computed here. A value matches if it is within one unit of the reference's last printed digit (n must match exactly). 93 reference values checked: 61 match within rounding, 32 differ (each explained in the appendix). The ones that differ, with their cause:


| Item | Reference | This report | Cause |
|---|---|---|---|
| Upbit KRW tick 1 s 5 min: n | 132.00 | 133.00 | H0051 is included here: its Binance spot ticks give an entry at +1 s and candles give the exit, but the ticks stop before +60 s, so it has no speed profile. The reference appears to require the full tick window (it reports 132 for both). |
| Upbit KRW tick 0.5 s 5 min: median | 16.50 | 16.12 | One extra event (H0051, see the n row) shifts the median. |
| Upbit KRW tick 0.5 s 5 min: mean | 29.00 | 28.77 | One extra event (H0051). |
| Upbit KRW tick 1 s 5 min: mean | 20.90 | 20.75 | One extra event (H0051). |
| Upbit KRW tick 1 s 5 min v1: median | 5.60 | 4.97 | H0051 is a v1 event (n 53 here against 52), which moves the v1 median. |
| Upbit KRW tick 2 s 5 min: median | 1.20 | 0.98 | One extra event (H0051). |
| Upbit KRW tick 1 s 5 min 2026: median | 6.50 | 6.30 | H0051 (2026) is included here. |
| Bithumb third-party: drift in the 60 s before | 5.80 | 5.40 | Same 37 events. The reference may take the price at -60 s from the first trade in the tick window rather than the last trade at or before -60 s; not confirmed. |
| Bithumb long at the open 24 h: median | -9.86 | -8.90 | Not explained. n (248) and the mean (-9.78) match the reference, so the event set is the same; the median here is computed directly from events_metrics.start_lst_n1440. No variant tried (high-of-candle entry, external venue) reproduces -9.86. |
| Bithumb window: long median | -0.52 | -0.27 | Not explained. Same 141 events and the same mean (1.17). Exiting at the open of the opening minute instead of the close of the minute before gives the same median here. |
| Bithumb window: short median | -0.98 | -1.27 | Follows the long difference; the means match (-2.78 against -2.79). |
| Bithumb window: last hour mean | -0.27 | -0.92 | Definition: here the entry is the delayed entry after the minute 61 minutes before the open, so the hour includes one extra minute of costs-free drift; an open-to-open variant gives a mean of -0.84. The reference definition of this leg is not stated. |
| Upbit KRW short 24 h: funding paid mean | 3.50 | 3.40 | Not explained. Summing over [entry, exit] or from the trading open instead of (entry, exit] gives the same 3.40 here, so the cause is upstream of the window (for example a different funding table or interval handling). |
| Upbit KRW short 24 h: funding paid median | 1.49 | 1.26 | See the mean row. |
| Binance perp listing tick 1 s on spot: n | 35.00 | 36.00 | One more event here has a spot tick entry and an exit candle (35 events have a full 60 s speed profile, matching the reference). |
| Binance perp listing tick 1 s on spot: mean | 11.00 | 12.18 | The extra event (see the n row) is a large winner. |
| Binance perp listing short 24 h no stop: n | 257.00 | 259.00 | Inferred: two more events here have a 24 h return in events_metrics; the reference may have dropped events without funding rows or without candles. |
| OKX short external perp 24 h: n | 23.00 | 22.00 | Inferred: the short here uses events_metrics.start_ext_ only when the external venue at the open is a Binance or Bybit USDT perp. v1 OKX and Bybit events have no stored perp candles, so a short on a perp that existed but was not the first external venue cannot be priced from data/. The reference likely priced those from another source. |
| OKX short external perp 24 h: median | 6.70 | 7.76 | See the n row. |
| Bybit short external perp 24 h: n | 57.00 | 46.00 | See the OKX n row: same venue rule. |
| Bybit short external perp 24 h: median | 1.50 | 1.90 | See the OKX n row. |
| Upbit KRW perp ask depth within 1% 2026: p25 USD k | 33.00 | 27.85 | Inferred: the reference may use a different quantile method or the closest snapshot rather than the last one at or before the announcement; the median (57) matches. |
| Upbit KRW spot 5 s flow before +2%: median USD k | 129.00 | 127.39 | Inferred: the window here starts at the first trade at or after the announcement and stops before the first trade above +2%; counting the first trade strictly after the announcement, or including the crossing trade, moves the median by about 1%. |
| DEX: buy impact under 1k (%) | 0.06 | 0.03 | Inferred: impact here is each buy's price against the previous swap of either side in the same pool, ordered by block and log index. A previous-buy or previous-block reference gives larger values. |
| DEX: buy impact 5k-20k (%) | 0.94 | 0.83 | See the under-1k row. |
| DEX: buy impact 20k-100k (%) | 4.18 | 2.86 | See the under-1k row; buys of 100k or more are a separate bucket here. |
| DEX: measured over constant-product ratio (5k or more) | 0.64 | 0.59 | See the under-1k row. |
| Survivorship: delisted D+1 median | 0.40 | -0.57 | Here an event needs a daily candle on the announcement day itself (39 events at D+1 against 45). The reference likely started from the first available daily candle, which adds six events that began trading after that day. |
| Survivorship: included D+1 n | 451.00 | 847.00 | Here every event with 1-minute candles covering the next UTC day is included (Binance spot candles first, else the perp). The reference set of 451 is smaller; its rule is not stated. |
| HL: Upbit KRW coarse short median | 3.90 | 3.65 | Inferred: entry and exit candles. Here the exit is the close of the HL candle containing entry + 24 h, so with 4 h candles the hold runs up to 28 h. |
| HL: Binance 1m entry at the open on the same events: mean | 2.10 | 0.88 | Same 61 events and the same 1-minute short as section A; the reference set of 61 may differ by a few events. |
| HL: 24 h volume against Binance | 0.09 | 0.06 | Inferred: here volume is the median per-event ratio of sum(volume x close) on HL candles to the same on Binance 1-minute candles over the first 24 h after the open. A ratio of totals or of means gives a larger value. |

