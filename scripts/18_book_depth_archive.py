"""Historical order-book depth around announcements from data.binance.vision/data/futures/um/daily/bookDepth (cumulative
depth and notional within +-1..5% of price, one snapshot every ~30-60 s, 1-second timestamps). Spot has no bookDepth or
bookTicker archive, and futures bookTicker stops in 2024-03, so only USD-M perps are covered. Window: 60 s before to 90 s
after the announcement, widened by one snapshot on each side so the book just before the announcement is kept.
Events: every (event, binance_perp) pair in the v2 publication's aggtrades_index (raw/v2pub) plus extra/v3/aggtrades_index(_bithumb) if present.
Output: extra/v3/book_depth_bands.parquet, extra/v3/book_depth_index.parquet."""
import io, os, sys, zipfile, datetime as dt, pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v3'; CACHE='raw/bookdepth'; os.makedirs(OUT,exist_ok=True); os.makedirs(CACHE,exist_ok=True)
S=requests.Session()
idx=[pd.read_parquet('raw/v2pub/aggtrades_index.parquet')]
for f in (f'{OUT}/aggtrades_index.parquet',f'{OUT}/aggtrades_index_bithumb.parquet'):
    if os.path.exists(f): idx.append(pd.read_parquet(f))
ev=pd.concat(idx,ignore_index=True)
ev=ev[ev.venue.eq('binance_perp')].drop_duplicates(['event_id','market'])[['event_id','market','announcement_ms']]

def day(sym,d):
    fn=f'{CACHE}/{sym}-{d}.parquet'
    if not os.path.exists(fn):
        r=S.get(f'https://data.binance.vision/data/futures/um/daily/bookDepth/{sym}/{sym}-bookDepth-{d}.zip',timeout=120)
        if r.status_code!=200: pd.DataFrame({'missing':[r.status_code]}).to_parquet(fn); return None
        z=zipfile.ZipFile(io.BytesIO(r.content)); df=pd.read_csv(z.open(z.namelist()[0]))
        ts=(pd.to_datetime(df.timestamp,utc=True)-pd.Timestamp(0,tz='UTC'))//pd.Timedelta(milliseconds=1)
        pd.DataFrame({'timestamp_ms':ts,'percentage':df.percentage.astype(int),'depth_qty':df.depth.astype(float),'notional_usd':df.notional.astype(float)}).to_parquet(fn)
    d=pd.read_parquet(fn)
    if 'missing' in d: return None
    if d.timestamp_ms.max()<1e11: d['timestamp_ms']=d.timestamp_ms*1000; d.to_parquet(fn)
    return d

def one(r):
    a=int(r.announcement_ms)
    days=sorted({dt.datetime.fromtimestamp((a+o)/1000,dt.timezone.utc).strftime('%Y-%m-%d') for o in (-600000,600000)})
    parts=[x for x in (day(r.market,d) for d in days) if x is not None]
    if not parts: return dict(event_id=r.event_id,venue='binance_perp',market=r.market,announcement_ms=a,n_snapshots=0,source='missing: no bookDepth archive file'),None
    d=pd.concat(parts); t=sorted(d.timestamp_ms.unique())
    before=[x for x in t if x<a-60000]; after=[x for x in t if x>a+90000]
    lo=before[-1] if before else a-60000; hi=after[0] if after else a+90000
    w=d[(d.timestamp_ms>=lo)&(d.timestamp_ms<=hi)].copy()
    w.insert(0,'event_id',r.event_id); w.insert(1,'venue','binance_perp'); w.insert(2,'market',r.market)
    snaps=w.timestamp_ms.unique()
    return dict(event_id=r.event_id,venue='binance_perp',market=r.market,announcement_ms=a,n_snapshots=len(snaps),
                first_snapshot_ms=int(snaps.min()) if len(snaps) else None,last_snapshot_ms=int(snaps.max()) if len(snaps) else None,
                last_snapshot_before_ann_ms=int(max([x for x in snaps if x<=a],default=0)) or None,
                source='data.binance.vision/futures/um/daily/bookDepth'),w

if __name__=='__main__':
    with ThreadPoolExecutor(6) as tp: res=list(tp.map(one,[r for r in ev.itertuples()]))
    pd.DataFrame([x[0] for x in res]).to_parquet(f'{OUT}/book_depth_index.parquet',index=False)
    b=[x[1] for x in res if x[1] is not None and len(x[1])]
    (pd.concat(b,ignore_index=True) if b else pd.DataFrame()).to_parquet(f'{OUT}/book_depth_bands.parquet',index=False)
    print('done',len(res),sum(1 for x in res if x[0]['n_snapshots']))
