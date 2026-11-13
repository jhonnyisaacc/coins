"""v2 non-Korean events (Jan 2024 .. today) -> raw/v2_other_events.csv
Binance spot: 'Binance Will List' (v1 rule) plus 'Introducing X on Binance HODLer Airdrops / Launchpool / Megadrop' posts,
  kept only when a Binance USD-M perp traded in the 3 h before the announcement; earliest post per symbol; symbols already
  in v1 events as Binance spot are skipped.
Coinbase: official Coinbase Exchange status page incidents '<X>-USD Markets Open'; announcement = first update
  ('Coinbase will add support for ...'), trading open = the 'full-trading mode' update."""
import sys, re, json, datetime as dt, pandas as pd
sys.path.insert(0,'scripts'); from candles import candles, HOUR
START=1704067200000
v1=pd.read_parquet('raw/v1/events.parquet')
rows=[]
have_bn=set(v1[(v1.exchange=='Binance')&(v1.market_type=='spot')].symbol)
cands=[]
for a in json.load(open('raw/binance_announcements_all.json')):
    t=a['title']; ms=int(a['releaseDate'])
    if ms<START: continue
    url=f"https://www.binance.com/en/support/announcement/{a['code']}"
    m=re.match(r'Binance Will List (.+)',t)
    if m and 'RWUSD' not in t and 'bStocks' not in t:
        for s in re.findall(r'\(([^)]+)\)',m.group(1)):
            if 'Seed Tag' in s or s.isdigit(): continue
            cands.append((s,ms,'binance_cms',t,url))
    m=re.match(r'Introducing .*?\(([A-Z0-9]+)\) on Binance (HODLer Airdrops|Launchpool|Megadrop)',t)
    if m: cands.append((m.group(1),ms,'binance_cms_'+m.group(2).lower().replace(' ','_'),t,url))
first={}
for s,ms,src,t,url in sorted(cands,key=lambda x:x[1]):
    if s not in first: first[s]=(s,ms,src,t,url)
for s,ms,src,t,url in first.values():
    if s in have_bn: continue
    perp=len(candles('binance_perp',s+'USDT',ms-3*HOUR,ms))>0
    rows.append(dict(exchange='Binance',symbol=s,product='spot',quote='USDT',markets='USDT',market_type='spot',ann_ms=ms,ann_source=src,
        title=t,url=url,source='historical',binance_perp_at_ann=perp))
inc=json.load(open('raw/coinbase_status_incidents.json'))
iso=lambda s:int(dt.datetime.fromisoformat(s).timestamp()*1000)
have_cb=v1[v1.exchange=='Coinbase']
fulls={}
for i in inc:
    m=re.match(r'^(.+?) (?:Moved|Markets) to Full Trading',i.get('name',''))
    if m and i.get('incident_updates'):
        for sym in re.findall(r'([A-Z0-9]+)-USD\b',m.group(1)): fulls.setdefault(sym,[]).append(iso(min(u['created_at'] for u in i['incident_updates'])))
for i in inc:
    name=i.get('name','')
    m=re.match(r'^(.+?) Markets? Open$',name)
    if not m or not i.get('incident_updates'): continue
    toks=[t for t in re.split(r'[ ,]+|\band\b',m.group(1)) if t]
    if any('-' in t and not t.endswith('-USD') for t in toks): continue
    syms=[t.replace('-USD','') for t in toks if re.fullmatch(r'[A-Z0-9]+(-USD)?',t)]
    ups=sorted(i['incident_updates'],key=lambda u:u['created_at'])
    ann=ups[0]; a_ms=iso(ann['created_at'])
    if a_ms<START: continue
    for sym in syms:
        inside=[iso(u['created_at']) for u in ups if re.search(r'full[- ]trading',u['body'],re.I) and (sym in u['body'])]
        later=[t for t in fulls.get(sym,[]) if 0<=t-a_ms<=30*86400000]
        ft=min(inside+later) if inside+later else None
        rows.append(dict(exchange='Coinbase',symbol=sym,product='spot',quote='USD',markets='USD',market_type='spot',ann_ms=a_ms,
            ann_source='coinbase_exchange_status_first_update',title=name+' | '+ann['body'][:300],url=i.get('shortlink') or f"https://status.exchange.coinbase.com/incidents/{i['code']}",
            source='historical',coinbase_full_trading_ms=ft))
df=pd.DataFrame(rows).sort_values('ann_ms')
df=df.drop_duplicates(['exchange','symbol','ann_ms']).reset_index(drop=True)
prev={}; keep=[]
for r in df.itertuples():
    k=(r.exchange,r.symbol); keep.append(not (k in prev and r.ann_ms-prev[k]<=30*86400000))
    if keep[-1]: prev[k]=r.ann_ms
df=df[keep].reset_index(drop=True)
cb1=v1[v1.exchange=='Coinbase'][['event_id','symbol','trading_open_ms']]
def match(r):
    if r.exchange!='Coinbase': return None
    c=cb1[(cb1.symbol==r.symbol)&(cb1.trading_open_ms>=r.ann_ms-86400000)&(cb1.trading_open_ms<=r.ann_ms+15*86400000)]
    return c.event_id.iloc[0] if len(c) else None
df['v1_event_id']=df.apply(match,axis=1)
prods={p['id']:p['status'] for p in __import__('requests').get('https://api.exchange.coinbase.com/products',timeout=30).json()}
df.loc[df.exchange=='Coinbase','coinbase_usd_product_status_now']=df[df.exchange=='Coinbase'].symbol.map(lambda s:prods.get(f'{s}-USD','not_listed_now'))
n0=len(pd.read_csv('raw/events_all_v2.csv'))
new=df.v1_event_id.isna()
df.loc[new,'event_id']=[f"V{n0+i+1:04d}" for i in range(new.sum())]
df.loc[~new,'event_id']=df.loc[~new,'v1_event_id']
df.to_csv('raw/v2_other_events.csv',index=False)
print(df.groupby(['exchange',df.v1_event_id.notna()]).size(), df.coinbase_usd_product_status_now.value_counts(), df[df.exchange=='Binance'].binance_perp_at_ann.value_counts())
