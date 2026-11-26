"""Process-flow CSV loading and flow-derived TEMOA coefficient formulas.

Each process flow is editable inside the package. Ratios follow the model's
numerical convention; mixed input/output units require scientific review.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path

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
