"""Load editable sector assumptions into the unchanged TEMOA v4 SQLite schema.

Inputs are six purpose-based JSON files, not snapshots of database tables.
Records are generated from compact technology groups, year ranges, process
connections, and shared cost/emission assumptions.  SQL tables are an output,
not the primary authoring interface.
"""
from __future__ import annotations

import csv
import itertools
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def normalize_data_quality(table: str, row: dict) -> dict:
    """Store missing data-quality ratings as SQL NULL, never empty text.

    The five data_quality_* lookup tables contain *valid keys* and are not
    normalized. Real numeric ratings are preserved, including 1--5.
    """
    if not table.startswith('data_quality_'):
        for key, value in row.items():
            if key.startswith('dq_') and isinstance(value, str) and not value.strip():
                row[key] = None
    return row


DERIVED_VALUES = {
    'efficiency': 'efficiency',
    'limit_tech_input_split_annual': 'proportion',
    'limit_tech_output_split_annual': 'proportion',
}


def _bindings(data:Path) -> dict:
    file=data/'mappings'/'commodity_bindings.csv'
    mapped=defaultdict(lambda: defaultdict(set))
    with file.open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            mapped[row['tech']][row['direction']].add(row['commodity'])
    return mapped


def expand_rule(table:str,rule:dict,defaults:dict,bindings:dict,model_periods:tuple):
    """Expand combinations of techs, vintages and active lifetime periods."""
    axes=dict(rule.get('axes',{}))
    values={**defaults,**rule.get('values',{})}
    techs=axes.pop('tech',None)
    techs=techs if techs is not None else [None]
    if not isinstance(techs,list) or not techs:
        raise ValueError(f'{table}: axes.tech must be a nonempty list')
    year_pairs=axes.pop('year_pairs',None)
    period_policy=axes.pop('period_policy',None)
    arcs=axes.pop('arc_pairs',None)
    raw_inputs=axes.pop('input_comm',None)
    raw_outputs=axes.pop('output_comm',None)
    time_vints=axes.pop('vintage',None)
    time_periods=axes.pop('period',None)
    for tech in techs:
        base=dict(values)
        if tech is not None:base['tech']=tech
        if year_pairs is not None:
            if any(x is not None for x in (time_vints,time_periods,period_policy)):
                raise ValueError(f'{table}: year_pairs cannot be combined with vintage/period axes')
            time_rows=[{'vintage':v,'period':p} for v,p in year_pairs]
        elif period_policy=='from_vintage':
            if time_periods is not None or not time_vints:
                raise ValueError(f'{table}: from_vintage requires vintage axis only')
            time_rows=[{'vintage':v,'period':p} for v in time_vints for p in model_periods if int(p)>=int(v)]
        else:
            if period_policy is not None:raise ValueError(f'{table}: unknown period policy {period_policy}')
            time_rows=[dict(zip([key for key,val in [('vintage',time_vints),('period',time_periods)] if val is not None],comb))
                for comb in itertools.product(*[arr for arr in [time_vints,time_periods] if arr is not None])]
        if arcs is not None:
            if raw_inputs is not None or raw_outputs is not None:
                raise ValueError(f'{table}: arc_pairs cannot be combined with input/output axes')
            arc_rows=[{'input_comm':i,'output_comm':o} for i,o in arcs]
        else:
            def resolve(raw,direction):
                if raw is None:return [None]
                if raw=='all':
                    if not tech:raise ValueError(f'{table}: all commodities requires tech')
                    names=sorted(bindings[tech][direction])
                    if not names:raise ValueError(f'{table}: no commodity bindings for {tech}/{direction}')
                    return names
                if not isinstance(raw,list) or not raw:
                    raise ValueError(f'{table}: bad {direction} commodity axis')
                return raw
            ins=resolve(raw_inputs,'in');outs=resolve(raw_outputs,'out')
            arc_rows=[dict((k,v) for k,v in [('input_comm',i),('output_comm',o)] if v is not None)
                for i,o in itertools.product(ins,outs)]
        extra_axes={k:v for k,v in axes.items()}
        if any(not isinstance(v,list) or not v for v in extra_axes.values()):
            raise ValueError(f'{table}: other axes must be nonempty lists')
        for times,arc,extras in itertools.product(time_rows,arc_rows,
               [dict(zip(extra_axes.keys(),v)) for v in itertools.product(*extra_axes.values())]):
            row={**base,**times,**arc,**extras}
            if table in DERIVED_VALUES:
                row[DERIVED_VALUES[table]]='1'  # calculated from flows in derive()
            yield row


