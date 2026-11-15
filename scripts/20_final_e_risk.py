"""Final report section 4E: risk and bias. Reads data/ and analysis/strategy_table.csv. Writes analysis/e_*.csv.
Survivorship: delisted_daily_candles is daily data, used only for the size and direction of the bias. Included events get the
same daily calculation from their 1-minute candles: close of the announcement day (UTC) to the close of later days. Returns are
gross here (no 0.6% cost) on both sides, because only the difference between the two groups matters."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

ev=events(); G=ev.set_index('event_id')
dl=pd.read_parquet(f'{D}/delisted_daily_candles.parquet').sort_values(['event_id','timestamp_ms'])
rows=[]
for eid,g in dl.groupby('event_id'):
    if eid not in G.index or pd.isna(G.at[eid,'announcement_ms']): continue
    d0=(int(G.at[eid,'announcement_ms'])//DAY)*DAY; c=g.set_index('timestamp_ms').close
    if d0 not in c.index: continue
    r=dict(event_id=eid,group=G.at[eid,'group'],source='delisted_daily_candles',period=G.at[eid,'period'],year=int(G.at[eid,'year']),outlier_flag=False)
    for k in (1,7,30): r[f'd{k}']=c[d0+k*DAY]/c[d0]-1 if d0+k*DAY in c.index else np.nan
    rows.append(r)
SC=spot_candles(); PC=perp_candles()
for e in ev.dropna(subset=['announcement_ms']).itertuples():
    C=SC.get(e.event_id) or PC.get(e.event_id)
    if C is None: continue
    d0=(int(e.announcement_ms)//DAY)*DAY
    def close_at(t):
        j=int(np.searchsorted(C['ts'],t))-1
        return C['c'][j] if j>=0 and C['ts'][j]>=t-5*MIN and C['ts'][-1]>=t-MIN else None
    a,b=close_at(d0+DAY),close_at(d0+2*DAY)
    if a and b: rows.append(dict(event_id=e.event_id,group=e.group,source='included, 1m candles',period=e.period,year=e.year,outlier_flag=e.outlier_flag,d1=b/a-1))
sv=pd.DataFrame(rows); save(sv,'e_survivorship_events')
out=[]
for src,g in sv.groupby('source'):
    for k in ('d1','d7','d30'):
        if k in g and g[k].notna().any(): s=stats(g[k]); s.update(source=src,horizon=k); out.append(s)
save(pd.DataFrame(out),'e_survivorship')
x=pd.read_parquet(f'{D}/excluded_events.parquet'); no=x[x.reason.str.contains('no 1m candles on listing market',na=False)].event_id.unique()
gs=ev.assign(no_open_candles=ev.event_id.isin(no)).groupby('group').agg(n=('event_id','size'),no_open_candles=('no_open_candles','sum'))
gs['share_pct']=gs.no_open_candles/gs.n*100; save(gs.reset_index(),'e_no_open_candles')

st=pd.read_csv(f'{A}/strategy_table.csv')
KEY=['Upbit KRW | long | tick 1s | 5m','Bithumb official | long | tick 1s | 5m','Upbit KRW | short | trading open +1m on perp | 1440m | stop +20% pessimistic',
     'Upbit KRW | short | trading open +1m on perp | 1440m | stop none','Bithumb | short | trading open +1m on perp | 1440m | stop +20% pessimistic',
     'Bithumb | short | trading open +1m on perp | 1440m | stop none','Binance perp listing | short | perp open +1m on listed perp (events_metrics) | 1440m | stop none',
     'Binance spot with prior perp | short | spot open +1m on perp | 1440m | stop +20% pessimistic']
cols=['strategy','n','median','mean','worst','total_pnl','top5_share','mean_ex_top5','median_ex_top5','max_drawdown_pp','longest_losing_streak','losses_beyond_50']
save(st[st.strategy.isin(KEY)][cols].set_index('strategy').loc[[k for k in KEY if k in set(st.strategy)]].reset_index(),'e_concentration')
tr=pd.concat([pd.read_csv(f'{A}/trades_{x}.csv') for x in ('a','b')]); tr['stop']=tr['stop'].fillna('none')
w=tr.sort_values('ret').drop_duplicates('strategy')
save(w[w.strategy.isin(KEY)][['strategy','event_id','ret']].assign(ret_pct=lambda d:d.ret*100).merge(ev[['event_id','symbol','exchange','year']],on='event_id'),'e_worst_events')
print('E done')
