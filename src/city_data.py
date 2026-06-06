"""
City/CoC-level homelessness data utilities.

Adds lat/lon centroids and primary city names to the CoC dataset for bubble maps.
Re-uses embedded CoC data from county_data to avoid duplication.

Sources:
- Same as county_data.py (HUD 2023 PIT, HUD FMR, NOAA, SAMHSA, HUD grants)
- CoC centroid lat/lon: manually curated from HUD CoC shapefiles
- Primary city name: derived from CoC name (first city mentioned)
"""

import pandas as pd
from county_data import _COC_DATA, _COC_COLS, _SAMHSA_STATE, _ELECTION_COUNTY_2020

# CoC centroid coordinates (lat, lon) for major CoCs
# Source: HUD CoC shapefiles (https://www.hudexchange.info/programs/coc/gis-tools/)
_COC_CENTROIDS = {
    "CA-600": (34.05, -118.24),  "CA-601": (32.72, -117.15),
    "CA-500": (38.58, -121.49),  "CA-502": (37.80, -122.27),
    "CA-501": (37.77, -122.42),
    "CA-516": (36.74, -119.77),  "CA-511": (34.15, -118.14),
    "CA-522": (40.80, -124.16),  "CA-526": (37.90, -122.04),
    "CA-524": (38.68, -121.82),  "CA-606": (33.77, -118.19),
    "CA-612": (34.14, -118.26),  "CA-614": (37.34, -121.89),
    "CA-608": (33.98, -117.40),
    "NY-600": (40.71, -74.01),   "NY-505": (43.05, -76.15),
    "NY-603": (40.73, -73.59),   "NY-606": (41.11, -73.99),
    "NY-507": (42.81, -73.94),
    "WA-500": (47.61, -122.33),  "WA-501": (47.25, -120.50),
    "WA-502": (47.66, -117.43),  "WA-503": (47.25, -122.44),
    "OR-501": (45.52, -122.68),  "OR-505": (44.50, -122.50),
    "OR-502": (42.33, -122.87),
    "TX-700": (29.76, -95.37),   "TX-600": (32.78, -96.80),
    "TX-601": (32.75, -97.33),   "TX-503": (30.27, -97.74),
    "TX-604": (31.55, -97.15),
    "FL-500": (27.34, -82.54),   "FL-501": (27.95, -82.46),
    "FL-507": (28.54, -81.38),   "FL-519": (28.25, -82.13),
    "FL-600": (25.77, -80.19),
    "CO-503": (39.74, -104.98),  "CO-500": (39.10, -105.50),
    "CO-504": (38.83, -104.82),
    "MA-500": (42.36, -71.06),   "MA-516": (42.00, -71.50),
    "MA-502": (42.47, -70.95),
    "AZ-502": (33.45, -112.07),  "AZ-500": (34.00, -112.00),
    "AZ-501": (32.22, -110.97),
    "IL-510": (41.88, -87.63),   "IL-500": (40.50, -89.00),
    "IL-514": (41.85, -88.02),
    "MN-500": (44.98, -93.27),   "MN-501": (44.95, -93.09),
    "MN-502": (44.02, -92.46),
    "PA-500": (39.95, -75.17),   "PA-501": (40.44, -80.00),
    "PA-502": (40.50, -77.00),
    "GA-500": (33.75, -84.39),   "GA-501": (32.50, -83.00),
    "NV-500": (36.17, -115.14),  "NV-501": (39.53, -119.81),
    "MI-501": (42.33, -83.05),   "MI-502": (42.31, -83.18),
    "MI-523": (43.01, -83.69),
    "OH-500": (39.10, -84.51),   "OH-501": (41.66, -83.56),
    "OH-503": (39.96, -82.99),   "OH-504": (41.10, -80.65),
    "OH-507": (41.50, -81.69),
    "MD-501": (39.29, -76.61),   "MD-500": (39.00, -76.80),
    "VA-501": (37.27, -79.94),   "VA-505": (37.10, -76.40),
    "VA-600": (38.88, -77.11),   "VA-521": (38.00, -78.50),
    "NC-507": (35.78, -78.64),   "NC-505": (35.23, -80.84),
    "NC-501": (35.99, -78.90),   "NC-502": (35.50, -79.50),
    "HI-500": (20.89, -156.47),  "HI-501": (21.31, -157.86),
    "IN-503": (39.77, -86.16),   "IN-502": (40.00, -86.50),
    "TN-500": (36.17, -86.78),   "TN-501": (35.15, -90.05),
    "TN-502": (36.00, -86.00),
    "MO-501": (38.63, -90.20),   "MO-500": (38.75, -90.40),
    "MO-503": (39.10, -94.58),
    "LA-500": (30.22, -92.02),   "LA-503": (29.95, -90.07),
    "LA-505": (32.51, -92.11),
    "WI-500": (44.50, -90.00),   "WI-502": (42.73, -87.78),
    "NM-500": (35.08, -106.65),  "NM-501": (34.50, -106.00),
    "OK-501": (35.47, -97.52),   "OK-502": (36.15, -95.99),
    "KY-500": (38.25, -85.76),   "KY-501": (37.50, -85.00),
    "SC-500": (34.00, -81.03),   "SC-501": (34.85, -82.40),
    "ME-500": (44.50, -69.00),   "ME-502": (44.80, -68.78),
}

