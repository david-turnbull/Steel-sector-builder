"""Validate editable TEMOA limit records without imposing unsupported science."""
from __future__ import annotations
import math
import sqlite3
from collections import defaultdict

# Empty limit_* tables are legitimate. Non-empty ones are validated based on
# their schema and supported operators; bounds are interpreted per group/period.
def validate_limits(conn: sqlite3.Connection) -> dict:
    names=[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'limit_%' ORDER BY name")]
    valid_operators={row[0] for row in conn.execute('SELECT operator FROM operator')}
    stats={}
    for table in names:
        columns={col[1] for col in conn.execute(f'PRAGMA table_info("{table}")')}
        count=conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        stats[table]=count
        if not count:continue
        if 'operator' in columns:
            invalid=conn.execute(f'SELECT DISTINCT operator FROM "{table}" WHERE operator NOT IN '
                                 f'({",".join("?" for _ in valid_operators)})',tuple(valid_operators)).fetchall()
            if invalid:raise ValueError(f'{table}: unrecognized operators {invalid}')
        numeric=next((k for k in ('activity','capacity','share','value','proportion','factor','rate','fraction') if k in columns),None)
        if numeric:
            for (x,) in conn.execute(f'SELECT "{numeric}" FROM "{table}"'):
                if x is None or not math.isfinite(float(x)) or float(x)<0:
                    raise ValueError(f'{table}: nonfinite, negative or missing {numeric}: {x}')
                if numeric in ('share','proportion','fraction','factor') and float(x)>1:
                    raise ValueError(f'{table}: {numeric} must be <= 1, got {x}')
    # The same constraint key can have a lower and upper bound; they must agree.
    for table,field in [('limit_activity','activity'),('limit_capacity','capacity')]:
        bounds=defaultdict(dict)
        for region,period,name,operator,value,data_id in conn.execute(f'SELECT region,period,tech_or_group,operator,{field},data_id FROM {table}'):
            bounds[(region,period,name,data_id)][operator]=float(value)
        for key,b in bounds.items():
            if 'ge' in b and 'le' in b and b['ge']>b['le']+1e-9:
                raise ValueError(f'{table}: conflicting activity/capacity bounds at {key}: {b}')
            if 'e' in b and ('ge' in b and b['e']<b['ge']-1e-9 or 'le' in b and b['e']>b['le']+1e-9):
                raise ValueError(f'{table}: equality outside bounds at {key}: {b}')
    return {'table_row_counts':stats,'populated_tables':sum(bool(v) for v in stats.values())}
