"""Append the v3 collection to the published dataset in data/ without changing any v1 or v2 row. The base is the v2
publication (main commit f1cc253), copied to raw/v2pub so reruns are idempotent. Shared tables (events, events_metrics,
events_source_list, aggtrades_index, excluded_events) get v3 rows appended. dex_pool_status gets liquidity_usd_at_ann filled
where it was empty plus a liquidity_at_ann_method column (no other value changes). Large v3 tables go to <table>_v3_<year>
files split by the event's announcement year; new tables are written whole. Every file stays under 50 MB."""
import os, re, json, glob, subprocess, datetime as dt, importlib, sys, numpy as np, pandas as pd
D='data'; X='extra/v3'; LIMIT=50e6; COST=0.006; H=[1,5,15,60,240,1440]
BASE='raw/v2pub'; BASE_COMMIT='f1cc253'
SHARED=['events','events_metrics','events_source_list','aggtrades_index','excluded_events','dex_pool_status']
os.makedirs(BASE,exist_ok=True)
for f in SHARED:
    if not os.path.exists(f'{BASE}/{f}.parquet'): subprocess.run(f'git show {BASE_COMMIT}:data/{f}.parquet > {BASE}/{f}.parquet',shell=True,check=True)
if not os.path.exists(f'{BASE}/row_counts.json'): subprocess.run(f'git show {BASE_COMMIT}:row_counts.json > {BASE}/row_counts.json',shell=True,check=True)
counts=json.load(open(f'{BASE}/row_counts.json')); sizes={}
base=lambda t: pd.read_parquet(f'{BASE}/{t}.parquet')
rd=lambda n: pd.read_parquet(f'{X}/{n}.parquet') if os.path.exists(f'{X}/{n}.parquet') else pd.DataFrame()

def norm(df):
    for c in df.columns:
        if c.endswith('_ms'): df[c]=pd.to_numeric(df[c],errors='coerce').round().astype('Int64')
    return df

def save(df,name):
    df=norm(df.reset_index(drop=True))
    for f in glob.glob(f'{D}/{name}.parquet')+glob.glob(f'{D}/{name}.part*')+glob.glob(f'{D}/{name}.csv*'): os.remove(f)
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
    for yr,g in df.groupby(y): save(g.assign(collection_batch='v3'),f'{name}_v3_{yr}')

def derive(df):
    df=df.copy()
    df['group']=df.exchange+np.where(df['product']=='perp',' perp',' spot')
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

src3=[pd.read_csv(f'{X}/events_v3.csv')]; met3=[pd.read_csv('out/metrics_v3_raw.csv',low_memory=False)]
if os.path.exists(f'{X}/events_v3_bithumb.csv'):
    src3.append(pd.read_csv(f'{X}/events_v3_bithumb.csv')); met3.append(pd.read_csv('out/metrics_v3_bithumb_raw.csv',low_memory=False))
src3=pd.concat(src3,ignore_index=True); v3m=derive(pd.concat(met3,ignore_index=True)).assign(collection_batch='v3')
OFFICIAL_SRC={'binance_cms','okx_api','bybit_api','bithumb_page_via_wayback'}
v3m['announcement_time_official']=v3m.ann_source.isin(OFFICIAL_SRC)

em=base('events_metrics'); save(pd.concat([em,v3m[[c for c in v3m.columns if c in em.columns or c not in ('err',)]]],ignore_index=True),'events_metrics')

def mtype(r): return 'KRW' if r.exchange=='Bithumb' else ('perp' if r['product']=='perp' else 'spot')
v3e=pd.DataFrame({'event_id':v3m.event_id,'exchange':v3m.exchange,'symbol':v3m.symbol,'market_type':v3m.apply(mtype,axis=1),
    'quote':v3m.quote,'markets_opened':v3m.markets,'announcement_ms':v3m.announcement_ms,'announcement_source':v3m.ann_source,
    'trading_open_ms':v3m.trading_open_ms,'measurement_venue':v3m.lst_venue,'measurement_market':v3m.lst_market,
    'external_venue_at_announcement':v3m.ext_at_ann,'external_market':v3m.ext_market,'already_trading_elsewhere':v3m.already_trading_elsewhere.astype(bool),
    'outlier_flag':(v3m.get('start_lst_outlier',pd.Series(False,index=v3m.index)).fillna(False).astype(bool)|v3m.get('ann_ext_outlier',pd.Series(False,index=v3m.index)).fillna(False).astype(bool)),
    'record_source':v3m.source,'notice_url':v3m.url,'collection_batch':'v3','announcement_time_official':v3m.announcement_time_official})
ev=pd.concat([base('events'),v3e],ignore_index=True); save(ev,'events')
ANN=dict(zip(ev.event_id,ev.announcement_ms.astype('Int64')))

es=base('events_source_list'); cols=[c for c in es.columns if c not in ('collection_batch','announcement_time_official','v1_announcement_ms')]
v3s=src3.rename(columns={'ann_ms':'announcement_ms'})[cols].assign(collection_batch='v3')
v3s['announcement_time_official']=v3s.ann_source.isin(OFFICIAL_SRC)
save(pd.concat([es,v3s],ignore_index=True),'events_source_list')

