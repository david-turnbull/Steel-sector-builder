"""Source of workbook-cell-to-CSV mappings, and TEMOA commodity aliases.

Important: ratios deliberately follow the arithmetic of the v4 workbook, even
where the flows mix mass, energy and volume. They are model coefficients, NOT
unit-consistent physical efficiencies.
"""
from __future__ import annotations
from collections import defaultdict
import csv
import math
from pathlib import Path

# flow ID, direction, cell on the named workbook sheet
FLOW_SHEETS = {
 'coke_oven': ('Coke Oven', [
  ('coal','in','B4'),('cogas','in','B5'),('bfgas','in','B6'),('elc','in','B7'),
  ('cogas','out','B10'),('coke','out','B11')]),
 'blast_furnace': ('Blast Furnace', [
  ('iron_pellet','in','B3'),('ironore','in','B4'),('coke','in','B5'),
  ('elc','in','B6'),('bfgas','in','B7'),('pigiron','out','B11'),('bfgas','out','B12')]),
 'basic_oxygen_furnace': ('Basic Oxygen Furnace', [
  ('home_scrap','in','B4'),('scrap','in','B5'),('pigiron','in','B6'),('elc','in','B7'),
  ('liq_steel','out','B11'),('waste_slag','out','B12'),('export_slag','out','B13'),('bofgas','out','B14')]),
 'dri_ng': ('DRI-NG', [
  ('iron_pellet','in','B4'),('ng','in','B5'),('elc','in','B6'),('dri','out','B10')]),
 'powerplant': ('Powerplant', [
  ('bfgas','in','C6'),('bofgas','in','C7'),('elc','out','E10')]),
 'electrolyser': ('Electrolyser', [
  ('elc','in','D5'),('h2','out','C9')]),
 'dri_h2': ('DRI-H2', [
  ('iron_pellet','in','B4'),('ng','in','B5'),('elc','in','B6'),('h2','in','B7'),('dri','out','B11')]),
 'dri_eaf': ('DRI-EAF', [
  ('dri','in','B4'),('elc','in','B5'),('steel','out','B9'),('slag','out','B10')]),
 'scrap_eaf': ('Scrap-EAF', [
  ('scrap','in','B8'),('elc','in','B9'),('steel','out','B13'),('slag','out','B14')]),
 'postprocessing': ('Postprocessing', [
  ('liq_steel','in','B27'),('elc','in','B28'),('rolled_steel','out','B32'),('home_scrap','out','B33')]),
 'ccs_90': ('CCS', [
  ('elc','in','C23'),('ng','in','C24'),('co2','out','C28')]),
 'ccs_99': ('CCS', [
  ('elc','in','G22'),('ng','in','G23'),('co2','out','G27')]),
}
# Explicit unit declarations from input/output blocks of source workbook.
FLOW_UNITS={
 'coke_oven': {'elc':'GJ'},
 'blast_furnace': {'elc':'GJ'},
 'basic_oxygen_furnace': {'elc':'GJ'},
 'dri_ng': {'elc':'GJ'},
 'powerplant': {'elc':'GJ'},
 'electrolyser': {'elc':'GJ','h2':'thousands m3'},
 'dri_h2': {'elc':'GJ','h2':'thousands m3'},
 'dri_eaf': {'elc':'GJ'},
 'scrap_eaf': {'elc':'GJ'},
 'postprocessing': {'elc':'GJ'},
 'ccs_90': {'elc':'PJ/kt CO2','ng':'PJ/kt CO2','co2':'fraction'},
 'ccs_99': {'elc':'PJ/kt CO2','ng':'PJ/kt CO2','co2':'fraction'},
}

def process_for(tech: str, inputs: set[str]) -> str:
 u=tech.upper()
 if u.startswith('F_') or '_IMP_' in u: return 'pass_through'
 if u.endswith('_CCS_90'):return 'ccs_90'
 if u.endswith('_CCS_99'):return 'ccs_99'
 if u.endswith('_H2_ELEC'):return 'electrolyser'
 if u.endswith('_H2_DRI'):return 'dri_h2'
 if u.endswith('_NG_DRI') or u.endswith('_DRI'):return 'dri_ng'
 if u.endswith('_D_EAF'):return 'dri_eaf'
 if u.endswith('_S_EAF'):return 'scrap_eaf'
 if u.endswith('_EAF_PP') or u.endswith('_PP'):return 'postprocessing'
 if u.endswith('_PPLANT'):return 'powerplant'
 if u.endswith('_BOF'):return 'basic_oxygen_furnace'
 if u.endswith('_BF'):return 'blast_furnace'
 if u.endswith('_CO'):return 'coke_oven'
 if u.endswith('_EAF'):
  return 'dri_eaf' if any(x.lower().endswith('_dri') for x in inputs) else 'scrap_eaf'
 raise ValueError(f'No process rule for technology {tech}')

