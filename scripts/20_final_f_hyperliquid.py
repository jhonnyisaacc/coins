"""Final report section 4F: Hyperliquid as a perp venue. Reads data/ only. Writes analysis/f_*.csv.
Hyperliquid candles are 5 min to 8 h, so shorts are coarse: entry at the close of the HL candle containing the trading open,
exit at the close of the HL candle containing entry + 24 h, funding from hyperliquid_funding over (entry, exit]. The same
timestamps are priced on Binance (last 1m close at or before them, Binance funding), and compared with the 1-minute Binance entry."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

ev=events(); G=ev.set_index('event_id')
hs=pd.read_parquet(f'{D}/hyperliquid_perp_status.parquet')
kp=pd.read_parquet(f'{D}/korean_perp_status.parquet')[['event_id','binance_perp_at_ann','bybit_perp_at_ann']]
h=hs.merge(kp,on='event_id',how='left').merge(ev[['event_id','group','year','period']],on='event_id')
h['hl']=h.hl_perp_at_ann.fillna(False).astype(bool); h['cex']=h.binance_perp_at_ann.fillna(False).astype(bool)|h.bybit_perp_at_ann.fillna(False).astype(bool)
cov=h.groupby(['group','year']).agg(n=('event_id','size'),hl_perp_at_ann=('hl','sum'),hl_only=('hl',lambda s:(s&~h.loc[s.index,'cex']).sum()))
cov['hl_share_pct']=cov.hl_perp_at_ann/cov.n*100; c2=h.groupby('group').agg(n=('event_id','size'),hl_perp_at_ann=('hl','sum'),hl_only=('hl',lambda s:(s&~h.loc[s.index,'cex']).sum()))
c2['hl_share_pct']=c2.hl_perp_at_ann/c2.n*100; c2['year']='all'
tot=c2[['n','hl_perp_at_ann','hl_only']].sum().to_frame().T.assign(group='All Korean',year='all'); tot['hl_share_pct']=tot.hl_perp_at_ann/tot.n*100
save(pd.concat([cov.reset_index(),c2.reset_index(),tot]),'f_coverage')

IV={'5m':5,'15m':15,'1h':60,'4h':240,'8h':480}
hc=pd.read_parquet(f'{D}/hyperliquid_candles.parquet').sort_values(['event_id','timestamp_ms'])
hf=pd.read_parquet(f'{D}/hyperliquid_funding.parquet'); HF={e:(g.timestamp_ms.to_numpy('int64'),g.funding_rate.to_numpy(float)) for e,g in hf.sort_values('timestamp_ms').groupby('event_id')}
PC=perp_candles(); FM=funding_map(); rows=[]
for eid,g in hc.groupby('event_id'):
    if eid not in G.index or pd.isna(G.at[eid,'trading_open_ms']): continue
    o=int(G.at[eid,'trading_open_ms']); iv=IV[g.interval.iloc[0]]*MIN; ts=g.timestamp_ms.to_numpy('int64'); cl=g.close.to_numpy(float)
    i=int(np.searchsorted(ts,o,side='right'))-1
    if i<0 or ts[i]+iv<=o: continue
    te=int(ts[i])+iv; j=int(np.searchsorted(ts,te+DAY-1,side='right'))-1
    if j<=i or ts[j]+iv<te+DAY: continue
    tx=int(ts[j])+iv; fu=funding_sum(HF.get(eid),te,tx)
    r=dict(event_id=eid,group=G.at[eid,'group'],interval=g.interval.iloc[0],period=G.at[eid,'period'],year=int(G.at[eid,'year']),outlier_flag=bool(G.at[eid,'outlier_flag']),
           hl=-(cl[j]/cl[i]-1)-COST+fu,hl_funding=fu,has_hl_funding=eid in HF)
    k=(g.timestamp_ms>=o)&(g.timestamp_ms<o+DAY); r['hl_vol24_usd']=float((g.volume_base[k]*g.close[k]).sum())
    C=PC.get(eid,'binance_perp')
    if C is not None:
        a=int(np.searchsorted(C['ts'],te))-1; b=int(np.searchsorted(C['ts'],tx))-1
        if a>=0 and b>a and C['ts'][-1]>=tx-MIN:
            F=FM.get((eid,'binance_perp')); bf=funding_sum(F,te,tx); r.update(binance_same=-(C['c'][b]/C['c'][a]-1)-COST+bf,binance_funding=bf)
        x=short_trade(C,FM.get((eid,'binance_perp')),o,1440)
        if x: r['binance_1m']=x['ret']
        k=(C['ts']>=o)&(C['ts']<o+DAY); r['binance_vol24_usd']=float((C['v'][k]*C['c'][k]).sum())
    rows.append(r)
f=pd.DataFrame(rows); save(f,'f_short_events')
out=[]
for grp,g in f.groupby('group'):
    both=g.dropna(subset=['binance_same','binance_1m'])
    for col,lab,d in [('hl','HL coarse short, all with HL candles',g),('hl','HL coarse short, events also on Binance',both),('binance_same','Binance at the HL timestamps',both),('binance_1m','Binance 1m entry at the open',both)]:
        s=split_stats(d.assign(ret=d[col],grp=grp,measure=lab),['grp','measure']); out.append(s)
fs=pd.concat(out); save(fs,'f_short')
fx=[]
for grp,g in f.groupby('group'):
    both=g.dropna(subset=['binance_same'])
    v=g.dropna(subset=['binance_vol24_usd']); v=v[v.binance_vol24_usd>0]
    fx.append(dict(grp=grp,n=len(both),hl_funding_paid_mean=-both.hl_funding.mean()*100,binance_funding_paid_mean=-both.binance_funding.mean()*100,
                   n_vol=len(v),hl_over_binance_vol24_median=(v.hl_vol24_usd/v.binance_vol24_usd).median(),intervals=';'.join(f'{k}:{n}' for k,n in g.interval.value_counts().items())))
save(pd.DataFrame(fx),'f_funding_volume')
print('F done',len(f))
