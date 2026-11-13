"""Build the historical listing-event table (one row per exchange+symbol listing) from public sources.
Output raw/events_base.csv. Columns: event_id, exchange, symbol, product(spot|perp), quote, ann_ms, ann_source, title, url, source."""
import json, re, csv, sys, datetime as dt
sys.path.insert(0,'scripts')
START=int(dt.datetime(2025,11,1,tzinfo=dt.timezone.utc).timestamp()*1000)
rows=[]
def add(**k): rows.append(k)
iso=lambda s: int(dt.datetime.fromisoformat(s).timestamp()*1000)
# ---- Upbit (official notices)
for n in json.load(open('raw/upbit_notices.json')):
    t=n['title']; ms=iso(n['first_listed_at'])
    if ms<START: continue
    if not ('신규 거래지원' in t or '디지털 자산 추가' in t): continue
    head=t.split(' (거래지원 개시')[0]
    markets=[m for m in ('KRW','BTC','USDT') if re.search(m+r'[ ,)]',t.split('신규')[0] if '마켓 신규' in t else t)]
    if '마켓 신규' in t:      # "BTC, USDT 마켓 신규 거래지원 안내 (A, B, C)"
        syms=re.findall(r'[A-Z0-9]+',re.search(r'안내 \(([^)]*)\)',t).group(1))
    else:
        syms=re.findall(r'\(([A-Z0-9]+)\)',t.split('신규')[0].split('KRW')[0])
    cancelled=re.findall(r'\(([A-Z0-9]+)\) 거래지원 취소',t)
    for s in syms:
        if s in cancelled: continue
        add(exchange='Upbit',symbol=s,product='spot',quote='KRW' if 'KRW' in markets else ('USDT' if 'USDT' in markets else 'BTC'),
            markets='/'.join(markets),ann_ms=ms,ann_source='upbit_notice',title=t,url=f"https://upbit.com/service_center/notice?id={n['id']}",source='historical')
# ---- Bithumb (CryptoListing.ws public archive, detection time of the official notice)
for e in json.load(open('raw/clw_recent_announcements.json'))['events']:
    if e['cex']=='bithumb' and e['type']=='spot_listing' and e['detected_at_us']//1000>=START:
        for s in e['ticker'].split(','):
            add(exchange='Bithumb',symbol=s.strip(),product='spot',quote='KRW',markets='KRW',ann_ms=e['detected_at_us']//1000,
                ann_source='clw_public_feed',title='',url='',source='historical')
# ---- Binance (official CMS catalog 48)
for a in json.load(open('raw/binance_announcements.json')):
    t=a['title']; ms=int(a['releaseDate'])
    if ms<START: continue
    m=re.match(r'Binance Will List (.+)',t)
    if m and 'RWUSD' not in t:
        for s in re.findall(r'\(([^)]+)\)',m.group(1)):
            if 'Seed Tag' in s or s.isdigit(): continue
            add(exchange='Binance',symbol=s,product='spot',quote='USDT',markets='USDT',ann_ms=ms,ann_source='binance_cms',title=t,
                url=f"https://www.binance.com/en/support/announcement/{a['code']}",source='historical')
    m=re.match(r'Binance Futures Will Launch (?:USDⓈ-Margined )?(.+?) (?:USDⓈ-Margined )?Perpetual Contracts?',t)
    if m and 'TradFi' not in t and 'Multiple' not in t and 'Pre-IPO' not in t and 'Quanto' not in t:
        for s in re.findall(r'([A-Z0-9]{2,15})USDT\b',m.group(1)):
            add(exchange='Binance',symbol=s,product='perp',quote='USDT',markets='USDT-M',ann_ms=ms,ann_source='binance_cms',title=t,
                url=f"https://www.binance.com/en/support/announcement/{a['code']}",source='historical')
# ---- OKX (official announcements API) — spot only
for a in json.load(open('raw/okx_announcements.json')):
    t=a['title']; ms=int(a['pTime'])
    if ms<START or 'spot trading' not in t.lower() or 'pre-market' in t.lower(): continue
    syms=set(re.findall(r'\b([A-Za-z0-9]{2,15})/USD[TⓈC]',t)) or set(re.findall(r'list ([A-Z0-9]{2,15}) ',t))
    for s in syms:
        add(exchange='OKX',symbol=s.upper(),product='spot',quote='USDT',markets='USDT',ann_ms=ms,ann_source='okx_api',title=t,url=a['url'],source='historical')
# ---- Bybit (official announcements API) — spot only
for a in json.load(open('raw/bybit_announcements.json')):
    t=a['title']; ms=int(a['publishTime'])
    if ms<START or 'Spot Listings' not in a['tags']: continue
    if 'Convert' in t or 'Launchpool' in t or 'Pre-Market' in t: continue
    m=re.search(r'List .*?\(([A-Z0-9]+)\) on\s+Spot',t) or re.search(r'New [Ll]isting: ([A-Z0-9]+)/USDT',t)
    if m: add(exchange='Bybit',symbol=m.group(1),product='spot',quote='USDT',markets='USDT',ann_ms=ms,ann_source='bybit_api',title=t,url=a['url'],source='historical')
# dedupe exchange+symbol+product keep earliest
seen={}
for r in sorted(rows,key=lambda r:r['ann_ms']):
    k=(r['exchange'],r['symbol'],r['product'])
    if k not in seen: seen[k]=r
rows=list(seen.values())
for i,r in enumerate(sorted(rows,key=lambda r:r['ann_ms'])): r['event_id']=f"H{i+1:04d}"
cols=['event_id','exchange','symbol','product','quote','markets','ann_ms','ann_source','title','url','source']
with open('raw/events_base.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); [w.writerow({c:r.get(c,'') for c in cols}) for r in sorted(rows,key=lambda r:r['ann_ms'])]
import collections; print(len(rows), collections.Counter((r['exchange'],r['product']) for r in rows))
