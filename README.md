# Listing pump study: public dataset

How do coins move after an exchange announces a new listing, and after trading opens? This dataset covers 1,494 listing events on Upbit, Bithumb, Binance (spot and USD-M perps), OKX, Bybit and Coinbase, plus 1-minute candles, funding history and tick-level trades around them. The original 467 events (v1) run from Nov 2025 to Nov 2026. The v2 collection adds 364 events from Jan 2024 onwards, plus Hyperliquid and DEX tables. The v3 collection adds 663 events from 2024 to 2025 (Bithumb, OKX, Bybit and Binance perp listings), on-chain DEX swaps, order-book depth, funding gaps and forward-only latency logs. See [v2 collection](#v2-collection-2026-11-13) and [v3 collection](#v3-collection-2026-11-14).

It is research data only. No trades were placed, and none of it is investment advice.

## Headline results
These are the v1 results (467 events). The v2 numbers are under the `v2` and `v1_plus_v2` keys of `data/summary.json`, and the v3 numbers are under `v3`.

All returns are net of a 0.6% round-trip cost.
- **Upbit KRW listing notices.** The coin jumps on Binance spot by a median of about 16% within 2 seconds. In tick data, half of the first-minute move happens in a median of 0.9 s (29 Upbit KRW events).
  - With an instant buy at the price just before the notice, the median 5-minute net return is +16.3%.
  - Buying at the close of the announcement minute gives a median of -0.6%.
- **Buying when trading opens.** On Upbit KRW the 1-hour median is -4.1% and the 24-hour median is -17.7% (85 events). Bithumb's 1-hour median is -5.5% (63 events).
- **Coinbase.** The only exchange where buying at the open was mildly positive: +0.6% median after 1 hour (90 events). The result is driven by outliers.
- **Binance, OKX, Bybit.** No edge after costs.

## Layout
- `data/`: one table per file, in Parquet (primary) and CSV. A CSV larger than 90 MB is shipped gzipped as `.csv.gz`.
- `data/summary.json`: the summary numbers behind the original study page.
- `scripts/`: the full pipeline. See `STUDY_RUN_NOTES.md` for the run order.
- `DATA_DICTIONARY.md`: every table and column.
- `row_counts.json`: rows per table.

Every timestamp is UTC epoch milliseconds in an integer column whose name ends in `_ms`. Durations are named `*_min` or `*_s`. Returns are fractions, so 0.05 means +5%.

## Tables
| Table | Rows | What it holds |
|---|---|---|
| events | 1,494 | One row per listing: exchange, symbol, market type, announcement and trading-open times, measurement venue, outlier flag |
| events_metrics | 1,494 | Every per-event metric (returns at 1/5/15/60/240/1440 min, peak, time to peak, drawdowns) for three entry types |
| events_source_list | 1,494 | The merged event list before any metrics were computed |
| excluded_events | 2,384 | Every exclusion or missing-data case, with its reason. Use it to measure survivorship bias |
| korean_perp_status | 353 | For each Upbit and Bithumb event: whether a USDT-M perp existed on Binance or Bybit at the announcement, which venue, and the perp's listing time |
| perp_candles_1m | 534,943 | v1: 1-minute candles of that perp, from 60 min before the announcement to 72 h after (123 events) |
| spot_candles_1m | 268,279 | v1: 1-minute Binance spot candles over the same window, where the market exists (62 events) |
| funding_history | 2,773 | v1: Funding rates of those perps over the same window (119 of 123 events) |
| aggtrades_index | 942 | One row per event and tick venue, with its tick count: the 161 v1 speed-test candidates, 468 v2 rows and 313 v3 rows |
| aggtrades | 2,596,728 | v1: Binance aggTrades from 60 s before to 90 s after each announcement (157 of 161 events have ticks) |
| speed_test_tick_entry | 57 | The original tick-level speed test (Binance spot) |
| speed_test_1m_entry | 243 | Speed sensitivity measured on 1-minute candles |
| exit_rule_grid_trades | 51,825 | Simulated trades for the take-profit / stop-loss / time-exit grid |
| coinsentry_alerts | 69 | Our CoinSentry alert log, reduced to exchange, symbol, pairs and times |
| coinsentry_latency | 59 | CoinSentry detection time vs the official announcement time (or the first trade, for live alerts). 40 alerts are matched |
| perp_candles_1m_v2_<year> | 210,240 (2024) + 363,540 (2025) | v2 Korean events: perp 1-minute candles, 60 min before to 72 h after |
| perp_candles_1m_other_v2_<year> | 70,080 (2024) + 459,900 (2025) + 188,340 (2026) | Binance USD-M perp 1-minute candles around Binance-spot and Coinbase announcements |
| spot_candles_1m_v2_<year> | 169,215 (2024) + 325,766 (2025) | v2 Korean events: Binance spot 1-minute candles |
| funding_history_v2_<year> | 665 (2024) + 3,365 (2025) + 432 (2026) | Funding for v2 Korean and Binance-spot events |
| aggtrades_v2_<year> | 1,690,483 (2024) + 5,882,839 (2025) + 1,105,300 (2026) | Binance spot and USD-M perp aggTrades, 60 s before to 90 s after, for every venue that existed (Korean, Binance-spot, Coinbase events) |
| btc_candles_1m_<year> | 293,460 (2024) + 516,840 (2025) + 728,692 (2026) | BTCUSDT perp 1-minute benchmark, same window as each Korean event |
| hyperliquid_perp_status | 353 | Hyperliquid perp at each Korean announcement, listing time, stored candle interval |
| hyperliquid_candles | 6,162 | Hyperliquid candles at the finest available interval, 60 min before to 72 h after |
| hyperliquid_funding | 8,045 | Hyperliquid hourly funding over the same window |
| dex_pool_status | 602 | Token contract per chain (CoinGecko), deepest pool created before the announcement, pool creation time, and (v3) pool liquidity at the announcement block where readable |
| dex_candles | 1,313 | 1-minute USD candles of that pool, 2 min before to 10 min after (last 180 days only) |
| upbit_poll_log | grows | Our forward-only Upbit notice detection log, extended in v3 with Binance round trips and book captures |
| binance_poll_log, bithumb_poll_log | grows | Forward-only detection logs for Binance announcements and Bithumb's official notices API |
| perp_status_v3 | 663 | Perp availability at each v3 announcement (Binance USD-M, Bybit) |
| perp_candles_1m_v3_<year> | 607,347 (2024) + 1,027,654 (2025) | v3 events: perp 1-minute candles, 60 min before to 72 h after |
| spot_candles_1m_v3_<year> | 413,563 (2024) + 544,306 (2025) | v3 events: Binance spot 1-minute candles |
| aggtrades_v3_<year> | 1,139,889 (2024) + 2,063,102 (2025) | v3 events: Binance spot and USD-M perp aggTrades, 60 s before to 90 s after |
| funding_history_v3_<year> | 2,379 (2024) + 7,019 (2025) + 1,959 (2026) | Funding for every event with a USDT perp that had none before (v1, v2 and v3) |
| book_snapshots | 39,304 | Order-book depth around announcements: USD-M bookDepth bands (archive) and forward REST/websocket levels |
| book_index | 564 | Book coverage per event and venue |
| aggtrades_suspect_ticks | 64 | Isolated prints more than 20% away from both neighbours, flagged and kept |
| delisted_daily_candles | 1,353 | DAILY candles for events with no 1-minute candles on the listing market. Not comparable with the 1-minute metrics |
| dex_swaps | 69,985 | On-chain swaps, 2 min before to 10 min after, for 57 events (Ethereum, Base, recent BSC) |
| perp_limits_snapshots | grows daily | Binance and Bybit USDT-perp limits: leverage, order and position caps, funding interval and caps |
| bithumb_wayback_notices | 2,564 | Every Bithumb notice found in Wayback captures of feed.bithumb.com, with Bithumb's own publication time |

## v2 collection (2026-11-13)
Every table that got new rows has a `collection_batch` column (`v1` or `v2`). v1 values are unchanged, with two exceptions where an official announcement time replaced the old one:
- Bithumb DNA: the old time is kept in `v1_announcement_ms`. It is the only one of the 64 v1 Bithumb events that the official API still returns.
- 83 v1 Coinbase events now have an official announcement time, where v1 had none.

`announcement_time_official` says which times come from the exchange itself. Large tables keep their v1 file. Their v2 rows are in `<table>_v2_<year>` files, split by the year of the announcement, and every file is under 50 MB.

**What was added**
- **Upbit**: 176 listing events from 2024-01-01 to 2025-10-31 (119 KRW, 57 BTC/USDT-only), taken from the official notices API (`first_listed_at`). Relistings, such as OMNI, ALT, POKT and BIGTIME, are separate events.
- **Korean market data** (all 353 Upbit and Bithumb events):
  - `korean_perp_status` adds the v2 rows and `binance_spot_listing_ms`.
  - Perp, spot and funding rows for v2 events.
  - New `btc_candles_1m_<year>` (BTCUSDT perp, from 60 min before to 72 h after).
  - aggTrades on both Binance spot and Binance USD-M perp wherever the market existed at the announcement.
- **Hyperliquid**: `hyperliquid_perp_status` (98 of 353 events had a perp at the announcement), `hyperliquid_candles` and `hyperliquid_funding` (hourly). Candle history is limited to the latest ~5000 candles per interval. Each event stores the finest interval that reaches its window and names it in `interval`. For 2024–2025 events that is mostly 4h.
- **DEX**: `dex_pool_status` covers 602 event–chain rows. 274 of the 353 Korean events have a pool on at least one of Solana, Base, BSC or Ethereum. `dex_candles` holds 1,313 one-minute candles for 94 events. See the limits below.
- **Binance spot listings with a perp already trading**, 2024-01 to today: 46 new events plus 20 v1 events. Announcements come from catalog 48, covering both "Binance Will List" and the HODLer Airdrops, Launchpool and Megadrop posts (`announcement_source` says which). They come with perp aggTrades, perp candles in `perp_candles_1m_other_v2_<year>` and funding.
- **Coinbase**, 2024-01 to today: 227 listings, timed by the first update of the official Coinbase Exchange status-page incident ("Coinbase will add support for…"). 142 are new events. `coinbase_full_trading_ms` is the full-trading update, and `coinbase_usd_product_status_now` flags the 11 listings delisted since. Each comes with Binance aggTrades and perp candles where those markets existed.
- **Upbit poll log**: `scripts/12_upbit_poll.py` writes `data/upbit_poll_log.csv` going forward. The current host is a macOS laptop in Esquel, Chubut, Argentina, on a residential ISP (AS27983). Latency from Korea or a nearby cloud region will be much lower.

**Sources that failed or were partial**
- **Bithumb 2024-01 to 2025-10: not collected.** feed.bithumb.com returns 403 to automated reads. The official API (`feed-api.bithumb.com/v1/notices`) returns only the latest notices. No browser session was available, and the Wayback Machine was offline. Only DNA got an official time.
- **Robinhood: not collected.** No official timestamped listing feed could be reached.
- **Hyperliquid trades: not built.** There is no public historical trade API.
- **DEX per-swap trades: not built.** GeckoTerminal's public trades cover only the last 24 h. `dex_candles` holds 1-minute pool candles instead, and only for announcements inside the public API's 180-day window. Pool liquidity is today's reserve, not the reserve at the announcement. Contracts come from CoinGecko's own Upbit and Bithumb ticker lists. A coin that is no longer listed has no mapping and is logged in `excluded_events`.
- **CoinSentry latency: not extended.** The private Worker credentials were not available.
- **Binance spot REST aggTrades** returns nothing for older windows. Those ticks were refilled from the `data.binance.vision` spot archives, whose timestamps are microseconds from 2025 and are converted to ms.
- **Coinbase metrics**: `04_metrics` skips external-venue entries for Coinbase (the v1 method), so `ann_ext_` is empty for Coinbase even where an official time now exists.
- **OKX and Bybit**: nothing new was collected, as asked.

## v3 collection (2026-11-14)
v3 rows carry `collection_batch = "v3"`. No v1 or v2 row changed. The only exception is `dex_pool_status.liquidity_usd_at_ann`, which v3 fills where it was empty. `scripts/15_check_dataset.py` compares every v1 and v2 row and file with main commit f1cc253. Large tables are in `<table>_v3_<year>` files, and every file is under 50 MB. Each task below is marked done, partial or failed.

**What was added**
- **1. Own latency (partial, forward-only).**
  - `12_upbit_poll.py` is extended, and `16_binance_poll.py` (catalog 48, `first_seen_ms` next to `releaseDate`) and `17_bithumb_poll.py` (official notices API) are new.
  - On a listing notice, each poller records the round trip of Binance's spot and USD-M `time` endpoints and starts a book capture.
  - Binance's test-order endpoints need an API key, so that round trip is logged as unavailable.
  - The logs start 2026-11-13 and hold no listing yet. The first rows show Upbit serving a notice 6.8 s after its `first_listed_at`, and Bithumb's API serving one 22.7 min after its `published_at`, both from Argentina.
  - The runbook for Seoul or Tokyo is in `STUDY_RUN_NOTES.md`.
- **2. Order books (partial).**
  - data.binance.vision publishes `bookDepth` (cumulative depth within ±1–5%, about every 30 s) for USD-M perps only. `book_snapshots` has it for 542 of 564 perp tick windows; the other 22 have no archive file.
  - There is no spot book archive, and futures `bookTicker` stops in 2024-03.
  - Forward REST depth plus 5 minutes of `depth20@100ms` start automatically on each new listing notice.
- **3. Funding gaps (done, OKX partial).**
  - `funding_history_v3_<year>` holds 11,357 rows for 608 of the 1,170 events that had no funding. That is 522 events on Binance, 84 on Bybit and 2 on OKX.
  - OKX keeps only recent months, so 31 OKX windows are logged as missing.
  - The Hyperliquid archive is requester-pays, so it was not read.
- **4. OKX, Bybit and Binance perp history (done).**
  - 454 events from 2024-01-01 to 2025-10-31: Bybit spot 241, Binance USD-M perp 168 and OKX spot 45.
  - They come from the same official announcement APIs as v1, with the v1 metrics, perp status, candles, funding and aggTrades.
- **5. Bithumb 2024–2025 (done).**
  - Wayback captures of feed.bithumb.com yielded 2,564 notices from 1,574 usable pages. 181 market-addition notices fall in the period, which gives 209 KRW events.
  - The time is the `publicationDateTime` from Bithumb's own page served by the Wayback Machine, so `announcement_time_official` is True and `announcement_source` is `bithumb_page_via_wayback`.
  - The archive also covers 54 of the 64 v1 Bithumb events. Their third-party times trail the official time by a median of 1.35 s. v1 rows were left as they were.
- **6. Delisted coins (partial).**
  - `delisted_daily_candles` covers 45 of 84 events: Binance spot or USD-M daily candles for the exact market, else CoinGecko.
  - CryptoCompare now needs an API key, and CoinGecko's public API serves only the last 365 days.
- **7. DEX on-chain (partial).**
  - `dex_swaps` holds 69,985 swaps for 57 events, read with `eth_getLogs` from keyless public RPCs: Ethereum 30 of 33 pools, Base 31 of 31, BSC 9 of 44.
  - Swap prices match `dex_candles` within 4% in 54 of 55 pools. The exception is a single swap in a 77%-fee pool.
  - `liquidity_usd_at_ann` is filled for 41 pools from token balances at the last block before the announcement.
- **8. Short-side limits (done, forward-only).** `perp_limits_snapshots` takes one snapshot per UTC day (1,480 perps on 2026-11-13). Binance max leverage needs a signed call, so it stays empty.
- **9. Data quality (done).**
  - `aggtrades_suspect_ticks` flags 64 isolated prints. H0194 BABYUSDT accounts for 16, all inside one 0.2 s burst about 1 s after the announcement.
  - No tick was deleted.
  - Announcement-time precision per source is in `DATA_DICTIONARY.md`.

**Sources that failed or were partial**
- **Binance test orders: not recorded.** `api/v3/order/test` and `fapi/v1/order/test` are SIGNED endpoints.
- **Spot order books: not available.** data.binance.vision has no spot `bookDepth` or `bookTicker`. Perp history is in ±% bands, not price levels.
- **Hyperliquid archive: not read.** The S3 buckets are requester-pays (AWS-billed).
- **OKX funding before the last few months: not available** from the public API.
- **Solana swaps: not collected** (29 pools). The free public RPC has no time-indexed history.
- **BSC swaps: partial** (35 of 44 pools missing). Keyless BSC RPCs either prune history (bloXroute keeps a few weeks) or rate-limit `eth_getLogs` (BlastAPI, drpc).
- **Curve pools: not decoded** (2 pools).
- **Liquidity at the announcement** is missing for Uniswap v4 and PancakeSwap Infinity pools. Their singleton contract holds every pool's tokens.
- **Delisted daily: partial.** 39 events have no source: they are not on Binance, and the CoinGecko id is unknown or older than 365 days. CryptoCompare needs a key.
- **Binance max leverage: not recorded.** `fapi/v1/leverageBracket` is SIGNED.
- **Paid routes that would close these gaps:**
  - An archive RPC plan (Alchemy, QuickNode, or a publicnode token) for BSC swaps and v4 liquidity.
  - A Solana indexer (Helius, Bitquery) for Solana swaps.
  - Hyperliquid's requester-pays S3 for its candles and trades.
  - CoinGecko or CryptoCompare paid plans for older delisted coins.

## Speed test: 57 vs 29 events, and the expanded tick set
- **57** is the full original tick test. It includes every event whose external buy venue at the announcement was Binance spot and which had a trade before the announcement: Upbit KRW 29, Upbit BTC/USDT-only 12, Bithumb 10, OKX 5, Bybit 1.
- **29** is the Upbit KRW subset. The study page charted only that subset because it is the decision-relevant group.
- The original test used Binance spot only. Binance's REST endpoint `fapi/v1/aggTrades` serves just the last 2 days, so ticks for perp-venue events weren't available then.
- For this release, ticks were fetched for every speed-test candidate: 161 events.
  - 62 have Binance spot as the venue. 61 of those have ticks via REST.
  - 99 have a Binance USD-M perp as the venue. 96 of those have ticks from the `data.binance.vision` daily aggTrades archives.
  - Missing ticks: USDS (spot, no trades in the window), and XCN, B3 and PUFFER (no perp archive file).
- The 104 extra events are not part of the published speed-test results. `aggtrades_index.in_original_speed_test` marks which events are.

## Sources
- **Announcements**
  - Upbit notices API: `api-manager.upbit.com`, field `first_listed_at`.
  - Binance CMS catalog 48: `releaseDate`.
  - OKX `api/v5/support/announcements`: `pTime`.
  - Bybit `v5/announcements`: `publishTime`.
  - Bithumb: the official API returns only the latest 20 notices and the notice site blocks automated reads. Bithumb times therefore come from the CryptoListing.ws public archive (`cryptolisting.ws/data/recent-announcements.json`, detection time of the official notice). This covers Apr–Nov 2026 only.
  - Coinbase: no announcement feed. A listing is the first daily candle of a USD product after 2025-11-01.
- **Prices**: public 1-minute candles from Upbit, Bithumb, Binance (`data-api.binance.vision`, `fapi`), OKX `history-candles`, Bybit `v5/market/kline` and Coinbase Exchange.
- **Ticks**: Binance spot `aggTrades` (REST) and `data.binance.vision/data/futures/um/daily/aggTrades`.
- **Funding**: Binance `fapi/v1/fundingRate` and `fapi/v1/fundingInfo`; Bybit `v5/market/funding/history` and `instruments-info` (`fundingInterval`, `launchTime`).
- **Perp listing time**: Binance `exchangeInfo.onboardDate` (or the first daily kline for a delisted symbol); Bybit `launchTime`.
- **CoinSentry**: our own webhook log. Only exchange, symbol, pairs, event type and times are published.

## Methodology
- **Trading open** is the first 1-minute candle on the listing market within 10 days of the announcement.
- **Entries**: there are three kinds, each with a realistic delay. The buy is at the close of the minute after the trigger minute, so 60–120 s late.
  - `ann_ext_`: at the announcement, buy on an external venue where the coin already trades. Venues are tried in this order: Binance spot, Binance perp, Bybit spot, OKX spot, Bybit perp, Upbit, Bithumb, Coinbase.
  - `start_lst_`: at trading open, buy on the listing exchange itself.
  - `start_ext_`: at trading open, buy on the external venue.
- **Return columns**: `_hi` columns assume a pessimistic fill at the entry candle's high. `r*` columns are gross returns; `n*` columns are net of the 0.6% round trip (0.1% fee plus 0.2% slippage per side).
- **Peak and drawdown** are measured within 24 h of entry. An event is flagged as an outlier if its peak is above +200% or its 24 h move is beyond ±100%.
- **Already trading elsewhere** means at least 3 one-minute candles on an external venue in the 3 h before the announcement.
- **Funding interval**
  - `funding_interval_hours` is inferred from the gaps between consecutive funding timestamps, so `funding_interval_inferred` is True for every row.
  - Where the venue publishes the interval, `current_venue_interval_hours` holds today's value from Binance `fundingInfo` or Bybit `instruments-info`. Historical intervals can differ.
  - If an event has only one funding row, the interval falls back to the venue value or to Binance's 8 h default (see `funding_interval_source`).

## Limits
- **Survivorship**: markets delisted on Upbit, Bithumb or Coinbase return no candles, so losers are under-represented. See `excluded_events`.
- **Bithumb** v1 events (Apr–Nov 2026) use third-party times, except DNA. The v3 events (2024–2025) use Bithumb's own archived times. See `announcement_time_official`.
- **Coinbase** v1 events had no announcement times. v2 adds official status-page times, but we didn't check whether its coins already traded elsewhere.
- **Resolution**: 1-minute candles can't resolve fills inside a minute. Only the aggTrades table can.
- **Upbit notice times** have 1-second precision.
- **Sample size**: groups are small (13–93 events) and come from a single year. Nothing here is a validated trading strategy.
- **Symbol mapping**: Upbit's name-clash suffix "2" (MET2, META2, UP2, AMP2) is stripped to match external tickers, which may mismatch.

## Reproducing
Use Python 3.11+ with `requests pandas numpy pyarrow`. Run `scripts/01`–`07` in order; `STUDY_RUN_NOTES.md` has the details.

`01_extract_alerts.py` needs private `WORKER_BASE_URL` and `WORKER_READ_TOKEN` env vars and is included for transparency only. Everything else uses public endpoints.

Exchange data belongs to the respective exchanges; check their terms before commercial use.
