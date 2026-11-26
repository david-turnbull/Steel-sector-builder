CREATE TABLE capacity_credit
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    tech        TEXT,
    vintage     INTEGER,
    credit      REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, period, tech, vintage, data_id),
    CHECK (credit >= 0 AND credit <= 1)
);

CREATE TABLE capacity_factor_process
(
    region      TEXT,
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    tech        TEXT,
    vintage     INTEGER,
    factor      REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, season, tod, tech, vintage, data_id),
    CHECK (factor >= 0 AND factor <= 1)
);

CREATE TABLE capacity_factor_tech
(
    region      TEXT,
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    tech        TEXT,
    factor      REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, season, tod, tech, data_id),
    CHECK (factor >= 0 AND factor <= 1)
);

CREATE TABLE capacity_to_activity
(
    region      TEXT,
    tech        TEXT,
    c2a         REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, data_id)
);

CREATE TABLE commodity
(
    name        TEXT,
    flag        TEXT
        REFERENCES commodity_type (label),
    description TEXT,
    units       TEXT,
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (name) REFERENCES commodity_label (commodity),
    PRIMARY KEY (name, data_id)
);

CREATE TABLE commodity_label
(
    commodity TEXT PRIMARY KEY,
    notes     TEXT
);

CREATE TABLE commodity_type
(
    label       TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE construction_input
(
    region      TEXT,
    input_comm  TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    value       REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (input_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, input_comm, tech, vintage, data_id)
);

CREATE TABLE cost_emission
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    emis_comm   TEXT NOT NULL,
    cost        REAL NOT NULL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, emis_comm, data_id)
);

CREATE TABLE cost_fixed
(
    region      TEXT    NOT NULL,
    period      INTEGER NOT NULL
        REFERENCES time_period (period),
    tech        TEXT    NOT NULL,
    vintage     INTEGER NOT NULL
        REFERENCES time_period (period),
    cost        REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, period, tech, vintage, data_id)
);

CREATE TABLE cost_invest
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    cost        REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, vintage, data_id)
);

CREATE TABLE cost_variable
(
    region      TEXT    NOT NULL,
    period      INTEGER NOT NULL
        REFERENCES time_period (period),
    tech        TEXT    NOT NULL,
    vintage     INTEGER NOT NULL
        REFERENCES time_period (period),
    cost        REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, period, tech, vintage, data_id)
);

CREATE TABLE data_quality_credibility
(
    dq_cred     INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE data_quality_geography
(
    dq_geog     INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE data_quality_structure
(
    dq_struc    INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE data_quality_technology
(
    dq_tech     INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE data_quality_time
(
    dq_time     INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE data_set
(
    data_id     TEXT PRIMARY KEY,
    label       TEXT,
    version     TEXT,
    description TEXT,
    status      TEXT,
    author      TEXT,
    date        TEXT,
    parent_id   TEXT
        REFERENCES data_set (data_id),
    changelog   TEXT,
    notes       TEXT
);

CREATE TABLE data_source
(
    source_id TEXT,
    source    TEXT,
    notes     TEXT,
    data_id   TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (source_id) REFERENCES data_source_label (source_id),
    PRIMARY KEY (source_id, data_id)
);

CREATE TABLE data_source_label
(
    source_id TEXT PRIMARY KEY,
    notes     TEXT
);

CREATE TABLE demand
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    commodity   TEXT,
    demand      REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (commodity) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, commodity, data_id)
);

CREATE TABLE demand_specific_distribution
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    demand_name TEXT,
    dsd         REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (demand_name) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, season, tod, demand_name, data_id),
    CHECK (dsd >= 0 AND dsd <= 1)
);

CREATE TABLE efficiency
(
    region      TEXT,
    input_comm  TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT,
    efficiency  REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (input_comm) REFERENCES commodity_label (commodity),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, input_comm, tech, vintage, output_comm, data_id),
    CHECK (efficiency > 0)
);

CREATE TABLE efficiency_variable
(
    region      TEXT,
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    input_comm  TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT,
    efficiency  REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (input_comm) REFERENCES commodity_label (commodity),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, season, tod, input_comm, tech, vintage, output_comm, data_id),
    CHECK (efficiency > 0)
);

