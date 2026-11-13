"""Dataset checks: row_counts.json matches the files, every file in data/ is under 50 MB, *_ms columns are integers,
event ids are unique, and v1 rows equal the v1 commit except the documented official-time columns. Exit 1 on any failure."""
import sys, os, re, glob, json, subprocess, io, numpy as np, pandas as pd
V1_COMMIT='e27214a'; LIMIT=50e6; ALLOWED={'announcement_ms','announcement_source','ann_source'}
fail=[]
counts=json.load(open('row_counts.json'))
for f in glob.glob('data/*'):
    if os.path.getsize(f)>LIMIT: fail.append(f'{f} is {os.path.getsize(f)/1e6:.1f} MB')
for name,n in counts.items():
    parts=sorted(glob.glob(f'data/{name}.parquet'))+sorted(glob.glob(f'data/{name}.part*.parquet'))
    if not parts:
        if name=='upbit_poll_log': continue
        fail.append(f'{name}: no parquet'); continue
    df=pd.concat([pd.read_parquet(p) for p in parts],ignore_index=True)
    if len(df)!=n: fail.append(f'{name}: {len(df)} rows, row_counts says {n}')
    bad=[c for c in df.columns if c.endswith('_ms') and not (pd.api.types.is_integer_dtype(df[c]) or df[c].isna().all())]
    if bad: fail.append(f'{name}: non-integer _ms columns {bad}')
ev=pd.read_parquet('data/events.parquet')
if ev.event_id.duplicated().any(): fail.append('events: duplicate event_id')
def same(x,y):
    xn,yn=x.isna(),y.isna()
    try: eq=np.isclose(pd.to_numeric(x).astype(float).fillna(0),pd.to_numeric(y).astype(float).fillna(0),rtol=1e-12,atol=0)
    except Exception: eq=x.astype(object).where(~xn,None)==y.astype(object).where(~yn,None)
    return (xn&yn)|(~xn&~yn&eq)
for t in ['events','events_metrics','events_source_list','korean_perp_status','aggtrades_index','excluded_events']:
    a=pd.read_parquet(io.BytesIO(subprocess.run(['git','show',f'{V1_COMMIT}:data/{t}.parquet'],capture_output=True,check=True).stdout))
    b=pd.read_parquet(f'data/{t}.parquet'); b=b[b.collection_batch.eq('v1')].reset_index(drop=True)
    if len(a)!=len(b): fail.append(f'{t}: {len(b)} v1 rows, expected {len(a)}'); continue
    for c in a.columns:
        if c in ALLOWED: continue
        if c not in b: fail.append(f'{t}: v1 column {c} missing'); continue
        n=int((~same(a[c],b[c])).sum())
        if n: fail.append(f'{t}.{c}: {n} v1 values changed')
print('\n'.join(fail) if fail else 'all dataset checks passed')
sys.exit(1 if fail else 0)
