"""Poll Binance announcements (CMS catalog 48, new listings) and append each NEW post to data/binance_poll_log.csv with
first_seen_ms next to the post's releaseDate, so the gap between releaseDate and public visibility can be measured.
On a listing post it records Binance round trips and captures order books (see poll_common.py).
Usage: python3 scripts/16_binance_poll.py --region "<where this runs>" [--interval 1.0]"""
import argparse, re, sys, time, os
sys.path.insert(0,os.path.dirname(__file__)); import poll_common as P
ap=argparse.ArgumentParser(); ap.add_argument('--region',required=True); ap.add_argument('--interval',type=float,default=1.0)
ap.add_argument('--out',default='data/binance_poll_log.csv'); A=ap.parse_args()
URL='https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo=1&pageSize=20'
COLS=['code','title','first_seen_ms','release_date_ms','seen_minus_release_ms','poll_interval_s','http_elapsed_ms','region',
      'is_listing','symbols','forward_event_id','binance_spot_time_rtt_ms','binance_fapi_time_rtt_ms','test_order_status','book_capture_event_id']
def fetch():
    t0=time.time(); r=P.S.get(URL,timeout=5); el=int((time.time()-t0)*1000); r.raise_for_status()
    return r.json()['data']['catalogs'][0]['articles'],el
def is_listing(a): return bool(re.match(r'(Binance Will List|Introducing .* on Binance (HODLer|Launchpool|Megadrop)|Binance Futures Will Launch)',a['title']))
def symbols_of(a):
    t=a['title']
    if t.startswith('Binance Futures'): return [s for s in re.findall(r'\b([A-Z0-9]{2,15})USDT\b',t)]
    return [s for s in re.findall(r'\(([A-Z0-9]{2,15})\)',t)]
def to_row(a,ts,el):
    rd=int(a['releaseDate'])
    return dict(code=a['code'],title=a['title'],first_seen_ms=ts,release_date_ms=rd,seen_minus_release_ms=ts-rd,forward_event_id=f"FB{a['code'][:12]}")
P.run('binance',fetch,lambda a:a['code'],to_row,is_listing,symbols_of,A.out,COLS,A.interval,A.region)
