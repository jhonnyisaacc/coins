"""Shared pieces for the forward-only notice pollers (12_upbit_poll.py, 16_binance_poll.py, 17_bithumb_poll.py):
CSV log with schema migration, timestamped stdout with a heartbeat, Binance round-trip probes, and order-book capture
(REST depth snapshot plus 5 minutes of the depth20@100ms websocket) written to raw/forward/book/."""
import csv, os, json, time, threading, datetime as dt, requests, pandas as pd
BOOK_DIR='raw/forward/book'
TEST_ORDER_STATUS='unavailable: /api/v3/order/test and /fapi/v1/order/test are SIGNED endpoints and need an API key'
S=requests.Session(); S.headers.update({'Accept':'application/json','User-Agent':'listing-study-poller/1.0'})
now=lambda:int(time.time()*1000)

def log(*a):
    print(dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4]+'Z',*a,flush=True)

class CsvLog:
    def __init__(self,path,cols):
        self.path,self.cols=path,cols
        if os.path.exists(path):
            rows=list(csv.DictReader(open(path)))
            head=open(path).readline().strip().split(',')
            if head!=cols:
                with open(path,'w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); [w.writerow({c:r.get(c,'') for c in cols}) for r in rows]
            self.rows=rows
        else:
            with open(path,'w',newline='') as f: csv.writer(f).writerow(cols)
            self.rows=[]
    def append(self,row):
        with open(self.path,'a',newline='') as f: csv.DictWriter(f,fieldnames=self.cols).writerow({c:row.get(c,'') for c in self.cols})

def rtt(url):
    t0=time.time()
    try: S.get(url,timeout=5).raise_for_status(); return int((time.time()-t0)*1000)
    except Exception: return None

def binance_probes():
    return dict(binance_spot_time_rtt_ms=rtt('https://api.binance.com/api/v3/time'),
                binance_fapi_time_rtt_ms=rtt('https://fapi.binance.com/fapi/v1/time'),test_order_status=TEST_ORDER_STATUS)

def _rest_depth(venue,sym):
    url=('https://api.binance.com/api/v3/depth' if venue=='binance_spot' else 'https://fapi.binance.com/fapi/v1/depth')+f'?symbol={sym}&limit=100'
    r=S.get(url,timeout=5); ts=now()
    if r.status_code!=200: return [],f'rest {r.status_code}'
    d=r.json()
    rows=[dict(timestamp_ms=ts,source='rest_depth_limit100',side=s,level=i+1,price=float(p),qty=float(q))
          for s,k in (('bid','bids'),('ask','asks')) for i,(p,q) in enumerate(d[k])]
    return rows,'ok'

def _ws_depth(venue,sym,seconds,rows):
    import websocket
    host='wss://stream.binance.com:9443/ws/' if venue=='binance_spot' else 'wss://fstream.binance.com/ws/'
    end=time.time()+seconds
    def on_msg(ws,m):
        d=json.loads(m); ts=d.get('E') or now()
        for s,k in (('bid','bids' if 'bids' in d else 'b'),('ask','asks' if 'asks' in d else 'a')):
            for i,(p,q) in enumerate(d.get(k,[])): rows.append(dict(timestamp_ms=ts,source='ws_depth20_100ms',side=s,level=i+1,price=float(p),qty=float(q)))
        if time.time()>end: ws.close()
    while time.time()<end:
        ws=websocket.WebSocketApp(host+sym.lower()+'@depth20@100ms',on_message=on_msg)
        ws.run_forever(ping_interval=20,ping_timeout=10)

def capture_books(event_id,symbols,seconds=300):
    """Non-blocking: one thread per Binance spot and USD-M perp market of each symbol."""
    os.makedirs(BOOK_DIR,exist_ok=True)
    def work(venue,sym):
        rest,status=_rest_depth(venue,sym)
        ws=[]
        if status=='ok': _ws_depth(venue,sym,seconds,ws)
        df=pd.DataFrame(rest+ws)
        meta=dict(event_id=event_id,venue=venue,market=sym,rest_status=status,captured_at_ms=now(),rows=len(df))
        if len(df):
            df.insert(0,'event_id',event_id); df.insert(1,'venue',venue); df.insert(2,'market',sym)
            df.to_parquet(f'{BOOK_DIR}/{event_id}_{venue}_{sym}.parquet',index=False)
        json.dump(meta,open(f'{BOOK_DIR}/{event_id}_{venue}_{sym}.json','w'))
        log('book',event_id,venue,sym,status,len(df),'rows')
    for s in symbols:
        for venue in ('binance_spot','binance_perp'):
            threading.Thread(target=work,args=(venue,s+'USDT'),daemon=True).start()

def run(name,fetch,ident,to_row,is_listing,symbols_of,out,cols,interval,region,heartbeat_s=600):
    """fetch() -> list of items; ident(item) -> stable id; to_row(item, first_seen_ms, http_elapsed_ms) -> dict."""
    L=CsvLog(out,cols); seen={str(r[cols[0]]) for r in L.rows}
    while True:
        try: items,_=fetch(); seen|={str(ident(x)) for x in items}; break
        except Exception as e: log('seed error',repr(e)[:120]); time.sleep(5)
    log(name,'seeded',len(seen),'region',region,'interval',interval)
    back=interval; polls=errs=0; hb=time.time()
    while True:
        t=time.time()
        try:
            items,el=fetch(); polls+=1; back=interval; ts=now()
            for x in items:
                k=str(ident(x))
                if k in seen: continue
                seen.add(k); row=to_row(x,ts,el); row.update(poll_interval_s=interval,http_elapsed_ms=el,region=region)
                lst=is_listing(x); row['is_listing']=lst
                if lst:
                    syms=symbols_of(x); row['symbols']='|'.join(syms); row.update(binance_probes())
                    row['book_capture_event_id']=row['forward_event_id'] if syms else ''
                    if syms: capture_books(row['forward_event_id'],syms)
                L.append(row); log('NEW',k,row.get('title','')[:80],'listing' if lst else '')
        except requests.HTTPError as e:
            errs+=1; code=e.response.status_code if e.response is not None else None
            back=min(back*2,30) if code==429 else min(back*2,10); log('http',code,'backoff',back)
        except Exception as e:
            errs+=1; back=min(back*2,10); log('err',repr(e)[:120])
        if time.time()-hb>=heartbeat_s: log('heartbeat polls',polls,'errors',errs); hb=time.time()
        time.sleep(max(0,back-(time.time()-t)))
