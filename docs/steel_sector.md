# Steel sector: data sources, assumptions and technology representation

**Model:** CANOE high-resolution steel sector (TEMOA schema v4)  
**Status:** Prototype sector dataset; technical and scientific validation pending  
**Implementation:** Standalone `Steel` sector, not yet integrated into the general industry-sector pipeline  
**Source dataset:** `Steel-Updated.xlsx` and four supplied steel scenario SQLite databases  
**Last documentation review:** 26 November 2026

## 1. Scope and modelling approach

This module represents steel production as a network of technologies that consume and produce commodities. It includes conventional blast-furnace/basic-oxygen-furnace steelmaking, electric-arc-furnace (EAF) routes, natural-gas and hydrogen direct reduction, site power generation, post-processing, and optional carbon capture and storage (CCS). Technology and commodity names follow the existing CANOE/TEMOA schema.

The steel dataset is **separate from the general `Industry` sector** for now. Four alternative scenario databases are generated from a common library of process flows and scenario-specific records. This separation makes it possible to evaluate the steel network before linking it to the remainder of CANOE. It does not imply that energy supply, commodity imports or cross-sector interactions have been fully integrated or validated.

The principal production chains are:

```text
Iron ore / pellets + coal → coke oven → blast furnace → basic oxygen furnace ┐
                                                                       ├→ post-processing → rolled steel
Iron pellets + natural gas or H₂ → direct reduction → DRI-EAF ───────────┤
Scrap + electricity → scrap EAF ───────────────────────────────────────────┘

Additional technologies: onsite power generation, H₂ electrolysis,
import/supply links, and optional 90% or 99% CCS technologies.
```

These are conceptual chains. Actual feasible connections depend on the technology/commodity pairs in each scenario's SQLite tables; the builder does not infer new links.

## 2. Geographic and temporal coverage

The supplied scenario files contain three regions: **Ontario (ON), Quebec (QC) and Saskatchewan (SK)**. They are not a complete representation of Canadian steel production outside these regions.

- **Existing-capacity vintage:** 2020 in the supplied `existing_capacity` records.
- **Demand periods:** 2025, 2030, 2035, 2040 and 2045, in five-year steps.
- **Demand commodity:** `I_rolled_steel`.
- **Demand assumption:** fixed at each region's 2025 value throughout the modelled demand periods. The source rows say these values were estimated from the average of the preceding ten years of steel production, allocated provincially according to capacity. The demand rows cite [Trading Economics: Canada steel production](https://tradingeconomics.com/canada/steel-production). This demand construction has not been independently recalculated in the CSV builder.

| Region | Rolled steel demand in each modelled period | Units in SQLite |
|---|---:|---|
| Ontario | 9.499992923 | MT |
| Quebec | 2.478259023 | MT |
| Saskatchewan | 0.991303609 | MT |
| **Total** | **12.969555555** | **MT** |

Here `MT` is the label used in the source database. The demand figures are model inputs, not forecasts produced by the builder. Other model data may specify different production, activity, capacity or emission units; always inspect the table's `units` field.

## 3. Model technologies

The underlying source workbook is separated into **13 process-flow CSV definitions** (12 workbook-derived process variants plus one synthetic pass-through definition). The technology-to-process assignment is in `data/mappings/technology.csv`; the mapping from technology-specific commodity names to physical flows is in `data/mappings/commodity_bindings.csv`.

