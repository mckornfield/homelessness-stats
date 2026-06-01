# Homelessness Stats — Plan 1: Repo Scaffold

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the full repo skeleton — dependencies, directory layout, HTML generator, and all documentation files — so Plans 2–4 can be executed without further setup.

**Architecture:** Python 3.9+ project managed with uv. Notebooks (written in Plans 2–4) are executed via Papermill and their Plotly outputs are extracted by `scripts/generate_html.py` into a single self-contained `docs/report.html`. Three geographic sections (state, county, city) map to notebook ranges 01–07, 08–16, 17–25.

**Tech Stack:** Python 3.9+, uv, pandas, plotly, scipy, papermill, nbconvert, requests

---

### Task 1: Project structure + pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `data/raw/.gitkeep`
- Create: `data/processed/.gitkeep`
- Create: `notebooks/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src data/raw data/processed notebooks scripts docs
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "homelessness-stats"
version = "0.1.0"
description = "US homelessness rate analysis by state, county, and city"
requires-python = ">=3.9"
dependencies = [
    "jupyter>=1.1.1",
    "matplotlib>=3.9.0",
    "numpy>=2.0.0",
    "pandas>=2.0.0",
    "plotly>=5.24.0",
    "python-dotenv>=1.0.0",
    "requests>=2.32.0",
    "papermill>=2.6.0",
    "nbconvert>=7.0.0",
    "scipy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

- [ ] **Step 3: Create src/__init__.py (empty)**

Write an empty file to `src/__init__.py`.

- [ ] **Step 4: Create .gitkeep files**

Write empty files to `data/raw/.gitkeep`, `data/processed/.gitkeep`, `notebooks/.gitkeep`.

- [ ] **Step 5: Set up virtual environment**

```bash
uv venv && uv pip install -e .
```

Expected: `.venv/` created, packages installed without errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/__init__.py data/ notebooks/
git commit -m "feat: scaffold project structure and dependencies"
```

---

### Task 2: scripts/generate_html.py

**Files:**
- Create: `scripts/generate_html.py`

This script walks all executed notebooks in order, extracts Plotly figures and markdown, and writes `docs/report.html` — a single self-contained file that works in any browser. Section headers separate state, county, and city analyses.

- [ ] **Step 1: Write scripts/generate_html.py**

