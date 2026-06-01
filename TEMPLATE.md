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
