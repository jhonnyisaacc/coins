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

# v3 collection (2026-11-13)
Run from the repo root with `.venv/bin/python` (requests pandas numpy pyarrow websocket-client). Raw downloads and caches go to `raw/`, `out/` and `extra/` (git-ignored). The v3 build reads the v2 publication from `raw/v2pub` (copied from main commit f1cc253), never from `data/`.
1. Forward pollers (keep running): `scripts/12_upbit_poll.py`, `scripts/16_binance_poll.py`, `scripts/17_bithumb_poll.py`, sharing `scripts/poll_common.py`. Each logs new notices with `first_seen_ms`, `region`, `poll_interval_s` and `http_elapsed_ms`. On a listing notice each one also records Binance spot and USD-M `time` round trips and starts a book capture (REST depth, then 5 minutes of `depth20@100ms`) into `raw/forward/book/`.
2. `scripts/18_book_depth_archive.py`: USD-M `bookDepth` bands from data.binance.vision around every Binance-perp tick window (run again after step 5 so v3 windows are included).
3. `scripts/20_cex_announcements_v3.py` (OKX and Bybit announcements back to 2024), then `scripts/21_events_v3.py` (v3 events and v1 `04_metrics.run`).
4. `scripts/26_market_v3.py` (perp status, perp and spot candles, aggTrades), then `scripts/08e_spot_ticks_archive.py extra/v3/aggtrades_index.parquet extra/v3/aggtrades.parquet`.
5. `scripts/19_funding_v3.py`: funding for every event with a USDT perp and no published funding rows.
6. `scripts/22_bithumb_wayback.py` (Wayback CDX and captures, about 3 h at one request every 4 s), then `scripts/28_bithumb_events_v3.py` (Bithumb events, metrics and market data from the archived notices).
7. `scripts/23_delisted_daily.py`, `scripts/24_dex_swaps.py` (free public RPCs, about 1–2 h), `scripts/27_suspect_ticks.py`.
8. `scripts/25_perp_limits_snapshot.py` once per UTC day (forward-only; reruns on the same day are skipped).
9. `scripts/29_build_publish_v3.py` writes `data/`, `row_counts.json` and `out/file_sizes.json`. Then `scripts/30_summary_v3.py` adds the `v3` keys to `data/summary.json`.
10. `scripts/15_check_dataset.py` must print `all dataset checks passed`.

## Running the pollers on a server in Seoul or Tokyo
The collection host so far is a laptop in Argentina, about 0.4–0.6 s from Upbit and Binance. That latency is in every `first_seen_ms`, so use a host near the exchanges for measurements you plan to act on: AWS `ap-northeast-2` (Seoul) for Upbit and Bithumb, `ap-northeast-1` (Tokyo) for Binance, or one Seoul host for all three.
1. Create a small Linux VM (1 vCPU is enough) with Python 3.11+, and keep the clock synced: `timedatectl set-ntp true` (chrony on Amazon Linux). `first_seen_ms` is only as good as the clock.
2. `git clone` the repo, then `python3 -m venv .venv && .venv/bin/pip install requests pandas pyarrow websocket-client`.
3. Start each poller under systemd or tmux, with a region string that names the provider, region and host type:
   ```
   R="AWS ap-northeast-2 (Seoul), t3.small"
   .venv/bin/python scripts/12_upbit_poll.py   --region "$R" --interval 0.5 >> out/12_poll.log 2>&1
   .venv/bin/python scripts/16_binance_poll.py --region "$R" --interval 3.0 >> out/16_poll.log 2>&1
   .venv/bin/python scripts/17_bithumb_poll.py --region "$R" --interval 1.0 >> out/17_poll.log 2>&1
   ```
   Measured limits: Upbit returned 429 at about 4 requests per second, so keep it at 0.5 s or slower. Binance's CMS list answered 429 on a third of polls at 1 s, so use 3 s. Bithumb ran clean at 1 s.
4. Add a daily cron for the perp limits: `5 0 * * * cd ~/coins && .venv/bin/python scripts/25_perp_limits_snapshot.py >> out/25.log 2>&1`.
5. Every week, copy `data/*_poll_log.csv`, `data/perp_limits_snapshots.csv` and `raw/forward/book/` back, rerun the v3 build, and commit on a `chore/` branch through a PR (never directly to main).
6. Each log line has a UTC timestamp, and every 10 minutes the poller writes a heartbeat with poll and error counts. A gap in heartbeats means the poller was down for that interval, so treat no rows in that gap as "not observed", not "no notice".
