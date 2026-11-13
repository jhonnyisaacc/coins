"""v2 events (raw/v2_upbit_events.csv) -> raw/events_all_v2.csv and out/metrics_v2_raw.csv using the v1 04_metrics.run method."""
import sys, csv, importlib, pandas as pd
sys.path.insert(0,'scripts')
m04=importlib.import_module('04_metrics')
from concurrent.futures import ThreadPoolExecutor
up=pd.read_csv('raw/v2_upbit_events.csv')
cols=['event_id','exchange','symbol','product','quote','markets','ann_ms','ann_source','title','url','source']
up['event_id']=[f"V{i+1:04d}" for i in range(len(up))]
up[cols+['market_type','notice_id']].to_csv('raw/events_all_v2.csv',index=False)
evs=[{k:str(v) for k,v in r.items()} for r in up[cols].to_dict('records')]
def safe(e):
    try: return m04.run(e)
    except Exception as ex:
        r=dict(e); r['err']=repr(ex)[:120]; return r
with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv)>1 else 6) as tp:
    res=list(tp.map(safe,evs))
pd.DataFrame(res).to_csv('out/metrics_v2_raw.csv',index=False)
print(len(res))
