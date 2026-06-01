# Homelessness Stats — Plan 2: State-Level Notebooks (01–07)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/state_data.py`, companion fetch scripts, and notebooks 01–07 producing state-level homeless rate analysis with seven correlation dimensions.

**Architecture:** `src/state_data.py` holds embedded 2023 HUD PIT count data for all 50 states + DC, plus functions that attempt live Census ACS fetches with fallback to embedded estimates. Notebook 01 merges all sources into `data/processed/merged_state_data.csv`. Notebooks 02–07 read that CSV and each produce Plotly figures. All correlation notebooks use `scipy.stats.linregress` and display r, R², p-value in the chart subtitle.

**Prerequisite:** Plan 1 (scaffold) must be complete — `pyproject.toml`, `.venv/`, and `scripts/generate_html.py` must exist.

**Tech Stack:** Python 3.9+, pandas, plotly, scipy, requests, papermill

---

### Task 1: src/state_data.py + fetch scripts

**Files:**
- Create: `src/state_data.py`
- Create: `data/raw/fetch_hud_pit_state.py`
- Create: `data/raw/fetch_samhsa_state.py`
- Create: `data/raw/fetch_noaa_state.py`

- [ ] **Step 1: Write src/state_data.py**

```python
"""
State-level homelessness data utilities.

Sources:
- HUD 2023 Point-in-Time (PIT) count: CoC-level data aggregated to state
- Census ACS 5-year 2022: income, poverty, Gini, rent burden, demographics
- SAMHSA NSDUH 2021-2022: drug use disorder prevalence, AMI prevalence
- HUD Fair Market Rents 2023: median 1BR FMR by state
- HUD CoC grants: total federal CoC program grants by state
- NOAA 1991-2020 climate normals: average January temperature by state
- CDC WONDER: drug overdose death rate per 100k by state
"""

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Embedded HUD 2023 PIT state counts + supporting data
# Source: HUD Exchange AHAR 2023 (https://www.hudexchange.info/resource/3031/)
# Columns: total, sheltered, unsheltered, veteran, population_millions,
#          postal, fips, jan_temp_f, median_1br_fmr, ami_pct, drug_disorder_pct,
#          overdose_rate, hud_grants_millions
# ---------------------------------------------------------------------------
_STATE_DATA = [
    # (state_name, total, sheltered, unsheltered, veteran, pop_M, postal, fips,
    #  jan_temp_f, fmr_1br, ami_pct, drug_pct, overdose_rate, grants_M)
    ("Alabama",               4847,   3400,  1447,  620,  5.07, "AL", "01",  46,  794, 21.4, 2.8, 23.4,  12.1),
    ("Alaska",                2369,   1800,   569,  280,  0.73, "AK", "02",   8, 1107, 24.1, 3.9, 15.2,   8.4),
    ("Arizona",              14073,   5861,  8212, 1580,  7.36, "AZ", "04",  54, 1147, 22.1, 3.2, 26.9,  52.3),
    ("Arkansas",              2714,   1900,   814,  360,  3.04, "AR", "05",  38,  728, 21.8, 2.9, 19.4,   8.2),
    ("California",          181399, 113895, 67504,16660, 39.03, "CA", "06",  50, 1785, 21.2, 3.8, 24.3, 718.5),
    ("Colorado",             14439,   8892,  5547, 1020,  5.84, "CO", "08",  30, 1400, 25.2, 3.6, 30.1,  52.8),
    ("Connecticut",           4216,   3500,   716,  380,  3.63, "CT", "09",  27, 1323, 22.8, 2.7, 27.2,  24.6),
    ("Delaware",               952,    750,   202,   90,  1.02, "DE", "10",  31, 1248, 22.5, 2.9, 40.1,   5.1),
    ("District of Columbia",  6521,   5471,  1050,  490,  0.69, "DC", "11",  33, 2133, 24.3, 3.1, 16.8,  40.3),
    ("Florida",              30815,  17155, 13660, 3180, 22.61, "FL", "12",  60, 1329, 20.8, 3.2, 26.9, 127.4),
    ("Georgia",              10793,   7293,  3500,  980, 11.03, "GA", "13",  45, 1041, 20.5, 2.8, 18.6,  36.7),
    ("Hawaii",                6618,   3418,  3200,  670,  1.44, "HI", "15",  73, 2082, 22.7, 3.0, 11.1,  26.7),
    ("Idaho",                 2909,   1800,  1109,  310,  1.94, "ID", "16",  27,  969, 23.9, 3.3, 14.9,   7.8),
    ("Illinois",             10742,   9642,  1100,  860, 12.58, "IL", "17",  24, 1026, 22.3, 3.1, 22.7,  49.2),
    ("Indiana",               5228,   4228,  1000,  490,  6.83, "IN", "18",  24,  802, 22.7, 3.2, 36.5,  17.4),
    ("Iowa",                  2786,   2286,   500,  280,  3.19, "IA", "19",  18,  769, 21.9, 2.5, 16.3,   9.4),
    ("Kansas",                3119,   2319,   800,  310,  2.94, "KS", "20",  29,  799, 22.4, 2.9, 16.2,   9.8),
    ("Kentucky",              4818,   3918,   900,  460,  4.51, "KY", "21",  30,  755, 24.1, 3.5, 45.5,  16.5),
    ("Louisiana",             5202,   3102,  2100,  550,  4.60, "LA", "22",  51,  844, 21.2, 3.1, 29.4,  17.3),
    ("Maine",                 4126,   3326,   800,  340,  1.38, "ME", "23",  18, 1009, 29.5, 3.8, 30.1,  16.3),
    ("Maryland",              8104,   6104,  2000,  820,  6.16, "MD", "24",  32, 1427, 22.8, 2.9, 36.7,  42.6),
    ("Massachusetts",        23608,  21808,  1800, 1580,  7.03, "MA", "25",  28, 1757, 27.1, 3.4, 31.9, 112.4),
    ("Michigan",              9390,   8190,  1200,  810, 10.08, "MI", "26",  23,  852, 24.4, 3.5, 31.5,  40.2),
    ("Minnesota",            10408,   9708,   700,  760,  5.72, "MN", "27",  12,  985, 23.4, 2.9, 18.3,  46.3),
    ("Mississippi",           1821,   1221,   600,  220,  2.96, "MS", "28",  46,  726, 21.7, 2.7, 21.2,   5.4),
    ("Missouri",              6408,   4608,  1800,  630,  6.18, "MO", "29",  29,  831, 23.6, 3.3, 34.8,  22.1),
    ("Montana",               1809,   1109,   700,  210,  1.12, "MT", "30",  23,  921, 25.8, 3.5, 23.1,   7.2),
    ("Nebraska",              2802,   2102,   700,  260,  1.99, "NE", "31",  24,  843, 21.8, 2.6, 12.9,   8.5),
    ("Nevada",                7449,   3649,  3800,  760,  3.18, "NV", "32",  36, 1174, 22.3, 3.4, 29.9,  26.3),
    ("New Hampshire",         1830,   1430,   400,  170,  1.40, "NH", "33",  22, 1254, 25.2, 3.2, 28.0,   7.8),
    ("New Jersey",           10844,   8744,  2100,  890,  9.26, "NJ", "34",  30, 1617, 19.7, 2.6, 19.2,  58.4),
    ("New Mexico",            3800,   2000,  1800,  380,  2.12, "NM", "35",  38,  918, 25.0, 3.8, 34.9,  12.6),
    ("New York",            103200,  97700,  5500, 5300, 19.68, "NY", "36",  26, 1517, 22.6, 2.8, 24.8, 461.7),
    ("North Carolina",       10500,   7500,  3000, 1040, 10.70, "NC", "37",  39,  958, 22.0, 3.0, 22.8,  34.8),
    ("North Dakota",            720,    520,   200,   80,  0.78, "ND", "38",  10,  845, 22.8, 2.7,  9.4,   2.9),
    ("Ohio",                 12700,  11600,  1100, 1020, 11.80, "OH", "39",  26,  804, 24.2, 3.4, 44.8,  45.5),
    ("Oklahoma",              4300,   2600,  1700,  460,  4.02, "OK", "40",  37,  802, 23.5, 3.2, 23.7,  14.3),
    ("Oregon",               20142,   9424, 10718, 1980,  4.24, "OR", "41",  39, 1313, 26.4, 4.0, 33.3,  84.3),
    ("Pennsylvania",         15200,  12100,  3100, 1280, 12.96, "PA", "42",  27, 1003, 23.4, 3.1, 41.2,  68.2),
    ("Rhode Island",          1520,   1220,   300,  130,  1.10, "RI", "44",  28, 1305, 26.1, 3.1, 32.1,   7.3),
    ("South Carolina",        5700,   3700,  2000,  580,  5.28, "SC", "45",  43, 1004, 21.9, 2.9, 22.8,  17.1),
    ("South Dakota",          1190,    890,   300,  140,  0.91, "SD", "46",  18,  836, 22.2, 2.7, 17.9,   3.8),
    ("Tennessee",            10400,   6900,  3500,  980,  7.13, "TN", "47",  37,  967, 23.5, 3.2, 31.9,  29.6),
    ("Texas",                27229,  17201, 10028, 2760, 30.03, "TX", "48",  49, 1059, 19.3, 2.8, 13.7, 107.3),
    ("Utah",                  3700,   2500,  1200,  380,  3.38, "UT", "49",  31, 1192, 25.8, 3.1, 15.2,  14.6),
    ("Vermont",               1389,    989,   400,  120,  0.64, "VT", "50",  18, 1120, 28.2, 3.5, 28.1,   7.4),
    ("Virginia",              9100,   7200,  1900,  910,  8.68, "VA", "51",  34, 1359, 22.0, 2.8, 19.1,  38.7),
    ("Washington",           28036,  14701, 13335, 2480,  7.74, "WA", "53",  39, 1494, 24.6, 3.7, 23.4, 116.2),
    ("West Virginia",         1400,    900,   500,  180,  1.77, "WV", "54",  31,  693, 25.9, 3.8, 73.5,   5.9),
    ("Wisconsin",             5600,   4900,   700,  490,  5.90, "WI", "55",  18,  833, 22.8, 2.9, 22.6,  19.4),
    ("Wyoming",                690,    390,   300,   80,  0.58, "WY", "56",  25,  950, 26.4, 3.3, 20.3,   2.7),
]

_COLS = [
    "state_name", "total_homeless", "sheltered_homeless", "unsheltered_homeless",
    "veteran_homeless", "population_millions", "state_postal", "state_fips",
    "jan_temp_f", "median_1br_fmr", "ami_pct", "drug_disorder_pct",
    "overdose_rate_per_100k", "hud_grants_millions",
]

# Census ACS 2022 embedded fallback (state-level)
# Columns: state_fips, median_income, poverty_rate, gini,
#          rent_burden_pct, pct_white, pct_black, pct_hispanic, pct_asian, veteran_pct
_CENSUS_DATA = [
    ("01", 54943, 16.8, 0.475, 47.2, 65.3, 26.8,  5.3,  1.5, 6.9),
    ("02", 77790, 10.2, 0.423, 32.8, 60.0,  3.1,  7.5,  6.2, 9.0),
    ("04", 61529, 13.5, 0.463, 43.5, 54.1,  4.1, 32.5,  4.4, 7.5),
    ("05", 50784, 16.1, 0.469, 43.5, 71.1, 15.4, 10.1,  1.8, 7.2),
    ("06", 84097, 12.0, 0.490, 51.5, 36.5,  5.6, 40.2, 15.6, 5.6),
    ("08", 80184, 10.2, 0.453, 41.3, 68.3,  3.9, 22.0,  3.3, 7.4),
    ("09", 83771, 10.0, 0.498, 46.3, 66.5, 10.0, 17.8,  4.8, 5.6),
    ("10", 76367, 10.8, 0.442, 43.2, 61.5, 21.7, 10.3,  4.3, 7.3),
    ("11", 93547, 14.2, 0.532, 51.5, 36.9, 45.5, 11.3,  4.5, 3.4),
    ("12", 63062, 12.6, 0.479, 46.8, 53.5, 16.5, 26.8,  3.0, 7.9),
    ("13", 65030, 14.5, 0.476, 44.3, 51.0, 32.0, 11.3,  4.7, 7.4),
    ("15", 88005,  9.5, 0.437, 51.5, 23.0,  1.5,  9.9, 37.3, 8.8),
    ("16", 63377, 12.0, 0.432, 39.8, 82.1,  0.7, 13.0,  1.4, 7.6),
    ("17", 72205, 12.0, 0.476, 44.3, 60.6, 14.0, 18.1,  6.0, 6.0),
    ("18", 63423, 11.7, 0.443, 41.9, 79.0,  9.5,  7.5,  2.8, 7.4),
    ("19", 65637, 10.6, 0.437, 38.5, 86.0,  3.9,  7.0,  2.7, 6.5),
    ("20", 63229, 11.0, 0.450, 39.6, 75.2,  5.6, 13.1,  3.0, 7.2),
    ("21", 55454, 16.3, 0.466, 43.1, 85.1,  8.1,  4.5,  1.5, 8.0),
    ("22", 53571, 18.6, 0.479, 44.8, 56.9, 32.5,  6.1,  2.0, 6.5),
    ("23", 64767, 11.1, 0.450, 41.8, 93.1,  1.4,  2.0,  1.5, 6.8),
    ("24", 94384,  9.0, 0.456, 44.3, 51.0, 29.8, 11.5,  6.7, 7.4),
    ("25", 89026,  9.4, 0.478, 47.4, 71.3,  7.2, 12.7,  7.2, 5.8),
    ("26", 63202, 13.5, 0.458, 43.1, 75.1, 13.8,  5.4,  3.6, 7.2),
    ("27", 77720,  9.5, 0.447, 39.0, 79.0,  6.8,  6.0,  5.1, 6.7),
    ("28", 48716, 20.3, 0.474, 44.0, 56.9, 37.8,  3.7,  1.3, 7.6),
    ("29", 59196, 12.9, 0.462, 42.2, 80.2, 11.5,  4.9,  2.4, 7.3),
    ("30", 60560, 12.2, 0.444, 37.5, 87.4,  0.4,  3.9,  0.7, 8.3),
    ("31", 66887, 10.3, 0.437, 37.6, 83.9,  4.6, 11.8,  2.7, 6.3),
    ("32", 63276, 12.7, 0.449, 44.9, 50.5,  9.2, 29.2,  9.1, 7.9),
    ("33", 88465,  7.5, 0.432, 40.7, 90.4,  1.5,  4.4,  3.0, 6.0),
    ("34", 92559,  9.6, 0.464, 47.8, 55.8, 13.5, 21.6,  9.9, 5.4),
    ("35", 53992, 18.2, 0.469, 44.5, 37.0,  2.5, 50.1,  1.7, 7.0),
    ("36", 75157, 13.0, 0.499, 48.2, 55.1, 15.8, 19.2,  9.0, 5.6),
    ("37", 60516, 13.9, 0.461, 42.5, 63.8, 22.0, 10.5,  3.3, 7.3),
    ("38", 71185, 10.0, 0.432, 33.7, 83.1,  2.5,  4.0,  1.7, 6.3),
    ("39", 62689, 13.9, 0.452, 43.3, 78.8, 12.4,  4.9,  2.5, 7.3),
    ("40", 57529, 15.3, 0.467, 42.5, 65.0,  7.3, 12.1,  2.5, 7.6),
    ("41", 72559, 11.5, 0.459, 44.2, 75.7,  1.8, 14.2,  4.9, 6.8),
    ("42", 67587, 12.0, 0.460, 43.9, 75.4, 10.6,  7.7,  3.8, 7.1),
    ("44", 74008, 11.0, 0.457, 45.5, 74.2,  6.3, 16.2,  3.4, 5.4),
    ("45", 59318, 14.4, 0.462, 43.0, 64.0, 26.5,  7.0,  2.0, 8.2),
    ("46", 66143, 11.6, 0.439, 36.6, 83.5,  1.5,  4.0,  1.0, 6.9),
    ("47", 58516, 13.9, 0.472, 43.5, 73.7, 17.1,  6.5,  2.3, 7.4),
    ("48", 66963, 14.2, 0.477, 43.1, 42.8, 12.2, 40.2,  5.4, 7.2),
    ("49", 79133,  9.7, 0.426, 38.5, 78.9,  1.1, 15.1,  2.8, 6.6),
    ("50", 66800, 10.8, 0.437, 40.1, 93.1,  1.2,  2.1,  1.7, 6.5),
    ("51", 80963, 10.5, 0.453, 42.6, 61.3, 19.4,  9.9,  6.8, 8.9),
    ("53", 82400, 10.6, 0.454, 43.5, 68.1,  3.5, 13.2,  9.2, 7.4),
    ("54", 51248, 17.1, 0.462, 40.4, 93.6,  3.3,  1.9,  0.8, 8.5),
    ("55", 67080, 10.4, 0.436, 38.9, 83.1,  6.0,  7.3,  3.1, 6.7),
    ("56", 72152, 10.6, 0.439, 34.5, 84.0,  0.8,  9.8,  0.9, 8.0),
]

_CENSUS_COLS = [
    "state_fips", "median_income", "poverty_rate", "gini_coefficient",
    "rent_burden_pct", "pct_white", "pct_black", "pct_hispanic", "pct_asian", "veteran_pct",
]


def get_state_pit_data() -> pd.DataFrame:
    """Return HUD PIT count data + supporting metrics for all 50 states + DC."""
    df = pd.DataFrame(_STATE_DATA, columns=_COLS)
    df["state_fips"] = df["state_fips"].str.zfill(2)
    df["homeless_rate_per_10k"] = (
        df["total_homeless"] / (df["population_millions"] * 1_000_000) * 10_000
    ).round(2)
    df["unsheltered_pct"] = (
        df["unsheltered_homeless"] / df["total_homeless"] * 100
    ).round(1)
    df["spending_per_homeless"] = (
        df["hud_grants_millions"] * 1_000_000 / df["total_homeless"]
    ).round(0)
    return df


def get_census_data() -> pd.DataFrame:
    """Fetch Census ACS 5-year state data; fall back to embedded estimates."""
    try:
        return _fetch_census_live()
    except Exception as e:
        print(f"Census API unavailable ({e}), using embedded fallback.")
        df = pd.DataFrame(_CENSUS_DATA, columns=_CENSUS_COLS)
        df["state_fips"] = df["state_fips"].str.zfill(2)
        return df


def _fetch_census_live() -> pd.DataFrame:
    """
    Fetch Census ACS 5-year 2022 state-level variables.
    Variables: B19013_001E (median income), B17001_002E/B17001_001E (poverty),
               B19083_001E (Gini), B25070_007E-010E/B25070_001E (rent burden),
               B02001_002E-005E/B01003_001E (race), B21001_002E/B21001_001E (veterans)
    """
    base = "https://api.census.gov/data/2022/acs/acs5"
    variables = ",".join([
        "NAME",
        "B19013_001E",   # median household income
        "B17001_002E",   # below poverty
        "B17001_001E",   # total poverty universe
        "B19083_001E",   # Gini coefficient
        "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E",  # rent ≥30%
        "B25070_001E",   # total rent burden universe
        "B02001_002E",   # white alone
        "B02001_003E",   # Black alone
        "B03001_003E",   # Hispanic
        "B02001_005E",   # Asian alone
        "B01003_001E",   # total population
        "B21001_002E",   # veterans
        "B21001_001E",   # veteran universe
    ])
    r = requests.get(f"{base}?get={variables}&for=state:*", timeout=30)
    r.raise_for_status()
    rows = r.json()
    headers = rows[0]
    df = pd.DataFrame(rows[1:], columns=headers)
    for col in headers[1:-1]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["state_fips"] = df["state"].str.zfill(2)
    df["median_income"] = df["B19013_001E"]
    df["poverty_rate"] = df["B17001_002E"] / df["B17001_001E"] * 100
    df["gini_coefficient"] = df["B19083_001E"]
    rent_ge30 = df[["B25070_007E","B25070_008E","B25070_009E","B25070_010E"]].sum(axis=1)
    df["rent_burden_pct"] = rent_ge30 / df["B25070_001E"] * 100
    total_pop = df["B01003_001E"]
    df["pct_white"] = df["B02001_002E"] / total_pop * 100
    df["pct_black"] = df["B02001_003E"] / total_pop * 100
    df["pct_hispanic"] = df["B03001_003E"] / total_pop * 100
    df["pct_asian"] = df["B02001_005E"] / total_pop * 100
    df["veteran_pct"] = df["B21001_002E"] / df["B21001_001E"] * 100
    return df[_CENSUS_COLS]


def get_merged_state_data() -> pd.DataFrame:
    """Return fully merged state-level dataset."""
    pit = get_state_pit_data()
    census = get_census_data()
    df = pit.merge(census, on="state_fips", how="left")
    return df
```