ps=rd('perp_status_v3')
if os.path.exists(f'{X}/perp_status_v3_bithumb.parquet'): ps=pd.concat([ps,pd.read_parquet(f'{X}/perp_status_v3_bithumb.parquet')],ignore_index=True)
save(ps.assign(collection_batch='v3'),'perp_status_v3')
def cat(n): return pd.concat([rd(n),rd(n+'_bithumb')],ignore_index=True)
by_year(cat('perp_candles_1m_v3'),'perp_candles_1m',ANN)
by_year(cat('spot_candles_1m_v3'),'spot_candles_1m',ANN)
by_year(cat('aggtrades'),'aggtrades',ANN)
fu=rd('funding_v3')
if len(fu): by_year(fu,'funding_history',ANN)
ai3=cat('aggtrades_index').assign(collection_batch='v3')
save(pd.concat([base('aggtrades_index'),ai3],ignore_index=True),'aggtrades_index')

bk=[]; bi=[]
bd=rd('book_depth_bands')
if len(bd):
    bk.append(pd.DataFrame({'event_id':bd.event_id,'venue':bd.venue,'market':bd.market,'timestamp_ms':bd.timestamp_ms,
        'side':np.where(bd.percentage<0,'bid','ask'),'level':bd.percentage.abs().astype(int),'level_kind':'pct_band','price':np.nan,
        'qty':bd.depth_qty,'notional_usd':bd.notional_usd,'source':'data.binance.vision/futures/um/daily/bookDepth'}))
bix=rd('book_depth_index')
if len(bix): bi.append(bix.assign(level_kind='pct_band',window='ann-60s..ann+90s, widened by one snapshot each side'))
for f in sorted(glob.glob('raw/forward/book/*.parquet')):
    d=pd.read_parquet(f); d['level_kind']='price_level'; d['notional_usd']=d.price*d.qty; bk.append(d)
for f in sorted(glob.glob('raw/forward/book/*.json')):
    m=json.load(open(f)); bi.append(pd.DataFrame([dict(event_id=m['event_id'],venue=m['venue'],market=m['market'],n_snapshots=None,rows=m['rows'],
        source=f"forward capture: REST depth limit 100 + ws depth20@100ms for 300 s ({m['rest_status']})",level_kind='price_level',first_snapshot_ms=m['captured_at_ms'])]))
save((pd.concat(bk,ignore_index=True) if bk else pd.DataFrame(columns=['event_id','venue','market','timestamp_ms','side','level','level_kind','price','qty','notional_usd','source'])).assign(collection_batch='v3'),'book_snapshots')
save((pd.concat(bi,ignore_index=True) if bi else pd.DataFrame()).assign(collection_batch='v3'),'book_index')

dl=rd('delisted_daily_candles')
save(dl.assign(interval='1d',collection_batch='v3'),'delisted_daily_candles')
sw=rd('dex_swaps'); save(sw.assign(collection_batch='v3'),'dex_swaps')
dx=base('dex_pool_status'); dst=rd('dex_swaps_status')
if 'liquidity_at_ann_method' not in dx: dx['liquidity_at_ann_method']=pd.Series(pd.NA,index=dx.index,dtype='string')
if len(dst) and 'liquidity_usd_at_ann' in dst:
    for r in dst[dst.liquidity_usd_at_ann.notna()].itertuples():
        k=dx.event_id.eq(r.event_id)&dx.pool_address.eq(r.pool_address)&dx.liquidity_usd_at_ann.isna()
        dx.loc[k,'liquidity_usd_at_ann']=r.liquidity_usd_at_ann; dx.loc[k,'liquidity_at_ann_method']=r.liquidity_at_ann_method
save(dx,'dex_pool_status')
sus=rd('aggtrades_suspect_ticks'); save(sus.assign(collection_batch='v3'),'aggtrades_suspect_ticks')
bw=rd('bithumb_wayback_all_notices')
if len(bw): save(bw.assign(collection_batch='v3'),'bithumb_wayback_notices')
for n in ['upbit_poll_log','binance_poll_log','bithumb_poll_log','perp_limits_snapshots']:
    if os.path.exists(f'{D}/{n}.csv'):
        t=pd.read_csv(f'{D}/{n}.csv'); norm(t).to_parquet(f'{D}/{n}.parquet',index=False); counts[n]=len(t)

