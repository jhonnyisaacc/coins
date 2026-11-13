"""Binance data around v2 Binance-spot (perp already listed) and Coinbase announcements (v2 rows and v1 rows that got an
official time): Binance USD-M perp 1m candles -60 min..+72 h, funding (Binance events), aggTrades -60 s..+90 s on Binance
spot and perp where each market existed at the announcement. Same fetchers as 08d. Output extra/v2/other_*.parquet."""
import sys, importlib, pandas as pd
sys.path.insert(0,'scripts')
m=importlib.import_module('08d_korean_market_v2')
from candles import candles, MIN, HOUR
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v2'
ev=pd.read_csv('raw/v2_other_events.csv')
ev=ev[(ev.exchange=='Coinbase')|((ev.exchange=='Binance')&ev.binance_perp_at_ann.astype(bool))]
v1=pd.read_parquet('raw/v1/events.parquet')
v1=v1[(v1.exchange=='Binance')&(v1.market_type=='spot')].rename(columns={'announcement_ms':'ann_ms'})[['event_id','exchange','symbol','ann_ms']]
ev=pd.concat([ev[['event_id','exchange','symbol','ann_ms']],v1],ignore_index=True)

def one(r):
    a=int(r.ann_ms); s=m.ext_sym(r.symbol)+'USDT'; eid=r.event_id; w0,w1=a-60*MIN,min(a+72*HOUR,m.NOW)
    sp_at=len(candles('binance',s,a-3*HOUR,a))>0 if r.exchange=='Coinbase' else False
    bn_at=len(candles('binance_perp',s,a-3*HOUR,a))>0
    if r.exchange=='Binance' and not bn_at: return None
    out=dict(perp=None,funding=None,ticks=[],idx=[],status=dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,perp_symbol=s,
        binance_perp_at_ann=bn_at,binance_spot_at_ann=sp_at,binance_perp_onboard_ms=m.bn_onboard.get(s)))
    if bn_at:
        out['perp']=m.frame(candles('binance_perp',s,w0,w1),eid,'binance_perp',s)
        if r.exchange=='Binance':
            fd=m.funding('binance_perp',s,w0,w1,None)
            if len(fd): fd.insert(0,'event_id',eid); fd.insert(1,'venue','binance_perp'); fd.insert(2,'symbol',s); out['funding']=fd
    for venue,exists,fn in [('binance_spot',sp_at,m.spot_ticks),('binance_perp',bn_at,m.perp_ticks)]:
        if not exists or (eid,venue) in m.have_ticks: continue
        tr,src=fn(s,a)
        df=pd.DataFrame(tr,columns=['agg_trade_id','price','qty','timestamp_ms','is_buyer_maker'])
        df.insert(0,'event_id',eid); df.insert(1,'venue',venue); df.insert(2,'symbol',s); out['ticks'].append(df)
        out['idx'].append(dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,venue=venue,market=s,announcement_ms=a,n_ticks=len(df),source=src,in_original_speed_test=False))
    return out

def safe(r):
    try: return one(r)
    except Exception as e: print('ERR',r.event_id,repr(e)[:150],flush=True); return None

if __name__=='__main__':
    with ThreadPoolExecutor(4) as tp: res=[x for x in tp.map(safe,[r for _,r in ev.iterrows()]) if x]
    pd.DataFrame([x['status'] for x in res]).to_parquet(f'{OUT}/other_binance_status.parquet',index=False)
    for k,name in [('perp','other_perp_candles_1m'),('funding','other_funding_history')]:
        p=[x[k] for x in res if x[k] is not None and len(x[k])]
        (pd.concat(p,ignore_index=True) if p else pd.DataFrame()).to_parquet(f'{OUT}/{name}.parquet',index=False)
    t=[d for x in res for d in x['ticks'] if len(d)]
    (pd.concat(t,ignore_index=True) if t else pd.DataFrame()).to_parquet(f'{OUT}/other_aggtrades.parquet',index=False)
    pd.DataFrame([d for x in res for d in x['idx']]).to_parquet(f'{OUT}/other_aggtrades_index.parquet',index=False)
    print('done',len(res),len(ev))