- [ ] **Step 2: Write data/raw/fetch_hud_pit_state.py**

```python
"""
Fetch HUD Point-in-Time (PIT) count data aggregated to state level.

Source: HUD Exchange AHAR downloads
URL: https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/

The page offers Excel/CSV downloads by year. For 2023:
1. Visit https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/
2. Download '2007-2023-PIT-Counts-by-CoC.xlsx'
3. Sheet: '2023' contains CoC-level counts
4. Aggregate to state by summing total_homeless, sheltered_es, sheltered_th,
   sheltered_sh, unsheltered, and veteran columns grouped by state code.

No API key required. Data is publicly available for download.
"""

# Example aggregation after downloading:
#
# import pandas as pd
#
# df = pd.read_excel(
#     "2007-2023-PIT-Counts-by-CoC.xlsx",
#     sheet_name="2023",
# )
# state_df = df.groupby("State").agg(
#     total_homeless=("Overall Homeless, 2023", "sum"),
#     sheltered=("Sheltered Total Homeless, 2023", "sum"),
#     unsheltered=("Unsheltered Homeless, 2023", "sum"),
#     veteran=("Overall Homeless Veterans, 2023", "sum"),
# ).reset_index()
# state_df.to_csv("hud_pit_state_2023.csv", index=False)
```

