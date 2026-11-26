"""Build all TEMOA v4 Steel SQLite files from editable CSV sources.

Strictly preserve all original tables, constraints, provenance, and
scenario-specific data; ALWAYS recompute *existing* efficiency and annual
split rows from process flow CSVs. Never silently create new technology edges.
"""
from __future__ import annotations
import argparse,csv,sqlite3,json,math,os,tempfile
from collections import defaultdict
from pathlib import Path
from .flows import load_process_flows,computed

SCENARIOS=['basecase','eaf','ccs','all']

def load_csv(path:Path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def mappings(data:Path):
 tech={r['tech']:r for r in load_csv(data/'mappings'/'technology.csv')}
 bound=defaultdict(lambda: defaultdict(dict))
 for r in load_csv(data/'mappings'/'commodity_bindings.csv'):
  k=(r['tech'],r['direction'],r['commodity'])
  if r['commodity'] in bound[r['tech']][r['direction']]:raise ValueError(f'duplicate binding {k}')
  bound[r['tech']][r['direction']][r['commodity']]=r['flow_id']
 return tech,bound

def load_database(data:Path,scenario:str,destination:Path):
 if destination.exists():destination.unlink()
 c=sqlite3.connect(destination)
 try:
  c.execute('PRAGMA foreign_keys=OFF')  # references contain existing FKs not found in source tables
  c.executescript((data/'schema.sql').read_text(encoding='utf-8'))
  available={r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type="table"')}
  files=list((data/'scenarios'/scenario).glob('*.csv'))
  for path in files:
   table=path.stem
   if table not in available:raise ValueError(f'unknown table {table} in {path}')
   with path.open(newline='',encoding='utf-8-sig') as f:
    reader=csv.reader(f);cols=next(reader)
    expected=[x[1] for x in c.execute(f'PRAGMA table_info("{table}")')]
    if cols!=expected:raise ValueError(f'Columns in {path}: {cols} differ from {expected}')
    q=f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in cols)})'
    chunk=[]
    for row in reader:
     if len(row)!=len(cols):raise ValueError(f'Wrong CSV column count in {path}: {row}')
     chunk.append([None if v=='\\N' else v for v in row])
     if len(chunk)>=5000:c.executemany(q,chunk);chunk=[]
    if chunk:c.executemany(q,chunk)
  c.commit()
  return c
 except BaseException:
  c.close()
  if destination.exists():destination.unlink()
  raise

