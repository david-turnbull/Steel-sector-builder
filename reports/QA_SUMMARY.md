# Validation summary — 23 November 2026

## Structure and new coefficient policy

All four generated scenarios use the original 91 SQLite table definitions and maintain their original row counts and non-derived tables. The original reference SQLite efficiency values are **not** reproduced by the updated builder, because all efficiencies now follow one formula:

`efficiency = sum(output process flows) / sum(input process flows)`

The input and output annual splits are rebuilt from their respective mapped flow amounts. The formula is applied to **every** efficiency row, including the DRI/EAF cases that previously had a `legacy_paired` mode. `technology_modes.csv`, `legacy_factor`, `identity` and `--reference-values` have been removed.

A physical process flow may have several TEMOA output commodity aliases without representing several simultaneous physical products. `F_I_SCRAP` illustrates this: its 1-unit generic input and 1-unit generic physical output produce efficiency = 1 (rather than incorrectly counting four alternative mill destinations as four units of material).

## Source database issues preserved outside the coefficient calculation

| Scenario | SQLite tables | Integrity check | Existing FK findings in source |
|---|---:|---|---:|
| basecase | 91 | ok | 9,480 |
| eaf | 91 | ok | 18,257 |
| ccs | 91 | ok | 16,772 |
| all | 91 | ok | 25,028 |

## Substantive differences versus uploaded efficiencies

With a numerical difference threshold of `1e-6`, **efficiency** fields differ materially from the supplied source databases as follows:

| Scenario | Changed efficiency rows | Affected technologies |
|---|---:|---:|
| Base case | 0 | 0 |
| EAF | 195 | 11 |
| CCS | 0 | 0 |
| All pathways | 405 | 22 |

The remaining numerical differences across efficiency and split fields are generally rounding/precision changes. There are 88 unchanged tables per scenario, and the only changed tables are the three intended flow-derived coefficient tables. The all-pathways case contains some particularly large changes due to removal of legacy input-specific efficiencies (for example, a hydrogen DRI input/output coefficient of 9.523809524 is recalculated to 0.3875968992). See `material_efficiency_differences.json` for a per-technology record of affected rows and `derived_vs_uploaded.json` for a table-by-table comparison.

The builder does not fix pre-existing foreign-key errors. In the uploaded EAF scenario, 123 NG-DRI efficiency records had `0.287170233` rather than the `dri_ng.csv`-derived `0.441696113`; these values are replaced by the universal aggregate calculation.

## Review before deploying in CANOE/TEMOA

1. Confirm that the uniform aggregate efficiency rule produces the intended model behaviour for DRI-EAF / NG-DRI and H2-DRI when solving TEMOA (this is now the only implemented rule).
2. Decide how to put mixed energy/mass/volume flows on a suitable physical basis. Keeping the workbook's ratios is a compatibility choice, **not** a scientifically normalized energy efficiency.
3. Review the EAF scenario's NG-DRI coefficient correction (123 rows) against intended model behavior.
4. Fix referential-integrity issues as a separate schema task; investigate 2020-only `time_period`, vintage/period references, and non-null blank data-quality fields.
5. Run at least one TEMOA test case per scenario and review outputs, pathway choices, costs and emissions.
