# MapSeed Lab

A Python command-line tool for checking procedural tile maps and running repeatable tests of map generators. It checks the layout, tile alphabet, sealed border, unique spawn and exit, and a walkable route from spawn to exit. The benchmark compares two ways to choose inputs under the same budget.

## Quick start

Use Python 3.10 or later from the repository root. No third-party packages are required. On Windows, use the Python launcher **py** in place of **python** if needed.

    python -m mapseed inspect 271 --width 15 --height 10 --density 45
    python -m mapseed inspect 41 --fault extra-spawn
    python -m unittest discover -s tests -v

The second command reproduces an injected duplicate spawn and exits with status 1. A valid map returns 0, and invalid input or file errors return 2.

## Check a map from your generator

Export a JSON array of strings, one string per row. Use **#** for walls, **.** for walkable cells, **S** for spawn and **E** for exit. Exporters can translate their own tile IDs before writing the JSON.

    ["#####", "#S.E#", "#####"]

Save the array as **map.json** and run:

    python -m mapseed validate map.json

Walkability uses four neighbors. The route must begin at S and end at E. The validator permits disconnected pockets of floor when the required route is intact. Its dimensions are limited only by available memory. The included reference generator accepts widths and heights from 7 through 24 and densities from 0 through 100. The density is the chance of a wall before carving the guaranteed route.

## Reproduce the benchmark

    python -m mapseed benchmark --seed 271 --trials 48 --budget 20 --out docs

Open [docs/index.html](docs/index.html) locally for the benchmark report with expandable maps and commands that replay failures. The same run writes [summary.csv](docs/summary.csv) and [results.json](docs/results.json).

| Sampling strategy | Mean injected faults detected per trial | Clean reference maps flagged |
| --- | ---: | ---: |
| Uniform random | 3.38 / 6 | 0 / 960 |
| Hybrid boundary and random | 5.40 / 6 | 0 / 960 |

The average counts each of the six faults once per trial if any evaluated map reveals its expected violation. Each strategy uses the same map seeds and the same budget in each paired trial. The uniform strategy samples width, height and density uniformly. Hybrid replaces those dimensions in alternating cases with a fixed sequence of small, large and asymmetric shapes and of density values that include both bounds. For each input, the benchmark builds a clean reference map, then evaluates each eligible fault in isolation. It stops evaluating a fault after its first detection within a trial.

The scenarios are controlled regressions such as a missing exit on open terrain and an isolated exit at high wall densities. They are synthetic fixtures. The result measures detection under this generator and fault set, with several faults deliberately triggered at boundaries. It does not establish detection rates for production games or general testing workloads.

See [RESEARCH.md](RESEARCH.md) for the hypothesis, method and results at four testing budgets.

## Layout

- **mapseed/grid.py** implements reference generation and the validator.
- **mapseed/benchmark.py** implements samplers, fault fixtures and aggregation.
- **mapseed/report.py** exports the HTML, CSV and JSON reports.
- **tests/test_mapseed.py** verifies clean controls, specific failures, paired sampling and the CLI.

[MIT license](LICENSE)