ex=[]
def add(eid,x,s,an,reason): ex.append(dict(event_id=eid,exchange=x,symbol=s,analysis=an,reason=reason,collection_batch='v3'))
for _,r in v3m.iterrows():
    e,x,s=r.event_id,r.exchange,r.symbol
    if pd.isna(r.trading_open_ms): add(e,x,s,'trading_open','no 1m candles on listing market within 10 days of announcement (delisted / never opened / API returns nothing)')
    elif pd.isna(r.get('start_lst_entry_ms')): add(e,x,s,'trading_open','no trade in the 5 minutes after the entry minute (thin market)')
    elif pd.isna(r.get('start_lst_r1440')): add(e,x,s,'trading_open','24h window not complete (too recent) or data gap')
    if not r.already_trading_elsewhere: add(e,x,s,'announcement','coin not trading on any external venue in the 3h before the announcement (new token)')
    elif pd.isna(r.get('ann_ext_entry_ms')): add(e,x,s,'announcement','external venue had no trade within 5 min after entry minute')
    if r.get('start_lst_outlier')==True or r.get('ann_ext_outlier')==True: add(e,x,s,'flag','outlier (peak > +200% or |24h| > 100%), kept but flagged')
for r in ai3[ai3.n_ticks.eq(0)].itertuples(): add(r.event_id,r.exchange,r.symbol,'aggtrades',f'{r.venue} {r.market}: no ticks in -60s..+90s ({r.source})')
fs=rd('funding_v3_status')
for r in fs[fs.n_rows.fillna(0).eq(0)].itertuples(): add(r.event_id,r.exchange,r.symbol,'funding',f'no funding rows: {r.note}'+(f' [{r.venue}]' if isinstance(getattr(r,"venue",None),str) else ''))
for r in bix[bix.n_snapshots.eq(0)].itertuples() if len(bix) else []: add(r.event_id,'','','book_snapshots',f'{r.venue} {r.market}: {r.source}')
for r in (dst[dst.note.notna()].itertuples() if len(dst) and 'note' in dst else []): add(r.event_id,'','','dex_swaps',f'{r.chain} {r.dex} {r.pool_address}: {r.note}')
for r in (dst[dst.get('liquidity_note',pd.Series(index=dst.index,dtype=str)).notna()].itertuples() if len(dst) else []): add(r.event_id,'','','dex_liquidity_at_ann',f'{r.chain} {r.dex}: {r.liquidity_note}')
dls=rd('delisted_daily_status')
for r in (dls[dls.source.isna()].itertuples() if len(dls) else []): add(r.event_id,r.exchange,r.symbol,'delisted_daily',r.note)
nk=f'{X}/bithumb_v3_non_krw.csv'
for r in (pd.read_csv(nk).itertuples() if os.path.exists(nk) and os.path.getsize(nk)>1 else []):
    add('','Bithumb',r.symbol,'event_build',f'Bithumb {r.market}-market addition at {r.ann_ms} ({r.title}): not a KRW listing, not measured (04_metrics uses the KRW market)')
wb=json.load(open(f'{X}/bithumb_wayback_status.json')) if os.path.exists(f'{X}/bithumb_wayback_status.json') else {}
add('','','','test_order','Binance /api/v3/order/test and /fapi/v1/order/test are SIGNED (need an API key): test-order round trip not recorded; pollers log test_order_status')
add('','Binance','','book_snapshots','data.binance.vision has no spot bookDepth/bookTicker archive and futures bookTicker stops in 2024-03: historical books are USD-M perp bookDepth bands only (+-1..5%, ~30-60 s cadence), not price levels')
add('','','','book_snapshots_forward','forward REST depth + 5-minute websocket captures exist only for listing notices seen by the pollers after they started (2026-11-13)')
add('','Hyperliquid','','hyperliquid_archive','Hyperliquid historical archive (s3://hyperliquid-archive, s3://hl-mainnet-node-data) is requester-pays: anonymous reads are denied, so no 1m candles or trades from it')
add('','OKX','','funding','OKX public funding-rate-history keeps only recent months; older OKX perp windows have no funding')
add('','Bithumb','','source',f"Bithumb 2024-2025 from Wayback captures of feed.bithumb.com/notice: {json.dumps(wb,ensure_ascii=False)}")
add('','','','delisted_daily','CryptoCompare histoday now needs an API key (401); CoinGecko public market_chart serves only the last 365 days')
add('','Solana','','dex_swaps','Solana pools not covered: the free public RPC has no time-indexed history and paging signatures back months is not feasible at its rate limit; no free indexer without a key')
add('','BSC','','dex_swaps','BSC: free RPCs either prune history (bloXroute keeps a few weeks; drpc free plan has only recent state) or rate-limit eth_getLogs; only recent BSC windows are covered')
add('','Binance','','perp_limits','Binance per-symbol max leverage and notional brackets come from fapi/v1/leverageBracket, which is SIGNED; max_leverage is empty for Binance rows')
save(pd.concat([base('excluded_events'),pd.DataFrame(ex)],ignore_index=True),'excluded_events')

json.dump(counts,open('row_counts.json','w'),indent=1)
for f in sorted(glob.glob(f'{D}/*')): sizes[os.path.basename(f)]=os.path.getsize(f)
json.dump(sizes,open('out/file_sizes.json','w'),indent=1)
print(json.dumps({k:v for k,v in counts.items() if k not in json.load(open(f'{BASE}/row_counts.json')) or v!=json.load(open(f'{BASE}/row_counts.json'))[k]},indent=1))
print('over 50MB:',[(k,v) for k,v in sizes.items() if v>LIMIT])
