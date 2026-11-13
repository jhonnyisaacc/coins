"""v1 04_metrics.run on the new v2 Binance spot (perp listed at announcement) and Coinbase events -> out/metrics_v2_other_raw.csv."""
import sys, importlib, pandas as pd
sys.path.insert(0,'scripts'); m04=importlib.import_module('04_metrics')
from concurrent.futures import ThreadPoolExecutor
ev=pd.read_csv('raw/v2_other_events.csv')
ev=ev[ev.v1_event_id.isna()&((ev.exchange=='Coinbase')|ev.binance_perp_at_ann.fillna(False).astype(bool))]
cols=['event_id','exchange','symbol','product','quote','markets','ann_ms','ann_source','title','url','source']
evs=[{k:('' if pd.isna(v) else str(v)) for k,v in r.items()} for r in ev[cols].to_dict('records')]
def safe(e):
    try: return m04.run(e)
    except Exception as ex: r=dict(e); r['err']=repr(ex)[:120]; return r
with ThreadPoolExecutor(4) as tp: res=list(tp.map(safe,evs))
pd.DataFrame(res).to_csv('out/metrics_v2_other_raw.csv',index=False); print(len(res))
