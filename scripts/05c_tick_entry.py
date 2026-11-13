"""Tick-level reaction-speed test using Binance aggTrades (spot and USD-M perp) for events whose
external venue at the announcement is Binance. Entry = last trade price at ann + d seconds
(d = 1,2,5,10,30,60), +0.2% slippage per side & 0.1% fee per side (0.6% round trip). Exit at 1m closes.
Writes out/tick_entry.csv."""
import sys, pandas as pd
sys.path.insert(0,'scripts'); from common import get; from candles import candles, MIN
df=pd.read_csv('out/metrics_all_raw.csv'); rows=[]
D=[0,1,2,5,10,30,60]
for _,r in df.iterrows():
    v=r.get('ext_at_ann')
    if v not in ('binance','binance_perp'): continue
    a=int(r.ann_ms); sym=r.ext_market
    base='https://data-api.binance.vision/api/v3/aggTrades' if v=='binance' else 'https://fapi.binance.com/fapi/v1/aggTrades'
    tr=[]; s=a-60000
    while s < a+90000:
        d=get(f"{base}?symbol={sym}&startTime={s}&endTime={a+90000}&limit=1000",min_interval=0.2)
        if not isinstance(d,list) or not d: break
        tr+=d; 
        if len(d)<1000: break
        s=d[-1]['T']+1
    if not tr: continue
    pre=[t for t in tr if t['T']<a]
    if not pre: continue
    p0=float(pre[-1]['p'])
    cs=candles(v, sym, a-5*MIN, a+1450*MIN)
    o=dict(event_id=r.event_id,venue=v,n_trades=len(tr),pre_px=p0)
    for dd in D:
        upto=[t for t in tr if t['T']<=a+dd*1000]
        ep=float(upto[-1]['p']) if upto else p0
        o[f'move_{dd}s']=ep/p0-1
        for h in [5,15,60,240]:
            t=a+dd*1000+h*MIN; prev=[c for c in cs if c[0]+MIN<=t]
            if prev: o[f'e{dd}s_n{h}']=prev[-1][4]/ep-1-0.006
    # first time price moved >= 50% of the 60 s move
    m60=o['move_60s']; tt=None
    if abs(m60)>0.01:
        for t in tr:
            if t['T']>=a and (float(t['p'])/p0-1)/m60>=0.5: tt=(t['T']-a)/1000; break
    o['t_half_move_s']=tt
    rows.append(o)
pd.DataFrame(rows).to_csv('out/tick_entry.csv',index=False); print(len(rows))
