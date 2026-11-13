"""Coinbase Exchange status page (official): every '<X>-USD Markets Open' style incident since 2024-01 with all updates -> raw/coinbase_status_incidents.json."""
import sys, json, re; sys.path.insert(0,'scripts'); from common import get
inc=[]; p=1
while True:
    d=get(f"https://status.exchange.coinbase.com/history.json?page={p}",cache=False,min_interval=0.5)
    ms=d.get('months') or []
    if not ms: break
    for mo in ms: inc+= [dict(i,month=mo['name'],year=mo['year']) for i in mo['incidents']]
    if min(mo['year'] for mo in ms)<2024: break
    p+=1
sel=[i for i in inc if re.search(r'market|trading|listing|launch|transfer',i['name'],re.I)]
full=[]
for i in sel:
    x=get(f"https://status.exchange.coinbase.com/incidents/{i["code"]}.json",min_interval=0.4)
    full.append(dict(x,code=i["code"]) if isinstance(x,dict) else {'code':i['code'],'name':i['name']})
json.dump(full,open('raw/coinbase_status_incidents.json','w'))
print(len(inc),len(sel))