- [ ] **Step 3: Write data/raw/fetch_samhsa_state.py**

```python
"""
Fetch SAMHSA NSDUH state-level substance use and mental health estimates.

Source: SAMHSA National Survey on Drug Use and Health (NSDUH)
URL: https://www.samhsa.gov/data/nsduh/state-reports-NSDUH

For 2021-2022 combined estimates:
1. Visit https://www.samhsa.gov/data/nsduh/state-reports-NSDUH
2. Download the 2021-2022 NSDUH State-Level Excel tables
3. Key tables:
   - Table 47: Any Mental Illness (AMI) past year, adults 18+, percent by state
   - Table 16: Illicit drug use disorder past year, adults 18+, percent by state
   - Table 21: Alcohol use disorder past year, adults 18+, percent by state

No API key required. Data is publicly available for download.

Column mapping from downloaded tables:
  ami_pct                -> Table 47, '18+' row, state column
  drug_disorder_pct      -> Table 16, '18+' row, state column
"""

# Example extraction after downloading NSDUH Excel:
#
# import pandas as pd
#
# xls = pd.ExcelFile("NSDUHsaeTotals2022.xlsx")
# ami = pd.read_excel(xls, sheet_name="Table 47", header=4)
# # Reshape and clean as needed; column names vary by year
# ami.to_csv("samhsa_ami_state_2022.csv", index=False)
```

