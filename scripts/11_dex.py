"""DEX data for every Korean event (v1 + v2) -> extra/v2/dex_pool_status.parquet, extra/v2/dex_candles.parquet.
Contract: CoinGecko coin_id taken from CoinGecko's own Upbit/Bithumb ticker list (exchange-anchored, no ticker search), then
  /coins/{id}.platforms for solana, base, binance-smart-chain, ethereum.
Pool: GeckoTerminal token pools; the deepest pool created before the announcement by CURRENT reserve_in_usd (historical
  liquidity is not served by the free API, so liquidity_usd_at_ann stays empty).
Swaps: GeckoTerminal serves trades for the last 24 h only, so per-swap history is not available; the finest candles
  (1 minute, USD) are stored for events inside the free API's 180-day OHLCV window."""
import sys, os, json, time, hashlib, datetime as dt, pandas as pd, requests
OUT='extra/v2'; os.makedirs(OUT,exist_ok=True); CACHE='raw/dex_cache'; os.makedirs(CACHE,exist_ok=True)
NOW=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
CHAINS={'solana':'solana','base':'base','binance-smart-chain':'bsc','ethereum':'eth'}
S=requests.Session(); S.headers['Accept']='application/json'
_last={}
def get(url,gap,key):
    fn=os.path.join(CACHE,hashlib.sha1(url.encode()).hexdigest()+'.json')
    if os.path.exists(fn): return json.load(open(fn))
    for a in range(8):
        w=gap-(time.time()-_last.get(key,0))
        if w>0: time.sleep(w)
        _last[key]=time.time()
        try: r=S.get(url,timeout=30)
        except Exception: time.sleep(5); continue
        if r.status_code==429: time.sleep(30+15*a); continue
        if r.status_code in (400,401,404): d={'_error':r.status_code,'_body':r.text[:200]}; json.dump(d,open(fn,'w')); return d
        if r.status_code>=500: time.sleep(5); continue
        d=r.json(); json.dump(d,open(fn,'w')); return d
    return {'_error':'failed'}
cg=lambda p: get('https://api.coingecko.com/api/v3/'+p,6.5,'cg')
gt=lambda p: get('https://api.geckoterminal.com/api/v2/'+p,2.2,'gt')

def exchange_map(exid):
    m={}; p=1
    while True:
        d=cg(f'exchanges/{exid}/tickers?page={p}')
        t=d.get('tickers') or []
        if not t: break
        for x in t:
            if x.get('coin_id'): m.setdefault(x['base'],x['coin_id'])
        p+=1
    return m

def iso(s): return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000)

if __name__=='__main__':
    v1=pd.read_parquet('raw/v1/events.parquet'); v1=v1[v1.exchange.isin(['Upbit','Bithumb'])].assign(collection_batch='v1')
    v2=pd.read_csv('raw/events_all_v2.csv').rename(columns={'ann_ms':'announcement_ms'}).assign(collection_batch='v2')
    K=pd.concat([x[['event_id','exchange','symbol','announcement_ms','collection_batch']] for x in (v1,v2)],ignore_index=True)
    maps={'Upbit':exchange_map('upbit'),'Bithumb':exchange_map('bithumb')}
    print('tickers',{k:len(v) for k,v in maps.items()},flush=True)
    status=[]; candles=[]
    for i,r in enumerate(K.itertuples()):
        a=int(r.announcement_ms)
        base=dict(event_id=r.event_id,exchange=r.exchange,symbol=r.symbol,announcement_ms=a,collection_batch=r.collection_batch)
        cid=maps[r.exchange].get(r.symbol) or maps['Upbit' if r.exchange=='Bithumb' else 'Bithumb'].get(r.symbol)
        if not cid:
            status.append(dict(base,coingecko_id=None,note='symbol not in CoinGecko Upbit/Bithumb ticker lists today (delisted or unmapped); contract not resolved')); continue
        plat=(cg(f'coins/{cid}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false').get('platforms')) or {}
        found=False
        for cgchain,net in CHAINS.items():
            addr=plat.get(cgchain)
            if not addr: continue
            found=True
            o=dict(base,coingecko_id=cid,chain=net,token_address=addr,contract_source='coingecko_coins_platforms(via coingecko exchange tickers)')
            d=gt(f'networks/{net}/tokens/{addr}/pools?page=1')
            pools=[p for p in (d.get('data') or []) if p['attributes'].get('pool_created_at') and iso(p['attributes']['pool_created_at'])<=a]
            if not pools:
                o['note']='no GeckoTerminal pool created before the announcement' if d.get('data') is not None else f"geckoterminal error {d.get('_error')}"
                status.append(o); continue
            p=max(pools,key=lambda p:float(p['attributes'].get('reserve_in_usd') or 0)); at=p['attributes']
            o.update(pool_address=at['address'],dex=p['relationships']['dex']['data']['id'],pool_name=at['name'],pool_created_ms=iso(at['pool_created_at']),
                liquidity_usd_now=float(at.get('reserve_in_usd') or 0),liquidity_usd_at_ann=None,pool_selection='max current reserve_in_usd among pools created before announcement',
                n_candidate_pools=len(pools))
            if a-60000 >= NOW-180*86400000:
                q=f"networks/{net}/pools/{at['address']}/ohlcv/minute?aggregate=1&before_timestamp={(a+11*60000)//1000}&limit=20&currency=usd"
                c=(gt(q).get('data') or {}).get('attributes',{}).get('ohlcv_list') or []
                c=[x for x in c if a-120000 <= x[0]*1000 <= a+600000]
                candles+=[dict(event_id=r.event_id,chain=net,pool_address=at['address'],interval='1m',timestamp_ms=x[0]*1000,open=x[1],high=x[2],low=x[3],close=x[4],volume_usd=x[5]) for x in c]
                o['dex_candle_rows']=len(c)
            else:
                o['dex_candle_rows']=0; o['note']='announcement older than the 180-day GeckoTerminal public OHLCV window; per-swap and candle history not available'
            status.append(o)
        if not found: status.append(dict(base,coingecko_id=cid,note='no contract on solana/base/bsc/ethereum in CoinGecko platforms'))
        if i%20==0: print(i,len(K),flush=True)
    pd.DataFrame(status).to_parquet(f'{OUT}/dex_pool_status.parquet',index=False)
    pd.DataFrame(candles).to_parquet(f'{OUT}/dex_candles.parquet',index=False)
    print('done',len(status),len(candles))
