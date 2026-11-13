"""Fetch raw announcement lists from Binance (catalog 48), OKX (new listings), Bybit (new_crypto)."""
import sys,json,time; sys.path.insert(0,'scripts'); from common import get
CUT=1763000000000  # ~2025-11-13
which=sys.argv[1]
out=[]
if which=='binance':
    for p in range(1,200):
        d=get(f"https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo={p}&pageSize=50",cache=False,min_interval=0.5)
        arts=d['data']['catalogs'][0]['articles']
        if not arts: break
        out+=arts
        if arts[-1]['releaseDate']<CUT-30*864e5: break
elif which=='okx':
    for p in range(1,400):
        d=get(f"https://www.okx.com/api/v5/support/announcements?annType=announcements-new-listings&page={p}",cache=False,min_interval=0.4)
        try: det=d['data'][0]['details']
        except Exception: print('err',d); break
        if not det: break
        out+=det
        if int(det[-1]['pTime'])<CUT-30*864e5: break
elif which=='bybit':
    for p in range(1,400):
        d=get(f"https://api.bybit.com/v5/announcements/index?locale=en-US&type=new_crypto&limit=50&page={p}",cache=False,min_interval=0.3)
        L=d.get('result',{}).get('list',[])
        if not L: break
        out+=L
        if L[-1].get('publishTime',L[-1].get('dateTimestamp'))<CUT-30*864e5: break
json.dump(out,open(f'raw/{which}_announcements.json','w'),ensure_ascii=False)
print(which,len(out))