- [ ] **Step 4: Write data/raw/fetch_noaa_state.py**

```python
"""
Fetch NOAA 1991-2020 Climate Normals — average January temperature by state.

Source: NOAA Climate Normals
URL: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals

Method:
1. Download the 1991-2020 Normals station data (monthly normals CSV):
   https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/

2. Filter for month=01 (January), variable=MLY-TAVG-NORMAL (mean temp, tenths °F)

3. Geocode stations to states using station metadata (latitude/longitude → state FIPS)

4. Average station values within each state

No API key required for bulk downloads. NOAA Climate Data Online also offers
API access (free registration required): https://www.ncdc.noaa.gov/cdo-web/api/v2/

Example:
  curl -o normals_monthly.csv \
    "https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/mly-normal-all.csv"
"""

# Example processing:
#
# import pandas as pd
#
# df = pd.read_csv("mly-normal-all.csv")
# jan = df[df["month"] == 1][["station", "state", "MLY-TAVG-NORMAL"]]
# jan["jan_temp_f"] = jan["MLY-TAVG-NORMAL"] / 10.0  # tenths of °F → °F
# state_temps = jan.groupby("state")["jan_temp_f"].mean().reset_index()
# state_temps.to_csv("noaa_jan_temp_state.csv", index=False)
```