def derive(c:sqlite3.Connection,data:Path,scenario:str):
 techs,binds=mappings(data);flows=load_process_flows(data/'process_flows')
 c.row_factory=sqlite3.Row
 # Each reference table has scenario-specific presence/absence of technologies.
 # Only rebuild ratios on existing reference pairs/limits, never auto-add constraints.
 tech_commodities=defaultdict(lambda:{'in':set(),'out':set()})
 for r in c.execute('SELECT DISTINCT tech,input_comm,output_comm FROM efficiency'):
  tech_commodities[r['tech']]['in'].add(r['input_comm'])
  tech_commodities[r['tech']]['out'].add(r['output_comm'])
 for t,d,col in [('limit_tech_input_split_annual','in','input_comm'),('limit_tech_output_split_annual','out','output_comm')]:
  for r in c.execute(f'SELECT DISTINCT tech,{col} FROM {t}'):
   tech_commodities[r['tech']][d].add(r[col])
 report={'technologies':{},'updated':{'efficiency':0,'limit_tech_input_split_annual':0,'limit_tech_output_split_annual':0},'warnings':[]}
 for tech,comms in sorted(tech_commodities.items()):
  if tech not in techs:raise ValueError(f'{tech} has no mapping in technology.csv')
  info=techs[tech];proc=info['process']
  if proc not in flows:raise ValueError(f'Missing process CSV for {tech}: {proc}')
  binding=binds[tech]
  in_map={k:binding['in'][k] for k in comms['in']}
  out_map={k:binding['out'][k] for k in comms['out']}
  for direction,items in [('in',in_map),('out',out_map)]:
   for commodity,flow_key in items.items():
    if (direction,flow_key) not in flows[proc]:
     raise ValueError(f'{tech}: {commodity} mapped to nonexistent {direction}:{flow_key} in {proc}.csv')
  eff,ins,outs=computed(proc,flows[proc],in_map,out_map)
  # Count each physical flow once, not every alias of an alternative outlet.
  total_i=sum(flows[proc]['in',name] for name in set(in_map.values()))
  total_o=sum(flows[proc]['out',name] for name in set(out_map.values()))
  # This is a coefficient, possibly with heterogeneous units, not mass conservation.
  report['technologies'][tech]={
   'process':proc,'efficiency_method':'sum_outputs_over_sum_inputs',
   'inputs':len(ins),'outputs':len(outs),
   'input_total_numeric':total_i,'output_total_numeric':total_o,
   'aggregate_efficiency_numeric':total_o/total_i,
   'input_split_sum':sum(ins.values()),'output_split_sum':sum(outs.values())}
  for row in c.execute('SELECT rowid,input_comm,output_comm,efficiency FROM efficiency WHERE tech=?',(tech,)).fetchall():
   k=(row['input_comm'],row['output_comm'])
   if k not in eff:raise ValueError(f'Missing efficiency pair {tech}: {k}')
   val=eff[k]
   if not math.isfinite(val) or val<=0:raise ValueError(f'Invalid efficiency {tech} {k}: {val}')
   c.execute('UPDATE efficiency SET efficiency=? WHERE rowid=?',(round(val,10),row['rowid']))
   report['updated']['efficiency']+=1
  for table,direction,measure,values in [('limit_tech_input_split_annual','in','input_comm',ins),('limit_tech_output_split_annual','out','output_comm',outs)]:
   for row in c.execute(f'SELECT rowid,{measure},proportion FROM {table} WHERE tech=?',(tech,)).fetchall():
    comm=row[measure];val=values[comm]
    if not (0<=val<=1):raise ValueError(f'Invalid split {tech} {comm}: {val}')
    c.execute(f'UPDATE {table} SET proportion=? WHERE rowid=?',(round(val,10),row['rowid']))
    report['updated'][table]+=1
 c.commit()
 return report

def build_one(data:Path,scenario:str,output:Path):
 """Atomic build: keep last known-good output if any source CSV fails validation."""
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(prefix='.steel_build_',suffix='.sqlite',dir=output.parent,delete=False) as f:
  temp=Path(f.name)
 try:
  conn=load_database(data,scenario,temp)
  try:
   report=derive(conn,data,scenario)
   check=conn.execute('PRAGMA integrity_check').fetchone()[0]
   if check!='ok':raise ValueError('SQLite integrity check failed: '+str(check))
   report['scenario']=scenario;report['integrity_check']=check
   report['row_counts']={r[0]:conn.execute(f'SELECT COUNT(*) FROM "{r[0]}"').fetchone()[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type="table"')}
  finally:conn.close()
  os.replace(temp,output)
  return report
 finally:
  temp.unlink(missing_ok=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path('.'),help='Project root with data/')
 p.add_argument('--scenario',choices=SCENARIOS+['all_scenarios'],default='all_scenarios')
 p.add_argument('--output-dir',type=Path,default=None)
 a=p.parse_args();data=a.root/'data';output=a.output_dir or a.root/'outputs'
 scenarios=SCENARIOS if a.scenario=='all_scenarios' else [a.scenario]
 for scenario in scenarios:
  db=output/f'CANOE_steel_{scenario}.sqlite'
  report=build_one(data,scenario,db)
  dest=output/f'{scenario}_build_report.json'
  dest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
  print(f'{scenario}: {db} / updated {report["updated"]} / integrity {report["integrity_check"]}')
if __name__=='__main__':main()
