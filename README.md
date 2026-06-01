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
