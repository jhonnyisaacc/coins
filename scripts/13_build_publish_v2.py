"""Append the v2 collection to the published dataset in data/ without changing v1 values (except the documented
Bithumb official-time and Coinbase official-time replacements, whose old values are kept in v1_announcement_ms).
Small tables get v2 rows appended plus a collection_batch column. Large tick and candle tables keep their v1 file as is;
v2 rows go to <table>_v2_<year> files split by the event's announcement year. Every file is kept under 50 MB. v1 inputs are read from the v1 commit (raw/v1), so reruns are idempotent."""
import os, re, json, glob, subprocess, datetime as dt, numpy as np, pandas as pd, requests
D='data'; X='extra/v2'; LIMIT=50e6; COST=0.006; H=[1,5,15,60,240,1440]
V1='raw/v1'; V1_COMMIT='e27214a'
os.makedirs(V1,exist_ok=True)
for f in ['events','events_metrics','events_source_list','korean_perp_status','aggtrades_index','excluded_events']:
    if not os.path.exists(f'{V1}/{f}.parquet'): subprocess.run(f'git show {V1_COMMIT}:data/{f}.parquet > {V1}/{f}.parquet',shell=True,check=True)
if not os.path.exists(f'{V1}/row_counts.json'): subprocess.run(f'git show {V1_COMMIT}:row_counts.json > {V1}/row_counts.json',shell=True,check=True)
counts=json.load(open(f'{V1}/row_counts.json')); sizes={}

def norm(df):
    for c in df.columns:
        if c.endswith('_ms'): df[c]=pd.to_numeric(df[c],errors='coerce').round().astype('Int64')
    return df

def save(df,name):
    df=norm(df.reset_index(drop=True))
    for f in glob.glob(f'{D}/{name}.*'): os.remove(f)
    df.to_parquet(f'{D}/{name}.parquet',index=False)
    if os.path.getsize(f'{D}/{name}.parquet')>LIMIT:
        os.remove(f'{D}/{name}.parquet'); n=int(np.ceil(len(df)/2_000_000))
        for i in range(n): df.iloc[i*2_000_000:(i+1)*2_000_000].to_parquet(f'{D}/{name}.part{i+1:02d}.parquet',index=False)
    df.to_csv(f'{D}/{name}.csv',index=False)
    if os.path.getsize(f'{D}/{name}.csv')>LIMIT:
        os.remove(f'{D}/{name}.csv'); df.to_csv(f'{D}/{name}.csv.gz',index=False,compression='gzip')
        if os.path.getsize(f'{D}/{name}.csv.gz')>LIMIT:
            os.remove(f'{D}/{name}.csv.gz'); n=int(np.ceil(len(df)/1_000_000))
            for i in range(n): df.iloc[i*1_000_000:(i+1)*1_000_000].to_csv(f'{D}/{name}.part{i+1:02d}.csv.gz',index=False,compression='gzip')
    counts[name]=len(df)

def by_year(df,name,ann):
    if df is None or not len(df): return
    y=df.event_id.map(ann).map(lambda ms: dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).year)
    for yr,g in df.groupby(y): save(g.assign(collection_batch='v2'),f'{name}_v2_{yr}')

rd=lambda n: pd.read_parquet(f'{X}/{n}.parquet') if os.path.exists(f'{X}/{n}.parquet') else pd.DataFrame()

