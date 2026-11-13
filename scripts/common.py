import json, os, time, hashlib, threading
import requests
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
CACHE=os.path.join(os.path.dirname(__file__),'..','raw','cache')
os.makedirs(CACHE,exist_ok=True)
_last={}; _lock=threading.Lock(); _tl=threading.local()
def _sess():
    s=getattr(_tl,'s',None)
    if s is None:
        s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"application/json"})
        a=requests.adapters.HTTPAdapter(pool_connections=20,pool_maxsize=20); s.mount('https://',a); _tl.s=s
    return s
def _wait(hk,min_interval):
    while True:
        with _lock:
            now=time.time(); t=_last.get(hk,0)
            if now-t>=min_interval: _last[hk]=now; return
            dt=min_interval-(now-t)
        time.sleep(dt)
def get(url, min_interval=0.12, cache=True, retries=4, host_key=None):
    fn=os.path.join(CACHE,hashlib.sha1(url.encode()).hexdigest()+'.json')
    if cache and os.path.exists(fn):
        try: return json.load(open(fn))
        except Exception: pass
    hk=host_key or url.split('/')[2]
    for a in range(retries):
        _wait(hk,min_interval)
        try:
            r=_sess().get(url,timeout=20)
            if r.status_code in (429,418,500,502,503,504): time.sleep(2*(a+1)); continue
            if r.status_code in (400,404):
                d={"_error":r.status_code}
                if cache: json.dump(d,open(fn,'w'))
                return d
            d=r.json()
            if cache: json.dump(d,open(fn,'w'))
            return d
        except Exception:
            time.sleep(1+a)
    return {"_error":"failed"}
