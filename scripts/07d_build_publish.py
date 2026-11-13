"""Assemble the public dataset in publish/: CSV + Parquet per table, timestamps as UTC epoch ms (Int64, *_ms)."""
import os, re, json, shutil, glob, datetime as dt, pandas as pd, numpy as np
P='publish'; D=f'{P}/data'; os.makedirs(D,exist_ok=True)
counts={}
def save(df,name,csv_gzip=False):
    for c in df.columns:
        if c.endswith('_ms'): df[c]=pd.to_numeric(df[c],errors='coerce').round().astype('Int64')
    df.to_parquet(f'{D}/{name}.parquet',index=False)
    df.to_csv(f'{D}/{name}.csv',index=False)
    if os.path.getsize(f'{D}/{name}.csv')>90e6:
        os.remove(f'{D}/{name}.csv'); df.to_csv(f'{D}/{name}.csv.gz',index=False,compression='gzip')
        if os.path.getsize(f'{D}/{name}.csv.gz')>90e6:
            os.remove(f'{D}/{name}.csv.gz'); n=int(np.ceil(len(df)/1_500_000))
            for i in range(n): df.iloc[i*1_500_000:(i+1)*1_500_000].to_csv(f'{D}/{name}.part{i+1:02d}.csv.gz',index=False,compression='gzip')
    counts[name]=len(df)
m=pd.read_csv('out/events_metrics.csv',low_memory=False)
# --- events_metrics (full), *_entry_ts -> *_entry_ms
ren={c:c.replace('_entry_ts','_entry_ms') for c in m.columns if c.endswith('_entry_ts')}
ren.update({'ann_ms':'announcement_ms','start_ms':'trading_open_ms'})
em=m.rename(columns=ren)
em.loc[em.exchange.eq('Coinbase')&em.ann_source.astype(str).str.startswith('coinbase_first'),'coinbase_first_day_ms']=em.announcement_ms
em.loc[em.exchange.eq('Coinbase')&em.ann_source.astype(str).str.startswith('coinbase_first'),'announcement_ms']=np.nan
save(em,'events_metrics')
# --- events
def mtype(r):
    if r.exchange=='Upbit': return 'KRW' if 'KRW' in str(r.markets) else 'USDT'
    if r.exchange=='Bithumb': return 'KRW'
    return 'perp' if r['product']=='perp' else 'spot'
ev=pd.DataFrame({'event_id':em.event_id,'exchange':em.exchange,'symbol':em.symbol,'market_type':em.apply(mtype,axis=1),
    'quote':em.quote,'markets_opened':em.markets,'announcement_ms':em.announcement_ms,'announcement_source':em.ann_source,
    'trading_open_ms':em.trading_open_ms,'measurement_venue':em.lst_venue,'measurement_market':em.lst_market,
    'external_venue_at_announcement':em.ext_at_ann,'external_market':em.ext_market,'already_trading_elsewhere':em.already_trading_elsewhere,
    'outlier_flag':(em.start_lst_outlier.fillna(False).astype(bool)|em.ann_ext_outlier.fillna(False).astype(bool)),
    'record_source':em.source,'notice_url':em.url})
save(ev,'events')
# --- excluded / incomplete events
ex=[]
def add(eid,exch,sym,analysis,reason): ex.append(dict(event_id=eid,exchange=exch,symbol=sym,analysis=analysis,reason=reason))
for _,r in em.iterrows():
    e,x,s=r.event_id,r.exchange,r.symbol
    if pd.isna(r.trading_open_ms): add(e,x,s,'trading_open','no 1m candles on listing market within 10 days of announcement (delisted / never opened / API returns nothing)')
    elif pd.isna(r.get('start_lst_entry_ms')): add(e,x,s,'trading_open','no trade in the 5 minutes after the entry minute (thin market)')
    elif pd.isna(r.get('start_lst_r1440')): add(e,x,s,'trading_open','24h window not complete (too recent) or data gap')
    if pd.isna(r.announcement_ms): add(e,x,s,'announcement','no announcement time (Coinbase: listing derived from first daily candle)')
    elif not r.already_trading_elsewhere: add(e,x,s,'announcement','coin not trading on any external venue in the 3h before the announcement (new token)')
    elif pd.isna(r.get('ann_ext_entry_ms')): add(e,x,s,'announcement','external venue had no trade within 5 min after entry minute')
    if x=='Upbit' and 'KRW' not in str(r.markets): add(e,x,s,'conclusions','Upbit BTC/USDT-only market: thin, excluded from conclusions')
    if r.get('start_lst_outlier')==True or r.get('ann_ext_outlier')==True: add(e,x,s,'flag','outlier (peak > +200% or |24h| > 100%), kept but flagged')
