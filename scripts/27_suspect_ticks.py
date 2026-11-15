"""Flag isolated aggTrade prints: a tick whose price deviates more than 20% from BOTH the previous and the next tick of the same
(event_id, venue, symbol) series, ordered by timestamp_ms then agg_trade_id. Nothing is deleted; the flags go to a side table
keyed by (event_id, venue, symbol, agg_trade_id). Reads every published aggtrades table in data/ plus extra/v3/aggtrades(_bithumb).parquet.
Output: extra/v3/aggtrades_suspect_ticks.parquet (one row per flagged tick, suspect_tick = True)."""
import glob, os, pandas as pd
TH=0.20
fs=[f for f in sorted(glob.glob('data/aggtrades*.parquet')) if 'index' not in f and '_v3_' not in f and 'suspect' not in f]
fs+=[f for f in ('extra/v3/aggtrades.parquet','extra/v3/aggtrades_bithumb.parquet') if os.path.exists(f)]
out=[]
for f in fs:
    a=pd.read_parquet(f,columns=['event_id','venue','symbol','agg_trade_id','price','timestamp_ms'])
    a=a.sort_values(['event_id','venue','symbol','timestamp_ms','agg_trade_id'])
    g=a.groupby(['event_id','venue','symbol'],sort=False).price
    a['prev_price']=g.shift(); a['next_price']=g.shift(-1)
    a['dev_prev']=a.price/a.prev_price-1; a['dev_next']=a.price/a.next_price-1
    x=a[(a.dev_prev.abs()>TH)&(a.dev_next.abs()>TH)].copy()
    x['source_table']=os.path.basename(f).split('.')[0]; out.append(x)
r=pd.concat(out,ignore_index=True); r['suspect_tick']=True; r['rule']='|p/prev-1|>0.20 and |p/next-1|>0.20'
r.to_parquet('extra/v3/aggtrades_suspect_ticks.parquet',index=False)
print(len(r), r.groupby('source_table').size().to_dict(), r.event_id.nunique())
