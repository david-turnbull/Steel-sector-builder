"""Initial source migration only: reference SQLite files -> scenario input CSVs.

The finished builder does NOT need the supplied source .sqlite files. Preserve
original rows, units, notes, provenance and explicit constraints in CSV form.
"""
from __future__ import annotations
import argparse,csv,json,sqlite3
from pathlib import Path
from collections import defaultdict
from .flows import process_for,flow_for

SCENARIOS=['basecase','eaf','ccs','all']

def seed(reference_folder:Path, project_root:Path):
 data=project_root/'data'; sc=data/'scenarios'; mapping=data/'mappings'
 mapping.mkdir(parents=True,exist_ok=True)
 techs={};binds={};ref_counts={};schema=None
 for scenario in SCENARIOS:
  db=reference_folder/f'CANOE_steel_{scenario}.sqlite'
  if not db.exists():raise FileNotFoundError(db)
  con=sqlite3.connect(db);con.row_factory=sqlite3.Row
  ddls=[(r['name'],r['sql']) for r in con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name") if r['sql']]
  current='\n\n'.join(sql+';' for name,sql in ddls)+'\n'
  if schema is None: schema=current
  elif current!=schema:raise ValueError(f'{scenario} differs in SQLite table schema')
  d=sc/scenario;d.mkdir(parents=True,exist_ok=True)
  counts={}
  for table,sql in ddls:
   rows=con.execute(f'SELECT * FROM "{table}"').fetchall()
   cols=[x['name'] for x in con.execute(f'PRAGMA table_info("{table}")')]
   counts[table]=len(rows)
   if not rows:continue
   with (d/(table+'.csv')).open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(cols)
    for row in rows:w.writerow(['\\N' if v is None else v for v in row])
  ref_counts[scenario]=counts
  all_inputs=defaultdict(set);all_comm=defaultdict(lambda:defaultdict(set))
  for r in con.execute('SELECT DISTINCT tech,input_comm,output_comm FROM efficiency'):
   all_inputs[r['tech']].add(r['input_comm'])
   all_comm[r['tech']]['in'].add(r['input_comm'])
   all_comm[r['tech']]['out'].add(r['output_comm'])
  for table,direction,col in [('limit_tech_input_split_annual','in','input_comm'),('limit_tech_output_split_annual','out','output_comm')]:
   for r in con.execute(f'SELECT DISTINCT tech,{col} FROM {table}'):
    all_comm[r['tech']][direction].add(r[col])
  for r in con.execute('SELECT DISTINCT tech FROM technology'):
   tech=r['tech'];
   try:process=process_for(tech,all_inputs[tech])
   except ValueError as e:raise ValueError(f'{scenario}: {e}') from e
   if tech in techs:
    if techs[tech]!=process:raise ValueError(f'Inconsistent process for {tech}')
   else:techs[tech]=process
  for tech,dir_map in all_comm.items():
   proc=process_for(tech,all_inputs[tech])
   for direction, comms in dir_map.items():
    for comm in comms:
     k=tech,direction,comm
     value=flow_for(proc,direction,comm)
     if k in binds and binds[k]!=value:raise ValueError(f'Inconsistent commodity mapping {k}')
     binds[k]=value
  con.close()
 (data/'schema.sql').write_text(schema,encoding='utf-8')
 with (mapping/'technology.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['tech','process','notes'])
  for tech,process in sorted(techs.items()):
   w.writerow([tech,process,'All efficiencies use sum(outputs) / sum(inputs)'])
 # Remove obsolete technology-mode overrides if reseeding an older project.
 (mapping/'technology_modes.csv').unlink(missing_ok=True)
 with (mapping/'commodity_bindings.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['tech','direction','commodity','flow_id'])
  for (t,d,c),v in sorted(binds.items()):w.writerow([t,d,c,v])
 (data/'reference_row_counts.json').write_text(json.dumps(ref_counts,indent=2)+'\n',encoding='utf-8')
 print(f'Seeded {len(techs)} technology mappings, {len(binds)} commodity bindings and 4 scenario directories')

def main():
 p=argparse.ArgumentParser();p.add_argument('--reference-folder',type=Path,default=Path('.'));p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args()
 seed(a.reference_folder,a.root)
if __name__=='__main__':main()
