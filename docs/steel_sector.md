# Steel sector: data sources, assumptions and technology representation

**Model:** CANOE high-resolution steel sector (TEMOA schema v4)  
**Status:** Prototype sector dataset; technical and scientific validation pending  
**Implementation:** Standalone `Steel` sector, not yet integrated into the general industry-sector pipeline  
**Editable inputs:** Process-flow CSVs, internal model parameters and scenario rules in this package  
**Last documentation review:** 26 November 2026

## 1. Scope and modelling approach

This module represents steel production as a network of technologies that consume and produce commodities. It includes conventional blast-furnace/basic-oxygen-furnace steelmaking, electric-arc-furnace (EAF) routes, natural-gas and hydrogen direct reduction, site power generation, post-processing, and optional carbon capture and storage (CCS). Technology and commodity names follow the existing CANOE/TEMOA schema.

The steel dataset is **separate from the general `Industry` sector** for now. Four alternative scenario databases are generated from a common library of process flows and shared model assumptions with explicit scenario membership. This separation makes it possible to evaluate the steel network before linking it to the remainder of CANOE. It does not imply that energy supply, commodity imports or cross-sector interactions have been fully integrated or validated.

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

The package contains **13 editable process-flow CSV definitions** (12 physical process variants and one synthetic pass-through definition). The technology-to-process assignment is in `data/mappings/technology.csv`; the mapping from technology-specific commodity names to physical flows is in `data/mappings/commodity_bindings.csv`.

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
| Import / transfer — `pass_through.csv` | One generic input | One generic output | Builder convention for import and transfer technologies |

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

> **Important limitation:** The current process-flow conventions sum numerical quantities with **different units** (tonnes, GJ, hydrogen volumes and, for CCS, energy-per-captured-CO₂ and capture fractions). Thus, these values follow the model's **numerical coefficient convention**; they should **not** be interpreted as dimensionless physical, mass-based or thermodynamic efficiencies. A later scientific revision should normalize onto a defined reference unit if physical efficiencies are required.

The generated annual split constraints retain the **original SQLite `operator` values** (in these files, typically `ge`, meaning lower bounds). Computing a proportion does not automatically impose an equality constraint or change the existing feasible set in any other way. The generator also does not add missing split constraints or new input/output commodity pairs.

### Emissions handling

The builder does not treat calculated CO₂ emissions as a further steelmaking material output. In particular, the scrap-EAF process has a separate CO₂ calculation that is **excluded** from the process-flow output numerator. Emissions coefficients reside in `data/inputs/emissions.json`; they are not recalculated from the process flows. The capture technologies and their represented captured-CO₂ streams are separate cases using `ccs_90.csv` and `ccs_99.csv`.

## 5. Scenarios and constraints

| Scenario | Generated database | Representation |
|---|---|---|
| **Base case** | `CANOE_steel_basecase.sqlite` | Conventional and existing steel routes; no modelled CCS or H₂-DRI/electrolysis technologies in the reference scenario. Includes `limit_activity` records absent from the other three supplied scenarios. |
| **EAF** | `CANOE_steel_eaf.sqlite` | Expanded electric/DRI technology options, including hydrogen DRI and onsite electrolyser technologies; no CCS technology records. |
| **CCS** | `CANOE_steel_ccs.sqlite` | Conventional routes plus 90% and 99% CCS options; no modelled H₂-DRI/electrolysis technology records. |
| **All pathways** | `CANOE_steel_all.sqlite` | The combined technology option set, including EAF/DRI, hydrogen and CCS routes. |

Scenario differences extend beyond the available technology list: the editable model rules contain distinct investment/fixed/variable costs, existing capacity, capacity ceilings, activity shares, demand, emissions and other metadata. These are scenario-specific **row selections and assumptions** in purpose-based model definitions. Changing a process flow updates every scenario using it; changing a cost in `data/parameters/costs.json` and `data/inputs/economics.json` updates the scenarios named in that row's `scenarios` membership, while overrides use disjoint scenario masks.

The supplied **CCS scenario alone** contains an explicit `limit_emission` constraint of `co2 <= 7000` for **Ontario** in **2030, 2035, 2040 and 2045**. The `units` field on these particular rows is blank/NULL, so the numerical limit should not be assigned a physical unit without further verification. The presence of CCS technologies in the **All pathways** case does **not** by itself mean it inherits the CCS case's emission cap.