CREATE TABLE emission_activity
(
    region      TEXT,
    emis_comm   TEXT,
    input_comm  TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT,
    activity    REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    FOREIGN KEY (input_comm) REFERENCES commodity_label (commodity),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, emis_comm, input_comm, tech, vintage, output_comm, data_id)
);

CREATE TABLE emission_embodied
(
    region      TEXT,
    emis_comm   TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    value       REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, emis_comm, tech, vintage, data_id)
);

CREATE TABLE emission_end_of_life
(
    region      TEXT,
    emis_comm   TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    value       REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, emis_comm, tech, vintage, data_id)
);

CREATE TABLE end_of_life_output
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT,
    value       REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, tech, vintage, output_comm, data_id)
);

CREATE TABLE existing_capacity
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    capacity    REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, vintage, data_id)
);

CREATE TABLE lifetime_process
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    lifetime    REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, vintage, data_id)
);

CREATE TABLE lifetime_survival_curve
(
    region      TEXT    NOT NULL,
    period      INTEGER NOT NULL,
    tech        TEXT    NOT NULL,
    vintage     INTEGER NOT NULL
        REFERENCES time_period (period),
    fraction    REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, period, tech, vintage, data_id)
);

CREATE TABLE lifetime_tech
(
    region      TEXT,
    tech        TEXT,
    lifetime    REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, data_id)
);

CREATE TABLE limit_activity
(
    region        TEXT,
    period        INTEGER
        REFERENCES time_period (period),
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    activity      REAL,
    units         TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, period, tech_or_group, operator, data_id)
);

CREATE TABLE limit_activity_share
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    sub_group   TEXT,
    super_group TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    share       REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, period, sub_group, super_group, operator, data_id)
);

CREATE TABLE limit_annual_capacity_factor
(
    region        TEXT,
    tech_or_group TEXT,
    vintage       INTEGER
        REFERENCES time_period (period),
    output_comm   TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    factor        REAL,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, tech_or_group, vintage, output_comm, operator, data_id),
    CHECK (factor >= 0 AND factor <= 1)
);

CREATE TABLE limit_capacity
(
    region        TEXT,
    period        INTEGER
        REFERENCES time_period (period),
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    capacity      REAL,
    units         TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, period, tech_or_group, operator, data_id)
);

CREATE TABLE limit_capacity_share
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    sub_group   TEXT,
    super_group TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    share       REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, period, sub_group, super_group, operator, data_id)
);

CREATE TABLE limit_degrowth_capacity
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_degrowth_new_capacity
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_degrowth_new_capacity_delta
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_emission
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    emis_comm   TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    value       REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, emis_comm, operator, data_id)
);

CREATE TABLE limit_growth_capacity
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_growth_new_capacity
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_growth_new_capacity_delta
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    rate          REAL NOT NULL DEFAULT 0,
    seed          REAL NOT NULL DEFAULT 0,
    seed_units    TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_new_capacity
(
    region        TEXT,
    tech_or_group TEXT,
    vintage       INTEGER
        REFERENCES time_period (period),
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    new_cap       REAL,
    units         TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, vintage, operator, data_id)
);

CREATE TABLE limit_new_capacity_share
(
    region      TEXT,
    sub_group   TEXT,
    super_group TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    share       REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, sub_group, super_group, vintage, operator, data_id)
);

CREATE TABLE limit_resource
(
    region        TEXT,
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    cum_act       REAL,
    units         TEXT,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech_or_group, operator, data_id)
);

CREATE TABLE limit_seasonal_capacity_factor
(
    region        TEXT
        REFERENCES region (region),
    season        TEXT
        REFERENCES time_season (season),
    tech_or_group TEXT,
    operator      TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    factor        REAL,
    notes         TEXT,
    data_source   TEXT,
    dq_cred       INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog       INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc      INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech       INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time       INTEGER REFERENCES data_quality_time (dq_time),
    data_id       TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, season, tech_or_group, operator, data_id)
);

CREATE TABLE limit_storage_level_fraction
(
    region      TEXT,
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    tech        TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    fraction    REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    CHECK (fraction >= 0 AND fraction <= 1),
    PRIMARY KEY (region, season, tod, tech, operator, data_id)
);

CREATE TABLE limit_tech_input_split
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    input_comm  TEXT,
    tech        TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    proportion  REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (input_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, input_comm, tech, operator, data_id)
);

