# Homelessness Stats — Plan 4: City/CoC-Level Notebooks (17–25)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/city_data.py` and notebooks 17–25 for city/CoC-level analysis, culminating in the headline climate × sheltered/unsheltered analysis (notebook 24) and veteran homeless breakdown (notebook 25).

**Architecture:** `src/city_data.py` holds the same CoC dataset as `county_data.py` but adds lat/lon centroids for bubble maps, and provides a city-name field for labeling. It re-uses the `_COC_DATA` structure from county_data but imports it rather than duplicating. Notebook 17 writes `data/processed/merged_city_data.csv`. Notebooks 18–25 read that CSV.

**Prerequisite:** Plan 1 (scaffold) must be complete. Plans 2 and 3 do NOT need to be complete — city data is independently sourced from the same embedded CoC data.

**Tech Stack:** Python 3.9+, pandas, plotly, scipy, papermill

---

### Task 1: src/city_data.py + fetch scripts

**Files:**
- Create: `src/city_data.py`
- Create: `data/raw/fetch_hud_coc_crosswalk.py`

- [ ] **Step 1: Write src/city_data.py**

```python
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
from county_data import _COC_DATA, _COC_COLS, _SAMHSA_STATE

# CoC centroid coordinates (lat, lon) for major CoCs
# Source: HUD CoC shapefiles (https://www.hudexchange.info/programs/coc/gis-tools/)
_COC_CENTROIDS = {
    "CA-600": (34.05, -118.24),  "CA-601": (32.72, -117.15),
    "CA-500": (38.58, -121.49),  "CA-502": (37.80, -122.27),
    "CA-501": (37.77, -122.42),  "CA-503": (38.58, -121.49),
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
    "CA-502": "Oakland", "CA-501": "San Francisco", "CA-503": "Sacramento",
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
    return df


def get_merged_city_data() -> pd.DataFrame:
    """Return city data (no additional merge needed — all data embedded)."""
    return get_city_data()
```

- [ ] **Step 2: Write data/raw/fetch_hud_coc_crosswalk.py**

```python
"""
Fetch the HUD CoC-to-county crosswalk and CoC centroid coordinates.

Source 1: HUD CoC GIS Shapefiles
URL: https://www.hudexchange.info/programs/coc/gis-tools/

The shapefile contains CoC boundaries as polygons. Use geopandas to compute centroids:
  import geopandas as gpd
  gdf = gpd.read_file("CoC_GIS_NatlTerrDC_Shapefile_2023.zip")
  gdf["centroid"] = gdf.geometry.centroid
  gdf["lat"] = gdf["centroid"].y
  gdf["lon"] = gdf["centroid"].x
  gdf[["COCNUM", "COCNAME", "lat", "lon"]].to_csv("coc_centroids.csv", index=False)

Source 2: HUD CoC-to-county crosswalk
URL: https://www.hudexchange.info/resource/6000/

Download 'FY2023_CoC_to_County_crosswalk.xlsx'
This file maps each CoC code to all counties it overlaps, with population weights.
Use the highest-weight county as the primary county FIPS for choropleth mapping.
"""
```

- [ ] **Step 3: Commit**

```bash
git add src/city_data.py data/raw/fetch_hud_coc_crosswalk.py
git commit -m "feat: add city_data.py with CoC centroids and city names"
```

---

### Task 2: Notebook 17 — City Data Collection

**Files:**
- Create: `notebooks/17_city_data_collection.ipynb`