# Primary city name for each CoC (for chart labeling)
_COC_CITY_NAMES = {
    "CA-600": "Los Angeles", "CA-601": "San Diego", "CA-500": "Sacramento",
    "CA-502": "Oakland", "CA-501": "San Francisco",
    "CA-516": "Fresno", "CA-511": "Pasadena", "CA-522": "Eureka",
    "CA-526": "Contra Costa", "CA-524": "Woodland", "CA-606": "Long Beach",
    "CA-612": "Glendale", "CA-614": "San Jose", "CA-608": "Riverside",
    "NY-600": "New York City", "NY-505": "Syracuse", "NY-603": "Nassau/Suffolk",
    "NY-606": "Rockland", "NY-507": "Schenectady",
    "WA-500": "Seattle", "WA-501": "WA Balance", "WA-502": "Spokane",
    "WA-503": "Tacoma",
    "OR-501": "Portland", "OR-505": "OR Balance", "OR-502": "Medford",
    "TX-700": "Houston", "TX-600": "Dallas", "TX-601": "Fort Worth",
    "TX-503": "Austin", "TX-604": "Waco",
    "FL-500": "Sarasota", "FL-501": "Tampa", "FL-507": "Orlando",
    "FL-519": "Pasco", "FL-600": "Miami",
    "CO-503": "Denver", "CO-500": "CO Balance", "CO-504": "Colorado Springs",
    "MA-500": "Boston", "MA-516": "MA Balance", "MA-502": "Lynn",
    "AZ-502": "Phoenix", "AZ-500": "AZ Balance", "AZ-501": "Tucson",
    "IL-510": "Chicago", "IL-500": "IL Balance", "IL-514": "DuPage",
    "MN-500": "Minneapolis", "MN-501": "St. Paul", "MN-502": "Rochester",
    "PA-500": "Philadelphia", "PA-501": "Pittsburgh", "PA-502": "PA Balance",
    "GA-500": "Atlanta", "GA-501": "GA Balance",
    "NV-500": "Las Vegas", "NV-501": "Reno",
    "MI-501": "Detroit", "MI-502": "Dearborn", "MI-523": "Flint",
    "OH-500": "Cincinnati", "OH-501": "Toledo", "OH-503": "Columbus",
    "OH-504": "Youngstown", "OH-507": "Cleveland",
    "MD-501": "Baltimore", "MD-500": "MD Balance",
    "VA-501": "Roanoke", "VA-505": "Hampton Roads", "VA-600": "Arlington",
    "VA-521": "VA Balance",
    "NC-507": "Raleigh", "NC-505": "Charlotte", "NC-501": "Durham",
    "NC-502": "NC Balance",
    "HI-500": "HI Balance", "HI-501": "Honolulu",
    "IN-503": "Indianapolis", "IN-502": "IN Balance",
    "TN-500": "Nashville", "TN-501": "Memphis", "TN-502": "TN Balance",
    "MO-501": "St. Louis City", "MO-500": "St. Louis Co", "MO-503": "Kansas City",
    "LA-500": "Lafayette", "LA-503": "New Orleans", "LA-505": "Monroe",
    "WI-500": "WI Balance", "WI-502": "Racine",
    "NM-500": "Albuquerque", "NM-501": "NM Balance",
    "OK-501": "Oklahoma City", "OK-502": "Tulsa",
    "KY-500": "Louisville", "KY-501": "KY Balance",
    "SC-500": "Columbia", "SC-501": "Greenville",
    "ME-500": "ME Balance", "ME-502": "Bangor",
}


def get_city_data() -> pd.DataFrame:
    """Return CoC data with lat/lon centroids and city names."""
    df = pd.DataFrame(_COC_DATA, columns=_COC_COLS)
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
    df["state_fips"] = df["county_fips"].str[:2]
    df["lat"] = df["coc_code"].map(lambda c: _COC_CENTROIDS.get(c, (None, None))[0])
    df["lon"] = df["coc_code"].map(lambda c: _COC_CENTROIDS.get(c, (None, None))[1])
    df["city_name"] = df["coc_code"].map(lambda c: _COC_CITY_NAMES.get(c, c))
    df["homeless_rate_per_10k"] = (df["total_homeless"] / df["population"] * 10_000).round(2)
    df["unsheltered_pct"] = (df["unsheltered_homeless"] / df["total_homeless"] * 100).round(1)
    df["unsheltered_rate_per_10k"] = (df["unsheltered_homeless"] / df["population"] * 10_000).round(2)
    df["spending_per_homeless"] = (df["hud_grants_millions"] * 1_000_000 / df["total_homeless"]).round(0)
    df["veteran_rate_per_10k"] = (df["veteran_homeless"] / df["population"] * 10_000).round(2)
    # SAMHSA state proxy
    df["ami_pct"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[0])
    df["drug_disorder_pct"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[1])
    df["overdose_rate_per_100k"] = df["state_postal"].map(lambda s: _SAMHSA_STATE.get(s, (None,None,None))[2])
    df["biden_pct_2020"] = df["county_fips"].map(_ELECTION_COUNTY_2020)
    df["dem_pres_margin_2020"] = (df["biden_pct_2020"] * 2 - 100).round(1)
    return df


def get_merged_city_data() -> pd.DataFrame:
    """Return city data (no additional merge needed — all data embedded)."""
    return get_city_data()
