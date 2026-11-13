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

# v2 additions (collection_batch "v2", 2026-11-13)

Every table that received v2 rows has a `collection_batch` column: `v1` for the original rows, `v2` for rows added in this collection. Large tick and candle tables keep their v1 file unchanged. Their v2 rows are in files named `<table>_v2_<year>` (year of the event's announcement, UTC), with the same columns plus `collection_batch`. Coinbase and Binance-spot events have their perp candles in `perp_candles_1m_other_v2_<year>`. A table whose Parquet or CSV would exceed 50 MB is split into `.partNN` files.

Event ids: `V####` are v2 events. Coinbase listings that already existed in v1 keep their v1 id.

## New columns on existing tables

| table | column | type | description |
|---|---|---|---|
| events, events_metrics, events_source_list | `collection_batch` | str | `v1` or `v2` |
| events, events_metrics, events_source_list | `announcement_time_official` | bool | True when the announcement time comes from the exchange's own feed (Upbit API, Binance CMS, OKX/Bybit APIs, Bithumb official API, Coinbase Exchange status page). False for CryptoListing.ws Bithumb times, CoinSentry-only rows and Coinbase rows without an official time |
| events, events_metrics, events_source_list, korean_perp_status | `v1_announcement_ms` | Int64 | The v1 announcement time where v2 replaced it with an official one (Bithumb official API; Coinbase status page, where v1 had none). Null elsewhere |
| events | `coinbase_full_trading_ms` | Int64 | Coinbase: time of the status-page update that moved the pair to full trading |
| events | `coinbase_usd_product_status_now` | str | Coinbase: `<SYM>-USD` product status today (`online`, `delisted`, `not_listed_now`) |
| korean_perp_status | `binance_spot_listing_ms` | Int64 | Open time of the first 1m Binance spot `<SYM>USDT` kline. Null if the market never existed |
| korean_perp_status | `binance_spot_listing_source` | str | `first_1m_kline(data-api.binance.vision)` |
| korean_perp_status | `binance_perp_onboard_source` | str | v2 adds `first_1m_kline` for delisted perps, where v1 used `first_daily_kline` |
| aggtrades_index | `collection_batch` | str | v2 rows add the second Binance venue for v1 events and all venues for v2 events |
| aggtrades_index | `source` | str | v2 adds `data.binance.vision/spot/daily/aggTrades` (spot ticks the REST endpoint no longer serves) |

## btc_candles_1m_<year>

Binance USD-M BTCUSDT 1-minute candles from 60 min before to 72 h after each Korean event's announcement, as a market benchmark. One copy of the window per event.

| column | type | description |
|---|---|---|
| `event_id` | str | Event key |
| `venue` | str | `binance_perp` |
| `market` | str | `BTCUSDT` |
| `timestamp_ms` | Int64 | Candle open time |
| `open`, `high`, `low`, `close` | float64 | Prices in USDT |
| `volume` | float64 | Quote volume (USDT) |

## hyperliquid_perp_status

One row per Korean event (v1 and v2).

| column | type | description |
|---|---|---|
| `event_id`, `exchange`, `symbol`, `announcement_ms`, `collection_batch` | | As in events |
| `hl_coin` | str | Hyperliquid perp name. `k<SYM>` coins are quoted per 1000 tokens. Null when no perp of that name exists in the current meta universe (delisted coins included) |
| `hl_price_multiplier` | float | 1000 for `k` coins, else 1 |
| `hl_is_delisted_now` | bool | `isDelisted` in today's meta |
| `hl_listing_ms` | Int64 | First `fundingHistory` record (hourly precision) |
| `hl_listing_source` | str | `first_fundingHistory_record` |
| `hl_first_traded_day_ms` | Int64 | First 1d candle with trades |
| `hl_last_traded_day_end_ms` | Int64 | End of the last 1d candle with trades |
| `hl_perp_at_ann` | bool | Listed before the announcement and not delisted by then |
| `hl_candle_interval` | str | Interval stored in hyperliquid_candles for this event. The API serves only the latest ~5000 candles per interval, so it is the finest interval whose history reaches the window start (1m only back to 2026-11-10, 1h to 2026-04-19, 4h to 2024-08-02) |
| `hl_candle_rows`, `hl_funding_rows` | float | Rows stored |
| `hl_status_note` | str | Why there is no data |

## hyperliquid_candles

| column | type | description |
|---|---|---|
| `event_id`, `coin` | str | Event key and Hyperliquid coin |
| `interval` | str | Candle interval (see hyperliquid_perp_status) |
| `timestamp_ms` | Int64 | Candle open time, window 60 min before to 72 h after the announcement |
| `open`, `high`, `low`, `close` | float64 | USDC prices |
| `volume_base` | float64 | Base-asset volume |
| `n_trades` | int64 | Trades in the candle |

## hyperliquid_funding

| column | type | description |
|---|---|---|
| `event_id`, `coin` | str | Event key and Hyperliquid coin |
| `timestamp_ms` | Int64 | Funding time (hourly) |
| `funding_rate` | float64 | Hourly funding rate (fraction) |
| `premium` | float64 | Premium used for that funding |

hyperliquid_trades was not built: Hyperliquid has no public historical trades API.

## dex_pool_status

One row per Korean event and chain with a contract (Solana, Base, BSC, Ethereum), or one row with a `note` when no contract was resolved.

| column | type | description |
|---|---|---|
| `event_id`, `exchange`, `symbol`, `announcement_ms`, `collection_batch` | | As in events |
| `coingecko_id` | str | CoinGecko id, read from CoinGecko's own Upbit/Bithumb ticker list (exchange-anchored, not a ticker search) |
| `chain` | str | GeckoTerminal network: `solana`, `base`, `bsc`, `eth` |
| `token_address` | str | Contract from CoinGecko `/coins/{id}` `platforms` |
| `contract_source` | str | Provenance of the contract |
| `pool_address`, `dex`, `pool_name` | str | Selected pool |
| `pool_created_ms` | Int64 | Pool creation time (GeckoTerminal) |
| `liquidity_usd_now` | float64 | Pool reserve in USD today. Liquidity at the announcement is not served by the free API |
| `liquidity_usd_at_ann` | float | Always null (not available) |
| `pool_selection` | str | Deepest pool by today's reserve among pools created before the announcement (GeckoTerminal's first page of pools) |
| `n_candidate_pools` | float | Pools considered |
| `dex_candle_rows` | float | Rows in dex_candles |
| `note` | str | Why data is missing |

