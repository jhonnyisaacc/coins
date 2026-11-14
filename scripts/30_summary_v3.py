"""Add a "v3" key to data/summary.json (v1 and v2 keys untouched): the 14_summary_v2 per-group summaries for v3 rows, and
the per-task source status (done / partial / failed with counts and reasons) read from row_counts.json and extra/v3 status files."""
import json, os, pandas as pd
src=open('scripts/14_summary_v2.py').read(); ns={}; exec(src[:src.index("m=pd.read_parquet")],ns); summ=ns['summ']
m=pd.read_parquet('data/events_metrics.parquet'); d=m[m.collection_batch=='v3']
groups=sorted(d.group.dropna().unique())
S=json.load(open('data/summary.json')); C=json.load(open('row_counts.json'))
rc=lambda *ks: {k:C.get(k) for k in ks}
yr=lambda p: {k:v for k,v in C.items() if k.startswith(p)}
wb=json.load(open('extra/v3/bithumb_wayback_status.json')) if os.path.exists('extra/v3/bithumb_wayback_status.json') else {}
S['v3']={name:{g:summ(d[d.group==g],p) for g in groups} for p,name in [('ann_ext_','ann_ext'),('start_lst_','start_lst'),('start_ext_','start_ext')]}
S['v3']['events_by_group']=d.group.value_counts().to_dict()
S['v3_notes']={
 'collected_utc':'2026-11-13',
 'scope':'OKX/Bybit spot and Binance USD-M perp listings 2024-01-01..2025-10-31; Bithumb 2024-2025 from Wayback captures where found; funding gaps; order-book depth; delisted daily candles; DEX swaps; forward pollers and daily perp limits',
 'tables':{**rc('book_snapshots','book_index','perp_status_v3','delisted_daily_candles','dex_swaps','aggtrades_suspect_ticks','perp_limits_snapshots',
               'upbit_poll_log','binance_poll_log','bithumb_poll_log','bithumb_wayback_notices'),**yr('funding_history_v3'),**yr('perp_candles_1m_v3'),**yr('spot_candles_1m_v3'),**yr('aggtrades_v3')},
 'bithumb_wayback':wb,
 'not_comparable':'delisted_daily_candles is daily data and is not comparable with the 1-minute metrics; book_snapshots pct_band rows are cumulative depth bands, not price levels',
}
json.dump(S,open('data/summary.json','w'),default=lambda x:None)
print(pd.DataFrame(S['v3']['start_lst']).T[['n']].join(pd.DataFrame(S['v3']['ann_ext']).T[['n']],rsuffix='_ann').to_string())
