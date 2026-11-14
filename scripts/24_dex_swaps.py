"""Per-swap DEX trades from 2 minutes before to 10 minutes after the announcement for every pool that has dex_candles, read
from free public JSON-RPC endpoints with eth_getLogs (Ethereum and Base via eth.drpc.org / base.drpc.org, BSC via
bsc.rpc.blxrbdn.com (bloXroute, keeps only a few weeks of BSC history) with bsc.drpc.org for headers, all keyless; drpc's free plan accepts eth_getLogs spans of about 100 blocks, so ranges are chunked). Pool families and Swap events:
  uniswap_v2                       Swap(address,uint256,uint256,uint256,uint256,address)
  aerodrome-base (v2 style)        Swap(address,address,uint256,uint256,uint256,uint256)
  uniswap v3, slipstream           Swap(address,address,int256,int256,uint160,uint128,int24)
  pancakeswap v3                   Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)
  uniswap v4 (PoolManager, topic1 = pool id)          Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)
  pancakeswap infinity CL (CLPoolManager, topic1 = id) Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24,uint16)
Token order is the sorted address pair (all these families sort token0 < token1). The sign convention of singleton managers is
checked per pool against the sqrtPriceX96 move. price = quote per base; amount_usd uses quote_usd (stablecoin = 1, WETH/ETH and
WBNB/BNB = Binance 1m close), else base amount x dex_candles close (usd_source says which).
liquidity_usd_at_ann: token balances of the pool contract at the last block before the announcement (eth_call balanceOf at
that block), valued the same way. Only for per-pool contracts (v2/v3 families); singleton managers hold every pool's tokens.
Solana and Curve pools are logged as not covered.
Output: extra/v3/dex_swaps.parquet, extra/v3/dex_swaps_status.parquet."""
import sys, os, json, glob, time, pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
OUT='extra/v3'; CACHE='raw/rpc'; os.makedirs(CACHE,exist_ok=True)
RPC={'eth':['https://eth.drpc.org'],'base':['https://base.drpc.org','https://mainnet.base.org','https://base-mainnet.public.blastapi.io'],
     'bsc':['https://bsc.rpc.blxrbdn.com','https://bsc.drpc.org','https://bsc-mainnet.public.blastapi.io']}
MANAGER={('eth','uniswap-v4-ethereum'):'0x000000000004444c5dc75cB358380D2e3dE08A90',('base','uniswap-v4-base'):'0x498581fF718922c3f8e6A244956aF099B2652b2b',
         ('bsc','pancakeswap-infinity-clmm'):'0xa0FfB9c1CE1Fe56963B0321B32E7A0302114058b'}
T_V2='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'; T_AERO='0xb3e2773606abfd36b5bd91394b3a54d1398336c65005baf7bf7a05efeffaf75b'
T_V3='0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'; T_PCS3='0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83'
T_V4='0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'; T_INF='0x04206ad2b7c0f463bff3dd4f33c5735b0f2957a351e4f79763a4fa9e775dd237'
def family(chain,dex):
    if (chain,dex) in MANAGER: return 'v4' if 'uniswap' in dex else 'infinity'
    if dex=='uniswap_v2': return 'v2'
    if dex=='aerodrome-base': return 'aero'
    if dex.startswith('pancakeswap-v3'): return 'pcs3'
    if dex.startswith(('uniswap_v3','uniswap-v3','aerodrome-slipstream')): return 'v3'
    return None
TOPIC={'v2':T_V2,'aero':T_AERO,'v3':T_V3,'pcs3':T_PCS3,'v4':T_V4,'infinity':T_INF}
STABLE={'0x55d398326f99059ff775485246999027b3197955','0x833589fcd6edb6e08f4c7c32d4f71b54bda02913','0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7','0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d',
        '0xe9e7cea3dedca5984780bafc599bd69add087d56','0xc5f0f7b66764f6ec8c8dff7ba683102295e16409','0x6b175474e89094c44da98b954eedeac495271d0f'}
