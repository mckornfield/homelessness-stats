# Homelessness Stats — Design Spec
_Date: 2026-05-31_

## Overview

A Jupyter notebook + HTML report project analyzing US homelessness rates across three geographic slices (state, county/CoC, city/CoC), with correlations against housing affordability, federal spending, drug/mental health, income/poverty, demographics, climate, and veteran status. Follows the same conventions as `california-stats` and `gun-violence`.

## Architecture

```
homelessness-stats/
├── src/
│   ├── state_data.py       # state-level fetch + embedded fallbacks
│   ├── county_data.py      # county/CoC fetch + embedded fallbacks
│   └── city_data.py        # city/CoC fetch + embedded fallbacks
├── data/
│   ├── raw/                # downloaded CSVs + companion fetch_*.py scripts
│   └── processed/          # merged outputs from data collection notebooks
├── notebooks/              # numbered, sectioned (01-25)
├── scripts/
│   └── generate_html.py    # builds docs/report.html (self-contained, Plotly)
├── docs/
│   └── report.html
├── pyproject.toml          # uv, Python 3.9+, pandas/plotly/papermill/scipy
├── CLAUDE.md
├── README.md
└── TEMPLATE.md             # conventions doc for future stats repos
```

**Stack:** Python 3.9+, uv, Jupyter, Papermill, Plotly, pandas, scipy, nbconvert. No API keys required for any data source.

**Embedded fallback data:** Each `src/*.py` embeds a snapshot of the data so notebooks run offline. Every raw CSV in `data/raw/` has a companion `fetch_<dataset>.py` showing how it was originally downloaded (without keys).

**HTML report:** `scripts/generate_html.py` walks all executed notebooks in order, extracts Plotly figures and markdown, and writes a single self-contained `docs/report.html` with section headers per geographic level.

## Notebook Pipeline

Notebooks run in order within each section; later sections depend on processed CSVs from earlier data collection notebooks.

### State-level (01–07)

| # | Notebook | Output |
|---|----------|--------|
| 01 | `01_state_data_collection` | `data/processed/merged_state_data.csv` |
| 02 | `02_state_homeless_map` | Choropleth: homeless rate per 10k by state |
| 03 | `03_state_housing_affordability` | Scatter: homeless rate vs rent burden + FMR |
| 04 | `04_state_spending` | Scatter: homeless rate vs HUD CoC grant $ per homeless person |
| 05 | `05_state_drug_mental` | Scatter: homeless rate vs drug use rate + AMI prevalence |
| 06 | `06_state_income_poverty` | Scatter: homeless rate vs Gini, poverty rate, median income |
| 07 | `07_state_demographics` | Scatter: homeless rate vs race/ethnicity + veteran rate |

### County/CoC-level (08–16)

| # | Notebook | Output |
|---|----------|--------|
| 08 | `08_county_data_collection` | `data/processed/merged_county_data.csv` |
| 09 | `09_county_homeless_map` | Choropleth: homeless rate per 10k by county |
| 10 | `10_county_housing_affordability` | Scatter: homeless rate vs rent burden + FMR |
| 11 | `11_county_spending` | Scatter: homeless rate vs spending per homeless |
| 12 | `12_county_drug_mental` | Scatter: homeless rate vs CDC overdose death rate |
| 13 | `13_county_income_poverty` | Scatter: homeless rate vs Gini, poverty, income |
| 14 | `14_county_demographics` | Scatter: homeless rate vs race/ethnicity + veteran rate |
| 15 | `15_county_sheltered_vs_unsheltered` | Bar + map: sheltered vs unsheltered breakdown by CoC |
| 16 | `16_county_climate` | Scatter: unsheltered rate vs avg January temperature (NOAA) |

### City/CoC-level (17–25)

