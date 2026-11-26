"""Compare complete SQLite table contents to frozen previous-builder baselines.

The stored baseline reflects v0.5: the v0.4 model with missing data-quality
ratings normalized to SQL NULL. All other records have been preserved.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3


def signatures(database:Path) -> dict[str,str]:
    conn=sqlite3.connect(database)
    try:
        out={}
        for (table,) in conn.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name'):
            rows=[json.dumps(list(row),ensure_ascii=False,separators=(',',':'))
                  for row in conn.execute(f'SELECT * FROM "{table}"')]
            contents='\n'.join(sorted(rows)).encode('utf-8')
            out[table]=sha256(contents).hexdigest()
        return out
    finally:conn.close()


def verify(db:Path,scenario:str,baselines:Path) -> dict:
    expected=json.loads(baselines.read_text(encoding='utf-8'))[scenario]
    actual=signatures(db)
    changed={t:{'expected':expected.get(t),'actual':actual.get(t)}
             for t in sorted(set(actual)|set(expected)) if actual.get(t)!=expected.get(t)}
    return {'scenario':scenario,'tables_checked':len(expected),'changed_tables':changed,'matches':not changed}


def main():
    parser=argparse.ArgumentParser(description='Verify all SQLite table contents against the v0.5 normalized-data-quality baseline')
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--scenario',choices=['basecase','eaf','ccs','all','all_scenarios'],default='all_scenarios')
    args=parser.parse_args()
    names=['basecase','eaf','ccs','all'] if args.scenario=='all_scenarios' else [args.scenario]
    failures=0
    for name in names:
        result=verify(args.root/'outputs'/f'CANOE_steel_{name}.sqlite',name,
                      args.root/'data'/'reference_table_hashes.json')
        print(f'{name}: {result["tables_checked"]} tables; {len(result["changed_tables"])} changed')
        if not result['matches']:
            print('  Tables changed:', ', '.join(result['changed_tables']))
            failures+=1
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
