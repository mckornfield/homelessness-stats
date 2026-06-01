"""Generate a combined HTML report from all executed notebooks."""

import base64
import json
import re
import struct
import uuid
from pathlib import Path

_CORR_RE = re.compile(
    r"^(?P<label>.+?):\s*r=(?P<r>-?\d+\.\d+),\s*R[²2]=(?P<r2>\d+\.\d+),\s*p=(?P<p>\d+\.\d+)",
    re.MULTILINE,
)
# Same pattern but embedded in Plotly chart title HTML (no line-start anchor)
_TITLE_CORR_RE = re.compile(
    r"r=(?P<r>-?\d+\.\d+),\s*R[²2]=(?P<r2>\d+\.\d+),\s*p=(?P<p>\d+\.\d+)"
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Plotly 6.x serializes numeric arrays as base64-encoded binary (bdata/dtype).
# Plotly.js in the browser cannot decode this format, so we convert back to
# plain lists here before writing the HTML.
_DTYPE_FMT = {
    "f8": ("d", 8),
    "f4": ("f", 4),
    "i4": ("i", 4),
    "i2": ("h", 2),
    "i1": ("b", 1),
    "u4": ("I", 4),
    "u2": ("H", 2),
    "u1": ("B", 1),
    "i8": ("q", 8),
    "u8": ("Q", 8),
}


def _decode_bdata(obj):
    """Recursively decode Plotly 6.x bdata binary arrays to plain lists."""
    if isinstance(obj, dict):
        if "bdata" in obj and "dtype" in obj:
            dtype = obj["dtype"]
            raw = base64.b64decode(obj["bdata"])
            if dtype in _DTYPE_FMT:
                fmt_char, size = _DTYPE_FMT[dtype]
                n = len(raw) // size
                return list(struct.unpack(f"<{n}{fmt_char}", raw))
            return obj
        return {k: _decode_bdata(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_bdata(item) for item in obj]
    return obj

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
            in_list = False
            for line in source.split("\n"):
                if line.startswith("- "):
                    if not in_list:
                        html_lines.append("<ul>")
                        in_list = True
                    html_lines.append(f"<li>{line[2:]}</li>")
                else:
                    if in_list:
                        html_lines.append("</ul>")
                        in_list = False
                    if line.startswith("### "):
                        html_lines.append(f"<h4>{line[4:]}</h4>")
                    elif line.startswith("## "):
                        html_lines.append(f"<h3>{line[3:]}</h3>")
                    elif line.startswith("# "):
                        html_lines.append(f"<h2>{line[2:]}</h2>")
                    elif line.startswith("**") and line.endswith("**") and len(line) > 4:
                        html_lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
                    elif line.strip():
                        html_lines.append(f"<p>{line}</p>")
            if in_list:
                html_lines.append("</ul>")
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
                    fig_data = _decode_bdata(plotly_data.get("data", []))
                    fig_json = json.dumps(fig_data).replace("</script>", r"<\/script>")
                    layout = _decode_bdata(plotly_data.get("layout", {}))
                    layout.setdefault("autosize", True)
                    layout_json = json.dumps(layout).replace("</script>", r"<\/script>")
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


def _title_label(raw_title: str) -> str:
    """Extract a clean label from a Plotly chart title (strips HTML, takes pre-<br> part)."""
    before_br = raw_title.split("<br>")[0]
    return _HTML_TAG_RE.sub("", before_br).strip()


def extract_correlations(nb_path: Path, section_label: str) -> list[dict]:
    """Pull r / R² / p from stream print lines AND Plotly chart title subtitles."""
    nb = json.loads(nb_path.read_text())
    seen: set[tuple] = set()  # deduplicate (r, r2, p) across both sources
    results = []

    def _add(label, r, r2, p):
        key = (round(r, 4), round(r2, 4), round(p, 4))
        if key in seen:
            return
        seen.add(key)
        results.append({
            "label": label,
            "r": r, "r2": r2, "p": p,
            "section": section_label,
            "notebook": nb_path.stem,
        })

    for cell in nb.get("cells", []):
        if cell["cell_type"] != "code":
            continue
        for output in cell.get("outputs", []):
            otype = output.get("output_type", "")

            # Stream print lines: "Label: r=X, R²=X, p=X"
            if otype == "stream":
                text = "".join(output.get("text", []))
                for m in _CORR_RE.finditer(text):
                    _add(m.group("label").strip(),
                         float(m.group("r")), float(m.group("r2")), float(m.group("p")))

            # Plotly chart titles: extract from layout.title.text
            elif otype in ("display_data", "execute_result"):
                data = output.get("data", {})
                plotly = data.get("application/vnd.plotly.v1+json", {})
                if not plotly:
                    continue
                raw_title = ""
                title_field = plotly.get("layout", {}).get("title", {})
                if isinstance(title_field, dict):
                    raw_title = title_field.get("text", "")
                elif isinstance(title_field, str):
                    raw_title = title_field
                if not raw_title:
                    continue
                m = _TITLE_CORR_RE.search(raw_title)
                if m:
                    _add(_title_label(raw_title),
                         float(m.group("r")), float(m.group("r2")), float(m.group("p")))

    return results


def build_correlation_summary(sections: list) -> str:
    """Build a ranked HTML table of all correlations across all notebooks."""
    all_corrs = []
    for section_label, notebooks in sections:
        for nb_name in notebooks:
            nb_path = NOTEBOOKS_DIR / nb_name
            if nb_path.exists():
                all_corrs.extend(extract_correlations(nb_path, section_label))

    if not all_corrs:
        return "<p><em>No correlation data found — run notebooks first.</em></p>"

    all_corrs.sort(key=lambda c: abs(c["r"]), reverse=True)

    rows = []
    for i, c in enumerate(all_corrs, 1):
        r, r2, p = c["r"], c["r2"], c["p"]
        if p < 0.001:
            sig, sig_color = "***", "#1a6632"
        elif p < 0.01:
            sig, sig_color = "**", "#1a6632"
        elif p < 0.05:
            sig, sig_color = "*", "#856404"
        else:
            sig, sig_color = "ns", "#999"

        abs_r = abs(r)
        if abs_r >= 0.6:
            row_bg = "#d4edda"
        elif abs_r >= 0.4:
            row_bg = "#fff3cd"
        else:
            row_bg = "#f8f9fa"

        direction = "↑" if r >= 0 else "↓"
        rows.append(
            f'<tr style="background:{row_bg}">'
            f'<td style="text-align:center;padding:6px 8px;font-weight:bold;color:#555">{i}</td>'
            f'<td style="padding:6px 8px">{c["label"]}</td>'
            f'<td style="text-align:center;padding:6px 8px">{direction} {r:+.3f}</td>'
            f'<td style="text-align:center;padding:6px 8px">{r2:.3f}</td>'
            f'<td style="text-align:center;padding:6px 8px;color:{sig_color}'
            f';font-weight:bold">{p:.4f} {sig}</td>'
            f'<td style="text-align:center;padding:6px 8px;font-size:0.82em;color:#666">'
            f'{c["section"]}</td>'
            f'</tr>\n'
        )

    th = 'style="padding:8px;text-align:left;background:#4a90d9;color:white"'
    thc = 'style="padding:8px;text-align:center;background:#4a90d9;color:white"'
    header = (
        f"<tr><th {thc}>#</th><th {th}>Correlation</th>"
        f"<th {thc}>r</th><th {thc}>R²</th>"
        f"<th {thc}>p-value</th><th {thc}>Level</th></tr>"
    )
    legend = (
        '<p style="font-size:0.8em;color:#666;margin-top:10px">'
        "Ranked by |r|. "
        "*** p&lt;0.001 &nbsp; ** p&lt;0.01 &nbsp; * p&lt;0.05 &nbsp; ns not significant. "
        "↑ positive &nbsp; ↓ negative. "
        '<span style="background:#d4edda;padding:1px 6px">|r|≥0.6</span> &nbsp;'
        '<span style="background:#fff3cd;padding:1px 6px">0.4≤|r|&lt;0.6</span> &nbsp;'
        '<span style="background:#f8f9fa;padding:1px 6px">|r|&lt;0.4</span>'
        "</p>"
    )
    return (
        f'<table style="width:100%;border-collapse:collapse;font-size:0.9em">'
        f"<thead>{header}</thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        f"</table>{legend}"
    )


def build_html(sections: list) -> str:
    nav_items = "".join(
        f'<li><a href="#section-{i}">{title}</a></li>'
        for i, (title, _) in enumerate(sections)
    )
    nav_items += '<li><a href="#section-summary">Correlation Rankings</a></li>'

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

    summary_html = build_correlation_summary(sections)
    content_blocks.append(
        '<section id="section-summary">'
        "<h2>Correlation Rankings</h2>"
        "<p>All pairwise correlations against homeless rate (or unsheltered %) across "
        "state, county/CoC, and city levels, ranked by strength of correlation.</p>"
        + summary_html
        + "</section>"
    )

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
    out = DOCS_DIR / "index.html"
    out.write_text(html)
    print(f"Report written to {out}")
    print(f"Size: {len(html):,} bytes")


if __name__ == "__main__":
    main()
