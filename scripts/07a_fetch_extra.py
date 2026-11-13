"""Extra datasets for the public release (Korean events: perp status, 1m candles -60m..+72h, funding;
aggTrades for speed-test candidates). Output parquet files in extra/."""
import sys, io, zipfile, datetime as dt, pandas as pd, numpy as np
sys.path.insert(0,'scripts'); from common import get; from candles import candles, MIN, HOUR
from concurrent.futures import ThreadPoolExecutor
import requests
m=pd.read_csv('out/events_metrics.csv')
kor=m[m.exchange.isin(['Upbit','Bithumb'])].copy()
NOW=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
ex=get("https://fapi.binance.com/fapi/v1/exchangeInfo",cache=False)
bn_onboard={s['symbol']:int(s['onboardDate']) for s in ex['symbols'] if s.get('contractType')=='PERPETUAL'}
fi={s['symbol']:int(s['fundingIntervalHours']) for s in get("https://fapi.binance.com/fapi/v1/fundingInfo",cache=False)}
def bybit_instr(sym):
    d=get(f"https://api.bybit.com/v5/market/instruments-info?category=linear&symbol={sym}",cache=False)
    L=(d.get('result') or {}).get('list') or []
    return L[0] if L else None
def ext_sym(s):
    import re; return re.sub(r'(?<=[A-Z])2$','',s)
def one(r):
    a=int(r.ann_ms); s=ext_sym(r.symbol)+'USDT'; o=dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,perp_symbol=s)
    bn=candles('binance_perp',s,a-3*HOUR,a); by=candles('bybit_perp',s,a-3*HOUR,a)
    o['binance_perp_at_ann']=len(bn)>0; o['bybit_perp_at_ann']=len(by)>0
    o['binance_perp_onboard_ms']=bn_onboard.get(s)
    if o['binance_perp_onboard_ms'] is None and o['binance_perp_at_ann']:
        k=get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime=0&limit=1")
        if isinstance(k,list) and k: o['binance_perp_onboard_ms']=int(k[0][0]); o['binance_perp_onboard_source']='first_daily_kline'
    elif o['binance_perp_onboard_ms']: o['binance_perp_onboard_source']='exchangeInfo.onboardDate'
    bi=bybit_instr(s); o['bybit_perp_launch_ms']=int(bi['launchTime']) if bi else None
    o['bybit_funding_interval_min']=int(bi['fundingInterval']) if bi and bi.get('fundingInterval') else None
    o['perp_venue']='binance_perp' if o['binance_perp_at_ann'] else ('bybit_perp' if o['bybit_perp_at_ann'] else None)
    o['had_usdtm_perp_at_ann']=o['perp_venue'] is not None
    o['perp_listing_ms']=o['binance_perp_onboard_ms'] if o['perp_venue']=='binance_perp' else (o['bybit_perp_launch_ms'] if o['perp_venue']=='bybit_perp' else None)
    sp=candles('binance',s,a-3*HOUR,a); o['binance_spot_at_ann']=len(sp)>0
    w0,w1=a-60*MIN,min(a+72*HOUR,NOW)
    pc=pd.DataFrame(); scd=pd.DataFrame(); fd=pd.DataFrame()
    if o['perp_venue']:
        c=candles(o['perp_venue'],s,w0,w1)
        pc=pd.DataFrame(c,columns=['timestamp_ms','open','high','low','close','quote_volume']); pc.insert(0,'event_id',r.event_id); pc.insert(1,'venue',o['perp_venue']); pc.insert(2,'market',s)
        # funding
        rows=[]
        if o['perp_venue']=='binance_perp':
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
                d=get(f"https://api.bybit.com/v5/market/funding/history?category=linear&symbol={s}&startTime={w0}&endTime={e}&limit=200")
                L=(d.get('result') or {}).get('list') or []
                if not L: break
                rows+=[(int(x['fundingRateTimestamp']),float(x['fundingRate'])) for x in L]
                if len(L)<200: break
                e=min(int(x['fundingRateTimestamp']) for x in L)-1
            known=(o['bybit_funding_interval_min'] or 0)/60 or None; src='bybit_instruments_info(current)' if known else None
        fd=pd.DataFrame(sorted(set(rows)),columns=['timestamp_ms','funding_rate'])
        if len(fd):
            gaps=fd.timestamp_ms.diff().div(HOUR).round(2)
            fd['interval_inferred_hours']=gaps.bfill()
            fd['funding_interval_hours']=fd['interval_inferred_hours']
            fd['funding_interval_inferred']=True
            fd['funding_interval_source']='inferred_from_timestamp_gaps'
            if known:
                fd['current_venue_interval_hours']=known
            if len(fd)==1:
                fd['funding_interval_hours']=known if known else (8.0 if o['perp_venue']=='binance_perp' else None)
                fd['funding_interval_source']=src or 'venue_default_8h'
            fd.insert(0,'event_id',r.event_id); fd.insert(1,'venue',o['perp_venue']); fd.insert(2,'symbol',s)
    if o['binance_spot_at_ann'] or True:
        c=candles('binance',s,w0,w1)
        if c:
            scd=pd.DataFrame(c,columns=['timestamp_ms','open','high','low','close','quote_volume']); scd.insert(0,'event_id',r.event_id); scd.insert(1,'venue','binance_spot'); scd.insert(2,'market',s)
    return o,pc,scd,fd
with ThreadPoolExecutor(6) as tp: res=list(tp.map(one,[r for _,r in kor.iterrows()]))
pd.DataFrame([x[0] for x in res]).to_parquet('extra/korean_perp_status.parquet',index=False)
for i,name in [(1,'perp_candles_1m'),(2,'spot_candles_1m'),(3,'funding_history')]:
    parts=[x[i] for x in res if len(x[i])]
    df=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    df.to_parquet(f'extra/{name}.parquet',index=False); print(name,len(df))
print('status',len(res))
