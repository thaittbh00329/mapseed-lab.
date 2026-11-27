# Comparing input sampling strategies for procedural tile map tests

## Question

At a fixed map input budget, does combining boundary cases with uniform random inputs expose more layout regressions than sampling every input uniformly? The hypothesis is that boundary cases improve coverage of faults tied to map dimensions or wall density, while keeping the map seed stream fixed leaves detection of seed-only faults unchanged.

## Method

MapSeed Lab generates rectangular levels with a sealed boundary, spawn, exit and a guaranteed four-neighbor route. The validator checks those properties and the tile alphabet. Six single-fault variants inject a malformed row, an open border, a missing exit, a disconnected exit, an unsupported tile or a duplicate spawn. Each variant activates under a documented input condition in **mapseed/benchmark.py**.

The strategies share the same stream of map seeds in each paired trial. The uniform strategy draws both dimensions and wall density uniformly. The hybrid strategy replaces those three parameters with fixed edge sequences for every other case. The successful detection of a fault means that the validator reports its expected violation at least once during a trial. Each trial also checks all unmodified reference maps for false flags. The budget counts parameter cases per trial, and actual runtime and per-fault validation work can differ.

## Results

Each row uses 48 paired trials with base seed 271. The scores are mean distinct faults detected per trial, out of six.

| Map inputs per trial | Uniform | Hybrid | Hybrid advantage |
| ---: | ---: | ---: | ---: |
| 4 | 0.81 | 4.29 | 3.48 |
| 8 | 1.73 | 4.54 | 2.81 |
| 20 | 3.38 | 5.40 | 2.02 |
| 40 | 4.35 | 5.58 | 1.23 |

At 20 cases, the hybrid strategy found every geometry- or density-triggered fault in all 48 trials. Both strategies found the duplicate-spawn fault in 19 of 48 trials because this fault only depends on the map seed. At all four budgets, neither strategy flagged a valid reference map. The smaller advantage at higher budgets coincides with uniform sampling finding more of the edge conditions as it receives more chances to do so.

Re-run any row by replacing BUDGET with its value:

    python -m mapseed benchmark --seed 271 --trials 48 --budget BUDGET --out out

The report at [docs/index.html](docs/index.html) shows per-fault counts and runnable examples for the 20-case setting.

## Limits and next experiment

The fixtures were introduced deliberately and several use the same input boundaries covered by hybrid sampling. This controlled comparison shows how these fixtures respond to a fixed input budget. Actual defect rates and performance on different generators remain unmeasured. A follow-up can test exports from an independent Godot prototype, define faults after examining real generator failures, and report detection at equal map and equal time budgets.
