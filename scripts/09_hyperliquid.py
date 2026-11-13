"""Hyperliquid perps for every Korean event (v1 + v2) -> extra/v2/hyperliquid_*.parquet.
Candle history is capped at the latest ~5000 candles per interval, so each event gets the finest interval whose history
reaches back to the window start (-60 min). Historical trades have no public API, so hyperliquid_trades is not built."""
import sys, os, json, time, datetime as dt, pandas as pd, requests
sys.path.insert(0,'scripts'); from candles import MIN, HOUR
OUT='extra/v2'; os.makedirs(OUT,exist_ok=True)
URL='https://api.hyperliquid.xyz/info'
NOW=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
INTERVALS=[('1m',MIN),('5m',5*MIN),('15m',15*MIN),('1h',HOUR),('4h',4*HOUR),('8h',8*HOUR),('1d',24*HOUR)]
S=requests.Session()

def post(body):
    for a in range(6):
        r=S.post(URL,json=body,timeout=30)
        if r.status_code in (429,502,503): time.sleep(2+3*a); continue
        if r.status_code==500: return []
        r.raise_for_status(); time.sleep(0.25); return r.json()
    raise RuntimeError('hyperliquid 429')

def snap(coin,iv,s,e): return post({'type':'candleSnapshot','req':{'coin':coin,'interval':iv,'startTime':s,'endTime':e}}) or []

def funding(coin,s,e):
    out=[]
    while s<e:
        d=post({'type':'fundingHistory','coin':coin,'startTime':s,'endTime':e})
        if not d: break
        out+=d
        if len(d)<500: break
        s=d[-1]['time']+1
    return out

meta=post({'type':'meta'})['universe']
UNI={u['name']:u for u in meta}
_depth={}
def depth(iv):
    if iv not in _depth:
        d=snap('BTC',iv,0,NOW); _depth[iv]=d[0]['t'] if d else NOW
    return _depth[iv]

def hl_coin(sym):
    for c in (sym,'k'+sym):
        if c in UNI: return c
    return None

def one(r):
    a=int(r.announcement_ms); coin=hl_coin(r.symbol)
    st=dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,collection_batch=r.collection_batch,
            hl_coin=coin,hl_price_multiplier=1000 if coin and coin.startswith('k') else (1 if coin else None),
            hl_is_delisted_now=bool(UNI[coin].get('isDelisted')) if coin else None)
    if not coin:
        st.update(hl_perp_at_ann=False,hl_status_note='no Hyperliquid perp with this name (current meta universe incl. delisted)')
        return st,None,None
    f0=post({'type':'fundingHistory','coin':coin,'startTime':0})
    st['hl_listing_ms']=f0[0]['time'] if f0 else None; st['hl_listing_source']='first_fundingHistory_record' if f0 else None
    days=[c for c in snap(coin,'1d',0,NOW) if c['n']>0]
    st['hl_first_traded_day_ms']=days[0]['t'] if days else None
    st['hl_last_traded_day_end_ms']=days[-1]['T'] if days else None
    listed=st['hl_listing_ms'] is not None and st['hl_listing_ms']<=a
    alive=not st['hl_is_delisted_now'] or (st['hl_last_traded_day_end_ms'] or 0)>=a
    st['hl_perp_at_ann']=bool(listed and alive)
    w0,w1=a-60*MIN,min(a+72*HOUR,NOW)
    cs=None
    for iv,ms in INTERVALS:
        if depth(iv)<=w0 or (st['hl_listing_ms'] and depth(iv)<=st['hl_listing_ms']):
            d=snap(coin,iv,w0,w1)
            if d:
                cs=pd.DataFrame([dict(event_id=r.event_id,coin=coin,interval=iv,timestamp_ms=c['t'],open=float(c['o']),high=float(c['h']),
                    low=float(c['l']),close=float(c['c']),volume_base=float(c['v']),n_trades=int(c['n'])) for c in d])
            st['hl_candle_interval']=iv
            break
    fu=funding(coin,w0,w1)
    fd=pd.DataFrame([dict(event_id=r.event_id,coin=coin,timestamp_ms=x['time'],funding_rate=float(x['fundingRate']),premium=float(x['premium'])) for x in fu]) if fu else None
    st['hl_candle_rows']=0 if cs is None else len(cs); st['hl_funding_rows']=0 if fd is None else len(fd)
    return st,cs,fd

if __name__=='__main__':
    v1=pd.read_parquet('raw/v1/events.parquet'); v1=v1[v1.exchange.isin(['Upbit','Bithumb'])].assign(collection_batch='v1')
    v2=pd.read_csv('raw/events_all_v2.csv').rename(columns={'ann_ms':'announcement_ms'}).assign(collection_batch='v2')
    K=pd.concat([v1[['event_id','exchange','symbol','announcement_ms','collection_batch']],v2[['event_id','exchange','symbol','announcement_ms','collection_batch']]],ignore_index=True)
    res=[]
    for i,r in enumerate(K.itertuples()):
        try: res.append(one(r))
        except Exception as e: res.append((dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=int(r.announcement_ms),collection_batch=r.collection_batch,hl_status_note='error: '+repr(e)[:120]),None,None))
        if i%25==0: print(i,len(K),flush=True)
    pd.DataFrame([x[0] for x in res]).to_parquet(f'{OUT}/hyperliquid_perp_status.parquet',index=False)
    for k,name in [(1,'hyperliquid_candles'),(2,'hyperliquid_funding')]:
        parts=[x[k] for x in res if x[k] is not None]
        (pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()).to_parquet(f'{OUT}/{name}.parquet',index=False)
    print('done',len(res))
