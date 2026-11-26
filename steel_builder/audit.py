"""Compare all tables in regenerated SQLite against supplied references.

Numeric differences due to newly recalculated flows are reported; foreign-key
issues in the supplied source are intentionally not silently repaired.
"""
from __future__ import annotations
import argparse,sqlite3,json,collections,math
from pathlib import Path
from .build import SCENARIOS

def audit(original:Path,generated:Path):
 a=sqlite3.connect(original);b=sqlite3.connect(generated)
 result={'source':str(original),'built':str(generated),'different_tables':{},'same_tables':0,'source_foreign_key_errors':0,'built_foreign_key_errors':0}
 try:
  tables=[r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
  for t in tables:
   x=a.execute(f'SELECT * FROM "{t}"').fetchall()
   y=b.execute(f'SELECT * FROM "{t}"').fetchall()
   # rows primary-key order can differ, so compare multisets of exact rows
   cx=collections.Counter(x);cy=collections.Counter(y)
   if cx==cy:result['same_tables']+=1
   else:
    keys=a.execute(f'PRAGMA table_info("{t}")').fetchall();cols=[r[1] for r in keys]
    result['different_tables'][t]={
     'reference_rows':len(x),'generated_rows':len(y),
     'reference_only_rows':sum((cx-cy).values()),
     'generated_only_rows':sum((cy-cx).values()),
     'changed_columns':[]}
    diff=collections.Counter()
    pks=[r[1] for r in keys if r[5]]
    if pks:
     indices=[cols.index(c) for c in pks]
     da={tuple(row[i] for i in indices):row for row in x}
     db={tuple(row[i] for i in indices):row for row in y}
     for k in da.keys()&db.keys():
      for i,c in enumerate(cols):
       if da[k][i]!=db[k][i]:diff[c]+=1
    result['different_tables'][t]['changed_columns']=dict(diff)
  result['source_foreign_key_errors']=len(a.execute('PRAGMA foreign_key_check').fetchall())
  result['built_foreign_key_errors']=len(b.execute('PRAGMA foreign_key_check').fetchall())
  return result
 finally:a.close();b.close()

def main():
 p=argparse.ArgumentParser();p.add_argument('--references',type=Path,required=True);p.add_argument('--outputs',type=Path,default=Path('outputs'));p.add_argument('--scenario',choices=SCENARIOS+['all_scenarios'],default='all_scenarios');p.add_argument('--report',type=Path,default=None)
 a=p.parse_args();which=SCENARIOS if a.scenario=='all_scenarios' else [a.scenario]
 report={s:audit(a.references/f'CANOE_steel_{s}.sqlite',a.outputs/f'CANOE_steel_{s}.sqlite') for s in which}
 print(json.dumps(report,indent=2))
 if a.report:a.report.parent.mkdir(exist_ok=True,parents=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
