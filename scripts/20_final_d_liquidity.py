"""Final report section 4D: liquidity and size. Reads data/ only. Writes analysis/d_*.csv.
- Order book: book_snapshots pct_band rows (cumulative USD-M perp depth within +-1/2/5%, about every 30 s). Last snapshot at or
  before the announcement and the first three after it. Depth is an upper bound on size, not an impact model.
- Fillable size: USD traded by the whole market from the first trade at or after announcement + L, over 5 s and 30 s, until price
  first exceeds that trade's price by 1/2/5%. This is everyone's flow, not one participant's fill.
- DEX: one pool per event (most swaps). Onset is the first swap at or above +2% from the last swap before the announcement.
  Measured buy impact is the buy's price against the previous swap in the same pool, compared with size / (liquidity_usd_at_ann / 2).
  Gas per swap is an assumption (GAS_USD below)."""
import sys; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *

ev=events()
ev['kgroup']=np.where(ev.exchange.eq('Bithumb'),np.where(ev.bithumb_official,'Bithumb official','Bithumb third-party'),ev.group)
G=ev.set_index('event_id')
k3=lambda s: pd.Series(s,dtype=float)/1000
def q(s): s=pd.Series(s,dtype=float).dropna(); return dict(n=len(s),median=s.median(),p25=s.quantile(.25),p10=s.quantile(.1))

b=pd.read_parquet(f'{D}/book_snapshots.parquet'); b=b[b.level_kind.eq('pct_band')]
rows=[]
for eid,g in b.groupby('event_id'):
    if eid not in G.index: continue
    a=int(G.at[eid,'announcement_ms']); ts=np.sort(g.timestamp_ms.unique())
    pre=ts[ts<=a]; post=ts[ts>a][:3]
    if not len(pre): continue
    t0=pre[-1]
    for side in ('ask','bid'):
        for lvl in (1.0,2.0,5.0):
            s=g[g.side.eq(side)&g.level.eq(lvl)].set_index('timestamp_ms').notional_usd
            if t0 not in s.index: continue
            r=dict(event_id=eid,kgroup=G.at[eid,'kgroup'],year=int(G.at[eid,'year']),side=side,band_pct=lvl,depth_before_usd=float(s[t0]),before_s=(t0-a)/1000)
            for i,t in enumerate(post,1):
                if t in s.index: r[f'after{i}_s']=(t-a)/1000; r[f'change{i}']=float(s[t]/s[t0]-1) if s[t0] else np.nan
            rows.append(r)
bk=pd.DataFrame(rows); save(bk,'d_book_events')
bk['period']=np.where(bk.year.eq(2026),'2026','2024-2025')
out=[]
for keys,g in list(bk.groupby(['kgroup','side','band_pct']))+[((k,s,l,p),g) for (k,s,l,p),g in bk.groupby(['kgroup','side','band_pct','period'])]:
    k=keys if len(keys)==4 else keys+('all',)
    r=dict(kgroup=k[0],side=k[1],band_pct=k[2],period=k[3]); d=q(k3(g.depth_before_usd)); r.update({f'depth_k_{x}':v for x,v in d.items()})
    for i in (1,2,3):
        if f'change{i}' in g: r[f'after{i}_s_median']=g[f'after{i}_s'].median(); r[f'change{i}_median_pct']=g[f'change{i}'].median()*100
    out.append(r)
save(pd.DataFrame(out),'d_book')

T,_=ticks(); fl=[]
for r in ev[ev.event_id.isin({e for e,_ in T})].itertuples():
    for v in ('binance_spot','binance_perp'):
        Tr=T.get((r.event_id,v))
        if Tr is None: continue
        for L in (0,1):
            for w in (5,30):
                for cap in (0.01,0.02,0.05):
                    x=fillable(Tr,int(r.announcement_ms),L*1000,w,cap)
                    if x is not None: fl.append(dict(event_id=r.event_id,kgroup=r.kgroup,year=r.year,venue=v,L=L,window_s=w,cap_pct=int(cap*100),usd=x))
fl=pd.DataFrame(fl); save(fl,'d_fillable_events')
out=[]
for k,g in fl.groupby(['kgroup','venue','L','window_s','cap_pct']):
    r=dict(zip(['kgroup','venue','L','window_s','cap_pct'],k)); r.update({f'usd_k_{x}':v for x,v in q(k3(g.usd)).items()}); out.append(r)