## dex_candles

Per-swap history was not available (see excluded_events). These are the finest candles available: 1-minute USD candles of the selected pool from 2 min before to 10 min after the announcement, only for announcements inside GeckoTerminal's 180-day public window.

| column | type | description |
|---|---|---|
| `event_id`, `chain`, `pool_address` | str | Keys |
| `interval` | str | `1m` |
| `timestamp_ms` | Int64 | Candle open time |
| `open`, `high`, `low`, `close` | float64 | Token price in USD |
| `volume_usd` | float64 | USD volume |

## upbit_poll_log

Written by `scripts/12_upbit_poll.py`, going forward only. One row per notice first seen by the poller (notices present at startup are not logged).

| column | type | description |
|---|---|---|
| `notice_id` | int | Upbit notice id |
| `title`, `category` | str | Notice title and category |
| `first_seen_ms` | Int64 | Local clock (NTP-synced macOS) when the poller first saw the notice |
| `notice_first_listed_ms` | Int64 | Notice `first_listed_at` (1-second precision) |
| `notice_listed_ms` | Int64 | Notice `listed_at` |
| `seen_minus_first_listed_ms` | Int64 | Detection delay. Includes up to 1 s of timestamp truncation and the poll interval |
| `poll_interval_s` | float | Target poll interval |
| `http_elapsed_ms` | int | Round trip of the request that saw it |
| `region` | str | Where the poller runs |
