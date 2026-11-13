"""v2 Upbit listing events 2024-01-01..2025-10-31 from raw/upbit_notices_all.json -> raw/v2_upbit_events.csv.
One row per (symbol, market_type): KRW if the notice opens a KRW market, else USDT (BTC/USDT-only), matching v1 market_type."""
import json, re, csv, datetime as dt
S,E='2024-01-01','2025-10-31'
TK=r'[A-Z0-9]{1,12}'
def markets_in(s): return [m for m in ('KRW','BTC','USDT') if re.search(rf'\b{m}\b',s)]
def parse(t):
    if not re.search(r'신규 거래지원|디지털 자산 추가|마켓 추가 안내',t): return []
    head=re.split(r' \((?:거래지원 개시|매도|매수|명칭|주문|업비트|유통량|가상자산|출금|SWELL|AKT|POKT)',t)[0]
    out=[]
    m=re.match(rf'^((?:KRW|BTC|USDT)(?:, (?:KRW|BTC|USDT))*) 마켓 디지털 자산 추가 \(([^)]*)\)',head)
    if m: return [(s,markets_in(m.group(1))) for s in re.findall(TK,m.group(2))]
    m=re.search(r'신규 거래지원 안내 \(([^)]*)\)$',head)
    if m and not re.search(r'마켓',m.group(1)):
        mk=markets_in(head.split('신규')[0]); return [(s,mk) for s in re.findall(TK,m.group(1))]
    per=re.findall(rf'\(({TK})\)\(([^)]*마켓)\)',head)
    if per: return [(a,markets_in(b)) for a,b in per]
    for seg in re.split(r'(?<=마켓)\s*,\s*',head):
        segm=markets_in(re.sub(r'\([^)]*[가-힣][^)]*\)','',seg)) or markets_in(head)
        syms=re.findall(rf'[가-힣A-Za-z0-9 ]*\(({TK})\)',seg)+re.findall(rf'(?:^|, )({TK})\([가-힣]',seg)
        for s in syms: out.append((s,segm))
    return out
rows=[]
for n in json.load(open('raw/upbit_notices_all.json')):
    if not (S<=n['first_listed_at'][:10]<=E): continue
    t=n['title']
    if '거래지원 종료' in t or '유의' in t: continue
    for s,mk in parse(t):
        if s in ('KRW','BTC','USDT') and s!='USDT': continue
        if s=='USDT':
            if 'KRW, BTC 마켓 추가' not in t: continue
            mk=['KRW','BTC']
        ms=int(dt.datetime.fromisoformat(n['first_listed_at']).timestamp()*1000)
        rows.append(dict(exchange='Upbit',symbol=s,product='spot',quote='KRW' if 'KRW' in mk else ('USDT' if 'USDT' in mk else 'BTC'),
            markets='/'.join(mk),market_type='KRW' if 'KRW' in mk else 'USDT',ann_ms=ms,ann_source='upbit_notice',title=t,
            url=f"https://upbit.com/service_center/notice?id={n['id']}",notice_id=n['id'],source='historical'))
seen={}
for r in sorted(rows,key=lambda r:r['ann_ms']):
    k=(r['symbol'],r['market_type'],r['notice_id'])
    if k not in seen: seen[k]=r
rows=sorted(seen.values(),key=lambda r:r['ann_ms'])
with open('raw/v2_upbit_events.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows)); import collections; print(collections.Counter(r['market_type'] for r in rows))
