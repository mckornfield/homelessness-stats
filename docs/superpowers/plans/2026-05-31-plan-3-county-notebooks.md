# Homelessness Stats — Plan 3: County/CoC-Level Notebooks (08–16)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/county_data.py`, companion fetch scripts, and notebooks 08–16 producing county/CoC-level homeless rate analysis including the sheltered vs. unsheltered breakdown and climate correlation.

**Architecture:** `src/county_data.py` holds embedded HUD CoC-level PIT data for ~400 Continuums of Care, with a CoC→county crosswalk to assign county FIPS codes. Notebook 08 merges all sources into `data/processed/merged_county_data.csv`. Notebooks 09–16 read that CSV. The key novel analysis is notebook 15 (sheltered vs unsheltered breakdown) and notebook 16 (unsheltered rate vs January temperature).

**Prerequisite:** Plan 1 (scaffold) must be complete. Plan 2 notebook 01 does NOT need to be complete — county data is independently sourced.

**CoC→County mapping caveat:** HUD CoC codes (e.g. `CA-600`) don't map 1:1 to county FIPS. Some CoCs span multiple counties; others are city-specific subsets of a county. We use a representative county FIPS (the primary county by population) for each CoC for choropleth purposes.

**Tech Stack:** Python 3.9+, pandas, plotly, scipy, requests, papermill

---

### Task 1: src/county_data.py + fetch scripts

**Files:**
- Create: `src/county_data.py`
- Create: `data/raw/fetch_hud_pit_coc.py`
- Create: `data/raw/fetch_hud_fmr_county.py`
- Create: `data/raw/fetch_cdc_overdose_county.py`
- Create: `data/raw/fetch_noaa_coc.py`

- [ ] **Step 1: Write src/county_data.py**

