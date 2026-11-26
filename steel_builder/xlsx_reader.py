"""Minimal read-only cached-cell reader for OOXML .xlsx (Python standard library).
Never edits XLSX or evaluates formulas; re-save the workbook in Excel if cached
formula results are absent. Intended ONLY for initial CSV migration.
"""
from __future__ import annotations
import zipfile,xml.etree.ElementTree as ET
from pathlib import Path
M='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

def cached_cells(path:Path)->dict[str,dict[str,str]]:
 with zipfile.ZipFile(path) as z:
  shared=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   root=ET.fromstring(z.read('xl/sharedStrings.xml'))
   shared=[''.join(t.text or '' for t in s.iter(M+'t')) for s in root.findall(M+'si')]
  rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
  paths={r.get('Id'):r.get('Target') for r in rels}
  book=ET.fromstring(z.read('xl/workbook.xml'))
  result={}
  for s in book.findall('.//'+M+'sheet'):
   name=s.get('name'); target=paths[s.get(R+'id')].lstrip('/')
   if not target.startswith('xl/'):target='xl/'+target
   root=ET.fromstring(z.read(target))
   cells={}
   for c in root.iter(M+'c'):
    v=c.find(M+'v');inline=c.find(M+'is');f=c.find(M+'f')
    if v is None and inline is None:continue
    val=v.text if v is not None else ''.join(t.text or '' for t in inline.iter(M+'t'))
    if c.get('t')=='s':val=shared[int(val)]
    if val is None and f is not None: raise ValueError(f'{name}!{c.get("r")} has no formula cache')
    cells[c.get('r')]=val
   result[name]=cells
 return result