ETHLIKE={('eth','0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),('base','0x4200000000000000000000000000000000000006'),('eth','0x0000000000000000000000000000000000000000'),('base','0x0000000000000000000000000000000000000000')}
BNBLIKE={('bsc','0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'),('bsc','0x0000000000000000000000000000000000000000')}
S=requests.Session(); SPAN=100
def rpc(chain,method,params):
    """Try each free endpoint in turn; back off after a full cycle of errors. Returns the result or {'_error': last message}."""
    msg='no response'
    for a in range(6):
        for u in RPC[chain]:
            try:
                r=S.post(u,json={'jsonrpc':'2.0','id':1,'method':method,'params':params},timeout=40).json()
                if 'result' in r and r['result'] is not None: return r['result']
                msg=f"{u}: {r.get('error')}"
            except Exception as e: msg=f'{u}: {e!r}'
        time.sleep(2+4*a)
    return {'_error':msg}
BTS={}
def block_ts(chain,n):
    if (chain,n) not in BTS:
        b=rpc(chain,'eth_getBlockByNumber',[hex(n),False]); BTS[(chain,n)]=int(b['timestamp'],16) if isinstance(b,dict) and 'timestamp' in b else None
    return BTS[(chain,n)]
HEAD={}
def block_at(chain,ts):
    """Last block with timestamp <= ts: interpolation search inside a [lo, hi] bracket (block times change over a chain's life)."""
    if chain not in HEAD: HEAD[chain]=int(rpc(chain,'eth_blockNumber',[]),16)
    lo,hi=1,HEAD[chain]; tlo,thi=block_ts(chain,lo),block_ts(chain,hi)
    if None in (tlo,thi) or not tlo<=ts<thi: return None
    while hi-lo>1:
        g=lo+int((ts-tlo)*(hi-lo)/max(1,thi-tlo)); g=min(max(g,lo+1),hi-1)
        if hi-lo>64: g=min(max(g,lo+(hi-lo)//64),hi-(hi-lo)//64)
        t=block_ts(chain,g)
        if t is None: return None
        if t<=ts: lo,tlo=g,t
        else: hi,thi=g,t
    return lo
def words(data): d=data[2:]; return [int(d[i:i+64],16) for i in range(0,len(d),64)]
def signed(x): return x-(1<<256) if x>=1<<255 else x
DEC={}
def decimals(chain,tok):
    if tok=='0x0000000000000000000000000000000000000000': return 18
    if (chain,tok) not in DEC:
        r=rpc(chain,'eth_call',[{'to':tok,'data':'0x313ce567'},'latest']); DEC[(chain,tok)]=int(r,16) if isinstance(r,str) and len(r)>2 else None
    return DEC[(chain,tok)]
def bal(chain,tok,holder,block):
    r=rpc(chain,'eth_call',[{'to':tok,'data':'0x70a08231'+holder[2:].lower().rjust(64,'0')},hex(block)])
    return int(r,16) if isinstance(r,str) and len(r)>2 else None
KL={}
def binance_close(sym,ms):
    k=(sym,ms//60000)
    if k not in KL:
        d=S.get(f'https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1m&startTime={ms//60000*60000}&limit=1',timeout=20).json()
        KL[k]=float(d[0][4]) if d else None
    return KL[k]
def quote_usd(chain,q,ms):
    if q in STABLE: return 1.0,'stablecoin'
    if (chain,q) in ETHLIKE: return binance_close('ETHUSDT',ms),'binance_ETHUSDT_1m'
    if (chain,q) in BNBLIKE: return binance_close('BNBUSDT',ms),'binance_BNBUSDT_1m'
    return None,None

pools={}
for f in glob.glob('raw/dex_cache/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    for x in (d.get('data') if isinstance(d.get('data'),list) else [d.get('data')]) or []:
        if isinstance(x,dict) and 'quote_token' in x.get('relationships',{}):
            pools[x['attributes']['address'].lower()]=(x['relationships']['base_token']['data']['id'].split('_',1)[1].lower(),x['relationships']['quote_token']['data']['id'].split('_',1)[1].lower())
st=pd.read_parquet('raw/v2pub/dex_pool_status.parquet'); cd=pd.read_parquet('raw/v2pub/dex_candles.parquet')
todo=st.merge(cd[['event_id','chain','pool_address']].drop_duplicates(),on=['event_id','chain','pool_address'])

def one(r):
    o=dict(event_id=r.event_id,chain=r.chain,pool_address=r.pool_address,dex=r.dex,announcement_ms=int(r.announcement_ms))
    fam=family(r.chain,r.dex) if r.chain in RPC else None
    if r.chain=='solana': o['note']='not covered: public Solana RPC has no time-indexed history; paging signatures back to the announcement is not feasible on the free tier'; return o,None
    if fam is None: o['note']=f'not covered: no decoder for {r.dex}'; return o,None
    base,quote=pools[r.pool_address.lower()]; t0,t1=sorted([base,quote]); base_is0=base==t0
    a=int(r.announcement_ms); b0=block_at(r.chain,(a-120000)//1000); b1=block_at(r.chain,(a+600000)//1000); ba=block_at(r.chain,a//1000-1)
    if None in (b0,b1,ba): o['note']='not covered: block lookup failed on every free RPC'; return o,None
    addr=MANAGER.get((r.chain,r.dex),r.pool_address); flt={'fromBlock':hex(b0),'toBlock':hex(b1+1),'address':addr,'topics':[TOPIC[fam]]}
    if fam in ('v4','infinity'): flt['topics'].append(r.pool_address.lower())
    logs=[]
    for c0 in range(b0,b1+2,SPAN):
        part=rpc(r.chain,'eth_getLogs',[dict(flt,fromBlock=hex(c0),toBlock=hex(min(c0+SPAN-1,b1+1)))])
        if isinstance(part,dict): o['note']='not covered: eth_getLogs error '+part['_error'][:120]; return o,None
        logs+=part
    d0,d1=decimals(r.chain,t0),decimals(r.chain,t1)
    if None in (d0,d1): o['note']='not covered: token decimals unavailable'; return o,None
    tss={}
    rows=[]
    for L in logs:
        w=words(L['data']); bn=int(L['blockNumber'],16)
        if fam in ('v2','aero'): p0=w[0]-w[2]; p1=w[1]-w[3]; sq=None
        else:
            p0,p1=signed(w[0]),signed(w[1]); sq=w[2]
            if fam in ('v4','infinity'): p0,p1=-p0,-p1
        if bn not in tss: tss[bn]=block_ts(r.chain,bn)
        rows.append(dict(block=bn,log_index=int(L['logIndex'],16),tx_hash=L['transactionHash'],pool0=p0/10**d0,pool1=p1/10**d1,sqrt_price_x96=sq,ts=tss[bn]))
    o['n_logs']=len(rows)
    if fam in ('v4','infinity','v3','pcs3') and len(rows)>2:
        agree=sum(1 for x,y in zip(rows,rows[1:]) if y['sqrt_price_x96'] and x['sqrt_price_x96'] and y['pool0']!=0 and ((y['pool0']>0)==(y['sqrt_price_x96']<x['sqrt_price_x96'])))
        o['sign_check_agree_share']=agree/max(1,len(rows)-1)
        if o['sign_check_agree_share']<0.5:
            for x in rows: x['pool0'],x['pool1']=-x['pool0'],-x['pool1']
            o['sign_flipped']=True
    qu,qsrc=quote_usd(r.chain,quote,a)
    cmin=cd[(cd.event_id==r.event_id)&(cd.pool_address==r.pool_address)].set_index('timestamp_ms').close
    out=[]
    for x in rows:
        pb,pq=(x['pool0'],x['pool1']) if base_is0 else (x['pool1'],x['pool0'])
        if pb==0 or pq==0: continue
        ms=x['ts']*1000; price=abs(pq/pb)
        if qu is not None: usd=abs(pq)*(binance_close('ETHUSDT' if qsrc.endswith('ETHUSDT_1m') else 'BNBUSDT',ms) if qsrc!='stablecoin' else 1.0); src=qsrc
        else:
            c=cmin.get(ms//60000*60000); usd=abs(pb)*c if c is not None else None; src='base_amount_x_dex_candle_close'
        out.append(dict(event_id=r.event_id,chain=r.chain,pool_address=r.pool_address,timestamp_ms=ms,block=x['block'],log_index=x['log_index'],
                        tx_hash=x['tx_hash'],side='buy' if pb<0 else 'sell',base_amount=abs(pb),quote_amount=abs(pq),amount_usd=usd,price=price,
                        quote_token=quote,usd_source=src))
    o.update(n_swaps=len(out),from_block=b0,to_block=b1,ann_block=ba,source='eth_getLogs '+RPC[r.chain][0])
    if fam in ('v2','aero','v3','pcs3'):
        bb,bq=bal(r.chain,base,r.pool_address,ba),bal(r.chain,quote,r.pool_address,ba)
        pre=[x for x in out if x['timestamp_ms']<=a]; ref=(pre[-1] if pre else (out[0] if out else None))
        if None not in (bb,bq) and ref:
            db,dq=(d0,d1) if base_is0 else (d1,d0); bu=ref['amount_usd']/ref['base_amount'] if ref['amount_usd'] else None
            qv=(qu if qu is not None else (ref['amount_usd']/ref['quote_amount'] if ref['amount_usd'] else None))
            if bu and qv: o.update(liquidity_usd_at_ann=bb/10**db*bu+bq/10**dq*qv,liquidity_at_ann_method=f'balanceOf at block {ba}, valued at nearest swap price')
        if 'liquidity_usd_at_ann' not in o: o['liquidity_note']='balances unavailable at that block on the free RPC, or no swap to price them'
    else: o['liquidity_note']='singleton pool manager: per-pool reserves are not a token balance'
    return o,pd.DataFrame(out)
def safe(r):
    try: o=one(r); print(r.event_id,r.chain,r.dex,o[0].get('n_swaps'),(o[0].get('note') or '')[:60],flush=True); return o
    except Exception as e: return dict(event_id=r.event_id,chain=r.chain,pool_address=r.pool_address,dex=r.dex,note='error '+repr(e)[:150]),None
if __name__=='__main__':
    lim=int(sys.argv[1]) if len(sys.argv)>1 else None
    rows=list(todo.itertuples())[:lim]
    with ThreadPoolExecutor(3) as tp: res=list(tp.map(safe,rows))
    stt=pd.DataFrame([x[0] for x in res]); stt.to_parquet(f'{OUT}/dex_swaps_status.parquet',index=False)
    p=[x[1] for x in res if x[1] is not None and len(x[1])]
    sw=pd.concat(p,ignore_index=True) if p else pd.DataFrame(); sw.to_parquet(f'{OUT}/dex_swaps.parquet',index=False)
    print(stt.drop(columns=[c for c in ('announcement_ms',) if c in stt]).to_string()[:3000] if lim else stt.note.fillna('ok').str[:60].value_counts().to_string(), len(sw))
