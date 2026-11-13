"""Per-event price metrics. Usage: python 04_metrics.py <Exchange|all>
Entries (each realistic +1 min delay; buy at the close of the minute AFTER the trigger minute;
 pessimistic variant buys at that candle's HIGH):
  ann_ext   : at the announcement, buy on an external venue where the coin already trades
  start_lst : at trading start, buy on the listing exchange itself
  start_ext : at trading start on the listing exchange, buy on the external venue
Costs: 0.6% round trip (0.1% fee + 0.2% slippage per side) subtracted in *_net columns (analysis step)."""
import sys, csv, json, math, datetime as dt
sys.path.insert(0,'scripts'); from candles import candles, first_trade, market_id, MIN, HOUR
H=[1,5,15,60,240,1440]
NOW=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
EXT_ORDER=['binance','binance_perp','bybit','okx','bybit_perp','upbit','bithumb','coinbase']
EXCH_VENUE={'Upbit':'upbit','Bithumb':'bithumb','Binance':'binance','OKX':'okx','Bybit':'bybit','Coinbase':'coinbase'}
SYM_ALIAS={}  # Upbit uses suffix 2 for name clashes (MET2, META2, UP2, AMP2) -> external ticker without the 2
def ext_sym(s):
    import re
    return re.sub(r'(?<=[A-Z])2$','',s)

def metrics(cs, trig_ms, prefix):
    out={}
    if not cs: return out
    m0=(trig_ms//MIN)*MIN + MIN
    ent=[c for c in cs if m0 <= c[0] <= m0+5*MIN]
    if not ent: return out
    e=ent[0]; ep=e[4]; eph=e[2]; t0=e[0]+MIN
    out[prefix+'entry_ts']=e[0]; out[prefix+'entry_px']=ep; out[prefix+'entry_px_high']=eph
    out[prefix+'entry_delay_s']=round((t0-trig_ms)/1000)
    pre=[c for c in cs if c[0] < (trig_ms//MIN)*MIN]
    if pre and pre[-1][0] >= trig_ms-30*MIN:
        out[prefix+'pre_px']=pre[-1][4]; out[prefix+'missed_move']=ep/pre[-1][4]-1
        trigc=[c for c in cs if c[0]==(trig_ms//MIN)*MIN]
        if trigc: out[prefix+'trig_min_high_move']=trigc[0][2]/pre[-1][4]-1
    for h in H:
        t=t0+h*MIN
        if t>NOW: continue
        prev=[c for c in cs if c[0] < t]
        if not prev or prev[-1][0] < e[0]: continue
        px=prev[-1][4]
        out[f'{prefix}r{h}']=px/ep-1; out[f'{prefix}r{h}_hi']=px/eph-1
    win=[c for c in cs if e[0] < c[0] < t0+1440*MIN]
    if win and t0+1440*MIN<=NOW+HOUR:
        pk=max(win,key=lambda c:c[2]); pi=win.index(pk)
        out[prefix+'peak_gain']=pk[2]/ep-1
        out[prefix+'peak_gain_hi']=pk[2]/eph-1
        out[prefix+'t_peak_min']=(pk[0]-e[0])/MIN
        pre=win[:pi+1]; out[prefix+'dd_before_peak']=min(min(c[3] for c in pre),ep)/ep-1
        post=win[pi:]; out[prefix+'dd_after_peak']=min(c[3] for c in post)/pk[2]-1
        out[prefix+'low24']=min(c[3] for c in win)/ep-1
        # first-hour peak (fast exit reference)
        w1=[c for c in win if c[0] < t0+60*MIN]
        if w1:
            p1=max(w1,key=lambda c:c[2]); out[prefix+'peak60_gain']=p1[2]/ep-1; out[prefix+'t_peak60_min']=(p1[0]-e[0])/MIN
    return out

def find_ext(sym, exclude, at_ms):
    for v in EXT_ORDER:
        if v==exclude: continue
        q = 'KRW' if v in ('upbit','bithumb') else None
        mid=market_id(v, ext_sym(sym), q)
        cs=candles(v, mid, at_ms-3*HOUR, at_ms, unit=1)
        if len(cs)>=3: return v, mid
    return None, None

def run(ev):
    r=dict(ev); ex=ev['exchange']; sym=ev['symbol']
    v=EXCH_VENUE[ex]
    if ex=='Binance' and ev['product']=='perp': v='binance_perp'
    q=None
    if ex=='Upbit': q='KRW' if 'KRW' in ev['markets'] else 'USDT'
    mid=market_id(v, sym, q); r['lst_venue']=v; r['lst_market']=mid
    ann=int(ev['ann_ms'])
    try:
        st, existed = first_trade(v, mid, ann - (0 if ex!='Coinbase' else 0))
    except Exception as e:
        st, existed = None, False; r['err']=str(e)[:80]
    r['lst_existed_before']=existed
    if st and st-ann > 10*86400000: st=None
    r['start_ms']=st or ''
    # external venue at announcement (coin already trading elsewhere?)
    exv, exm = find_ext(sym, v, ann) if ex!='Coinbase' else (None,None)
    r['ext_at_ann']=exv or ''; r['ext_market']=exm or ''
    r['already_trading_elsewhere']= bool(exv)
    if exv and ex!='Coinbase':
        cs=candles(exv, exm, ann-5*MIN, ann+1450*MIN)
        r.update(metrics(cs, ann, 'ann_ext_'))
    if st:
        cs=candles(v, mid, st-5*MIN, st+1450*MIN)
        r.update(metrics(cs, st, 'start_lst_'))
        r['lag_ann_to_start_min']=(st-ann)/MIN if ex!='Coinbase' else ''
        exv2, exm2 = (exv, exm) if exv else find_ext(sym, v, st)
        if exv2:
            cs=candles(exv2, exm2, st-5*MIN, st+1450*MIN)
            r.update(metrics(cs, st, 'start_ext_')); r['ext_at_start']=exv2
    return r

if __name__=='__main__':
    which=sys.argv[1]
    evs=list(csv.DictReader(open('raw/events_all.csv')))
    evs=[e for e in evs if which=='all' or e['exchange']==which]
    from concurrent.futures import ThreadPoolExecutor
    def safe(e):
        try: return run(e)
        except Exception as ex:
            r=dict(e); r['err']=repr(ex)[:120]; return r
    res=[]
    with ThreadPoolExecutor(int(sys.argv[2]) if len(sys.argv)>2 else 6) as tp:
        for i,r in enumerate(tp.map(safe,evs)):
            res.append(r)
            if i%10==0: print(which,i,len(evs),flush=True)
    keys=[]; [keys.append(k) for r in res for k in r if k not in keys]
    with open(f'out/metrics_{which}.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(res)
    print('done',which,len(res))
