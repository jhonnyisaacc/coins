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
