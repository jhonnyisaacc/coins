"""OKX (api/v5/support/announcements, annType announcements-new-listings) and Bybit (v5/announcements/index, type new_crypto)
announcements back to 2024-01-01 -> raw/okx_announcements_v3.json, raw/bybit_announcements_v3.json. Same endpoints as 02b."""
import sys, json; sys.path.insert(0,'scripts'); from common import get
CUT=1704067200000
okx=[]
for p in range(1,1000):
    d=get(f"https://www.okx.com/api/v5/support/announcements?annType=announcements-new-listings&page={p}",cache=False,min_interval=0.4)
    try: det=d['data'][0]['details']
    except Exception: print('okx stop',p,str(d)[:120]); break
    if not det: break
    okx+=det
    if int(det[-1]['pTime'])<CUT: break
json.dump(okx,open('raw/okx_announcements_v3.json','w'),ensure_ascii=False)
by=[]
for p in range(1,1000):
    d=get(f"https://api.bybit.com/v5/announcements/index?locale=en-US&type=new_crypto&limit=50&page={p}",cache=False,min_interval=0.3)
    L=(d.get('result') or {}).get('list') or []
    if not L: break
    by+=L
    if L[-1].get('publishTime',L[-1].get('dateTimestamp'))<CUT: break
json.dump(by,open('raw/bybit_announcements_v3.json','w'),ensure_ascii=False)
print('okx',len(okx),min(int(x['pTime']) for x in okx),'bybit',len(by),min(x.get('publishTime',x.get('dateTimestamp')) for x in by))