def flow_for(process: str, direction: str, commodity: str) -> str:
 if process=='pass_through': return 'generic'
 x=commodity.lower()
 if x=='co2_ccs':return 'co2'
 if x=='i_ng':return 'ng'
 if x=='i_met_coal':return 'coal'
 if x=='i_iron_pellet':return 'iron_pellet'
 if x=='i_ironore':return 'ironore'
 if x=='i_rolled_steel':return 'rolled_steel'
 if x.endswith('_bof_gas'):return 'bofgas'
 if x.endswith('_bfgas'):return 'bfgas'
 if x.endswith('_cogas'):return 'cogas'
 if x.endswith('_wasteslag'):return 'waste_slag'
 if x.endswith('_homescrap'):return 'home_scrap'
 if x.endswith('_scrap'):
  return 'home_scrap' if process=='postprocessing' and direction=='out' else 'scrap'
 if x.endswith('_coke'):return 'coke'
 if x.endswith('_pigiron'):return 'pigiron'
 if x.endswith('_elc') or x=='i_elc':return 'elc'
 if x.endswith('_h2'):return 'h2'
 if x.endswith('_dri'):return 'dri'
 if x.endswith('_eaf_crude_steel') or x.endswith('_crude_steel'):
  return ('liq_steel' if process in ('postprocessing','basic_oxygen_furnace') else 'steel')
 if x.endswith('_slag'):return 'export_slag' if process=='basic_oxygen_furnace' else 'slag'
 raise ValueError(f'Cannot map {commodity} ({direction}) for {process}')

def load_process_flows(folder: Path) -> dict:
 out={}
 for f in sorted(folder.glob('*.csv')):
  with f.open(encoding='utf-8-sig', newline='') as handle:
   rows=list(csv.DictReader(handle))
  grouped={}
  for r in rows:
   k=r['direction'],r['flow_id']
   if k in grouped:raise ValueError(f'Duplicate flow {f}: {k}')
   a=float(r['amount'])
   if not math.isfinite(a) or a<=0:raise ValueError(f'Non-positive or missing flow {f} / {k} ({a})')
   grouped[k]=a
  out[f.stem]=grouped
 return out

def computed(process: str, flows: dict, inputs: dict, outputs: dict):
 """Calculate EVERY input/output-pair efficiency using the new aggregate rule.

 Efficiency uses the sum of distinct *physical process flows*. Multiple TEMOA
 commodity aliases for a single process flow (for example, F_I_SCRAP routing a
 generic unit of scrap to one of four facilities) are alternative edges; they
 are not four physical output quantities. Counting such aliases multiple times
 would inflate an import link's efficiency to 4 instead of its physical 1.

 Splits are calculated over the modeled commodity quantities. This means that
 each distinct mapped commodity contributes to its side's split denominator,
 so shares sum to one when a technology has split constraints.
 """
 in_qty={k:flows[("in",v)] for k,v in inputs.items()}
 out_qty={k:flows[("out",v)] for k,v in outputs.items()}
 total_in=sum(flows[("in",name)] for name in set(inputs.values()))
 total_out=sum(flows[("out",name)] for name in set(outputs.values()))
 if total_in<=0 or total_out<=0:raise ValueError(f'{process}: invalid flow totals')
 input_denominator=sum(in_qty.values())
 output_denominator=sum(out_qty.values())
 if input_denominator<=0 or output_denominator<=0:
  raise ValueError(f'{process}: invalid commodity split totals')
 efficiency=total_out/total_in
 return ({(i,o):efficiency for i in in_qty for o in out_qty},
         {i:a/input_denominator for i,a in in_qty.items()},
         {o:b/output_denominator for o,b in out_qty.items()})
