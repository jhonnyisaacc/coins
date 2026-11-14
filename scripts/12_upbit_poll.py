"""Poll the Upbit notices API and append each NEW notice to data/upbit_poll_log.csv with the time we first saw it
(local clock, UTC ms) and the notice's own timestamps. Notices present at startup count as seen, not new.
On a listing notice it also records Binance round trips and starts an order-book capture (see poll_common.py).
Usage: python3 scripts/12_upbit_poll.py --region "<where this runs>" [--interval 0.5]"""
import argparse, re, sys, time, datetime as dt, os
sys.path.insert(0,os.path.dirname(__file__)); import poll_common as P
ap=argparse.ArgumentParser(); ap.add_argument('--region',required=True); ap.add_argument('--interval',type=float,default=0.5)
ap.add_argument('--out',default='data/upbit_poll_log.csv'); A=ap.parse_args()
URL='https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=all'
COLS=['notice_id','title','category','first_seen_ms','notice_first_listed_ms','notice_listed_ms','seen_minus_first_listed_ms',
      'poll_interval_s','http_elapsed_ms','region','is_listing','symbols','forward_event_id','binance_spot_time_rtt_ms',
      'binance_fapi_time_rtt_ms','test_order_status','book_capture_event_id']
iso=lambda s:int(dt.datetime.fromisoformat(s).timestamp()*1000) if s else None
def fetch():
    t0=time.time(); r=P.S.get(URL,timeout=5); el=int((time.time()-t0)*1000); r.raise_for_status()
    return r.json()['data']['notices'],el
def is_listing(n): return bool(re.search(r'신규 거래지원|디지털 자산 추가|마켓 추가',n['title'])) and '종료' not in n['title']
def symbols_of(n):
    s=re.findall(r'\(([A-Z0-9]{1,12})\)',n['title'])
    m=re.search(r'디지털 자산 추가 \(([^)]*)\)',n['title'])
    if m: s+=re.findall(r'[A-Z0-9]{1,12}',m.group(1))
    return [x for x in dict.fromkeys(re.sub(r'(?<=[A-Z])2$','',x) for x in s) if x not in ('KRW','BTC','USDT')]
def to_row(n,ts,el):
    fl=iso(n.get('first_listed_at'))
    return dict(notice_id=n['id'],title=n['title'],category=n.get('category'),first_seen_ms=ts,notice_first_listed_ms=fl,
                notice_listed_ms=iso(n.get('listed_at')),seen_minus_first_listed_ms=ts-fl if fl else None,forward_event_id=f"FU{n['id']}")
P.run('upbit',fetch,lambda n:n['id'],to_row,is_listing,symbols_of,A.out,COLS,A.interval,A.region)
