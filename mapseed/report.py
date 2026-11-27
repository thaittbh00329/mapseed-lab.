"""Export benchmark results as JSON, CSV and a standalone HTML report."""

import csv
import json
from html import escape
from pathlib import Path

STYLES = """
:root {color-scheme: light; --ink:#1b3128; --muted:#4a5f53; --paper:#f5f5ee;
  --line:#d9dfd2; --green:#1b5b45; --gold:#ffd67e}
* {box-sizing:border-box}
body {margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.55 system-ui,sans-serif}
main {width:min(1030px,calc(100% - 36px));margin:auto;padding:48px 0}
header {background:#173b31;color:white;border-radius:18px;padding:clamp(24px,6vw,60px)}
header p {max-width:60ch;color:#e1eee6;margin-bottom:0}
h1,h2 {line-height:1.12;margin:0 0 12px}
h1 {font-family:Georgia,serif;font-size:clamp(38px,7vw,72px);font-weight:500}
h2 {font-size:25px}
p {margin:0 0 14px}
section {margin-top:30px}
.kpis {display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px}
.kpi, .panel {background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi strong {display:block;font-size:32px;font-variant-numeric:tabular-nums}
.kpi span, .muted {color:var(--muted)}
.overflow {overflow-x:auto}
table {width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
caption {text-align:left;padding:0 0 10px;color:var(--muted)}
th,td {text-align:left;padding:10px;border-bottom:1px solid var(--line)}
tbody th {font-weight:600}
td {white-space:nowrap}
progress {width:72px;height:10px;accent-color:var(--green);margin-right:8px}
details {border-top:1px solid var(--line);padding:10px 0}
summary {cursor:pointer;font-weight:650}
.preview {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));
  gap:16px;align-items:start;margin-top:12px}
pre {margin:0;background:#173b31;color:white;border-radius:9px;display:inline-block;
  padding:10px;font:clamp(10px,2.6vw,15px)/1.2 monospace;letter-spacing:.06em;overflow:auto;max-width:100%}
pre .wall {color:#9abdac}
pre .floor {color:#a4dbc9}
pre .marker {color:var(--gold)}
pre .unknown {color:#ffb6b5}
code {overflow-wrap:anywhere}
a {color:var(--green);font-weight:650}
footer {margin-top:28px}
@media(max-width:520px){main{padding-top:18px}progress{display:none}td,th{padding:8px 5px}}
"""


def score(count: int, trials: int) -> str:
    return (f'<progress aria-hidden="true" value="{count}" max="{trials}"></progress>'
            f"{count}/{trials} ({count / trials:.0%})")


def draw_grid(grid: list[str]) -> str:
    classes = {"#": "wall", ".": "floor", "S": "marker", "E": "marker"}
    return "\n".join("".join(
        f'<span class="{classes.get(tile, "unknown")}">{escape(tile)}</span>'
        for tile in row
    ) for row in grid)


def render_html(data: dict) -> str:
    uniform = data["results"]["uniform"]
    hybrid = data["results"]["hybrid"]
    trials = data["trials"]
    budget = data["budget"]
    num_faults = len(data["faults"])
    rows = []
    examples = []
    for key, label in data["faults"].items():
        rows.append(f"<tr><th scope='row'>{escape(label)}</th>"
                    f"<td>{score(uniform['hits'][key], trials)}</td>"
                    f"<td>{score(hybrid['hits'][key], trials)}</td></tr>")
        example = hybrid["examples"].get(key) or uniform["examples"].get(key)
        if example is None:
            continue
        case = example["case"]
        command = (f"python -m mapseed inspect {case['seed']} --width {case['width']} "
                   f"--height {case['height']} --density {case['density']} --fault {key}")
        examples.append(
            f"""<details><summary>{escape(label)}</summary>
            <div class="preview"><div><pre aria-label="Tile map">{draw_grid(example['grid'])}</pre></div>
            <div><p>Detected checks <strong>{escape(', '.join(example['issues']))}</strong></p>
            <p>Run this case locally</p><code>{escape(command)}</code></div></div></details>"""
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MapSeed Lab · Benchmark</title><style>{STYLES}</style></head>
<body><main>
<header><h1>MapSeed Lab</h1><p>How many map generator regressions can a test run catch
with a fixed number of seeds? Compare uniform draws with a sampler that also exercises input boundaries.</p></header>
<section class="kpis" aria-label="Benchmark summary">
<div class="kpi"><strong>{uniform['mean_faults']:.2f}/{num_faults}</strong><span>Uniform mean faults found</span></div>
<div class="kpi"><strong>{hybrid['mean_faults']:.2f}/{num_faults}</strong><span>Hybrid mean faults found</span></div>
<div class="kpi"><strong>{trials} × {budget}</strong><span>Trials × maps per strategy</span></div>
<div class="kpi"><strong>{uniform['clean_failures'] + hybrid['clean_failures']}</strong><span>False flags on control maps</span></div>
</section>
<section class="panel"><h2>Fault detection</h2><div class="overflow"><table>
<caption>Trials that detected each injected fault at least once.</caption>
<thead><tr><th scope="col">Injected fault</th><th scope="col">Uniform</th><th scope="col">Hybrid</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></section>
<section class="panel"><h2>Reproduce a failure</h2>
<p class="muted">S marks the spawn, E the exit, # a wall and . open terrain.</p>
{''.join(examples) or '<p>No failures were captured at this budget.</p>'}</section>
<section class="panel"><h2>Experiment setup</h2>
<p>Both samplers use the same map seeds and budget in each paired trial. Hybrid replaces
every other input shape and wall density with a case from fixed edge sequences.</p>
<p>The fault scenarios are deliberate fixtures for one reference generator. Detection
rates describe this benchmark. Games with other generators or terrain rules need their own validation checks.</p>
<p class="muted">Seed {data['seed']} · {trials} trials · {budget} maps per trial per strategy</p></section>
<footer><a href="summary.csv">Download CSV</a> · <a href="results.json">Download JSON</a></footer>
</main></body></html>
"""


def save_report(data: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text(render_html(data), encoding="utf-8")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("strategy", "fault", "trials_detected", "trials_total"))
        for strategy, result in data["results"].items():
            for fault, count in result["hits"].items():
                writer.writerow((strategy, fault, count, data["trials"]))