| Process / CSV | Main inputs | Main outputs | Source reference(s) |
|---|---|---|---|
| Coke oven — `coke_oven.csv` | Coal, coke-oven gas, blast-furnace gas, electricity | Coke, coke-oven gas | S1 |
| Blast furnace — `blast_furnace.csv` | Iron pellets, iron ore, coke, electricity, blast-furnace gas | Pig iron, blast-furnace gas | S8 |
| Basic oxygen furnace — `basic_oxygen_furnace.csv` | Home scrap, scrap, pig iron, electricity | Liquid/crude steel, slag streams, BOF gas | S8 |
| Natural-gas DRI — `dri_ng.csv` | Iron pellets, natural gas, electricity | Direct-reduced iron (DRI) | S2 |
| Hydrogen DRI — `dri_h2.csv` | Iron pellets, natural gas, electricity, hydrogen | DRI | S2 |
| DRI-fed EAF — `dri_eaf.csv` | DRI, electricity | Crude steel, slag | S2 |
| Scrap-fed EAF — `scrap_eaf.csv` | Scrap, electricity | Crude steel, slag | S3 |
| Post-processing — `postprocessing.csv` | Liquid/crude steel, electricity | Rolled steel, home scrap | S8 |
| Onsite power — `powerplant.csv` | Blast-furnace gas, BOF gas | Electricity | S6 |
| Electrolyser — `electrolyser.csv` | Electricity | Hydrogen | S7 |
| 90% CCS — `ccs_90.csv` | Electricity, natural gas | Captured CO₂ stream, using a 0.90 capture fraction | S10 |
| 99% CCS — `ccs_99.csv` | Electricity, natural gas | Captured CO₂ stream, using a 0.99 capture fraction | S10 |
| Import / transfer — `pass_through.csv` | One generic input | One generic output | Builder convention; not taken from a workbook process sheet |

These are **shared process definitions**, not separate unique process intensities for every plant. Facility-specific technologies can be mapped to the same process, with different commodity aliases and scenario-specific costs, capacities and constraints.

### Technology and commodity naming

Most steelmaking technology identifiers start with `I_` and contain a facility code such as `ALG`, `DOF`, `AMM`, `EVRAZ`, `GERDAU`, `IVACO`, `STELCO` or `TINTO`. The suffix generally identifies the process: for example, `_BF` (blast furnace), `_BOF` (basic oxygen furnace), `_CO` (coke oven), `_NG_DRI` or `_DRI` (natural-gas DRI), `_H2_DRI`, `_D_EAF`, `_S_EAF`, `_PP`, `_PPLANT`, `_H2_ELEC`, `_CCS_90` and `_CCS_99`. Plain `_EAF` is mapped according to the associated input commodities; it is **not** universally synonymous with one feedstock route.

`F_` technologies serve as import, supply or routing links. The authoritative technology/process relationship is **the mapping CSV**, not a naming heuristic. Some commodities are deliberately local to a facility (for example, site-specific coke, gas, crude steel or scrap), while other resources are shared across multiple technologies.

The model includes co-products and internal recirculation where the source network defines them: coke-oven gas, blast-furnace gas, BOF gas, slag and home scrap. Their effect on the optimization depends on their explicitly defined commodity links and constraints.

## 4. Flow-derived efficiencies and technology splits

All technologies use the **same new aggregate efficiency rule**. For a technology with represented physical input flows \(I_i\) and physical output flows \(O_j\):

\[
\eta = \frac{\sum_j O_j}{\sum_i I_i}
\]

The input and output split proportions are:

\[
s_i^{\mathrm{in}} = \frac{I_i}{\sum_k I_k}
\qquad
s_j^{\mathrm{out}} = \frac{O_j}{\sum_l O_l}
\]

The builder writes the aggregate `efficiency` value into **every existing input/output commodity pair** for that technology and writes the applicable proportions into existing rows in `limit_tech_input_split_annual` and `limit_tech_output_split_annual`. It does **not** use older individual-input, pairwise, or identity-efficiency exceptions.

When multiple alternative TEMOA commodity aliases represent **the same physical flow**, that physical flow is counted **once** for the efficiency numerator or denominator. For instance, a single generic scrap link may connect to several alternative mill destinations without generating several units of physical scrap. The split ratios, however, are calculated over the **mapped commodity quantities** used in those split rows; this distinction matters for technology aliases.

**Worked example — DRI-fed EAF.** The process-flow CSV specifies 1.01 tonnes DRI and 2.5128 GJ electricity as numeric inputs, and 1 tonne crude steel plus approximately 0.0116433 tonnes slag as numeric outputs:

\[
\eta_{\mathrm{DRI\text{-}EAF}}
= \frac{1 + 0.0116433}{1.01 + 2.5128}
\approx 0.287170233
\]