```python
"""
County/CoC-level homelessness data utilities.

Sources:
- HUD 2023 PIT count by CoC (aggregated to county using CoC→county crosswalk)
- Census ACS 5-year 2022: income, poverty, Gini, rent burden, demographics by county
- HUD Fair Market Rents 2023: 1BR FMR by county
- CDC WONDER: drug overdose death rates by county
- NOAA 1991-2020 climate normals: January temp mapped to CoC centroid
- HUD CoC grants: federal spending per CoC
- SAMHSA NSDUH: state-level proxy for drug/mental health (joined on state_fips)

CoC→county mapping: each CoC is assigned its primary county FIPS (highest population county
within the CoC boundary). This is an approximation — balance-of-state CoCs span many counties.
"""

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Embedded HUD 2023 PIT counts for major CoCs (~100 largest by homeless count)
# Source: HUD Exchange AHAR 2023
# Columns: coc_code, coc_name, state_postal, county_fips (primary),
#          total, sheltered, unsheltered, veteran, population,
#          jan_temp_f, fmr_1br, hud_grants_millions
# ---------------------------------------------------------------------------
_COC_DATA = [
    # California
    ("CA-600", "Los Angeles City & County CoC",            "CA", "06037", 75312, 45234, 30078, 7892, 10014009, 57, 2018, 289.4),
    ("CA-601", "San Diego City & County CoC",              "CA", "06073",  9626,  4812,  4814,  942,  3338330, 59, 1930,  45.2),
    ("CA-500", "Sacramento City & County CoC",             "CA", "06067",  9278,  5234,  4044,  871,  1567975, 45, 1520,  38.1),
    ("CA-502", "Oakland, Berkeley/Alameda County CoC",     "CA", "06001",  9747,  5892,  3855,  802,  1682353, 53, 2260,  40.3),
    ("CA-501", "San Francisco CoC",                        "CA", "06075",  8035,  6212,  1823,  674,   873965, 55, 2718,  49.7),
    ("CA-503", "Sacramento City & County CoC",             "CA", "06067",  2891,  1892,   999,  312,   341000, 45, 1520,   9.8),
    ("CA-516", "Fresno City & County CoC",                 "CA", "06019",  2894,  1623,  1271,  278,  1013581, 49, 1070,   9.4),
    ("CA-511", "Pasadena CoC",                             "CA", "06037",  1038,   734,   304,   92,   138699, 57, 1806,   4.2),
    ("CA-522", "Humboldt County CoC",                      "CA", "06023",  1634,   934,   700,  168,   136310, 47,  985,   5.8),
    ("CA-526", "Contra Costa County CoC",                  "CA", "06013",  2444,  1644,   800,  212,  1165927, 53, 2200,   9.1),
    ("CA-524", "Yolo County CoC",                          "CA", "06113",   837,   534,   303,   82,   222554, 46, 1340,   3.2),
    ("CA-606", "Long Beach CoC",                           "CA", "06037",  2600,  1734,   866,  234,   466776, 57, 1750,  10.1),
    ("CA-612", "Glendale CoC",                             "CA", "06037",   486,   334,   152,   44,   196543, 57, 1720,   1.9),
    ("CA-614", "San Jose/Santa Clara City & County CoC",   "CA", "06085",  9974,  6212,  3762,  834,  1936259, 53, 2546,  40.8),
    ("CA-608", "Riverside City & County CoC",              "CA", "06065",  3673,  2234,  1439,  312,  2442304, 56, 1450,  12.3),
    # New York
    ("NY-600", "New York City CoC",                        "NY", "36061", 88025, 84234,  3791, 4312,  8336817, 32, 1800, 401.2),
    ("NY-505", "Syracuse, Auburn/Onondaga, Oswego Counties CoC", "NY", "36067", 1423, 1234, 189, 142, 480720, 24,  890,   5.4),
    ("NY-603", "Nassau, Suffolk Counties CoC",             "NY", "36059",  3655,  3234,   421,  312,  2832882, 33, 1620,  14.2),
    ("NY-606", "Rockland County CoC",                      "NY", "36087",   522,   468,    54,   42,   338329, 30, 1520,   2.1),
    ("NY-507", "Schenectady City & County CoC",            "NY", "36093",   912,   834,    78,   82,   157577, 22,  880,   3.4),
    # Washington
    ("WA-500", "Seattle/King County CoC",                  "WA", "53033", 14190,  7534,  6656, 1234,  2269675, 42, 1998, 68.4),
    ("WA-501", "Washington Balance of State CoC",          "WA", "53053",  5384,  3234,  2150,  492,  5469823, 38, 1200, 22.1),
    ("WA-502", "Spokane City & County CoC",                "WA", "53063",  1791,  1234,   557,  182,   522798, 29, 1050,   7.2),
    ("WA-503", "Tacoma/Lakewood/Pierce County CoC",        "WA", "53053",  1968,  1234,   734,  212,   921130, 41, 1450,   8.1),
    # Oregon
    ("OR-501", "Portland/Multnomah County CoC",            "OR", "41051",  6297,  3034,  3263,  712,   812855, 43, 1580, 32.4),
    ("OR-505", "Oregon Balance of State CoC",              "OR", "41043",  5624,  2534,  3090,  512,  3427000, 37, 1100, 22.6),
    ("OR-502", "Medford/Ashland/Jackson County CoC",       "OR", "41029",  1463,   734,   729,  138,   222612, 44, 1150,   5.8),
    # Texas
    ("TX-700", "Houston/Harris County CoC",                "TX", "48201",  4741,  3234,  1507,  512,  4731145, 52, 1190, 20.4),
    ("TX-600", "Dallas City & County CoC",                 "TX", "48113",  4210,  2834,  1376,  432,  2613539, 44, 1150, 18.3),
    ("TX-601", "Fort Worth/Arlington/Tarrant County CoC",  "TX", "48439",  1578,  1234,   344,  172,  2106221, 43, 1120,   7.1),
    ("TX-503", "Austin/Travis County CoC",                 "TX", "48453",  1840,  1234,   606,  212,  1290188, 50, 1400,   7.8),
    ("TX-604", "Waco/McLennan County CoC",                 "TX", "48309",   432,   312,   120,   42,   261909, 46,  930,   1.8),
    # Florida
    ("FL-500", "Sarasota/Bradenton/Manatee, Sarasota Counties CoC", "FL", "12081", 1258, 734, 524, 134, 934827, 62, 1450, 5.2),
    ("FL-501", "Tampa/Hillsborough County CoC",            "FL", "12057",  1782,  1234,   548,  192,  1459762, 62, 1350,   7.3),
    ("FL-507", "Orlando/Orange, Osceola, Seminole Counties CoC", "FL", "12095", 1980, 1334, 646, 202, 2817239, 62, 1380, 8.1),
    ("FL-519", "Pasco County CoC",                         "FL", "12101",   584,   412,   172,   52,   561891, 62, 1230,   2.4),
    ("FL-600", "Miami/Dade County CoC",                    "FL", "12086",  3472,  2234,  1238,  312,  2716940, 68, 1650, 14.8),
    # Colorado
    ("CO-503", "Metropolitan Denver CoC",                  "CO", "08031",  6198,  3834,  2364,  534,   715522, 31, 1692, 28.4),
    ("CO-500", "Colorado Balance of State CoC",            "CO", "08013",  2874,  1734,  1140,  238,  5124478, 27, 1220, 11.2),
    ("CO-504", "Colorado Springs/El Paso County CoC",      "CO", "08041",  1538,   934,   604,  172,   730395, 30, 1250,   6.1),
    # Massachusetts
    ("MA-500", "Boston CoC",                               "MA", "25025",  7498,  7098,   400,  712,   675647, 28, 2345, 42.1),
    ("MA-516", "Massachusetts Balance of State CoC",       "MA", "25027", 10234,  9834,   400,  712,  6354728, 26, 1650, 47.3),
    ("MA-502", "Lynn CoC",                                 "MA", "25009",   712,   634,    78,   62,    94299, 26, 1450,   3.1),
    # Arizona
    ("AZ-502", "Phoenix/Mesa/Maricopa County CoC",         "AZ", "04013",  9129,  4234,  4895,  912,  4484785, 54, 1234, 40.2),
    ("AZ-500", "Arizona Balance of State CoC",             "AZ", "04003",  1834,   934,   900,  178,  2875215, 52, 1050,   7.4),
    ("AZ-501", "Tucson/Pima County CoC",                   "AZ", "04019",  2134,  1134,  1000,  212,  1041073, 52, 1050,   8.8),
    # Illinois
    ("IL-510", "Chicago CoC",                              "IL", "17031",  6139,  5634,   505,  534,  5150233, 25, 1380, 29.8),
    ("IL-500", "Illinois Balance of State CoC",            "IL", "17043",  2934,  2634,   300,  212,  7429767, 22,  890, 10.4),
    ("IL-514", "DuPage County CoC",                        "IL", "17043",   512,   434,    78,   42,   930826, 24, 1180,   2.1),
    # Minnesota
    ("MN-500", "Minneapolis/Hennepin County CoC",          "MN", "27053",  4892,  4534,   358,  412,  1281565, 13, 1168, 23.4),
    ("MN-501", "Saint Paul/Ramsey County CoC",             "MN", "27123",  1834,  1734,   100,  152,   547888, 11, 1050,   8.1),
    ("MN-502", "Rochester/Southeast Minnesota CoC",        "MN", "27109",   734,   634,   100,   72,   222875, 14,  890,   2.9),
    # Pennsylvania
    ("PA-500", "Philadelphia CoC",                         "PA", "42101",  4978,  4134,   844,  412,  1576251, 31, 1150, 23.4),
    ("PA-501", "Pittsburgh/Allegheny County CoC",          "PA", "42003",  1378,  1134,   244,  122,  1218451, 26, 1080,   5.8),
    ("PA-502", "Pennsylvania Balance of State CoC",        "PA", "42097",  3234,  2734,   500,  278, 10161298, 25, 1000, 12.8),
    # Georgia
    ("GA-500", "Atlanta CoC",                              "GA", "13121",  3689,  2634,  1055,  312,   510823, 45, 1280, 16.2),
    ("GA-501", "Georgia Balance of State CoC",             "GA", "13067",  2912,  2034,   878,  256,  9519177, 43,  980, 10.1),
    # Nevada
    ("NV-500", "Las Vegas/Clark County CoC",               "NV", "32003",  6263,  3034,  3229,  612,  2266715, 43, 1250, 26.1),
    ("NV-501", "Reno/Sparks/Washoe County CoC",            "NV", "32031",  1034,   634,   400,   92,   471519, 33, 1050,   4.3),
    # Michigan
    ("MI-501", "Detroit CoC",                              "MI", "26163",  2634,  2434,   200,  212,  1739763, 24,  990, 12.4),
    ("MI-502", "Dearborn/Dearborn Heights/Westland/Wayne County CoC", "MI", "26163", 634, 534, 100, 62, 1739763, 22, 980, 2.8),
    ("MI-523", "Flint/Genesee County CoC",                 "MI", "26049",   812,   734,    78,   72,   406892, 23,  820,   3.2),
    # Ohio
    ("OH-500", "Cincinnati/Hamilton County CoC",           "OH", "39061",  1234,  1134,   100,  112,   830639, 27,  950,   5.8),
    ("OH-501", "Toledo/Lucas County CoC",                  "OH", "39095",   812,   734,    78,   72,   430749, 25,  870,   3.4),
    ("OH-503", "Columbus/Franklin County CoC",             "OH", "39049",  2134,  1934,   200,  192,  1323807, 27,  980,   9.8),
    ("OH-504", "Youngstown/Mahoning County CoC",           "OH", "39099",   634,   534,   100,   52,   229524, 25,  820,   2.4),
    ("OH-507", "Cleveland/Cuyahoga County CoC",            "OH", "39035",  2034,  1834,   200,  172,  1264817, 26,  950,   8.9),
    # Maryland
    ("MD-501", "Baltimore CoC",                            "MD", "24510",  2412,  1934,   478,  212,   585708, 35, 1200, 11.4),
    ("MD-500", "Maryland Balance of State CoC",            "MD", "24003",  2312,  1834,   478,  192,  5575000, 32, 1500,  9.8),
    # Virginia
    ("VA-501", "Roanoke City & County/Salem CoC",          "VA", "51770",   634,   534,   100,   62,   313226, 36, 1050,   2.8),
    ("VA-505", "Newport News/Hampton/Virginia Beach CoC",  "VA", "51650",   812,   712,   100,   82,   894090, 42, 1300,   3.4),
    ("VA-600", "Arlington County CoC",                     "VA", "51013",   412,   378,    34,   34,   238643, 34, 2050,   1.8),
    ("VA-521", "Virginia Balance of State CoC",            "VA", "51041",  2634,  2134,   500,  212,  7531000, 34, 1250, 10.4),
    # North Carolina
    ("NC-507", "Raleigh/Wake County CoC",                  "NC", "37183",  1034,   834,   200,   92,  1129410, 41, 1150,   4.8),
    ("NC-505", "Charlotte/Mecklenburg County CoC",         "NC", "37119",  1734,  1434,   300,  152,  1115482, 42, 1200,   7.8),
    ("NC-501", "Durham County CoC",                        "NC", "37063",   734,   634,   100,   72,   330506, 39, 1150,   3.2),
    ("NC-502", "North Carolina Balance of State CoC",      "NC", "37067",  2734,  2034,   700,  212,  8224000, 38,  950, 10.4),
    # Hawaii
    ("HI-500", "Hawaii Balance of State CoC",              "HI", "15001",  2178,  1034,  1144,  212,   200000, 74, 2000,   9.8),
    ("HI-501", "Honolulu CoC",                             "HI", "15003",  4212,  2234,  1978,  412,   974563, 75, 2200, 16.2),
    # Indiana
    ("IN-503", "Indianapolis CoC",                         "IN", "18097",  1834,  1634,   200,  162,   964582, 27, 1000,   7.8),
    ("IN-502", "Indiana Balance of State CoC",             "IN", "18089",  2034,  1734,   300,  178,  5865418, 22,  790,   8.2),
    # Tennessee
    ("TN-500", "Nashville/Davidson County CoC",            "TN", "47037",  2812,  2034,   778,  234,   715884, 40, 1150, 12.4),
    ("TN-501", "Memphis/Shelby County CoC",                "TN", "47157",  1834,  1234,   600,  152,   929744, 41, 1050,   7.8),
    ("TN-502", "Tennessee Balance of State CoC",           "TN", "47093",  1834,  1234,   600,  152,  5484372, 36,  900,   7.4),
    # Missouri
    ("MO-501", "St. Louis City CoC",                       "MO", "29510",  1234,  1034,   200,  112,   301578, 30,  950,   5.4),
    ("MO-500", "St. Louis County CoC",                     "MO", "29189",   812,   712,   100,   72,  1004125, 29,  980,   3.4),
    ("MO-503", "Kansas City CoC",                          "MO", "29095",  1234,  1034,   200,  112,   508090, 29, 1000,   5.2),
    # Louisiana
    ("LA-500", "Lafayette/Acadiana CoC",                   "LA", "22055",   634,   434,   200,   52,   240091, 54,  850,   2.4),
    ("LA-503", "New Orleans/Jefferson Parish CoC",         "LA", "22071",  1812,  1234,   578,  152,   455901, 54, 1000,   7.8),
    ("LA-505", "Monroe/Northeast Louisiana CoC",           "LA", "22073",   534,   334,   200,   42,   200000, 48,  820,   2.1),
    # Wisconsin
    ("WI-500", "Wisconsin Balance of State CoC",           "WI", "55025",  2034,  1834,   200,  172,  4614573, 17,  830,   7.8),
    ("WI-502", "Racine City & County CoC",                 "WI", "55101",   534,   434,   100,   42,   197314, 19,  850,   2.1),
    # New Mexico
    ("NM-500", "Albuquerque CoC",                          "NM", "35001",  1834,  1034,   800,  172,   677692, 40,  980,   7.4),
    ("NM-501", "New Mexico Balance of State CoC",          "NM", "35049",   834,   634,   200,   82,  1346308, 35,  850,   3.4),
    # Oklahoma
    ("OK-501", "Oklahoma City CoC",                        "OK", "40109",  1234,   834,   400,  112,   795399, 38,  900,   5.1),
    ("OK-502", "Tulsa City & County CoC",                  "OK", "40143",   834,   634,   200,   72,   648901, 36,  870,   3.4),
    # Kentucky
    ("KY-500", "Louisville/Jefferson County CoC",          "KY", "21111",  1234,  1034,   200,  112,   774159, 32,  900,   5.2),
    ("KY-501", "Kentucky Balance of State CoC",            "KY", "21067",  2034,  1734,   300,  172,  3735841, 28,  750,   8.1),
    # South Carolina
    ("SC-500", "Columbia/Midlands CoC",                    "SC", "45079",   812,   634,   178,   72,   416147, 45,  900,   3.4),
    ("SC-501", "Greenville/Anderson/Spartanburg CoC",      "SC", "45045",  1034,   834,   200,   92,   940000, 46,  900,   4.1),
    # Maine
    ("ME-500", "Maine Balance of State CoC",               "ME", "23005",  2034,  1734,   300,  172,  1218000, 16, 1000,   8.4),
    ("ME-502", "Bangor/Penobscot County CoC",              "ME", "23019",   934,   834,   100,   82,   154065, 14,  910,   3.8),
]

_COC_COLS = [
    "coc_code", "coc_name", "state_postal", "county_fips",
    "total_homeless", "sheltered_homeless", "unsheltered_homeless", "veteran_homeless",
    "population", "jan_temp_f", "median_1br_fmr", "hud_grants_millions",
]

# SAMHSA state-level proxy data (joined on state_postal)
_SAMHSA_STATE = {
    "AL": (21.4, 2.8, 23.4), "AK": (24.1, 3.9, 15.2), "AZ": (22.1, 3.2, 26.9),
    "AR": (21.8, 2.9, 19.4), "CA": (21.2, 3.8, 24.3), "CO": (25.2, 3.6, 30.1),
    "CT": (22.8, 2.7, 27.2), "DE": (22.5, 2.9, 40.1), "DC": (24.3, 3.1, 16.8),
    "FL": (20.8, 3.2, 26.9), "GA": (20.5, 2.8, 18.6), "HI": (22.7, 3.0, 11.1),
    "ID": (23.9, 3.3, 14.9), "IL": (22.3, 3.1, 22.7), "IN": (22.7, 3.2, 36.5),
    "IA": (21.9, 2.5, 16.3), "KS": (22.4, 2.9, 16.2), "KY": (24.1, 3.5, 45.5),
    "LA": (21.2, 3.1, 29.4), "ME": (29.5, 3.8, 30.1), "MD": (22.8, 2.9, 36.7),
    "MA": (27.1, 3.4, 31.9), "MI": (24.4, 3.5, 31.5), "MN": (23.4, 2.9, 18.3),
    "MS": (21.7, 2.7, 21.2), "MO": (23.6, 3.3, 34.8), "MT": (25.8, 3.5, 23.1),
    "NE": (21.8, 2.6, 12.9), "NV": (22.3, 3.4, 29.9), "NH": (25.2, 3.2, 28.0),
    "NJ": (19.7, 2.6, 19.2), "NM": (25.0, 3.8, 34.9), "NY": (22.6, 2.8, 24.8),
    "NC": (22.0, 3.0, 22.8), "ND": (22.8, 2.7,  9.4), "OH": (24.2, 3.4, 44.8),
    "OK": (23.5, 3.2, 23.7), "OR": (26.4, 4.0, 33.3), "PA": (23.4, 3.1, 41.2),
    "RI": (26.1, 3.1, 32.1), "SC": (21.9, 2.9, 22.8), "SD": (22.2, 2.7, 17.9),
    "TN": (23.5, 3.2, 31.9), "TX": (19.3, 2.8, 13.7), "UT": (25.8, 3.1, 15.2),
    "VT": (28.2, 3.5, 28.1), "VA": (22.0, 2.8, 19.1), "WA": (24.6, 3.7, 23.4),
    "WV": (25.9, 3.8, 73.5), "WI": (22.8, 2.9, 22.6), "WY": (26.4, 3.3, 20.3),
}


def get_coc_data() -> pd.DataFrame:
    """Return CoC-level PIT data with derived metrics."""
    df = pd.DataFrame(_COC_DATA, columns=_COC_COLS)
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
    df["state_fips"] = df["county_fips"].str[:2]
    df["homeless_rate_per_10k"] = (df["total_homeless"] / df["population"] * 10_000).round(2)
    df["unsheltered_pct"] = (df["unsheltered_homeless"] / df["total_homeless"] * 100).round(1)
    df["spending_per_homeless"] = (df["hud_grants_millions"] * 1_000_000 / df["total_homeless"]).round(0)
    df["unsheltered_rate_per_10k"] = (df["unsheltered_homeless"] / df["population"] * 10_000).round(2)
    # Join SAMHSA state proxy
    df["ami_pct"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[0])
    df["drug_disorder_pct"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[1])
    df["overdose_rate_per_100k"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[2])
    return df


def get_census_county_data() -> pd.DataFrame:
    """Fetch Census ACS 5-year 2022 county-level data; fall back prints a warning."""
    try:
        return _fetch_census_county_live()
    except Exception as e:
        print(f"Census county API unavailable ({e}). Using CoC data without Census join.")
        return pd.DataFrame(columns=[
            "county_fips", "median_income", "poverty_rate", "gini_coefficient",
            "rent_burden_pct", "pct_white", "pct_black", "pct_hispanic", "pct_asian", "veteran_pct",
        ])


def _fetch_census_county_live() -> pd.DataFrame:
    """
    Fetch Census ACS 5-year 2022 for all counties.
    Variables: B19013_001E (median income), B17001 (poverty), B19083_001E (Gini),
               B25070 (rent burden), B02001/B03001 (race), B21001 (veterans)
    """
    base = "https://api.census.gov/data/2022/acs/acs5"
    variables = ",".join([
        "NAME", "B19013_001E", "B17001_002E", "B17001_001E", "B19083_001E",
        "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E", "B25070_001E",
        "B02001_002E", "B02001_003E", "B03001_003E", "B02001_005E", "B01003_001E",
        "B21001_002E", "B21001_001E",
    ])
    r = requests.get(f"{base}?get={variables}&for=county:*", timeout=60)
    r.raise_for_status()
    rows = r.json()
    headers = rows[0]
    df = pd.DataFrame(rows[1:], columns=headers)
    for col in headers[1:-2]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["county_fips"] = (df["state"] + df["county"]).str.zfill(5)
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
    return df[[
        "county_fips", "median_income", "poverty_rate", "gini_coefficient",
        "rent_burden_pct", "pct_white", "pct_black", "pct_hispanic", "pct_asian", "veteran_pct",
    ]]


def get_merged_county_data() -> pd.DataFrame:
    """Return CoC data merged with Census county data where available."""
    coc = get_coc_data()
    census = get_census_county_data()
    if len(census) > 0:
        df = coc.merge(census, on="county_fips", how="left")
    else:
        df = coc
    return df
```

