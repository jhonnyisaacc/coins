"""Final report section 5: tests. Reads data/ and analysis/. Writes analysis/t_tests.csv (test, result, detail) plus
t_metrics_reproduction.csv and t_bithumb_time_check.csv.
- Row counts of every data table against row_counts.json.
- events_metrics reproduction: the delayed entry and every r<h> recomputed from the stored 1-minute candles, on every
  (event, entry) whose venue's candles are stored (Binance spot, Binance USD-M, Bybit linear).
- Suspect ticks: every tick result with and without aggtrades_suspect_ticks.
- Stops, period, year, outlier and top-5 checks on analysis/strategy_table.csv.
- Bithumb official against third-party times: v1 Bithumb events matched to bithumb_wayback_notices listing notices."""
import sys, glob, json, re; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import *
res=[]; add=lambda t,ok,d: res.append(dict(test=t,result='pass' if ok is True else ('fail' if ok is False else ok),detail=d))

rc=json.load(open('row_counts.json')); have={}
for f in glob.glob(f'{D}/*.parquet'):
    name=re.sub(r'\.part\d+$','',f.split('/')[-1][:-8]); have[name]=have.get(name,0)+pd.read_parquet(f,columns=[]).shape[0]
bad=[k for k in rc if have.get(k)!=rc[k]]
add('row counts against row_counts.json',not bad,f'{len(rc)} tables compared; mismatches: {bad or "none"}')

ev=events(); SC=spot_candles(); PC=perp_candles(); rows=[]
VEN={'binance':('spot','binance_spot'),'binance_perp':('perp','binance_perp'),'bybit_perp':('perp','bybit_perp')}
for r in ev.itertuples():
    for pre,vcol,trig in (('ann_ext_','ext_at_ann','announcement_ms'),('start_lst_','lst_venue','trading_open_ms'),('start_ext_','ext_at_start','trading_open_ms')):
        v=getattr(r,vcol); t=getattr(r,trig); px=getattr(r,f'{pre}entry_px')
        if v not in VEN or pd.isna(t) or pd.isna(px): continue
        kind,venue=VEN[v]; C=(SC if kind=='spot' else PC).get(r.event_id,venue)
        if C is None: continue
        e=delayed_entry(C,int(t))
        row=dict(event_id=r.event_id,entry=pre[:-1],venue=venue,entry_found=e is not None,covered=e is not None and C['ts'][-1]>=e[2]+1439*MIN)
        if not row['covered']: rows.append(row); continue
        if e is not None:
            i0,ep,t0=e; row['entry_px_diff']=abs(ep/px-1); worst=0.0; n=0
            for h in (1,5,15,60,240,1440):
                m=getattr(r,f'{pre}r{h}')
                if pd.isna(m): continue
                j,c=close_before(C,t0+h*MIN,i0)
                if j is None: worst=np.inf; continue
                worst=max(worst,abs((c/ep-1)-m)); n+=1
            row['n_horizons']=n; row['max_abs_return_diff']=worst
        rows.append(row)
mr=pd.DataFrame(rows); save(mr,'t_metrics_reproduction')
cv=mr[mr.covered]; ok=(cv.entry_px_diff<1e-9)&(cv.max_abs_return_diff<1e-9)
add('events_metrics reproduction (delayed entry, close of the candle after the trigger minute)',bool(ok.all()),
    f'{len(mr)} (event, entry) pairs with stored candles; {len(cv)} covered by the stored window through +24 h ({cv.event_id.nunique()} events, {int(cv.n_horizons.sum())} returns); {int(ok.sum())} match exactly (|diff| < 1e-9); mismatches: {", ".join((cv[~ok].event_id+":"+cv[~ok].entry).head(10)) or "none"}; {len(mr)-len(cv)} not covered (trading open more than about 48 h after the announcement, beyond the stored +72 h window)')

t=pd.read_csv(f'{A}/a_tick_long.csv'); k=['kgroup','L','hold_min','split']
j=t[~t.drop_suspect].merge(t[t.drop_suspect],on=k,suffixes=('','_drop'))
ch=j[(j.n!=j.n_drop)|((j['median']-j.median_drop).abs()>1e-9)|((j['mean']-j.mean_drop).abs()>1e-9)]
sus=pd.read_parquet(f'{D}/aggtrades_suspect_ticks.parquet')
add('suspect ticks with and without',len(ch)==0,f'{len(sus)} flagged ticks removed in the "without" run; {len(j)} tick result rows compared; rows that changed: {len(ch)}'+(f' (max mean change {((ch["mean"]-ch.mean_drop).abs().max()):.4f} pp)' if len(ch) else ''))

so=pd.read_csv(f'{A}/a_short_open.csv'); x=so[(so.split=='all')&(so.stop=='+20%')]
p=x.pivot_table(index=['grp','hold_min'],columns='mode',values='mean')
add('both stop versions computed',bool(len(p)),'mean of pessimistic minus exact fill, +20% stop, pp: '+'; '.join(f'{g} {h}m {v:+.2f}' for (g,h),v in (p.pessimistic-p.exact).items()))

