"""Uniform 1m/1h candle fetchers. Each returns sorted list of [ts_ms_open, o, h, l, c, quote_vol].
Venues: upbit, bithumb (KRW-XXX market), binance (spot XXXUSDT), binance_perp, okx (XXX-USDT spot),
bybit (spot XXXUSDT), bybit_perp, coinbase (XXX-USD)."""
import sys, datetime as dt
sys.path.insert(0, __import__('os').path.dirname(__file__)); from common import get
MIN=60000; HOUR=3600000
def _iso_utc(ms): return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def _kst(ms): return dt.datetime.fromtimestamp(ms/1000,dt.timezone(dt.timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S')
def _now_ms(): return int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)

def _korean(base, market, start, end, unit):
    # backward pagination with `to` (exclusive), 200 per page
    step = 200*unit*MIN; out={}; to=min(end, _now_ms())+unit*MIN
    url = 'https://api.upbit.com' if base=='upbit' else 'https://api.bithumb.com'
    while to > start:
        tos = _iso_utc(to) if base=='upbit' else _kst(to)
        d = get(f"{url}/v1/candles/minutes/{unit}?market={market}&count=200&to={tos}", min_interval=0.13 if base=='upbit' else 0.11, cache=(to < _now_ms()-HOUR))
        if not isinstance(d, list) or not d:
            # no trades in this window; jump one page back
            to -= step
            if isinstance(d,dict) and d.get('_error')==404: break
            continue
        for c in d:
            t = int(dt.datetime.fromisoformat(c['candle_date_time_utc']).replace(tzinfo=dt.timezone.utc).timestamp()*1000)
            out[t]=[t,float(c['opening_price']),float(c['high_price']),float(c['low_price']),float(c['trade_price']),float(c.get('candle_acc_trade_price') or 0)]
        earliest = min(out) if out else to-step
        if len(d) < 200: break   # reached the beginning of market history
        to = earliest
    return [out[k] for k in sorted(out) if start <= k < end]

def _binance(sym, start, end, unit, perp=False):
    base = 'https://fapi.binance.com/fapi/v1/klines' if perp else 'https://data-api.binance.vision/api/v3/klines'
    iv = '1m' if unit==1 else '1h'; out=[]; s=start
    while s < end:
        d = get(f"{base}?symbol={sym}&interval={iv}&startTime={s}&endTime={end-1}&limit=1000", min_interval=0.15, cache=(end < _now_ms()-HOUR))
        if not isinstance(d, list) or not d: break
        out += [[int(k[0]),float(k[1]),float(k[2]),float(k[3]),float(k[4]),float(k[7])] for k in d]
        s = int(d[-1][0]) + unit*MIN
        if len(d) < 1000: break
    return out

def _okx(inst, start, end, unit):
    bar = '1m' if unit==1 else '1H'; out={}; after=end
    while after > start:
        d = get(f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar={bar}&after={after}&limit=100", min_interval=0.12, cache=(end < _now_ms()-HOUR))
        rows = d.get('data') if isinstance(d, dict) else None
        if not rows: break
        for k in rows: out[int(k[0])]=[int(k[0]),float(k[1]),float(k[2]),float(k[3]),float(k[4]),float(k[7])]
        after = min(int(k[0]) for k in rows)
        if len(rows) < 100: break
    return [out[k] for k in sorted(out) if start <= k < end]

def _bybit(sym, start, end, unit, cat='spot'):
    iv = '1' if unit==1 else '60'; out={}; e=end-1
    while e > start:
        d = get(f"https://api.bybit.com/v5/market/kline?category={cat}&symbol={sym}&interval={iv}&start={start}&end={e}&limit=1000", min_interval=0.12, cache=(end < _now_ms()-HOUR))
        rows = (d.get('result') or {}).get('list') if isinstance(d, dict) else None
        if not rows: break
        for k in rows: out[int(k[0])]=[int(k[0]),float(k[1]),float(k[2]),float(k[3]),float(k[4]),float(k[6])]
        e = min(int(k[0]) for k in rows) - 1
        if len(rows) < 1000: break
    return [out[k] for k in sorted(out) if start <= k < end]

def _coinbase(pid, start, end, unit):
    g = 60 if unit==1 else 3600; out={}; s=start
    while s < end:
        e = min(end, s + 300*g*1000)
        d = get(f"https://api.exchange.coinbase.com/products/{pid}/candles?granularity={g}&start={_iso_utc(s)}&end={_iso_utc(e)}", min_interval=0.15, cache=(end < _now_ms()-HOUR))
        if isinstance(d, list):
            for k in d: out[int(k[0])*1000]=[int(k[0])*1000,float(k[3]),float(k[2]),float(k[1]),float(k[4]),float(k[5])*float(k[4])]
        s = e
    return [out[k] for k in sorted(out) if start <= k < end]

def market_id(venue, sym, quote=None):
    if venue in ('upbit','bithumb'): return f"{quote or 'KRW'}-{sym}"
    if venue in ('binance','binance_perp','bybit','bybit_perp'): return f"{sym}{quote or 'USDT'}"
    if venue=='okx': return f"{sym}-{quote or 'USDT'}"
    if venue=='coinbase': return f"{sym}-{quote or 'USD'}"

def candles(venue, mid, start, end, unit=1):
    if venue in ('upbit','bithumb'): return _korean(venue, mid, start, end, unit)
    if venue=='binance': return _binance(mid, start, end, unit)
    if venue=='binance_perp': return _binance(mid, start, end, unit, perp=True)
    if venue=='okx': return _okx(mid, start, end, unit)
    if venue=='bybit': return _bybit(mid, start, end, unit, 'spot')
    if venue=='bybit_perp': return _bybit(mid, start, end, unit, 'linear')
    if venue=='coinbase': return _coinbase(mid, start, end, unit)
    raise ValueError(venue)

def first_trade(venue, mid, after_ms, horizon_days=10, lookback_h=48):
    """Return (first_1m_ts_after, existed_before). existed_before=True if hourly candles exist in
    [after_ms-lookback_h, after_ms)."""
    hs = candles(venue, mid, after_ms - lookback_h*HOUR, after_ms + horizon_days*24*HOUR, unit=60)
    before = [c for c in hs if c[0] < after_ms - HOUR]
    after = [c for c in hs if c[0] >= after_ms - HOUR]
    if not after: return None, bool(before)
    h0 = after[0][0]
    ms = candles(venue, mid, max(h0, after_ms - HOUR), h0 + 3*HOUR, unit=1)
    ms = [c for c in ms if c[0] >= after_ms - MIN] or ms
    return (ms[0][0] if ms else h0), bool(before)