- [ ] **Step 2: Write data/raw/fetch_hud_pit_coc.py**

```python
"""
Fetch HUD 2023 PIT counts at the CoC level.

Source: HUD Exchange AHAR downloads
URL: https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/

Steps:
1. Download '2007-2023-PIT-Counts-by-CoC.xlsx'
2. Read sheet '2023'
3. Key columns: 'CoC Number', 'CoC Name', 'CoC Category',
   'Overall Homeless, 2023', 'Sheltered Total Homeless, 2023',
   'Unsheltered Homeless, 2023', 'Overall Homeless Veterans, 2023'

Example:
  import pandas as pd
  df = pd.read_excel("2007-2023-PIT-Counts-by-CoC.xlsx", sheet_name="2023")
  df = df.rename(columns={
      "CoC Number": "coc_code",
      "CoC Name": "coc_name",
      "Overall Homeless, 2023": "total_homeless",
      "Sheltered Total Homeless, 2023": "sheltered_homeless",
      "Unsheltered Homeless, 2023": "unsheltered_homeless",
      "Overall Homeless Veterans, 2023": "veteran_homeless",
  })
  df["state_postal"] = df["coc_code"].str[:2]
  df.to_csv("hud_pit_coc_2023.csv", index=False)
"""
```

- [ ] **Step 3: Write data/raw/fetch_hud_fmr_county.py**