```python
"""Generate a combined HTML report from all executed notebooks."""

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SECTIONS = [
    ("State-Level Analysis", [
        "01_state_data_collection.ipynb",
        "02_state_homeless_map.ipynb",
        "03_state_housing_affordability.ipynb",
        "04_state_spending.ipynb",
        "05_state_drug_mental.ipynb",
        "06_state_income_poverty.ipynb",
        "07_state_demographics.ipynb",
    ]),
    ("County / CoC-Level Analysis", [
        "08_county_data_collection.ipynb",
        "09_county_homeless_map.ipynb",
        "10_county_housing_affordability.ipynb",
        "11_county_spending.ipynb",
        "12_county_drug_mental.ipynb",
        "13_county_income_poverty.ipynb",
        "14_county_demographics.ipynb",
        "15_county_sheltered_vs_unsheltered.ipynb",
        "16_county_climate.ipynb",
    ]),
    ("City / CoC-Level Analysis", [
        "17_city_data_collection.ipynb",
        "18_city_homeless_map.ipynb",
        "19_city_housing_affordability.ipynb",
        "20_city_spending.ipynb",
        "21_city_drug_mental.ipynb",
        "22_city_income_poverty.ipynb",
        "23_city_demographics.ipynb",
        "24_city_sheltered_unsheltered_climate.ipynb",
        "25_city_veteran_homeless.ipynb",
    ]),
]


def extract_outputs(nb_path: Path) -> str:
    nb = json.loads(nb_path.read_text())
    parts = []
    for cell in nb.get("cells", []):
        if cell["cell_type"] == "markdown":
            source = "".join(cell.get("source", []))
            html_lines = []
            for line in source.split("\n"):
                if line.startswith("### "):
                    html_lines.append(f"<h4>{line[4:]}</h4>")
                elif line.startswith("## "):
                    html_lines.append(f"<h3>{line[3:]}</h3>")
                elif line.startswith("# "):
                    html_lines.append(f"<h3>{line[2:]}</h3>")
                elif line.startswith("**") and line.endswith("**"):
                    html_lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
                elif line.startswith("- "):
                    html_lines.append(f"<li>{line[2:]}</li>")
                elif line.strip():
                    html_lines.append(f"<p>{line}</p>")
            parts.append("\n".join(html_lines))
            continue

        if cell["cell_type"] != "code":
            continue

        for output in cell.get("outputs", []):
            otype = output.get("output_type", "")
            if otype in ("display_data", "execute_result"):
                data = output.get("data", {})
                if "application/vnd.plotly.v1+json" in data:
                    plotly_data = data["application/vnd.plotly.v1+json"]
                    div_id = f"plotly-{uuid.uuid4().hex[:12]}"
                    fig_json = json.dumps(plotly_data.get("data", []))
                    layout = plotly_data.get("layout", {})
                    layout.setdefault("autosize", True)
                    layout_json = json.dumps(layout)
                    parts.append(
                        f'<div id="{div_id}" style="width:100%;height:500px;"></div>\n'
                        f"<script>Plotly.newPlot('{div_id}', {fig_json}, {layout_json}, "
                        f"{{responsive: true}});</script>"
                    )
                elif "text/html" in data:
                    parts.append("".join(data["text/html"]))
                elif "text/plain" in data:
                    text = "".join(data["text/plain"])
                    parts.append(f"<pre>{text}</pre>")
            elif otype == "stream":
                text = "".join(output.get("text", []))
                if text.strip():
                    parts.append(f"<pre>{text}</pre>")
    return "\n".join(parts)


def build_html(sections: list) -> str:
    nav_items = "".join(
        f'<li><a href="#section-{i}">{title}</a></li>'
        for i, (title, _) in enumerate(sections)
    )
    content_blocks = []
    for i, (title, notebooks) in enumerate(sections):
        block = f'<section id="section-{i}"><h2>{title}</h2>'
        for nb_name in notebooks:
            nb_path = NOTEBOOKS_DIR / nb_name
            if not nb_path.exists():
                block += f"<p><em>{nb_name} not yet executed.</em></p>"
                continue
            block += extract_outputs(nb_path)
        block += "</section>"
        content_blocks.append(block)

    content = "\n".join(content_blocks)
    plotly_cdn = "https://cdn.plot.ly/plotly-latest.min.js"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US Homelessness Statistics</title>
<script src="{plotly_cdn}"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 1200px; margin: 0 auto; padding: 20px; color: #333; }}
  h2 {{ border-bottom: 2px solid #4a90d9; padding-bottom: 8px; margin-top: 40px; }}
  h3 {{ color: #2c5f8a; margin-top: 30px; }}
  nav ul {{ list-style: none; padding: 0; display: flex; gap: 16px; flex-wrap: wrap; }}
  nav a {{ color: #4a90d9; text-decoration: none; }}
  nav a:hover {{ text-decoration: underline; }}
  pre {{ background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }}
  li {{ margin: 4px 0; }}
</style>
</head>
<body>
<h1>US Homelessness Statistics</h1>
<nav><ul>{nav_items}</ul></nav>
{content}
</body>
</html>"""


def main():
    html = build_html(SECTIONS)
    out = DOCS_DIR / "report.html"
    out.write_text(html)
    print(f"Report written to {out}")
    print(f"Size: {len(html):,} bytes")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script runs (notebooks not yet executed — partial output is fine)**

```bash
.venv/bin/python scripts/generate_html.py
```

Expected: `Report written to .../docs/report.html` — file exists even if notebooks are missing.

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_html.py docs/
git commit -m "feat: add HTML report generator with three-section layout"
```

---

### Task 3: CLAUDE.md + README.md + TEMPLATE.md

**Files:**
- Create/replace: `CLAUDE.md`
- Create/replace: `README.md`
- Create: `TEMPLATE.md`

- [ ] **Step 1: Write CLAUDE.md**

```markdown
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

# Run a section (example: state-level, notebooks 01-07)
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
```

- [ ] **Step 2: Write README.md**

```markdown
# US Homelessness Statistics

Analysis of US homelessness rates across states, counties, and cities — correlating against
housing affordability, federal spending, drug use, mental health, income, climate, and veteran status.

## Quick Start

```bash
uv venv && uv pip install -e .