The input proportions are approximately 0.286704 (DRI) and 0.713296 (electricity); output proportions are approximately 0.988491 (crude steel) and 0.011509 (slag).

> **Important limitation:** The source workbook and builder sum numerical quantities with **different units** (tonnes, GJ, hydrogen volumes and, for CCS, energy-per-captured-CO₂ and capture fractions). Thus, these values follow the workbook's **model coefficient convention**; they should **not** be interpreted as dimensionless physical, mass-based or thermodynamic efficiencies. A later scientific revision should normalize onto a defined reference unit if physical efficiencies are required.

The generated annual split constraints retain the **original SQLite `operator` values** (in these files, typically `ge`, meaning lower bounds). Computing a proportion does not automatically impose an equality constraint or change the existing feasible set in any other way. The generator also does not add missing split constraints or new input/output commodity pairs.

### Emissions handling

The builder does not treat calculated CO₂ emissions as a further steelmaking material output. In particular, the `Scrap-EAF` workbook contains a separate CO₂ calculation that is **excluded** from the process-flow output numerator. Emissions coefficients reside in the scenario's `emission_activity.csv`; they are not recalculated from the process flows. The capture technologies and their represented captured-CO₂ streams are separate cases using `ccs_90.csv` and `ccs_99.csv`.

## 5. Scenarios and constraints

| Scenario | Generated database | Representation |
|---|---|---|
| **Base case** | `CANOE_steel_basecase.sqlite` | Conventional and existing steel routes; no modelled CCS or H₂-DRI/electrolysis technologies in the reference scenario. Includes `limit_activity` records absent from the other three supplied scenarios. |
| **EAF** | `CANOE_steel_eaf.sqlite` | Expanded electric/DRI technology options, including hydrogen DRI and onsite electrolyser technologies; no CCS technology records. |
| **CCS** | `CANOE_steel_ccs.sqlite` | Conventional routes plus 90% and 99% CCS options; no modelled H₂-DRI/electrolysis technology records. |
| **All pathways** | `CANOE_steel_all.sqlite` | The combined technology option set, including EAF/DRI, hydrogen and CCS routes. |

Scenario differences extend beyond the available technology list: the reference CSVs contain distinct investment/fixed/variable costs, existing capacity, capacity ceilings, activity shares, demand, emissions and other metadata. These are **independent datasets**. Changing a process flow updates every scenario using it; changing, for example, `data/scenarios/eaf/cost_invest.csv` does not update the other scenarios.

The supplied **CCS scenario alone** contains an explicit `limit_emission` constraint of `co2 <= 7000` for **Ontario** in **2030, 2035, 2040 and 2045**. The `units` field on these particular rows is blank/NULL, so the numerical limit should not be assigned a physical unit without further verification. The presence of CCS technologies in the **All pathways** case does **not** by itself mean it inherits the CCS case's emission cap.