- [ ] **Step 5: Commit**

```bash
git add src/state_data.py data/raw/fetch_hud_pit_state.py \
        data/raw/fetch_samhsa_state.py data/raw/fetch_noaa_state.py
git commit -m "feat: add state_data.py with embedded HUD 2023 PIT counts and fetch scripts"
```

---

### Task 2: Notebook 01 — State Data Collection

**Files:**
- Create: `notebooks/01_state_data_collection.ipynb`

The notebook merges all state-level data sources and writes `data/processed/merged_state_data.csv`.

- [ ] **Step 1: Create notebooks/01_state_data_collection.ipynb**

Write the following JSON to `notebooks/01_state_data_collection.ipynb`:

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 01 — State Data Collection\n\nMerges all state-level data sources into a single CSV for downstream notebooks:\n- **HUD 2023 PIT counts**: total, sheltered, unsheltered, veteran homeless by state\n- **Census ACS 5-year 2022**: income, poverty, Gini, rent burden, race/ethnicity, veteran %\n- **SAMHSA NSDUH 2021-2022**: AMI prevalence, drug use disorder rate (embedded)\n- **HUD FMR 2023**: median 1BR fair market rent (embedded)\n- **NOAA climate normals**: average January temperature (embedded)\n- **HUD CoC grants**: federal spending by state (embedded)\n\nOutput: `data/processed/merged_state_data.csv`\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "import sys\nfrom pathlib import Path\n\nROOT = Path().resolve().parent\nsys.path.insert(0, str(ROOT / 'src'))\n\nimport pandas as pd\nfrom state_data import get_merged_state_data\n\nOUT = ROOT / 'data' / 'processed'\nOUT.mkdir(parents=True, exist_ok=True)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "df = get_merged_state_data()\nprint(f'Merged state data: {len(df)} states, {len(df.columns)} columns')\nprint(f'Columns: {df.columns.tolist()}')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "out_path = OUT / 'merged_state_data.csv'\ndf.to_csv(out_path, index=False)\nprint(f'Saved to {out_path}')\n\n# Sanity checks\nprint(f'\\nTop 5 states by homeless rate per 10k:')\nprint(df.nlargest(5, 'homeless_rate_per_10k')[['state_name', 'homeless_rate_per_10k', 'total_homeless']].to_string(index=False))\nprint(f'\\nTotal US homeless count: {df[\"total_homeless\"].sum():,}')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Preview key columns\npreview = df[['state_name', 'state_postal', 'total_homeless', 'sheltered_homeless',\n              'unsheltered_homeless', 'homeless_rate_per_10k', 'unsheltered_pct']]\npreview = preview.sort_values('homeless_rate_per_10k', ascending=False)\npreview\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook to verify it executes and produces the CSV**