save(pd.DataFrame(out),'d_fillable')

GAS_USD={'eth':10.0,'base':0.05,'bsc':0.10}
sw=pd.read_parquet(f'{D}/dex_swaps.parquet').sort_values(['event_id','pool_address','timestamp_ms','block','log_index'])
pool=sw.groupby(['event_id','pool_address']).size().reset_index(name='n').sort_values('n').drop_duplicates('event_id',keep='last')
sw=sw.merge(pool[['event_id','pool_address']],on=['event_id','pool_address'])
ps=pd.read_parquet(f'{D}/dex_pool_status.parquet')[['event_id','pool_address','liquidity_usd_at_ann','liquidity_usd_now']]
ps['pool_address']=ps.pool_address.str.lower(); sw['pool_l']=sw.pool_address.str.lower()
liq=ps.drop_duplicates(['event_id','pool_address']).set_index(['event_id','pool_address'])
tk_on={}
for (eid,v),Tr in T.items():
    if eid in G.index and eid not in tk_on:
        vv,TT=event_ticks(T,eid); mp=move_profile(TT,int(G.at[eid,'announcement_ms'])); tk_on[eid]=mp['t_first2'] if mp else np.nan
ev_rows=[]; imp=[]; gross=[]
for eid,g in sw.groupby('event_id'):
    if eid not in G.index: continue
    a=int(G.at[eid,'announcement_ms']); pre=g[g.timestamp_ms<a]; post=g[g.timestamp_ms>=a]
    li=liq.loc[(eid,g.pool_l.iloc[0])] if (eid,g.pool_l.iloc[0]) in liq.index else None
    L_ann=float(li.liquidity_usd_at_ann) if li is not None and pd.notna(li.liquidity_usd_at_ann) else np.nan
    L_now=float(li.liquidity_usd_now) if li is not None and pd.notna(li.liquidity_usd_now) else np.nan
    r=dict(event_id=eid,kgroup=G.at[eid,'kgroup'],year=int(G.at[eid,'year']),chain=g.chain.iloc[0],n_swaps=len(g),n_pre=len(pre),n_post=len(post),liq_at_ann=L_ann,liq_now=L_now,
           buys10k_pre120=int(((pre.side=='buy')&(pre.amount_usd>=10_000)&(pre.timestamp_ms>=a-120_000)).sum()),
           vol60_usd=float(post[post.timestamp_ms<=a+60_000].amount_usd.sum()))
    enough=len(pre)>0 and len(post)>0; r['enough']=enough
    if enough:
        p0=pre.price.iloc[-1]; on=post[post.price>=p0*1.02]
        r['dex_onset_s']=(on.timestamp_ms.iloc[0]-a)/1000 if len(on) else np.nan
        r['binance_onset_s']=tk_on.get(eid,np.nan); r['dex_minus_binance_s']=r['dex_onset_s']-r['binance_onset_s']
        ex=g[g.timestamp_ms<=a+300_000]
        for L in (0,3,12):
            e=post[post.timestamp_ms>=a+L*1000]
            if len(e) and len(ex): gross.append(dict(event_id=eid,kgroup=r['kgroup'],chain=r['chain'],L=L,gross=ex.price.iloc[-1]/e.price.iloc[0]-1))
    ev_rows.append(r)
    pp=g.price.shift(); bb=g[(g.side=='buy')&pp.notna()]
    for x in bb.itertuples():
        m=x.price/pp.loc[x.Index]-1
        imp.append(dict(event_id=eid,chain=x.chain,amount_usd=x.amount_usd,impact=m,cp_estimate=x.amount_usd/(L_ann/2) if L_ann>0 else np.nan))
