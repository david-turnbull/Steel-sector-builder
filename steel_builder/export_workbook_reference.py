"""Optional complete, flat CSV snapshots + curated workbook cost/source values.

The canonical calculation inputs are data/process_flows/. Snapshot CSVs and
curated cost/reference files are documentary, not currently applied to SQLite;
scenario cost/emission CSVs are the model input until a separate audited
normalization pipeline is approved.
"""
from __future__ import annotations
import argparse,csv,re
from pathlib import Path
from .xlsx_reader import cached_cells

COST_CELLS=[
 ('coke_oven','Coke Oven','B19','B22','M CAD / MT coke'),
 ('blast_furnace','Blast Furnace','C17','C20','M CAD / MT hot metal'),
 ('basic_oxygen_furnace','Basic Oxygen Furnace','D20','D23','M CAD / MT liquid steel'),
 ('dri_ng','DRI-NG','D15','D16','M CAD / MT DRI'),
 ('powerplant','Powerplant','M5','M8','M CAD / GW'),
 ('electrolyser','Electrolyser','F18','F20','M CAD / million m3 H2'),
 ('dri_h2','DRI-H2','D16','D17','M CAD / MT DRI'),
 ('dri_eaf','DRI-EAF','D17','D18','M CAD / MT crude steel'),
 ('scrap_eaf','Scrap-EAF','D21','D22','M CAD / MT crude steel'),
 ('postprocessing','Postprocessing','B41','B44','M CAD / MT rolled steel'),
 ('ccs_90_bf','CCS','C4','E4','M CAD / kt CO2'),
 ('ccs_90_pp','CCS','C5','E5','M CAD / kt CO2'),
 ('ccs_99_bf','CCS','C2','E2','M CAD / kt CO2'),
 ('ccs_99_pp','CCS','C3','E3','M CAD / kt CO2'),
]

def letters_to_int(s):
 n=0
 for char in s:n=n*26+ord(char)-64
 return n

def int_to_letters(v):
 chars=[]
 while v:
  v,r=divmod(v-1,26);chars.append(chr(r+65))
 return ''.join(reversed(chars))

def export(xlsx:Path,dest:Path):
 sheets=cached_cells(xlsx);dest.mkdir(parents=True,exist_ok=True)
 snapshots=dest/'snapshots';snapshots.mkdir(exist_ok=True)
 for sheet,cells in sheets.items():
  if not cells:continue
  addresses=[(letters_to_int(m.group(1)),int(m.group(2)),val) for addr,val in cells.items() if (m:=re.fullmatch(r'([A-Z]+)([0-9]+)',addr))]
  if not addresses:continue
  ncol=max(c for c,r,v in addresses);nrow=max(r for c,r,v in addresses)
  grid={(r,c):v for c,r,v in addresses}
  filename=re.sub('[^a-z0-9]+','_',sheet.lower()).strip('_')
  with (snapshots/(filename+'.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.writer(f);w.writerow(['excel_row']+[int_to_letters(n) for n in range(1,ncol+1)])
   for row in range(1,nrow+1):w.writerow([row]+[grid.get((row,col),'') for col in range(1,ncol+1)])
 with (dest/'process_costs_from_workbook.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['process','capex','opex','units_as_reported','source_sheet','capex_cell','opex_cell','status'])
  for process,sheet,capex,opex,units in COST_CELLS:
   w.writerow([process,sheets[sheet].get(capex,''),sheets[sheet].get(opex,''),units,sheet,capex,opex,'reference only; edit scenario cost_*.csv for builder'])
 with (dest/'reference_sources.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['process','primary_source','secondary_source','additional_source'])
  s=sheets['Content and references']
  for row in range(2,15):
   if s.get('A'+str(row)):w.writerow([s.get('A'+str(row),''),s.get('B'+str(row),''),s.get('C'+str(row),''),s.get('D'+str(row),'')])
 print(f'Exported {len(list(snapshots.glob("*.csv")))} workbook snapshot tables and structured reference costs/sources to {dest}')

def main():
 p=argparse.ArgumentParser();p.add_argument('workbook',type=Path);p.add_argument('--output',type=Path,default=Path('data/workbook_reference'));a=p.parse_args();export(a.workbook,a.output)
if __name__=='__main__':main()