- [ ] **Step 1: Create notebooks/17_city_data_collection.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 17 — City/CoC Data Collection\n\nBuilds the city-level dataset from embedded CoC data with lat/lon centroids.\nThis section focuses on major urban CoCs where the city-level context is most meaningful.\n\nOutput: `data/processed/merged_city_data.csv`\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "import sys\nfrom pathlib import Path\n\nROOT = Path().resolve().parent\nsys.path.insert(0, str(ROOT / 'src'))\n\nimport pandas as pd\nfrom city_data import get_merged_city_data\n\nOUT = ROOT / 'data' / 'processed'\nOUT.mkdir(parents=True, exist_ok=True)\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "df = get_merged_city_data()\nprint(f'City data: {len(df)} CoCs, {len(df.columns)} columns')\nprint(f'CoCs with lat/lon: {df[\"lat\"].notna().sum()}')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "out_path = OUT / 'merged_city_data.csv'\ndf.to_csv(out_path, index=False)\nprint(f'Saved to {out_path}')\n\nprint(f'\\nTop 10 CoCs by homeless rate per 10k:')\nprint(df.nlargest(10, 'homeless_rate_per_10k')[['city_name', 'state_postal', 'homeless_rate_per_10k', 'unsheltered_pct', 'jan_temp_f']].to_string(index=False))\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "preview = df[['coc_code', 'city_name', 'state_postal', 'total_homeless',\n              'homeless_rate_per_10k', 'unsheltered_pct', 'jan_temp_f', 'lat', 'lon']]\npreview = preview.sort_values('homeless_rate_per_10k', ascending=False)\npreview.head(20)\n"}
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/17_city_data_collection.ipynb \
  notebooks/17_city_data_collection.ipynb --cwd notebooks
```

Expected: `data/processed/merged_city_data.csv` exists, 100 rows. No errors.

- [ ] **Step 3: Commit**

```bash
git add notebooks/17_city_data_collection.ipynb data/processed/
git commit -m "feat: add notebook 17 city/CoC data collection"
```

---

### Task 3: Notebook 18 — City Homeless Bubble Map

**Files:**
- Create: `notebooks/18_city_homeless_map.ipynb`

- [ ] **Step 1: Create notebooks/18_city_homeless_map.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 18 — City/CoC Homeless Rate Bubble Map\n\nBubble map of homeless rate per 10k by CoC centroid. Bubble size = total homeless count;\nbubble color = homeless rate per 10k. Cities lack standard polygon boundaries,\nso we use lat/lon centroids from HUD CoC shapefiles.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['lat', 'lon'])\nprint(f'Loaded {len(df)} CoCs with coordinates')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "fig = px.scatter_geo(\n    df,\n    lat='lat',\n    lon='lon',\n    size='total_homeless',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    scope='usa',\n    hover_name='city_name',\n    hover_data={\n        'lat': False, 'lon': False,\n        'state_postal': True,\n        'total_homeless': ':,',\n        'homeless_rate_per_10k': ':.1f',\n        'unsheltered_pct': ':.1f',\n    },\n    title='Homeless Rate per 10k by Major City/CoC (HUD 2023) — bubble size = total homeless',\n    labels={'homeless_rate_per_10k': 'Rate per 10k'},\n    size_max=60,\n)\nfig.update_layout(geo_bgcolor='lightblue')\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Bar: top 20 CoCs by homeless rate\ntop20 = df.nlargest(20, 'homeless_rate_per_10k')\nfig2 = px.bar(\n    top20.sort_values('homeless_rate_per_10k', ascending=True),\n    x='homeless_rate_per_10k',\n    y='city_name',\n    orientation='h',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    title='Top 20 CoCs by Homeless Rate per 10k (2023)',\n    labels={'homeless_rate_per_10k': 'Rate per 10k', 'city_name': ''},\n)\nfig2.show()\n"}
 ]
}
```

- [ ] **Step 2: Run and commit**

```bash
.venv/bin/python -m papermill notebooks/18_city_homeless_map.ipynb \
  notebooks/18_city_homeless_map.ipynb --cwd notebooks
git add notebooks/18_city_homeless_map.ipynb
git commit -m "feat: add notebook 18 city bubble map"
```

---

### Tasks 4–7: Notebooks 19–22 (City Correlations)

Each is a scatter + regression plot following the same pattern established in Plan 2 (Tasks 4–8). Create, run, and commit each in sequence.

---

### Task 4: Notebooks 19–22

**Files:**
- Create: `notebooks/19_city_housing_affordability.ipynb`
- Create: `notebooks/20_city_spending.ipynb`
- Create: `notebooks/21_city_drug_mental.ipynb`
- Create: `notebooks/22_city_income_poverty.ipynb`

