"""Binance CMS catalog 48 (new listings) back to 2024-01-01 -> raw/binance_announcements_all.json."""
import sys, json; sys.path.insert(0,'scripts'); from common import get
CUT=1704067200000
out=[]
for p in range(1,400):
    d=get(f"https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo={p}&pageSize=50",cache=False,min_interval=0.6)
    arts=((d.get('data') or {}).get('catalogs') or [{}])[0].get('articles') or []
    if not arts: break
    out+=arts
    if arts[-1]['releaseDate']<CUT: break
json.dump(out,open('raw/binance_announcements_all.json','w'),ensure_ascii=False)
print(len(out), min(a['releaseDate'] for a in out))
