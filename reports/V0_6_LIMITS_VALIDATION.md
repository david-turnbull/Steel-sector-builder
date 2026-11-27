# v0.6 Limit Integration — Database Validation

## Summary

This release refactors the **editable representation** of TEMOA limits without changing the resulting model data. Six nonempty limit table families have been migrated into `data/inputs/limits.json`; `data/parameters/limits.json` contains four shared capacity-to-activity ratios. The 80 basecase activity rows are now calculated from matching equality capacity constraints instead of copied as independent literal values. All input/output annual split coefficients remain derived from process flows. Other limit tables remain empty; no new scientific or policy limit is created.

Comparison against the internal **v0.5 uniform-efficiency and NULL-data-quality baseline** shows **0 changed tables out of 91** in each of the four scenarios. The standalone v0.5 file-content hash verification tool confirms this. The non-flow limit tables (`limit_activity`, `limit_capacity`, `limit_activity_share`, `limit_emission`) also match the four newly uploaded SQLite files exactly after normalizing blank optional data-quality entries to NULL.

## Populated table counts

| Scenario | Activity | Capacity | Activity share | Emission | Annual input split | Annual output split | Remaining foreign-key findings |
|---|---:|---:|---:|---:|---:|---:|---:|
| basecase | 80 | 90 | 15 | 0 | 500 | 330 | 4,210 |
| eaf | 0 | 40 | 15 | 0 | 850 | 440 | 6,562 |
| ccs | 0 | 40 | 15 | 4 | 660 | 330 | 5,672 |
| all | 0 | 40 | 15 | 0 | 1010 | 440 | 8,118 |

All 91 TEMOA tables are created for each scenario. All five `dq_*` foreign-key categories remain clean. The remaining foreign-key issues are inherited `time_period` and other source/reference problems and were **not** silently corrected. SQLite `PRAGMA integrity_check` is `ok` for all four.

## Key implementation details

- `data/inputs/limits.json`: 25 capacity rules, 8 derived activity rules (expanded to 80 activity rows), 3 activity-share rules, 1 emission-limit rule, 20 input-split relationship rules, 12 output-split relationship rules.
- `data/parameters/limits.json`: four editable multipliers, with separate lower and upper values for `I_ALG_EAF_PP` and the other seven finishing technologies.
- `steel_builder/model.py`: introduces a `capacity_multiplier` expression for the `limit_activity.activity` field. It looks up a capacity record by exact `region`, `period`, `tech_or_group`, `operator`, and `data_id`; a missing record fails the build. Literal activity values remain supported.
- `steel_builder/limits.py`: validates operators, numeric ranges, and conflicting lower/upper bounds. It does not make scientific assumptions about engineering units or plant utilization.
- `steel_builder/build.py`: calls limit validation before writing the generated SQLite file. Builds remain atomic and preserve prior outputs on failure.
- `docs/limits.md`: user-facing editing instructions and examples.

## Regression and edited-input tests

The 15 automated tests cover exact table-content reproduction, editing a capacity and common activity multipliers, rejected conflicting activity bounds, rejected missing capacity references, flow-derived coefficient recalculation, editable cost/emission parameters, and atomic build safety. All tests passed when the release was assembled.

## Scientific and modeling caveats

1. The activity/capacity ratios are *inferred from repeated model values*, **not** verified utilization assumptions. They currently reproduce the supplied data but should be reviewed before assigning a causal or physical interpretation.
2. Only the base case has explicit `limit_activity` rows. Do not apply them to EAF, CCS or All without an explicit model decision.
3. The CCS-only CO₂ upper limit has an unspecified unit in the source database; it remains unchanged.
4. The four uploaded SQLite files and the uniform-efficiency builder differ in their efficiency and annual split numbers because the builder uses the agreed formula. The limit integration does not alter that prior decision.
5. The databases still need TEMOA solver runs; database equivalence and unit tests alone do not prove model feasibility.
