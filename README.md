# CANOE Steel sector — reproducible CSV → SQLite builder

This project converts the *Steel-Updated.xlsx* process-flow information into editable CSV files and rebuilds the four supplied TEMOA schema v4 SQLite scenarios:

| Scenario | Output |
|---|---|
| Base case | `outputs/CANOE_steel_basecase.sqlite` |
| EAF | `outputs/CANOE_steel_eaf.sqlite` |
| CCS | `outputs/CANOE_steel_ccs.sqlite` |
| All pathways | `outputs/CANOE_steel_all.sqlite` |

**Status:** working prototype with uniform flow-derived efficiencies, structurally checked against all four uploaded reference databases. Python 3.10+; **no third-party Python dependencies** for building. Use generated databases for review and run TEMOA scenarios only after scientific/solver validation.

## Quick start

From the **project folder** (`steel-sector-builder/`):

```bash
python -m steel_builder.build
```

This generates all four SQLite files in `outputs/`. It recomputes the `efficiency`, `limit_tech_input_split_annual`, and `limit_tech_output_split_annual` fields based on process-flow CSVs, while preserving the other CSV-sourced data.

To regenerate only one scenario:

```bash
python -m steel_builder.build --scenario eaf
```

**All builds use the new efficiency rule.** There is no `--reference-values` option: original coefficient snapshots remain under `data/scenarios/<scenario>/` for audit purposes, but they are always replaced with the flow-derived efficiencies and splits in generated SQLite files. All 91 original tables remain structurally preserved.

To run tests:

```bash
python -m unittest discover -s tests -v
```

On Windows, use `py -m steel_builder.build` if `python` isn't on PATH. No need to install the package when the working directory is this folder.

## Workflow and file layout

```text
data/
  process_flows/              # EDIT: 13 process definitions, one CSV per process
    coke_oven.csv             # input/output flow amounts and units
    blast_furnace.csv
    basic_oxygen_furnace.csv
    dri_ng.csv, dri_h2.csv, dri_eaf.csv, scrap_eaf.csv
    powerplant.csv, electrolyser.csv, postprocessing.csv
    ccs_90.csv, ccs_99.csv, pass_through.csv
  mappings/
    technology.csv            # technology -> shared process (no efficiency overrides)
    commodity_bindings.csv    # commodity code -> process-flow name
  workbook_reference/         # Archive: source-sheet snapshots, workbook costs and references
    snapshots/*.csv            # All nonempty workbook sheets exported as cell-value CSVs
    process_costs_from_workbook.csv
    reference_sources.csv
  scenarios/
    basecase/*.csv            # All nonempty original SQLite tables as editable CSVs
    eaf/*.csv
    ccs/*.csv
    all/*.csv
  schema.sql                  # Schema v4 extracted from the supplied databases
  reference_row_counts.json  # Reference row counts for 91 tables per scenario
steel_builder/
  build.py                    # CSV -> SQLite, with derived calculations
  convert_workbook.py        # Optional cached Excel -> fresh flow CSV conversion
  export_workbook_reference.py # Optional full source-sheet/cost/reference CSV export
  seed_references.py         # Initial migration from four original SQLite files
  audit.py                   # Compare with original SQLite files, if available
  flows.py                   # Process mappings and calculation rules
  xlsx_reader.py             # Standard-library, read-only XLSX cached-value reader
outputs/                     # Four prebuilt SQLite files and JSON build reports
reports/                     # Validation/audit notes
```

## Editing the flows (normal workflow)

1. Open `data/process_flows/dri_eaf.csv` or another process CSV in Excel/text editor.
2. Change the `amount` for an existing input or output, keeping `flow_id`, `direction`, and the expected units intact.
3. Run `python -m steel_builder.build` (or `--scenario all`).
4. Read the scenario's `outputs/<scenario>_build_report.json`; examine `efficiency`, input splits, and output splits in SQLite with DB Browser for SQLite or Python.
5. Compare results and run a TEMOA model validation before publishing.

Example `dri_eaf.csv` structure:

