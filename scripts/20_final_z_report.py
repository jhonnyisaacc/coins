"""Render docs/FINAL_REPORT.md from scripts/final_report_template.md and the CSVs in analysis/, and write the "final_report"
key of data/summary.json (every other key is left as it is). Every number in the report is a lookup into a CSV:
  {{[name=]file#filters#column[#format]}}   one cell; filters are col=value joined by &&, value alternatives joined by ~
  {{table#file#filters#col:Header[:format],col:Header[#format]}}   a Markdown table of the matching rows, in CSV order
A lookup that matches no row or more than one row stops the render. Table rows with n = 0 are left out. Format "n" prints an integer and flags n < 20;
"pct" prints one decimal; "int" prints an integer with thousands separators; "s" prints the value as text.
Named cells go to summary.json["final_report"]. analysis/z_csv_rows.csv lists the row count of every analysis CSV."""
import sys, re, glob, json, os; sys.path.insert(0,'scripts')
import numpy as np, pandas as pd
from final_common import A, D, select
TEMPLATE='scripts/final_report_template.md'; OUT='docs/FINAL_REPORT.md'
rows=[dict(file=os.path.basename(f),rows=len(pd.read_csv(f,low_memory=False))) for f in sorted(glob.glob(f'{A}/*.csv')) if not f.endswith('z_csv_rows.csv')]
pd.DataFrame(rows).to_csv(f'{A}/z_csv_rows.csv',index=False)

def fmt(v, f):
    if v is None or (isinstance(v,float) and np.isnan(v)): return 'n/a'
    if f=='s': return str(v)
    if f=='n': n=int(round(float(v))); return f'{n:,} (n<20)' if n<20 else f'{n:,}'
    if f=='int': return f'{int(round(float(v))):,}'
    out=f'{float(v):.1f}' if f in ('pct','',None) else format(float(v),f)
    return out[1:] if re.fullmatch(r'-0(\.0+)?',out) else out

named={}
def cell(m):
    body=m.group(1); name=None
    if body.startswith('table#'):
        _,file,filters,cols,*f=body.split('#'); d=select(file,filters); f=f[0] if f else 'pct'
        if not len(d): raise ValueError(f'empty table: {body}')
        cs=[(c.split(':')+[None])[:3] for c in cols.split(',')]
        out=['| '+' | '.join(h for _,h,_ in cs)+' |','|'+'|'.join('---' for _ in cs)+'|']
        def num(v):
            try: return float(v)
            except (TypeError,ValueError): return None
        for _,r in d.iterrows():
            if 'n' in d and pd.notna(r['n']) and float(r['n'])==0: continue
            def one(c,cf):
                v=r[c]
                if cf: return fmt(v,cf)
                if c=='n' or c.endswith('_n') or c.startswith('n_'): return fmt(v,'n')
                if isinstance(v,(bool,np.bool_)) or isinstance(v,str) and num(v) is None: return str(v)
                return fmt(num(v),f) if num(v) is not None else fmt(v,f)
            out.append('| '+' | '.join(one(c,cf) for c,_,cf in cs)+' |')
        return '\n\n'+'\n'.join(out)+'\n'
    if '=' in body.split('#')[0]: name,body=body.split('=',1)
    file,filters,col,*f=body.split('#'); d=select(file,filters)
    if len(d)!=1: raise ValueError(f'{len(d)} rows for {{{{{m.group(1)}}}}}')
    v=d[col].iloc[0]; s=fmt(v,f[0] if f else 'pct')
    if name: named[name]=None if pd.isna(v) else (v.item() if hasattr(v,'item') else v)
    return s

text=open(TEMPLATE).read()
out=re.sub(r'\{\{(.+?)\}\}',cell,text,flags=re.S)
os.makedirs('docs',exist_ok=True); open(OUT,'w').write(out)
S=json.load(open(f'{D}/summary.json')); before={k:json.dumps(v,sort_keys=True) for k,v in S.items() if k!='final_report'}
S['final_report']={'generated_by':'scripts/20_final_z_report.py','report':OUT,'units':'returns in percent, net of 0.6% round trip; sizes in USD thousands where named _k','values':named}
assert all(json.dumps(S[k],sort_keys=True)==v for k,v in before.items())
json.dump(S,open(f'{D}/summary.json','w'),default=lambda x:None)
print('rendered',OUT,len(out.splitlines()),'lines,',len(named),'named values')