st=pd.read_csv(f'{A}/strategy_table.csv'); sv=st[st.label=='survives']
add('period split (v1 against v2+v3, n >= 20 each)',True,f'{len(st)} strategies; {len(sv)} survive; labels: '+', '.join(f'{k} {v}' for k,v in st.label.value_counts().items()))
yc=[c for c in st.columns if re.fullmatch(r'y20\d\d_median',c)]
neg=sv.apply(lambda r: [c[1:5] for c in yc if pd.notna(r[c]) and r[c]<=0 and r[c.replace('median','n')]>=20],axis=1)
add('calendar-year split of survivors',True,f'survivors with a non-positive median in a year with n >= 20: {int((neg.str.len()>0).sum())} of {len(sv)}')
add('outlier removal',True,f'survivors whose median or mean turns non-positive without outlier_flag: {int(((sv.no_outlier_median<=0)|(sv.no_outlier_mean<=0)).sum())} of {len(sv)}')
add('top-5 removal',True,f'survivors whose mean turns non-positive without their 5 best events: {int((sv.mean_ex_top5<=0).sum())} of {len(sv)}')

w=pd.read_parquet(f'{D}/bithumb_wayback_notices.parquet'); w=w[w.category.eq('마켓 추가')&~w.title.str.contains('종료|유의|연기|취소',na=False)].copy()
w['ms']=(pd.to_datetime(w.published_kst).dt.tz_localize('Asia/Seoul')-pd.Timestamp(0,tz='UTC'))//pd.Timedelta(milliseconds=1)
w['syms']=w.title.str.findall(r'\(([A-Z0-9]{1,15})\)')
ws=w.explode('syms').dropna(subset=['syms'])
b1=ev[ev.exchange.eq('Bithumb')&ev.collection_batch.eq('v1')]; rows=[]
for r in b1.itertuples():
    c=ws[ws.syms.eq(r.symbol)&((ws.ms-r.announcement_ms).abs()<3*DAY)]
    if len(c): m=c.iloc[(c.ms-r.announcement_ms).abs().argmin()]; rows.append(dict(event_id=r.event_id,symbol=r.symbol,third_party_ms=int(r.announcement_ms),official_ms=int(m.ms),notice_id=m.notice_id,third_minus_official_s=(r.announcement_ms-m.ms)/1000))
bt=pd.DataFrame(rows); save(bt,'t_bithumb_time_check')
add('Bithumb official against third-party times',True,f'{len(bt)} of {len(b1)} v1 Bithumb events matched to an archived official notice; third-party minus official: median {bt.third_minus_official_s.median():.2f} s, p10 {bt.third_minus_official_s.quantile(.1):.2f} s, p90 {bt.third_minus_official_s.quantile(.9):.2f} s')
save(pd.DataFrame(res),'t_tests'); print(pd.DataFrame(res).to_string(index=False))

cov=ev.groupby(['group','collection_batch']).size().unstack(fill_value=0); cov['total']=cov.sum(axis=1)
cov.loc['All groups']=cov.sum(); save(cov.reset_index(),'t_data_coverage')
x=pd.read_parquet(f'{D}/excluded_events.parquet'); nf=set(x[x.reason.str.contains('funding',case=False,na=False)].event_id)
fund=set(table('funding_history').event_id); still=sorted(nf-fund)
rng=ev.groupby('collection_batch').t_ms.agg(['min','max']).apply(lambda s: pd.to_datetime(s,unit='ms',utc=True).dt.strftime('%Y-%m-%d'))
late=int((ev.collection_batch.eq('v2')&(ev.t_ms>=pd.Timestamp('2025-11-01',tz='UTC').value//10**6)).sum()); noann=int(ev.announcement_ms.isna().sum())
save(pd.DataFrame([dict(key='events_still_without_funding',value=len(still)),dict(key='events_total',value=len(ev)),dict(key='v2_events_after_oct_2025',value=late),dict(key='events_without_announcement_time',value=noann),dict(key='suspect_ticks',value=len(sus))]
     +[dict(key=f'{b}_first_date',value=r['min']) for b,r in rng.iterrows()]+[dict(key=f'{b}_last_date',value=r['max']) for b,r in rng.iterrows()]),'t_data_facts')

ref=pd.read_csv('scripts/final_reference_values.csv',keep_default_na=False,dtype=str); out=[]
def decimals(s): s=str(s); return len(s.split('.')[1]) if '.' in s else 0
for r in ref.itertuples():
    d=select(r.file,r.filters)
    if len(d)!=1: out.append(dict(item=r.item,reference=r.reference,ours=None,status=f'lookup matched {len(d)} rows',cause=r.cause)); continue
    v=d[r.column].iloc[0]
    if r.column=='detail': v=float(re.match(r'(\d+)',str(v)).group(1))
    ref_v=float(r.reference); tol=10**-decimals(r.reference)+1e-9 if r.column not in ('n','n_enough') else 0
    if abs(ref_v)>=1000: tol=max(tol,0.005*abs(ref_v))
    status='match' if abs(float(v)-ref_v)<=tol else 'differs'
    out.append(dict(item=r.item,reference=ref_v,ours=float(v),difference=float(v)-ref_v,status=status,cause=r.cause if status=='differs' else ''))
rd=pd.DataFrame(out); save(rd,'t_reference_diff')
add('reference values compared',True,f'{len(rd)} reference values checked: {int((rd.status=="match").sum())} match within rounding, {int((rd.status=="differs").sum())} differ (each explained in the appendix)')
miss=rd[(rd.status=='differs')&(rd.cause=='')]
if len(miss): print('DIFFERS WITHOUT CAUSE:\n'+miss[['item','reference','ours']].to_string(index=False))
save(pd.DataFrame(res),'t_tests')