CREATE TABLE limit_tech_input_split_annual
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    input_comm  TEXT,
    tech        TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    proportion  REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, period, input_comm, tech, operator, data_id)
);

CREATE TABLE limit_tech_output_split
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    tech        TEXT,
    output_comm TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    proportion  REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, tech, output_comm, operator, data_id)
);

CREATE TABLE limit_tech_output_split_annual
(
    region      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    tech        TEXT,
    output_comm TEXT,
    operator    TEXT NOT NULL DEFAULT 'le'
        REFERENCES operator (operator),
    proportion  REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (output_comm) REFERENCES commodity_label (commodity),
    PRIMARY KEY (region, period, tech, output_comm, operator, data_id)
);

CREATE TABLE linked_tech
(
    primary_region TEXT,
    primary_tech   TEXT,
    emis_comm      TEXT,
    driven_tech    TEXT,
    notes          TEXT,
    data_source TEXT,
    data_id        TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (primary_tech) REFERENCES technology_label (tech),
    FOREIGN KEY (driven_tech) REFERENCES technology_label (tech),
    FOREIGN KEY (emis_comm) REFERENCES commodity_label (commodity),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (primary_region, primary_tech, emis_comm, data_id)
);

CREATE TABLE loan_lifetime_process
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    lifetime    REAL,
    units       TEXT,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, vintage, data_id)
);

CREATE TABLE loan_rate
(
    region      TEXT,
    tech        TEXT,
    vintage     INTEGER
        REFERENCES time_period (period),
    rate        REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, vintage, data_id)
);

CREATE TABLE metadata
(
    element TEXT PRIMARY KEY,
    value   INT,
    notes   TEXT
);

CREATE TABLE metadata_real
(
    element TEXT PRIMARY KEY,
    value   REAL,
    notes   TEXT
);

CREATE TABLE myopic_efficiency
(
    base_year   integer,
    region      text,
    input_comm  TEXT
        REFERENCES commodity_label (commodity),
    tech        TEXT
        REFERENCES technology_label (tech),
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT
        REFERENCES commodity_label (commodity),
    efficiency  real,
    lifetime    integer,
    PRIMARY KEY (region, input_comm, tech, vintage, output_comm)
);

CREATE TABLE operator
(
    operator TEXT PRIMARY KEY,
    notes    TEXT
);

CREATE TABLE output_built_capacity
(
    scenario TEXT,
    region   TEXT,
    sector   TEXT
        REFERENCES sector_label (sector),
    tech     TEXT
        REFERENCES technology_label (tech),
    vintage  INTEGER
        REFERENCES time_period (period),
    capacity REAL,
    units    TEXT,
    PRIMARY KEY (region, scenario, tech, vintage)
);

CREATE TABLE output_cost
(
    scenario TEXT,
    region   TEXT,
    sector   TEXT REFERENCES sector_label (sector),
    period   INTEGER REFERENCES time_period (period),
    tech     TEXT REFERENCES technology_label (tech),
    vintage  INTEGER REFERENCES time_period (period),
    d_invest REAL,
    d_fixed  REAL,
    d_var    REAL,
    d_emiss  REAL,
    invest   REAL,
    fixed    REAL,
    var      REAL,
    emiss    REAL,
    units    TEXT,
    PRIMARY KEY (scenario, region, period, tech, vintage),
    FOREIGN KEY (vintage) REFERENCES time_period (period),
    FOREIGN KEY (tech) REFERENCES technology_label (tech)
);

CREATE TABLE output_curtailment
(
    scenario    TEXT,
    region      TEXT,
    sector      TEXT,
    period      INTEGER
        REFERENCES time_period (period),
    season      TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    input_comm  TEXT
        REFERENCES commodity_label (commodity),
    tech        TEXT
        REFERENCES technology_label (tech),
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT
        REFERENCES commodity_label (commodity),
    curtailment REAL,
    units       TEXT,
    PRIMARY KEY (region, scenario, period, season, tod, input_comm, tech, vintage, output_comm)
);

CREATE TABLE output_dual_variable
(
    scenario        TEXT,
    constraint_name TEXT,
    dual            REAL,
    PRIMARY KEY (constraint_name, scenario)
);

