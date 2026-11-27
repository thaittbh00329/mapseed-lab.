import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mapseed.benchmark import FAULTS, apply_fault, benchmark, sample_cases
from mapseed.grid import Case, generate, validate


class GridTests(unittest.TestCase):
    def test_clean_maps_and_reproducibility(self):
        for seed in (0, 1, 271, 999):
            for width, height in ((7, 24), (24, 7), (12, 10)):
                for density in (0, 50, 100):
                    case = Case(seed, width, height, density)
                    grid = generate(case)
                    self.assertEqual(grid, generate(case))
                    self.assertEqual(validate(grid), ())

    def test_each_fault_detected_without_mutating_reference(self):
        cases = {
            "short-row": Case(1, 7, 12, 30),
            "open-border": Case(1, 12, 24, 30),
            "absent-exit": Case(1, 12, 12, 0),
            "isolated-exit": Case(1, 12, 12, 100),
            "unknown-tile": Case(1, 8, 22, 50),
            "extra-spawn": Case(41, 12, 12, 50),
        }
        self.assertEqual(set(cases), set(FAULTS))
        for key, case in cases.items():
            with self.subTest(fault=key):
                fault = FAULTS[key]
                clean = generate(case)
                self.assertEqual(validate(apply_fault(case, clean, fault)), (fault.code,))
                self.assertEqual(validate(clean), ())

    def test_invalid_shape_short_circuits(self):
        for grid in ([], [""], ["####", "##"], [42], "####"):
            self.assertEqual(validate(grid), ("shape",))


class BenchmarkTests(unittest.TestCase):
    def test_equal_budgets_and_same_map_seeds(self):
        uniform = sample_cases(271, 20, "uniform")
        hybrid = sample_cases(271, 20, "hybrid")
        self.assertEqual(len(uniform), 20)
        self.assertEqual([c.seed for c in uniform], [c.seed for c in hybrid])
        self.assertEqual(uniform[1::2], hybrid[1::2])

    def test_benchmark_is_reproducible(self):
        outcome = benchmark(271, 4, 20)
        self.assertEqual(outcome, benchmark(271, 4, 20))
        for row in outcome["results"].values():
            self.assertEqual(row["clean_failures"], 0)
            self.assertAlmostEqual(row["mean_faults"], sum(row["hits"].values()) / 4)

    def test_cli_exports_reports_and_validates_user_maps(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            subprocess.run(
                [sys.executable, "-m", "mapseed", "benchmark", "--trials", "3", "--out", folder],
                check=True,
                capture_output=True,
            )
            data = json.loads((path / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(data["trials"], 3)
            with (path / "summary.csv").open(newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2 * len(FAULTS))
            self.assertIn("Reproduce a failure", (path / "index.html").read_text(encoding="utf-8"))
            map_file = path / "map.json"
            map_file.write_text(json.dumps(["#####", "#S#E#", "#####"]), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "mapseed", "validate", str(map_file)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout.strip(), "FAIL: route")


if __name__ == "__main__":
    unittest.main()
