"""Final report section 4H: other patterns and risks, compiled from the section CSVs in analysis/. Writes analysis/h_patterns.csv
(pattern, measure, value, source)."""
import sys; sys.path.insert(0,'scripts')
import pandas as pd
from final_common import *
r=lambda n: pd.read_csv(f'{A}/{n}.csv',dtype={'split':str}); rows=[]
def add(p,m,v,src): rows.append(dict(pattern=p,measure=m,value=v,source=src))
ft=r('a_short_open_funding_touch'); so=r('a_short_open')
for g in ('Upbit KRW','Bithumb'):
    f=ft[(ft.grp==g)&(ft.hold_min==1440)].iloc[0]
    add('funding as large as the edge',f'{g}: funding paid by the short over 24 h, mean %',f.funding_paid_mean,'a_short_open_funding_touch')
    for st,mode in (('none','none'),('+20%','pessimistic')):
        x=so[(so.grp==g)&(so.hold_min==1440)&(so.stop==st)&(so['mode']==mode)&(so.split=='all')].iloc[0]
        add('funding as large as the edge',f'{g}: 24 h short after funding, stop {st}, mean %',x['mean'],'a_short_open')
b=r('d_book')
for g in ('Upbit KRW','Bithumb official','Upbit BTC/USDT only'):
    for p in ('2024-2025','2026'):
        x=b[(b.kgroup==g)&(b.side=='ask')&(b.band_pct==1)&(b.period==p)]
        if len(x): add('thinner books in 2026',f'{g}: ask depth within 1% before the announcement, {p}, median USD k',x.depth_k_median.iloc[0],'d_book')
t=r('a_tick_long')
for g in ('Upbit KRW','Bithumb official'):
    for L in (1,2):
        for y in ('2024','2025','2026'):
            x=t[(t.kgroup==g)&(t.L==L)&(t.hold_min==5)&(~t.drop_suspect.astype(bool))&(t.split==y)]
            if len(x) and x.n.iloc[0]>0: add('the fast edge narrowing over time',f'{g}: tick long {L} s, 5 min, {y}, median % (n={int(x.n.iloc[0])})',x['median'].iloc[0],'a_tick_long')
s=r('a_speed')
for g in ('Upbit KRW','Bithumb official'):
    for y in ('2024','2025','2026'):
        x=s[(s.kgroup==g)&(s.split==y)]
        if len(x): add('when the move starts against the timestamp',f'{g}: first +2% print, {y}, median s after the timestamp',x.t_first2_median_s.iloc[0],'a_speed')
bs=r('b_speed'); x=bs[(bs.group=='Binance spot with prior perp')&(bs.split=='all')]
add('when the move starts against the timestamp','Binance spot with prior perp: first +2% print, median s after releaseDate',x.t_first2_median_s.iloc[0],'b_speed')
x=s[(s.kgroup=='Bithumb third-party')&(s.split=='all')]
add('timestamps that arrive after the move','Bithumb v1 third-party times: drift in the 60 s before, median %',x.drift_pre60_median.iloc[0],'a_speed')
g=r('g_poll_logs'); u=g[g.table=='upbit_poll_log']
if len(u): add('timestamps that precede the visible post','Upbit API: our first sight minus first_listed_at, s (non-listing notices)',';'.join(f'{v:.1f}' for v in u.lag_s),'g_poll_logs')
bt=r('b_short_funding_touch'); x=bt[(bt.group=='Binance perp listing')&(bt.entry=='perp open +1m on listed perp')&(bt.hold_min==1440)]
if len(x):
    x=x.iloc[0]
    add('newly listed perps too volatile to short with a stop','Binance perp listings: share touching +20% within 24 h, %',x.touch20,'b_short_funding_touch')
    add('newly listed perps too volatile to short with a stop','Binance perp listings: share touching +50% within 24 h, %',x.touch50,'b_short_funding_touch')
save(pd.DataFrame(rows),'h_patterns'); print('H done',len(rows))
