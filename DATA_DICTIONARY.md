# Data dictionary

All `*_ms` columns: UTC epoch milliseconds (nullable integer). Returns are fractions. Prefixes in events_metrics: `ann_ext_` = buy on external venue at announcement, `start_lst_` = buy on listing exchange at trading open, `start_ext_` = buy on external venue at trading open.


## aggtrades

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `symbol` | str | Ticker on the listing exchange |
| `agg_trade_id` | int64 | Binance aggregate trade id |
| `price` | float64 | Trade price |
| `qty` | float64 | Base-asset quantity |
| `timestamp_ms` | Int64 | Candle open / funding / trade time, UTC epoch ms |
| `is_buyer_maker` | bool | True = sell-initiated |

## aggtrades_index

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `market` | str | Venue market symbol |
| `announcement_ms` | Int64 | Announcement time, UTC epoch ms (null for Coinbase-derived events) |
| `n_ticks` | int64 | Ticks in window (ann-60s..ann+90s) |
| `source` | str | Where ticks came from |
| `in_original_speed_test` | bool | Event is one of the 57 in speed_test_tick_entry |

## coinsentry_alerts

| column | type | description |
|---|---|---|
| `alert_id` | int64 | CoinSentry alert record id in our log |
| `event` | str | CoinSentry event type |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `pairs` | str | Pairs reported by CoinSentry |
| `detected_ms` | Int64 | CoinSentry detectedAtMs |
| `trading_starts_ms` | Int64 | CoinSentry tradingStartsAtMs |
| `worker_recv_ms` | Int64 | Time our Worker received the webhook |

## coinsentry_latency

| column | type | description |
|---|---|---|
| `alert_id` | int64 | CoinSentry alert record id in our log |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `event` | str | CoinSentry event type |
| `detected_ms` | Int64 | CoinSentry detectedAtMs |
| `worker_recv_ms` | Int64 | Time our Worker received the webhook |
| `trading_starts_ms` | Int64 | CoinSentry tradingStartsAtMs |
| `worker_recv_minus_detected_ms` | Int64 | Delivery delay CoinSentry -> our Worker (duration in ms) |
| `reference` | str | announcement or first_trade_1m_candle |
| `reference_ms` | Int64 | Official announcement time (announced) or first trade (live) |
| `reference_source` | str | Source of reference_ms |
| `reference_is_official` | object | Reference is an official exchange time |
| `latency_ms` | Int64 | detected_ms - reference_ms |
| `reference_title` | str | Matched announcement title |
| `latency_vs_trading_starts_ms` | Int64 | detected_ms - CoinSentry tradingStartsAtMs |

## events

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `market_type` | str | KRW / USDT (Upbit, Bithumb market measured) or spot / perp |
| `quote` | str | Quote currency |
| `markets_opened` | str | Markets opened per notice |
| `announcement_ms` | Int64 | Announcement time, UTC epoch ms (null for Coinbase-derived events) |
| `announcement_source` | str | Where announcement_ms came from |
| `trading_open_ms` | Int64 | First 1m candle on the listing market |
| `measurement_venue` | str | Venue whose candles define trading_open and start_lst_* metrics |
| `measurement_market` | str | Listing market measured |
| `external_venue_at_announcement` | str | Venue used for ann_ext_* (coin already trading there) |
| `external_market` | str | External market symbol |
| `already_trading_elsewhere` | bool | External venue had >=3 candles in 3h before announcement |
| `outlier_flag` | bool | peak > +200% or |24h| > 100% at either entry |
| `record_source` | str | historical (public feeds) or coinsentry (our alert log only) |
| `notice_url` | str | Public notice URL |