CREATE TABLE output_emission
(
    scenario  TEXT,
    region    TEXT,
    sector    TEXT
        REFERENCES sector_label (sector),
    period    INTEGER
        REFERENCES time_period (period),
    emis_comm TEXT
        REFERENCES commodity_label (commodity),
    tech      TEXT
        REFERENCES technology_label (tech),
    vintage   INTEGER
        REFERENCES time_period (period),
    emission  REAL,
    units     TEXT,
    PRIMARY KEY (region, scenario, period, emis_comm, tech, vintage)
);

CREATE TABLE output_flow_in
(
    scenario    TEXT,
    region      TEXT,
    sector      TEXT
        REFERENCES sector_label (sector),
    period      INTEGER
        REFERENCES time_period (period),
    season TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    input_comm  TEXT
        REFERENCES commodity_label (commodity),
    tech        TEXT
        REFERENCES technology_label (tech),
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT
        REFERENCES commodity_label (commodity),
    flow        REAL,
    units       TEXT,
    PRIMARY KEY (region, scenario, period, season, tod, input_comm, tech, vintage, output_comm)
);

CREATE TABLE output_flow_out
(
    scenario    TEXT,
    region      TEXT,
    sector      TEXT
        REFERENCES sector_label (sector),
    period      INTEGER
        REFERENCES time_period (period),
    season TEXT
        REFERENCES time_season (season),
    tod         TEXT
        REFERENCES time_of_day (tod),
    input_comm  TEXT
        REFERENCES commodity_label (commodity),
    tech        TEXT
        REFERENCES technology_label (tech),
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT
        REFERENCES commodity_label (commodity),
    flow        REAL,
    units       TEXT,
    PRIMARY KEY (region, scenario, period, season, tod, input_comm, tech, vintage, output_comm)
);

CREATE TABLE output_flow_out_summary
(
    scenario    TEXT,
    region      TEXT,
    sector      TEXT
        REFERENCES sector_label (sector),
    period      INTEGER
        REFERENCES time_period (period),
    input_comm  TEXT
        REFERENCES commodity_label (commodity),
    tech        TEXT
        REFERENCES technology_label (tech),
    vintage     INTEGER
        REFERENCES time_period (period),
    output_comm TEXT
        REFERENCES commodity_label (commodity),
    flow        REAL,
    PRIMARY KEY (scenario, region, period, input_comm, tech, vintage, output_comm)
);

CREATE TABLE output_net_capacity
(
    scenario TEXT,
    region   TEXT,
    sector   TEXT
        REFERENCES sector_label (sector),
    period   INTEGER
        REFERENCES time_period (period),
    tech     TEXT
        REFERENCES technology_label (tech),
    vintage  INTEGER
        REFERENCES time_period (period),
    capacity REAL,
    units    TEXT,
    PRIMARY KEY (region, scenario, period, tech, vintage)
);

CREATE TABLE output_objective
(
    scenario          TEXT,
    objective_name    TEXT,
    total_system_cost REAL
);

CREATE TABLE output_retired_capacity
(
    scenario TEXT,
    region   TEXT,
    sector   TEXT
        REFERENCES sector_label (sector),
    period   INTEGER
        REFERENCES time_period (period),
    tech     TEXT
        REFERENCES technology_label (tech),
    vintage  INTEGER
        REFERENCES time_period (period),
    cap_eol REAL,
    cap_early REAL,
    units     TEXT,
    PRIMARY KEY (region, scenario, period, tech, vintage)
);

CREATE TABLE output_storage_level
(
    scenario TEXT,
    region TEXT,
    sector TEXT
        REFERENCES sector_label (sector),
    period INTEGER
        REFERENCES time_period (period),
    season TEXT,
    tod TEXT
        REFERENCES time_of_day (tod),
    tech TEXT
        REFERENCES technology_label (tech),
    vintage INTEGER
        REFERENCES time_period (period),
    level REAL,
    units TEXT,
    PRIMARY KEY (scenario, region, period, season, tod, tech, vintage)
);

CREATE TABLE planning_reserve_margin
(
    region      TEXT,
    margin      REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (region) REFERENCES region (region),
    PRIMARY KEY (region, data_id)
);

CREATE TABLE ramp_down_hourly
(
    region      TEXT,
    tech        TEXT,
    rate        REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, data_id)
);

CREATE TABLE ramp_up_hourly
(
    region      TEXT,
    tech        TEXT,
    rate        REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, tech, data_id)
);

CREATE TABLE region
(
    region TEXT PRIMARY KEY,
    notes  TEXT
);

