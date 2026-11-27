"""Compare seed selection strategies with the same number of generated maps."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
from random import Random
from statistics import mean

from .grid import MAX_SIDE, MIN_SIDE, Case, generate, validate


@dataclass(frozen=True)
class Fault:
    name: str
    code: str
    when: Callable[[Case], bool]
    edit: Callable[[list[str], Case], None]


def change_tile(grid: list[str], x: int, y: int, tile: str) -> None:
    grid[y] = grid[y][:x] + tile + grid[y][x + 1:]


def isolate_exit(grid: list[str], case: Case) -> None:
    change_tile(grid, case.width - 3, case.height - 2, "#")
    change_tile(grid, case.width - 2, case.height - 3, "#")


FAULTS = {
    "short-row": Fault(
        "Truncated final row at minimum width", "shape",
        lambda c: c.width == MIN_SIDE,
        lambda g, c: g.__setitem__(-1, g[-1][:-1]),
    ),
    "open-border": Fault(
        "Open border on maximum-height maps", "border",
        lambda c: c.height == MAX_SIDE,
        lambda g, c: change_tile(g, 0, 2, "."),
    ),
    "absent-exit": Fault(
        "Missing exit with fully open terrain", "exit",
        lambda c: c.density == 0,
        lambda g, c: change_tile(g, c.width - 2, c.height - 2, "."),
    ),
    "isolated-exit": Fault(
        "Exit isolated at high wall densities", "route",
        lambda c: c.density >= 92,
        isolate_exit,
    ),
    "unknown-tile": Fault(
        "Unknown tile on narrow, tall maps", "tile",
        lambda c: c.width <= 8 and c.height >= 20,
        lambda g, c: change_tile(g, 2, 2, "?"),
    ),
    "extra-spawn": Fault(
        "Duplicate spawn for a rare class of seeds", "spawn",
        lambda c: c.seed % 41 == 0,
        lambda g, c: change_tile(g, 2, 2, "S"),
    ),
}

EDGE_SHAPES = (
    (MIN_SIDE, MAX_SIDE), (MAX_SIDE, MIN_SIDE),
    (MIN_SIDE, MIN_SIDE), (MAX_SIDE, MAX_SIDE),
    (MIN_SIDE + 1, MAX_SIDE - 1), (MAX_SIDE - 1, MIN_SIDE + 1),
)
EDGE_DENSITIES = (0, 1, 25, 50, 75, 99, 100)


def sample_cases(seed: int, budget: int, strategy: str) -> list[Case]:
    rng = Random(seed)
    cases = []
    for index in range(budget):
        case_seed = rng.randrange(2**32)
        width = rng.randint(MIN_SIDE, MAX_SIDE)
        height = rng.randint(MIN_SIDE, MAX_SIDE)
        density = rng.randint(0, 100)
        if strategy == "hybrid" and index % 2 == 0:
            # Keep the same map seeds while steering three input dimensions toward edges.
            width, height = EDGE_SHAPES[(index // 2) % len(EDGE_SHAPES)]
            density = EDGE_DENSITIES[(index // 2) % len(EDGE_DENSITIES)]
        cases.append(Case(case_seed, width, height, density))
    return cases


def apply_fault(case: Case, reference: list[str], fault: Fault) -> list[str]:
    grid = reference.copy()
    if fault.when(case):
        fault.edit(grid, case)
    return grid


def benchmark(seed: int, trials: int, budget: int) -> dict:
    results = {}
    for strategy in ("uniform", "hybrid"):
        hits = {key: 0 for key in FAULTS}
        first_cases = {}
        clean_failures = 0
        totals = []
        for trial in range(trials):
            found = set()
            for case in sample_cases(seed + trial, budget, strategy):
                reference = generate(case)
                if validate(reference):
                    clean_failures += 1
                for key, fault in FAULTS.items():
                    if key in found or not fault.when(case):
                        continue
                    grid = apply_fault(case, reference, fault)
                    issues = validate(grid)
                    if fault.code in issues:
                        found.add(key)
                        first_cases.setdefault(key, {"case": asdict(case), "grid": grid, "issues": issues})
            for key in found:
                hits[key] += 1
            totals.append(len(found))
        results[strategy] = {
            "mean_faults": mean(totals),
            "clean_failures": clean_failures,
            "hits": hits,
            "examples": first_cases,
        }
    return {
        "seed": seed,
        "trials": trials,
        "budget": budget,
        "faults": {key: fault.name for key, fault in FAULTS.items()},
        "results": results,
    }