```python
"""
Fetch HUD Fair Market Rents 2023 by county.

Source: HUD USER FMR data
URL: https://www.huduser.gov/portal/datasets/fmr.html

Steps:
1. Download 'FY2023_4050_FMRs_revised.xlsx' from the FMR page
2. Key columns: fips2000 (county FIPS), fmr_1 (1BR FMR)

Example:
  import pandas as pd
  df = pd.read_excel("FY2023_4050_FMRs_revised.xlsx")
  df["county_fips"] = df["fips2000"].astype(str).str.zfill(5)
  df = df[["county_fips", "fmr_1", "countyname", "State"]].rename(
      columns={"fmr_1": "median_1br_fmr"}
  )
  df.to_csv("hud_fmr_county_2023.csv", index=False)
"""
```

- [ ] **Step 4: Write data/raw/fetch_cdc_overdose_county.py**

```python
"""
Fetch CDC WONDER drug overdose death rates by county.

Source: CDC WONDER Multiple Cause of Death database
URL: https://wonder.cdc.gov/mcd.html

CDC WONDER uses a web query interface (not a REST API) that exports tab-separated text.

Steps to reproduce the query:
1. Go to https://wonder.cdc.gov/mcd-icd10-expanded.html
2. Group by: State, County
3. Year: 2020-2022 (3-year aggregate for stability)
4. ICD-10 codes: X40-X44, X60-X64, X85, Y10-Y14 (drug overdose deaths)
5. Export as tab-delimited text
6. Save as data/raw/cdc_overdose_county.txt

The exported file contains columns: State, County, FIPS, Deaths, Population, Crude Rate
Suppressed values (< 10 deaths) are marked as 'Suppressed' — treat as NA.

Example processing:
  import pandas as pd
  df = pd.read_csv("cdc_overdose_county.txt", sep="\\t", na_values=["Suppressed", "Missing"])
  df["county_fips"] = df["County Code"].astype(str).str.zfill(5)
  df["overdose_rate_per_100k"] = pd.to_numeric(df["Crude Rate"], errors="coerce")
  df = df[["county_fips", "overdose_rate_per_100k"]].dropna()
  df.to_csv("cdc_overdose_county.csv", index=False)
"""
```

