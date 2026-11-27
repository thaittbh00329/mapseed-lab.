"""Command-line entry point for MapSeed Lab."""

import argparse
import json
from pathlib import Path

from .benchmark import FAULTS, apply_fault, benchmark
from .grid import Case, generate, validate
from .report import save_report


def run() -> int:
    parser = argparse.ArgumentParser(prog="python -m mapseed")
    cmds = parser.add_subparsers(dest="command", required=True)
    inspect = cmds.add_parser("inspect", help="generate and validate a tile map")
    inspect.add_argument("seed", type=int)
    inspect.add_argument("--width", type=int, default=12)
    inspect.add_argument("--height", type=int, default=10)
    inspect.add_argument("--density", type=int, default=40)
    inspect.add_argument("--fault", choices=FAULTS)
    check = cmds.add_parser("validate", help="check an exported JSON array of tile rows")
    check.add_argument("file", type=Path)
    compare = cmds.add_parser("benchmark", help="compare samplers and write reports")
    compare.add_argument("--seed", type=int, default=271)
    compare.add_argument("--trials", type=int, default=48)
    compare.add_argument("--budget", type=int, default=20)
    compare.add_argument("--out", type=Path, default=Path("docs"))
    args = parser.parse_args()

    try:
        if args.command == "benchmark":
            if args.trials < 1 or args.budget < 1:
                parser.error("--trials and --budget must be positive")
            result = benchmark(args.seed, args.trials, args.budget)
            save_report(result, args.out)
            for key, row in result["results"].items():
                print(f"{key:7} {row['mean_faults']:.2f}/{len(FAULTS)} faults per trial; "
                      f"{row['clean_failures']} clean maps flagged")
            print(f"Reports written to {args.out}")
            return 0

        if args.command == "validate":
            grid = json.loads(args.file.read_text(encoding="utf-8"))
            if not isinstance(grid, list):
                parser.error("map file must contain an array of tile rows")
        else:
            case = Case(args.seed, args.width, args.height, args.density)
            grid = generate(case)
            if args.fault:
                fault = FAULTS[args.fault]
                if not fault.when(case):
                    print(f"{args.fault} did not trigger for this case.")
                grid = apply_fault(case, grid, fault)
            print("\n".join(grid))

        issues = validate(grid)
        print("PASS" if not issues else "FAIL: " + ", ".join(issues))
        return int(bool(issues))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(run())
