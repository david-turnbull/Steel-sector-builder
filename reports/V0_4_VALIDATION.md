# Steel Sector Builder v0.4 — validation report

## Scope

The package is now self-contained. No external source document, pre-existing SQLite database, or database-table CSV catalog is loaded by the build command. The following files are the editable source model: `data/parameters/`, `data/inputs/`, `data/process_flows/`, `data/mappings/`, `data/scenarios/` and `data/schema.sql`.

## Consolidation

| Input | v0.3 | v0.4 |
|---|---:|---:|
| Per-table catalog CSVs | 38 | 0 |
| Scenario-specific full table CSVs | 0 | 0 |
| Purpose-based JSON input files | 0 | 6 |
| Source rule templates | 6,027 catalog rows | 1,014 model rules |
| Shared numerical cost parameters | repeated in cost rules | 31 named values |
| Shared numeric emission activity parameters | repeated in emission rules | 5 named values |
| Editable process-flow CSV files | 13 | 13 |
| Editable scenario JSON files | 4 | 4 |
| TEMOA SQLite tables per database | 91 | 91 |

The count of model rule templates includes source/label metadata and other independent rows that must remain explicit. The most repeated groups are investment, fixed and variable costs; technology/year combinations are generated from named rules rather than maintained row by row.

## Regression test

All four databases were built using `python -m steel_builder.build --enforce-reference-counts`. `python -m steel_builder.verify_reference` returned **zero changed tables** for each scenario compared with the previously validated v0.3 flow-derived database contents.

| Scenario | Tables compared | Changed tables | SQLite `integrity_check` | Foreign-key findings (inherited) |
|---|---:|---:|---|---:|
| Base case | 91 | 0 | ok | 9,480 |
| EAF | 91 | 0 | ok | 18,257 |
| CCS | 91 | 0 | ok | 16,772 |
| All pathways | 91 | 0 | ok | 25,028 |

The foreign-key findings are a property of the retained reference model data; the generator does not claim referential integrity is clean. A passing SQLite integrity check is a different test from foreign-key validation.

## Automated tests

`python -m unittest discover -s tests -v` passed **9 tests** covering:

- Exact 91-table baseline content checks for all four scenarios.
- Propagation of common investment parameter edits to the intended technologies/scenarios.
- Propagation of a shared emission factor edit.
- Flow edits updating efficiencies while leaving economic assumptions unchanged.
- Rejection of missing parameter references without overwriting prior output.
- Optional strict row-count detection when intentionally adding a model record.
- Network arc expansion from model commodity bindings, including aliased pass-through flows.
- Fixed-cost active-vintage period expansion from internal model settings.
- Independence from external model source artifacts.

## Not yet validated

- End-to-end TEMOA solve/feasibility and scenario-specific economic outputs.
- Scientific consistency of mixed-unit efficiency ratios.
- Data-source attribution, units, cost basis and currency-year transformations.
- Resolution of inherited foreign-key inconsistencies.
- Completeness of constraints when users create entirely new technology pathways.
