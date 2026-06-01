# Project: US Homelessness Statistics Analysis

## Overview
Analyzes US homelessness rates across three geographic slices — state, county/CoC, and city/CoC —
correlating against housing affordability, federal spending, drug/mental health, income/poverty,
demographics, climate, and veteran status. Produces interactive Plotly charts and a single
self-contained HTML report.

## Architecture
- `src/state_data.py`  — State-level data: HUD PIT counts, SAMHSA, Census ACS (embedded fallbacks)
- `src/county_data.py` — County/CoC data: HUD CoC crosswalk, Census, CDC overdose (embedded fallbacks)
- `src/city_data.py`   — City/CoC data: major CoC centroids, full correlate set (embedded fallbacks)
- `data/raw/`          — Downloaded CSVs; each has a companion `fetch_<dataset>.py` showing provenance
- `data/processed/`    — Merged outputs: `merged_state_data.csv`, `merged_county_data.csv`, `merged_city_data.csv`
- `notebooks/`         — 25 Jupyter notebooks in three sections (01–07 state, 08–16 county, 17–25 city)
- `scripts/generate_html.py` — Extracts Plotly outputs from executed notebooks → `docs/report.html`
- `docs/report.html`   — Final self-contained report (all interactive charts)

## Notebook Pipeline
Notebooks must run in order within each section (later notebooks read CSVs from data collection notebooks):

### State-level (01–07)
| # | Notebook | Output |
|---|----------|--------|
| 01 | `01_state_data_collection` | `data/processed/merged_state_data.csv` |
| 02 | `02_state_homeless_map` | Choropleth: homeless rate per 10k by state |
| 03 | `03_state_housing_affordability` | Scatter: rate vs rent burden + FMR |
| 04 | `04_state_spending` | Scatter: rate vs HUD CoC grant $ per homeless person |
| 05 | `05_state_drug_mental` | Scatter: rate vs drug use + AMI prevalence |
| 06 | `06_state_income_poverty` | Scatter: rate vs Gini, poverty, median income |
| 07 | `07_state_demographics` | Scatter: rate vs race/ethnicity + veteran rate |

### County/CoC-level (08–16)
| # | Notebook | Output |
|---|----------|--------|
| 08 | `08_county_data_collection` | `data/processed/merged_county_data.csv` |
| 09 | `09_county_homeless_map` | Choropleth: homeless rate per 10k by county |
| 10 | `10_county_housing_affordability` | Scatter: rate vs rent burden + FMR |
| 11 | `11_county_spending` | Scatter: rate vs spending per homeless |
| 12 | `12_county_drug_mental` | Scatter: rate vs CDC overdose death rate |
| 13 | `13_county_income_poverty` | Scatter: rate vs Gini, poverty, income |
| 14 | `14_county_demographics` | Scatter: rate vs race/ethnicity + veteran rate |
| 15 | `15_county_sheltered_vs_unsheltered` | Bar + map: sheltered vs unsheltered by CoC |
| 16 | `16_county_climate` | Scatter: unsheltered rate vs avg January temperature |

### City/CoC-level (17–25)
| # | Notebook | Output |
|---|----------|--------|
| 17 | `17_city_data_collection` | `data/processed/merged_city_data.csv` |
| 18 | `18_city_homeless_map` | Bubble map: rate by major city/CoC centroid |
| 19 | `19_city_housing_affordability` | Scatter: rate vs rent burden + FMR |
| 20 | `20_city_spending` | Scatter: rate vs spending per homeless |
| 21 | `21_city_drug_mental` | Scatter: rate vs drug/mental health proxies |
| 22 | `22_city_income_poverty` | Scatter: rate vs Gini, poverty, income |
| 23 | `23_city_demographics` | Scatter: rate vs race/ethnicity |
| 24 | `24_city_sheltered_unsheltered_climate` | Key analysis: unsheltered % vs January temp |
| 25 | `25_city_veteran_homeless` | Bar + scatter: veteran vs non-veteran homeless rate |

## Running Notebooks
```bash
# Set up environment
uv venv && uv pip install -e .

# Run state section
for nb in notebooks/0{1..7}_*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done

# Run county section
for nb in notebooks/{08,09,10,11,12,13,14,15,16}_*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done

# Run city section
for nb in notebooks/{17,18,19,20,21,22,23,24,25}_*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done
```

## Generating the HTML Report
After running all notebooks:
```bash
.venv/bin/python scripts/generate_html.py
```
Output: `docs/report.html` — single self-contained file with all interactive Plotly charts.

## Data Sources
| Dataset | Source | Level | Key |
|---------|--------|-------|-----|
| PIT homeless counts (total, sheltered, unsheltered, veteran) | HUD AHAR | CoC/state | None |
| CoC federal grant spending | HUD CoC grant awards | CoC | None |
| Fair Market Rents | HUD FMR | County | None |
| Rent burden, income, poverty, Gini, demographics | Census ACS 5-year | State+county | None |
| Drug use, AMI prevalence | SAMHSA NSDUH | State proxy | None |
| Overdose death rates | CDC WONDER | County | None |
| Average January temperature | NOAA 1991-2020 climate normals | Station→CoC | None |

## Environment
- Python 3.9+ virtualenv at `.venv/`
- No API keys required for any data source
- Key dependencies: pandas, numpy, plotly, scipy, papermill, nbconvert
