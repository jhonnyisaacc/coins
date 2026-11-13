"""Refill Binance spot ticks that REST aggTrades no longer serves (empty for older windows) from
data.binance.vision/data/spot/daily/aggTrades. Spot archive times are microseconds from 2025-01-01; they are converted to ms."""
import sys, io, os, zipfile, datetime as dt, pandas as pd, requests
IDX=sys.argv[1]; TICKS=sys.argv[2]
os.makedirs('raw/bvs',exist_ok=True)
def ticks(sym,a):
    days=sorted({dt.datetime.fromtimestamp((a+o)/1000,dt.timezone.utc).strftime('%Y-%m-%d') for o in (-60000,90000)})
    out=[]; ok=False
    for day in days:
        fn=f'raw/bvs/{sym}-{day}-{a}.parquet'
        if not os.path.exists(fn):
            r=requests.get(f"https://data.binance.vision/data/spot/daily/aggTrades/{sym}/{sym}-aggTrades-{day}.zip",timeout=600)
            if r.status_code!=200: continue
            z=zipfile.ZipFile(io.BytesIO(r.content)); keep=[]
            for ch in pd.read_csv(z.open(z.namelist()[0]),header=None,usecols=range(7),chunksize=2_000_000):
                ch=ch[pd.to_numeric(ch[0],errors='coerce').notna()]
                T=pd.to_numeric(ch[5]); T=T.where(T<1e14,T//1000)
                ch=ch.assign(T=T)[(T>=a-60000)&(T<=a+90000)]
                keep.append(pd.DataFrame({'agg_trade_id':ch[0].astype('int64'),'price':ch[1].astype(float),'qty':ch[2].astype(float),
                    'timestamp_ms':ch['T'].astype('int64'),'is_buyer_maker':ch[6].astype(str).str.lower().eq('true')}))
            pd.concat(keep).to_parquet(fn)
        ok=True; out.append(pd.read_parquet(fn))
    return (pd.concat(out) if out else pd.DataFrame()), ('data.binance.vision/spot/daily/aggTrades' if ok else 'missing')
idx=pd.read_parquet(IDX); tk=pd.read_parquet(TICKS)
for i,r in idx[(idx.venue=='binance_spot')&(idx.n_ticks==0)].iterrows():
    df,src=ticks(r.market,int(r.announcement_ms))
    if len(df):
        df.insert(0,'event_id',r.event_id); df.insert(1,'venue','binance_spot'); df.insert(2,'symbol',r.market)
        tk=pd.concat([tk,df],ignore_index=True)
    idx.loc[i,'n_ticks']=len(df); idx.loc[i,'source']=src if len(df) else 'missing (REST empty; archive: '+src+')'
    print(r.event_id,r.market,len(df),src,flush=True)
idx.to_parquet(IDX,index=False); tk.to_parquet(TICKS,index=False)
