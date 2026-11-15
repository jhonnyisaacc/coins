"""Final report section 4B: other exchanges (Binance spot with a prior perp, Binance perp listings, OKX and Bybit spot,
Coinbase). Reads data/ only. Writes analysis/b_*.csv and analysis/trades_b.csv."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

ev=events(); E=ev.set_index('event_id'); trades=[]
T,_=ticks(); SC=spot_candles(); PC=perp_candles(); FM=funding_map()
STOPS=[(None,'none'),(0.20,'exact'),(0.20,'pessimistic'),(0.50,'pessimistic')]

def shorts(D, trig_of, holds, stops=STOPS, venue=None, label=None):
    out=[]
    for r in D.itertuples():
        C=PC.get(r.event_id,venue); trig=trig_of(r)
        if C is None or trig is None or pd.isna(trig): continue
        F=FM.get((r.event_id,C['venue']))
        for h in holds:
            for st,mode in stops:
                x=short_trade(C,F,int(trig),h,st,mode)
                if x: out.append(dict(event_id=r.event_id,sub=label(r) if label else 'all',venue=C['venue'],hold_min=h,stop='none' if st is None else f'+{int(st*100)}%',
                                      mode=mode,ret=x['ret'],funding=x['funding'],max_up=x.get('max_up'),has_funding=F is not None))
    return pd.DataFrame(out).merge(ev[['event_id','period','year','outlier_flag']],on='event_id')

def add(df, grp, side, entry, venue):
    for (sub,h,st,mode),x in df.groupby(['sub','hold_min','stop','mode']):
        if st!='none' and mode=='exact': continue
        g=grp if sub=='all' else f'{grp} [{sub}]'
        trades.append(trade_rows(ev,f'{g} | {side} | {entry} | {h}m | stop {st}{" pessimistic" if st!="none" else ""}',side,venue,entry,h,st,dict(zip(x.event_id,x.ret))).assign(group=g))

def tick_table(D, name, venues=('binance_spot','binance_perp')):
    rows=[]; prof=[]
    for r in D.itertuples():
        v,Tr=next(((v,T[(r.event_id,v)]) for v in venues if (r.event_id,v) in T),(None,None))
        if Tr is None: continue
        C=venue_candles(SC,PC,v,r.event_id); mp=move_profile(Tr,int(r.announcement_ms))
        if mp: prof.append(dict(event_id=r.event_id,venue=v,**mp))
        if C is None: continue
        for L in LAT:
            for h in (5,60):
                x=tick_long(Tr,C,int(r.announcement_ms),int(L*1000),h)
                if x is not None: rows.append(dict(event_id=r.event_id,venue=v,L=L,hold_min=h,ret=x))
    tk=pd.DataFrame(rows).merge(ev[['event_id','period','year','outlier_flag']],on='event_id').assign(group=name)
    pf=pd.DataFrame(prof).merge(ev[['event_id','period','year','outlier_flag']],on='event_id').assign(group=name)
    for (L,h),x in tk.groupby(['L','hold_min']):
        if L in (1,3,5): trades.append(trade_rows(ev,f'{name} | long | tick {L:g}s | {h}m','long',x.venue.iloc[0],f'tick {L:g}s',h,None,dict(zip(x.event_id,x.ret))).assign(group=name))
    return tk,pf

def speed(pf):
    rows=[]
    for name,s in splits(pf):
        if not len(s): continue
        rows.append(dict(split=name,n=len(s),m1_median=s.m1.median()*100,m5_median=s.m5.median()*100,m60_median=s.m60.median()*100,
            drift_pre60_median=s.drift_pre60.median()*100,t_first2_median_s=s.t_first2.median(),n_first2=int(s.t_first2.notna().sum()),t_half_median_s=s[s.m60>0.02].t_half.median()))
    return pd.DataFrame(rows)

out_t=[]; out_s=[]; out_v=[]
bs=ev[ev.group.eq('Binance spot')&ev.ext_at_ann.eq('binance_perp')]
tk,pf=tick_table(bs,'Binance spot with prior perp'); out_t.append(tk); out_v.append(speed(pf).assign(group='Binance spot with prior perp'))
src=lambda r: {'binance_cms_hodler_airdrops':'HODLer Airdrops','binance_cms':'Binance Will List','binance_cms_launchpool':'Launchpool'}.get(r.ann_source,r.ann_source)
for trig,entry in [(lambda r: r.announcement_ms,'announcement +1m on perp'),(lambda r: r.trading_open_ms,'spot open +1m on perp')]:
    s=shorts(bs,trig,(60,240,1440),label=None); s2=shorts(bs,trig,(60,240,1440),label=src)
    for x in (s,s2): x['group']='Binance spot with prior perp'; x['entry']=entry
    out_s+= [s,s2]; add(s,'Binance spot with prior perp','short',entry,'binance_perp'); add(s2,'Binance spot with prior perp','short',entry,'binance_perp')

bp=ev[ev.group.eq('Binance perp')]
s=shorts(bp,lambda r: r.trading_open_ms,(60,240,1440),stops=STOPS+[(0.10,'pessimistic')],venue='binance_perp'); s['group']='Binance perp listing'; s['entry']='perp open +1m on listed perp'
out_s.append(s); add(s,'Binance perp listing','short','perp open +1m on listed perp','binance_perp')
tk,pf=tick_table(bp,'Binance perp listing (spot ticks)',venues=('binance_spot',)); out_t.append(tk); out_v.append(speed(pf).assign(group='Binance perp listing (spot ticks)'))

for grp in ('OKX spot','Bybit spot'):
    d=ev[ev.group.eq(grp)]
    s=shorts(d,lambda r: r.trading_open_ms,(60,240,1440)); s['group']=grp; s['entry']='open +1m on external perp'
    out_s.append(s); add(s,grp,'short','open +1m on external perp','perp')

def metric_shorts(D, prefix, venue_of, grp, entry):
    """No-stop shorts from events_metrics returns (works where candles are not stored), funding over (entry, exit]."""
    out=[]
    for r in D.itertuples():
        v=venue_of(r); em=getattr(r,f'{prefix}entry_ms')
        if v not in ('binance_perp','bybit_perp') or pd.isna(em): continue
        F=FM.get((r.event_id,v)); t0=int(em)+MIN
        for h in (60,240,1440):
            x=getattr(r,f'{prefix}r{h}')
            if pd.isna(x): continue
            fu=funding_sum(F,t0,t0+h*MIN)
            out.append(dict(event_id=r.event_id,sub='all',venue=v,hold_min=h,stop='none',mode='none',ret=-x-COST+fu,funding=fu,max_up=np.nan,has_funding=F is not None))
    x=pd.DataFrame(out).merge(ev[['event_id','period','year','outlier_flag']],on='event_id'); x['group']=grp; x['entry']=entry
    out_s.append(x); add(x,grp,'short',entry,'perp'); return x
metric_shorts(bp,'start_lst_',lambda r:'binance_perp','Binance perp listing','perp open +1m on listed perp (events_metrics)')
for grp in ('OKX spot','Bybit spot'):
    metric_shorts(ev[ev.group.eq(grp)],'start_ext_',lambda r:r.ext_at_start,grp,'open +1m on external perp (events_metrics)')

cb=ev[ev.group.eq('Coinbase spot')].copy()
cb['status']=np.where(cb.coinbase_usd_product_status_now.eq('delisted'),'delisted now','not delisted')
tk,pf=tick_table(cb,'Coinbase (Binance perp ticks)',venues=('binance_perp',)); out_t.append(tk)
out_v.append(speed(pf).assign(group='Coinbase (Binance perp ticks)'))
s=shorts(cb,lambda r: r.coinbase_full_trading_ms,(60,240,1440),label=lambda r: r.status); s['group']='Coinbase'; s['entry']='full trading +1m on Binance perp'
sa=s.assign(sub='all'); out_s+=[s,sa]; add(sa,'Coinbase','short','full trading +1m on Binance perp','binance_perp'); add(s,'Coinbase','short','full trading +1m on Binance perp','binance_perp')
s=shorts(cb,lambda r: r.announcement_ms,(60,1440),stops=[(None,'none')]); s['group']='Coinbase'; s['entry']='announcement +1m on Binance perp'
out_s.append(s); add(s,'Coinbase','short','announcement +1m on Binance perp','binance_perp')

rows=[]
for grp,sel in [('Binance spot with prior perp',bs),('Binance perp listing',bp),('OKX spot',ev[ev.group.eq('OKX spot')]),('Bybit spot',ev[ev.group.eq('Bybit spot')]),('Coinbase',cb)]:
    for col in ('ann_ext_n5','ann_ext_n60','ann_ext_n1440','start_lst_n60','start_lst_n1440','start_ext_n60','start_ext_n1440'):
        x=sel[['event_id','period','year','outlier_flag']].assign(ret=sel[col]).dropna(subset=['ret'])
        if not len(x): continue
        rows.append(split_stats(x.assign(group=grp,metric=col),['group','metric']))
        if col in ('ann_ext_n60','start_lst_n60','start_lst_n1440','start_ext_n60','start_ext_n1440'):
            ent='announcement +1m external' if col.startswith('ann') else ('open +1m on listing exchange' if col.startswith('start_lst') else 'open +1m external')
            h=int(col.rsplit('_n',1)[1])
            trades.append(trade_rows(ev,f'{grp} | long | {ent} | {h}m','long','external' if 'ext' in col else 'listing exchange',ent,h,None,dict(zip(x.event_id,x.ret))).assign(group=grp))
    if grp=='Coinbase':
        for st,d in sel.groupby('status'):
            x=d[['event_id','period','year','outlier_flag']].assign(ret=d.start_lst_n1440).dropna(subset=['ret'])
            rows.append(split_stats(x.assign(group=f'Coinbase [{st}]',metric='start_lst_n1440'),['group','metric']))
save(pd.concat(rows),'b_delayed')

tk=pd.concat(out_t,ignore_index=True); save(tk,'b_tick_long_trades'); save(split_stats(tk,['group','L','hold_min']),'b_tick_long')
save(pd.concat(out_v,ignore_index=True),'b_speed')
sh=pd.concat(out_s,ignore_index=True); save(sh,'b_short_trades')
save(split_stats(sh,['group','entry','sub','hold_min','stop','mode']),'b_short')
fr=[]
for (g,en,sub,h),d in sh[sh.stop.eq('none')].groupby(['group','entry','sub','hold_min']):
    fr.append(dict(group=g,entry=en,sub=sub,hold_min=h,n=len(d),funding_paid_mean=(-d.funding*100).mean(),share_short_pays=(d.funding<0).mean()*100,
        n_no_funding=int((~d.has_funding).sum()),touch10=(d.max_up>=.1).mean()*100,touch20=(d.max_up>=.2).mean()*100,touch50=(d.max_up>=.5).mean()*100,losses_beyond_50=int((d.ret<-.5).sum())))
save(pd.DataFrame(fr),'b_short_funding_touch')
tb=pd.concat([t for t in trades if len(t)],ignore_index=True); save(tb,'trades_b')
print('B done',len(tb),'trades')
