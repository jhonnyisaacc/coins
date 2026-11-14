"""Market data for the v3 events (extra/v3/events_v3.csv), with the 08d/10d fetchers: perp status at the announcement
(Binance USD-M and Bybit linear 1m candles in the 3 h before it; for Binance perp-listing events the listed perp's first
candle), perp 1m candles -60 min..+72 h on the perp venue, Binance spot 1m candles over the same window, and aggTrades
-60 s..+90 s on Binance spot and USD-M perp where each market existed at the announcement. Funding is fetched by 19_funding_v3.
Output: extra/v3/perp_status_v3.parquet, perp_candles_1m_v3.parquet, spot_candles_1m_v3.parquet, aggtrades.parquet, aggtrades_index.parquet."""
import sys, importlib, pandas as pd
sys.path.insert(0,'scripts')
m=importlib.import_module('08d_korean_market_v2')
from candles import candles, MIN, HOUR
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v3'
ev=pd.read_csv(f'{OUT}/events_v3.csv')

def one(r):
    a=int(r.ann_ms); s=m.ext_sym(r.symbol)+'USDT'; eid=r.event_id; w0,w1=a-60*MIN,min(a+72*HOUR,m.NOW)
    listing=r.exchange=='Binance' and r.product=='perp'
    sp_at=len(candles('binance',s,a-3*HOUR,a))>0
    bn_at=len(candles('binance_perp',s,a-3*HOUR,a))>0
    by_at=len(candles('bybit_perp',s,a-3*HOUR,a))>0
    st=dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,market_type=r.product,announcement_ms=a,perp_symbol=s,
            binance_perp_at_ann=bn_at,bybit_perp_at_ann=by_at,binance_spot_at_ann=sp_at,binance_perp_onboard_ms=m.bn_onboard.get(s))
    if listing and st['binance_perp_onboard_ms'] is None:
        st['binance_perp_onboard_ms']=m.first_daily(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1m&startTime={a}&limit=1")
    venue='binance_perp' if (bn_at or listing) else ('bybit_perp' if by_at else None)
    st['perp_venue']=venue; st['had_usdt_perp_at_ann']=bn_at or by_at
    out=dict(status=st,perp=None,spot=None,ticks=[],idx=[])
    if venue:
        c=candles(venue,s,w0,w1)
        if c: out['perp']=m.frame(c,eid,venue,s)
    c=candles('binance',s,w0,w1)
    if c: out['spot']=m.frame(c,eid,'binance_spot',s)
    for v,exists,fn in [('binance_spot',sp_at,m.spot_ticks),('binance_perp',bn_at,m.perp_ticks)]:
        if not exists: continue
        tr,src=fn(s,a)
        df=pd.DataFrame(tr,columns=['agg_trade_id','price','qty','timestamp_ms','is_buyer_maker'])
        df.insert(0,'event_id',eid); df.insert(1,'venue',v); df.insert(2,'symbol',s); out['ticks'].append(df)
        out['idx'].append(dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,venue=v,market=s,announcement_ms=a,n_ticks=len(df),source=src,in_original_speed_test=False))
    return out

def safe(r):
    try: return one(r)
    except Exception as e: print('ERR',r.event_id,repr(e)[:150],flush=True); return None

if __name__=='__main__':
    with ThreadPoolExecutor(4) as tp: res=[x for x in tp.map(safe,[r for r in ev.itertuples()]) if x]
    pd.DataFrame([x['status'] for x in res]).to_parquet(f'{OUT}/perp_status_v3.parquet',index=False)
    for k,name in [('perp','perp_candles_1m_v3'),('spot','spot_candles_1m_v3')]:
        p=[x[k] for x in res if x[k] is not None and len(x[k])]
        (pd.concat(p,ignore_index=True) if p else pd.DataFrame()).to_parquet(f'{OUT}/{name}.parquet',index=False)
    t=[d for x in res for d in x['ticks'] if len(d)]
    (pd.concat(t,ignore_index=True) if t else pd.DataFrame()).to_parquet(f'{OUT}/aggtrades.parquet',index=False)
    pd.DataFrame([d for x in res for d in x['idx']]).to_parquet(f'{OUT}/aggtrades_index.parquet',index=False)
    print('done',len(res),len(ev))