| # | Notebook | Output |
|---|----------|--------|
| 17 | `17_city_data_collection` | `data/processed/merged_city_data.csv` |
| 18 | `18_city_homeless_map` | Bubble map: homeless rate by major city/CoC (CoC centroid lat/lon; cities lack standard polygon boundaries) |
| 19 | `19_city_housing_affordability` | Scatter: homeless rate vs rent burden + FMR |
| 20 | `20_city_spending` | Scatter: homeless rate vs spending per homeless |
| 21 | `21_city_drug_mental` | Scatter: homeless rate vs drug/mental health proxies |
| 22 | `22_city_income_poverty` | Scatter: homeless rate vs Gini, poverty, income |
| 23 | `23_city_demographics` | Scatter: homeless rate vs race/ethnicity |
| 24 | `24_city_sheltered_unsheltered_climate` | Key analysis: does cold climate shift people into shelters without reducing total homeless rate? Scatter of unsheltered % vs January temp, faceted by total homeless rate tier. |
| 25 | `25_city_veteran_homeless` | Bar + scatter: veteran vs non-veteran homeless rate by CoC |

## Data Sources

| Dataset | Source | Geographic Level | Key Required |
|---------|--------|-----------------|--------------|
| PIT homeless counts (total, sheltered, unsheltered, veteran) | HUD AHAR / CoC downloads | CoC → county/state rollup | No |
| CoC federal grant spending | HUD CoC grant awards | CoC | No |
| Fair Market Rents | HUD FMR data | County | No |
| Rent burden, income, poverty, Gini, race/ethnicity | Census ACS 5-year | State + county | No (unauthenticated API) |
| Drug use prevalence, AMI prevalence | SAMHSA NSDUH | State (proxy for lower levels) | No |
| Overdose death rates | CDC WONDER (web query export, not API — companion script documents query params) | County | No |
| Average January temperature | NOAA 1991-2020 Climate Normals (station data geocoded to nearest CoC centroid) | Weather station → CoC | No |
| Veteran homeless counts | HUD AHAR veteran supplement | CoC | No |

**Join keys:** State (FIPS 2-digit or postal code), county (5-digit FIPS), CoC (HUD CoC code e.g. `CA-600`).

**CoC → county mapping caveat:** CoC boundaries don't align cleanly with county FIPS boundaries — a CoC can span multiple counties (e.g., a rural balance-of-state CoC) or be a subset of a county (e.g., a city-specific CoC like San Jose's). The county-level section uses HUD's published CoC-to-county crosswalk file where available and falls back to primary-county assignment by CoC centroid.

## Sheltered vs. Unsheltered Analysis

HUD PIT counts distinguish:
- **Sheltered:** emergency shelter, transitional housing, safe haven
- **Unsheltered:** on street, in vehicles, in encampments

The climate hypothesis (notebook 16 + 24): colder cities push a larger share of homeless people into shelters without necessarily reducing the total homeless rate. We test this by plotting `unsheltered %` vs. average January temperature, colored/sized by total homeless rate per capita. If the hypothesis holds, warm cities (LA, Phoenix, Miami) cluster toward high unsheltered %; cold cities (NYC, Chicago, Boston) cluster toward low unsheltered % at similar or higher total rates.

## Template Document (TEMPLATE.md)

Documents the conventions established in this repo for reuse in future stats projects:

1. **Sectioned notebook pipeline** — data collection notebook per geographic level, then correlate notebooks; later sections depend on CSVs from earlier ones
2. **Embedded fallback data** — each `src/*.py` has fallback data so notebooks run offline; raw CSVs in `data/raw/` have companion `fetch_<dataset>.py`
3. **HTML report generation** — `scripts/generate_html.py` extracts Plotly figures + markdown from executed notebooks into a single self-contained HTML file
4. **Stack** — Python 3.9+, uv, Jupyter, Papermill, Plotly, pandas, scipy, nbconvert
5. **CLAUDE.md structure** — overview, architecture, methodology, notebook pipeline table, data sources table, run instructions, environment
6. **No API keys** — all data sources must be free and unauthenticated (or have embedded fallbacks)

## Running the Project

```bash
# Environment setup
uv venv && uv pip install -e .

# Run a section (example: state-level)
for nb in notebooks/0{1..7}_*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done

# Generate HTML report
.venv/bin/python scripts/generate_html.py
```

## Success Criteria

- All 25 notebooks execute without errors via Papermill
- `docs/report.html` is a single self-contained file viewable in any browser
- Each correlation notebook shows a regression line + r-value + p-value (scipy)
- Sheltered vs. unsheltered climate analysis produces a visually clear finding
- `TEMPLATE.md` is complete enough to scaffold a new stats repo without referencing this one