def scenario_settings(data:Path, scenario:str) -> dict:
    p=data/'scenarios'/f'{scenario}.json'
    cfg=json.loads(p.read_text(encoding='utf-8'))
    if cfg.get('name')!=scenario or not cfg.get('data_id'):
        raise ValueError(f'Invalid scenario config: {p}')
    return cfg


def load_model(data:Path,scenario:str,destination:Path) -> sqlite3.Connection:
    config=scenario_settings(data,scenario)
    if destination.exists():destination.unlink()
    conn=sqlite3.connect(destination)
    try:
        # Preserve legacy TEMOA schema and report upstream FK issues separately.
        conn.execute('PRAGMA foreign_keys=OFF')
        conn.executescript((data/'schema.sql').read_text(encoding='utf-8'))
        known=set(p.stem for p in (data/'scenarios').glob('*.json'))
        if scenario not in known:raise ValueError(f'Unknown scenario {scenario}')
        allowed=set(r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type="table"'))
        folder=data/'inputs'
        inputs=sorted(folder.glob('*.json'))
        if not inputs:raise ValueError(f'Missing editable inputs in {folder}')
        mapped=_bindings(data)
        model_settings=json.loads((data/'parameters'/'model.json').read_text(encoding='utf-8'))
        model_periods=tuple(str(y) for y in model_settings['operating_periods'])
        if not model_periods or len(set(model_periods))!=len(model_periods) or not all(y.isdecimal() for y in model_periods):
            raise ValueError('Invalid operating_periods in parameters/model.json')
        parameters={}
        for kind in ('costs','emissions'):
            path=data/'parameters'/f'{kind}.json'
            for key,entry in json.loads(path.read_text(encoding='utf-8'))['parameters'].items():
                if key in parameters:raise ValueError(f'Duplicate parameter {key}')
                parameters[key]=entry['value']
        seen=set()
        for path in inputs:
            obj=json.loads(path.read_text(encoding='utf-8'))
            for table,spec in obj['tables'].items():
                if table not in allowed:raise ValueError(f'Unknown SQLite table {table}: {path}')
                if table in seen:raise ValueError(f'Table {table} defined in more than one input file')
                seen.add(table)
                columns=[c[1] for c in conn.execute(f'PRAGMA table_info("{table}")')]
                quoted=','.join('"'+c+'"' for c in columns)
                query=f'INSERT INTO "{table}" ({quoted}) VALUES ({",".join("?" for _ in columns)})'
                batch=[]
                for idx,rule in enumerate(spec['rules'],1):
                    members=rule['scenarios'].split('|')
                    if len(set(members))!=len(members) or not set(members)<=known or not all(members):
                        raise ValueError(f'{path.name}:{table} rule {idx}: invalid scenario membership')
                    if scenario not in members:continue
                    for row in expand_rule(table,rule,spec.get('defaults',{}),mapped,model_periods):
                        for field,value in list(row.items()):
                            if isinstance(value,dict) and set(value)=={'parameter'}:
                                key=value['parameter']
                                if key not in parameters:
                                    raise ValueError(f'{table}: undefined model parameter {key}')
                                row[field]=parameters[key]
                        normalize_data_quality(table, row)
                        if set(row)!=set(columns):
                            raise ValueError(f'{path.name}:{table} rule {idx}: invalid fields; missing {set(columns)-set(row)}; extra {set(row)-set(columns)}')
                        batch.append(tuple(config['data_id'] if row[c]=='${SCENARIO_DATA_ID}' else row[c] for c in columns))
                if batch:conn.executemany(query,batch)
        essential={'technology','commodity','efficiency','cost_invest','cost_fixed'}
        if not essential<=seen:raise ValueError(f'Missing required model definitions: {essential-seen}')
        conn.commit()
        return conn
    except BaseException:
        conn.close()
        destination.unlink(missing_ok=True)
        raise