# parse-level exclusions from announcement feeds
for n in json.load(open('raw/upbit_notices.json')):
    for s in re.findall(r'\(([A-Z0-9]+)\) 거래지원 취소',n['title']): add('',"Upbit",s,'event_build','listing cancelled before trading (notice '+str(n['id'])+')')
for a in json.load(open('raw/binance_announcements.json')):
    t=a['title']
    if int(a['releaseDate'])<1761955200000: continue
    if 'RWUSD' in t: add('','Binance','RWUSD','event_build','stablecoin listing with zero-fee promo, excluded')
    if 'Perpetual' in t and re.search('TradFi|Multiple|Pre-IPO|Quanto',t): add('','Binance','','event_build','perp batch/TradFi/pre-IPO/quanto announcement excluded: '+t[:120])
    if 'bStocks' in t or 'Stocks on Binance' in t: add('','Binance','','event_build','tokenized-stock (bStocks) announcement not parsed: '+t[:120])
a=pd.read_csv('raw/coinsentry_alerts.csv')
for _,r in a.iterrows():
    if r.service!='coinsentry': add('','',str(r.symbol if isinstance(r.symbol,str) else ''),'coinsentry_log',f'alert {r.id}: other provider ({r.service}), dropped 2026-10-27')
    elif r.event not in ('listing_announced','listing_live'): add('',str(r.exchange),str(r.symbol),'coinsentry_log',f'alert {r.id}: {r.event} (not a listing)')
    elif r.exchange=='test-exchange': add('',str(r.exchange),str(r.symbol),'coinsentry_log',f'alert {r.id}: test record')
save(pd.DataFrame(ex),'excluded_events')
# --- extra tables
k=pd.read_parquet('extra/korean_perp_status.parquet'); save(k,'korean_perp_status')
for nm in ['perp_candles_1m','spot_candles_1m']:
    df=pd.read_parquet(f'extra/{nm}.parquet').rename(columns={'quote_volume':'volume'}); save(df,nm)
f=pd.read_parquet('extra/funding_history.parquet'); save(f,'funding_history')
save(pd.read_parquet('extra/aggtrades_index.parquet'),'aggtrades_index')
save(pd.read_parquet('extra/aggtrades.parquet'),'aggtrades')
cl=pd.read_parquet('extra/coinsentry_latency.parquet'); cl['latency_vs_trading_starts_ms']=cl.detected_ms-cl.trading_starts_ms
save(cl,'coinsentry_latency')
# sanitized CoinSentry log: exchange/symbol/pairs/times only
cs=a[a.service=='coinsentry'][['id','event','exchange','symbol','pairs','detected_ms','trading_starts_ms','recv_ms']].rename(columns={'id':'alert_id','recv_ms':'worker_recv_ms','trading_starts_ms':'trading_starts_ms'})
save(cs,'coinsentry_alerts')
# analysis outputs
save(pd.read_csv('out/tick_entry.csv'),'speed_test_tick_entry')
save(pd.read_csv('out/fast_entry.csv'),'speed_test_1m_entry')
save(pd.read_csv('out/sim_trades.csv'),'exit_rule_grid_trades')
eb=pd.read_csv('raw/events_all.csv').rename(columns={'ann_ms':'announcement_ms'}); save(eb,'events_source_list')
shutil.copy('out/summary.json',f'{D}/summary.json')
# code + docs
os.makedirs(f'{P}/scripts',exist_ok=True)
for s in glob.glob('scripts/*.py'): shutil.copy(s,f'{P}/scripts/')
json.dump(counts,open(f'{P}/row_counts.json','w'),indent=1); print(json.dumps(counts,indent=1))
