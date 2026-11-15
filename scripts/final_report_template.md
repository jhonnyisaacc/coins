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

1. Trade, in paper first: the fast long on Upbit KRW listing notices, only if the order reaches Binance within 1 s of the notice (median {{upbit_krw_fast_long_1s_5m_median=a_tick_long#kgroup=Upbit KRW&&L=1&&hold_min=5&&drop_suspect=False&&split=all#median}}% at 1 s, {{upbit_krw_fast_long_2s_5m_median=a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=all#median}}% at 2 s).
2. Trade, in paper first: the 24 h short after the Upbit KRW trading open, always with a +20% stop (median {{upbit_krw_short_open_24h_stop20_median=strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#median}}%, mean {{upbit_krw_short_open_24h_stop20_mean=strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#mean}}%, positive in both periods).
3. Do not trade: any long entered a minute or more after an announcement, any long at a trading open, any short without a stop, and shorts on newly listed Binance perps.
4. Bithumb's fast long and stopped short, and the Binance spot fast long, are candidates with reservations: one period only, a weak period, or a small sample.
5. Reasonable maximum size (inferred): about {{size_cap_upbit_krw_fast_long_k=d_size_caps#strategy=Upbit KRW fast long#cap_k#.0f}}k USD per event for the Upbit KRW fast long and {{size_cap_upbit_krw_short_k=d_size_caps#strategy=Upbit KRW short after the open#cap_k#.0f}}k USD notional for the Upbit KRW short. That is half of the thinner of the 2026 order-book depth and the measured early flow (section 4D).

## 2. Recommendations, ranked

Each card gives the period tested, the main reason it could fail, and the numbers behind it. v1 is November 2025 to November 2026. v2+v3 is January 2024 to October 2025, plus {{t_data_facts#key=v2_events_after_oct_2025#value#int}} v2 Binance-spot and Coinbase events dated after October 2025. "Survives" means the median and the mean are both positive in v1 and in v2+v3, with n ≥ 20 in each.

### Supported in both periods

**1. Fast long on Upbit KRW notices (Binance spot, else perp, entry 1 s after the notice, exit after 5 min).**
- What happens (measured): the price on Binance moves a median {{a_speed#kgroup=Upbit KRW&&split=all#m2_median}}% in the first 2 s and {{a_speed#kgroup=Upbit KRW&&split=all#m60_median}}% by 60 s. Half the 60 s move is done after {{a_speed#kgroup=Upbit KRW&&split=all#t_half_median_s#.2f}} s. A buyer at 1 s still catches part of it.
- Why (inferred): Upbit KRW listings bring new Korean demand, and the fastest traders buy the coin wherever it already trades.
- Results: {{table#strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#n:n,win:Win %,median:Median,mean:Mean,p10:p10,p90:p90,worst:Worst,v1_n:v1 n,v1_median:v1 median,v1_mean:v1 mean,v23_n:v2+v3 n,v23_median:v2+v3 median,v23_mean:v2+v3 mean}}
- Typical bad trade: p10 {{upbit_krw_fast_long_1s_5m_p10=strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#p10}}%. Worst: {{upbit_krw_fast_long_1s_5m_worst=strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#worst}}%.
- Needs: measured end-to-end latency under 1 s from the notice to a filled order. At 2 s the median is {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=all#median}}% overall and {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=v1#median}}% in v1.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: our own latency is unmeasured on a real listing (section G). The edge is shrinking: the 1 s median is {{a_tick_long#kgroup=Upbit KRW&&L=1&&hold_min=5&&drop_suspect=False&&split=2025#median}}% in 2025 and {{a_tick_long#kgroup=Upbit KRW&&L=1&&hold_min=5&&drop_suspect=False&&split=2026#median}}% in 2026.
- Invalidated by: a paper-trading median below {{strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#v1_median}}% (the v1 median) over at least 10 listings, or a measured latency above 1 s.

**2. Short after the Upbit KRW trading open (USDT perp on Binance, else Bybit, entry at the close of the minute after the open, 24 h hold, +20% stop).**
- What happens (measured): after the open, the coin tends to fall. A long on Upbit at the open has a median 24 h result of {{a_open_long#ogroup=Upbit KRW&&metric=start_lst_n1440&&subset=all&&split=all#median}}%. The short catches the same fall on the perp.
- Why (inferred): the announcement pump is already priced in by the open, and early buyers sell into the new Korean liquidity.
- Results, pessimistic stop fill: {{table#strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#n:n,win:Win %,median:Median,mean:Mean,p10:p10,p90:p90,worst:Worst,v1_n:v1 n,v1_median:v1 median,v1_mean:v1 mean,v23_n:v2+v3 n,v23_median:v2+v3 median,v23_mean:v2+v3 mean}}
- Typical bad trade: p10 {{upbit_krw_short_open_24h_stop20_p10=strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#p10}}%. Worst: {{upbit_krw_short_open_24h_stop20_worst=strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#worst}}%, because a 1-minute candle can close far above the stop.
- Needs: a USDT perp at the open, a stop placed on entry, and a funding check. The short paid a mean {{a_short_open_funding_touch#grp=Upbit KRW&&hold_min=1440#funding_paid_mean}}% in funding over 24 h, and paid funding in {{a_short_open_funding_touch#grp=Upbit KRW&&hold_min=1440#share_short_pays#.0f}}% of events.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: the result rests on a few big falls. The top 5 events are {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#top5_share#.0f}}% of the total, and the mean without them is {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#mean_ex_top5}}%. The worst run of losses cost {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#max_drawdown_pp#.0f}} percentage points.
- Invalidated by: a paper-trading median below {{strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#v1_median}}% (the v1 median), or funding regularly at the cap.

**3. Fast long on Binance spot listings of coins that already have a Binance perp (perp ticks, entry 1 s after releaseDate, 5 min hold).**
- What happens (measured): the perp moves a median {{b_speed#group=Binance spot with prior perp&&split=all#m5_median}}% in the first 5 s. The first +2% print comes a median {{b_speed#group=Binance spot with prior perp&&split=all#t_first2_median_s}} s after releaseDate.
- Results: {{table#strategy_table#strategy=Binance spot with prior perp | long | tick 1s | 5m#n:n,win:Win %,median:Median,mean:Mean,p10:p10,p90:p90,worst:Worst,v1_n:v1 n,v1_median:v1 median,v23_n:v2+v3 n,v23_median:v2+v3 median}}
- Typical bad trade: p10 {{strategy_table#strategy=Binance spot with prior perp | long | tick 1s | 5m#p10}}%. Worst: {{strategy_table#strategy=Binance spot with prior perp | long | tick 1s | 5m#worst}}%.
- Needs: detection of the catalog-48 post within about 1 s. At 3 s the median is {{b_tick_long#group=Binance spot with prior perp&&L=3&&hold_min=5&&split=all#median}}%, and at 5 s {{b_tick_long#group=Binance spot with prior perp&&L=5&&hold_min=5&&split=all#median}}%.
- Period tested: 2024-01 to 2026-11. Main reason it could fail: v1 has exactly {{strategy_table#strategy=Binance spot with prior perp | long | tick 1s | 5m#v1_n#n}} events, the minimum for this label. The 2026 perp book is thin: ask depth within 1% has a p25 of {{d_book#kgroup=Binance spot&&side=ask&&band_pct=1&&period=2026#depth_k_p25}}k USD.

### Supported with reservations

**4. Short after the Bithumb trading open (24 h, +20% stop, pessimistic fill).** Results: {{table#strategy_table#strategy=Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic#n:n,win:Win %,median:Median,mean:Mean,p10:p10,worst:Worst,v1_n:v1 n,v1_median:v1 median,v1_mean:v1 mean,v23_n:v2+v3 n,v23_median:v2+v3 median}}
It survives, but v1 is weak (median {{strategy_table#strategy=Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic#v1_median}}%). The top 5 events are {{e_concentration#strategy=Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic#top5_share#.0f}}% of the total. The worst stopped trade returned {{bithumb_short_open_24h_stop20_worst=strategy_table#strategy=Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic#worst}}%, because the price jumped through the stop inside one minute. Period tested: 2024-01 to 2026-11, pooling v1 and v3. Main reason it could fail: the v1 edge is close to zero.

**5. Fast long on Bithumb notices (official times, entry 1 s after the notice, 5 min hold).** Results: {{table#strategy_table#strategy=Bithumb official | long | tick 1s | 5m#n:n,win:Win %,median:Median,mean:Mean,p10:p10,p90:p90,worst:Worst}}
By year: 2024 median {{bithumb_official_fast_long_1s_2024_median=a_tick_long#kgroup=Bithumb official&&L=1&&hold_min=5&&drop_suspect=False&&split=2024#median}}% (n {{a_tick_long#kgroup=Bithumb official&&L=1&&hold_min=5&&drop_suspect=False&&split=2024#n#n}}), 2025 median {{bithumb_official_fast_long_1s_2025_median=a_tick_long#kgroup=Bithumb official&&L=1&&hold_min=5&&drop_suspect=False&&split=2025#median}}% (n {{a_tick_long#kgroup=Bithumb official&&L=1&&hold_min=5&&drop_suspect=False&&split=2025#n#n}}). Official Bithumb times exist only for 2024–2025, so this cannot be checked across periods. Treat it as a paper-trade candidate only. Main reason it could fail: no official-time test after October 2025.

**6. Short on the Binance perp after a Binance spot open, for coins that already had a perp (24 h, +20% stop).** Results: {{table#strategy_table#strategy=Binance spot with prior perp | short | spot open +1m on perp | 1440m | stop +20% pessimistic~Binance spot with prior perp [HODLer Airdrops] | short | spot open +1m on perp | 1440m | stop +20% pessimistic~Binance spot with prior perp [Binance Will List] | short | spot open +1m on perp | 1440m | stop +20% pessimistic#group:Subset,n:n,win:Win %,median:Median,mean:Mean,worst:Worst,v1_n:v1 n,label:Label}}
The HODLer Airdrops subset is stronger but exists only in v2. Main reason it could fail: small v1 sample.

### Watch, do not trade yet

**7. Short on the Binance perp after Coinbase full trading (24 h, no stop).** {{table#strategy_table#strategy=Coinbase | short | full trading +1m on Binance perp | 1440m | stop none~Coinbase | short | full trading +1m on Binance perp | 1440m | stop +20% pessimistic#strategy:Strategy,n:n,median:Median,mean:Mean,v1_n:v1 n,v1_median:v1 median,v1_mean:v1 mean,label:Label}}
v1 is negative on the mean. The price barely reacts to the announcement itself (Binance perp 60 s move median {{b_speed#group=Coinbase (Binance perp ticks)&&split=all#m60_median#.2f}}%).

**8. Short on an external perp after an OKX spot open (24 h).** {{table#strategy_table#strategy=OKX spot | short | open +1m on external perp (events_metrics) | 1440m | stop none#n:n,median:Median,mean:Mean,v1_n:v1 n,v23_n:v2+v3 n,label:Label}}
The sample is too small in both periods.

### Not recommended

{{table#strategy_table#strategy=Upbit KRW | long | announcement +1m delayed | 60m~Upbit KRW | long | announcement +1m delayed | 1440m~Upbit KRW | long | trading open +1m on listing exchange | 1440m~Bithumb | long | trading open +1m on listing exchange | 1440m~Upbit KRW | short | trading open +1m on perp | 1440m | stop none~Binance perp listing | short | perp open +1m on listed perp | 1440m | stop +20% pessimistic~Binance perp listing | short | perp open +1m on listed perp (events_metrics) | 1440m | stop none~Bybit spot | long | open +1m on listing exchange | 1440m~Bithumb official | short | announcement +1m delayed on perp | until open#strategy:Strategy,n:n,median:Median,mean:Mean,worst:Worst,label:Label}}

- A long one minute late misses most of the Upbit KRW move. The median missed move is {{a_delayed_long#kgroup=Upbit KRW&&metric=missed_move&&split=all#median}}% (measured).
- New tokens fall harder after the open. The Upbit KRW 24 h long has a median of {{a_open_long#ogroup=Upbit KRW&&metric=start_lst_n1440&&subset=new_token&&split=all#median}}% (n {{a_open_long#ogroup=Upbit KRW&&metric=start_lst_n1440&&subset=new_token&&split=all#n#n}}), and Bithumb {{a_open_long#ogroup=Bithumb&&metric=start_lst_n1440&&subset=new_token&&split=all#median}}% (n {{a_open_long#ogroup=Bithumb&&metric=start_lst_n1440&&subset=new_token&&split=all#n#n}}). This favours the short, but only with a stop.
- A short without a stop has a good median and a very bad tail. On Upbit KRW, {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop none#losses_beyond_50#int}} of {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop none#n#int}} trades lost more than 50%, and the worst returned {{e_concentration#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop none#worst}}%.

## 3. Data

- **Coverage (measured).** The dataset holds {{t_data_facts#key=events_total#value#int}} listing announcements from {{t_data_facts#key=v3_first_date#value#s}} to {{t_data_facts#key=v1_last_date#value#s}}:
{{table#t_data_coverage##group:Group,v1:v1,v2:v2,v3:v3,total:Total#int}}
- **The three collections.** v1 runs {{t_data_facts#key=v1_first_date#value#s}} to {{t_data_facts#key=v1_last_date#value#s}} and covers every group. v2 adds Upbit from 2024, plus Binance spot and Coinbase announcements from 2024 to today. v3 adds OKX, Bybit and Binance-perp listings, and Bithumb with official times, for 2024-01 to 2025-10. It also adds order-book depth, funding gaps, DEX swaps and the forward pollers. README.md describes the sources.
- **Known gaps.**
  - No Robinhood.
  - No spot order book. `book_snapshots` is USD-M perp depth only.
  - Hyperliquid has mostly 4 h candles before 2026.
  - No Solana swaps, and BSC swaps are partial.
  - Coinbase `ann_ext_` columns are empty by method: no external entry was taken at Coinbase announcements.
  - Delisted coins are under-represented (section E).
  - {{t_data_facts#key=events_still_without_funding#value#int}} events still have no funding rows. Where a perp short is priced on such an event, funding counts as zero, and the events are listed in `analysis/a_short_no_funding.csv` ({{z_csv_rows#file=a_short_no_funding.csv#rows#int}} Korean events).

## 4. Measurements

### Method

- **Costs:** 0.6% round trip on every trade. Returns are fractions in the data and percentages here.
- **Delayed entry:** the close of the 1-minute candle after the trigger minute, 60 to 120 s after the trigger. This is how `events_metrics` is built. Section 5 shows it reproduces the table exactly.
- **Tick entry at latency L:** the first Binance aggTrade at or after announcement + L, for L in 0, 0.5, 1, 2, 3, 5, 10, 30 and 60 s. The exit is the open of the 1-minute candle 5 or 60 minutes after the entry minute, on the same venue. Each event gets one row, from Binance spot ticks if there are any, else Binance perp.
- **Short:** −r − 0.6% + funding received, where r is the price return over the hold. Funding is summed over (entry, exit]. Only events with a USDT perp on Binance or Bybit at the entry count. A perp that is not listed yet has no candle at the entry minute.
- **Stops** at +10/+20/+50% come in two fills. The exact fill exits at the stop price. The pessimistic fill exits at the close of the first 1-minute candle whose high touches the stop.
- **Period split:** v1 against v2+v3 uses `collection_batch`. Year splits use the UTC calendar year of the announcement (or of the trading open, for the {{t_data_facts#key=events_without_announcement_time#value#int}} Coinbase events without an announcement time).

### A. Korean listings

**Long at the announcement, delayed (1-minute candles, external venue).**
{{table#a_delayed_long#metric=n5~n60~n1440~n60_hi~missed_move&&split=all#kgroup:Group,metric:Measure,n:n,median:Median,mean:Mean,win:Win %,p10:p10,p90:p90,worst:Worst}}
`n60_hi` buys at the high of the entry candle. `missed_move` is the gross move from the last candle before the announcement to the delayed entry. All values are measured.

**Long at the announcement by latency (ticks, 5 min hold).**
{{table#a_tick_long#kgroup=Upbit KRW~Bithumb official~Upbit BTC/USDT only~Bithumb third-party&&hold_min=5&&drop_suspect=False&&split=all&&L=0~0.5~1~2~3~5~10~30~60#kgroup:Group,L:Latency s,n:n,median:Median,mean:Mean,win:Win %,p10:p10,p90:p90,worst:Worst}}

By period and year at 1 s:
{{table#a_tick_long#kgroup=Upbit KRW~Bithumb official~Upbit BTC/USDT only&&hold_min=5&&drop_suspect=False&&L=1&&split=v1~v2+v3~2024~2025~2026~no_outlier#kgroup:Group,split:Split,n:n,median:Median,mean:Mean,win:Win %}}

The Upbit KRW 2 s result by year: 2024 {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=2024#median}}%, 2025 {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=2025#median}}%, 2026 {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=2026#median}}% (measured). Bithumb third-party times are v1 only and are not a fair test of speed (see below).

**Speed of the move (ticks).** Price relative to the last trade before the announcement, in percent (medians). The share columns use events whose 60 s move is above 2%.
{{table#a_speed#split=all~v1~v2+v3#kgroup:Group,split:Split,n:n,m1_median:1 s,m2_median:2 s,m5_median:5 s,m30_median:30 s,m60_median:60 s,share_m1_median:Share at 1 s,share_m2_median:Share at 2 s,t_half_median_s:Half move s,t_first2_median_s:First +2% s,drift_pre60_median:Drift before}}
- Upbit KRW against Bithumb on official times (measured): the median 60 s move is {{a_speed#kgroup=Upbit KRW&&split=all#m60_median}}% on Upbit KRW and {{a_speed#kgroup=Bithumb official&&split=all#m60_median}}% on Bithumb. Upbit's first +2% print comes {{a_speed#kgroup=Upbit KRW&&split=all#t_first2_median_s#.2f}} s after the notice time, and Bithumb's {{a_speed#kgroup=Bithumb official&&split=all#t_first2_median_s#.2f}} s after.
- Bithumb's v1 third-party times arrive after the move (measured). Prices already drifted a median {{a_speed#kgroup=Bithumb third-party&&split=all#drift_pre60_median}}% in the 60 s before those timestamps, against {{a_speed#kgroup=Bithumb official&&split=all#drift_pre60_median#.2f}}% before the official times. Official against third-party times: {{t_tests#test=Bithumb official against third-party times#detail#s}}.

**Long at the trading open (`start_lst_` on the listing exchange, `start_ext_` on an external venue).**
{{table#a_open_long#split=all#ogroup:Group,metric:Measure,subset:Subset,n:n,median:Median,mean:Mean,win:Win %,p10:p10,worst:Worst}}

**Bithumb's window between the announcement and the open, on the perp (official times).** The median lag is {{a_bithumb_window#metric=long&&split=all#lag_median_min#.0f}} minutes. The long and short run from the delayed entry after the announcement to the close of the minute before the open. Peak and trough are the highest high and lowest low inside the window, gross. The last hour is a long from about 60 minutes before the open to the open.
{{table#a_bithumb_window#split=all~2024~2025#metric:Measure,split:Split,n:n,median:Median,mean:Mean,win:Win %,p10:p10,p90:p90,worst:Worst}}
Neither side of the window is a reliable trade (measured). The long's median is {{a_bithumb_window#metric=long&&split=all#median}}% with a win rate of {{a_bithumb_window#metric=long&&split=all#win#.0f}}%, and its positive mean of {{a_bithumb_window#metric=long&&split=all#mean}}% comes from a few large moves. The short loses on both the median and the mean.

**Shorts after the open (perp, funding included).**
{{table#a_short_open#grp=Upbit KRW~Bithumb&&split=all&&stop=none~+20%#grp:Group,hold_min:Hold min,stop:Stop,mode:Fill,n:n,median:Median,mean:Mean,win:Win %,p10:p10,worst:Worst}}

By period and year, 24 h with a +20% pessimistic stop:
{{table#a_short_open#grp=Upbit KRW~Bithumb&&hold_min=1440&&stop=+20%&&mode=pessimistic&&split=v1~v2+v3~2024~2025~2026~no_outlier#grp:Group,split:Split,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}

Funding and stop touches over the hold (no stop):
{{table#a_short_open_funding_touch##grp:Group,hold_min:Hold min,n:n,funding_paid_mean:Funding paid mean,funding_paid_median:Funding paid median,share_short_pays:% short pays,touch10:% touch +10%,touch20:% touch +20%,touch50:% touch +50%,losses_beyond_50:Losses beyond -50%}}

Entry-time grid, 24 h short (an entry before the open must still be after the announcement):
{{table#a_short_grid#hold_min=1440&&split=all#grp:Group,entry:Entry,stop:Stop,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}
On Upbit KRW, entries from 15 minutes before the open to the open are best. Later entries and entries at the announcement are worse (measured).

**Perp limits (`perp_limits_snapshots`, a snapshot of today, not history).**
{{table#a_perp_limits##ogroup:Group,venue:Venue,snapshot_date:Date,n_symbols_listed_now:Symbols listed now,max_leverage_median:Max leverage median,position_limit_usd_median:Position limit USD median,position_limit_usd_p10:Position limit USD p10,funding_cap_median:Funding cap % per interval,funding_interval_h_median:Funding interval h#.0f}}
Binance max leverage is missing because the endpoint is signed. Bybit's limits (inferred) are far above the sizes in section 4D, so the order book, not the exchange limit, is what binds.

**Robustness.**
{{table#a_robust##strategy:Strategy,split_by:Split by,value:Value,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}
BTC candles cover the v1 and v2 Korean events but not v3, so for Bithumb the excess-over-BTC rows cover only the v1 events (stated in the Value column).

### B. Other exchanges

**Delayed entries from `events_metrics`.**
{{table#b_delayed#split=all#group:Group,metric:Measure,n:n,median:Median,mean:Mean,win:Win %,p10:p10,worst:Worst}}

**Tick long by latency (5 min hold).**
{{table#b_tick_long#hold_min=5&&split=all&&L=0.5~1~2~3~5~30#group:Group,L:Latency s,n:n,median:Median,mean:Mean,win:Win %,p10:p10,worst:Worst}}

**Speed of the move.**
{{table#b_speed#split=all#group:Group,n:n,m1_median:1 s,m5_median:5 s,m60_median:60 s,drift_pre60_median:Drift before,t_first2_median_s:First +2% s,t_half_median_s:Half move s}}
On Binance spot listings with a perp, the move starts a median {{b_speed#group=Binance spot with prior perp&&split=all#t_first2_median_s}} s after releaseDate (measured).

**Shorts (perp, funding included).** Rows marked "(events_metrics)" use the stored `events_metrics` returns, because v1 Binance-perp, OKX and Bybit events have no stored perp candles. They have no stops. Section 5 shows the two methods agree exactly where both exist.
{{table#b_short#split=all&&hold_min=1440&&stop=none~+20%&&mode=none~pessimistic#group:Group,entry:Entry,sub:Subset,hold_min:Hold min,stop:Stop,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}

Funding and stop touches:
{{table#b_short_funding_touch#hold_min=1440#group:Group,entry:Entry,sub:Subset,n:n,funding_paid_mean:Funding paid mean,n_no_funding:No funding rows,touch20:% touch +20%,touch50:% touch +50%,losses_beyond_50:Losses beyond -50%}}

- Binance perp listings: the newly listed perp is too volatile to short with a stop. {{b_short_funding_touch#group=Binance perp listing&&entry=perp open +1m on listed perp&&sub=all&&hold_min=1440#touch20#.0f}}% of them touch +20% and {{b_short_funding_touch#group=Binance perp listing&&entry=perp open +1m on listed perp&&sub=all&&hold_min=1440#touch50#.0f}}% touch +50% within 24 h (measured).
- OKX and Bybit: the long at the open loses in both periods. The Bybit 24 h long has a v1 median of {{b_delayed#group=Bybit spot&&metric=start_lst_n1440&&split=v1#median}}% (n {{b_delayed#group=Bybit spot&&metric=start_lst_n1440&&split=v1#n#n}}) and v2+v3 {{b_delayed#group=Bybit spot&&metric=start_lst_n1440&&split=v2+v3#median}}% (n {{b_delayed#group=Bybit spot&&metric=start_lst_n1440&&split=v2+v3#n#n}}). More history makes it clearer, not better.
- Coinbase: the Binance perp barely moves in the 60 s after the announcement, and coins that are delisted now are listed separately in the tables.

### C. Strategy table

The full table, {{z_csv_rows#file=strategy_table.csv#rows#int}} strategies with per-year results, concentration, drawdown and losing streak, is `analysis/strategy_table.csv`. It is sorted by robustness: survives, n<20 in one period, single period, no, negative in both, then by the weaker period's median. The strategies that survive:
{{table#strategy_table#label=survives#strategy:Strategy,n:n,median:Median,mean:Mean,win:Win %,p10:p10,worst:Worst,v1_median:v1 median,v23_median:v2+v3 median,top5_share:Top-5 share %,max_drawdown_pp:Max drawdown pp,longest_losing_streak:Longest losing streak}}

**Where only a long or only a short is possible (at the announcement).** "Long" means the coin already trades on an external spot venue. "Short" means a Binance or Bybit USDT perp exists. The spot side is inferred from the first external venue found, so a coin with both a perp and spot elsewhere can show as short only.
{{table#c_long_short_availability##group:Group,long and short:Long and short,long only (no USDT perp):Long only,short only (no external spot):Short only,neither at the announcement:Neither,n:n#int}}

### D. Liquidity and size

**Order-book depth (USD-M perp, cumulative depth within the band, USD thousands).** The depth is the last snapshot at or before the announcement. The changes compare the first three snapshots after it. Treat depth as an upper bound on size, not as an impact model.
{{table#d_book#side=ask&&band_pct=1#kgroup:Group,period:Period,depth_k_n:n,depth_k_median:Median,depth_k_p25:p25,depth_k_p10:p10,after1_s_median:1st after s,change1_median_pct:Change %,after2_s_median:2nd after s,change2_median_pct:Change %,after3_s_median:3rd after s,change3_median_pct:Change %}}
Within ±2% and ±5%, and the bid side, are in `analysis/d_book.csv`. On Upbit KRW, ask depth within 1% changes a median {{d_book#kgroup=Upbit KRW&&side=ask&&band_pct=1&&period=all#change2_median_pct#.0f}}% by the second snapshot, about {{d_book#kgroup=Upbit KRW&&side=ask&&band_pct=1&&period=all#after2_s_median#.0f}} s after the notice (measured). Coinbase and Bybit books do not change. The 2026 books are thinner than 2024–2025 for Upbit KRW and Upbit BTC/USDT (measured). For Bithumb the 2024–2025 rows (official times) and the 2026 rows (third-party times) are different event sets, so the comparison is only indicative.

**Fillable size from ticks (USD thousands).** This is the whole market's flow, not one participant's fill: USD traded in the first 5 s from the first trade at or after announcement + L, until price first exceeds that trade's price by 2%.
{{table#d_fillable#window_s=5&&cap_pct=2&&kgroup=Upbit KRW~Bithumb official~Upbit BTC/USDT only~Binance spot~Coinbase spot#kgroup:Group,venue:Venue,L:Latency s,usd_k_n:n,usd_k_median:Median,usd_k_p25:p25,usd_k_p10:p10}}
The 30 s window and the 1% and 5% caps are in `analysis/d_fillable.csv`.

**DEX swaps** (one pool per event, the one with the most swaps).
{{table#d_dex_summary##kgroup:Group,n_enough:Events with swaps before and after,years:Years,n_onset_pairs:Onset pairs,dex_minus_binance_median_s:DEX onset minus Binance s,dex_after:DEX after,dex_before:DEX before,vol60_median_usd:Volume first 60 s USD,events_with_buys10k_pre:Events with a 10k+ buy before#.0f}}
- Timing (measured): the DEX +2% onset follows Binance's first +2% print by a median {{dex_onset_minus_binance_median_s=d_dex_summary#kgroup=all#dex_minus_binance_median_s}} s. All events with enough swaps are from 2026.
- Buys of 10k USD or more in the 2 minutes before the announcement (measured): none on Upbit events, and {{d_dex_summary#kgroup=Bithumb third-party#events_with_buys10k_pre#int}} of {{d_dex_summary#kgroup=Bithumb third-party#n_enough#int}} Bithumb events. Those Bithumb times are third-party and arrive after the move (section A), so a "before" buy may really come after the notice. The test cannot tell an early buyer from a late timestamp (inferred).
- Measured buy impact against the constant-product estimate size / (liquidity_usd_at_ann / 2):
{{table#d_dex_impact##bucket:Buy size USD,n:n,impact_median_pct:Measured impact % median,cp_estimate_median_pct:Constant-product estimate % median#.2f}}
Measured impact is {{d_dex_impact#bucket=<1k#measured_over_cp_ratio_ge5k#.2f}} of the estimate for buys of 5k USD or more. Liquidity today is {{d_dex_impact#bucket=<1k#liq_now_over_at_ann_median#.2f}} of liquidity at the announcement ({{d_dex_impact#bucket=<1k#liq_pools_both#int}} pools).
- Gross return to +5 min and the largest size still positive after costs. The cost is twice the measured median impact for that size plus gas for two swaps. Gas per swap is an assumption: {{table#d_gas_assumptions##chain:Chain,gas_usd_per_swap_assumed:Gas USD per swap (assumed)#.2f}}
{{table#d_dex_gross##kgroup:Group,L:Entry s after the notice,n:n,gross_median_pct:Gross median,net_median_pct_1k:Net 1k,net_median_pct_5k:Net 5k,net_median_pct_20k:Net 20k,net_median_pct_100k:Net 100k,largest_positive_size_usd:Largest positive size USD}}
The Upbit KRW rows have n {{d_dex_gross#kgroup=Upbit KRW&&L=0#n#n}}. The DEX edge is gone within about 12 s (measured, small sample).

**Size caps (inferred rule).** The cap is half of the smaller of the 2026 depth within 1% (p25) and the 1-s-late 5 s flow (p25), rounded down to 5k USD.
{{table#d_size_caps##strategy:Strategy,inputs:Inputs,cap_k:Cap USD k#.0f}}

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
{{table#e_survivorship##source:Source,horizon:Horizon,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}
Share of events with no opening candles on the listing market:
{{table#e_no_open_candles##group:Group,n:n,no_open_candles:No opening candles,share_pct:Share %}}
Direction (inferred): on the only horizon both groups share, day one, the missing coins do no worse than the included ones (median {{e_survivorship#source=delisted_daily_candles&&horizon=d1#median}}% against {{e_survivorship#source=included, 1m candles&&horizon=d1#median}}%). The included events have 1-minute candles only to +72 h, so there is no included D+7 or D+30 to compare with. The missing coins keep falling afterwards (D+30 median {{e_survivorship#source=delisted_daily_candles&&horizon=d30#median}}%), so leaving them out most likely understates the short side and overstates the long side. The size is limited by how few they are, about {{e_no_open_candles#group=Upbit KRW#share_pct#.0f}}% of Upbit KRW and {{e_no_open_candles#group=Bithumb spot#share_pct#.0f}}% of Bithumb events.

**Concentration, drawdown and losing streaks.**
{{table#e_concentration##strategy:Strategy,n:n,median:Median,mean:Mean,worst:Worst,top5_share:Top-5 share %,mean_ex_top5:Mean without top 5,median_ex_top5:Median without top 5,max_drawdown_pp:Max drawdown pp,longest_losing_streak:Longest losing streak,losses_beyond_50:Losses beyond -50%}}
Drawdown is in percentage points of cumulative per-trade returns, one equal-size trade per event, in date order. The worst events:
{{table#e_worst_events##strategy:Strategy,event_id:Event,symbol:Symbol,exchange:Exchange,year:Year,ret_pct:Return %}}

### F. Hyperliquid as the only perp venue

**Coverage.** Hyperliquid perps at the announcement, for the {{f_coverage#group=All Korean&&year=all#n#int}} Korean events with an HL status (Upbit 2024–2026 and Bithumb v1). There is no HL status for Bithumb 2024–2025.
{{table#f_coverage##group:Group,year:Year,n:n,hl_perp_at_ann:HL perp at announcement,hl_only:HL only (no Binance or Bybit perp),hl_share_pct:Share %}}

**Coarse short (24 h from the open).** HL candles are 5 min to 8 h, so the entry is the close of the HL candle containing the open, and the exit is the close of the HL candle containing entry + 24 h. The same timestamps are priced on Binance, and compared with the 1-minute Binance entry on the same events.
{{table#f_short#split=all#grp:Group,measure:Measure,n:n,median:Median,mean:Mean,win:Win %,worst:Worst}}
{{table#f_funding_volume##grp:Group,n:n,hl_funding_paid_mean:HL funding paid mean %,binance_funding_paid_mean:Binance funding paid mean %,hl_over_binance_vol24_median:HL 24 h volume / Binance,intervals:HL candle intervals#.2f}}
On the same timestamps, HL and Binance shorts give nearly the same result (measured). The gap to the 1-minute Binance entry comes from the coarse entry. HL volume is a small fraction of Binance, so HL is a fallback venue, not a primary one (inferred). Not measurable here: HL ticks, HL 1-minute candles, HL order books, and HL status for Bithumb 2024–2025.

### G. Own latency

{{table#g_poll_logs##table:Log,rows:Rows:int,title:Notice,is_listing:Listing:s,lag_s:Seen after official time s,poll_interval_s:Poll interval s,http_elapsed_ms:HTTP ms:int,region:Region}}
The logs settle nothing yet. They hold no listing notice, they were polled from South America, far from the exchanges, and `binance_poll_log` is empty. The first Upbit rows show the public API serving a notice several seconds after its `first_listed_at`. That delay would by itself use up the whole 1 s budget of the fast long (inferred). Settling it needs at least 10 real listing notices polled from Seoul or Tokyo, with the delay from the official time to the first sight measured on each.

### H. Other patterns and risks

{{table#h_patterns##pattern:Pattern,measure:Measure,value:Value,source:Source CSV}}
- Funding is as large as the edge (measured). On Upbit KRW the 24 h short paid a mean {{a_short_open_funding_touch#grp=Upbit KRW&&hold_min=1440#funding_paid_mean}}% in funding. That is more than the unstopped mean result of {{a_short_open#grp=Upbit KRW&&hold_min=1440&&stop=none&&split=all#mean}}% and about the size of the stopped mean of {{a_short_open#grp=Upbit KRW&&hold_min=1440&&stop=+20%&&mode=pessimistic&&split=all#mean}}%.
- Books are thinner in 2026 (measured, section 4D).
- The fast edge is narrowing (measured). The Upbit KRW 2 s median went from {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=2024#median}}% in 2024 to {{a_tick_long#kgroup=Upbit KRW&&L=2&&hold_min=5&&drop_suspect=False&&split=2026#median}}% in 2026.
- Timestamps may precede the visible post (inferred). On Bithumb's official 2025 times the first +2% print comes a median {{a_speed#kgroup=Bithumb official&&split=2025#t_first2_median_s}} s after the timestamp. On Binance it comes {{b_speed#group=Binance spot with prior perp&&split=all#t_first2_median_s}} s after releaseDate. A reader polling the page cannot act before the post is visible, so the usable window is shorter than the timestamp suggests.
- Newly listed perps spike too often to short with a stop (measured, section 4B).

## 5. Tests performed

{{table#t_tests##test:Test,result:Result,detail:Detail}}

Also run:
- `scripts/15_check_dataset.py` passes, so no data table and no v1/v2/v3 row changed.
- Every tick result was computed twice, with and without the {{t_data_facts#key=suspect_ticks#value#int}} suspect ticks. The two runs match.
- The reference comparison is in the appendix.

## 6. How to execute (playbook, described, not built)

**Fast long on Upbit KRW notices.**
- Detection: poll the Upbit notice API from a server in Seoul or Tokyo every 0.5 s, within Upbit's published rate limits, with keep-alive connections. The open question is how long the public API takes to serve a new notice after its `first_listed_at`. The first non-listing rows took several seconds (section G).
- Path: notice JSON, then parse the title for "신규 거래지원" or "디지털 자산 추가" and the KRW market, then map the ticker, then a pre-signed order to the Binance spot API (else the USD-M perp).
- Latency budget, with a go/no-go threshold of 1 s total from `first_listed_at` to the fill: API visibility, then parse and decision under 5 ms, then order send and acknowledgement under 50 ms from Tokyo. If the measured median total is above 1 s, do not trade.
- Order: an IOC limit order at most 2% above the last trade, so a late fill does not chase the spike.
- Exit: market or IOC at 5 minutes.
- Size cap: {{d_size_caps#strategy=Upbit KRW fast long#cap_k#.0f}}k USD per event (section 4D).
- Log per event: `first_listed_at`, first sight, order send, acknowledgement, fill time and price, exit price, fees, and the Binance last trade at each step.

**Short after the trading open on Upbit KRW and Bithumb.**
- Entry: from 15 minutes before the open to the open, on the Binance USD-M perp, else Bybit.
- Stop: +20% above the entry, placed with the entry.
- Funding check before entry: skip if the current rate is at the venue's cap ({{a_perp_limits#ogroup=Upbit KRW&&venue=bybit_perp#funding_cap_median#.0f}}% per interval on Bybit today) or the next payment is against the short by more than 0.5%.
- Size: at most {{d_size_caps#strategy=Upbit KRW short after the open#cap_k#.0f}}k USD notional on Upbit KRW and {{d_size_caps#strategy=Bithumb short after the open#cap_k#.0f}}k USD on Bithumb. Keep the loss at the stop, about 20–35% of notional with gaps, under 1–2% of capital per trade.
- Skip when there is no perp, when funding is at the cap, or when the entry would be more than an hour after the open.

**Fast long on Bithumb notices.** Same path, polling Bithumb's feed, with a smaller edge (section 2, card 5) and the single-period caveat. Paper-trade only. Size cap {{d_size_caps#strategy=Bithumb fast long (paper only)#cap_k#.0f}}k USD.

**Venue options.**
- **Binance or Bybit:** they have the perps for most events (section C), the ticks and books measured here, and Bybit's limits shown in section 4A. Unmeasured: our own order latency to them.
- **Hyperliquid with local signing:** HL perps covered {{f_coverage#group=Upbit KRW&&year=all#hl_share_pct#.0f}}% of Upbit KRW events. Volume is a fraction of Binance, and funding is similar (section F). Local signing avoids an exchange API key with withdrawal rights. Unmeasured: ticks, 1-minute prices, books and latency.

**Paper-trading protocol (4–8 weeks).**
- Record per event: every field in the latency log above, plus the would-be entry and exit prices from the live book and the funding at entry.
- Before any real size:
  - The fast long needs a measured end-to-end latency under 1 s on at least 10 real listings. It also needs a realised median of at least {{strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#v1_median}}% and a win rate of at least {{strategy_table#strategy=Upbit KRW | long | tick 1s | 5m#v1_win#.0f}}%, the v1 values.
  - The short needs a realised median of at least {{strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#v1_median}}% and a win rate of at least {{strategy_table#strategy=Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic#v1_win#.0f}}%, the v1 values.

**Position sizing.** Tie every size to the measured depth and flow in section 4D, and recompute them each month. The 2026 book is thinner than 2024–2025: Upbit KRW ask depth within 1% has a median of {{d_book#kgroup=Upbit KRW&&side=ask&&band_pct=1&&period=2026#depth_k_median}}k USD in 2026, against {{d_book#kgroup=Upbit KRW&&side=ask&&band_pct=1&&period=2024-2025#depth_k_median}}k in 2024–2025.

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
{{table#z_csv_rows##file:File,rows:Rows#int}}

## Appendix: differences from the reference analysis

An independent analysis of the same data gave reference values, stored in `scripts/final_reference_values.csv`. They are used only as a check. The reference values are not computed here. A value matches if it is within one unit of the reference's last printed digit (n must match exactly). {{reference_check=t_tests#test=reference values compared#detail#s}}. The ones that differ, with their cause:
{{table#t_reference_diff#status=differs#item:Item,reference:Reference,ours:This report,cause:Cause#.2f}}
