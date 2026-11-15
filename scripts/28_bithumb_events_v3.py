"""v3 Bithumb events from the Wayback notices (22_bithumb_wayback.py): market-addition notices published 2024-01-01..2025-10-31
(KST publicationDateTime from Bithumb's own page), KRW-market symbols only (BTC-market additions go to bithumb_v3_non_krw.csv), one event per symbol per 30 days (earliest notice; later relistings are separate events), ids after the v3 events. Then the
v1 04_metrics.run and the 26_market_v3 fetchers (perp status, perp/spot candles, aggTrades) on them.
Output: extra/v3/events_v3_bithumb.csv, out/metrics_v3_bithumb_raw.csv, extra/v3/*_bithumb.parquet."""
import sys, re, os, importlib, datetime as dt, pandas as pd
sys.path.insert(0,'scripts'); m04=importlib.import_module('04_metrics'); mk=importlib.import_module('26_market_v3')
from concurrent.futures import ThreadPoolExecutor
X='extra/v3'; KST=dt.timezone(dt.timedelta(hours=9)); S,E=1704067200000,1761955200000
n=pd.read_parquet(f'{X}/bithumb_wayback_notices.parquet')
MK={'원화':'KRW','BTC':'BTC','USDT':'USDT'}
def markets(title):
    """Symbols in parentheses take the market named after them: '크웬타(KWENTA) BTC 마켓, 오픈 캠퍼스(EDU) 원화 마켓 추가' -> KWENTA BTC, EDU KRW."""
    out=[]; pend=[]
    for m in re.finditer(r'\(([A-Z0-9]{1,12})\)|(원화|BTC|USDT)\s*마켓',title):
        if m.group(1): pend.append(m.group(1))
        else: out+=[(x,MK[m.group(2)]) for x in pend]; pend=[]
    return list(dict.fromkeys(out))
rows=[]; skipped=[]
for r in n.itertuples():
    ms=int(dt.datetime.strptime(r.published_kst,'%Y-%m-%d %H:%M:%S').replace(tzinfo=KST).timestamp()*1000)
    if not S<=ms<E: continue
    for s,mkt in markets(r.title):
        if mkt!='KRW': skipped.append(dict(symbol=s,market=mkt,ann_ms=ms,title=r.title)); continue
        rows.append(dict(exchange='Bithumb',symbol=s,product='spot',quote='KRW',markets='KRW',ann_ms=ms,ann_source='bithumb_page_via_wayback',title=r.title,
                         url=f'https://feed.bithumb.com/notice/{r.notice_id}' if pd.notna(r.notice_id) else r.capture_url,source='wayback:'+str(r.capture_timestamp)))
ev=pd.DataFrame(rows).sort_values('ann_ms') if rows else pd.DataFrame()
if len(ev):
    last={}; keep=[]
    for r in ev.itertuples():
        keep.append(r.symbol not in last or r.ann_ms-last[r.symbol]>30*86400000)
        if keep[-1]: last[r.symbol]=r.ann_ms
    ev=ev[keep]
if not len(ev): print('no Bithumb listing notices in range'); sys.exit()
n0=int(pd.read_csv(f'{X}/events_v3.csv').event_id.str[1:].astype(int).max())
ev.insert(0,'event_id',[f'V{n0+i+1:04d}' for i in range(len(ev))]); ev['market_type']='KRW'
ev.to_csv(f'{X}/events_v3_bithumb.csv',index=False); pd.DataFrame(skipped).to_csv(f'{X}/bithumb_v3_non_krw.csv',index=False); print(len(ev),'Bithumb KRW events,',len(skipped),'non-KRW market additions skipped')
cols=['event_id','exchange','symbol','product','quote','markets','ann_ms','ann_source','title','url','source']
def safe(e):
    try: return m04.run(e)
    except Exception as x: r=dict(e); r['err']=repr(x)[:120]; return r
with ThreadPoolExecutor(6) as tp: res=list(tp.map(safe,[{k:str(v) for k,v in r.items()} for r in ev[cols].to_dict('records')]))
pd.DataFrame(res).to_csv('out/metrics_v3_bithumb_raw.csv',index=False)
with ThreadPoolExecutor(4) as tp: out=[x for x in tp.map(mk.safe,list(ev.itertuples())) if x]
pd.DataFrame([x['status'] for x in out]).to_parquet(f'{X}/perp_status_v3_bithumb.parquet',index=False)
for k,name in [('perp','perp_candles_1m_v3_bithumb'),('spot','spot_candles_1m_v3_bithumb')]:
    p=[x[k] for x in out if x[k] is not None and len(x[k])]
    (pd.concat(p,ignore_index=True) if p else pd.DataFrame()).to_parquet(f'{X}/{name}.parquet',index=False)
t=[d for x in out for d in x['ticks'] if len(d)]
(pd.concat(t,ignore_index=True) if t else pd.DataFrame()).to_parquet(f'{X}/aggtrades_bithumb.parquet',index=False)
pd.DataFrame([d for x in out for d in x['idx']]).to_parquet(f'{X}/aggtrades_index_bithumb.parquet',index=False)
print('metrics',len(res),'market',len(out))