The uploaded `limit_activity_share` records also constrain the relative operation of particular facility/process groups (for example, Dofasco's BOF, scrap-EAF and DRI-EAF shares). Such constraints are **explicit scenario assumptions**, not automatically derived from the flow workbook. Inspect the scenario CSVs before interpreting a run as a technology-neutral optimization.

## 6. Costs, emissions, capacity and other assumptions

These values are **retained from the supplied scenario databases** and are **not** regenerated from the flow workbook by the current builder:

| Input or assumption | Where to inspect/edit | Provenance or current treatment |
|---|---|---|
| Investment cost | `data/scenarios/<scenario>/cost_invest.csv` | Scenario records with unit and currency/basis notes; some entries say converted from 2010 EUR to 2022 CAD. |
| Fixed and variable operating costs | `cost_fixed.csv`, `cost_variable.csv` | Scenario records; review individual `units`, `notes` and `data_source` fields. |
| Existing steel capacity | `existing_capacity.csv` | 2020-vintage records; source catalogue notes Global Energy Monitor and some mass-balance extrapolation. |
| Capacity-to-activity conversion | `capacity_to_activity.csv` | Explicit technology coefficients, including conversions scaled to output units. |
| Demand | `demand.csv` | Fixed regional rolled-steel demand across 2025–2045, as described above. |
| Emissions factors | `emission_activity.csv` | Original per-technology input/output/vintage emissions activity records; not flow-derived. |
| Limits and group shares | `limit_capacity.csv`, `limit_activity.csv`, `limit_activity_share.csv`, and any `limit_emission.csv` | Scenario-defined constraints; absent files/tables may be empty. |
| Units and source references | Each table's `units`, `notes`, `data_source`, `data_id` and DQI fields | Retained with existing data, not automatically reconciled or re-sourced. |

The workbook reference export also contains entries marked **"Assuming to be 100"** for *scrap variable cost*, *iron pellets* and *iron ore price*, each annotated **"To be replaced by Ola"**. These are source-workbook placeholders, **not proof** that every current scenario CSV still uses 100. Current cost records may differ; review the active scenario tables individually before interpreting or publishing price assumptions.

**Provenance review needed:** The source catalogue describes `S9` as an IEA-ETSAP technology-cost reference and `S4` as World Steel Association production statistics, but at least some investment-cost rows are labelled `data_source = S4`. Those row-level labels should be reconciled before a documentation or model release. The builder preserves the labels as supplied; it does not assume they are correct.

## 7. Data sources

The following references come from the workbook's *Content and References* sheet and/or the SQLite `data_source` table. These are **recorded source attributions**, not a claim that all underlying numbers have been independently reproduced against the publications.

| Code | Source recorded in the model | Intended use recorded in source metadata |
|---|---|---|
| **S1** | IEAGHG (2013), *Iron and Steel CCS Study (Techno-Economics Integrated Steel Mill).* | Coke-oven process data. |
| **S2** | Azimi & van der Spek (2025), [*Prospective life cycle assessment suggests direct reduced iron is the most sustainable pathway to net-zero steelmaking*](https://doi.org/10.1021/acs.iecr.4c03321); Nurdiawati et al. (2023), *Towards Fossil-Free Steel: Life Cycle Assessment of Biosyngas-Based DRI Production Process*; IEAGHG (2013). | NG-DRI, H₂-DRI, and DRI-EAF process data. |
| **S3** | Burchart-Korol (2013), [*Life cycle assessment of steel production in Poland*](https://doi.org/10.1016/j.jclepro.2013.04.031); van Wortswinkel & Nijs (2010), [IEA-ETSAP *Iron and Steel* technology brief](https://iea-etsap.org/E-TechDS/PDF/I02-Iron&Steel-GS-AD-gct.pdf). | Scrap EAF. |
| **S4** | World Steel Association (2026), [*World Steel in Figures 2026*](https://worldsteel.org/data/world-steel-in-figures/world-steel-in-figures-2026/). | Historical production context and projection work. |
| **S5** | Global Energy Monitor (2026), [*Global Iron and Steel Tracker*, September 2026 v1](https://globalenergymonitor.org/projects/global-iron-steel-tracker/). | Existing capacities; some unspecified units extrapolated using mass balance. |
| **S6** | Rechberger et al. (2020), [*Green Hydrogen-Based Direct Reduction for Low-Carbon Steelmaking*](https://doi.org/10.1002/srin.202000110). | Onsite powerplant data. |
| **S7** | Internal work of the Sleep group (unpublished in the supplied metadata). | Electrolyser assumptions; source metadata says publication information will be added later. |
| **S8** | Azimi & van der Spek (2025); Nurdiawati et al. (2023); IEAGHG (2013). | Blast furnace, BOF and post-processing process data. |
| **S9** | van Wortswinkel & Nijs (2010), [IEA-ETSAP *Iron and Steel* technology brief](https://iea-etsap.org/E-TechDS/PDF/I02-Iron&Steel-GS-AD-gct.pdf). | Technology costs in source catalogue. |
| **S10** | Hughes et al. (2022), [NETL *Cost of Capturing CO₂ from Industrial Sources*, DOE/NETL-2022/3319](https://www.netl.doe.gov/projects/files/CostofCapturingCO2fromIndustrialSources_071522.pdf). | CCS assumptions. |

Additional source notes in the supplied data include [Trading Economics' Canada steel production series](https://tradingeconomics.com/canada/steel-production) for demand, and the process-by-process attributions in `data/workbook_reference/reference_sources.csv`. See `data/workbook_reference/snapshots/` for the corresponding exported worksheet values. Source references stored in the scenario database are **not** guaranteed to identify every intermediate calculation or the precise workbook cell used.

## 8. Data processing and reproduction

The Python builder separates **editable flow definitions** from **scenario-specific model records**:

```text
Steel-Updated.xlsx (reference workbook)
        │
        ├── data/process_flows/*.csv       # process flows, quantities and units
        └── data/workbook_reference/*      # archived sheets, costs, source metadata

Original scenario SQLite files
        └── data/scenarios/{basecase,eaf,ccs,all}/*.csv

Technology mappings + process flows + scenario table CSVs
        │
        └── steel_builder.build
               ├── outputs/CANOE_steel_basecase.sqlite
               ├── outputs/CANOE_steel_eaf.sqlite
               ├── outputs/CANOE_steel_ccs.sqlite
               └── outputs/CANOE_steel_all.sqlite
```

Run from the package root:

```bash
python -m steel_builder.build
# Or generate one case:
python -m steel_builder.build --scenario ccs
```

The generator recreates the existing **91-table schema**, preserves original non-derived records and table row counts, and **recalculates only** the values in `efficiency`, `limit_tech_input_split_annual`, and `limit_tech_output_split_annual`. It does not calculate technology investment costs, extrapolate emissions, add technologies, or construct commodity edges from scratch. It also does not silently convert units.

To change an existing technology's numerical flow assumptions, edit its mapped file in `data/process_flows/`. To create a new technology, also edit the appropriate scenario table CSVs and the explicit technology/commodity mapping files. Refer to the separate `README.md` for operational commands and developer-specific setup; this page describes the **model**, not the command-line interface.

## 9. Validation status and known limitations

- **Structure:** The four regenerated databases pass SQLite `PRAGMA integrity_check`, preserve the 91 original table definitions and keep non-derived tables unchanged.
- **Coefficient policy:** All technology efficiencies are now the flow-derived `sum(outputs)/sum(inputs)`. This changes **195 efficiency records in EAF** and **405 in All pathways**, relative to the uploaded reference databases, at a difference threshold of `1e-6`. Base case and CCS have no material changes at that threshold.
- **Reference discrepancy:** The supplied EAF database contains 123 NG-DRI efficiency rows with an older value of approximately `0.287170233`; applying the NG-DRI flow rule produces approximately `0.441696113`. The generator now uses the flow-derived value.
- **Referential integrity:** The uploaded reference databases contain pre-existing foreign-key violations (including later-year records despite `time_period` listing only 2020, and some missing quality labels). These are **not fixed** by rebuilding the coefficients. A passing `integrity_check` is not the same as a passing `foreign_key_check`.
- **Model coverage:** Copper contamination, scrap-quality classes, dilution, and stock turnover/recycling dynamics are **not implemented** in this standalone flow-derived steel module. Any material-stock integration would require separate work.
- **Scientific interpretation:** Mixed-unit efficiency arithmetic, possible inconsistencies in source labels, incomplete capacity provenance and placeholder cost assumptions require review.
- **TEMOA solve:** An end-to-end TEMOA optimization/smoke test has **not** been reported for these regenerated databases. Solver feasibility, steel balances, technology choices, costs and emissions must be checked before merging or releasing the module.

### Recommended release checks

1. Reconcile data-source tags, cost basis and any placeholder prices; document currency year for all relevant cost records.
2. Validate conversion factors and physically meaningful flow units, especially electricity, hydrogen and CCS.
3. Resolve existing foreign-key issues without silently changing calibrated model assumptions.
4. Run and review a TEMOA solve for each scenario, including process choices, production balances, emissions and constraint binding.
5. Record revisions to process and scenario CSVs alongside corresponding model results.