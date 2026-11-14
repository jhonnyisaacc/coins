"""Daily forward-only snapshot of public short-side constraints for every USDT perpetual on Binance USD-M and Bybit linear.
Binance: fapi/v1/exchangeInfo (LOT_SIZE and MARKET_LOT_SIZE max qty, requiredMarginPercent, maintMarginPercent,
marketTakeBound, onboardDate) plus fapi/v1/fundingInfo (fundingIntervalHours and adjusted funding cap/floor, published only for
symbols with non-default settings; others get the default 8 h and no cap). Max leverage per Binance symbol comes from
fapi/v1/leverageBracket, which is SIGNED, so binance max_leverage stays empty.
Bybit: v5/market/instruments-info (maxLeverage, maxOrderQty, maxMktOrderQty, fundingInterval, upper/lowerFundingRate) plus
v5/market/risk-limit (tier-1 notional and the largest tier's notional = the position cap).
Appends to data/perp_limits_snapshots.csv; one run per UTC day (a rerun on the same day is skipped).
Usage: python3 scripts/25_perp_limits_snapshot.py   (cron: 5 0 * * *)"""
import os, sys, time, csv, datetime as dt, requests, pandas as pd
OUT='data/perp_limits_snapshots.csv'; S=requests.Session()
COLS=['snapshot_date','snapshot_ms','venue','symbol','status','onboard_ms','max_leverage','max_leverage_source','max_order_qty','max_market_order_qty',
      'position_limit_notional_usd','tier1_notional_usd','tier1_max_leverage','funding_interval_hours','funding_interval_source','funding_cap','funding_floor',
      'required_margin_percent','maint_margin_percent','market_take_bound']
def get(url):
    for a in range(6):
        try:
            r=S.get(url,timeout=30)
            if r.status_code==200: return r.json()
            time.sleep(2+3*a)
        except Exception: time.sleep(2+3*a)
    raise RuntimeError('unreachable '+url)
day=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'); ts=int(time.time()*1000)
if os.path.exists(OUT) and (pd.read_csv(OUT,usecols=['snapshot_date']).snapshot_date==day).any(): print('already snapshotted',day); sys.exit()
rows=[]
ex=get('https://fapi.binance.com/fapi/v1/exchangeInfo'); fi={x['symbol']:x for x in get('https://fapi.binance.com/fapi/v1/fundingInfo')}
for s in ex['symbols']:
    if s['contractType']!='PERPETUAL' or s['quoteAsset']!='USDT': continue
    f={x['filterType']:x for x in s['filters']}; g=fi.get(s['symbol'])
    rows.append(dict(venue='binance_perp',symbol=s['symbol'],status=s['status'],onboard_ms=s['onboardDate'],max_leverage=None,
        max_leverage_source='unavailable: fapi/v1/leverageBracket is SIGNED',max_order_qty=f['LOT_SIZE']['maxQty'],max_market_order_qty=f['MARKET_LOT_SIZE']['maxQty'],
        funding_interval_hours=g['fundingIntervalHours'] if g else 8,funding_interval_source='fundingInfo' if g else 'default (not listed in fundingInfo)',
        funding_cap=g['adjustedFundingRateCap'] if g else None,funding_floor=g['adjustedFundingRateFloor'] if g else None,
        required_margin_percent=s['requiredMarginPercent'],maint_margin_percent=s['maintMarginPercent'],market_take_bound=s.get('marketTakeBound')))
def bybit(path):
    out=[]; cur=''
    while True:
        d=get(f'https://api.bybit.com/v5/market/{path}&limit=1000&cursor={cur}' if 'instruments' in path else f'https://api.bybit.com/v5/market/{path}&cursor={cur}')
        out+=d['result']['list']; cur=d['result'].get('nextPageCursor') or ''
        if not cur: return out
rl={}
for x in bybit('risk-limit?category=linear'): rl.setdefault(x['symbol'],[]).append(x)
for s in bybit('instruments-info?category=linear'):
    if s['contractType']!='LinearPerpetual' or s['quoteCoin']!='USDT': continue
    t=sorted(rl.get(s['symbol'],[]),key=lambda x:float(x['riskLimitValue']))
    rows.append(dict(venue='bybit_perp',symbol=s['symbol'],status=s['status'],onboard_ms=s['launchTime'],max_leverage=s['leverageFilter']['maxLeverage'],
        max_leverage_source='instruments-info leverageFilter',max_order_qty=s['lotSizeFilter']['maxOrderQty'],max_market_order_qty=s['lotSizeFilter'].get('maxMktOrderQty'),
        position_limit_notional_usd=t[-1]['riskLimitValue'] if t else None,tier1_notional_usd=t[0]['riskLimitValue'] if t else None,tier1_max_leverage=t[0]['maxLeverage'] if t else None,
        funding_interval_hours=int(s['fundingInterval'])/60,funding_interval_source='instruments-info',funding_cap=s.get('upperFundingRate'),funding_floor=s.get('lowerFundingRate')))
new=not os.path.exists(OUT)
with open(OUT,'a',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=COLS)
    if new: w.writeheader()
    for r in rows: r.update(snapshot_date=day,snapshot_ms=ts); w.writerow({c:r.get(c) for c in COLS})
print(day,len(rows),'rows')
