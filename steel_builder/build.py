"""Generate four TEMOA v4 steel databases from editable sector assumptions and flows.

Core data is stored in six sector input JSON files with shared technology, cost and network rules.
The scenario configs are small JSON files. Numeric efficiency and input/output
splits are ALWAYS calculated from physical process flows, never copied from
scenario table snapshots. The 91-table TEMOA schema remains unchanged.
"""
from __future__ import annotations
import argparse, csv, json, math, os, sqlite3, tempfile
from collections import defaultdict
from pathlib import Path
from .model import load_model
from .flows import load_process_flows, computed

SCENARIOS=['basecase','eaf','ccs','all']


def load_csv(path:Path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def mappings(data:Path):
    tech={r['tech']:r for r in load_csv(data/'mappings'/'technology.csv')}
    bound=defaultdict(lambda:defaultdict(dict))
    for r in load_csv(data/'mappings'/'commodity_bindings.csv'):
        k=(r['tech'],r['direction'],r['commodity'])
        if r['commodity'] in bound[r['tech']][r['direction']]:
            raise ValueError(f'Duplicate binding {k}')
        bound[r['tech']][r['direction']][r['commodity']]=r['flow_id']
    return tech,bound


def derive(conn:sqlite3.Connection,data:Path,scenario:str):
    """Calculate, validate, and update every generated coefficient record."""
    techs,binds=mappings(data)
    flows=load_process_flows(data/'process_flows')
    conn.row_factory=sqlite3.Row
    tech_commodities=defaultdict(lambda:{'in':set(),'out':set()})
    for r in conn.execute('SELECT DISTINCT tech,input_comm,output_comm FROM efficiency'):
        tech_commodities[r['tech']]['in'].add(r['input_comm'])
        tech_commodities[r['tech']]['out'].add(r['output_comm'])
    for t,d,col in [('limit_tech_input_split_annual','in','input_comm'),
                    ('limit_tech_output_split_annual','out','output_comm')]:
        for r in conn.execute(f'SELECT DISTINCT tech,{col} FROM {t}'):
            tech_commodities[r['tech']][d].add(r[col])
    report={'technologies':{},'updated':{'efficiency':0,'limit_tech_input_split_annual':0,
                                        'limit_tech_output_split_annual':0},'warnings':[]}
    for tech,comms in sorted(tech_commodities.items()):
        if tech not in techs:raise ValueError(f'{tech} has no mapping in technology.csv')
        proc=techs[tech]['process']
        if proc not in flows:raise ValueError(f'Missing process CSV for {tech}: {proc}')
        binding=binds[tech]
        for direction in ('in','out'):
            missing=comms[direction]-binding[direction].keys()
            if missing:raise ValueError(f'Missing bindings for {tech}/{direction}: {sorted(missing)}')
        in_map={k:binding['in'][k] for k in comms['in']}
        out_map={k:binding['out'][k] for k in comms['out']}
        for direction,items in [('in',in_map),('out',out_map)]:
            for commodity,flow_key in items.items():
                if (direction,flow_key) not in flows[proc]:
                    raise ValueError(f'{tech}: {commodity} maps to nonexistent {direction}:{flow_key} in {proc}.csv')
        eff,ins,outs=computed(proc,flows[proc],in_map,out_map)
        total_in=sum(flows[proc][('in',name)] for name in set(in_map.values()))
        total_out=sum(flows[proc][('out',name)] for name in set(out_map.values()))
        report['technologies'][tech]={
            'process':proc,'efficiency_method':'sum_outputs_over_sum_inputs',
            'inputs':len(ins),'outputs':len(outs),
            'input_total_numeric':total_in,'output_total_numeric':total_out,
            'aggregate_efficiency_numeric':total_out/total_in,
            'input_split_sum':sum(ins.values()),'output_split_sum':sum(outs.values())}
        for row in conn.execute('SELECT rowid,input_comm,output_comm FROM efficiency WHERE tech=?',(tech,)).fetchall():
            key=row['input_comm'],row['output_comm']
            if key not in eff:raise ValueError(f'Missing efficiency pair {tech}: {key}')
            val=eff[key]
            if not math.isfinite(val) or val<=0:raise ValueError(f'Invalid efficiency {tech}: {key}={val}')
            conn.execute('UPDATE efficiency SET efficiency=? WHERE rowid=?',(round(val,10),row['rowid']))
            report['updated']['efficiency']+=1
        for table,measure,values in [('limit_tech_input_split_annual','input_comm',ins),
                                     ('limit_tech_output_split_annual','output_comm',outs)]:
            for row in conn.execute(f'SELECT rowid,{measure} FROM {table} WHERE tech=?',(tech,)).fetchall():
                comm=row[measure]
                if comm not in values:raise ValueError(f'No modeled {table} value for {tech}/{comm}')
                val=values[comm]
                if not math.isfinite(val) or not 0<=val<=1:
                    raise ValueError(f'Invalid split {tech}/{comm}: {val}')
                conn.execute(f'UPDATE {table} SET proportion=? WHERE rowid=?',(round(val,10),row['rowid']))
                report['updated'][table]+=1
    conn.commit()
    return report


def build_one(data:Path,scenario:str,output:Path, *, enforce_reference_counts:bool=False):
    """Atomically replace a database after model generation and validation."""
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.steel_build_',suffix='.sqlite',dir=output.parent,delete=False) as f:
        tmp=Path(f.name)
    try:
        conn=load_model(data,scenario,tmp)
        try:
            report=derive(conn,data,scenario)
            integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity!='ok':raise ValueError(f'SQLite integrity check failed: {integrity}')
            report['scenario']=scenario
            report['integrity_check']=integrity
            fk_findings=conn.execute('PRAGMA foreign_key_check').fetchall()
            report['foreign_key_findings']=len(fk_findings)
            fk_columns={}
            for (table_name,) in conn.execute('SELECT name FROM sqlite_master WHERE type="table"'):
                for entry in conn.execute(f'PRAGMA foreign_key_list("{table_name}")'):
                    fk_columns[(table_name,entry[0])]=entry[3]
            by_category={'data_quality':0,'time_period':0,'other':0}
            by_table={}
            for table_name, _row_id, parent, fk_id in fk_findings:
                column=fk_columns.get((table_name,fk_id),'unknown')
                category=('data_quality' if column.startswith('dq_') else
                          'time_period' if parent=='time_period' else 'other')
                by_category[category]+=1
                by_table[table_name]=by_table.get(table_name,0)+1
            report['foreign_key_findings_by_category']=by_category
            report['foreign_key_findings_by_table']=dict(sorted(by_table.items()))
            report['row_counts']={r[0]:conn.execute(f'SELECT COUNT(*) FROM "{r[0]}"').fetchone()[0]
                for r in conn.execute('SELECT name FROM sqlite_master WHERE type="table"')}
            expected_path=data/'reference_row_counts.json'
            if expected_path.is_file():
                expected=json.loads(expected_path.read_text(encoding='utf-8'))[scenario]
                differences={t:{'expected':expected.get(t),'actual':report['row_counts'].get(t)}
                    for t in set(expected)|set(report['row_counts'])
                    if expected.get(t)!=report['row_counts'].get(t)}
                report['reference_row_count_differences']=differences
                if differences and enforce_reference_counts:
                    raise ValueError(f'Reference row counts differ: {differences}')
                if differences:
                    report['warnings'].append('Model row counts differ from the supplied reference; review intentional model additions/removals.')
            if report['foreign_key_findings']:
                report['warnings'].append('Unresolved foreign-key references remain (not data-quality blanks); see foreign_key_findings_by_category. Time-period and source references require separate scientific review.')
        finally:conn.close()
        os.replace(tmp,output)
        return report
    finally:tmp.unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('.'),help='Project root containing data/')
    parser.add_argument('--scenario',choices=SCENARIOS+['all_scenarios'],default='all_scenarios')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--enforce-reference-counts',action='store_true',
        help='Fail on any model row-count change; omit when intentionally adding technologies')
    args=parser.parse_args()
    data=args.root/'data'
    output=args.output_dir or args.root/'outputs'
    scenarios=SCENARIOS if args.scenario=='all_scenarios' else [args.scenario]
    for scenario in scenarios:
        out=output/f'CANOE_steel_{scenario}.sqlite'
        report=build_one(data,scenario,out,enforce_reference_counts=args.enforce_reference_counts)
        (output/f'{scenario}_build_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(f'{scenario}: {out} / calculated {report["updated"]} / integrity={report["integrity_check"]}, remaining foreign-key findings={report["foreign_key_findings"]}')

if __name__=='__main__':main()
