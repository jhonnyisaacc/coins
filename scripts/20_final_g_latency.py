"""Final report section 4G: own latency so far, from upbit_poll_log, binance_poll_log and bithumb_poll_log. Writes analysis/g_poll_logs.csv."""
import sys; sys.path.insert(0,'scripts')
import pandas as pd
from final_common import *
rows=[]
for name,lag in [('upbit_poll_log','seen_minus_first_listed_ms'),('bithumb_poll_log','seen_minus_published_ms'),('binance_poll_log','seen_minus_release_ms')]:
    d=pd.read_parquet(f'{D}/{name}.parquet')
    if not len(d): rows.append(dict(table=name,rows=0)); continue
    for r in d.itertuples():
        rows.append(dict(table=name,rows=len(d),title=r.title,is_listing=r.is_listing,lag_s=getattr(r,lag)/1000,poll_interval_s=r.poll_interval_s,
                         http_elapsed_ms=r.http_elapsed_ms,region=r.region,binance_spot_time_rtt_ms=r.binance_spot_time_rtt_ms,test_order_status=r.test_order_status))
save(pd.DataFrame(rows),'g_poll_logs'); print('G done')
