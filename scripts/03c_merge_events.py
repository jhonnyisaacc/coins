"""Merge historical events + Coinbase-derived + CoinSentry alerts into raw/events_all.csv."""
import csv
rows=list(csv.DictReader(open('raw/events_base.csv')))
for r in csv.DictReader(open('raw/coinbase_new_products.csv')):
    rows.append(dict(event_id='',exchange='Coinbase',symbol=r['symbol'],product='spot',quote='USD',markets='USD',ann_ms=r['first_day_ms'],
        ann_source='coinbase_first_daily_candle(no announcement time)',title='',url='',source='historical'))
have={(r['exchange'],r['symbol']) for r in rows}
# CoinSentry: earliest record per exchange+symbol (announced preferred), excluding tests/delistings
cs={}
for a in csv.DictReader(open('raw/coinsentry_alerts.csv')):
    if a['service']!='coinsentry' or a['event'] not in ('listing_announced','listing_live') or a['exchange'] in ('test-exchange',None,''): continue
    k=(a['exchange'],a['symbol'])
    if k not in cs or int(a['detected_ms'])<int(cs[k]['detected_ms']): cs[k]=a
for k,a in cs.items():
    if k in have: continue
    rows.append(dict(event_id='',exchange=a['exchange'],symbol=a['symbol'],product='spot',quote=(a['pairs'].split('|')[0].split('-')[-1] if a['pairs'] else 'USDT'),
        markets=a['pairs'],ann_ms=a['detected_ms'],ann_source='coinsentry_'+a['event'],title='',url=a['source_url'] or '',source='coinsentry'))
for i,r in enumerate(rows):
    if not r['event_id']: r['event_id']=f"X{i:04d}"
with open('raw/events_all.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import collections; print(len(rows),collections.Counter((r['exchange'],r['source']) for r in rows))
