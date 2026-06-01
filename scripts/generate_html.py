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
