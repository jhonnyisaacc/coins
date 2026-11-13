"""Coinbase has no listing-announcement API. Derive listings = USD products whose first daily candle
falls on/after 2025-11-01 (trading start); announcement time unknown."""
import sys,csv,json,datetime as dt; sys.path.insert(0,'scripts'); from common import get; from candles import candles
START=int(dt.datetime(2025,11,1,tzinfo=dt.timezone.utc).timestamp()*1000)
now=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
prods=get("https://api.exchange.coinbase.com/products",cache=False)
json.dump(prods,open('raw/coinbase_products.json','w'))
out=[]
for p in prods:
    if p['quote_currency']!='USD' or p['status']!='online': continue
    d=candles('coinbase',p['id'],START-20*86400000,now,unit=60*24) if False else None
    # daily candles via direct calls (granularity 86400)
    first=None; existed=False
    for s,e in [(START-10*86400000,START+290*86400000),(START+290*86400000,now)]:
        r=get(f"https://api.exchange.coinbase.com/products/{p['id']}/candles?granularity=86400&start={dt.datetime.utcfromtimestamp(s/1000):%Y-%m-%dT%H:%M:%SZ}&end={dt.datetime.utcfromtimestamp(min(e,now)/1000):%Y-%m-%dT%H:%M:%SZ}",min_interval=0.15)
        if isinstance(r,list) and r:
            ts=min(k[0] for k in r)*1000
            if ts < START: existed=True; break
            first=ts if first is None else min(first,ts)
            break
    if not existed and first: out.append((p['base_currency'],p['id'],first))
with open('raw/coinbase_new_products.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['symbol','product_id','first_day_ms']); w.writerows(out)
print(len(out))
