"""Final report section 4C: one strategy table (exchange x side x entry x hold) from analysis/trades_a.csv and trades_b.csv,
sorted by robustness, with per-period and per-year results, concentration, drawdown and losing streak.
Writes analysis/strategy_table.csv and analysis/c_long_short_availability.csv. Hyperliquid's coarse shorts are kept out of
this table (section F) because they use 5 min to 8 h candles."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

tr=pd.concat([pd.read_csv(f'{A}/trades_{x}.csv') for x in ('a','b')],ignore_index=True)
tr['stop']=tr['stop'].fillna('none'); tr['outlier_flag']=tr.outlier_flag.astype(bool)
st=summarize(tr,['strategy','group','side','entry','hold_min','stop'])
order={'survives':0,'n<20 in one period':1,'single period':2,'no':3,'negative in both':4}
st['rank_label']=st.label.map(order)
st['weaker_period_median']=st[['v1_median','v23_median']].min(axis=1)
st=st.sort_values(['rank_label','weaker_period_median','median'],ascending=[True,False,False]).drop(columns='rank_label')
yc=sorted([c for c in st.columns if c.startswith('y20')]); lead=[c for c in st.columns if c not in yc]
save(st[lead+yc],'strategy_table')

ev=events()
ps=pd.concat([pd.read_parquet(f'{D}/korean_perp_status.parquet')[['event_id','binance_perp_at_ann','bybit_perp_at_ann']],
              pd.read_parquet(f'{D}/perp_status_v3.parquet')[['event_id','binance_perp_at_ann','bybit_perp_at_ann']]]).drop_duplicates('event_id')
x=ev.merge(ps,on='event_id',how='left')
x['perp']=x.binance_perp_at_ann.fillna(False).astype(bool)|x.bybit_perp_at_ann.fillna(False).astype(bool)|x.ext_at_ann.isin(['binance_perp','bybit_perp'])
x['spot']=x.ext_at_ann.isin(['binance','bybit','okx','upbit','bithumb','coinbase'])|x.already_trading_elsewhere.fillna(False).astype(bool)&~x.ext_at_ann.isin(['binance_perp','bybit_perp'])
x['case']=np.select([x.perp&x.spot,x.spot&~x.perp,x.perp&~x.spot],['long and short','long only (no USDT perp)','short only (no external spot)'],'neither at the announcement')
av=x.groupby(['group','case']).size().unstack(fill_value=0); av['n']=av.sum(axis=1)
save(av.reset_index(),'c_long_short_availability')
print('C done',len(st),'strategies;',(st.label=='survives').sum(),'survive')