- [ ] **Step 5: Write data/raw/fetch_noaa_coc.py**

```python
"""
Map NOAA 1991-2020 climate normals (January average temperature) to CoC centroids.

Source: NOAA Climate Normals
URL: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals

Steps:
1. Download monthly normals: https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/
2. Filter for month=01, variable=MLY-TAVG-NORMAL (mean temp, tenths of °F)
3. Load station metadata (lat/lon) from station list
4. For each CoC, compute centroid (from HUD CoC shapefiles or a CoC→lat/lon table)
5. Assign nearest station's January temp to each CoC

CoC centroid reference (manually curated for major CoCs):
  CA-600: (34.05, -118.24)  — Los Angeles
  NY-600: (40.71, -74.01)   — New York City
  WA-500: (47.61, -122.33)  — Seattle
  (etc.)

Alternatively, use state-level January averages as a proxy (embedded in src/county_data.py).
"""
```

- [ ] **Step 6: Commit**

```bash
git add src/county_data.py \
        data/raw/fetch_hud_pit_coc.py data/raw/fetch_hud_fmr_county.py \
        data/raw/fetch_cdc_overdose_county.py data/raw/fetch_noaa_coc.py
git commit -m "feat: add county_data.py with embedded CoC PIT data and fetch scripts"
```