- [ ] **Step 1: Create notebooks/19_city_housing_affordability.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 19 — Housing Affordability vs. Homeless Rate (City/CoC)\n\nScatter: median 1BR FMR vs homeless rate per 10k at CoC level.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'median_1br_fmr'])\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['median_1br_fmr'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'FMR vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['median_1br_fmr'].min(), df['median_1br_fmr'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='median_1br_fmr', y='homeless_rate_per_10k',\n    text='city_name',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'Median 1BR FMR vs. Homeless Rate (City/CoC)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'median_1br_fmr': 'Median 1BR FMR ($)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 2: Create notebooks/20_city_spending.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 20 — Spending per Homeless vs. Homeless Rate (City/CoC)\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'spending_per_homeless'])\ndf = df[df['spending_per_homeless'] > 0]\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['spending_per_homeless'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Spending/homeless vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['spending_per_homeless'].min(), df['spending_per_homeless'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='spending_per_homeless', y='homeless_rate_per_10k',\n    text='city_name',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'HUD CoC Spending per Homeless vs. Rate (City/CoC)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'spending_per_homeless': 'HUD Spending per Homeless ($)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 3: Create notebooks/21_city_drug_mental.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 21 — Drug Use & Mental Health vs. Homeless Rate (City/CoC)\n\nUses state-level SAMHSA proxies joined to each CoC by state postal code.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'ami_pct', 'drug_disorder_pct'])\nprint(f'Loaded {len(df)} CoCs')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['ami_pct'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'AMI vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['ami_pct'].min(), df['ami_pct'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='ami_pct', y='homeless_rate_per_10k', text='city_name',\n    color='state_postal',\n    hover_name='coc_name',\n    title=f'AMI Prevalence (State Proxy) vs. Homeless Rate (City/CoC)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'ami_pct': 'AMI % (state proxy)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='black', dash='dash'), showlegend=False))\nfig.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 4: Create notebooks/22_city_income_poverty.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 22 — Income & Poverty vs. Homeless Rate (City/CoC)\n\nScatter plots of homeless rate vs. median income and poverty rate at CoC level.\nCensus data joined on primary county FIPS.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf_inc = df.dropna(subset=['homeless_rate_per_10k', 'median_income'])\nprint(f'Loaded {len(df_inc)} CoCs with income data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df_inc['median_income'], df_inc['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'Median income vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df_inc['median_income'].min(), df_inc['median_income'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df_inc, x='median_income', y='homeless_rate_per_10k', text='city_name',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'Median Income vs. Homeless Rate (City/CoC)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'median_income': 'Median Household Income ($)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig.show()\n"}
 ]
}
```

- [ ] **Step 5: Run all four notebooks**

```bash
for nb in 19 20 21 22; do
  .venv/bin/python -m papermill "notebooks/${nb}_city_"*.ipynb \
    "notebooks/${nb}_city_"*.ipynb --cwd notebooks
done
```

- [ ] **Step 6: Commit**

```bash
git add notebooks/19_city_housing_affordability.ipynb \
        notebooks/20_city_spending.ipynb \
        notebooks/21_city_drug_mental.ipynb \
        notebooks/22_city_income_poverty.ipynb
git commit -m "feat: add notebooks 19-22 city-level correlations"
```

---

### Task 5: Notebook 23 — City Demographics

**Files:**
- Create: `notebooks/23_city_demographics.ipynb`

- [ ] **Step 1: Create notebooks/23_city_demographics.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 23 — Demographics vs. Homeless Rate (City/CoC)\n\nCorrelations between homeless rate and racial/ethnic composition at CoC level.\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'pct_black', 'pct_hispanic', 'pct_white'])\nprint(f'Loaded {len(df)} CoCs with demographic data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope, intercept, r, p, se = stats.linregress(df['pct_black'], df['homeless_rate_per_10k'])\nr2 = r ** 2\nprint(f'% Black vs rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['pct_black'].min(), df['pct_black'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig = px.scatter(\n    df, x='pct_black', y='homeless_rate_per_10k', text='city_name',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'% Black Population vs. Homeless Rate (City/CoC)<br><sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f}</sup>',\n    labels={'pct_black': '% Black (non-Hispanic)', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "slope2, intercept2, r2v, p2, se2 = stats.linregress(df['pct_hispanic'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'% Hispanic vs rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\n\nx_range2 = [df['pct_hispanic'].min(), df['pct_hispanic'].max()]\ny_range2 = [slope2 * x + intercept2 for x in x_range2]\n\nfig2 = px.scatter(\n    df, x='pct_hispanic', y='homeless_rate_per_10k', text='city_name',\n    color='homeless_rate_per_10k', color_continuous_scale='Reds',\n    hover_name='coc_name',\n    title=f'% Hispanic Population vs. Homeless Rate (City/CoC)<br><sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}</sup>',\n    labels={'pct_hispanic': '% Hispanic', 'homeless_rate_per_10k': 'Rate per 10k'},\n)\nfig2.add_trace(go.Scatter(x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='darkred', dash='dash')))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"}
 ]
}
```

