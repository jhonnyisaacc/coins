"""v2 market data for every Korean event (v1 Upbit/Bithumb + v2 Upbit), same methods as 07a/07b.
Writes extra/v2/*.parquet:
  korean_perp_status (v2 events), binance_spot_listing (all Korean events), perp_candles_1m / spot_candles_1m / funding_history (v2 events),
  btc_candles_1m (all), aggtrades + aggtrades_index (every Binance spot and USD-M perp market that existed at the announcement,
  skipping event+venue pairs already in data/aggtrades_index)."""
import sys, io, os, re, zipfile, datetime as dt, pandas as pd, requests
sys.path.insert(0,'scripts'); from common import get; from candles import candles, MIN, HOUR
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v2'; os.makedirs(OUT,exist_ok=True); os.makedirs('raw/bv',exist_ok=True)
NOW=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
CANDLE_COLS=['timestamp_ms','open','high','low','close','volume']

v1=pd.read_parquet('raw/v1/events.parquet')
v1=v1[v1.exchange.isin(['Upbit','Bithumb'])][['event_id','exchange','symbol','announcement_ms']].assign(collection_batch='v1')
v2=pd.read_csv('raw/events_all_v2.csv').rename(columns={'ann_ms':'announcement_ms'})
v2=v2[v2.exchange.isin(['Upbit','Bithumb'])][['event_id','exchange','symbol','announcement_ms']].assign(collection_batch='v2')
K=pd.concat([v1,v2],ignore_index=True)
v1_idx=pd.read_parquet('raw/v1/aggtrades_index.parquet'); have_ticks=set(zip(v1_idx.event_id,v1_idx.venue))

ex=get("https://fapi.binance.com/fapi/v1/exchangeInfo",cache=False)
bn_onboard={s['symbol']:int(s['onboardDate']) for s in ex['symbols'] if s.get('contractType')=='PERPETUAL'}
fi={s['symbol']:int(s['fundingIntervalHours']) for s in get("https://fapi.binance.com/fapi/v1/fundingInfo",cache=False)}

def ext_sym(s): return re.sub(r'(?<=[A-Z])2$','',s)
def frame(c,eid,venue,market):
    d=pd.DataFrame(c,columns=CANDLE_COLS)
    d.insert(0,'event_id',eid); d.insert(1,'venue',venue); d.insert(2,'market',market); return d
def bybit_instr(sym):
    L=(get(f"https://api.bybit.com/v5/market/instruments-info?category=linear&symbol={sym}",cache=False).get('result') or {}).get('list') or []
    return L[0] if L else None
def first_daily(url):
    k=get(url)
    return int(k[0][0]) if isinstance(k,list) and k else None

def funding(venue,s,w0,w1,bybit_min):
    rows=[]
    if venue=='binance_perp':
        st=w0
        while st<w1:
            d=get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={st}&endTime={w1}&limit=1000")
            if not isinstance(d,list) or not d: break
            rows+=[(int(x['fundingTime']),float(x['fundingRate'])) for x in d]
            if len(d)<1000: break
            st=int(d[-1]['fundingTime'])+1
        known=fi.get(s); src='binance_fundingInfo(current)' if known else None
    else:
        e=w1
        while e>w0:
            L=(get(f"https://api.bybit.com/v5/market/funding/history?category=linear&symbol={s}&startTime={w0}&endTime={e}&limit=200").get('result') or {}).get('list') or []
            if not L: break
            rows+=[(int(x['fundingRateTimestamp']),float(x['fundingRate'])) for x in L]
            if len(L)<200: break
            e=min(int(x['fundingRateTimestamp']) for x in L)-1
        known=(bybit_min or 0)/60 or None; src='bybit_instruments_info(current)' if known else None
    fd=pd.DataFrame(sorted(set(rows)),columns=['timestamp_ms','funding_rate'])
    if len(fd):
        fd['interval_inferred_hours']=fd.timestamp_ms.diff().div(HOUR).round(2).bfill()
        fd['funding_interval_hours']=fd['interval_inferred_hours']
        fd['funding_interval_inferred']=True
        fd['funding_interval_source']='inferred_from_timestamp_gaps'
        fd['current_venue_interval_hours']=known
        if len(fd)==1:
            fd['funding_interval_hours']=known if known else (8.0 if venue=='binance_perp' else None)
            fd['funding_interval_source']=src or 'venue_default_8h'
    return fd

