# CANOE Steel Sector Builder v0.5 — editable model assumptions

Build **four standalone TEMOA v4 steel-sector SQLite databases** using editable source data **inside this package**. There are no external source files required during builds and **no per-table catalog CSVs**. The SQLite database tables are *generated outputs*, not files researchers must manually maintain.

The v0.5 build preserves the v0.4 model coefficients, assumptions and all non-data-quality fields. Missing `dq_*` ratings now use SQL `NULL` (instead of empty strings); this eliminates all data-quality foreign-key violations. Other inherited foreign-key findings, especially incomplete `time_period` references, remain for review. **End-to-end TEMOA optimization has not been tested.**

## Quick start

Requires Python 3.10+ (no third-party Python dependencies for normal builds).

```bash
python -m steel_builder.build
python -m steel_builder.build --scenario eaf
python -m unittest discover -s tests -v
python -m steel_builder.verify_reference
```

Rebuilt SQLite databases and JSON reports are written to `outputs/`. A failed build does **not** overwrite the previous working database. Use `--enforce-reference-counts` only when an exact regression rebuild is intended; deliberately adding technologies may change row counts.

## What to edit

| Desired change | Edit | Behaviour |
|---|---|---|
| Common investment, fixed and variable cost | `data/parameters/costs.json` | 31 **named numeric assumptions** reused by cost rules |
| Shared emission coefficient | `data/parameters/emissions.json` | 5 editable numeric factors reused by source emission rules |
| Input/output amounts and units | `data/process_flows/<process>.csv` | Efficiency and commodity splits recomputed automatically |
| Technology-to-process mapping | `data/mappings/technology.csv` | Reuses the physical process for many facility technologies |
| Technology commodity connections | `data/mappings/commodity_bindings.csv` | Defines input/output commodities; `all` network rules expand from bindings |
| Which cost applies to which technology | `data/inputs/economics.json` | Group membership, scenario selection, vintage/period schedules, units and source notes |
| Technology / commodity definition and labels | `data/inputs/entities.json` | Generated TEMOA `technology`, `commodity` and labeling rows |
| Network topology / vintage availability | `data/inputs/network.json` | Flow-based efficiency arcs and split-constraint templates |
| Existing capacity, demand, operational constraints | `data/inputs/operations.json` | Common assumptions and scenario-specific rules |
| Emission-activity mappings and emission caps | `data/inputs/emissions.json` | Application of emission factors and limits |
| Source attribution, time periods, model metadata | `data/inputs/model_settings.json` | TEMOA model metadata and provenance records |
| Period expansion used by shared annual costs | `data/parameters/model.json` | List of modeled operating periods |
| Scenario `data_id` and description | `data/scenarios/{basecase,eaf,ccs,all}.json` | Individual scenario outputs |

The 13 process-flow CSVs use just `direction, flow_id, amount, unit, notes`. There are **no source-sheet or cell references**. Costs, emissions, demand, capacity, constraints, process flows and source metadata are all maintained as inputs in this package.

## Example: change a shared cost

Open `data/parameters/costs.json`, locate `invest__direct_reduced_iron`, and update only its `value`:

```json
"invest__direct_reduced_iron": {
  "value": "299.6656217",
  "description": "Capital/investment cost — direct reduced iron",
  "examples": ["I_ALG_NG_DRI", "I_AMM_DRI"]
}
```

(The `examples` array in the actual file may contain more technologies; it is explanatory, **not** a selection rule.) Run `python -m steel_builder.build`. The updated value is used for **all investment cost rules referencing that parameter**. Units, currency bases and exact applicable technologies are in `data/inputs/economics.json`. To change **only one facility or scenario**, split the relevant rule in `economics.json` and create a separate named parameter; do not edit a shared factor unless all its uses should change.

## Example: edit process efficiency

Edit `data/process_flows/dri_ng.csv`. For each mapped technology, the builder calculates:

\[
\eta = \frac{\sum \text{distinct physical output flows}}{\sum \text{distinct physical input flows}},\qquad
s_i^{in}=\frac{I_i}{\sum I},\qquad s_j^{out}=\frac{O_j}{\sum O}.
\]

