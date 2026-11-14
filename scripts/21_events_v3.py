"""v3 events: OKX and Bybit spot listings and Binance USD-M perp listings from 2024-01-01 to 2025-10-31, parsed with the
03_build_events rules (dedupe per exchange+symbol+product, earliest), then the v1 04_metrics.run on each.
Output: extra/v3/events_v3.csv, out/metrics_v3_raw.csv."""
import sys, re, json, importlib, pandas as pd
sys.path.insert(0,'scripts'); m04=importlib.import_module('04_metrics')
from concurrent.futures import ThreadPoolExecutor
S,E=1704067200000,1761955200000
rows=[]
def add(**k): rows.append(k)
for a in json.load(open('raw/binance_announcements_all.json')):
    t=a['title']; ms=int(a['releaseDate'])
    if not S<=ms<E: continue
    m=re.match(r'Binance Futures Will Launch (?:USDⓈ-Margined )?(.+?) (?:USDⓈ-Margined )?Perpetual Contracts?',t)
    if m and 'TradFi' not in t and 'Multiple' not in t and 'Pre-IPO' not in t and 'Quanto' not in t:
        for s in re.findall(r'([A-Z0-9]{2,15})USDT\b',m.group(1)):
            add(exchange='Binance',symbol=s,product='perp',quote='USDT',markets='USDT-M',ann_ms=ms,ann_source='binance_cms',title=t,
                url=f"https://www.binance.com/en/support/announcement/{a['code']}",source='historical')
for a in json.load(open('raw/okx_announcements_v3.json')):
    t=a['title']; ms=int(a['pTime'])
    if not S<=ms<E or 'spot trading' not in t.lower() or 'pre-market' in t.lower(): continue
    syms=set(re.findall(r'\b([A-Za-z0-9]{2,15})/USD[TⓈC]',t)) or set(re.findall(r'list ([A-Z0-9]{2,15}) ',t))
    for s in syms: add(exchange='OKX',symbol=s.upper(),product='spot',quote='USDT',markets='USDT',ann_ms=ms,ann_source='okx_api',title=t,url=a['url'],source='historical')
for a in json.load(open('raw/bybit_announcements_v3.json')):
    t=a['title']; ms=int(a.get('publishTime',a.get('dateTimestamp')))
    if not S<=ms<E or 'Spot Listings' not in a['tags']: continue
    if 'Convert' in t or 'Launchpool' in t or 'Pre-Market' in t: continue
    m=re.search(r'List .*?\(([A-Z0-9]+)\) on\s+Spot',t) or re.search(r'New [Ll]isting: ([A-Z0-9]+)/USDT',t)
    if m: add(exchange='Bybit',symbol=m.group(1),product='spot',quote='USDT',markets='USDT',ann_ms=ms,ann_source='bybit_api',title=t,url=a['url'],source='historical')
seen={}
for r in sorted(rows,key=lambda r:r['ann_ms']):
    k=(r['exchange'],r['symbol'],r['product'])
    if k not in seen: seen[k]=r
ev=pd.DataFrame(sorted(seen.values(),key=lambda r:r['ann_ms']))
n0=int(pd.read_parquet('raw/v2pub/events.parquet').event_id.str.extract(r'^V(\d+)$')[0].dropna().astype(int).max())
ev.insert(0,'event_id',[f"V{n0+i+1:04d}" for i in range(len(ev))])
ev['market_type']=ev['product']
ev.to_csv('extra/v3/events_v3.csv',index=False)
print(ev.groupby(['exchange','product']).size())
if __name__=='__main__' and '--no-metrics' not in sys.argv:
    cols=['event_id','exchange','symbol','product','quote','markets','ann_ms','ann_source','title','url','source']
    evs=[{k:str(v) for k,v in r.items()} for r in ev[cols].to_dict('records')]
    def safe(e):
        try: return m04.run(e)
        except Exception as x: r=dict(e); r['err']=repr(x)[:120]; return r
    with ThreadPoolExecutor(6) as tp: res=list(tp.map(safe,evs))
    pd.DataFrame(res).to_csv('out/metrics_v3_raw.csv',index=False); print('metrics',len(res))