The uploaded `limit_activity_share` records also constrain the relative operation of particular facility/process groups (for example, Dofasco's BOF, scrap-EAF and DRI-EAF shares). Such constraints are **explicit scenario assumptions**, not automatically derived from the process flows. Inspect the `scenarios` on input rules before interpreting a run as a technology-neutral optimization.

## 6. Costs, emissions, capacity and other assumptions

All assumptions are **internal editable inputs**, not external file lookups. The same numeric price or cost can be shared across numerous technologies, vintages and scenarios. Every applied record still carries its units and source attribution, and differences in scenario membership are explicit.

| Assumption | Source inside this package | Treatment |
|---|---|---|
| Investment, fixed and variable costs | `data/parameters/costs.json` (31 named values); `data/inputs/economics.json` (technology/year/scenario applicability) | The builder expands shared cost parameters over the specified technologies, vintages and periods. |
| Process input/output quantities | `data/process_flows/*.csv` (13 processes) | Updated flows recalculate efficiency and annual commodity splits. |
| Emission activity | `data/parameters/emissions.json` (5 numerical values); `data/inputs/emissions.json` (application) | Explicit assigned coefficients, **not** derived from process-flow ratios. |
| Existing plant capacity | `data/inputs/operations.json` | Facility-specific 2020-vintage capacity and units where recorded. |
| Capacity to activity | `data/inputs/operations.json` | Technology-specific activity conversion factors. |
| Regional demand | `data/inputs/operations.json` | Fixed rolled-steel demand values over model periods. |
| Capacity, activity, emission and group limits | `data/inputs/operations.json`, `data/inputs/emissions.json` | Explicit per-scenario assumptions; not inferred from flow definitions. |
| Technology/commodity definitions | `data/inputs/entities.json` | Generated model records and labels. |
| Network availability and commodity splits | `data/inputs/network.json`, `data/mappings/commodity_bindings.csv` | Arc combinations expanded from declared bindings, then coefficients calculated from flows. |

The individual cost rules retain the recorded unit labels and cost-basis notes. Some descriptions refer to conversion from a 2010 EUR or USD basis to a 2020/2022 CAD basis. These historical transformations are **not re-evaluated** when a user changes a cost parameter. The user must supply the value on the appropriate model basis.

**Scientific provenance caveat:** Recorded source IDs and technology costs may contain mismatches. For example, `S4` is described as a production-statistics source in model metadata, while some investment-cost rules are tagged `S4`. Review assignments against primary references before interpreting these as independently validated unit costs.

## 7. Data sources

The following references are recorded in the model's source metadata and technology notes. These are **recorded source attributions**, not a claim that all underlying numbers have been independently reproduced against the publications.

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
| **S9** | van Wortswinkel & Nijs (2010), [IEA-ETSAP *Iron and Steel* technology brief](https://iea-etsap.org/E-TechDS/PDF/I02-Iron&Steel-GS-AD-gct.pdf). | Technology-cost attribution appearing in the model metadata. |
| **S10** | Hughes et al. (2022), [NETL *Cost of Capturing CO₂ from Industrial Sources*, DOE/NETL-2022/3319](https://www.netl.doe.gov/projects/files/CostofCapturingCO2fromIndustrialSources_071522.pdf). | CCS assumptions. |

Additional model source notes include [Trading Economics' Canada steel production series](https://tradingeconomics.com/canada/steel-production) for demand. The recorded source IDs are retained for traceability, but have not all been independently checked against the underlying publications. Current source descriptions and per-rule attributions are editable in `data/inputs/model_settings.json` and the relevant sector input files.

## 8. Building and changing the dataset

The **package itself is the editable source of truth**:

```text
data/parameters/costs.json + emissions.json + model.json
    + data/process_flows/*.csv
    + data/mappings/*.csv
    + data/inputs/{entities,economics,emissions,network,operations,model_settings}.json
    + data/scenarios/*.json
                    |
              Python builder
                    |
         TEMOA schema.sql (91 tables)
                    |
       CANOE_steel_{basecase,eaf,ccs,all}.sqlite
```

Run the following commands from the package root:

```bash
python -m steel_builder.build
python -m steel_builder.build --scenario ccs
python -m unittest discover -s tests -v
python -m steel_builder.verify_reference
```

The builder loads internal model definitions, expands shared rules into their target regions, technologies and time periods, then calculates every efficiency and split coefficient from the mapped physical flows. The SQLite databases are **outputs**, not manually maintained master files. Configuration and scientific assumptions can be edited independently.

To introduce a new technology, edit `entities.json`, `mappings/technology.csv`, `mappings/commodity_bindings.csv`, `network.json`, and any applicable economics, operations or emissions records. Future technology families can reuse existing processes and cost profiles. The generator does **not yet invent a fully connected network, capacity constraints or scientifically meaningful cost profile solely from a new flow file**.

## 9. Validation status and limitations

- **Regression:** The v0.4 generated contents of all 91 tables are identical in every scenario to the immediately preceding v0.3 flow-derived model baseline. This is a technical equivalence result, not an independent scientific validation.
- **Efficiency policy:** All efficiencies use the aggregate `sum(outputs)/sum(inputs)` method, as agreed. Existing values in older databases that used per-input efficiencies are not brought forward.
- **Physical interpretation:** The flow inputs mix mass, electricity, hydrogen volumes and CCS coefficients, so numerical flow efficiencies need unit-consistency review before physical interpretation. Alias handling also requires care when adding new commodity connections.
- **Data quality:** Facility capacities, cost units, scenario constraints, provenance tags and source assumptions should be reviewed by domain experts. Cost values are editable but currency/unit conversions are not automated.
- **Referential integrity:** Missing quality ratings (`dq_cred`, `dq_geog`, `dq_struc`, `dq_tech`, `dq_time`) are stored as SQL `NULL` (v0.5), eliminating data-quality foreign-key findings. Other legacy references, especially years in `time_period` and some data-source IDs, still have unresolved foreign-key inconsistencies. The builder reports them separately from SQLite's `integrity_check`.
- **TEMOA:** The four rebuilt databases have not yet undergone full solver validation. They should be assessed for feasibility, material balances, costs, emissions and binding constraints before being treated as production-ready.
- **Scope:** Copper contamination and scrap-quality stock/dilution modeling are not implemented here.

This documentation is intended for model interpretation and review. For implementation details and guidance on adapting the approach to another sector, refer to `docs/sector_builder_development.md`.