## events_metrics

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `product` | str | spot or perp |
| `quote` | str | Quote currency |
| `markets` | str | Markets opened (Upbit) / pairs |
| `announcement_ms` | Int64 | Announcement time, UTC epoch ms (null for Coinbase-derived events) |
| `ann_source` | str | Where the announcement time came from |
| `title` | str | Announcement title |
| `url` | str | Public notice URL |
| `source` | str | Where ticks came from |
| `lst_venue` | str | Listing venue measured |
| `lst_market` | str | Listing market measured |
| `lst_existed_before` | bool | Listing market had candles before the announcement |
| `trading_open_ms` | Int64 | First 1m candle on the listing market |
| `ext_at_ann` | str | External venue used at announcement |
| `ext_market` | str | External market symbol |
| `already_trading_elsewhere` | bool | External venue had >=3 candles in 3h before announcement |
| `start_lst_entry_ms` | Int64 | Entry candle open time |
| `start_lst_entry_px` | float64 | Entry price (close of entry candle) |
| `start_lst_entry_px_high` | float64 | Pessimistic entry price (high of entry candle) |
| `start_lst_entry_delay_s` | float64 | Seconds from trigger to entry fill |
| `start_lst_r1` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r1_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r5` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r5_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r15` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r15_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r60` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r60_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r240` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r240_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r1440` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_r1440_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_lst_peak_gain` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `start_lst_peak_gain_hi` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `start_lst_t_peak_min` | float64 | Minutes from entry to the 24h peak |
| `start_lst_dd_before_peak` | float64 | Lowest low before the peak / entry - 1 |
| `start_lst_dd_after_peak` | float64 | Lowest low after the peak (within 24h) / peak - 1 |
| `start_lst_low24` | float64 | Lowest low within 24h / entry - 1 |
| `start_lst_peak60_gain` | float64 | First-hour peak / entry - 1 |
| `start_lst_t_peak60_min` | float64 | Minutes to first-hour peak |
| `lag_ann_to_start_min` | float64 | Minutes from announcement to trading open |
| `ann_ext_entry_ms` | Int64 | Entry candle open time |
| `ann_ext_entry_px` | float64 | Entry price (close of entry candle) |
| `ann_ext_entry_px_high` | float64 | Pessimistic entry price (high of entry candle) |
| `ann_ext_entry_delay_s` | float64 | Seconds from trigger to entry fill |
| `ann_ext_pre_px` | float64 | Close of the minute before the trigger |
| `ann_ext_missed_move` | float64 | entry / pre_px - 1 (move missed by the delay) |
| `ann_ext_trig_min_high_move` | float64 | High of the trigger minute / pre_px - 1 |
| `ann_ext_r1` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r1_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r5` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r5_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r15` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r15_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r60` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r60_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r240` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r240_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r1440` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_r1440_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `ann_ext_peak_gain` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `ann_ext_peak_gain_hi` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `ann_ext_t_peak_min` | float64 | Minutes from entry to the 24h peak |
| `ann_ext_dd_before_peak` | float64 | Lowest low before the peak / entry - 1 |
| `ann_ext_dd_after_peak` | float64 | Lowest low after the peak (within 24h) / peak - 1 |
| `ann_ext_low24` | float64 | Lowest low within 24h / entry - 1 |
| `ann_ext_peak60_gain` | float64 | First-hour peak / entry - 1 |
| `ann_ext_t_peak60_min` | float64 | Minutes to first-hour peak |
| `start_ext_entry_ms` | Int64 | Entry candle open time |
| `start_ext_entry_px` | float64 | Entry price (close of entry candle) |
| `start_ext_entry_px_high` | float64 | Pessimistic entry price (high of entry candle) |
| `start_ext_entry_delay_s` | float64 | Seconds from trigger to entry fill |
| `start_ext_pre_px` | float64 | Close of the minute before the trigger |
| `start_ext_missed_move` | float64 | entry / pre_px - 1 (move missed by the delay) |
| `start_ext_trig_min_high_move` | float64 | High of the trigger minute / pre_px - 1 |
| `start_ext_r1` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r1_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r5` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r5_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r15` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r15_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r60` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r60_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r240` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r240_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r1440` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_r1440_hi` | float64 | Gross return at horizon N minutes from entry (fraction); _hi = entry at candle high |
| `start_ext_peak_gain` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `start_ext_peak_gain_hi` | float64 | Max high within 24h / entry - 1 (_hi: vs pessimistic entry) |
| `start_ext_t_peak_min` | float64 | Minutes from entry to the 24h peak |
| `start_ext_dd_before_peak` | float64 | Lowest low before the peak / entry - 1 |
| `start_ext_dd_after_peak` | float64 | Lowest low after the peak (within 24h) / peak - 1 |
| `start_ext_low24` | float64 | Lowest low within 24h / entry - 1 |
| `start_ext_peak60_gain` | float64 | First-hour peak / entry - 1 |
| `start_ext_t_peak60_min` | float64 | Minutes to first-hour peak |
| `ext_at_start` | str | External venue used at trading open |
| `start_lst_pre_px` | float64 | Close of the minute before the trigger |
| `start_lst_missed_move` | float64 | entry / pre_px - 1 (move missed by the delay) |
| `start_lst_trig_min_high_move` | float64 | High of the trigger minute / pre_px - 1 |
| `group` | str | Analysis group (e.g. Upbit KRW, Binance perp) |
| `ann_hour_kst` | int64 | Announcement hour in KST |
| `new_token` | bool | Not trading on any external venue before announcement |
| `ext_kind` | str | spot / perp external venue |
| `ann_ext_n1` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_n1440` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `ann_ext_outlier` | bool | Outlier flag for this entry type |
| `start_lst_n1` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_n1440` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_lst_outlier` | bool | Outlier flag for this entry type |
| `start_ext_n1` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_n1440` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `start_ext_outlier` | bool | Outlier flag for this entry type |
| `coinbase_first_day_ms` | Int64 | Coinbase: first daily candle (used instead of an announcement time) |

## events_source_list

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `product` | str | spot or perp |
| `quote` | str | Quote currency |
| `markets` | str | Markets opened (Upbit) / pairs |
| `announcement_ms` | Int64 | Announcement time, UTC epoch ms (null for Coinbase-derived events) |
| `ann_source` | str | Where the announcement time came from |
| `title` | str | Announcement title |
| `url` | str | Public notice URL |
| `source` | str | Where ticks came from |

## excluded_events

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `analysis` | str | Which analysis the exclusion applies to |
| `reason` | str | Why excluded / incomplete |

## exit_rule_grid_trades

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `product` | str | spot or perp |
| `entry` | str | Entry type of simulated trade |
| `tp` | float64 | Take-profit fraction (null = none) |
| `sl` | float64 | Stop-loss fraction (null = none) |
| `tmax` | int64 | Time exit, minutes |
| `ret` | float64 | Net return of the simulated trade |

## funding_history

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `symbol` | str | Ticker on the listing exchange |
| `timestamp_ms` | Int64 | Candle open / funding / trade time, UTC epoch ms |
| `funding_rate` | float64 | Funding rate for the interval (fraction) |
| `interval_inferred_hours` | float64 | Gap to next/previous funding timestamp, hours |
| `funding_interval_hours` | float64 | Hours between funding events (see source/inferred) |
| `funding_interval_inferred` | bool | True if interval inferred from timestamp gaps |
| `funding_interval_source` | str | How the interval was set |
| `current_venue_interval_hours` | float64 | Interval published by the venue today (may differ historically) |

## korean_perp_status

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `exchange` | str | Listing exchange |
| `symbol` | str | Ticker on the listing exchange |
| `announcement_ms` | Int64 | Announcement time, UTC epoch ms (null for Coinbase-derived events) |
| `perp_symbol` | str | Perp symbol checked |
| `binance_perp_at_ann` | bool | Binance USDT-M perp traded in 3h before announcement |
| `bybit_perp_at_ann` | bool | Bybit USDT-M perp traded in 3h before announcement |
| `binance_perp_onboard_ms` | Int64 | Binance exchangeInfo onboardDate (or first daily kline if delisted) |
| `binance_perp_onboard_source` | str | Source of onboard time |
| `bybit_perp_launch_ms` | Int64 | Bybit instruments-info launchTime |
| `bybit_funding_interval_min` | float64 | Bybit fundingInterval (minutes, current) |
| `perp_venue` | str | binance_perp preferred, else bybit_perp |
| `had_usdtm_perp_at_ann` | bool | Binance or Bybit USDT-M perp traded in 3h before announcement |
| `perp_listing_ms` | Int64 | Perp listing time (Binance onboardDate / Bybit launchTime) |
| `binance_spot_at_ann` | bool | Binance spot traded in 3h before announcement |

## perp_candles_1m

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `market` | str | Venue market symbol |
| `timestamp_ms` | Int64 | Candle open / funding / trade time, UTC epoch ms |
| `open` | float64 | Open price |
| `high` | float64 | High |
| `low` | float64 | Low |
| `close` | float64 | Close |
| `volume` | float64 | Quote-asset volume (USDT) in the minute |

## speed_test_1m_entry

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `instant_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `instant_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `instant_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `instant_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `instant_peak60` | float64 | Entry at the pre-announcement close (theoretical best case); suffix n<H> = net return at H min, peak60 = first-hour peak |
| `same_min_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `same_min_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `same_min_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `same_min_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `same_min_peak60` | float64 | Entry at the close of the announcement minute; suffix as instant_ |

## speed_test_tick_entry

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `n_trades` | int64 | aggTrades in window |
| `pre_px` | float64 | Last trade price before the announcement |
| `move_0s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e0s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e0s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e0s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e0s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_1s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e1s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e1s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e1s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e1s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_2s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e2s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e2s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e2s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e2s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_5s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e5s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e5s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e5s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e5s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_10s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e10s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e10s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e10s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e10s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_30s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e30s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e30s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e30s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e30s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `move_60s` | float64 | Price move N seconds after the announcement vs last pre-announcement trade |
| `e60s_n5` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e60s_n15` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e60s_n60` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `e60s_n240` | float64 | Net return (minus 0.6% round trip) at horizon N minutes |
| `t_half_move_s` | float64 | Seconds until half of the 60 s move was reached |

## spot_candles_1m

| column | type | description |
|---|---|---|
| `event_id` | str | Event key (H#### historical from announcement feeds, X#### Coinbase-derived or CoinSentry-only) |
| `venue` | str | binance_spot / binance_perp / bybit_perp ... |
| `market` | str | Venue market symbol |
| `timestamp_ms` | Int64 | Candle open / funding / trade time, UTC epoch ms |
| `open` | float64 | Open price |
| `high` | float64 | High |
| `low` | float64 | Low |
| `close` | float64 | Close |
| `volume` | float64 | Quote-asset volume (USDT) in the minute |