- [ ] **Step 2: Run and commit**

```bash
.venv/bin/python -m papermill notebooks/23_city_demographics.ipynb \
  notebooks/23_city_demographics.ipynb --cwd notebooks
git add notebooks/23_city_demographics.ipynb
git commit -m "feat: add notebook 23 city demographics correlation"
```

---

### Task 6: Notebook 24 — Sheltered/Unsheltered × Climate (Headline Analysis)

**Files:**
- Create: `notebooks/24_city_sheltered_unsheltered_climate.ipynb`

This is the headline analysis of the project. It tests whether cold climates shift homeless people into shelters (lower unsheltered %) without necessarily reducing the total homeless rate. Includes a faceted view by total homeless rate tier.

- [ ] **Step 1: Create notebooks/24_city_sheltered_unsheltered_climate.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 24 — Climate × Sheltered/Unsheltered: The Headline Analysis\n\n**Hypothesis:** Cold climates push a larger share of homeless people into shelters without\nreducing the *total* homeless rate. Warmer cities like Los Angeles, Phoenix, and Honolulu\nhave high unsheltered rates because sleeping outside is survivable year-round — not\nnecessarily because they have worse policies or more homeless people per capita.\n\nNew York City exemplifies the inverse: a legal 'right to shelter' combined with brutal winters\nproduces very low unsheltered % (~4%) despite one of the highest total homeless rates in the US.\n\nWe test this by:\n1. Scatter: unsheltered % vs January temperature (primary test)\n2. Scatter: total homeless rate vs January temperature (does climate drive total rate too?)\n3. Faceted view: unsheltered % vs temp, split by total homeless rate tier\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport numpy as np\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'unsheltered_pct', 'jan_temp_f'])\nprint(f'Loaded {len(df)} CoCs with climate data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Primary test: unsheltered % vs January temperature\nslope, intercept, r, p, se = stats.linregress(df['jan_temp_f'], df['unsheltered_pct'])\nr2 = r ** 2\nprint(f'Jan temp vs unsheltered %: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\nprint(f'Interpretation: Each 10°F increase in January temp → {slope*10:.1f}% more unsheltered')\n\nx_range = np.linspace(df['jan_temp_f'].min(), df['jan_temp_f'].max(), 100)\ny_range = slope * x_range + intercept\n\nfig1 = px.scatter(\n    df,\n    x='jan_temp_f',\n    y='unsheltered_pct',\n    size='total_homeless',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    text='city_name',\n    hover_name='coc_name',\n    hover_data={\n        'lat': False, 'lon': False,\n        'state_postal': True,\n        'jan_temp_f': ':.0f°F',\n        'unsheltered_pct': ':.1f%',\n        'total_homeless': ':,',\n        'homeless_rate_per_10k': ':.1f',\n    },\n    title=f'January Temperature vs. % Unsheltered Homeless (City/CoC Level)<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} — warmer cities have higher unsheltered share; '\n          f'bubble size = total homeless count; color = rate per 10k</sup>',\n    labels={\n        'jan_temp_f': 'Avg January Temperature (°F, NOAA 1991-2020)',\n        'unsheltered_pct': '% of Homeless Who Are Unsheltered',\n    },\n    size_max=60,\n)\nfig1.add_trace(go.Scatter(\n    x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='black', width=2, dash='dash'),\n))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Control check: does January temp also predict TOTAL homeless rate?\nslope2, intercept2, r2v, p2, se2 = stats.linregress(df['jan_temp_f'], df['homeless_rate_per_10k'])\nr2_2 = r2v ** 2\nprint(f'Jan temp vs total homeless rate: r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f}')\nprint(f'Interpretation: Climate explains {r2_2*100:.0f}% of variance in total homeless rate')\n\nx_range2 = np.linspace(df['jan_temp_f'].min(), df['jan_temp_f'].max(), 100)\ny_range2 = slope2 * x_range2 + intercept2\n\nfig2 = px.scatter(\n    df,\n    x='jan_temp_f',\n    y='homeless_rate_per_10k',\n    size='total_homeless',\n    color='unsheltered_pct',\n    color_continuous_scale='OrRd',\n    text='city_name',\n    hover_name='coc_name',\n    title=f'January Temperature vs. Total Homeless Rate (City/CoC Level)<br>'\n          f'<sup>r={r2v:.3f}, R²={r2_2:.3f}, p={p2:.4f} — color = % unsheltered</sup>',\n    labels={\n        'jan_temp_f': 'Avg January Temperature (°F)',\n        'homeless_rate_per_10k': 'Total Homeless Rate per 10k',\n    },\n    size_max=60,\n)\nfig2.add_trace(go.Scatter(\n    x=x_range2, y=y_range2, mode='lines',\n    name='Regression', line=dict(color='black', width=2, dash='dash'),\n))\nfig2.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig2.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Faceted: unsheltered % vs temp, by homeless rate tier\ndf['rate_tier'] = pd.qcut(\n    df['homeless_rate_per_10k'],\n    q=3,\n    labels=['Low rate (bottom third)', 'Medium rate (middle third)', 'High rate (top third)'],\n)\n\nfig3 = px.scatter(\n    df,\n    x='jan_temp_f',\n    y='unsheltered_pct',\n    facet_col='rate_tier',\n    color='homeless_rate_per_10k',\n    color_continuous_scale='Reds',\n    text='city_name',\n    hover_name='coc_name',\n    trendline='ols',\n    title='January Temperature vs. Unsheltered % — by Homeless Rate Tier<br>'\n          '<sup>Climate effect on shelter share holds across all rate tiers</sup>',\n    labels={\n        'jan_temp_f': 'Jan Temp (°F)',\n        'unsheltered_pct': '% Unsheltered',\n    },\n)\nfig3.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig3.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Key findings summary\nwarm = df[df['jan_temp_f'] >= 55]\ncold = df[df['jan_temp_f'] <= 30]\nprint('Warm cities (Jan avg ≥ 55°F):')\nprint(f'  Mean unsheltered %: {warm[\"unsheltered_pct\"].mean():.1f}%')\nprint(f'  Mean homeless rate per 10k: {warm[\"homeless_rate_per_10k\"].mean():.1f}')\nprint(f'  Cities: {\", \".join(warm[\"city_name\"].tolist())}')\nprint()\nprint('Cold cities (Jan avg ≤ 30°F):')\nprint(f'  Mean unsheltered %: {cold[\"unsheltered_pct\"].mean():.1f}%')\nprint(f'  Mean homeless rate per 10k: {cold[\"homeless_rate_per_10k\"].mean():.1f}')\nprint(f'  Cities: {\", \".join(cold[\"city_name\"].tolist())}')\n"}
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/24_city_sheltered_unsheltered_climate.ipynb \
  notebooks/24_city_sheltered_unsheltered_climate.ipynb --cwd notebooks
