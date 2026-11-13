"""Poll the Upbit notices API several times per second and append each NEW notice to data/upbit_poll_log.csv with the time we
first saw it (local clock, UTC ms) and the notice's own timestamps. Notices present at startup are recorded as seen, not new.
Usage: python3 scripts/12_upbit_poll.py --region "<where this runs>" [--interval 0.3]"""
import argparse, csv, os, time, datetime as dt, requests
ap=argparse.ArgumentParser(); ap.add_argument('--region',required=True); ap.add_argument('--interval',type=float,default=0.3)
ap.add_argument('--out',default='data/upbit_poll_log.csv'); A=ap.parse_args()
URL='https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=all'
COLS=['notice_id','title','category','first_seen_ms','notice_first_listed_ms','notice_listed_ms','seen_minus_first_listed_ms',
      'poll_interval_s','http_elapsed_ms','region']
S=requests.Session(); S.headers.update({'Accept':'application/json','User-Agent':'listing-study-poller/1.0'})
iso=lambda s:int(dt.datetime.fromisoformat(s).timestamp()*1000) if s else None
now=lambda:int(time.time()*1000)
def fetch():
    t0=time.time(); r=S.get(URL,timeout=5); el=int((time.time()-t0)*1000)
    if r.status_code==429: return None,el,429
    r.raise_for_status(); return r.json()['data']['notices'],el,200
seen=set()
if os.path.exists(A.out):
    seen|={int(r['notice_id']) for r in csv.DictReader(open(A.out))}
else:
    with open(A.out,'w',newline='') as f: csv.writer(f).writerow(COLS)
while True:
    try:
        ns,_,_=fetch()
        if ns is not None: seen|={n['id'] for n in ns}; break
    except Exception: pass
    time.sleep(2)
print('seeded',len(seen),flush=True)
back=A.interval
while True:
    t=time.time()
    try:
        ns,el,code=fetch()
        if code==429: back=min(back*2,10); print('429, backing off',back,flush=True)
        else:
            back=A.interval; ts=now()
            new=[n for n in ns if n['id'] not in seen]
            if new:
                with open(A.out,'a',newline='') as f:
                    w=csv.writer(f)
                    for n in new:
                        fl=iso(n.get('first_listed_at'))
                        w.writerow([n['id'],n['title'],n.get('category'),ts,fl,iso(n.get('listed_at')),ts-fl if fl else None,
                                    A.interval,el,A.region])
                        seen.add(n['id']); print('NEW',n['id'],n['title'],ts-(fl or ts),'ms',flush=True)
    except Exception as e:
        print('err',repr(e)[:100],flush=True); back=min(back*2,10)
    time.sleep(max(0,back-(time.time()-t)))