```csv
direction,flow_id,amount,unit,source_sheet,source_cell,notes
in,dri,1.01,t,DRI-EAF,B4,Reference workbook
in,elc,2.5128,GJ,DRI-EAF,B5,Reference workbook
out,steel,1,t,DRI-EAF,B9,Reference workbook
out,slag,0.011643296952,t,DRI-EAF,B10,Reference workbook
```

**There is a single canonical value per process flow**; the same values are applied to different companies through `commodity_bindings.csv`, rather than repeatedly copy/pasting the flow amounts for every steel facility and period.

### What is recomputed?

For a technology's input amounts \(I_i\) and output amounts \(O_j\):

\[ \eta = \frac{\sum_j O_j}{\sum_i I_i} \]

\[ s^{in}_i = \frac{I_i}{\sum_k I_k}, \quad s^{out}_j = \frac{O_j}{\sum_l O_l} \]

These values populate existing rows in:

- `efficiency.efficiency` (one row for each input × output commodity pair and vintage);
- `limit_tech_input_split_annual.proportion` (one row for each constrained input, period, operator);
- `limit_tech_output_split_annual.proportion` (one row for each constrained output, period, operator).

No new rows, new technologies, new period combinations or new constraints are automatically invented. Use the matching scenario CSV and mapping CSV when expanding the technology network.

The generated constraints use the *existing* `operator` values (mostly `ge`). The code does **not** change them to `eq`, or enforce that new technologies must have both split tables.

### Universal efficiency rule (no legacy exceptions)

For **all technologies**, including NG-DRI, H2-DRI, DRI-EAF, scrap EAF, post-processing, CCS and import/transfer links:

- `efficiency.efficiency = sum(distinct physical output flows) / sum(distinct physical input flows)` for every existing input/output pair;
- `limit_tech_input_split_annual.proportion = input amount / sum(mapped input amounts)`;
- `limit_tech_output_split_annual.proportion = output amount / sum(mapped output amounts)`.

The sums are computed over flows actually represented by that technology, not all rows in a source worksheet. Multiple TEMOA commodity aliases for **the same** physical flow are not multiplied when computing efficiency. For example, `F_I_SCRAP` is a generic one-unit supply link that can route to one of four alternative mill outputs: the source flow contains one physical output of 1, so its aggregate efficiency remains **1**, not **4**. Its alternatives are not four simultaneous physical outputs. No `technology_modes.csv`, `legacy_paired`, `identity` or per-pair factor is applied.

There is no backward-compatible switch to legacy efficiencies in the generator. Archived source CSVs can still be used to compare outcomes, but cannot override the universal calculation. **Warning:** the new formula makes substantial numerical changes in the EAF (195 rows) and All (405 rows) scenarios compared with the uploaded databases; see `reports/material_efficiency_differences.json`. These changes are intentional and require a TEMOA solve before production use.

### Scenario parameters, costs and emissions

All non-flow information stays in **scenario-specific** table CSV files, preserving the original record columns, notes, data source, dates, data IDs and constraints. Examples:

| Purpose | Where to edit |
|---|---|
| Investment costs | `data/scenarios/all/cost_invest.csv` |
| Fixed / variable costs | `cost_fixed.csv`, `cost_variable.csv` |
| Demand | `demand.csv` |
| Existing capacity | `existing_capacity.csv` |
| Technology/commodity definitions | `technology.csv`, `commodity.csv`, plus corresponding `*_label.csv` |
| Emissions coefficients | `emission_activity.csv` |
| Capacity and activity constraints | `limit_capacity.csv`, `limit_activity_share.csv` |
| Time periods, region and reference metadata | `time_period.csv`, `region.csv`, `metadata.csv` |

Each scenario is currently independent. Editing an investment-cost CSV in `all/` does **not** automatically update `basecase/`, `ccs/` or `eaf/`; common process-flow edits **do** propagate to all scenarios.

The original SQLite values remain archived in the per-scenario CSVs for audit comparisons. Their efficiency and split fields are **always replaced** by the flow-derived values during building.

### Optional: resplit an updated workbook into process CSVs

The workbook need not be present to generate SQLite databases. If updated `.xlsx` data are supplied, they can be converted using the cached formula values in that workbook:

```bash
python -m steel_builder.convert_workbook "../Steel-Updated.xlsx" --data data/process_flows --overwrite
```