CREATE TABLE reserve_capacity_derate
(
    region      TEXT,
    season      TEXT
        REFERENCES time_season (season),
    tech        TEXT,
    vintage     INTEGER,
    factor      REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (region, season, tech, vintage, data_id),
    CHECK (factor >= 0 AND factor <= 1)
);

CREATE TABLE rps_requirement
(
    region      TEXT    NOT NULL
        REFERENCES region (region),
    period      INTEGER NOT NULL
        REFERENCES time_period (period),
    tech_group  TEXT    NOT NULL,
    requirement REAL    NOT NULL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    FOREIGN KEY (tech_group) REFERENCES tech_group_label (group_name),
    PRIMARY KEY (region, period, tech_group, data_id)
);

CREATE TABLE sector_label
(
    sector TEXT PRIMARY KEY,
    notes  TEXT
);

CREATE TABLE storage_duration
(
    region      TEXT,
    tech        TEXT,
    duration    REAL,
    notes       TEXT,
    data_source TEXT,
    dq_cred     INTEGER REFERENCES data_quality_credibility (dq_cred),
    dq_geog     INTEGER REFERENCES data_quality_geography (dq_geog),
    dq_struc    INTEGER REFERENCES data_quality_structure (dq_struc),
    dq_tech     INTEGER REFERENCES data_quality_technology (dq_tech),
    dq_time     INTEGER REFERENCES data_quality_time (dq_time),
    data_id     TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (data_source) REFERENCES data_source_label (source_id),
    PRIMARY KEY (region, tech, data_id)
);

CREATE TABLE tech_group
(
    group_name TEXT,
    notes      TEXT,
    data_id    TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (group_name) REFERENCES tech_group_label (group_name),
    PRIMARY KEY (group_name, data_id)
);

CREATE TABLE tech_group_label
(
    group_name TEXT PRIMARY KEY,
    notes      TEXT
);

CREATE TABLE tech_group_member
(
    group_name TEXT,
    tech       TEXT,
    data_id    TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    FOREIGN KEY (group_name) REFERENCES tech_group_label (group_name),
    PRIMARY KEY (group_name, tech, data_id)
);

CREATE TABLE technology
(
    tech         TEXT    NOT NULL,
    flag         TEXT    NOT NULL,
    sector       TEXT,
    category     TEXT,
    sub_category TEXT,
    unlim_cap    INTEGER NOT NULL DEFAULT 0,
    annual       INTEGER NOT NULL DEFAULT 0,
    reserve      INTEGER NOT NULL DEFAULT 0,
    curtail      INTEGER NOT NULL DEFAULT 0,
    retire       INTEGER NOT NULL DEFAULT 0,
    flex         INTEGER NOT NULL DEFAULT 0,
    exchange     INTEGER NOT NULL DEFAULT 0,
    seas_stor    INTEGER NOT NULL DEFAULT 0,
    description  TEXT,
    data_id      TEXT
        REFERENCES data_set (data_id),
    FOREIGN KEY (flag) REFERENCES technology_type (label),
    FOREIGN KEY (tech) REFERENCES technology_label (tech),
    PRIMARY KEY (tech, data_id)
);

CREATE TABLE technology_label
(
    tech  TEXT PRIMARY KEY,
    notes TEXT
);

CREATE TABLE technology_type
(
    label       TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE time_of_day
(
    sequence INTEGER UNIQUE,
    tod      TEXT PRIMARY KEY,
    hours    REAL NOT NULL DEFAULT 1,
    notes    TEXT,
    CHECK (hours > 0)
);

CREATE TABLE time_period
(
    sequence INTEGER UNIQUE,
    period   INTEGER PRIMARY KEY,
    flag     TEXT
        REFERENCES time_period_type (label)
);

CREATE TABLE time_period_type
(
    label       TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE time_season
(
    sequence         INTEGER UNIQUE,
    season           TEXT PRIMARY KEY,
    segment_fraction REAL NOT NULL,
    notes            TEXT,
    CHECK (segment_fraction >= 0 AND segment_fraction <= 1)
);

CREATE TABLE time_season_sequential
(
    sequence         INTEGER UNIQUE,
    seas_seq         TEXT PRIMARY KEY,
    season           TEXT
        REFERENCES time_season (season),
    segment_fraction REAL NOT NULL,
    notes            TEXT,
    CHECK (segment_fraction >= 0 AND segment_fraction <= 1)
);
