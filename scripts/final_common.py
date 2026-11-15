"""Shared definitions for the final report (scripts/20_final_*.py). Reads data/ only; no network.
Method (documented in docs/FINAL_REPORT.md):
- COST = 0.6% round trip. Returns are fractions here and percentages in the report.
- Delayed entry: close of the first 1m candle opening in [trigger minute + 1, + 5 min] (04_metrics.metrics); exit after h minutes
  at the close of the last candle opening before entry-candle close + h.
- Tick entry at latency L: first aggTrade at or after announcement + L; exit at the open of the 1m candle h minutes after the
  entry trade's minute (first candle at or after that minute, within 5 minutes) on the same venue.
- Short: -r - COST + funding received (positive rate = short receives), funding summed over (entry, exit].
- Stops: exact fill at the stop level, or pessimistic fill at the close of the 1m candle whose high touches it."""
import glob, os, re, json, numpy as np, pandas as pd
D='data'; A='analysis'; MIN=60_000; HOUR=3_600_000; DAY=86_400_000; COST=0.006
os.makedirs(A,exist_ok=True)

def table(name, extra=()):
    """A published table: base file, .partNN files, and <name>_v2_<year> / _v3_<year> files (exact names only)."""
    pats=[f'{D}/{name}.parquet',f'{D}/{name}.part*.parquet']+[f'{D}/{name}_{b}[0-9][0-9][0-9][0-9]{p}.parquet' for b in ('','v2_','v3_') for p in ('','.part*')]
    pats+=[f'{D}/{x}.parquet' for x in extra]+[f'{D}/{x}.part*.parquet' for x in extra]
    fs=sorted({f for p in pats for f in glob.glob(p)})
    return pd.concat([pd.read_parquet(f) for f in fs],ignore_index=True) if fs else pd.DataFrame()

def events():
    m=pd.read_parquet(f'{D}/events_metrics.parquet'); e=pd.read_parquet(f'{D}/events.parquet')
    m=m.merge(e[['event_id','outlier_flag','coinbase_full_trading_ms','coinbase_usd_product_status_now','markets_opened']],on='event_id',how='left')
    m['period']=np.where(m.collection_batch.eq('v1'),'v1','v2+v3')
    m['t_ms']=m.announcement_ms.fillna(m.trading_open_ms).astype('int64')
    m['year']=pd.to_datetime(m.t_ms,unit='ms',utc=True).dt.year
    m['outlier_flag']=m.outlier_flag.fillna(False).astype(bool)
    m['bithumb_official']=m.exchange.eq('Bithumb')&m.announcement_time_official.fillna(False).astype(bool)&m.collection_batch.eq('v3')
    return m

class Candles:
    """Per-(event, venue) 1m candles as numpy arrays. get(eid) returns the first venue in `prefer` that exists."""
    def __init__(self, df, prefer=('binance_perp','bybit_perp')):
        self.d={}; self.prefer=prefer
        if not len(df): return
        df=df.drop_duplicates(['event_id','venue','timestamp_ms']).sort_values(['event_id','venue','timestamp_ms'])
        for (eid,v),g in df.groupby(['event_id','venue'],sort=False):
            self.d[(eid,v)]=dict(venue=v,ts=g.timestamp_ms.to_numpy('int64'),o=g.open.to_numpy(float),h=g.high.to_numpy(float),
                                 l=g.low.to_numpy(float),c=g.close.to_numpy(float),v=g.volume.to_numpy(float))
    def get(self, eid, venue=None):
        if venue: return self.d.get((eid,venue))
        for v in self.prefer:
            if (eid,v) in self.d: return self.d[(eid,v)]
        return None

def perp_candles(): return Candles(table('perp_candles_1m',extra=('perp_candles_1m_other_v2_2024','perp_candles_1m_other_v2_2025','perp_candles_1m_other_v2_2026')))
def spot_candles(): return Candles(table('spot_candles_1m'),prefer=('binance_spot',))

