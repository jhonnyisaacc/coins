# Listing pump study (notify-only research, no trading)
Built 2026-11-13 by Lee for Jhonny. Re-run in order (Python 3.11+, `.venv` has requests/pandas/numpy):
1. `scripts/01_extract_alerts.py` – CoinSentry alerts from the Worker `/read` endpoint (private Worker URL/token via env vars, not published) -> `raw/coinsentry_alerts.csv` (sanitized: no webhook paths/headers).
2. `scripts/02a_upbit_notices.py` (Upbit official notices API), `scripts/02b_cex_announcements.py binance|okx|bybit` (official announcement APIs).
   Bithumb history: official notice API returns only the latest 20 and feed.bithumb.com blocks the box (403), so Bithumb announcement times come from the CryptoListing.ws public archive `raw/clw_recent_announcements.json` (detection time of the official notice, Apr–Nov 2026).
3. `scripts/03_build_events.py` -> `raw/events_base.csv`; `scripts/03b_coinbase_events.py` (Coinbase has no announcement API: listing = first daily candle of a USD product after 2025-11-01); `scripts/03c_merge_events.py` -> `raw/events_all.csv` (467 events).
4. `scripts/04_metrics.py <Exchange> [threads]` -> `out/metrics_<Exchange>.csv` (1-min candles, public APIs, cached in `raw/cache/`).
5. `scripts/05_simulate.py` TP/SL/time-stop grid -> `out/sim_trades.csv`; `scripts/05b_fast_entry.py` reaction-speed (1m) -> `out/fast_entry.csv`; `scripts/05c_tick_entry.py` tick-level (Binance aggTrades) -> `out/tick_entry.csv`.
6. `scripts/06_analysis.py` -> `out/events_metrics.csv` (one row per event, all metrics) and `out/summary.json`.

Conventions: returns are net of 0.6% round trip (0.1% fee + 0.2% slippage per side). Base entry = close of the 1-min candle after the trigger minute (60–120 s delay); `_hi` columns = pessimistic fill at that candle's high.
Entries: `ann_ext_` = at the announcement on an external venue where the coin already trades (order: Binance spot, Binance perp, Bybit spot, OKX spot, Bybit perp, Upbit, Bithumb, Coinbase); `start_lst_` = at trading start on the listing exchange; `start_ext_` = external venue at that trading start.
Limits: survivorship (delisted Upbit/Bithumb/Coinbase markets return no candles), Bithumb only Apr–Nov 2026, Binance perp aggTrades not returned so tick test is Binance-spot-only, 1-min candles cannot resolve sub-minute fills except in the tick test.

# v2 collection (2026-11-13)
Run from the repo root with `.venv/bin/python` (requests pandas numpy pyarrow). Raw downloads and caches go to `raw/`, `out/` and `extra/` (git-ignored).
0. `mkdir -p raw/v1 && for t in events events_metrics events_source_list korean_perp_status aggtrades_index excluded_events; do git show e27214a:data/$t.parquet > raw/v1/$t.parquet; done`. The v2 scripts read v1 from these copies, never from `data/`.
1. `scripts/08a_upbit_notices_v2.py` (all Upbit trade notices), then `scripts/08b_upbit_events_v2.py` (listing events 2024-01-01..2025-10-31, one row per symbol, market type and notice, so relistings stay separate events).
2. `scripts/08c_metrics_v2.py` runs the v1 `04_metrics.run` on the Upbit v2 events.
3. `scripts/08d_korean_market_v2.py` builds perp status, Binance spot listing time, perp, spot and BTC 1m candles, funding, and aggTrades on both Binance spot and USD-M perp for every Korean event. Then `scripts/08e_spot_ticks_archive.py extra/v2/aggtrades_index.parquet extra/v2/aggtrades.parquet` refills spot ticks that REST no longer serves, from data.binance.vision spot archives.
4. `scripts/09_hyperliquid.py`: Hyperliquid perp status, candles and funding.
5. `scripts/10a_coinbase_status.py` (Coinbase Exchange status page incidents), `scripts/10b_binance_announcements_v2.py` (catalog 48 since 2024), `scripts/10c_other_events_v2.py` (Binance spot with a perp at the announcement, Coinbase official times), `scripts/10e_metrics_other_v2.py`, `scripts/10d_other_market_v2.py`, then `08e` again on `extra/v2/other_aggtrades_index.parquet extra/v2/other_aggtrades.parquet`.
6. `scripts/11_dex.py`: CoinGecko contracts and GeckoTerminal pools and 1m candles. It is rate-limited and takes about 2–3 h.
7. `scripts/13_build_publish_v2.py` writes `data/`, `row_counts.json` and `out/file_sizes.json`. Then `scripts/14_summary_v2.py` adds the v2 keys to `data/summary.json`.
8. `scripts/12_upbit_poll.py --region "<where it runs>" --interval 0.5` runs forward-only. The endpoint answered 429 at about 4 requests per second from the collection host, so 0.5 s is the default.
9. `scripts/15_check_dataset.py` is the local check. It verifies row counts, the 50 MB limit, integer `*_ms` columns, unique event ids, and that v1 rows equal commit e27214a apart from the documented announcement-time replacements.
