"""Dataset checks: row_counts.json matches the files, every file in data/ is under 50 MB, *_ms columns are integers,
event ids are unique, v1 rows equal the v1 commit except the documented official-time columns, and v1/v2 rows equal the v2
publication (main commit f1cc253): shared tables row by row (dex_pool_status may only fill an empty liquidity_usd_at_ann),
every other v1/v2 data file byte for byte. v3 tables must carry collection_batch = v3. Exit 1 on any failure."""
import sys, os, re, glob, json, subprocess, io, numpy as np, pandas as pd
V1_COMMIT='e27214a'; V2_COMMIT='f1cc253'; LIMIT=50e6; ALLOWED={'announcement_ms','announcement_source','ann_source'}
SHARED=['events','events_metrics','events_source_list','aggtrades_index','excluded_events','dex_pool_status']
LIVE={'data/upbit_poll_log.csv','data/summary.json'}
fail=[]
git=lambda *a: subprocess.run(['git',*a],capture_output=True,check=True).stdout
counts=json.load(open('row_counts.json'))
for f in glob.glob('data/*'):
    if os.path.getsize(f)>LIMIT: fail.append(f'{f} is {os.path.getsize(f)/1e6:.1f} MB')
for name,n in counts.items():
    parts=sorted(glob.glob(f'data/{name}.parquet'))+sorted(glob.glob(f'data/{name}.part*.parquet'))
    if not parts:
        if name=='upbit_poll_log' and n==0: continue
        fail.append(f'{name}: no parquet'); continue
    if not (glob.glob(f'data/{name}.csv')+glob.glob(f'data/{name}.csv.gz')+glob.glob(f'data/{name}.part*.csv.gz')): fail.append(f'{name}: no csv')
    df=pd.concat([pd.read_parquet(p) for p in parts],ignore_index=True)
    if len(df)!=n: fail.append(f'{name}: {len(df)} rows, row_counts says {n}')
    bad=[c for c in df.columns if c.endswith('_ms') and not (pd.api.types.is_integer_dtype(df[c]) or df[c].isna().all())]
    if bad: fail.append(f'{name}: non-integer _ms columns {bad}')
    for c in [c for c in df.columns if c in ('timestamp_ms','announcement_ms','first_seen_ms','snapshot_ms')]:
        v=pd.to_numeric(df[c],errors='coerce').dropna()
        if len(v) and not v.between(1.23e12,4.1e12).all(): fail.append(f'{name}.{c}: values outside 2009..2100 in epoch ms (unit error?)')
    if ('_v3_' in name or name in ('book_snapshots','book_index','perp_status_v3','delisted_daily_candles','dex_swaps','aggtrades_suspect_ticks','bithumb_wayback_notices')) and not df.get('collection_batch',pd.Series(['v3'])).eq('v3').all():
        fail.append(f'{name}: rows without collection_batch v3')
ev=pd.read_parquet('data/events.parquet')
if ev.event_id.duplicated().any(): fail.append('events: duplicate event_id')
def same(x,y):
    xn,yn=x.isna(),y.isna()
    try: eq=np.isclose(pd.to_numeric(x).astype(float).fillna(0),pd.to_numeric(y).astype(float).fillna(0),rtol=1e-12,atol=0)
    except Exception: eq=x.astype(object).where(~xn,None)==y.astype(object).where(~yn,None)
    return (xn&yn)|(~xn&~yn&eq)
def compare(t,commit,batches,allowed=(),fill_only=()):
    a=pd.read_parquet(io.BytesIO(git('show',f'{commit}:data/{t}.parquet')))
    if 'collection_batch' in a: a=a[a.collection_batch.isin(batches)].reset_index(drop=True)
    b=pd.read_parquet(f'data/{t}.parquet')
    b=b[b.collection_batch.isin(batches)].reset_index(drop=True) if 'collection_batch' in b else b.iloc[:len(a)].reset_index(drop=True)
    if len(a)!=len(b): fail.append(f'{t}: {len(b)} {"/".join(batches)} rows, expected {len(a)} from {commit}'); return
    for c in a.columns:
        if c in allowed: continue
        if c not in b: fail.append(f'{t}: column {c} missing'); continue
        d=~same(a[c],b[c])
        if c in fill_only: d&=~a[c].isna()
        if int(d.sum()): fail.append(f'{t}.{c}: {int(d.sum())} {"/".join(batches)} values changed vs {commit}')
for t in ['events','events_metrics','events_source_list','korean_perp_status','aggtrades_index','excluded_events']:
    compare(t,V1_COMMIT,['v1'],allowed=ALLOWED)
for t in SHARED:
    compare(t,V2_COMMIT,['v1','v2'],fill_only=('liquidity_usd_at_ann',) if t=='dex_pool_status' else ())
for line in git('ls-tree','-r',V2_COMMIT,'data/').decode().splitlines():
    meta,path=line.split('\t'); blob=meta.split()[2]; name=os.path.basename(path).split('.')[0]
    if name in SHARED or path in LIVE: continue
    if not os.path.exists(path): fail.append(f'{path}: removed since {V2_COMMIT}'); continue
    if git('hash-object',path).decode().strip()!=blob: fail.append(f'{path}: changed since {V2_COMMIT}')
print('\n'.join(fail) if fail else 'all dataset checks passed')
sys.exit(1 if fail else 0)
