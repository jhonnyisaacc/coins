"""Poll Bithumb's official notices API (feed-api.bithumb.com/v1/notices, latest notices only, so forward-only) and
append each NEW notice to data/bithumb_poll_log.csv with first_seen_ms next to published_at (KST, 1-second precision).
On a market-addition notice it records Binance round trips and captures order books (see poll_common.py).
Usage: python3 scripts/17_bithumb_poll.py --region "<where this runs>" [--interval 1.0]"""
import argparse, re, sys, time, os, datetime as dt
sys.path.insert(0,os.path.dirname(__file__)); import poll_common as P
ap=argparse.ArgumentParser(); ap.add_argument('--region',required=True); ap.add_argument('--interval',type=float,default=1.0)
ap.add_argument('--out',default='data/bithumb_poll_log.csv'); A=ap.parse_args()
URL='https://feed-api.bithumb.com/v1/notices'
KST=dt.timezone(dt.timedelta(hours=9))
COLS=['pc_url','title','categories','first_seen_ms','published_ms','seen_minus_published_ms','poll_interval_s','http_elapsed_ms','region',
      'is_listing','symbols','forward_event_id','binance_spot_time_rtt_ms','binance_fapi_time_rtt_ms','test_order_status','book_capture_event_id']
kst=lambda s:int(dt.datetime.strptime(s,'%Y-%m-%d %H:%M:%S').replace(tzinfo=KST).timestamp()*1000)
def fetch():
    t0=time.time(); r=P.S.get(URL,timeout=5); el=int((time.time()-t0)*1000); r.raise_for_status()
    return r.json(),el
def is_listing(n): return '마켓 추가' in (n.get('categories') or [])
def symbols_of(n): return [s for s in dict.fromkeys(re.findall(r'\(([A-Z0-9]{1,12})\)',n['title'])) if s not in ('KRW','BTC','USDT')]
def to_row(n,ts,el):
    pm=kst(n['published_at'])
    return dict(pc_url=n['pc_url'],title=n['title'],categories='|'.join(n.get('categories') or []),first_seen_ms=ts,published_ms=pm,
                seen_minus_published_ms=ts-pm,forward_event_id='FT'+n['pc_url'].rstrip('/').split('/')[-1])
P.run('bithumb',fetch,lambda n:n['pc_url'],to_row,is_listing,symbols_of,A.out,COLS,A.interval,A.region)