def spot_ticks(sym,a):
    tr=[]; s=a-60000
    while s<a+90000:
        d=get(f"https://data-api.binance.vision/api/v3/aggTrades?symbol={sym}&startTime={s}&endTime={a+90000}&limit=1000",min_interval=0.2)
        if not isinstance(d,list) or not d: break
        tr+=[(x['a'],float(x['p']),float(x['q']),int(x['T']),bool(x['m'])) for x in d]
        if len(d)<1000: break
        s=d[-1]['T']+1
    return tr,'rest_api_v3_aggTrades'

def perp_ticks(sym,a):
    days=sorted({dt.datetime.fromtimestamp((a+o)/1000,dt.timezone.utc).strftime('%Y-%m-%d') for o in (-60000,90000)})
    tr=[]; src=[]
    for day in days:
        fn=f'raw/bv/{sym}-{day}.parquet'
        if not os.path.exists(fn):
            r=requests.get(f"https://data.binance.vision/data/futures/um/daily/aggTrades/{sym}/{sym}-aggTrades-{day}.zip",timeout=300)
            if r.status_code!=200: pd.DataFrame({'missing':[r.status_code]}).to_parquet(fn); continue
            z=zipfile.ZipFile(io.BytesIO(r.content))
            df=pd.read_csv(z.open(z.namelist()[0]),header=None,usecols=range(7),dtype=str)
            df=df[df[0].str[0].str.isdigit()]
            df.columns=['a','p','q','f','l','T','m']
            df=pd.DataFrame({'a':df.a.astype('int64'),'p':df.p.astype(float),'q':df.q.astype(float),'T':df['T'].astype('int64'),'m':df.m.str.lower().eq('true')})
            df.to_parquet(fn)
        df=pd.read_parquet(fn)
        if 'missing' in df: continue
        df=df[(df['T']>=a-60000)&(df['T']<=a+90000)]
        tr+=list(zip(df.a,df.p,df.q,df['T'],df.m))
        src.append('data.binance.vision/futures/um/daily/aggTrades')
    return tr,(src[0] if src else 'missing')

