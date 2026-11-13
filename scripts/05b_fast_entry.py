"""Sensitivity: how much does reaction speed matter at a Korean/any announcement?
Entry variants on the external venue: (a) 'instant' = close of the minute BEFORE the announcement minute
(theoretical best case, roughly a sub-second bot), (b) 'same_min' = close of the announcement minute (<=60 s),
(c) base = close of the next minute (60-120 s). Returns net of 0.6% cost. Writes out/fast_entry.csv."""
import sys, pandas as pd
sys.path.insert(0,'scripts'); from candles import candles, MIN
df=pd.read_csv('out/metrics_all_raw.csv'); rows=[]
def px_at(cs,t):
    prev=[c for c in cs if c[0]<t]; return prev[-1][4] if prev else None
for _,r in df.iterrows():
    if pd.isna(r.get('ext_at_ann')) or pd.isna(r.get('ann_ext_entry_ts')): continue
    a=int(r.ann_ms); cs=candles(r.ext_at_ann, r.ext_market, a-5*MIN, a+1450*MIN)
    m=(a//MIN)*MIN
    pre=[c for c in cs if c[0]<m]; same=[c for c in cs if c[0]==m]
    if not pre or not same: continue
    o=dict(event_id=r.event_id)
    for name,ep,t0 in [('instant',pre[-1][4],m),('same_min',same[0][4],m+MIN)]:
        for h in [5,15,60,240]:
            p=px_at(cs,t0+h*MIN)
            if p: o[f'{name}_n{h}']=p/ep-1-0.006
        hi=max([c[2] for c in cs if m<=c[0]<t0+60*MIN] or [ep]); o[f'{name}_peak60']=hi/ep-1
    rows.append(o)
pd.DataFrame(rows).to_csv('out/fast_entry.csv',index=False); print(len(rows))
