import sys,json; sys.path.insert(0,'scripts'); from common import get
out=[]
for p in range(1,45):
    d=get(f"https://api-manager.upbit.com/api/v1/announcements?os=web&page={p}&per_page=20&category=trade",cache=False,min_interval=0.3)
    ns=d.get('data',{}).get('notices',[])
    if not ns: break
    out+=ns
    if ns[-1]['first_listed_at']<'2025-04-01': break
json.dump(out,open('raw/upbit_notices.json','w'),ensure_ascii=False)
print(len(out))
