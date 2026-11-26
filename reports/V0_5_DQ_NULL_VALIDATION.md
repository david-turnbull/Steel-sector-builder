# Steel Sector Builder v0.5 — SQL NULL Data-Quality Fix

## Change

- In all editable `data/inputs/*.json` input rules, unassigned `dq_cred`, `dq_geog`, `dq_struc`, `dq_tech` and `dq_time` ratings now use JSON `null` instead of `""` (1,436 blank rule/default fields corrected).
- The builder also normalizes future empty/whitespace-only `dq_*` input values to `None` before inserting into SQLite. A Python `None` is stored as SQL `NULL`. This rule does not change valid, explicit quality ratings or the keys of quality lookup tables.
- No SQL schema changes, process-flow coefficients, costs, scenario memberships, or non-quality values were modified. The four generated databases retain 91 tables each.
- Every build report now groups foreign-key violations as `data_quality`, `time_period` and `other`.

## Before/after comparison

| Scenario | v0.4 total FK issues | v0.4 DQ FK issues | v0.5 DQ FK issues | Remaining time-period FK issues | Remaining other FK issues | v0.5 total FK issues |
|---|---:|---:|---:|---:|---:|---:|
| Basecase | 9,480 | 5,270 | **0** | 4,195 | 15 | 4,210 |
| Eaf | 18,257 | 11,695 | **0** | 6,384 | 178 | 6,562 |
| Ccs | 16,772 | 11,100 | **0** | 5,258 | 414 | 5,672 |
| All | 25,028 | 16,910 | **0** | 7,579 | 539 | 8,118 |

The complete table contents of each v0.5 database were compared against the v0.4 ZIP source after normalizing only missing data-quality fields in that v0.4 reference. **All 91 tables per scenario matched, with zero unexpected differences.**

## Validation

- SQLite `PRAGMA integrity_check`: `ok` for all scenarios.
- SQLite `PRAGMA foreign_key_check`: **zero data-quality violations** in all scenarios.
- Automated tests: 10 passed, including normalization checks and full v0.5 table-hash comparisons.
- `python -m steel_builder.verify_reference`: 91/91 tables unchanged against v0.5 baseline for each scenario.
- A fresh TEMOA solver run has **not** been completed.

## Remaining FK problems (not addressed in this change)

The `time_period` table still lists only 2020, while model inputs reference operating years 2025–2045 and other vintages. Resolving this properly requires reviewing TEMOA period types and planning-horizon semantics, not merely adding arbitrary rows. In addition, some source and dataset IDs are unresolved in the corresponding lookup tables. Those cannot safely be fixed by setting every missing foreign key to `NULL`; the intended source and parent relationships need to be checked.

**This is a data-quality foreign-key fix, not a claim of complete referential integrity or TEMOA solvability.**