**Warning:** `--overwrite` replaces all process CSV edits, including comments. The conversion is intentionally cell-mapped to the specific supplied workbook version; if sheets or cell addresses change, review `steel_builder/flows.py` first. The read-only XLSX reader does not recalculate formulas; open and save in Excel so calculated values are cached before converting.

### Optional: export the rest of the workbook to CSV

The initial migration also includes **14 full worksheet snapshots**, **a structured cost/opex table**, and **a citation/reference table** under `data/workbook_reference/`. The `Diagrams` worksheet contains visual objects rather than tabular cell data, so it is not exported into a CSV. Re-export these after revising the workbook:

```bash
python -m steel_builder.export_workbook_reference "../Steel-Updated.xlsx" --output data/workbook_reference
```

These are **traceable reference files**, not a second source of truth. The builder currently derives flow ratios from `process_flows/`; cost and emissions inputs are kept in the editable `scenarios/<name>/cost_*.csv` and `emission_activity.csv`. This avoids silently overwriting scenario-specific assumptions or cost conventions from a single workbook. You can use `process_costs_from_workbook.csv` to audit and manually reconcile cost tables.

### Optional: re-export the original SQLite references

If all four original SQLite databases are available in a folder:

```bash
python -m steel_builder.seed_references --reference-folder .. --root .
python -m steel_builder.audit --references .. --outputs outputs --report reports/diff.json
```

The `seed_references` command overwrites the scenario CSV snapshots and mappings, so do not run it after making edits without versioning or backing up the CSVs.

## Scientific/model-quality warnings

1. **Mixed units:** Workbook v4 sums quantities such as tonnes, GJ and thousands of cubic metres (and uses fraction-like CCS outputs). The above ratio reproduces its **numeric model convention**, not a thermodynamic/material efficiency. For the next major revision, consider a deliberately selected reference commodity or energy-equivalent conversion before summing flows. The `unit` column is intentionally retained for that review.
2. **Emissions are not extra material outputs:** `Scrap-EAF` includes a CO₂ calculation in row 15 with a different scaling/unit. Its steel and slag quantities are process outputs; CO₂ coefficients remain in `emission_activity.csv`. Adding row 15 to the process outputs would produce a nonsensical `sum(out)/sum(in)`.
3. **Legacy efficiency definitions are removed.** Every efficiency uses the aggregate sum(outputs)/sum(inputs), including DRI-EAF, NG-DRI and H2-DRI pathways.
4. **EAF scenario anomaly:** The supplied `CANOE_steel_eaf.sqlite` has 123 natural-gas DRI efficiency rows set to `0.287170233`, consistent with the DRI-EAF process coefficient, rather than the `dri_ng.csv` calculation `0.441696113`. The builder recalculates those 123 records alongside every other efficiency row; legacy values cannot be generated with the standard build. Confirm the intended physical/system convention before treating the new EAF scenario as the published scenario.
5. **Pre-existing foreign-key failures:** The source SQLite files have thousands of `PRAGMA foreign_key_check` findings, chiefly because `time_period` contains only 2020 while other tables reference later years, and because some blank data-quality labels are not valid FK values. The generator preserves the source schema/content and imports with FK enforcement disabled. This is **not** a claim of relational integrity; address this in a separate schema migration with TEMOA compatibility tests rather than altering source data silently.
6. **No end-to-end solver test yet:** SQLite structural integrity checks pass and unchanged reference tables remain intact, but no optimization run is included here. Before merging these outputs into CANOE, run Temoa smoke tests and confirm production/emissions balances and expected cost outcomes.
7. **Editing mappings:** If you add/remove material streams, you must update `commodity_bindings.csv`, the technology/network rows in the relevant scenario CSVs, and applicable derived-constraint row definitions. The builder is not a graph-generation system that decides feasible new steel technologies automatically.
8. **NULL vs empty string:** To preserve exact reference rows, an explicit `\N` in scenario CSVs represents SQLite `NULL`; an empty CSV field represents `''`. Do not replace every `\N` with a blank string during CSV edits.

See `reports/QA_SUMMARY.md` for reference comparison details and recommended follow-up decisions.
