"""aggTrades ticks (announcement-60s .. +90s) for every speed-test candidate: events whose external
venue at the announcement was Binance spot (REST /api/v3/aggTrades) or Binance USD-M perp
(REST is limited to the last 2 days, so data.binance.vision daily aggTrades zips are used)."""
import sys, io, zipfile, os, datetime as dt, pandas as pd, requests
sys.path.insert(0,'scripts'); from common import get
from concurrent.futures import ThreadPoolExecutor
m=pd.read_csv('out/events_metrics.csv')
c=m[m.ext_at_ann.isin(['binance','binance_perp'])]
os.makedirs('raw/bv',exist_ok=True)
def spot(sym,a):
    tr=[]; s=a-60000
    while s<a+90000:
        d=get(f"https://data-api.binance.vision/api/v3/aggTrades?symbol={sym}&startTime={s}&endTime={a+90000}&limit=1000",min_interval=0.2)
        if not isinstance(d,list) or not d: break
        tr+=[(x['a'],float(x['p']),float(x['q']),int(x['T']),bool(x['m'])) for x in d]
        if len(d)<1000: break
        s=d[-1]['T']+1
    return tr,'rest_api_v3_aggTrades'
def perp(sym,a):
    days={dt.datetime.fromtimestamp((a+o)/1000,dt.timezone.utc).strftime('%Y-%m-%d') for o in (-60000,90000)}
    tr=[]; src=[]
    for day in sorted(days):
        fn=f'raw/bv/{sym}-{day}.csv'
        if not os.path.exists(fn):
            r=requests.get(f"https://data.binance.vision/data/futures/um/daily/aggTrades/{sym}/{sym}-aggTrades-{day}.zip",timeout=120)
            if r.status_code!=200: open(fn,'w').write('MISSING'); continue
            z=zipfile.ZipFile(io.BytesIO(r.content)); raw=z.read(z.namelist()[0]).decode()
            # keep only rows near any announcement that day is unknown here -> filter now for this event window, cache per event
            lines=[l for l in raw.splitlines() if l and l[0].isdigit()]
            df=pd.DataFrame([l.split(',') for l in lines]).iloc[:,:7]
            df.columns=['a','p','q','f','l','T','m']; df.to_csv(fn,index=False)
        if open(fn).read(7)=='MISSING': continue
        df=pd.read_csv(fn); df=df[(df['T']>=a-60000)&(df['T']<=a+90000)]
        tr+=[(int(x.a),float(x.p),float(x.q),int(x.T),str(x.m).lower()=='true') for x in df.itertuples()]
        src.append('data.binance.vision/futures/um/daily/aggTrades')
    return tr,(src[0] if src else 'missing')
def one(r):
    a=int(r.ann_ms); sym=r.ext_market
    tr,src=(spot if r.ext_at_ann=='binance' else perp)(sym,a)
    df=pd.DataFrame(tr,columns=['agg_trade_id','price','qty','timestamp_ms','is_buyer_maker'])
    df.insert(0,'event_id',r.event_id); df.insert(1,'venue','binance_spot' if r.ext_at_ann=='binance' else 'binance_perp'); df.insert(2,'symbol',sym)
    return dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,venue=df.venue.iloc[0] if len(df) else ('binance_spot' if r.ext_at_ann=='binance' else 'binance_perp'),
                market=sym,announcement_ms=a,n_ticks=len(df),source=src,in_original_speed_test=False), df
with ThreadPoolExecutor(4) as tp: res=list(tp.map(one,[r for _,r in c.iterrows()]))
idx=pd.DataFrame([x[0] for x in res]); t=pd.read_csv('out/tick_entry.csv'); idx['in_original_speed_test']=idx.event_id.isin(t.event_id)
idx.to_parquet('extra/aggtrades_index.parquet',index=False)
pd.concat([x[1] for x in res if len(x[1])],ignore_index=True).to_parquet('extra/aggtrades.parquet',index=False)
print(idx.groupby('venue').agg(n=('event_id','count'),with_ticks=('n_ticks',lambda s:(s>0).sum()),ticks=('n_ticks','sum')))