# Run all notebooks
for nb in notebooks/*.ipynb; do
  .venv/bin/python -m papermill "$nb" "$nb" --cwd notebooks
done

# Generate HTML report
.venv/bin/python scripts/generate_html.py
open docs/report.html
```

## Data

All data sources are free and publicly available. Raw CSVs in `data/raw/` each have a companion
`fetch_<dataset>.py` script showing how the data was originally obtained.

See [CLAUDE.md](CLAUDE.md) for full methodology and data source details.
```

- [ ] **Step 3: Write TEMPLATE.md**

```markdown
# Stats Repo Template

Conventions established across `california-stats`, `gun-violence`, and `homelessness-stats`.
Copy this into a new repo's CLAUDE.md to orient future sessions.

## Directory Layout

```
<project>/
├── src/
│   └── <topic>_data.py      # Data fetch functions + embedded fallback data
├── data/
│   ├── raw/                 # Raw CSVs + companion fetch_<dataset>.py per file
│   └── processed/           # Merged outputs from data collection notebooks
├── notebooks/               # Numbered Jupyter notebooks
├── scripts/
│   └── generate_html.py     # Extracts Plotly outputs → docs/report.html
├── docs/
│   └── report.html          # Final self-contained report
├── pyproject.toml           # uv project (Python 3.9+)
├── CLAUDE.md                # Full methodology + run instructions
└── README.md
```

## Notebook Conventions

- **Numbered sequentially.** First notebook in each section is data collection; rest are analysis.
- **Sectioned by geographic/thematic slice.** E.g., state-level (01–07), county-level (08–16).
- **Each section is independently runnable** after its data collection notebook executes.
- **Later sections may depend on earlier sections' CSVs** — document this in CLAUDE.md.

## Data Collection Notebooks

- Read from APIs or download URLs; fall back to embedded data if unavailable.
- Write merged output to `data/processed/merged_<scope>_data.csv`.
- Save any raw downloads to `data/raw/`.

## Analysis Notebooks

Each notebook follows this cell structure:
1. Markdown header: title + what this analysis tests
2. Imports + load processed CSV (`ROOT = Path().resolve().parent`)
3. One or more Plotly figures with `fig.show()`
4. Correlation notebooks: `scipy.stats.linregress` → r, R², p-value in chart title

## Embedded Fallback Data

Each `src/<topic>_data.py` contains a dict or list of embedded data so notebooks
run offline. Format:
```python
EMBEDDED_DATA = [
    {"key": "value", ...},
    ...
]

def get_data():
    try:
        return _fetch_live()
    except Exception:
        return pd.DataFrame(EMBEDDED_DATA)
```

## Companion Fetch Scripts

Every CSV in `data/raw/` has a sibling `fetch_<dataset>.py` that documents:
- The URL or API endpoint
- Any query parameters
- How to save the result

No API keys allowed. If a source requires a key, use only its embedded fallback.

## generate_html.py Pattern

- Lists notebooks in section order
- Extracts `application/vnd.plotly.v1+json` outputs → inline Plotly JS
- Extracts markdown cells → basic HTML
- Writes single self-contained `docs/report.html` with Plotly CDN

## pyproject.toml Template

```toml
[project]
name = "<project-name>"
version = "0.1.0"
description = "<description>"
requires-python = ">=3.9"
dependencies = [
    "jupyter>=1.1.1",
    "matplotlib>=3.9.0",
    "numpy>=2.0.0",
    "pandas>=2.0.0",
    "plotly>=5.24.0",
    "python-dotenv>=1.0.0",
    "requests>=2.32.0",
    "papermill>=2.6.0",
    "nbconvert>=7.0.0",
    "scipy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

## CLAUDE.md Sections (required)

1. **Overview** — what the project analyzes and produces
2. **Architecture** — file-by-file responsibilities
3. **Notebook Pipeline** — table per section: number, name, output
4. **Data Sources** — table: dataset, source, geographic level, key required
5. **Running Notebooks** — exact bash commands with papermill
6. **Generating the HTML Report** — exact command
7. **Environment** — Python version, virtualenv location, no-key policy
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md TEMPLATE.md
git commit -m "feat: add CLAUDE.md, README.md, and TEMPLATE.md"
```