def derive(df):
    df=df.copy()
    df['group']=df.exchange+np.where(df['product']=='perp',' perp',' spot')
    u=df.exchange=='Upbit'
    df.loc[u,'group']=np.where(df.loc[u,'markets'].astype(str).str.contains('KRW'),'Upbit KRW','Upbit BTC/USDT only')
    df['ann_hour_kst']=((df.ann_ms.astype('int64')//3600000)+9)%24
    df['new_token']=~df.already_trading_elsewhere.astype(bool)
    ext=df.ext_at_ann.astype('string')
    df['ext_kind']=np.where(ext.fillna('').str.contains('perp'),'perp',np.where(ext.notna(),'spot',''))
    for p in ['ann_ext_','start_lst_','start_ext_']:
        for h in H:
            if p+f'r{h}' in df: df[p+f'n{h}']=df[p+f'r{h}']-COST
        if p+'peak_gain' in df: df[p+'outlier']=(df[p+'peak_gain']>2)|(df[p+'r1440'].abs()>1)
    ren={c:c.replace('_entry_ts','_entry_ms') for c in df.columns if c.endswith('_entry_ts')}
    ren.update({'ann_ms':'announcement_ms','start_ms':'trading_open_ms'})
    return df.rename(columns=ren)

v1m=pd.read_parquet(f'{V1}/events_metrics.parquet').assign(collection_batch='v1')
mu=pd.read_csv('out/metrics_v2_raw.csv',low_memory=False)
mo=pd.read_csv('out/metrics_v2_other_raw.csv',low_memory=False) if os.path.exists('out/metrics_v2_other_raw.csv') else pd.DataFrame()
v2m=derive(pd.concat([mu,mo],ignore_index=True)).assign(collection_batch='v2')
oth=pd.read_csv('raw/v2_other_events.csv')
ofc={r.event_id:r for r in oth.itertuples()}

def official_cols(df):
    df['announcement_time_official']=~df.exchange.eq('Bithumb')
    df.loc[df.announcement_ms.isna(),'announcement_time_official']=False
    src=next(c for c in ('announcement_source','ann_source') if c in df)
    df.loc[df[src].astype(str).str.startswith(('coinsentry','coinbase_first','clw')),'announcement_time_official']=False
    return df

bt=[]
for f in sorted(glob.glob('raw/bithumb_api_notices_*.json')):
    for n in json.load(open(f)):
        if '마켓 추가' in (n.get('categories') or []):
            ms=int(dt.datetime.strptime(n['published_at'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone(dt.timedelta(hours=9))).timestamp()*1000)
            for s in re.findall(r'\(([A-Z0-9]+)\)',n['title']): bt.append((s,ms,n['pc_url']))
bt=sorted({s:(s,ms,u) for s,ms,u in sorted(bt,key=lambda x:-x[1])}.values())

def apply_official(df,ann_col,src_col):
    df['v1_announcement_ms']=pd.Series(pd.NA,index=df.index,dtype='Int64')
    for s,ms,url in bt:
        k=df.exchange.eq('Bithumb')&df.symbol.eq(s)&(df[ann_col]-ms).abs().le(6*3600000)
        df.loc[k,'v1_announcement_ms']=df.loc[k,ann_col]; df.loc[k,ann_col]=ms; df.loc[k,src_col]='bithumb_official_api_published_at'
        if 'announcement_time_official' in df: df.loc[k,'announcement_time_official']=True
    for r in oth[oth.v1_event_id.notna()].itertuples():
        k=df.event_id.eq(r.v1_event_id)
        df.loc[k,'v1_announcement_ms']=df.loc[k,ann_col]; df.loc[k,ann_col]=r.ann_ms; df.loc[k,src_col]=r.ann_source
        if 'announcement_time_official' in df: df.loc[k,'announcement_time_official']=True
    return df

em=pd.concat([v1m,v2m],ignore_index=True)
em=official_cols(em); em=apply_official(em,'announcement_ms','ann_source')
save(em,'events_metrics')

def mtype(r):
    if r.exchange=='Upbit': return 'KRW' if 'KRW' in str(r.markets) else 'USDT'
    if r.exchange=='Bithumb': return 'KRW'
    return 'perp' if r['product']=='perp' else 'spot'
v1e=pd.read_parquet(f'{V1}/events.parquet').assign(collection_batch='v1')
v2e=pd.DataFrame({'event_id':v2m.event_id,'exchange':v2m.exchange,'symbol':v2m.symbol,'market_type':v2m.apply(mtype,axis=1),
    'quote':v2m.quote,'markets_opened':v2m.markets,'announcement_ms':v2m.announcement_ms,'announcement_source':v2m.ann_source,
    'trading_open_ms':v2m.trading_open_ms,'measurement_venue':v2m.lst_venue,'measurement_market':v2m.lst_market,
    'external_venue_at_announcement':v2m.ext_at_ann,'external_market':v2m.ext_market,'already_trading_elsewhere':v2m.already_trading_elsewhere.astype(bool),
    'outlier_flag':(v2m.get('start_lst_outlier',pd.Series(False,index=v2m.index)).fillna(False).astype(bool)|v2m.get('ann_ext_outlier',pd.Series(False,index=v2m.index)).fillna(False).astype(bool)),
    'record_source':v2m.source,'notice_url':v2m.url,'collection_batch':'v2'})
ev=pd.concat([v1e,v2e],ignore_index=True)
ev=official_cols(ev); ev=apply_official(ev,'announcement_ms','announcement_source')
cbx=oth.set_index('event_id')
ev['coinbase_full_trading_ms']=ev.event_id.map(cbx.coinbase_full_trading_ms[~cbx.index.duplicated()])
for r in oth[oth.v1_event_id.notna()].itertuples(): ev.loc[ev.event_id.eq(r.v1_event_id),'coinbase_full_trading_ms']=r.coinbase_full_trading_ms
ev['coinbase_usd_product_status_now']=ev.event_id.map(cbx.coinbase_usd_product_status_now[~cbx.index.duplicated()])
for r in oth[oth.v1_event_id.notna()].itertuples(): ev.loc[ev.event_id.eq(r.v1_event_id),'coinbase_usd_product_status_now']=r.coinbase_usd_product_status_now
save(ev,'events')
ANN=dict(zip(ev.event_id,ev.announcement_ms.astype('Int64')))

v1s=pd.read_parquet(f'{V1}/events_source_list.parquet').assign(collection_batch='v1')
src=pd.concat([pd.read_csv('raw/events_all_v2.csv'),oth[oth.event_id.isin(v2m.event_id)]],ignore_index=True)
cols=[c for c in v1s.columns if c not in ('collection_batch',)]
v2s=src.rename(columns={'ann_ms':'announcement_ms'})[cols].assign(collection_batch='v2')
es=official_cols(pd.concat([v1s,v2s],ignore_index=True))
es=apply_official(es,'announcement_ms','ann_source')
save(es,'events_source_list')

kp=pd.concat([pd.read_parquet(f'{V1}/korean_perp_status.parquet').assign(collection_batch='v1'),rd('korean_perp_status').assign(collection_batch='v2')],ignore_index=True)
sl=rd('binance_spot_listing')
kp=kp.drop(columns=[c for c in sl.columns if c!='event_id' and c in kp]).merge(sl,on='event_id',how='left')
kp=apply_official(kp.assign(exchange=kp.exchange),'announcement_ms','_src').drop(columns=['_src'],errors='ignore')
save(kp,'korean_perp_status')

def in_window(df,lo,hi):
    if not len(df): return df
    a=df.event_id.map(ANN).astype('float')
    return df[(df.timestamp_ms>=a+lo)&(df.timestamp_ms<=a+hi)].drop_duplicates()
W=(-60*60000,72*3600000); T=(-60000,90000)
by_year(rd('perp_candles_1m'),'perp_candles_1m',ANN)
by_year(in_window(rd('other_perp_candles_1m'),*W),'perp_candles_1m_other',ANN)
by_year(rd('spot_candles_1m'),'spot_candles_1m',ANN)
by_year(pd.concat([rd('funding_history'),in_window(rd('other_funding_history'),*W)],ignore_index=True),'funding_history',ANN)
by_year(pd.concat([rd('aggtrades'),in_window(rd('other_aggtrades'),*T)],ignore_index=True),'aggtrades',ANN)
btc=rd('btc_candles_1m')
if len(btc):
    y=btc.event_id.map(ANN).map(lambda ms: dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).year)
    for yr,g in btc.groupby(y): save(g,f'btc_candles_1m_{yr}')
ai=pd.concat([pd.read_parquet(f'{V1}/aggtrades_index.parquet').assign(collection_batch='v1'),
              pd.concat([rd('aggtrades_index'),(lambda o:o[o.announcement_ms.eq(o.event_id.map(ANN))])(rd('other_aggtrades_index'))],ignore_index=True).assign(collection_batch='v2')],ignore_index=True)
save(ai,'aggtrades_index')

for n in ['hyperliquid_perp_status','hyperliquid_candles','hyperliquid_funding','dex_pool_status','dex_candles']:
    t=rd(n)
    if len(t): save(t,n)
if os.path.exists(f'{D}/upbit_poll_log.csv'): counts['upbit_poll_log']=len(pd.read_csv(f'{D}/upbit_poll_log.csv'))

v1x=pd.read_parquet(f'{V1}/excluded_events.parquet').assign(collection_batch='v1')
ex=[]
def add(eid,x,s,an,reason): ex.append(dict(event_id=eid,exchange=x,symbol=s,analysis=an,reason=reason,collection_batch='v2'))
for _,r in v2m.iterrows():
    e,x,s=r.event_id,r.exchange,r.symbol
    if pd.isna(r.trading_open_ms): add(e,x,s,'trading_open','no 1m candles on listing market within 10 days of announcement (delisted / never opened / API returns nothing)')
    elif pd.isna(r.get('start_lst_entry_ms')): add(e,x,s,'trading_open','no trade in the 5 minutes after the entry minute (thin market)')
    elif pd.isna(r.get('start_lst_r1440')): add(e,x,s,'trading_open','24h window not complete (too recent) or data gap')
    if x=='Coinbase': pass
    elif not r.already_trading_elsewhere: add(e,x,s,'announcement','coin not trading on any external venue in the 3h before the announcement (new token)')
    elif pd.isna(r.get('ann_ext_entry_ms')): add(e,x,s,'announcement','external venue had no trade within 5 min after entry minute')
    if x=='Upbit' and 'KRW' not in str(r.markets): add(e,x,s,'conclusions','Upbit BTC/USDT-only market: thin, excluded from conclusions')
    if r.get('start_lst_outlier')==True or r.get('ann_ext_outlier')==True: add(e,x,s,'flag','outlier (peak > +200% or |24h| > 100%), kept but flagged')
up_now={m['market'] for m in requests.get('https://api.upbit.com/v1/market/all',timeout=30).json()}
for r in ev[ev.exchange.eq('Upbit')].itertuples():
    q='KRW' if r.market_type=='KRW' else 'USDT'
    if f'{q}-{r.symbol}' not in up_now and f'BTC-{r.symbol}' not in up_now: add(r.event_id,'Upbit',r.symbol,'delisted_since',f'no {q}/BTC market for this symbol on Upbit today (api.upbit.com/v1/market/all)')
for r in ev[ev.exchange.eq('Coinbase')&ev.coinbase_usd_product_status_now.isin(['delisted','not_listed_now'])].itertuples():
    add(r.event_id,'Coinbase',r.symbol,'delisted_since',f'Coinbase Exchange {r.symbol}-USD product status today: {r.coinbase_usd_product_status_now}')
for r in oth[(oth.exchange=='Binance')&~oth.binance_perp_at_ann.fillna(False).astype(bool)].itertuples():
    add('','Binance',r.symbol,'event_build',f'Binance spot listing {r.ann_ms} without a Binance USD-M perp trading in the 3h before: outside item 15 scope')
for r in ai[ai.collection_batch.eq('v2')&ai.n_ticks.eq(0)].itertuples():
    add(r.event_id,r.exchange,r.symbol,'aggtrades',f'{r.venue} {r.market}: no ticks in -60s..+90s ({r.source})')
hl=rd('hyperliquid_perp_status')
for r in hl[hl.hl_coin.isna()].itertuples(): add(r.event_id,r.exchange,r.symbol,'hyperliquid','no Hyperliquid perp with this name (meta universe incl. delisted)')
dx=rd('dex_pool_status')
for r in dx[dx.get('note',pd.Series(index=dx.index,dtype=str)).notna()].itertuples(): add(r.event_id,r.exchange,r.symbol,'dex',r.note+(f' [{r.chain}]' if isinstance(getattr(r,'chain',None),str) else ''))
add('','Bithumb','','source','Bithumb listings 2024-01-01..2025-10-31 not collected: feed.bithumb.com returns 403 to automated reads, the official API serves only the latest notices, no browser session was available and the Wayback Machine was offline; no other official archive found')
add('','Robinhood','','source','Robinhood listings not collected: no official timestamped listing feed reachable (newsroom feed 404, nummus currency_pairs has no listing time, X posts need an API key)')
add('','','','hyperliquid_trades','hyperliquid_trades not built: Hyperliquid serves no public historical trades (recentTrades only; the node-data S3 archive is requester-pays)')
add('','','','dex_trades','dex_trades (per swap) not built: GeckoTerminal public trades cover the last 24 h only and no keyed indexer/RPC archive was used; 1m pool candles are in dex_candles for events inside the 180-day window')
add('','CoinSentry','','coinsentry_latency','not extended: WORKER_BASE_URL / WORKER_READ_TOKEN not available in this environment')
save(pd.concat([v1x,pd.DataFrame(ex)],ignore_index=True),'excluded_events')

json.dump(counts,open('row_counts.json','w'),indent=1)
for f in sorted(glob.glob(f'{D}/*')): sizes[os.path.basename(f)]=os.path.getsize(f)
json.dump(sizes,open('out/file_sizes.json','w'),indent=1)
big=[(k,v) for k,v in sizes.items() if v>LIMIT]
print(json.dumps(counts,indent=1)); print('over 50MB:',big)