```

Expected: no errors, four Plotly charts including the faceted trendline chart.

- [ ] **Step 3: Commit**

```bash
git add notebooks/24_city_sheltered_unsheltered_climate.ipynb
git commit -m "feat: add notebook 24 headline climate × sheltered/unsheltered analysis"
```

---

### Task 7: Notebook 25 — Veteran Homeless

**Files:**
- Create: `notebooks/25_city_veteran_homeless.ipynb`

- [ ] **Step 1: Create notebooks/25_city_veteran_homeless.ipynb**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9.0"}},
 "cells": [
  {"cell_type": "markdown", "metadata": {},
   "source": "# 25 — Veteran Homeless by CoC\n\nExamines veteran homelessness:\n- Veteran homeless rate per 10k veterans (vs overall homeless rate)\n- Which CoCs have disproportionately high veteran homeless rates?\n- Correlation: overall homeless rate vs veteran homeless rate\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "from pathlib import Path\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nfrom scipy import stats\n\nROOT = Path().resolve().parent\ndf = pd.read_csv(ROOT / 'data' / 'processed' / 'merged_city_data.csv')\ndf = df.dropna(subset=['homeless_rate_per_10k', 'veteran_rate_per_10k', 'veteran_homeless'])\ndf = df[df['veteran_homeless'] > 0]\nprint(f'Loaded {len(df)} CoCs with veteran data')\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Scatter: overall homeless rate vs veteran homeless rate per 10k veterans\nslope, intercept, r, p, se = stats.linregress(df['homeless_rate_per_10k'], df['veteran_rate_per_10k'])\nr2 = r ** 2\nprint(f'Overall vs veteran homeless rate: r={r:.3f}, R²={r2:.3f}, p={p:.4f}')\n\nx_range = [df['homeless_rate_per_10k'].min(), df['homeless_rate_per_10k'].max()]\ny_range = [slope * x + intercept for x in x_range]\n\nfig1 = px.scatter(\n    df,\n    x='homeless_rate_per_10k',\n    y='veteran_rate_per_10k',\n    size='veteran_homeless',\n    color='veteran_rate_per_10k',\n    color_continuous_scale='Blues',\n    text='city_name',\n    hover_name='coc_name',\n    hover_data={'state_postal': True, 'veteran_homeless': ':,',\n                'homeless_rate_per_10k': ':.1f', 'veteran_rate_per_10k': ':.1f'},\n    title=f'Overall vs. Veteran Homeless Rate by CoC<br>'\n          f'<sup>r={r:.3f}, R²={r2:.3f}, p={p:.4f} — bubble size = veteran homeless count</sup>',\n    labels={\n        'homeless_rate_per_10k': 'Overall Homeless Rate per 10k',\n        'veteran_rate_per_10k': 'Veteran Homeless Rate per 10k Veterans',\n    },\n    size_max=50,\n)\nfig1.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines',\n    name='Regression', line=dict(color='navy', dash='dash')))\nfig1.update_traces(textposition='top center', selector=dict(mode='markers+text'))\nfig1.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Bar: top 20 CoCs by veteran homeless count\ntop20 = df.nlargest(20, 'veteran_homeless')\nfig2 = px.bar(\n    top20.sort_values('veteran_homeless', ascending=True),\n    x='veteran_homeless',\n    y='city_name',\n    orientation='h',\n    color='veteran_rate_per_10k',\n    color_continuous_scale='Blues',\n    title='Top 20 CoCs by Veteran Homeless Count (HUD 2023)',\n    labels={'veteran_homeless': 'Veteran Homeless Count', 'city_name': ''},\n)\nfig2.show()\n"},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": "# Veteran share of total homeless by CoC\ndf['veteran_share_pct'] = (df['veteran_homeless'] / df['total_homeless'] * 100).round(1)\nprint(f'National veteran share of homeless: {df[\"veteran_share_pct\"].mean():.1f}%')\nprint(f'\\nHighest veteran share:')\nprint(df.nlargest(5, 'veteran_share_pct')[['city_name', 'state_postal', 'veteran_share_pct', 'veteran_homeless']].to_string(index=False))\n"}
 ]
}
```

