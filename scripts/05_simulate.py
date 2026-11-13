"""TP/SL/time-stop grid on 1m candles (from cache). Conservative: if TP and SL inside same candle -> SL.
Writes out/sim_trades.csv (one row per event x entry x rule)."""
import sys, csv, itertools, pandas as pd
sys.path.insert(0,'scripts'); from candles import candles, MIN
df=pd.read_csv('out/metrics_all_raw.csv')
TPS=[0.03,0.05,0.10,0.20,None]; SLS=[-0.05,-0.10,None]; TMAX=[5,15,60,240,1440]
COST=0.006
rows=[]
def sim(cs, e_ts, ep, tp, sl, tmax):
    end=e_ts+MIN+tmax*MIN; last=ep
    for c in cs:
        if c[0]<=e_ts: continue
        if c[0]>=end: break
        if sl is not None and c[3]<=ep*(1+sl): return sl
        if tp is not None and c[2]>=ep*(1+tp): return tp
        last=c[4]
    return last/ep-1
for _,r in df.iterrows():
    for pre,venue,mkt in [('ann_ext_',r.get('ext_at_ann'),r.get('ext_market')),('start_lst_',r.get('lst_venue'),r.get('lst_market'))]:
        ets=r.get(pre+'entry_ts')
        if pd.isna(ets) or pd.isna(venue) or pd.isna(r.get(pre+'r1440')): continue
        ets=int(ets); ep=r[pre+'entry_px']
        cs=candles(venue, mkt, ets-5*MIN, ets+1450*MIN)
        for tp,sl,tm in itertools.product(TPS,SLS,TMAX):
            rows.append(dict(event_id=r.event_id,exchange=r.exchange,product=r['product'],entry=pre[:-1],tp=tp,sl=sl,tmax=tm,ret=sim(cs,ets,ep,tp,sl,tm)-COST))
pd.DataFrame(rows).to_csv('out/sim_trades.csv',index=False); print(len(rows))