def delayed_entry(C, trig):
    m0=(int(trig)//MIN)*MIN+MIN; i=int(np.searchsorted(C['ts'],m0))
    if i>=len(C['ts']) or C['ts'][i]>m0+5*MIN: return None
    return i, C['c'][i], int(C['ts'][i])+MIN

def close_before(C, t, i0):
    j=int(np.searchsorted(C['ts'],t))-1
    return (j, C['c'][j]) if j>=i0 else (None,None)

def funding_sum(F, a, b):
    if F is None: return 0.0
    t,r=F; k=(t>a)&(t<=b); return float(r[k].sum())

def short_trade(C, F, trig, hold_min, stop=None, mode='exact'):
    """Short at the delayed entry after `trig`, hold `hold_min`; returns dict(ret, stopped, funding) or None."""
    e=delayed_entry(C,trig)
    if e is None: return None
    i0,ep,t0=e; j,px=close_before(C,t0+hold_min*MIN,i0)
    if j is None or C['ts'][-1] < t0+hold_min*MIN-MIN: return None
    if stop is not None:
        lvl=ep*(1+stop); hit=np.nonzero(C['h'][i0+1:j+1]>=lvl)[0]
        if len(hit):
            k=i0+1+hit[0]; xp=lvl if mode=='exact' else C['c'][k]; fu=funding_sum(F,t0,int(C['ts'][k])+MIN)
            return dict(ret=-(xp/ep-1)-COST+fu,stopped=True,funding=fu,entry_ms=t0)
    fu=funding_sum(F,t0,t0+hold_min*MIN)
    return dict(ret=-(px/ep-1)-COST+fu,stopped=False,funding=fu,entry_ms=t0,max_up=float(C['h'][i0+1:j+1].max()/ep-1) if j>i0 else 0.0)

def funding_map():
    f=table('funding_history'); out={}
    for (eid,v),g in f.sort_values('timestamp_ms').groupby(['event_id','venue']): out[(eid,v)]=(g.timestamp_ms.to_numpy('int64'),g.funding_rate.to_numpy(float))
    return out

def ticks():
    """Per (event, venue) tick arrays from every aggtrades table, plus the suspect-tick keys."""
    a=table('aggtrades'); a=a.drop_duplicates(['event_id','venue','agg_trade_id']).sort_values(['event_id','venue','timestamp_ms','agg_trade_id'])
    sus=pd.read_parquet(f'{D}/aggtrades_suspect_ticks.parquet')
    a['suspect']=pd.MultiIndex.from_frame(a[['event_id','venue','agg_trade_id']]).isin(pd.MultiIndex.from_frame(sus[['event_id','venue','agg_trade_id']]))
    out={}
    for (eid,v),g in a.groupby(['event_id','venue'],sort=False):
        out[(eid,v)]=dict(ts=g.timestamp_ms.to_numpy('int64'),p=g.price.to_numpy(float),q=g.qty.to_numpy(float),sus=g.suspect.to_numpy(bool))
    return out, int(a.suspect.sum())

def tick_view(T, drop_suspect):
    if not drop_suspect or not T['sus'].any(): return T
    k=~T['sus']; return {x:T[x][k] for x in ('ts','p','q','sus')}

def tick_long(T, C, ann, L, hold_min):
    i=int(np.searchsorted(T['ts'],ann+L))
    if i>=len(T['ts']) or T['ts'][i]>ann+90_000: return None
    ep=T['p'][i]; tgt=(int(T['ts'][i])//MIN)*MIN+hold_min*MIN; j=int(np.searchsorted(C['ts'],tgt))
    if j>=len(C['ts']) or C['ts'][j]>tgt+5*MIN: return None
    return C['o'][j]/ep-1-COST

def stats(x):
    x=pd.Series(x,dtype=float).dropna()*100
    if not len(x): return dict(n=0)
    return dict(n=len(x),median=x.median(),mean=x.mean(),win=(x>0).mean()*100,p10=x.quantile(.1),p90=x.quantile(.9),worst=x.min())

def label(v1, v23):
    n1,n2=v1.get('n',0),v23.get('n',0)
    if n1==0 or n2==0: return 'single period'
    if n1<20 or n2<20: return 'n<20 in one period'
    pos=lambda s: s['median']>0 and s['mean']>0
    neg=lambda s: s['median']<0 and s['mean']<0
    if pos(v1) and pos(v23): return 'survives'
    if neg(v1) and neg(v23): return 'negative in both'
    return 'no'

def risk(df):
    """Concentration and sequence risk on a trade frame with ann_ms and ret (fractions)."""
    d=df.sort_values('ann_ms'); r=d.ret.to_numpy()*100
    if not len(r): return {}
    tot=r.sum(); top=np.sort(r)[::-1][:5]; rest=np.sort(r)[::-1][5:]
    cum=np.cumsum(r); dd=float((np.maximum.accumulate(np.r_[0,cum])[1:]-cum).max())
    streak=cur=0
    for v in r: cur=cur+1 if v<0 else 0; streak=max(streak,cur)
    return dict(total_pnl=tot,top5_share=top.sum()/tot*100 if tot else np.nan,mean_ex_top5=rest.mean() if len(rest) else np.nan,
                median_ex_top5=np.median(rest) if len(rest) else np.nan,max_drawdown_pp=dd,longest_losing_streak=streak,losses_beyond_50=int((r<-50).sum()))

def summarize(trades, keys):
    """One row per strategy: overall, v1, v2+v3, per year, without outliers, survive label and risk."""
    rows=[]
    for k,g in trades.groupby(keys,dropna=False,sort=False):
        k=k if isinstance(k,tuple) else (k,)
        s=stats(g.ret); v1=stats(g[g.period.eq('v1')].ret); v23=stats(g[g.period.eq('v2+v3')].ret); no=stats(g[~g.outlier_flag].ret)
        row=dict(zip(keys,k)); row.update(s)
        for tag,x in (('v1',v1),('v23',v23),('no_outlier',no)):
            row.update({f'{tag}_{c}':x.get(c) for c in ('n','median','mean','win')})
        for y in sorted(g.year.unique()):
            ys=stats(g[g.year.eq(y)].ret); row.update({f'y{y}_n':ys['n'],f'y{y}_median':ys.get('median'),f'y{y}_mean':ys.get('mean')})
        row['label']=label(v1,v23); row.update(risk(g)); rows.append(row)
    return pd.DataFrame(rows)

TRADE_COLS=['strategy','group','side','venue','entry','hold_min','stop','event_id','ann_ms','period','year','outlier_flag','ret']
def trade_rows(ev, strategy, side, venue, entry, hold, stop, rets):
    """rets: dict event_id -> return fraction."""
    e=ev.set_index('event_id')
    return pd.DataFrame([dict(strategy=strategy,group=e.at[k,'group'] if k in e.index else None,side=side,venue=venue,entry=entry,hold_min=hold,stop=stop,
        event_id=k,ann_ms=int(e.at[k,'t_ms']),period=e.at[k,'period'],year=int(e.at[k,'year']),outlier_flag=bool(e.at[k,'outlier_flag']),ret=v)
        for k,v in rets.items() if v is not None and k in e.index],columns=TRADE_COLS)

def save(df, name): df.to_csv(f'{A}/{name}.csv',index=False); return df

def splits(df, col='ret'):
    """(split name, frame) pairs: all, v1, v2+v3, each calendar year, and all without outlier_flag."""
    out=[('all',df),('v1',df[df.period.eq('v1')]),('v2+v3',df[df.period.eq('v2+v3')])]
    out+=[(str(int(y)),df[df.year.eq(y)]) for y in sorted(df.year.dropna().unique())]
    return out+[('no_outlier',df[~df.outlier_flag])]

def split_stats(df, keys, col='ret'):
    rows=[]
    for k,g in df.groupby(keys,sort=False,dropna=False):
        k=k if isinstance(k,tuple) else (k,)
        for name,s in splits(g):
            st=stats(s[col]); st.update(dict(zip(keys,k))); st['split']=name; rows.append(st)
    return pd.DataFrame(rows)[list(keys)+['split','n','median','mean','win','p10','p90','worst']]

LAT=[0,0.5,1,2,3,5,10,30,60]
def event_ticks(T, eid):
    for v in ('binance_spot','binance_perp'):
        if (eid,v) in T: return v, T[(eid,v)]
    return None, None

def venue_candles(SC, PC, venue, eid): return SC.get(eid,'binance_spot') if venue=='binance_spot' else PC.get(eid,'binance_perp')

def move_profile(T, ann):
    """Price path in the first minute after `ann`, relative to the last trade strictly before it."""
    ts,p=T['ts'],T['p']; i0=int(np.searchsorted(ts,ann))-1
    if i0<0 or ts[-1]<ann+60_000: return None
    p0=p[i0]
    def at(ms):
        j=int(np.searchsorted(ts,ann+ms,side='right'))-1; return p[j]/p0-1
    out={f'm{t}':at(t*1000) for t in (1,2,5,30,60)}
    k=int(np.searchsorted(ts,ann-60_000,side='right'))-1; pp=p[max(k,0)]; out['drift_pre60']=p0/pp-1
    post=slice(i0+1,int(np.searchsorted(ts,ann+60_000,side='right')))
    pr,tt=p[post]/p0-1,(ts[post]-ann)/1000
    m60=out['m60']
    out['t_half']=float(tt[np.argmax(pr>=m60/2)]) if m60>0 and (pr>=m60/2).any() else np.nan
    out['t_first2']=float(tt[np.argmax(pr>=0.02)]) if (pr>=0.02).any() else np.nan
    return out

def fillable(T, ann, L, window_s, cap):
    """USD traded by the whole market from the first trade at or after ann+L, over window_s, until price first exceeds
    that trade's price by `cap`."""
    ts,p,q=T['ts'],T['p'],T['q']; i=int(np.searchsorted(ts,ann+L))
    if i>=len(ts) or ts[i]>ann+90_000: return None
    j=int(np.searchsorted(ts,ts[i]+window_s*1000))
    seg=p[i:j]; over=np.nonzero(seg>p[i]*(1+cap))[0]; end=i+(over[0] if len(over) else len(seg))
    return float((p[i:end]*q[i:end]).sum())

_cache={}
def csv(name):
    if name not in _cache: _cache[name]=pd.read_csv(f'{A}/{name}.csv',low_memory=False)
    return _cache[name]

def _match(series, val):
    alts=val.split('~')
    try:
        nums=[float(a) for a in alts]; s=pd.to_numeric(series,errors='coerce')
        return np.logical_or.reduce([np.isclose(s,v) for v in nums])
    except ValueError:
        return series.astype(str).isin(alts)

def select(name, filters):
    """Rows of analysis/<name>.csv matching filters 'col=value&&col=value' (alternatives joined by ~)."""
    d=csv(name)
    for f in [x for x in filters.split('&&') if x.strip()]:
        k,v=f.split('=',1); k=k.strip()
        if k not in d: raise KeyError(f'{name}: no column {k}')
        d=d[_match(d[k],v.strip())]
    return d
