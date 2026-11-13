"""Add v2 sections to data/summary.json (v1 keys unchanged): the 06_analysis summaries for v2 rows and for v1+v2, plus source status."""
import json, pandas as pd, numpy as np
H=[1,5,15,60,240,1440]
def summ(d,p):
    o={'n':int(d[p+'entry_px'].notna().sum()) if p+'entry_px' in d else 0}
    if o['n']==0: return o
    for h in H:
        c=p+f'n{h}'
        if c in d and d[c].notna().sum()>0:
            o[f'win{h}']=float((d[c].dropna()>0).mean()*100); o[f'med{h}']=float(d[c].median()*100); o[f'mean{h}']=float(d[c].mean()*100); o[f'n{h}']=int(d[c].notna().sum())
    for k in ['peak_gain','t_peak_min','dd_before_peak','dd_after_peak','missed_move','peak60_gain','t_peak60_min','low24']:
        if p+k in d and d[p+k].notna().any():
            o['med_'+k]=float(d[p+k].median()*(1 if k.startswith('t_') else 100))
            if k=='peak_gain': o['p_peak10']=float((d[p+k].dropna()>0.10).mean()*100); o['p_peak5']=float((d[p+k].dropna()>0.05).mean()*100)
    return o
m=pd.read_parquet('data/events_metrics.parquet')
groups=['Upbit KRW','Upbit BTC/USDT only','Bithumb spot','Binance spot','Binance perp','OKX spot','Bybit spot','Coinbase spot']
S=json.load(open('data/summary.json'))
for tag,d in [('v2',m[m.collection_batch=='v2']),('v1_plus_v2',m)]:
    S[tag]={name:{g:summ(d[d.group==g],p) for g in groups} for p,name in [('ann_ext_','ann_ext'),('start_lst_','start_lst'),('start_ext_','start_ext')]}
S['v2_notes']={
 'collected_utc':'2026-11-13',
 'v2_scope':'Upbit listing notices 2024-01-01..2025-10-31; Binance spot listings with a USD-M perp at the announcement 2024-01..2026-11; Coinbase listings from the Coinbase Exchange status page 2024-01..2026-11',
 'coinbase_ann_ext':'04_metrics skips external-venue entries for Coinbase (v1 method), so ann_ext is empty for Coinbase even where an official time now exists',
 'sources_failed':['Bithumb notice archive (feed.bithumb.com 403, official API latest notices only, no browser session, Wayback offline)','Robinhood (no timestamped official listing feed)','Hyperliquid historical trades (no public API)','DEX per-swap history (GeckoTerminal trades last 24 h only)','CoinSentry Worker (credentials not available)'],
 'sources_partial':['Hyperliquid candles (finest interval whose ~5000-candle history reaches the window)','DEX candles (GeckoTerminal public OHLCV only for the last 180 days; liquidity is current, not at the announcement)','Bithumb official times (1 of 64 v1 events, from feed-api.bithumb.com/v1/notices)','Binance spot REST aggTrades (empty for older windows; refilled from data.binance.vision spot archives)']}
json.dump(S,open('data/summary.json','w'),default=lambda x:None)
for k in ['ann_ext','start_lst']:
    print(k,pd.DataFrame(S['v2'][k]).T[['n','med5','med60','med1440']].round(1).to_string())
