"""One-time or repeated extraction of the Steel-Updated workbook to editable CSVs."""
from __future__ import annotations
import csv,argparse
from pathlib import Path
from .xlsx_reader import cached_cells
from .flows import FLOW_SHEETS, FLOW_UNITS

def convert(xlsx:Path, flow_dir:Path, overwrite:bool=False):
 book=cached_cells(xlsx);flow_dir.mkdir(parents=True,exist_ok=True)
 for process,(sheet,items) in FLOW_SHEETS.items():
  path=flow_dir/(process+'.csv')
  if path.exists() and not overwrite:raise FileExistsError(f'{path} exists; use --overwrite to overwrite your edits')
  with path.open('w',newline='',encoding='utf-8') as file:
   w=csv.writer(file);w.writerow(['direction','flow_id','amount','unit','source_sheet','source_cell','notes'])
   for flow,direction,cell in items:
    try:amount=float(book[sheet][cell])
    except (ValueError,KeyError) as e:raise ValueError(f'Missing numeric value: {sheet}!{cell}') from e
    unit=FLOW_UNITS.get(process,{}).get(flow, 't')
    if process=='scrap_eaf' and direction=='out':note='CO2 from source row 15 is excluded from material output; keep emissions in emission_activity CSV'
    else:note='Source workbook cached value; check heterogeneous units before physical interpretation'
    w.writerow([direction,flow,format(amount,'.17g'),unit,sheet,cell,note])
 # fixed passthrough mapping for imports, separate from the original workbook
 p=flow_dir/'pass_through.csv'
 if not p.exists() or overwrite:
  with p.open('w',newline='',encoding='utf-8') as f:
   w=csv.writer(f);w.writerow(['direction','flow_id','amount','unit','source_sheet','source_cell','notes'])
   for d in ('in','out'):w.writerow([d,'generic',1,'unit','', '', 'Generic one-to-one supply/link technology; not in Excel'])
 print(f'Wrote {len(FLOW_SHEETS)+1} process CSVs to {flow_dir}')

def main():
 p=argparse.ArgumentParser();p.add_argument('workbook',type=Path);p.add_argument('--data',type=Path,default=Path('data/process_flows'));p.add_argument('--overwrite',action='store_true');a=p.parse_args()
 convert(a.workbook,a.data,a.overwrite)
if __name__=='__main__': main()
