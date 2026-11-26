"""Regression and editable-input behaviour of the standalone steel-sector package."""
import csv
import json
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from steel_builder.build import build_one
from steel_builder.flows import load_process_flows,computed
from steel_builder.model import expand_rule, normalize_data_quality
from steel_builder.verify_reference import verify

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SCENARIOS=('basecase','eaf','ccs','all')

def clone(path):
    path.mkdir(exist_ok=True,parents=True)
    for folder in ('inputs','mappings','process_flows','scenarios','parameters'):
        shutil.copytree(DATA/folder,path/folder)
    for f in ('schema.sql','reference_row_counts.json'):
        shutil.copy2(DATA/f,path/f)

def write_json(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

class SectorBuilderTests(unittest.TestCase):
    def test_all_scenarios_exact_match_normalized_dq_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            for scen in SCENARIOS:
                db=Path(d)/(scen+'.sqlite')
                report=build_one(DATA,scen,db,enforce_reference_counts=True)
                self.assertEqual(report['integrity_check'],'ok')
                self.assertEqual(report['foreign_key_findings_by_category']['data_quality'],0)
                self.assertEqual(sum(report['foreign_key_findings_by_category'].values()),report['foreign_key_findings'])
                self.assertEqual(report['reference_row_count_differences'],{})
                self.assertEqual(len(report['row_counts']),91)
                result=verify(db,scen,DATA/'reference_table_hashes.json')
                self.assertTrue(result['matches'],f'{scen}: {result["changed_tables"]}')

    def test_missing_dq_becomes_null_and_legitimate_ratings_remain_intact(self):
        # This normalization is limited to source records, not rating lookup keys.
        row={'dq_time':'  ', 'dq_geog':'', 'dq_cred':None, 'dq_tech':3, 'dq_struc':'2'}
        normalize_data_quality('efficiency',row)
        self.assertEqual(row,{'dq_time':None, 'dq_geog':None,
                              'dq_cred':None, 'dq_tech':3, 'dq_struc':'2'})
        lookup={'dq_time':''}
        normalize_data_quality('data_quality_time',lookup)
        self.assertEqual(lookup['dq_time'],'')

        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'steel.sqlite'
            report=build_one(DATA,'basecase',db)
            self.assertEqual(report['foreign_key_findings_by_category']['data_quality'],0)
            with closing(sqlite3.connect(db)) as c:
                for (table,) in c.execute('SELECT name FROM sqlite_master WHERE type="table"'):
                    if table.startswith('data_quality_'):
                        continue
                    cols=[col[1] for col in c.execute(f'PRAGMA table_info("{table}")')
                          if col[1].startswith('dq_')]
                    for col in cols:
                        invalid=c.execute(f'SELECT COUNT(*) FROM "{table}" WHERE "{col}" IS NOT NULL AND TRIM(CAST("{col}" AS TEXT)) = ?', ('',)).fetchone()[0]
                        self.assertEqual(invalid,0,(table,col))

    def test_internal_cost_parameter_updates_common_technology_costs(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'data';clone(data)
            file=data/'parameters'/'costs.json';obj=json.loads(file.read_text())
            original=obj['parameters']['invest__direct_reduced_iron']['value']
            self.assertAlmostEqual(float(original),299.6656217)
            obj['parameters']['invest__direct_reduced_iron']['value']='381.1234'
            write_json(file,obj)
            for scen in ('basecase','all'):
                db=Path(d)/(scen+'.sqlite');build_one(data,scen,db)
                with closing(sqlite3.connect(db)) as c:
                    costs={row[0] for row in c.execute("SELECT cost FROM cost_invest WHERE tech='I_AMM_DRI'")}
                    self.assertIn(381.1234,costs)
                    self.assertNotIn(299.6656217,costs)
                    self.assertIn(352.5477903,{row[0] for row in c.execute("SELECT cost FROM cost_invest WHERE tech='I_ALG_CO'")})

    def test_emission_parameter_updates_only_emission_records(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'data';clone(data)
            file=data/'parameters'/'emissions.json';obj=json.loads(file.read_text())
            obj['parameters']['emission__electric_arc_furnace']['value']='266.0006905'
            write_json(file,obj)
            db=Path(d)/'new.sqlite';build_one(data,'basecase',db)
            with closing(sqlite3.connect(db)) as c:
                self.assertGreater(c.execute('SELECT COUNT(*) FROM emission_activity WHERE activity=266.0006905').fetchone()[0],0)
                self.assertAlmostEqual(c.execute("SELECT cost FROM cost_invest WHERE tech='I_AMM_DRI' LIMIT 1").fetchone()[0],299.6656217)

    def test_process_flow_change_updates_coefficients_not_costs(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'data';clone(data)
            file=data/'process_flows'/'dri_ng.csv'
            with file.open(newline='',encoding='utf-8') as h:rows=list(csv.DictReader(h))
            for row in rows:
                if row['direction']=='in' and row['flow_id']=='ng':row['amount']='0.48'
            with file.open('w',newline='',encoding='utf-8') as h:
                wr=csv.DictWriter(h,fieldnames=rows[0],lineterminator='\n');wr.writeheader();wr.writerows(rows)
            db=Path(d)/'new.sqlite';build_one(data,'basecase',db,enforce_reference_counts=True)
            with closing(sqlite3.connect(db)) as c:
                vals={row[0] for row in c.execute("SELECT efficiency FROM efficiency WHERE tech='I_AMM_DRI'")}
                self.assertEqual(len(vals),1)
                self.assertLess(next(iter(vals)),0.4416961131)
                self.assertAlmostEqual(c.execute("SELECT cost FROM cost_invest WHERE tech='I_AMM_DRI' LIMIT 1").fetchone()[0],299.6656217)

    def test_failed_build_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'data';clone(data)
            db=Path(d)/'last_good.sqlite';db.write_bytes(b'previous valid sqlite data placeholder')
            file=data/'parameters'/'costs.json';obj=json.loads(file.read_text());del obj['parameters']['invest__direct_reduced_iron'];write_json(file,obj)
            with self.assertRaisesRegex(ValueError,'undefined model parameter'):
                build_one(data,'basecase',db)
            self.assertEqual(db.read_bytes(),b'previous valid sqlite data placeholder')

    def test_row_count_enforcement_does_not_prevent_intentional_edit(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'data';clone(data)
            file=data/'inputs'/'entities.json';obj=json.loads(file.read_text());rules=obj['tables']['technology_label']['rules']
            new_rule=json.loads(json.dumps(rules[0]));new_rule['axes']['tech']=['I_TEST_NEW_TECH'];rules.append(new_rule)
            write_json(file,obj)
            db=Path(d)/'new.sqlite'
            result=build_one(data,'basecase',db)
            self.assertIn('technology_label',result['reference_row_count_differences'])
            with self.assertRaisesRegex(ValueError,'Reference row counts differ'):
                build_one(data,'basecase',db,enforce_reference_counts=True)
            self.assertTrue(db.exists())

    def test_network_all_bindings_and_passthrough_aliases(self):
        fake={'test_tech':{'in':{'a','b'},'out':{'x','y'}}}
        rule={'scenarios':'all','axes':{'tech':['test_tech'],'vintage':['2025'],'input_comm':'all','output_comm':'all'},'values':{'region':'ON'}}
        rows=list(expand_rule('efficiency',rule,{},fake,('2025',)))
        self.assertEqual(len(rows),4)
        self.assertEqual({(r['input_comm'],r['output_comm']) for r in rows},{('a','x'),('a','y'),('b','x'),('b','y')})
        flows=load_process_flows(DATA/'process_flows')
        ratios,_,split=computed('pass_through',flows['pass_through'],{'F_scrap':'generic'},
            {x:'generic' for x in ('one','two','three','four')})
        self.assertEqual(set(ratios.values()),{1.0})
        self.assertEqual(set(split.values()),{0.25})

    def test_active_years_expand_from_internal_model_periods(self):
        rule={'scenarios':'all','axes':{'tech':['tech_a'],'vintage':['2020','2030'],'period_policy':'from_vintage'},'values':{'region':'ON'}}
        rows=list(expand_rule('cost_fixed',rule,{}, {},('2025','2030','2035')))
        self.assertEqual({(x['vintage'],x['period']) for x in rows},
            {('2020','2025'),('2020','2030'),('2020','2035'),('2030','2030'),('2030','2035')})

    def test_no_external_model_inputs_or_table_catalog(self):
        self.assertFalse((DATA/'catalog').exists())
        self.assertFalse((DATA/'workbook_reference').exists())
        self.assertEqual(len(list((DATA/'inputs').glob('*.json'))),6)
        for folder in ('data','steel_builder','docs'):
            for path in (ROOT/folder).rglob('*'):
                if path.is_file() and path.suffix in ('.py','.json','.md','.csv'):
                    self.assertNotIn('steel-updated',path.read_text(encoding='utf-8').lower(),path.name)

if __name__=='__main__':unittest.main()
