"""Run the silver script against small workbooks in temporary directories."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


class SilverScriptTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        scripts = self.root / "assets" / "scripts" / "too_messy_to_melt"
        self.data = self.root / "assets" / "files" / "datasets" / "too_messy_to_melt"
        scripts.mkdir(parents=True)
        self.data.mkdir(parents=True)
        source = Path(__file__).with_name("silver_too_messy_to_melt_script.py")
        self.script = scripts / source.name
        shutil.copy2(source, self.script)

        clubs = ["Sample City", "Sample United"]
        rows = [{
            "Relegated Team": club,
            "Season": "2023-24",
            "Year Before": "2022-23",
            "Year Before Att": 19000,
            "Attendance": 20000,
            "Year After": "2024-25",
            "Attendance year after": 18000,
            "2 years after": "2025-26",
            "Attendance 2 years after": 18500,
        } for club in clubs]
        # A misspelled club exercises the audit's sort/fuzzy-match branch.
        rows[0]["Relegated Team"] = "Sample Cty"
        rows.extend([{"Attendance": 40000}, {"Attendance": 2}, {"Attendance": 0}])
        pd.DataFrame(rows).to_excel(
            self.data / "Relegation Attendance Churn_copy.xlsx", index=False
        )

        history = [{
            "team_name": club, "season": year, "position": 18 if year == 2023 else 10,
            "played": 38 if year < 2024 else 46, "wins": 10,
            "goals_for": 40, "goals_against": 50, "points": 40,
            "tier": 1 if year < 2024 else 2,
        } for club in clubs for year in range(2022, 2026)]
        pd.DataFrame(history).to_csv(self.data / "standings.csv", index=False)

    def run_script(self, cwd):
        return subprocess.run(
            [sys.executable, str(self.script)], cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=30,
        )

    def assert_successful_panel(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        csv = pd.read_csv(self.data / "silver_relegation_attendance.csv")
        parquet = pd.read_parquet(self.data / "silver_relegation_attendance.parquet")
        self.assertEqual(len(csv), 8)
        self.assertEqual(set(csv["Team"]), {"Sample City", "Sample United"})
        self.assertTrue(csv["Observation_ID"].is_unique)
        for _, panel in csv.groupby("Relegation_Event_ID"):
            self.assertEqual(set(panel["Year_vs_Relegation"]), {-1, 0, 1, 2})
        latest = csv.loc[csv["Season"] == "2025-26"]
        self.assertEqual(len(latest), 2)
        self.assertTrue(latest["Tier"].notna().all())
        self.assertEqual(set(latest["Attendance"]), {18500})
        self.assertEqual(list(csv["Observation_ID"]), list(parquet["Observation_ID"]))
        self.assertTrue((self.data / "silver_run_log.csv").is_file())

    def test_root_run_ignores_blank_team_summary_rows_and_preserves_2025_data(self):
        self.assert_successful_panel(self.run_script(self.root))

    def test_run_from_unrelated_directory_uses_script_relative_paths(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()
        self.assert_successful_panel(self.run_script(unrelated))

    def test_missing_workbook_stops_without_writing_outputs(self):
        (self.data / "Relegation Attendance Churn_copy.xlsx").unlink()
        result = self.run_script(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Attendance workbook not found", result.stderr)
        self.assertFalse((self.data / "silver_relegation_attendance.csv").exists())
        self.assertFalse((self.data / "silver_relegation_attendance.parquet").exists())


if __name__ == "__main__":
    unittest.main()
