"""CoinSentry latency for every CoinSentry listing record that can be matched to an official time.
announced -> official announcement time (Upbit notice first_listed_at, Binance CMS releaseDate, OKX pTime,
Bybit publishTime; Bithumb has no official archive reachable, CryptoListing.ws detection time is used and flagged).
live -> first 1-minute trade on the listing market (trading_open_ms) and CoinSentry's tradingStartsAtMs."""
import json, re, datetime as dt, pandas as pd
a=pd.read_csv('raw/coinsentry_alerts.csv')
a=a[(a.service=='coinsentry')&a.event.isin(['listing_announced','listing_live'])&~a.exchange.isin(['test-exchange'])]
ann=[]
for n in json.load(open('raw/upbit_notices.json')):
    ann.append(('Upbit',int(dt.datetime.fromisoformat(n['first_listed_at']).timestamp()*1000),n['title'],'upbit_notice_first_listed_at',True))
for x in json.load(open('raw/binance_announcements.json')): ann.append(('Binance',int(x['releaseDate']),x['title'],'binance_cms_releaseDate',True))
for x in json.load(open('raw/okx_announcements.json')): ann.append(('OKX',int(x['pTime']),x['title'],'okx_pTime',True))
for x in json.load(open('raw/bybit_announcements.json')): ann.append(('Bybit',int(x['publishTime']),x['title'],'bybit_publishTime',True))
for e in json.load(open('raw/clw_recent_announcements.json'))['events']:
    if e['cex']=='bithumb' and e['type']=='spot_listing': ann.append(('Bithumb',e['detected_at_us']//1000,e['ticker'],'cryptolisting_ws_detected_at (not official)',False))
ann=pd.DataFrame(ann,columns=['exchange','ref_ms','title','ref_source','ref_is_official'])
m=pd.read_csv('out/events_metrics.csv')
rows=[]
for _,r in a.iterrows():
    o=dict(alert_id=int(r.id),exchange=r.exchange,symbol=r.symbol,event=r.event,detected_ms=int(r.detected_ms),worker_recv_ms=int(r.recv_ms),
           trading_starts_ms=None if pd.isna(r.trading_starts_ms) else int(r.trading_starts_ms))
    o['worker_recv_minus_detected_ms']=o['worker_recv_ms']-o['detected_ms']
    if r.event=='listing_announced':
        sym=r.symbol; base=re.sub(r'^X','',sym) if r.exchange=='OKX' else sym
        c=ann[(ann.exchange==r.exchange)&(ann.ref_ms<=o['detected_ms']+60000)&(ann.ref_ms>=o['detected_ms']-14*86400000)]
        c=c[c.title.str.contains(rf'(?<![A-Za-z0-9]){re.escape(sym)}(?![A-Za-z0-9])',case=False,regex=True)|
            c.title.str.contains(rf'(?<![A-Za-z0-9])x{re.escape(base)}(?![A-Za-z0-9])',case=False,regex=True)]
        if len(c):
            b=c.iloc[(o['detected_ms']-c.ref_ms).abs().argsort()].iloc[0]
            o.update(reference='announcement',reference_ms=int(b.ref_ms),reference_source=b.ref_source,reference_is_official=bool(b.ref_is_official),reference_title=b.title)
    else:
        e=m[(m.exchange==r.exchange)&(m.symbol==r.symbol)&m.start_ms.notna()]
        if len(e):
            o.update(reference='first_trade_1m_candle',reference_ms=int(e.start_ms.iloc[0]),reference_source='first 1m candle on '+str(e.lst_market.iloc[0]),reference_is_official=False)
    if o.get('reference_ms') is not None: o['latency_ms']=o['detected_ms']-o['reference_ms']
    rows.append(o)
df=pd.DataFrame(rows); df.to_parquet('extra/coinsentry_latency.parquet',index=False)
print(len(df), df.latency_ms.notna().sum()); print(df[['exchange','symbol','event','latency_ms','reference_source']].to_string())
