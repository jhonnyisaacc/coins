"""Fetch CoinSentry alert records from the Worker /read endpoint (private Worker URL and read token come from env vars; never published)
and write a sanitized CSV (no paths/headers). Usage: python3 01_extract_alerts.py"""
import json, csv, os, urllib.request
BASE=os.environ["WORKER_BASE_URL"]  # private; not published
tok=os.environ['WORKER_READ_TOKEN']  # private; not published
req=urllib.request.Request(f"{BASE}/read?since=0&limit=500",headers={"Authorization":f"Bearer {tok}","User-Agent":"listing-study/1.0"})
recs=json.load(urllib.request.urlopen(req,timeout=30))['records']
rows=[]
for r in recs:
    try: b=json.loads(r['body'] or '{}')
    except Exception: b={}
    L=b.get('listing') or {}
    rows.append(dict(id=r['id'],service=r['service'],recv_ms=r['recv_ms'],event=b.get('event'),
        exchange=L.get('exchange'),symbol=L.get('baseAssetSymbol'),pairs='|'.join(L.get('pairSymbols') or []),
        detected_ms=L.get('detectedAtMs'),trading_starts_ms=L.get('tradingStartsAtMs')))
os.makedirs('raw',exist_ok=True)
with open('raw/coinsentry_alerts.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
