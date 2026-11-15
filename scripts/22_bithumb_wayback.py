"""Bithumb 2024-2025 listing notices from Wayback Machine captures of feed.bithumb.com/notice pages.
Step 1 pages the CDX API month by month (cached in raw/wayback/cdx.json) (with retries; the CDX server often answers 504). Step 2 fetches each distinct capture
(id_ raw mode, one request every 4 s with a descriptive User-Agent (Wayback answers 429 to the default python-requests agent), list pages first, then one capture per notice id; captures under 3 kB compressed (the block page is about 2.2 kB) are Bithumb's bot-block page and are skipped). Step 3 reads every notice object (title, categoryName1, publicationDateTime in KST) from the page's __NEXT_DATA__ JSON and keeps the market-addition notices
('마켓 추가') and their published time from the page itself.
Output: raw/wayback/cdx.json, extra/v3/bithumb_wayback_notices.parquet, extra/v3/bithumb_wayback_status.json."""
import os, re, json, time, datetime as dt, requests, pandas as pd
OUT='extra/v3'; W='raw/wayback'; os.makedirs(W,exist_ok=True)
S=requests.Session(); S.headers['User-Agent']='dataset-research-script/1.0'
def get(url,tries=6):
    for a in range(tries):
        try:
            r=S.get(url,timeout=90)
            if r.status_code==200: return r
            if r.status_code==429: time.sleep(60); continue
            if r.status_code in (502,503,504): time.sleep(5+10*a); continue
            return r
        except Exception: time.sleep(5+10*a)
    return None
if os.path.exists(f'{W}/cdx.json'): cdx=json.load(open(f'{W}/cdx.json')); months=[]
else: cdx=[]; months=[(y,mo) for y in (2024,2025) for mo in range(1,13)]+[(2026,mo) for mo in range(1,12)]
failed_months=[]
for y,mo in months:
    a=f'{y}{mo:02d}'; b=f'{y+(mo==12)}{(mo%12)+1:02d}'
    r=get(f'https://web.archive.org/cdx/search/cdx?url=feed.bithumb.com/notice&matchType=prefix&from={a}01&to={b}01&output=json&fl=original,timestamp,statuscode,length,digest')
    if r is None or r.status_code!=200 or not r.text.startswith('['): failed_months.append(a); continue
    cdx+=[dict(zip(['original','timestamp','statuscode','length','digest'],x)) for x in r.json()[1:]]
if months: json.dump(cdx,open(f'{W}/cdx.json','w'))
from concurrent.futures import ThreadPoolExecutor
ok=[c for c in cdx if c['statuscode']=='200' and c['length'].isdigit() and int(c['length'])>=3000]
lists=[c for c in ok if not re.search(r'/notice/\d+',c['original'])]
best={}
for c in ok:
    m=re.search(r'/notice/(\d+)',c['original'])
    if m and (m.group(1) not in best or int(c['length'])>int(best[m.group(1)]['length'])): best[m.group(1)]=c
todo=list({c['digest']:c for c in lists}.values())+sorted(best.values(),key=lambda c:c['timestamp'])
def fetch(c):
    fn=f"{W}/{c['digest']}.html"
    if not os.path.exists(fn) or os.path.getsize(fn)==0:
        time.sleep(4); r=get(f"https://web.archive.org/web/{c['timestamp']}id_/{c['original']}",tries=4)
        open(fn,'wb').write(r.content if r is not None and r.status_code==200 else b'')
    return c,open(fn,encoding='utf-8',errors='ignore').read()
got=[fetch(c) for c in todo]
def notices(o):
    if isinstance(o,dict):
        if 'title' in o and 'publicationDateTime' in o: yield o
        for v in o.values(): yield from notices(v)
    elif isinstance(o,list):
        for v in o: yield from notices(v)
rows=[]; blocked=empty=usable=0
for c,h in got:
    if not h: empty+=1; continue
    nd=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',h,re.S)
    if not nd: blocked+=1; continue
    usable+=1
    for n in notices(json.loads(nd.group(1))):
        rows.append(dict(notice_id=n.get('id'),title=n['title'],category=n.get('categoryName1'),published_kst=n['publicationDateTime'],
                         capture_url=c['original'],capture_timestamp=c['timestamp']))
allr=pd.DataFrame(rows).drop_duplicates(['notice_id','title','published_kst']) if rows else pd.DataFrame(columns=['notice_id','title','category','published_kst'])
allr.to_parquet(f'{OUT}/bithumb_wayback_all_notices.parquet',index=False)
lst=allr[allr.title.str.contains('마켓 추가')&~allr.title.str.contains('종료|유의|연기|취소')] if len(allr) else allr
st=dict(cdx_rows=len(cdx),cdx_200_not_block_sized=len(ok),list_pages=len(lists),notice_ids=len(best),fetched=len(got),empty_fetch=empty,
        no_next_data=blocked,usable_pages=usable,distinct_notices=len(allr),listing_notices=len(lst),failed_months=failed_months,
        published_kst_min=str(allr.published_kst.min()) if len(allr) else None,published_kst_max=str(allr.published_kst.max()) if len(allr) else None)
json.dump(st,open(f'{OUT}/bithumb_wayback_status.json','w'),indent=1,ensure_ascii=False); print(st)
lst.to_parquet(f'{OUT}/bithumb_wayback_notices.parquet',index=False)
