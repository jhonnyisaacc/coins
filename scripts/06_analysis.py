"""Summaries for the study page. Writes out/events_metrics.csv and out/summary.json; prints tables."""
import pandas as pd, numpy as np, json, datetime as dt
COST=0.006
df=pd.read_csv('out/metrics_all_raw.csv')
df['group']=df.exchange+np.where(df['product']=='perp',' perp',' spot')
df.loc[df.exchange=='Upbit','group']=np.where(df.loc[df.exchange=='Upbit','markets'].str.contains('KRW'),'Upbit KRW','Upbit BTC/USDT only')
df['ann_hour_kst']=((df.ann_ms//3600000)+9)%24
df['new_token']=~df.already_trading_elsewhere.astype(bool)
df['ext_kind']=np.where(df.ext_at_ann.fillna('').str.contains('perp'),'perp',np.where(df.ext_at_ann.notna(),'spot',''))
H=[1,5,15,60,240,1440]
for p in ['ann_ext_','start_lst_','start_ext_']:
    for h in H:
        if p+f'r{h}' in df: df[p+f'n{h}']=df[p+f'r{h}']-COST
    if p+'peak_gain' in df:
        df[p+'outlier']=(df[p+'peak_gain']>2)|(df[p+f'r1440'].abs()>1)
df.to_csv('out/events_metrics.csv',index=False)
def summ(d,p):
    o={'n':int(d[p+'entry_px'].notna().sum())}
    if o['n']==0: return o
    for h in H:
        c=p+f'n{h}'
        if c in d and d[c].notna().sum()>0:
            o[f'win{h}']=float((d[c]>0).mean()*100) if d[c].notna().any() else None
            o[f'win{h}']=float((d[c].dropna()>0).mean()*100); o[f'med{h}']=float(d[c].median()*100); o[f'mean{h}']=float(d[c].mean()*100); o[f'n{h}']=int(d[c].notna().sum())
    for k in ['peak_gain','t_peak_min','dd_before_peak','dd_after_peak','missed_move','peak60_gain','t_peak60_min','low24']:
        if p+k in d and d[p+k].notna().any():
            o['med_'+k]=float(d[p+k].median()*(1 if k.startswith('t_') else 100))
            if k=='peak_gain': o['p_peak10']=float((d[p+k].dropna()>0.10).mean()*100); o['p_peak5']=float((d[p+k].dropna()>0.05).mean()*100)
    return o
out={}
order=['Upbit KRW','Upbit BTC/USDT only','Bithumb spot','Binance spot','Binance perp','OKX spot','Bybit spot','Coinbase spot']
for p,name in [('ann_ext_','ann_ext'),('start_lst_','start_lst'),('start_ext_','start_ext')]:
    out[name]={g:summ(df[df.group==g],p) for g in order}
    out[name+'_all']=summ(df,p)
# breakdowns
out['start_lst_by_newtoken']={f"{g}|{'new' if nt else 'existing'}":summ(df[(df.group==g)&(df.new_token==nt)],'start_lst_') for g in order for nt in [True,False]}
out['ann_ext_by_kind']={f"{g}|{k}":summ(df[(df.group==g)&(df.ext_kind==k)],'ann_ext_') for g in order for k in ['spot','perp']}
df['hour_bucket']=pd.cut(df.ann_hour_kst,[-1,8,12,18,24],labels=['00-08 KST','09-12 KST','13-18 KST','19-23 KST'])
out['ann_ext_korea_by_hour']={str(b):summ(df[(df.exchange.isin(['Upbit','Bithumb']))&(df.hour_bucket==b)],'ann_ext_') for b in df.hour_bucket.cat.categories}
# simulation grid
sim=pd.read_csv('out/sim_trades.csv')
sim['group']=sim.event_id.map(df.set_index('event_id').group)
best={}
for (g,e),d in sim.groupby(['group','entry']):
    agg=d.groupby(['tp','sl','tmax'],dropna=False).ret.agg(['count','mean','median',lambda x:(x>0).mean()*100]).reset_index()
    agg.columns=['tp','sl','tmax','n','mean','median','win']
    agg=agg[agg.n>=8].sort_values('mean',ascending=False)
    if len(agg): 
        top=agg.iloc[0]; best[f'{g}|{e}']={k:(None if pd.isna(v) else float(v)) for k,v in top.items()}
        # also baseline: hold 60 no TP/SL
        b=d[(d.tp.isna())&(d.sl.isna())&(d.tmax==60)].ret
        best[f'{g}|{e}']['hold60_mean']=float(b.mean()) if len(b) else None
out['sim_best']=best
# per-event list for page (compact)
ev=[]
for _,r in df.sort_values('ann_ms',ascending=False).iterrows():
    ev.append(dict(id=r.event_id,g=r.group,s=r.symbol,d=dt.datetime.fromtimestamp(r.ann_ms/1000,dt.timezone(dt.timedelta(hours=-3))).strftime('%Y-%m-%d'),
      nt=bool(r.new_token),ext=(r.ext_at_ann if isinstance(r.ext_at_ann,str) else ''),
      a5=None if pd.isna(r.get('ann_ext_n5')) else round(r.ann_ext_n5*100,1),a60=None if pd.isna(r.get('ann_ext_n60')) else round(r.ann_ext_n60*100,1),
      am=None if pd.isna(r.get('ann_ext_missed_move')) else round(r.ann_ext_missed_move*100,1),
      s5=None if pd.isna(r.get('start_lst_n5')) else round(r.start_lst_n5*100,1),s60=None if pd.isna(r.get('start_lst_n60')) else round(r.start_lst_n60*100,1),
      s1440=None if pd.isna(r.get('start_lst_n1440')) else round(r.start_lst_n1440*100,1),
      pk=None if pd.isna(r.get('start_lst_peak_gain')) else round(r.start_lst_peak_gain*100,1),tp=None if pd.isna(r.get('start_lst_t_peak_min')) else int(r.start_lst_t_peak_min),
      src=r.source))
out['events']=ev
json.dump(out,open('out/summary.json','w'),default=lambda x:None)
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
for k in ['ann_ext','start_lst','start_ext']:
    print('\n==',k); print(pd.DataFrame(out[k]).T[['n','win1','med1','win5','med5','win15','med15','win60','med60','win240','med240','win1440','med1440','mean60','med_peak_gain','p_peak10','med_t_peak_min','med_dd_before_peak','med_dd_after_peak','med_missed_move']].round(1).to_string())
print('\n== start_lst new vs existing'); print(pd.DataFrame(out['start_lst_by_newtoken']).T[['n','win5','med5','win60','med60','med1440','med_peak_gain','p_peak10','med_t_peak_min']].round(1).to_string())
print('\n== ann_ext by ext kind'); print(pd.DataFrame(out['ann_ext_by_kind']).T[['n','win5','med5','win60','med60','med_missed_move','med_peak_gain']].round(1).to_string())
print('\n== Korea ann by hour'); print(pd.DataFrame(out['ann_ext_korea_by_hour']).T[['n','win5','med5','win60','med60','med_missed_move']].round(1).to_string())
print('\n== best sim'); print(pd.DataFrame(best).T.round(3).to_string())