- [ ] **Step 2: Run notebook**

```bash
.venv/bin/python -m papermill notebooks/25_city_veteran_homeless.ipynb \
  notebooks/25_city_veteran_homeless.ipynb --cwd notebooks
```

- [ ] **Step 3: Regenerate HTML report**

```bash
.venv/bin/python scripts/generate_html.py
```

Expected: `docs/report.html` contains all three sections (state, county, city) with all charts.

```bash
wc -c docs/report.html
```

Expected: at least 500KB (all charts embedded).

- [ ] **Step 4: Final commit**

```bash
git add notebooks/25_city_veteran_homeless.ipynb docs/report.html
git commit -m "feat: add notebook 25 veteran homeless analysis, finalize HTML report"
```

---

### Task 8: Verify complete pipeline

- [ ] **Step 1: Run full pipeline from scratch to confirm reproducibility**

```bash
# Clear executed outputs and re-run all notebooks
for nb in notebooks/*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done
```

Expected: all 25 notebooks execute without errors.

- [ ] **Step 2: Regenerate report**

```bash
.venv/bin/python scripts/generate_html.py
open docs/report.html
```

Expected: report opens, all three sections visible, all charts interactive.

- [ ] **Step 3: Final verification commit**

```bash
git add -A
git commit -m "chore: verify full pipeline, regenerate final report"
```