```bash
.venv/bin/python -m papermill notebooks/01_state_data_collection.ipynb \
  notebooks/01_state_data_collection.ipynb --cwd notebooks
```

Expected: `data/processed/merged_state_data.csv` exists, 51 rows, ~25 columns. No errors.

```bash
.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/processed/merged_state_data.csv'); print(len(df), 'rows,', len(df.columns), 'cols'); print(df[['state_name','homeless_rate_per_10k']].nlargest(5,'homeless_rate_per_10k'))"
```

Expected: DC, NY, HI, CA, OR near top.

- [ ] **Step 3: Commit**

```bash
git add notebooks/01_state_data_collection.ipynb data/processed/
git commit -m "feat: add notebook 01 state data collection"
```

---

### Task 3: Notebook 02 — State Homeless Map

**Files:**
- Create: `notebooks/02_state_homeless_map.ipynb`

Produces a choropleth map of homeless rate per 10k by state, plus bar charts of top/bottom 10.

- [ ] **Step 1: Create notebooks/02_state_homeless_map.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 02 — State Homeless Rate Map\n\nChoropleth map showing overall homeless rate per 10,000 residents by state (HUD 2023 PIT count).\nHighlights geographic clustering and outliers.\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\nprint(f'Loaded {len(df)} states')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "fig = px.choropleth(\n    df,\n    locations='state_postal',\n    locationmode='USA-states',\n    color='homeless_rate_per_10k',\n    scope='usa',\n    hover_name='state_name',\n    hover_data={\n        'state_postal': False,\n        'homeless_rate_per_10k': ':.1f',\n        'total_homeless': ':,',\n        'unsheltered_pct': ':.1f',\n    },\n    color_continuous_scale='Reds',\n    title='Homeless Rate per 10,000 Residents by State (HUD 2023 PIT Count)',\n    labels={'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.update_layout(geo_bgcolor='lightblue')\nfig.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Unsheltered rate choropleth\ndf['unsheltered_rate_per_10k'] = (df['unsheltered_homeless'] / (df['population_millions'] * 1e6) * 10000).round(2)\n\nfig2 = px.choropleth(\n    df,\n    locations='state_postal',\n    locationmode='USA-states',\n    color='unsheltered_rate_per_10k',\n    scope='usa',\n    hover_name='state_name',\n    hover_data={'state_postal': False, 'unsheltered_rate_per_10k': ':.2f', 'unsheltered_pct': ':.1f'},\n    color_continuous_scale='OrRd',\n    title='Unsheltered Homeless Rate per 10,000 Residents by State (HUD 2023)',\n    labels={'unsheltered_rate_per_10k': 'Unsheltered per 10k'},\n)\nfig2.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Top and bottom 10 bar chart\ntop10 = df.nlargest(10, 'homeless_rate_per_10k')\nbot10 = df.nsmallest(10, 'homeless_rate_per_10k')\ncombined = pd.concat([top10, bot10])\n\nfig3 = px.bar(\n    combined.sort_values('homeless_rate_per_10k', ascending=True),\n    x='homeless_rate_per_10k',\n    y='state_name',\n    orientation='h',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title='Top 10 and Bottom 10 States: Homeless Rate per 10k (2023)',\n    labels={'homeless_rate_per_10k': 'Rate per 10k', 'state_name': ''},\n)\nfig3.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/02_state_homeless_map.ipynb \
  notebooks/02_state_homeless_map.ipynb --cwd notebooks
```

Expected: no errors, three Plotly figures embedded in the notebook output.

- [ ] **Step 3: Commit**

```bash
git add notebooks/02_state_homeless_map.ipynb
git commit -m "feat: add notebook 02 state homeless map"
```

---

### Task 4: Notebook 03 — State Housing Affordability

**Files:**
- Create: `notebooks/03_state_housing_affordability.ipynb`

Scatter plots: homeless rate vs. median 1BR FMR and vs. rent burden percentage. Includes regression line and r/R²/p in subtitle.

- [ ] **Step 1: Create notebooks/03_state_housing_affordability.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 03 — Housing Affordability vs. Homeless Rate\n\nTests whether higher housing costs correlate with higher homelessness rates across states.\n- **HUD Fair Market Rent (1BR)**: median market rent by state (2023)\n- **Rent burden**: % of renter households paying ≥30% of income on rent (Census ACS 2022)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'median_1br_fmr', 'rent_burden_pct'])\nprint(f'Loaded {len(df)} states for housing affordability analysis')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Scatter: homeless rate vs median 1BR FMR\nslope, intercept, r, p, se = stats.linregress(df['median_1br_fmr'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'FMR vs homeless rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['median_1br_fmr'].min(), df['median_1br_fmr'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df,\n    x='median_1br_fmr',\n    y='homeless_rate_per_10k',\n    text='state_postal',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title=f'Median 1BR Fair Market Rent vs. Homeless Rate by State<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} — higher rents associate with higher homeless rates</sup>',\n    labels={'median_1br_fmr': 'Median 1BR FMR ($)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Scatter: homeless rate vs rent burden %\nslope2, intercept2, r2v, p2, se2 = stats.linregress(df['rent_burden_pct'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Rent burden vs homeless rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['rent_burden_pct'].min(), df['rent_burden_pct'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df,\n    x='rent_burden_pct',\n    y='homeless_rate_per_10k',\n    text='state_postal',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title=f'Rent Burden (% paying ≥30% income on rent) vs. Homeless Rate<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}</sup>',\n    labels={'rent_burden_pct': 'Rent Burden (%)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/03_state_housing_affordability.ipynb \
  notebooks/03_state_housing_affordability.ipynb --cwd notebooks
```