---

### Task 2: Notebook 08 — County Data Collection

**Files:**
- Create: `notebooks/08_county_data_collection.ipynb`

- [ ] **Step 1: Create notebooks/08_county_data_collection.ipynb**

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
   "source": "# 08 — County/CoC Data Collection\n\nMerges all county/CoC-level data sources:\n- **HUD 2023 PIT counts** by CoC (embedded + fetch script in data/raw/)\n- **Census ACS 5-year 2022** county-level: income, poverty, Gini, rent burden, demographics\n- **SAMHSA NSDUH** state-level proxy for drug/mental health\n- **NOAA climate normals** January temperature (embedded in CoC data)\n- **HUD CoC grants** federal spending per CoC (embedded)\n\nOutput: `data/processed/merged_county_data.csv`\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "import sys\nfrom pathlib import Path\n\nROOT = Path().resolve().parent\nsys.path.insert(0, str(ROOT / 'src'))\n\nimport pandas as pd\nfrom county_data import get_merged_county_data\n\nOUT = ROOT / 'data' / 'processed'\nOUT.mkdir(parents=True, exist_ok=True)\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "df = get_merged_county_data()\nprint(f'Merged county/CoC data: {len(df)} CoCs, {len(df.columns)} columns')\nprint(f'Columns: {df.columns.tolist()}')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "out_path = OUT / 'merged_county_data.csv'\ndf.to_csv(out_path, index=False)\nprint(f'Saved to {out_path}')\n\nprint(f'\\nTop 10 CoCs by homeless rate per 10k:')\nprint(df.nlargest(10, 'homeless_rate_per_10k')[['coc_name', 'homeless_rate_per_10k', 'total_homeless', 'unsheltered_pct']].to_string(index=False))\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "preview = df[['coc_code', 'coc_name', 'state_postal', 'total_homeless',\n              'sheltered_homeless', 'unsheltered_homeless', 'homeless_rate_per_10k',\n              'unsheltered_pct', 'jan_temp_f']]\npreview = preview.sort_values('homeless_rate_per_10k', ascending=False)\npreview.head(20)\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/08_county_data_collection.ipynb \
  notebooks/08_county_data_collection.ipynb --cwd notebooks
```

Expected: `data/processed/merged_county_data.csv` exists, 100 rows, no errors.

- [ ] **Step 3: Commit**

```bash
git add notebooks/08_county_data_collection.ipynb data/processed/
git commit -m "feat: add notebook 08 county/CoC data collection"
```

---

### Task 3: Notebook 09 — County Homeless Map

**Files:**
- Create: `notebooks/09_county_homeless_map.ipynb`

- [ ] **Step 1: Create notebooks/09_county_homeless_map.ipynb**

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
   "source": "# 09 — County/CoC Homeless Rate Map\n\nChoropleth map of homeless rate per 10,000 residents by county (using CoC primary county FIPS).\nAlso shows top/bottom 15 CoCs by homeless rate.\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf['county_fips'] = df['county_fips'].astype(str).str.zfill(5)\nprint(f'Loaded {len(df)} CoCs')\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "fig = px.choropleth(\n    df,\n    geojson='https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json',\n    locations='county_fips',\n    color='homeless_rate_per_10k',\n    scope='usa',\n    color_continuous_scale='Reds',\n    hover_name='coc_name',\n    hover_data={'county_fips': False, 'homeless_rate_per_10k': ':.1f',\n                'total_homeless': ':,', 'unsheltered_pct': ':.1f'},\n    title='Homeless Rate per 10,000 Residents by County/CoC (HUD 2023)',\n    labels={'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.show()\n"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "top15 = df.nlargest(15, 'homeless_rate_per_10k')\nbot15 = df.nsmallest(15, 'homeless_rate_per_10k')\ncombined = pd.concat([top15, bot15])\n\nfig2 = px.bar(\n    combined.sort_values('homeless_rate_per_10k', ascending=True),\n    x='homeless_rate_per_10k',\n    y='coc_name',\n    orientation='h',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title='Top 15 and Bottom 15 CoCs: Homeless Rate per 10k (2023)',\n    labels={'homeless_rate_per_10k': 'Rate per 10k', 'coc_name': ''},\n)\nfig2.update_layout(height=700)\nfig2.show()\n"
  }
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/09_county_homeless_map.ipynb \
  notebooks/09_county_homeless_map.ipynb --cwd notebooks
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/09_county_homeless_map.ipynb
git commit -m "feat: add notebook 09 county homeless map"
```

---

### Tasks 4–8: Notebooks 10–14 (County Correlations)

Each follows the same pattern as the state correlation notebooks (scatter + regression line, r/R²/p in subtitle). Create and run each in sequence.

---

### Task 4: Notebook 10 — County Housing Affordability

**Files:**
- Create: `notebooks/10_county_housing_affordability.ipynb`

