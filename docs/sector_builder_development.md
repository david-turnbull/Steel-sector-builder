# Development guide: Building data-driven CANOE sector packages

**Reference implementation:** CANOE Steel Sector Builder v0.4  
**Purpose:** Explain the architecture and a repeatable approach for other TEMOA sectors. This is independent of the steel scientific documentation and the user's README.

## 1. Architectural principle

A sector's source of truth should be **human-editable input assumptions within the package**. Avoid treating a generated SQLite database, a collection of mirrored table CSV files or an external source document as the master data. Let the Python builder translate model assumptions into TEMOA tables.

The steel implementation separates:

1. **Physical process definitions:** `data/process_flows/` CSVs (amount, direction and unit).
2. **Commodity topology:** `data/mappings/technology.csv` and `commodity_bindings.csv`.
3. **Shared numerical parameters:** `data/parameters/costs.json`, `emissions.json`, and global model periods.
4. **Source/model rules:** six `data/inputs/*.json` files grouped by purpose, not by individual SQL table.
5. **Scenarios:** four small configurations plus rule-level scenario membership.
6. **TEMOA schema and output:** a version-controlled `data/schema.sql`; generated SQLite is an artifact.

The implementation writes 91 existing TEMOA tables, but only 38 table types contain authored data. A sector package does not need an editable CSV for each of those tables; a small set of rules can produce many generated rows.

## 2. How the steel package was constructed

The initial steel model contained four scenario datasets. During the refactoring, the implementation was changed in stages:

1. Separate reusable process inputs from facility-specific technology/commodity names.
2. Compute every `efficiency` record using aggregate output/input totals and every annual input/output split using the corresponding side's flow proportions.
3. Find records identical across scenarios and consolidate their technology, vintage and period applicability.
4. Convert repeated yearly cost records into **shared cost rules**: rather than repeat a cost for each facility and planning period, an investment rule can apply a single cost parameter to a technology group and a set of vintages; fixed costs can use `period_policy: "from_vintage"`.
5. Generate technology input/output arcs and annual split rows from **declared network rules plus commodity bindings**, instead of storing one complete list of arc rows per scenario and vintage.
6. Centralize the 31 existing distinct cost numbers and 5 emission-activity numbers as named internal parameters. Preserve explicit units, data-source notes and scenario masks on the application rules.
7. Retain sector-specific constraints, capacities, demand, source metadata and definitions in purpose-based JSON inputs.
8. Rebuild all four databases and compare complete table contents against the last verified model baseline.

The result is a **reproducible declarative model generator**. The schema, inputs, mappings and parameter files are sufficient for rebuilding; neither an external spreadsheet nor the prior SQLite databases are runtime inputs.

## 3. Input file layout and editing conventions

```text
sector-builder/
├── data/
│   ├── schema.sql
│   ├── parameters/
│   │   ├── costs.json
│   │   ├── emissions.json
│   │   └── model.json
│   ├── process_flows/*.csv
│   ├── mappings/
│   │   ├── technology.csv
│   │   └── commodity_bindings.csv
│   ├── inputs/
│   │   ├── economics.json
│   │   ├── emissions.json
│   │   ├── operations.json
│   │   ├── network.json
│   │   ├── entities.json
│   │   └── model_settings.json
│   ├── scenarios/*.json
│   └── reference_*.json             # optional regression fixtures
├── steel_builder/
│   ├── model.py                     # JSON/rule expansion and SQL rows
│   ├── flows.py                     # physical flow calculations
│   ├── build.py                     # scenario build, validation, atomic output
│   └── verify_reference.py         # complete baseline hash comparison
├── tests/
├── docs/
└── outputs/                         # generated, not maintained by hand
```

**JSON conventions:**

- A top-level `tables` dictionary in each `data/inputs/*.json` maps TEMOA destination table names to rule collections. Table defaults are values common to every generated row of that table.
- Each rule has `scenarios` (pipe-separated scenario names), `axes` (sets of technologies/years/commodities to expand) and `values` (shared attributes).
- Numeric values in `values` may refer to a named parameter via `{"parameter":"invest__direct_reduced_iron"}`. The parameter's number is stored only in the corresponding `data/parameters/*.json` file.
- An axis like `"tech":["I_ALG_BF","I_DOF_BF"]` generates separate records for both facilities; `"vintage":["2025","2030"]` expands each permitted vintage.
- `"period_policy":"from_vintage"` creates fixed-cost operating-period records for periods greater than or equal to each vintage; `"year_pairs"` stores explicit vintage/period combinations where this simple rule is unsuitable.
- In network definitions, `"input_comm":"all"` and `"output_comm":"all"` use the technology's explicit commodity bindings. The Cartesian product defines eligible input/output efficiency arcs; `arc_pairs` can specify non-Cartesian edges.
- Nulls are JSON `null`, not an empty string. Empty strings are preserved deliberately where the legacy model distinguishes them.
- `${SCENARIO_DATA_ID}` is replaced during generation. Source IDs and `data_id` values are not silently rewritten otherwise.

## 4. Calculation and mapping rules

For a technology with mapped process flows (physical quantities, not duplicated aliases):

\[
\text{efficiency}=\frac{\sum \text{distinct output flows}}{\sum \text{distinct input flows}}
\]

For each mapped commodity:

