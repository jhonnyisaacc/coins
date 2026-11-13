"""v2: every Upbit trade-category notice (all pages) -> raw/upbit_notices_all.json."""
import sys,json; sys.path.insert(0,'scripts'); from common import get
out=[]; p=1
while True:
    d=get(f"https://api-manager.upbit.com/api/v1/announcements?os=web&page={p}&per_page=20&category=trade",cache=False,min_interval=0.3)
    ns=(d.get('data') or {}).get('notices') or []
    if not ns: break
    out+=ns; p+=1
json.dump(out,open('raw/upbit_notices_all.json','w'),ensure_ascii=False)
print(len(out),out[-1]['first_listed_at'] if out else None)