def one(r):
    a=int(r.announcement_ms); s=ext_sym(r.symbol)+'USDT'; eid=r.event_id
    w0,w1=a-60*MIN,min(a+72*HOUR,NOW)
    res={'status':None,'spot_listing':None,'perp':None,'spot':None,'funding':None,'btc':None,'ticks':[], 'idx':[]}
    sp_at=len(candles('binance',s,a-3*HOUR,a))>0
    bn_at=len(candles('binance_perp',s,a-3*HOUR,a))>0
    spot_list=first_daily(f"https://data-api.binance.vision/api/v3/klines?symbol={s}&interval=1m&startTime=0&limit=1")
    res['spot_listing']=dict(event_id=eid,binance_spot_listing_ms=spot_list,
        binance_spot_listing_source='first_1m_kline(data-api.binance.vision)' if spot_list else None)
    if r.collection_batch=='v2':
        by=candles('bybit_perp',s,a-3*HOUR,a)
        o=dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,perp_symbol=s,binance_perp_at_ann=bn_at,bybit_perp_at_ann=len(by)>0)
        o['binance_perp_onboard_ms']=bn_onboard.get(s); o['binance_perp_onboard_source']=None
        if o['binance_perp_onboard_ms'] is None and bn_at:
            o['binance_perp_onboard_ms']=first_daily(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1m&startTime=0&limit=1")
            if o['binance_perp_onboard_ms']: o['binance_perp_onboard_source']='first_1m_kline'
        elif o['binance_perp_onboard_ms']: o['binance_perp_onboard_source']='exchangeInfo.onboardDate'
        bi=bybit_instr(s); o['bybit_perp_launch_ms']=int(bi['launchTime']) if bi else None
        o['bybit_funding_interval_min']=int(bi['fundingInterval']) if bi and bi.get('fundingInterval') else None
        o['perp_venue']='binance_perp' if bn_at else ('bybit_perp' if o['bybit_perp_at_ann'] else None)
        o['had_usdtm_perp_at_ann']=o['perp_venue'] is not None
        o['perp_listing_ms']=o['binance_perp_onboard_ms'] if o['perp_venue']=='binance_perp' else (o['bybit_perp_launch_ms'] if o['perp_venue']=='bybit_perp' else None)
        o['binance_spot_at_ann']=sp_at
        res['status']=o
        if o['perp_venue']:
            res['perp']=frame(candles(o['perp_venue'],s,w0,w1),eid,o['perp_venue'],s)
            fd=funding(o['perp_venue'],s,w0,w1,o['bybit_funding_interval_min'])
            if len(fd): fd.insert(0,'event_id',eid); fd.insert(1,'venue',o['perp_venue']); fd.insert(2,'symbol',s); res['funding']=fd
        c=candles('binance',s,w0,w1)
        if c: res['spot']=frame(c,eid,'binance_spot',s)
    res['btc']=frame(candles('binance_perp','BTCUSDT',w0,w1),eid,'binance_perp','BTCUSDT')
    for venue,exists,fn in [('binance_spot',sp_at,spot_ticks),('binance_perp',bn_at,perp_ticks)]:
        if not exists or (eid,venue) in have_ticks: continue
        tr,src=fn(s,a)
        df=pd.DataFrame(tr,columns=['agg_trade_id','price','qty','timestamp_ms','is_buyer_maker'])
        df.insert(0,'event_id',eid); df.insert(1,'venue',venue); df.insert(2,'symbol',s)
        res['ticks'].append(df)
        res['idx'].append(dict(event_id=eid,exchange=r.exchange,symbol=r.symbol,venue=venue,market=s,announcement_ms=a,n_ticks=len(df),source=src,in_original_speed_test=False))
    return res

def safe(r):
    try: return one(r)
    except Exception as e:
        print('ERR',r.event_id,repr(e)[:150],flush=True); return {'err':(r.event_id,repr(e)[:150])}

if __name__=='__main__':
    rows=[r for _,r in K.iterrows()]
    res=[]
    with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv)>1 else 6) as tp:
        for i,x in enumerate(tp.map(safe,rows)):
            res.append(x)
            if i%20==0: print(i,len(rows),flush=True)
    ok=[x for x in res if 'err' not in x]
    pd.DataFrame([x['err'] for x in res if 'err' in x],columns=['event_id','error']).to_csv(f'{OUT}/errors.csv',index=False)
    pd.DataFrame([x['status'] for x in ok if x['status']]).to_parquet(f'{OUT}/korean_perp_status.parquet',index=False)
    pd.DataFrame([x['spot_listing'] for x in ok]).to_parquet(f'{OUT}/binance_spot_listing.parquet',index=False)
    for k,name in [('perp','perp_candles_1m'),('spot','spot_candles_1m'),('funding','funding_history'),('btc','btc_candles_1m')]:
        parts=[x[k] for x in ok if x[k] is not None and len(x[k])]
        (pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()).to_parquet(f'{OUT}/{name}.parquet',index=False)
    t=[d for x in ok for d in x['ticks'] if len(d)]
    (pd.concat(t,ignore_index=True) if t else pd.DataFrame()).to_parquet(f'{OUT}/aggtrades.parquet',index=False)
    pd.DataFrame([d for x in ok for d in x['idx']]).to_parquet(f'{OUT}/aggtrades_index.parquet',index=False)
    print('done',len(ok),'errors',len(res)-len(ok))