\[
\text{input split}_i=\frac{I_i}{\sum_k I_k}, \qquad
\text{output split}_j=\frac{O_j}{\sum_l O_l}.
\]

The split denominators count each modeled commodity edge; the aggregate efficiency calculation counts distinct *physical* flow identifiers. This guards against inflating one import process into multiple physical outputs when it simply permits alternative routing. Each technology input/output pair receives the same aggregate efficiency. Values are rounded to ten decimal places when writing SQLite.

**Units:** Do not assume arbitrary mass, energy and volume values can be summed into a physical efficiency. This convention is a reproduction of the existing steel model's numerical coefficients. For new sectors, document a defensible reference unit, conversions and physical meaning first.

## 5. Worked example: changing a common cost

Suppose the cost of NG-DRI should change across every site and relevant scenario:

1. Open `data/parameters/costs.json`.
2. Locate `invest__direct_reduced_iron` and update its `value` using the units implied by its `economics.json` rules.
3. Run `python -m steel_builder.build`.
4. Check the output cost records and revised build report. Existing scenario masks and year combinations are reused automatically.

If a single facility needs a distinct cost, **do not edit the common parameter**. Create a new parameter, and split the existing application rule into disjoint technology/scenario groups. Add the one facility to the new rule with its distinct value.

If a technology has a time-dependent cost trajectory, use separate year- or vintage-scoped cost rules with named values. The engine should not invent interpolation unless the project defines and validates it.

## 6. Worked example: changing a process quantity

1. Open `data/process_flows/dri_ng.csv` and update the relevant numeric `amount` (keep `direction`, `flow_id` and `unit` correct).
2. Check the affected technology/process mappings in `data/mappings/technology.csv`.
3. Rebuild a scenario containing the technology with `python -m steel_builder.build --scenario basecase`.
4. Confirm that `efficiency` and, where present, `limit_tech_*_split_annual` changed as expected, but costs and metadata did not.

## 7. Adding a new sector: repeatable procedure

1. **Scope:** Define independent sector boundaries, model geography, years, demand commodity, existing capacity and pathways. Agree which interactions are imports/exports to other sectors.
2. **Physical technology definitions:** Write one process-flow CSV per distinct process, with named flows and explicit units. Reuse one process definition for multiple physical facilities wherever defensible.
3. **Technology and commodity records:** Populate `entities.json` and the technology/commodity mapping CSVs. The flow identifier in a binding must exist in its process CSV on the correct side.
4. **Network:** Define year/vintage availability in `network.json`. Use `"all"` edges where a Cartesian commodity network is correct, otherwise list explicit allowable pairs. Specify annual split constraints only where scientifically justified.
5. **Economics:** Define shared cost assumptions once in `parameters/costs.json`. Use `economics.json` to apply them by facility, vintage, operating period and scenario. Record units, currency year and sources; avoid untraceable default costs.
6. **Emissions:** Define source emissions factors and the process records they apply to; check sign conventions for captured CO₂.
7. **Other operations:** Set demand, existing capacities, activity/capacity relationships and any capacity, activity, share or emissions bounds. Explicitly model relevant scenario differences.
8. **Model-wide metadata:** Keep source citation records, units and data-quality fields where the TEMOA schema expects them. Use a consistent scenario `data_id`.
9. **Build:** Generate one simple scenario first; inspect table counts, key sample records and SQLite integrity; extend to the other scenarios.
10. **Test:** Add automated checks for formula logic, propagation of a shared cost edit, scenario filtering, model additions, output atomicity, referential integrity and actual TEMOA solve feasibility.
11. **Document:** Publish a separate scientific page describing sources, processes, model limitations, costs, constraints and the scope of validation.

## 8. Safeguards and validation

The builder runs `PRAGMA integrity_check` and collects findings from `PRAGMA foreign_key_check`. **These are different tests.** Starting with v0.5, blank optional `dq_*` quality ratings are normalized to SQL `NULL`, eliminating all data-quality foreign-key violations. Remaining `time_period`, source and dataset references are reported separately pending review. Future sectors should aim for zero foreign-key issues, subject to the specific TEMOA version's schema.

For regression comparison, `verify_reference.py` computes a SHA-256 content signature for every populated or empty table, based on all rows sorted independently of insertion order. This can confirm an internal refactor did not alter model semantics; it cannot establish scientific accuracy or solve feasibility. Update regression fixtures only after reviewing and approving intentional changes.

A failed build should not replace a previously working SQLite output. The builder constructs in a temporary file, performs its validations, then atomically replaces the target on success.

## 9. Current boundaries of reuse

**Reusable without changing model mathematics:** Shared parameter references, scenario rule expansion, JSON-to-SQL loading, simple year expansions, output atomicity, flow calculations, regression tests and basic reporting.

**Sector-specific adaptation required:** Physical processes, units, technology and commodity names, constraint assumptions, cost provenance, regional demand, existing capacities, emissions mappings and, where necessary, time handling.

**Not yet automated:** Scientific design of new processes from scratch; a full constraint-complete topology inferred solely from flow CSVs; unit conversions across incompatible commodities; automatic validation of source publications; physical mass/energy balance checks; TEMOA solver execution and performance evaluation.

This distinction matters: v0.4 is a substantially more maintainable steel-sector **model builder**, not a universal one-click TEMOA sector authoring system.