de=pd.DataFrame(ev_rows); save(de,'d_dex_events')
im=pd.DataFrame(imp); bins=[0,1e3,5e3,2e4,1e5,np.inf]; labs=['<1k','1k-5k','5k-20k','20k-100k','>=100k']
im['bucket']=pd.cut(im.amount_usd,bins,labels=labs,right=False); save(im,'d_dex_impact_swaps')
ib=im.groupby('bucket',observed=False).agg(n=('impact','size'),impact_median_pct=('impact',lambda s:s.median()*100),cp_estimate_median_pct=('cp_estimate',lambda s:s.median()*100)).reset_index()
big=im[(im.amount_usd>=5000)&im.cp_estimate.notna()&(im.cp_estimate>0)]
ib['measured_over_cp_ratio_ge5k']=(big.impact/big.cp_estimate).median()
li2=ps.dropna(subset=['liquidity_usd_at_ann','liquidity_usd_now']); li2=li2[li2.liquidity_usd_at_ann>0]
ib['liq_now_over_at_ann_median']=(li2.liquidity_usd_now/li2.liquidity_usd_at_ann).median(); ib['liq_pools_both']=len(li2)
save(ib,'d_dex_impact')
gr=pd.DataFrame(gross); save(gr,'d_dex_gross_events')
SIZES=[1e3,5e3,2e4,1e5]; imed=dict(zip(ib.bucket.astype(str),ib.impact_median_pct/100))
bucket=lambda s: labs[np.searchsorted(bins,s,side='right')-1]
out=[]
for (k,L),g in gr.groupby(['kgroup','L']):
    r=dict(kgroup=k,L=L,n=len(g),gross_median_pct=g.gross.median()*100,gross_mean_pct=g.gross.mean()*100); best=0
    for S in SIZES:
        net=g.gross-2*imed[bucket(S)]-g.chain.map(GAS_USD)*2/S
        r[f'net_median_pct_{int(S/1000)}k']=net.median()*100
        if net.median()>0: best=S
    r['largest_positive_size_usd']=best; out.append(r)
save(pd.DataFrame(out),'d_dex_gross')
dd=de[de.enough]
summ=[]
for k,g in [('all',dd)]+list(dd.groupby('kgroup')):
    z=g.dex_minus_binance_s.dropna()
    summ.append(dict(kgroup=k,n_enough=len(g),years=','.join(map(str,sorted(g.year.unique()))),n_onset_pairs=len(z),dex_minus_binance_median_s=z.median(),
        dex_after=int((z>0).sum()),dex_before=int((z<0).sum()),vol60_median_usd=g.vol60_usd.median(),events_with_buys10k_pre=int((g.buys10k_pre120>0).sum())))
save(pd.DataFrame(summ),'d_dex_summary')
pd.DataFrame([dict(chain=c,gas_usd_per_swap_assumed=v) for c,v in GAS_USD.items()]).to_csv(f'{A}/d_gas_assumptions.csv',index=False)
print('D done',len(bk),len(fl),len(de),len(im))

bt=pd.read_csv(f'{A}/d_book.csv'); ft=pd.read_csv(f'{A}/d_fillable.csv')
def depth(g,side,period): x=bt[(bt.kgroup==g)&(bt.side==side)&(bt.band_pct==1)&(bt.period==period)]; return float(x.depth_k_p25.iloc[0]) if len(x) else np.nan
def flow(g): x=ft[(ft.kgroup==g)&(ft.venue=='binance_spot')&(ft.L==1)&(ft.window_s==5)&(ft.cap_pct==2)]; return float(x.usd_k_p25.iloc[0]) if len(x) else np.nan
caps=[]
for strat,parts in [('Upbit KRW fast long',[('2026 ask depth within 1%, p25',depth('Upbit KRW','ask','2026')),('5 s flow at 1 s latency before +2%, Binance spot, p25',flow('Upbit KRW'))]),
                    ('Bithumb fast long (paper only)',[('2024-2025 ask depth within 1%, p25',depth('Bithumb official','ask','2024-2025')),('2026 ask depth within 1% (third-party-time events), p25',depth('Bithumb third-party','ask','2026')),('5 s flow at 1 s latency before +2%, Binance spot, p25',flow('Bithumb official'))]),
                    ('Upbit KRW short after the open',[('2026 bid depth within 1% before the announcement, p25',depth('Upbit KRW','bid','2026'))]),
                    ('Bithumb short after the open',[('2026 bid depth within 1% before the announcement (third-party-time events), p25',depth('Bithumb third-party','bid','2026'))]),
                    ('Binance spot with prior perp fast long',[('2026 ask depth within 1%, p25',depth('Binance spot','ask','2026'))])]:
    m=np.nanmin([v for _,v in parts]); caps.append(dict(strategy=strat,inputs='; '.join(f'{k} = {v:.1f}k' for k,v in parts),min_input_k=m,cap_k=np.floor(0.5*m/5)*5 if m>=10 else np.floor(0.5*m)))
save(pd.DataFrame(caps),'d_size_caps')