The same efficiency is written to each input-output pair of the technology. Repeated commodity aliases referencing the same physical flow are counted once in the efficiency total; their output/input split shares are calculated across the mapped commodity quantities. Note that the model's historical source values mix tonnes, GJ, hydrogen volumes and CCS units; this formula reproduces the **numerical model convention**, not a universally unit-consistent physical efficiency.

## How shared rules work

Each rule in the six `data/inputs/*.json` files defines a subset of scenarios, a group of technologies (or other axes), and their shared values. Example (illustrative):

```json
{
  "scenarios": "eaf|all",
  "axes": {"tech": ["I_ALG_NG_DRI", "I_DOF_NG_DRI"], "vintage": ["2025", "2030"]},
  "values": {"region": "ON", "cost": {"parameter": "invest__direct_reduced_iron"}, "units": "M$/MT DRI"}
}
```

The actual rules may include `notes`, `data_source` and data-quality fields; some fields are inherited from the per-table `defaults`. The builder validates each fully expanded record against the SQL schema. Supported axes include `tech`, `vintage`, `period`, `year_pairs`, and `period_policy: "from_vintage"`; network rules can use `input_comm: "all"` and `output_comm: "all"` to derive commodity combinations directly from the mapping.

Changing a scenario selection changes which rules apply, without duplicating shared records. **The four scenario configurations alone do not specify all differences:** scenario selection also appears explicitly on the model input rules.

## Adding a technology

1. Add its definition and optional label under `data/inputs/entities.json`.
2. Map it to an existing/new process in `data/mappings/technology.csv` and to its physical commodities in `commodity_bindings.csv`.
3. Add/extend its network rules under `data/inputs/network.json` (available vintages and optional split constraints). Use `"all"` to generate arcs from commodity bindings.
4. Assign its cost parameter(s) in `data/inputs/economics.json`. Add any new numeric assumptions in `data/parameters/costs.json`.
5. Update emissions, capacity and scenario constraints as needed. Build and validate the changed scenario(s).

The engine creates arcs from a *declared* network rule, but it does **not yet infer a complete steel technology network and all cost/capacity rules merely from the process CSV**. That remains an intentional limitation.

## Validation

- `python -m unittest discover -s tests -v` tests baseline matching, edits, flow calculations and failure handling.
- `python -m steel_builder.verify_reference` compares the outputs against frozen v0.5 hashes (identical to v0.4 except missing data-quality values normalized to SQL `NULL`). After a deliberate edit, hash differences are expected; the report identifies changed tables.
- `python -m steel_builder.build --enforce-reference-counts` rejects changes in table row counts.
- Every build checks SQLite `PRAGMA integrity_check`, reports foreign-key issues by category (`data_quality`, `time_period`, `other`), and normalizes unassigned `dq_*` ratings to SQL `NULL`. Existing numeric data-quality ratings are retained. Other foreign-key issues are reported, not silently repaired.

For more information see `docs/steel_sector.md` (scientific assumptions) and `docs/sector_builder_development.md` (implementation and future sectors).

## Data-quality (`dq_*`) fields and referential integrity (v0.5)

The five optional quality ratings are `dq_cred`, `dq_geog`, `dq_struc`, `dq_tech` and `dq_time`. **Use JSON `null` when a rating has not been assigned**, not `""`. For example:

```json
{
  "dq_cred": null,
  "dq_geog": null,
  "dq_struc": null,
  "dq_tech": null,
  "dq_time": null
}
```

For backwards compatibility, the builder automatically converts blank strings and whitespace-only values in these fields to SQLite `NULL` when generating records. Nonblank ratings and the `data_quality_*` lookup tables are preserved. v0.5 eliminates all foreign-key violations related to these five fields.

**Important:** Additional foreign-key problems remain because references to years in `time_period` and certain source/data-set IDs are unresolved. The builder reports them in each `outputs/*_build_report.json`. Do not interpret `integrity_check=ok` as proof of full foreign-key validity. See `reports/V0_5_DQ_NULL_VALIDATION.md`.