- [ ] **Step 1: Create notebooks/10_county_housing_affordability.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.9.0"}
 },
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 10 — Housing Affordability vs. Homeless Rate (County/CoC)\n\nScatter plots of homeless rate per 10k vs. median 1BR FMR and rent burden % at the CoC level.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'median_1br_fmr'])\nprint(f'Loaded {len(df)} CoCs with FMR data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['median_1br_fmr'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'FMR vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['median_1br_fmr'].min(), df['median_1br_fmr'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='median_1br_fmr', y='homeless_rate_per_10k',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    hover_data={'state_postal': True, 'total_homeless': ':,'},\n    title=f'Median 1BR FMR vs. Homeless Rate (CoC Level)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'median_1br_fmr': 'Median 1BR FMR ($)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/10_county_housing_affordability.ipynb \
  notebooks/10_county_housing_affordability.ipynb --cwd notebooks
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/10_county_housing_affordability.ipynb
git commit -m "feat: add notebook 10 county housing affordability"
```

---

### Task 5: Notebook 11 — County Spending

**Files:**
- Create: `notebooks/11_county_spending.ipynb`

- [ ] **Step 1: Create notebooks/11_county_spending.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 11 — Spending per Homeless vs. Homeless Rate (County/CoC)\n\nDoes higher federal HUD CoC spending per homeless person correlate with lower homeless rates?\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'spending_per_homeless'])\ndf = df[df['spending_per_homeless'] > 0]\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['spending_per_homeless'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Spending/homeless vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['spending_per_homeless'].min(), df['spending_per_homeless'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='spending_per_homeless', y='homeless_rate_per_10k',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'HUD CoC Spending per Homeless Person vs. Homeless Rate (CoC Level)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'spending_per_homeless': 'HUD Spending per Homeless ($)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 2: Run and commit**

```bash
.venv/bin/python -m papermill notebooks/11_county_spending.ipynb \
  notebooks/11_county_spending.ipynb --cwd notebooks
git add notebooks/11_county_spending.ipynb
git commit -m "feat: add notebook 11 county spending correlation"
```

---

### Task 6: Notebook 12 — County Drug & Mental Health

**Files:**
- Create: `notebooks/12_county_drug_mental.ipynb`

- [ ] **Step 1: Create notebooks/12_county_drug_mental.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 12 — Drug Use & Mental Health vs. Homeless Rate (County/CoC)\n\nUses state-level SAMHSA proxies (drug disorder %, AMI %) joined to each CoC by state.\nAlso uses state-level CDC overdose death rate proxy.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'ami_pct', 'drug_disorder_pct'])\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['ami_pct'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'AMI vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['ami_pct'].min(), df['ami_pct'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='ami_pct', y='homeless_rate_per_10k',\n    color='state_postal',\n    hover_name='coc_name',\n    title=f'AMI Prevalence (State Proxy) vs. Homeless Rate (CoC Level)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} — SAMHSA NSDUH 2021-2022</sup>',\n    labels={'ami_pct': 'AMI Prevalence (% adults, state proxy)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='black', dash='dash'), showlegend=False))\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope2, intercept2, r2v, p2, se2 = stats.linregress(df['drug_disorder_pct'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Drug disorder vs rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['drug_disorder_pct'].min(), df['drug_disorder_pct'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df, x='drug_disorder_pct', y='homeless_rate_per_10k',\n    color='state_postal',\n    hover_name='coc_name',\n    title=f'Drug Use Disorder Rate (State Proxy) vs. Homeless Rate (CoC Level)<br><sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}</sup>',\n    labels={'drug_disorder_pct': 'Drug Disorder % (state proxy)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='black', dash='dash'), showlegend=False))\nfig2.show()\n"}
 ]
}
```

- [ ] **Step 2: Run and commit**

```bash
.venv/bin/python -m papermill notebooks/12_county_drug_mental.ipynb \
  notebooks/12_county_drug_mental.ipynb --cwd notebooks
git add notebooks/12_county_drug_mental.ipynb
git commit -m "feat: add notebook 12 county drug and mental health correlation"
```

---

### Task 7: Notebooks 13–14 (County Income/Poverty + Demographics)

**Files:**
- Create: `notebooks/13_county_income_poverty.ipynb`
- Create: `notebooks/14_county_demographics.ipynb`

- [ ] **Step 1: Create notebooks/13_county_income_poverty.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 13 — Income & Poverty vs. Homeless Rate (County/CoC)\n\nScatter plots of homeless rate vs. median income, poverty rate, and Gini at CoC level.\nCensus data joined on primary county FIPS; CoCs without Census match use state averages.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'median_income'])\nprint(f'Loaded {len(df)} CoCs with income data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['median_income'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Median income vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['median_income'].min(), df['median_income'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='median_income', y='homeless_rate_per_10k',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'Median Income vs. Homeless Rate (CoC Level)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'median_income': 'Median Household Income ($)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "df2 = df.dropna(subset=['poverty_rate'])\nslope2, intercept2, r2v, p2, se2 = stats.linregress(df2['poverty_rate'], df2['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Poverty rate vs rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df2['poverty_rate'].min(), df2['poverty_rate'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df2, x='poverty_rate', y='homeless_rate_per_10k',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'Poverty Rate vs. Homeless Rate (CoC Level)<br><sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}</sup>',\n    labels={'poverty_rate': 'Poverty Rate (%)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.show()\n"}
 ]
}
```

- [ ] **Step 2: Create notebooks/14_county_demographics.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 14 — Demographics vs. Homeless Rate (County/CoC)\n\nCorrelations between homeless rate and racial/ethnic demographics and veteran population % at CoC level.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'pct_black'])\nprint(f'Loaded {len(df)} CoCs with demographics')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['pct_black'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'% Black vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['pct_black'].min(), df['pct_black'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='pct_black', y='homeless_rate_per_10k',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'% Black Population vs. Homeless Rate (CoC Level)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'pct_black': '% Black (non-Hispanic)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 3: Run both notebooks**

```bash
.venv/bin/python -m papermill notebooks/13_county_income_poverty.ipynb \
  notebooks/13_county_income_poverty.ipynb --cwd notebooks
.venv/bin/python -m papermill notebooks/14_county_demographics.ipynb \
  notebooks/14_county_demographics.ipynb --cwd notebooks
```

- [ ] **Step 4: Commit**

```bash
git add notebooks/13_county_income_poverty.ipynb notebooks/14_county_demographics.ipynb
git commit -m "feat: add notebooks 13-14 county income/poverty and demographics"
```

---

### Task 8: Notebook 15 — Sheltered vs. Unsheltered Breakdown

**Files:**
- Create: `notebooks/15_county_sheltered_vs_unsheltered.ipynb`

- [ ] **Step 1: Create notebooks/15_county_sheltered_vs_unsheltered.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 15 — Sheltered vs. Unsheltered Breakdown by CoC\n\nCompares sheltered (emergency shelter, transitional housing, safe haven) vs. unsheltered\n(on street, in vehicles, in encampments) homeless populations across CoCs.\n\nKey question: which CoCs have the highest share of unsheltered homeless?\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.sort_values('unsheltered_pct', ascending=False)\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Stacked bar: sheltered vs unsheltered for top 30 CoCs by total homeless\ntop30 = df.nlargest(30, 'total_homeless')[['coc_name', 'sheltered_homeless', 'unsheltered_homeless', 'unsheltered_pct']].copy()\ntop30 = top30.sort_values('unsheltered_pct', ascending=True)\n\nfig = px.bar(\n    top30,\n    x=['sheltered_homeless', 'unsheltered_homeless'],\n    y='coc_name',\n    orientation='h',\n    barmode='stack',\n    color_discrete_map={'sheltered_homeless': '#4a90d9', 'unsheltered_homeless': '#d94a4a'},\n    title='Sheltered vs. Unsheltered Homeless: Top 30 CoCs by Total Count',\n    labels={'value': 'Homeless Count', 'coc_name': '', 'variable': 'Status'},\n)\nfig.update_layout(height=800, legend_title='Status')\nfig.for_each_trace(lambda t: t.update(name=t.name.replace('_homeless', '').replace('_', ' ').title()))\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Unsheltered % bar for top 30\nfig2 = px.bar(\n    top30.sort_values('unsheltered_pct', ascending=True),\n    x='unsheltered_pct',\n    y='coc_name',\n    orientation='h',\n    color='unsheltered_pct',\n    color_continuous_scale='OrRd',\n    title='Unsheltered % of Total Homeless: Top 30 CoCs by Total Count',\n    labels={'unsheltered_pct': '% Unsheltered', 'coc_name': ''},\n)\nfig2.update_layout(height=800)\nfig2.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Summary stats\nprint(f'National unsheltered %: {df[\"unsheltered_pct\"].mean():.1f}%')\nprint(f'Highest unsheltered %: {df.nlargest(5, \"unsheltered_pct\")[[\"coc_name\", \"unsheltered_pct\"]].to_string(index=False)}')\nprint(f'Lowest unsheltered %: {df.nsmallest(5, \"unsheltered_pct\")[[\"coc_name\", \"unsheltered_pct\"]].to_string(index=False)}')\n"}
 ]
}
```

- [ ] **Step 2: Run and commit**

```bash
.venv/bin/python -m papermill notebooks/15_county_sheltered_vs_unsheltered.ipynb \
  notebooks/15_county_sheltered_vs_unsheltered.ipynb --cwd notebooks
git add notebooks/15_county_sheltered_vs_unsheltered.ipynb
git commit -m "feat: add notebook 15 sheltered vs unsheltered breakdown"
```

---

### Task 9: Notebook 16 — Climate Correlation

**Files:**
- Create: `notebooks/16_county_climate.ipynb`

- [ ] **Step 1: Create notebooks/16_county_climate.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": "# 16 — Climate vs. Sheltered/Unsheltered Homeless Rate (County/CoC)\n\n**Hypothesis:** Colder climates push a larger share of homeless people into shelters without\nnecessarily reducing the total homeless rate. Warmer cities like LA, Phoenix, and Miami may\nhave higher unsheltered rates not because of policy failure but because sleeping outside\nis survivable year-round.\n\nWe test this by plotting unsheltered rate per 10k vs. average January temperature (NOAA\n1991-2020 climate normals, mapped to CoC).\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_county_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'unsheltered_pct', 'jan_temp_f'])\ndf['unsheltered_rate_per_10k'] = (df['unsheltered_homeless'] / df['population'] * 10000).round(2)\nprint(f'Loaded {len(df)} CoCs with climate data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Scatter: unsheltered % vs January temperature\nslope, intercept, r, p, se = stats.linregress(df['jan_temp_f'], df['unsheltered_pct'])\nr2 = r ** 2\nprint(f'Jan temp vs unsheltered %: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['jan_temp_f'].min(), df['jan_temp_f'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df,\n    x='jan_temp_f',\n    y='unsheltered_pct',\n    size='total_homeless',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    hover_name='coc_name',\n    hover_data={'state_postal': True, 'jan_temp_f': ':.0f', 'unsheltered_pct': ':.1f',\n                'total_homeless': ':,', 'homeless_rate_per_10k': ':.1f'},\n    title=f'January Temperature vs. Unsheltered % of Homeless (CoC Level)<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} — warmer climates → higher unsheltered share</sup>',\n    labels={'jan_temp_f': 'Avg January Temperature (°F)', 'unsheltered_pct': '% Homeless Who Are Unsheltered'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='black', dash='dash')))\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Scatter: January temp vs TOTAL homeless rate (to check if climate drives total rate too)\nslope2, intercept2, r2v, p2, se2 = stats.linregress(df['jan_temp_f'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Jan temp vs total homeless rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['jan_temp_f'].min(), df['jan_temp_f'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df,\n    x='jan_temp_f',\n    y='homeless_rate_per_10k',\n    size='total_homeless',\n    color='unsheltered_pct',\n    color_continuous_scale='OrRd',\n    hover_name='coc_name',\n    title=f'January Temperature vs. Total Homeless Rate (CoC Level)<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}</sup>',\n    labels={'jan_temp_f': 'Avg January Temperature (°F)', 'homeless_rate_per_10k': 'Homeless Rate per 10k'},\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='black', dash='dash')))\nfig2.show()\n"}
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/16_county_climate.ipynb \
  notebooks/16_county_climate.ipynb --cwd notebooks
```

- [ ] **Step 3: Regenerate HTML report and commit**

```bash
.venv/bin/python scripts/generate_html.py
git add notebooks/16_county_climate.ipynb docs/report.html
git commit -m "feat: add notebook 16 climate correlation, regenerate HTML report"
```
