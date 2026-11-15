"""Final report section 4A: Korean listings (Upbit KRW, Upbit BTC/USDT-only, Bithumb). Reads data/ only.
Writes analysis/a_*.csv and analysis/trades_a.csv (one row per event and strategy, used by 20_final_c_strategy.py).
Bithumb rows timed from the announcement (ticks, delayed longs, the announcement-to-open window and short entries at the
announcement) use announcement_time_official = True (v3, 2024-2025) only and report the v1 third-party times separately;
entries timed from the trading open pool v1 and v3."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

ev=events(); E=ev.set_index('event_id')
def kgroup(r):
    if r.exchange=='Bithumb': return 'Bithumb official' if r.bithumb_official else 'Bithumb third-party'
    return r.group
ev['kgroup']=ev.apply(kgroup,axis=1)
K=ev[ev.group.isin(['Upbit KRW','Upbit BTC/USDT only','Bithumb spot'])].copy()
K['ogroup']=np.where(K.exchange.eq('Bithumb'),'Bithumb',K.group)
ANN_GROUPS=['Upbit KRW','Upbit BTC/USDT only','Bithumb official','Bithumb third-party']
OPEN_GROUPS=['Upbit KRW','Upbit BTC/USDT only','Bithumb']
trades=[]

rows=[]
for g in ANN_GROUPS:
    d=K[K.kgroup.eq(g)]
    for col,lab in [*[(f'ann_ext_n{h}',f'n{h}') for h in (1,5,15,60,240,1440)],('ann_ext_r60_hi','n60_hi'),('ann_ext_missed_move','missed_move')]:
        x=d[['event_id','period','year','outlier_flag']].assign(ret=d[col]-(COST if lab=='n60_hi' else 0)).dropna(subset=['ret'])
        s=split_stats(x.assign(metric=lab,kgroup=g),['kgroup','metric']); rows.append(s)
        if lab in ('n5','n60','n1440'):
            trades.append(trade_rows(ev,f'{g} | long | announcement +1m delayed | {lab[1:]}m',  'long','external',f'announcement delayed',int(lab[1:]),None,dict(zip(x.event_id,x.ret))).assign(group=g))
save(pd.concat(rows),'a_delayed_long')

T,n_sus=ticks(); SC=spot_candles(); PC=perp_candles()
tick_rows=[]; prof=[]
for r in K.itertuples():
    v,Tr=event_ticks(T,r.event_id)
    if Tr is None: continue
    C=venue_candles(SC,PC,v,r.event_id)
    for drop in (False,True):
        Tv=tick_view(Tr,drop)
        if C is not None:
            for L in LAT:
                for h in (5,60):
                    x=tick_long(Tv,C,int(r.announcement_ms),int(L*1000),h)
                    if x is not None: tick_rows.append(dict(event_id=r.event_id,kgroup=r.kgroup,venue=v,L=L,hold_min=h,drop_suspect=drop,ret=x))
        if drop: continue
        mp=move_profile(Tv,int(r.announcement_ms))
        if mp: prof.append(dict(event_id=r.event_id,kgroup=r.kgroup,venue=v,**mp))
tk=pd.DataFrame(tick_rows).merge(ev[['event_id','period','year','outlier_flag']],on='event_id')
save(tk,'a_tick_long_trades')
save(split_stats(tk,['kgroup','L','hold_min','drop_suspect']),'a_tick_long')
for (g,L,h),x in tk[~tk.drop_suspect].groupby(['kgroup','L','hold_min']):
    if L in (0.5,1,2,5) :
        trades.append(trade_rows(ev,f'{g} | long | tick {L:g}s | {h}m','long','binance',f'tick {L:g}s',h,None,dict(zip(x.event_id,x.ret))).assign(group=g))

pf=pd.DataFrame(prof).merge(ev[['event_id','period','year','outlier_flag']],on='event_id'); save(pf,'a_speed_events')
sp=[]
for g,d in pf.groupby('kgroup'):
    for name,s in splits(d):
        if not len(s): continue
        big=s[s.m60>0.02]
        row=dict(kgroup=g,split=name,n=len(s),n_move60_over2=len(big))
        for c in ('m1','m2','m5','m30','m60','drift_pre60'): row[f'{c}_median']=s[c].median()*100
        for c in ('m1','m2','m5','m30'): row[f'share_{c}_median']=(big[c]/big.m60).median()*100 if len(big) else np.nan
        row['t_half_median_s']=big.t_half.median() if len(big) else np.nan
        row['t_first2_median_s']=s.t_first2.median(); row['n_first2']=int(s.t_first2.notna().sum())
        sp.append(row)
save(pd.DataFrame(sp),'a_speed')

rows=[]
for g in OPEN_GROUPS:
    d=K[K.ogroup.eq(g)]
    for col in ('start_lst_n60','start_lst_n1440','start_ext_n60','start_ext_n1440'):
        for nt in ('all','new_token'):
            dd=d if nt=='all' else d[d.new_token.fillna(False).astype(bool)]
            x=dd[['event_id','period','year','outlier_flag']].assign(ret=dd[col]).dropna(subset=['ret'])
            rows.append(split_stats(x.assign(ogroup=g,metric=col,subset=nt),['ogroup','metric','subset']))
            if nt=='all' and col in ('start_lst_n60','start_lst_n1440'):
                trades.append(trade_rows(ev,f'{g} | long | trading open +1m on listing exchange | {col[12:]}m','long','listing exchange','open delayed',int(col[12:]),None,dict(zip(x.event_id,x.ret))).assign(group=g))
save(pd.concat(rows),'a_open_long')

FM=funding_map()
win=[]
for r in K[K.kgroup.eq('Bithumb official')].itertuples():
    C=PC.get(r.event_id)
    if C is None or pd.isna(r.trading_open_ms): continue
    a,o=int(r.announcement_ms),int(r.trading_open_ms)
    e=delayed_entry(C,a)
    if e is None or o-a<5*MIN: continue
    i0,ep,t0=e; j,px=close_before(C,(o//MIN)*MIN,i0)
    if j is None or j<=i0 or C['ts'][-1]<o: continue
    F=FM.get((r.event_id,C['venue'])); fu=funding_sum(F,t0,o)
    e2=delayed_entry(C,o-60*MIN-MIN) if o-60*MIN>a else None
    last=None
    if e2 and e2[0]<j: last=C['c'][j]/e2[1]-1-COST
    win.append(dict(event_id=r.event_id,lag_min=(o-a)/MIN,long=px/ep-1-COST,short=-(px/ep-1)-COST+fu,funding=fu,
        peak=C['h'][i0+1:j+1].max()/ep-1,trough=C['l'][i0+1:j+1].min()/ep-1,last_hour_long=last,has_funding=F is not None))
bw=pd.DataFrame(win).merge(ev[['event_id','period','year','outlier_flag']],on='event_id'); save(bw,'a_bithumb_window_events')
rows=[]
for c in ('long','short','peak','trough','last_hour_long'):
    rows.append(split_stats(bw.assign(ret=bw[c],metric=c),['metric']))
w=pd.concat(rows); w['lag_median_min']=bw.lag_min.median(); save(w,'a_bithumb_window')
trades.append(trade_rows(ev,'Bithumb official | long | announcement +1m delayed on perp | until open','long','perp','announcement delayed','until open',None,dict(zip(bw.event_id,bw.long))).assign(group='Bithumb official'))
trades.append(trade_rows(ev,'Bithumb official | short | announcement +1m delayed on perp | until open','short','perp','announcement delayed','until open',None,dict(zip(bw.event_id,bw.short))).assign(group='Bithumb official'))

STOPS=[(None,'none'),(0.10,'exact'),(0.10,'pessimistic'),(0.20,'exact'),(0.20,'pessimistic'),(0.50,'exact'),(0.50,'pessimistic')]
GRID=[('announcement',0),('announcement',15),('announcement',60),('open',-60),('open',-15),('open',0),('open',15),('open',60),('open',240)]
def short_grid(D, groupcol, groups, grid, holds, stops):
    out=[]; nofund=set()
    for r in D[D[groupcol].isin(groups)].itertuples():
        C=PC.get(r.event_id)
        if C is None: continue
        F=FM.get((r.event_id,C['venue']))
        if F is None: nofund.add(r.event_id)
        a=int(r.announcement_ms)
        for base,off in grid:
            if base=='open' and pd.isna(r.trading_open_ms): continue
            if base=='announcement' and r.exchange=='Bithumb' and not r.bithumb_official: continue
            grp=('Bithumb official' if base=='announcement' and r.exchange=='Bithumb' else getattr(r,groupcol))
            trig=(a if base=='announcement' else int(r.trading_open_ms))+off*MIN
            if trig<a: continue
            for h in holds:
                for st,mode in stops:
                    x=short_trade(C,F,trig,h,st,mode)
                    if x: out.append(dict(event_id=r.event_id,grp=grp,venue=C['venue'],entry=f'{base} {off:+d}m',hold_min=h,
                                          stop='none' if st is None else f'+{int(st*100)}%',mode=mode,ret=x['ret'],funding=x['funding'],stopped=x['stopped'],max_up=x.get('max_up')))
    return pd.DataFrame(out).merge(ev[['event_id','period','year','outlier_flag']],on='event_id'), nofund

so,nf=short_grid(K,'ogroup',['Upbit KRW','Bithumb','Upbit BTC/USDT only'],[('open',0)],(60,240,1440),STOPS)
save(so,'a_short_open_trades')
save(split_stats(so,['grp','hold_min','stop','mode']),'a_short_open')
fr=[]
for (g,h),d in so[so.stop.eq('none')].groupby(['grp','hold_min']):
    paid=-d.funding*100
    fr.append(dict(grp=g,hold_min=h,n=len(d),funding_paid_mean=paid.mean(),funding_paid_median=paid.median(),share_short_pays=(d.funding<0).mean()*100,
        touch10=(d.max_up>=0.10).mean()*100,touch20=(d.max_up>=0.20).mean()*100,touch50=(d.max_up>=0.50).mean()*100,
        losses_beyond_50=int((d.ret<-0.5).sum())))
save(pd.DataFrame(fr),'a_short_open_funding_touch')
save(pd.DataFrame(sorted(nf),columns=['event_id']).merge(ev[['event_id','group','symbol','period']],on='event_id'),'a_short_no_funding')
for (g,h,st,mode),x in so.groupby(['grp','hold_min','stop','mode']):
    if mode=='exact' and st!='none': continue
    trades.append(trade_rows(ev,f'{g} | short | trading open +1m on perp | {h}m | stop {st}{" pessimistic" if st!="none" else ""}','short','perp','open delayed',h,st,dict(zip(x.event_id,x.ret))).assign(group=g))

gr,_=short_grid(K,'ogroup',['Upbit KRW','Bithumb'],GRID,(60,240,1440),[(None,'none'),(0.20,'pessimistic')])
save(split_stats(gr,['grp','entry','hold_min','stop']),'a_short_grid')
for (g,en,h,st),x in gr[gr.hold_min.eq(1440)].groupby(['grp','entry','hold_min','stop']):
    if en=='open +0m': continue
    trades.append(trade_rows(ev,f'{g} | short | {en} +1m on perp | {h}m | stop {st}{" pessimistic" if st!="none" else ""}','short','perp',en,h,st,dict(zip(x.event_id,x.ret))).assign(group=g))

pl=pd.read_parquet(f'{D}/perp_limits_snapshots.parquet')
pl=pl[pl.snapshot_date.eq(pl.snapshot_date.max())]
sym=K.assign(perp_symbol=K.symbol.str.replace(r'(?<=[A-Z])2$','',regex=True)+'USDT')
rows=[]
for g,d in sym.groupby('ogroup'):
    for v,p in pl.groupby('venue'):
        q=p[p.symbol.isin(d.perp_symbol)]
        num=lambda c: pd.to_numeric(q[c],errors='coerce')
        rows.append(dict(ogroup=g,venue=v,snapshot_date=pl.snapshot_date.max(),n_symbols_listed_now=len(q),
            max_leverage_median=num('max_leverage').median(),position_limit_usd_median=num('position_limit_notional_usd').median(),
            position_limit_usd_p10=num('position_limit_notional_usd').quantile(.1),tier1_notional_usd_median=num('tier1_notional_usd').median(),
            funding_cap_median=num('funding_cap').median()*100,funding_interval_h_median=num('funding_interval_hours').median()))
save(pd.DataFrame(rows),'a_perp_limits')

ev_sorted=ev.sort_values('announcement_ms'); ev_sorted['relisting']=ev_sorted.duplicated(['exchange','symbol'])
REL=ev_sorted.set_index('event_id').relisting
hour=lambda h: '00-08' if h<9 else ('09-15' if h<16 else '16-23')
attrs=ev.set_index('event_id')
def robust(x, name):
    x=x.copy(); a=attrs.loc[x.event_id]
    x['new_token']=a.new_token.fillna(False).astype(bool).map({True:'new token',False:'not new'}).values
    x['ann_hour_kst']=a.ann_hour_kst.map(hour).values
    x['relisting']=REL.loc[x.event_id].map({True:'relisting',False:'first listing'}).values
    x['year_s']=x.year.astype(str)
    out=[]
    for c in ('new_token','ann_hour_kst','relisting','year_s')+(('venue',) if 'venue' in x else ()):
        for k,g in x.groupby(c):
            s=stats(g.ret); s.update(strategy=name,split_by=c.replace('_s',''),value=k); out.append(s)
    return out
rb=[]
for g in ('Upbit KRW','Bithumb official','Upbit BTC/USDT only'):
    rb+=robust(tk[(tk.kgroup.eq(g))&tk.L.eq(1)&tk.hold_min.eq(5)&~tk.drop_suspect],f'{g} tick long 1s 5m')
for g in ('Upbit KRW','Bithumb'):
    rb+=robust(so[so.grp.eq(g)&so.hold_min.eq(1440)&so.stop.eq('+20%')&so['mode'].eq('pessimistic')],f'{g} short open 24h +20% stop pessimistic')
BTC=Candles(table('btc_candles_1m'),prefer=('binance_perp',))
def btc_ret(eid,t0,t1):
    B=BTC.get(eid)
    if B is None: return None
    i=int(np.searchsorted(B['ts'],t0))-1; j=int(np.searchsorted(B['ts'],t1))-1
    if i<0 or j<=i or B['ts'][-1]<t1-MIN: return None
    return B['c'][j]/B['c'][i]-1
ex=[]
for g in ('Upbit KRW','Bithumb'):
    d=so[so.grp.eq(g)&so.hold_min.eq(1440)&so.stop.eq('none')]
    for r in d.itertuples():
        C=PC.get(r.event_id); e=delayed_entry(C,int(attrs.at[r.event_id,'trading_open_ms'])); b=btc_ret(r.event_id,e[2],e[2]+1440*MIN)
        ex.append(dict(event_id=r.event_id,grp=g,ret=r.ret,btc=b))
ex=pd.DataFrame(ex); exb=ex.dropna(subset=['btc'])
for g,d in exb.groupby('grp'):
    s=stats(d.ret+d.btc); s.update(strategy=f'{g} short open 24h no stop',split_by='excess over BTC (short minus short BTC)',value=f'{len(d)} of {int(ex.grp.eq(g).sum())} events have BTC candles'); rb.append(s)
    s=stats(d.ret); s.update(strategy=f'{g} short open 24h no stop',split_by='same events, raw',value=f'{len(d)} events'); rb.append(s)
save(pd.DataFrame(rb)[['strategy','split_by','value','n','median','mean','win','p10','p90','worst']],'a_robust')

ta=pd.concat([t for t in trades if len(t)],ignore_index=True); save(ta,'trades_a')
print('A done',len(ta),'trades; ticks',len(tk),'profiles',len(pf),'shorts',len(so))
