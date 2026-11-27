# Editing TEMOA limit constraints — Steel builder v0.6

This document describes the **model input constraints** (not general process flow efficiency). All values are editable **inside the package**. No source spreadsheet or pre-existing SQLite file is needed to regenerate the scenarios.

## Where to edit

- `data/inputs/limits.json`: scenario membership; region, technology or group, modeled periods, relational operator, capacity, share and emissions limit; source and quality metadata. Contains the six populated `limit_*` rule families.
- `data/parameters/limits.json`: four reusable numerical ratios defining base-case activity bounds relative to *matching equality capacity bounds*.
- `data/process_flows/*.csv`: physical process inputs and outputs; builder computes the two annual input/output split limits using these, not from prefilled split numbers.
- `data/scenarios/{basecase,eaf,ccs,all}.json`: scenario data ID and name.

## Tables observed in uploaded steel models

| Table | Basecase | EAF | CCS | All | Values generated from |
|---|---:|---:|---:|---:|---|
| `limit_activity` | 80 | 0 | 0 | 0 | `limit_capacity` equality bound × named activity multiplier |
| `limit_capacity` | 90 | 40 | 40 | 40 | Explicit scenario limits |
| `limit_activity_share` | 15 | 15 | 15 | 15 | Explicit share constraints |
| `limit_emission` | 0 | 0 | 4 | 0 | Explicit emissions cap |
| `limit_tech_input_split_annual` | 500 | 850 | 660 | 1,010 | Process-flow input shares |
| `limit_tech_output_split_annual` | 330 | 440 | 330 | 440 | Process-flow output shares |

The 91-table TEMOA schema includes additional `limit_*` tables, but they have **zero records** in the supplied models. No extra model constraints have been invented.

## `limit_activity` calculation

The 80 base-case rows represent 8 finishing technologies × 5 years × 2 operators:

- `ge`: activity must be at least the number stored in `activity`.
- `le`: activity must not exceed the number stored in `activity`.
- `e`: capacity is set equal to the number stored in `limit_capacity.capacity` for the technologies with base-case activity limits.

For each matching plant and year, the generator evaluates:

```text
lower_activity = equal_capacity * activity_min_capacity_ratio
upper_activity = equal_capacity * activity_max_capacity_ratio
```

The look-up key is `(region, period, tech_or_group, data_id)` with `operator = 'e'`. If a capacity row is missing, the build fails safely. The activity output is rounded to 9 decimals to preserve the source database precision. **These multipliers were inferred from repeating values already present in the steel models.** They are not validated physical utilization rates or justified substitutes for independently measured output constraints.

| Technologies | Minimum ratio | Maximum ratio |
|---|---:|---:|
| `I_AMM_PP`, `I_DOF_EAF_PP`, `I_EVRAZ_PP`, `I_GERDAU_PP`, `I_IVACO_PP`, `I_STELCO_PP`, `I_TINTO_PP` | 0.855405663988 | 0.9088685181 |
| `I_ALG_EAF_PP` | 0.739810304054 | 0.786048448108 |

The ratios are stored only once in `data/parameters/limits.json`. Technology, region and period membership is defined in `data/inputs/limits.json`, so one can reassign a technology to another ratio group by changing the rule. The model does not assume these ratios apply to other sectors or scenarios.

### Example: change an Algoma capacity or activity assumption

In `data/inputs/limits.json`, find the `limit_capacity` rule with `"tech_or_group": ["I_ALG_EAF_PP"]`, and edit `"capacity": "3.7"` to `"capacity": "4.0"`. Rebuild the base case. The activity bounds will recalculate automatically. If only the upper activity multiplier should change, edit `activity_max_capacity_ratio__algoma` in `data/parameters/limits.json`. This does **not** change the capacity limit or cost assumptions.

A limit can instead be entered independently from a capacity constraint by replacing the activity expression with a literal value, such as:

```json
"activity": "2.9"
```

Or it may be tied to equal capacity through the new expression:

```json
"activity": {
  "capacity_multiplier": {
    "parameter": "activity_max_capacity_ratio__algoma",
    "capacity_operator": "e"
  }
}
```

Literal activity bounds are only appropriate where the technology and units have been reviewed. The solver sees the generated limits, not the source expressions.

## Other model-specific limits

**Capacity (`limit_capacity`).** The base case contains 90 rows, including technology closures and plant-level equality limits. Other scenarios have 40 capacity limit rows each; inspect the operators when adapting them. Do not interpret all capacities as equalities.

**Activity share (`limit_activity_share`).** Each scenario contains 15 constraints: in Ontario, `I_DOF_BOF <= 0` of group `I_DOF_PROCESS`, `I_DOF_S_EAF >= 0.36`, and `I_DOF_D_EAF >= 0.64`, for 2025, 2030, 2035, 2040, 2045. These are binding share assumptions, not values calculated from flows. If modifying the plant configuration, review the `tech_group` and its membership as well.

**Emissions (`limit_emission`).** Only CCS has Ontario `co2` upper-limit rows, `7000` in 2030–2045. No physical units are filled in those records; the data-source and scenario metadata are carried forward from the supplied model rather than inferred. The All scenario is not automatically assigned this cap.

**Flow shares (`limit_tech_input_split_annual` and `limit_tech_output_split_annual`).** The number of rows comes from the mappings and rule membership; their numerical proportions are recalculated from the process-flow quantities in every build. Use the process-flow CSV to change a split, not the generated SQLite.

## Validation and caveats

Run:

```bash
python -m steel_builder.build
python -m unittest discover -s tests -v
python -m steel_builder.verify_reference
```

The build checks that all 91 tables exist, generates and checks every populated limit table, validates operators and numeric ranges, and rejects contradictory minimum/maximum activity/capacity bounds. It also runs SQLite integrity and foreign-key checks. Existing time-period and source-reference violations are reported rather than silently repaired. Data-quality `dq_*` blanks are converted to SQL `NULL`.

The v0.6 outputs were compared against **all 91 tables** in the preceding v0.5 builder; all four scenarios matched exactly. The new editable structure therefore changes *how values are maintained*, not the current model results. **TEMOA optimization solves have not been run**, and the scientific justification for the activity multipliers and emissions cap remains subject to review.
