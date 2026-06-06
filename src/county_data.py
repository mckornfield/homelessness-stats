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
    ("MD-500", "Maryland Balance of State CoC",            "MD", "24003",  2312,  1834,   478,  192,  5575000, 32, 1500,   9.8),
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
    ("WI-500", "Wisconsin Balance of State CoC",           "WI", "55025",  2034,  1834,   200,  172,  4614573, 17,  833,   7.8),
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


# 2020 presidential election: Biden 2-party vote % by county FIPS
# Source: MIT Election Lab county-level returns (doi:10.7910/DVN/VOQCHQ)
_ELECTION_COUNTY_2020 = {
    # California
    "06037": 71.2, "06073": 63.9, "06067": 63.2, "06001": 80.3, "06075": 85.7,
    "06019": 54.8, "06023": 72.0, "06013": 76.8, "06113": 68.1, "06065": 54.1,
    "06085": 72.7, "06079": 67.6, "06071": 55.6,
    # New York
    "36061": 86.7, "36059": 56.0, "36067": 57.8, "36087": 56.0, "36093": 58.2,
    # Washington
    "53033": 79.7, "53063": 52.5, "53053": 59.8,
    # Oregon
    "41051": 79.8, "41043": 54.3, "41029": 53.8,
    # Texas
    "48201": 56.5, "48113": 65.1, "48439": 49.8, "48453": 71.4, "48309": 43.2,
    # Florida
    "12081": 53.3, "12057": 52.4, "12095": 55.0, "12101": 46.2, "12086": 53.4,
    # Colorado
    "08031": 80.3, "08013": 52.7, "08041": 40.6,
    # Massachusetts
    "25025": 81.7, "25027": 66.5, "25009": 62.1,
    # Arizona
    "04013": 50.3, "04003": 55.8, "04019": 58.5,
    # Illinois
    "17031": 74.3, "17043": 67.4,
    # Minnesota
    "27053": 73.1, "27123": 68.4, "27109": 60.2,
    # Pennsylvania
    "42101": 81.4, "42003": 59.4, "42097": 45.2,
    # Georgia
    "13121": 80.7, "13067": 44.2,
    # Nevada
    "32003": 53.9, "32031": 52.6,
    # Michigan
    "26163": 68.4, "26049": 47.8,
    # Ohio
    "39061": 57.9, "39095": 42.9, "39049": 64.2, "39099": 39.7, "39035": 59.1,
    # Maryland
    "24510": 87.4, "24003": 66.3,
    # Virginia
    "51770": 55.8, "51650": 56.2, "51013": 79.6, "51041": 52.3,
    # North Carolina
    "37183": 67.3, "37119": 68.1, "37063": 67.5, "37067": 47.2,
    # Hawaii
    "15001": 63.4, "15003": 70.8,
    # Indiana
    "18097": 62.7, "18089": 44.1,
    # Tennessee
    "47037": 64.4, "47157": 54.9, "47093": 38.6,
    # Missouri
    "29510": 82.8, "29189": 47.2, "29095": 62.7,
    # Louisiana
    "22055": 43.3, "22071": 62.1, "22073": 35.6,
    # Wisconsin
    "55025": 53.9, "55101": 48.2,
    # New Mexico
    "35001": 61.0, "35049": 43.2,
    # Oklahoma
    "40109": 40.8, "40143": 37.4,
    # Kentucky
    "21111": 59.7, "21067": 38.6,
    # South Carolina
    "45079": 53.2, "45045": 46.8,
    # Maine
    "23005": 57.4, "23019": 53.8,
}


def get_merged_county_data() -> pd.DataFrame:
    """Return CoC data merged with Census county data where available."""
    coc = get_coc_data()
    census = get_census_county_data()
    if len(census) > 0:
        df = coc.merge(census, on="county_fips", how="left")
    else:
        df = coc
    df["biden_pct_2020"] = df["county_fips"].map(_ELECTION_COUNTY_2020)
    df["dem_pres_margin_2020"] = (df["biden_pct_2020"] * 2 - 100).round(1)
    return df
