"""Run with: python -m unittest discover -s tests -v"""
import csv,json,sqlite3,shutil,tempfile,unittest
from pathlib import Path
from collections import defaultdict
from steel_builder.build import build_one
from steel_builder.flows import load_process_flows,computed

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

class TestSteelBuilder(unittest.TestCase):
 def test_excel_formula_math(self):
  flows=load_process_flows(DATA/'process_flows')
  def ratio(process):
   inp=sum(v for (direction,key),v in flows[process].items() if direction=='in')
   out=sum(v for (direction,key),v in flows[process].items() if direction=='out')
   return out/inp
  self.assertAlmostEqual(ratio('coke_oven'),0.5750596484394022)
  self.assertAlmostEqual(ratio('blast_furnace'),1.064221674476557)
  self.assertAlmostEqual(ratio('basic_oxygen_furnace'),0.8987627884844158)
  self.assertAlmostEqual(ratio('dri_ng'),0.44169611307420492)
  self.assertAlmostEqual(ratio('dri_eaf'),0.28717023303963513)
  self.assertAlmostEqual(ratio('scrap_eaf'),0.45699245081631695)
  self.assertAlmostEqual(ratio('postprocessing'),0.71075619725712114)

 def test_rebuild_preserves_counts(self):
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/'steel.sqlite'
   report=build_one(DATA,'all',file)
   counts=json.loads((DATA/'reference_row_counts.json').read_text())['all']
   self.assertEqual(report['row_counts'],counts)
   c=sqlite3.connect(file)
   self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   self.assertEqual(len(c.execute('PRAGMA foreign_key_check').fetchall()),25028)
   c.close()

 def test_calculated_coefficient_and_splits(self):
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/'steel.sqlite'
   build_one(DATA,'all',file)
   c=sqlite3.connect(file)
   eff=c.execute("SELECT efficiency FROM efficiency WHERE tech='I_ALG_BOF' LIMIT 1").fetchone()[0]
   self.assertAlmostEqual(eff,0.8987627884844158,places=9)
   for t in ['limit_tech_input_split_annual','limit_tech_output_split_annual']:
    rows=c.execute(f'SELECT region,period,tech,operator,SUM(proportion) FROM {t} GROUP BY region,period,tech,operator').fetchall()
    self.assertTrue(rows)
    for row in rows:self.assertAlmostEqual(row[4],1.0,places=7,msg=str(row))
   c.close()

 def test_eaf_copied_efficiency_is_recalculated(self):
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/'steel.sqlite'
   build_one(DATA,'eaf',file)
   c=sqlite3.connect(file)
   v=c.execute("SELECT efficiency FROM efficiency WHERE tech='I_AMM_DRI' LIMIT 1").fetchone()[0]
   self.assertAlmostEqual(v,0.4416961131,places=9)
   c.close()

 def test_uniform_aggregate_efficiencies_in_all_scenarios(self):
  # Validate every vintage, input/output pair, and technology, not merely a
  # representative DRI case. This also covers all legacy-paired candidates.
  flows=load_process_flows(DATA/'process_flows')
  with (DATA/'mappings'/'technology.csv').open(newline='',encoding='utf-8') as f:
   tech_map={r['tech']:r['process'] for r in csv.DictReader(f)}
  bindings=defaultdict(lambda:{'in':{},'out':{}})
  with (DATA/'mappings'/'commodity_bindings.csv').open(newline='',encoding='utf-8') as f:
   for r in csv.DictReader(f):
    bindings[r['tech']][r['direction']][r['commodity']]=r['flow_id']
  with tempfile.TemporaryDirectory() as tmp:
   for scenario in ('basecase','eaf','ccs','all'):
    f=Path(tmp)/f'{scenario}.sqlite'
    report=build_one(DATA,scenario,f)
    c=sqlite3.connect(f)
    for tech,process in tech_map.items():
     pairs=c.execute('SELECT input_comm,output_comm,efficiency FROM efficiency WHERE tech=?',(tech,)).fetchall()
     if not pairs:continue
     actual_ins={x[0] for x in pairs}
     actual_outs={x[1] for x in pairs}
     # All mapped constrained commodities are included in this calculation.
     for table,direction,column in (
       ('limit_tech_input_split_annual','in','input_comm'),
       ('limit_tech_output_split_annual','out','output_comm')):
      existing=c.execute(f'SELECT DISTINCT {column} FROM {table} WHERE tech=?',(tech,)).fetchall()
      if direction=='in':actual_ins.update(x[0] for x in existing)
      else:actual_outs.update(x[0] for x in existing)
     in_map={name:bindings[tech]['in'][name] for name in actual_ins}
     out_map={name:bindings[tech]['out'][name] for name in actual_outs}
     calculated,_,_=computed(process,flows[process],in_map,out_map)
     for inc,outc,eff in pairs:
      self.assertAlmostEqual(eff,calculated[inc,outc],places=9,msg=f'{scenario}/{tech}/{inc}/{outc}')
    self.assertEqual(len(report['row_counts']),91)
    c.close()

 def test_alternative_scrap_routing_is_not_counted_as_four_material_outputs(self):
  flows=load_process_flows(DATA/'process_flows')
  ins={'F_scrap':'generic'}
  outs={name:'generic' for name in ('I_alg_scrap','I_dof_scrap','I_stelco_scrap','I_tinto_scrap')}
  calculated,_,splits=computed('pass_through',flows['pass_through'],ins,outs)
  self.assertEqual(set(calculated.values()),{1.0})
  self.assertEqual(set(splits.values()),{0.25})

 def test_changing_one_flow_recalculates_coefficients_but_not_costs(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);small=folder/'data';small.mkdir()
   shutil.copytree(DATA/'process_flows',small/'process_flows')
   shutil.copytree(DATA/'mappings',small/'mappings')
   shutil.copytree(DATA/'scenarios'/'basecase',small/'scenarios'/'basecase')
   shutil.copyfile(DATA/'schema.sql',small/'schema.sql')
   f=small/'process_flows'/'dri_ng.csv'
   with f.open(newline='',encoding='utf-8') as src:rows=list(csv.DictReader(src));cols=list(rows[0])
   for row in rows:
    if row['direction']=='in' and row['flow_id']=='ng':row['amount']='0.48'
   with f.open('w',newline='',encoding='utf-8') as out:
    w=csv.DictWriter(out,fieldnames=cols);w.writeheader();w.writerows(rows)
   file=folder/'changed.sqlite'
   build_one(small,'basecase',file)
   c=sqlite3.connect(file)
   eff=c.execute("SELECT efficiency FROM efficiency WHERE tech='I_AMM_DRI' LIMIT 1").fetchone()[0]
   self.assertLess(eff,0.44169611307420492)
   cost=c.execute("SELECT cost FROM cost_invest WHERE tech='I_AMM_DRI' LIMIT 1").fetchone()[0]
   self.assertAlmostEqual(cost,299.6656217)
   c.close()

if __name__=='__main__':unittest.main()