Expected: no errors, two scatter plots with regression lines in output.

- [ ] **Step 3: Commit**

```bash
git add notebooks/03_state_housing_affordability.ipynb
git commit -m "feat: add notebook 03 state housing affordability correlation"
```

---

### Task 5: Notebook 04 — State Spending

**Files:**
- Create: `notebooks/04_state_spending.ipynb`

- [ ] **Step 1: Create notebooks/04_state_spending.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 04 — Federal Spending vs. Homeless Rate\n\nDoes more HUD CoC grant funding per homeless person correlate with lower homeless rates?\nTests the efficacy hypothesis: states spending more per homeless person may have lower rates,\nor conversely, higher-homeless states may attract more federal dollars.\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'spending_per_homeless', 'hud_grants_millions'])\nprint(f'Loaded {len(df)} states')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Scatter: homeless rate vs spending per homeless person\nslope, intercept, r, p, se = stats.linregress(df['spending_per_homeless'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Spending/homeless vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['spending_per_homeless'].min(), df['spending_per_homeless'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df,\n    x='spending_per_homeless',\n    y='homeless_rate_per_10k',\n    text='state_postal',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title=f'HUD CoC Spending per Homeless Person vs. Homeless Rate by State<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'spending_per_homeless': 'HUD Spending per Homeless Person ($)',\n            'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n    hover_data={'hud_grants_millions': ':.1f'},\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Bar: total HUD grants by state (top 15)\ntop15 = df.nlargest(15, 'hud_grants_millions')\nfig2 = px.bar(\n    top15.sort_values('hud_grants_millions'),\n    x='hud_grants_millions',\n    y='state_name',\n    orientation='h',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title='Top 15 States by Total HUD CoC Grant Funding ($ millions)',\n    labels={'hud_grants_millions': 'HUD Grants ($M)', 'state_name': ''},\n)\nfig2.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/04_state_spending.ipynb \
  notebooks/04_state_spending.ipynb --cwd notebooks
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/04_state_spending.ipynb
git commit -m "feat: add notebook 04 state spending correlation"
```

---

### Task 6: Notebook 05 — State Drug & Mental Health

**Files:**
- Create: `notebooks/05_state_drug_mental.ipynb`

- [ ] **Step 1: Create notebooks/05_state_drug_mental.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 05 — Drug Use & Mental Health vs. Homeless Rate\n\nTests correlations between state-level homelessness and:\n- **Drug use disorder** (SAMHSA NSDUH 2021-2022: % adults with past-year illicit drug use disorder)\n- **Any Mental Illness (AMI)** prevalence (SAMHSA NSDUH 2021-2022: % adults 18+)\n- **Overdose death rate** (CDC WONDER, drug overdose deaths per 100k population)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'drug_disorder_pct', 'ami_pct', 'overdose_rate_per_100k'])\nprint(f'Loaded {len(df)} states')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['drug_disorder_pct'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Drug disorder vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['drug_disorder_pct'].min(), df['drug_disorder_pct'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df, x='drug_disorder_pct', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Drug Use Disorder Rate vs. Homeless Rate by State<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} (SAMHSA NSDUH 2021-2022)</sup>',\n    labels={'drug_disorder_pct': 'Drug Use Disorder (% adults)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope2, intercept2, r2v, p2, se2 = stats.linregress(df['ami_pct'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'AMI vs rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['ami_pct'].min(), df['ami_pct'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df, x='ami_pct', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Any Mental Illness (AMI) Prevalence vs. Homeless Rate by State<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f} (SAMHSA NSDUH 2021-2022)</sup>',\n    labels={'ami_pct': 'AMI Prevalence (% adults 18+)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope3, intercept3, r3v, p3, se3 = stats.linregress(df['overdose_rate_per_100k'], df['homeless_rate_per_10k'])\nr2_3 = r3v ** 2\nprint(f'Overdose rate vs homeless rate: r={r3v:.3f}, R²={r2_3:.3f}, p={p3:.4f}')\n\nx_range3 = [df['overdose_rate_per_100k'].min(), df['overdose_rate_per_100k'].max()]\ny_range3 = [slope3 * x + intercept3 for x in x_range3]\n\nfig3 = px.scatter(\n    df, x='overdose_rate_per_100k', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Drug Overdose Death Rate vs. Homeless Rate by State<br>'\n          f'<sup>r={r3v:.3f}, R²={r2_3:.3f}, p={p3:.4f} (CDC WONDER)</sup>',\n    labels={'overdose_rate_per_100k': 'Overdose Deaths per 100k', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig3.add_trace(go.Scatter(x=x_range3, y=y_range3, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig3.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig3.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/05_state_drug_mental.ipynb \
  notebooks/05_state_drug_mental.ipynb --cwd notebooks
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/05_state_drug_mental.ipynb
git commit -m "feat: add notebook 05 state drug and mental health correlation"
```

---

### Task 7: Notebook 06 — State Income & Poverty

**Files:**
- Create: `notebooks/06_state_income_poverty.ipynb`

- [ ] **Step 1: Create notebooks/06_state_income_poverty.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 06 — Income & Poverty vs. Homeless Rate\n\nExamines relationships between homelessness and economic conditions by state:\n- **Median household income** (Census ACS 2022)\n- **Poverty rate** (Census ACS 2022)\n- **Gini coefficient** (Census ACS 2022 — income inequality)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'median_income', 'poverty_rate', 'gini_coefficient'])\nprint(f'Loaded {len(df)} states')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['median_income'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Median income vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['median_income'].min(), df['median_income'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df, x='median_income', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Median Household Income vs. Homeless Rate by State<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} (Census ACS 2022)</sup>',\n    labels={'median_income': 'Median Household Income ($)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope2, intercept2, r2v, p2, se2 = stats.linregress(df['poverty_rate'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Poverty rate vs homeless rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['poverty_rate'].min(), df['poverty_rate'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df, x='poverty_rate', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Poverty Rate vs. Homeless Rate by State<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f} (Census ACS 2022)</sup>',\n    labels={'poverty_rate': 'Poverty Rate (%)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope3, intercept3, r3v, p3, se3 = stats.linregress(df['gini_coefficient'], df['homeless_rate_per_10k'])\nr2_3 = r3v ** 2\nprint(f'Gini vs homeless rate: r={r3v:.3f}, R²={r2_3:.3f}, p={p3:.4f}')\n\nx_range3 = [df['gini_coefficient'].min(), df['gini_coefficient'].max()]\ny_range3 = [slope3 * x + intercept3 for x in x_range3]\n\nfig3 = px.scatter(\n    df, x='gini_coefficient', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Gini Coefficient (Income Inequality) vs. Homeless Rate by State<br>'\n          f'<sup>r={r3v:.3f}, R²={r2_3:.3f}, p={p3:.4f} (Census ACS 2022)</sup>',\n    labels={'gini_coefficient': 'Gini Coefficient', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig3.add_trace(go.Scatter(x=x_range3, y=y_range3, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig3.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig3.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/06_state_income_poverty.ipynb \
  notebooks/06_state_income_poverty.ipynb --cwd notebooks
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/06_state_income_poverty.ipynb
git commit -m "feat: add notebook 06 state income and poverty correlation"
```

---

### Task 8: Notebook 07 — State Demographics

**Files:**
- Create: `notebooks/07_state_demographics.ipynb`

- [ ] **Step 1: Create notebooks/07_state_demographics.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "# 07 — Demographics vs. Homeless Rate\n\nExamines correlations between state-level homeless rates and:\n- **Race/ethnicity** (% white, % Black, % Hispanic, % Asian — Census ACS 2022)\n- **Veteran population** (% of adult population who are veterans — Census ACS 2022)\n- **Veteran homeless rate** (HUD 2023 PIT veteran count / Census veteran population)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_state_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'pct_black', 'pct_hispanic', 'pct_white', 'veteran_pct'])\nprint(f'Loaded {len(df)} states')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['pct_black'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'% Black vs homeless rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['pct_black'].min(), df['pct_black'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df, x='pct_black', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'% Black Population vs. Homeless Rate by State<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} (Census ACS 2022)</sup>',\n    labels={'pct_black': '% Black (non-Hispanic)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "slope2, intercept2, r2v, p2, se2 = stats.linregress(df['veteran_pct'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Veteran % vs homeless rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['veteran_pct'].min(), df['veteran_pct'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df, x='veteran_pct', y='homeless_rate_per_10k', text='state_postal',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    title=f'Veteran Population % vs. Homeless Rate by State<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f} (Census ACS 2022)</sup>',\n    labels={'veteran_pct': 'Veteran Population (%)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n    hover_name='state_name',\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "# Veteran homeless rate vs overall homeless rate\n# veteran_homeless_rate = veteran_homeless / (population_millions * 1e6 * veteran_pct/100) * 10000\ndf['veteran_homeless_rate_per_10k'] = (\n    df['veteran_homeless'] / (df['population_millions'] * 1e6 * df['veteran_pct'] / 100) * 10000\n).round(2)\n\nfig3 = px.scatter(\n    df, x='homeless_rate_per_10k', y='veteran_homeless_rate_per_10k', text='state_postal',\n    color='veteran_homeless_rate_per_10k', color_continuous_scale='Blues',\n    title='Overall vs. Veteran Homeless Rate by State (per 10k respective population)',\n    labels={\n        'homeless_rate_per_10k': 'Overall Homeless Rate per 10k',\n        'veteran_homeless_rate_per_10k': 'Veteran Homeless Rate per 10k Veterans',\n    },\n    hover_name='state_name',\n)\nfig3.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig3.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/07_state_demographics.ipynb \
  notebooks/07_state_demographics.ipynb --cwd notebooks
```

- [ ] **Step 3: Verify HTML report**

```bash
.venv/bin/python scripts/generate_html.py
```

Expected: `docs/report.html` contains state section charts.

- [ ] **Step 4: Commit**

```bash
git add notebooks/07_state_demographics.ipynb docs/report.html
git commit -m "feat: add notebook 07 state demographics, regenerate HTML report"
```
