"""Daily candles, announcement day to 30 days after, for events whose listing market returned no 1-minute candles
(excluded_events analysis trading_open 'no 1m candles...' and delisted_since, plus v3 events whose metrics found no trading open). DAILY data: not comparable with the
1-minute metrics. Sources in order: Binance spot 1d klines, Binance USD-M 1d klines (both exchange-anchored by the exact
<SYM>USDT market), then CoinGecko market_chart/range (public API: last 365 days only), used only when the CoinGecko id is known
from dex_pool_status or the symbol maps to exactly one id in /coins/list. CryptoCompare needs an API key and is not used.
Output: extra/v3/delisted_daily_candles.parquet, extra/v3/delisted_daily_status.parquet."""
import sys, os, json, time, datetime as dt, pandas as pd, requests
sys.path.insert(0,'scripts'); from common import get
OUT='extra/v3'; DAY=86400000; NOW=int(time.time()*1000)
x=pd.read_parquet('raw/v2pub/excluded_events.parquet')
ids=set(x[(x.analysis.eq('trading_open')&x.reason.str.startswith('no 1m candles'))|x.analysis.eq('delisted_since')].event_id.dropna())
ev=pd.read_parquet('raw/v2pub/events.parquet')
ev=ev[ev.event_id.isin(ids)&ev.announcement_ms.notna()]
for f in ('out/metrics_v3_raw.csv','out/metrics_v3_bithumb_raw.csv'):
    if os.path.exists(f):
        v3=pd.read_csv(f,usecols=['event_id','exchange','symbol','ann_ms','start_ms']); v3=v3[v3.start_ms.isna()]
        ev=pd.concat([ev,v3.rename(columns={'ann_ms':'announcement_ms'})[['event_id','exchange','symbol','announcement_ms']]],ignore_index=True)
dex=pd.read_parquet('raw/v2pub/dex_pool_status.parquet')[['event_id','coingecko_id']].dropna().drop_duplicates('event_id')
cgid=dict(zip(dex.event_id,dex.coingecko_id))
clist=get('https://api.coingecko.com/api/v3/coins/list',min_interval=7)
bysym={}
for c in clist if isinstance(clist,list) else []: bysym.setdefault(c['symbol'].upper(),[]).append(c['id'])
def binance(url):
    d=get(url,min_interval=0.15)
    return [(int(k[0]),float(k[1]),float(k[2]),float(k[3]),float(k[4]),float(k[7])) for k in d] if isinstance(d,list) else []
rows=[]; st=[]
for r in ev.itertuples():
    a=int(r.announcement_ms); d0=a//DAY*DAY; d1=d0+31*DAY; s=r.symbol.rstrip('2') if r.symbol.endswith('2') and r.symbol[-2].isalpha() else r.symbol
    o=dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=a)
    got=None
    for src,url in (('binance_spot_1d',f'https://data-api.binance.vision/api/v3/klines?symbol={s}USDT&interval=1d&startTime={d0}&endTime={d1}&limit=40'),
                    ('binance_perp_1d',f'https://fapi.binance.com/fapi/v1/klines?symbol={s}USDT&interval=1d&startTime={d0}&endTime={d1}&limit=40')):
        k=binance(url)
        if k: got=(src,f'{s}USDT',k,'exact Binance market'); break
    if not got:
        cid=cgid.get(r.event_id); how='dex_pool_status.coingecko_id'
        if not cid and len(bysym.get(s,[]))==1: cid=bysym[s][0]; how='coins_list_unique_symbol'
        if not cid: o.update(source=None,note='not on Binance; CoinGecko id unknown or symbol ambiguous'); st.append(o); continue
        if a<NOW-365*DAY: o.update(source=None,coingecko_id=cid,note='CoinGecko public API serves only the last 365 days'); st.append(o); continue
        d=get(f'https://api.coingecko.com/api/v3/coins/{cid}/market_chart/range?vs_currency=usd&from={d0//1000}&to={d1//1000}',min_interval=7)
        p=d.get('prices') if isinstance(d,dict) else None
        if not p: o.update(source=None,coingecko_id=cid,note='CoinGecko returned no prices'); st.append(o); continue
        df=pd.DataFrame(p,columns=['t','px']); df['day']=df.t//DAY*DAY
        vol=pd.DataFrame(d.get('total_volumes') or [],columns=['t','v']); vol['day']=vol.t//DAY*DAY
        g=df.groupby('day').px.agg(['first','max','min','last']).join(vol.groupby('day').v.last())
        k=[(int(i),x['first'],x['max'],x['min'],x['last'],x['v']) for i,x in g.iterrows()]
        got=('coingecko_market_chart',cid,k,how+' (OHLC built from CoinGecko price points, volume = 24h USD volume)')
    src,mk,k,how=got
    rows+=[dict(event_id=r.event_id,source=src,market=mk,timestamp_ms=t,open=op,high=hi,low=lo,close=cl,volume=v) for t,op,hi,lo,cl,v in k]
    o.update(source=src,market=mk,mapping=how,n_days=len(k)); st.append(o)
pd.DataFrame(rows).to_parquet(f'{OUT}/delisted_daily_candles.parquet',index=False)
pd.DataFrame(st).to_parquet(f'{OUT}/delisted_daily_status.parquet',index=False)
print(len(ev),pd.DataFrame(st).source.value_counts(dropna=False).to_dict(),len(rows))
