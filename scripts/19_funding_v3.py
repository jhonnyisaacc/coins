"""Funding for every event that had a USDT perp at the announcement (or, for perp-listing events, that lists one) but has
no rows in the published funding tables. Venue order: Binance USD-M (fapi/v1/fundingRate), Bybit linear
(v5/market/funding/history), OKX swap (api/v5/public/funding-rate-history, which keeps only recent months).
Window: 60 min before to 72 h after the announcement, same columns as funding_history.
Events: the v2 publication's events (raw/v2pub) plus extra/v3/events_v3.csv and events_v3_bithumb.csv if present. Output: extra/v3/funding_v3.parquet, extra/v3/funding_v3_status.parquet."""
import sys, os, glob, importlib, datetime as dt, pandas as pd
sys.path.insert(0,'scripts'); from common import get; from candles import candles, MIN, HOUR
m=importlib.import_module('08d_korean_market_v2')
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v3'; NOW=m.NOW
ev=pd.read_parquet('raw/v2pub/events.parquet')[['event_id','exchange','symbol','market_type','announcement_ms']]
for f in (f'{OUT}/events_v3.csv',f'{OUT}/events_v3_bithumb.csv'):
    if os.path.exists(f):
        v3=pd.read_csv(f).rename(columns={'ann_ms':'announcement_ms'})
        ev=pd.concat([ev,v3[['event_id','exchange','symbol','market_type','announcement_ms']]],ignore_index=True)
ev=ev[ev.announcement_ms.notna()]
have=set(pd.concat([pd.read_parquet(f) for f in glob.glob('data/funding_history*.parquet') if '_v3_' not in f]).event_id)
ev=ev[~ev.event_id.isin(have)]

def okx_funding(inst,w0,w1):
    rows=[]; after=w1
    while True:
        d=get(f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&after={after}&limit=100",min_interval=0.25)
        L=d.get('data') if isinstance(d,dict) else None
        if not L: break
        rows+=[(int(x['fundingTime']),float(x['realizedRate'] or x['fundingRate'])) for x in L if w0<=int(x['fundingTime'])<=w1]
        oldest=min(int(x['fundingTime']) for x in L)
        if oldest<=w0 or len(L)<100: break
        after=oldest
    return rows

def one(r):
    a=int(r.announcement_ms); s=m.ext_sym(r.symbol)+'USDT'; w0,w1=a-60*MIN,min(a+72*HOUR,NOW)
    listing=r.market_type=='perp'
    probe=(a,a+72*HOUR) if listing else (a-3*HOUR,a)
    st=dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,perp_symbol=s)
    for venue,mk in (('binance_perp',s),('bybit_perp',s),('okx_perp',f'{m.ext_sym(r.symbol)}-USDT-SWAP')):
        if venue=='okx_perp':
            k=get(f"https://www.okx.com/api/v5/market/history-candles?instId={mk}&bar=1H&after={probe[1]}&before={probe[0]}&limit=100",min_interval=0.25)
            exists=bool(isinstance(k,dict) and k.get('data'))
        else: exists=len(candles(venue,mk,*probe,unit=60 if listing else 1))>0
        if not exists: continue
        st['venue']=venue
        if venue=='okx_perp':
            fd=pd.DataFrame(sorted(set(okx_funding(mk,w0,w1))),columns=['timestamp_ms','funding_rate'])
            if len(fd):
                fd['interval_inferred_hours']=fd.timestamp_ms.diff().div(HOUR).round(2).bfill(); fd['funding_interval_hours']=fd.interval_inferred_hours
                fd['funding_interval_inferred']=True; fd['funding_interval_source']='inferred_from_timestamp_gaps'; fd['current_venue_interval_hours']=None
        else:
            bi=m.bybit_instr(s) if venue=='bybit_perp' else None
            fd=m.funding(venue,s,w0,w1,int(bi['fundingInterval']) if bi and bi.get('fundingInterval') else None)
        st['n_rows']=len(fd)
        st['note']=None if len(fd) else ('OKX funding-rate-history keeps only recent months' if venue=='okx_perp' else 'venue returned no funding in window')
        if len(fd): fd.insert(0,'event_id',r.event_id); fd.insert(1,'venue',venue); fd.insert(2,'symbol',mk)
        return st,fd
    st.update(venue=None,n_rows=0,note='no USDT perp on Binance, Bybit or OKX around the announcement'); return st,None

def safe(r):
    try: return one(r)
    except Exception as e: return dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=int(r.announcement_ms),n_rows=0,note='error '+repr(e)[:100]),None

if __name__=='__main__':
    with ThreadPoolExecutor(4) as tp: res=list(tp.map(safe,[r for r in ev.itertuples()]))
    pd.DataFrame([x[0] for x in res]).to_parquet(f'{OUT}/funding_v3_status.parquet',index=False)
    p=[x[1] for x in res if x[1] is not None and len(x[1])]
    (pd.concat(p,ignore_index=True) if p else pd.DataFrame()).to_parquet(f'{OUT}/funding_v3.parquet',index=False)
    print('done',len(res),sum(len(x[1]) for x in res if x[1] is not None))
