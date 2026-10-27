"""Check COVID comparisons with nullable stadium and silver Parquet data."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


class GoldScriptTests(unittest.TestCase):
    def test_nullable_covid_comparisons_preserve_panel_and_baseline_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "assets" / "scripts" / "too_messy_to_melt"
            data = root / "assets" / "files" / "datasets" / "too_messy_to_melt"
            scripts.mkdir(parents=True)
            data.mkdir(parents=True)
            script = scripts / "gold_too_messy_to_melt_script.py"
            shutil.copy2(Path(__file__).with_name(script.name), script)

            clubs = ["Equal FC", "One missing FC", "Both missing FC",
                     "Different FC", "Unknown tier FC", "Century FC"]
            pd.DataFrame({"Team": clubs, "Club_City": ["Home city"] * len(clubs)}).to_csv(
                data / "club_city_lookup.csv", index=False
            )
            silver_rows = []
            stadium_rows = []
            for club in clubs:
                event_year = 1999 if club == "Century FC" else 2020
                event_id = f"{club} {event_year}-{str(event_year + 1)[-2:]}"
                for year_vs in (-1, 0, 1, 2):
                    year = event_year + year_vs
                    season = f"{year}-{str(year + 1)[-2:]}"
                    tier = 1 if year_vs <= 0 else 2
                    if club == "Unknown tier FC" and year_vs == -1:
                        tier = pd.NA
                    silver_rows.append({
                        "Observation_ID": f"{event_id}_{year_vs}",
                        "Relegation_Event_ID": event_id,
                        "Team": club, "Season": season, "Tier": tier,
                        "Year_vs_Relegation": year_vs,
                        "Attendance": {-1: 10000, 0: pd.NA, 1: 8000, 2: 8500}[year_vs],
                        "Year_End_Outcome": "Survived",
                        "Goals_For_History": 40, "Points_History": 45,
                        "Games_Played_History": 38,
                    })
                    stadium, capacity = "Same ground", 20000
                    if club == "Both missing FC" and year_vs <= 0:
                        stadium, capacity = pd.NA, pd.NA
                    elif club == "One missing FC" and year_vs == 0:
                        stadium, capacity = pd.NA, pd.NA
                    elif club == "One missing FC" and year_vs == -1:
                        capacity = pd.NA
                    elif club == "Different FC" and year_vs == 0:
                        stadium = "New ground"
                    stadium_rows.append({
                        "Team": club,
                        "Season": "1999–2000" if year == 1999 else season.replace("-", "–"),
                        "Tier": tier, "Stadium": stadium, "Capacity": capacity,
                        "GeoPlace": "Old stadium, Other city, England",
                    })

            silver = pd.DataFrame(silver_rows)
            for column in ("Tier", "Attendance", "Goals_For_History", "Points_History",
                           "Games_Played_History"):
                silver[column] = silver[column].astype("Int64")
            silver.to_parquet(data / "silver_relegation_attendance.parquet", index=False)
            pd.DataFrame(stadium_rows).to_csv(data / "gold_dim_stadiums_pyramid.csv", index=False)

            result = subprocess.run(
                [sys.executable, str(script)], cwd=root, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            gold = pd.read_parquet(data / "gold_relegation_attendance.parquet")
            self.assertEqual(len(gold), len(silver))
            self.assertTrue(gold["Observation_ID"].is_unique)
            self.assertEqual(set(gold["Observation_ID"]), set(silver["Observation_ID"]))
            self.assertEqual(set(gold["Club_City"]), {"Home city"})
            self.assertTrue(gold.loc[gold["Stadium"].isna(), "Club_City"].notna().all())
            self.assertEqual(set(gold["GeoPlace"]), {"Home city, United Kingdom"})
            century = gold.loc[gold["Team"].eq("Century FC")]
            self.assertEqual(len(century), 4)
            self.assertTrue(century["Stadium"].notna().all())
            self.assertTrue(century["Capacity"].notna().all())
            self.assertEqual(set(century["Season"]), {"1998-99", "1999-00", "2000-01", "2001-02"})
            substituted = gold.loc[gold["Is_Baseline_Substituted"]]
            self.assertEqual(set(substituted["Team"]), {"Equal FC", "Both missing FC"})
            self.assertEqual(set(substituted["Baseline_Attendance"]), {10000})
            reviewed = gold.loc[gold["Covid_Baseline_Review_Flag"]]
            self.assertEqual(set(reviewed["Team"]), {"Both missing FC"})
            rejected = gold.loc[gold["Covid_Baseline_Not_Comparable"]]
            self.assertEqual(set(rejected["Team"]),
                             {"One missing FC", "Different FC", "Unknown tier FC"})
            year_one = substituted.loc[substituted["Year_vs_Relegation"] == 1]
            self.assertEqual(set(year_one["Pct_Change_Analysis"].round(8)), {-20.0})
            self.assertTrue(gold.loc[gold["Year_vs_Relegation"] <= 0,
                                     "Pct_Change_Analysis"].isna().all())

            # One club-season can occur in multiple event panels. The lookup
            # must fill both observations without multiplying rows.
            repeated = silver.loc[silver["Team"].eq("One missing FC")].copy()
            repeated["Observation_ID"] += "_repeat"
            repeated["Relegation_Event_ID"] += "_repeat"
            expanded = pd.concat([silver, repeated], ignore_index=True)
            expanded.to_parquet(data / "silver_relegation_attendance.parquet", index=False)
            lookup = pd.DataFrame([
                {"Team": "One missing FC", "Season": "2019-20", "Tier": 1,
                 "Stadium": "Do not replace sourced ground", "Capacity": 20000.0,
                 "SourceURL": "https://example.test/history", "Notes": "Capacity-only fill"},
                {"Team": "One missing FC", "Season": "2020-21", "Tier": 1,
                 "Stadium": "Same ground", "Capacity": 20000.0,
                 "SourceURL": "https://example.test/history", "Notes": "User-supplied season record"},
                {"Team": "Both missing FC", "Season": "2019-20", "Tier": 1,
                 "Stadium": "Manual ground", "Capacity": 19000.0,
                 "SourceURL": "https://example.test/manual", "Notes": "Manual value"},
                {"Team": "Both missing FC", "Season": "2020-21", "Tier": 1,
                 "Stadium": "Manual ground", "Capacity": 19000.0,
                 "SourceURL": "https://example.test/manual", "Notes": "Manual value"},
                {"Team": "Century FC", "Season": "1999-2000", "Tier": 1,
                 "Stadium": "Do not replace", "Capacity": 99999.0,
                 "SourceURL": "https://example.test/unused", "Notes": "Existing fields take priority"},
                {"Team": "One missing FC", "Season": "2021-22", "Tier": 3,
                 "Stadium": "Wrong tier", "Capacity": 21000.0,
                 "SourceURL": "https://example.test/unused", "Notes": "Tier must match"},
            ])
            lookup.to_csv(data / "stadium_capacity_lookup_template.csv", index=False)
            result = subprocess.run([sys.executable, str(script)], cwd=root, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            enriched = pd.read_parquet(data / "gold_relegation_attendance.parquet")
            self.assertEqual(len(enriched), len(expanded))
            self.assertTrue(enriched["Observation_ID"].is_unique)
            self.assertEqual(enriched["Stadium_Lookup_Applied"].sum(), 4)
            self.assertEqual(enriched["Capacity_Lookup_Applied"].sum(), 6)
            partial = enriched.loc[enriched["Team"].eq("One missing FC") & enriched["Season"].eq("2019-20")]
            self.assertEqual(set(partial["Stadium"]), {"Same ground"})
            self.assertFalse(partial["Stadium_Lookup_Applied"].any())
            self.assertTrue(partial["Capacity_Lookup_Applied"].all())
            supplied = enriched.loc[enriched["Team"].eq("One missing FC") & enriched["Season"].eq("2020-21")]
            self.assertEqual(len(supplied), 2)
            self.assertEqual(set(supplied["Stadium"]), {"Same ground"})
            self.assertEqual(set(supplied["Capacity"]), {20000})
            self.assertEqual(set(supplied["Capacity_SourceURL"]), {"https://example.test/history"})
            self.assertEqual(set(supplied["Stadium_Capacity_Lookup_Notes"]), {"User-supplied season record"})
            self.assertTrue(supplied["Is_Baseline_Substituted"].all())
            self.assertFalse(enriched.loc[enriched["Team"].eq("Both missing FC"), "Covid_Baseline_Review_Flag"].any())
            century = enriched.loc[enriched["Team"].eq("Century FC")]
            self.assertEqual(set(century["Capacity"]), {20000})
            self.assertEqual(set(century["Stadium"]), {"Same ground"})
            self.assertFalse(century["Stadium_Lookup_Applied"].any())
            self.assertEqual(set(enriched["GeoPlace"]), {"Home city, United Kingdom"})
            pd.testing.assert_series_equal(
                enriched.set_index("Observation_ID")["Attendance"].sort_index(),
                expanded.set_index("Observation_ID")["Attendance"].sort_index(),
            )

    def test_invalid_stadium_lookup_stops_before_outputs_are_overwritten(self):
        row = {"Team": "Club", "Season": "2025-26", "Tier": 2,
               "Stadium": "Ground", "Capacity": 20000.0}
        cases = [
            (pd.DataFrame([row, row]), "duplicate"),
            (pd.DataFrame([{**row, "Capacity": 20000.5}]), "whole numbers"),
            (pd.DataFrame([{**row, "Capacity": -1}]), "whole numbers"),
            (pd.DataFrame([{**row, "Capacity": None}]), "blank"),
            (pd.DataFrame([{**row, "Tier": 2.5}]), "tiers"),
            (pd.DataFrame([{**row, "Season": "2025-28"}]), "end years"),
        ]
        for lookup, error in cases:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                scripts = root / "assets" / "scripts" / "too_messy_to_melt"
                data = root / "assets" / "files" / "datasets" / "too_messy_to_melt"
                scripts.mkdir(parents=True)
                data.mkdir(parents=True)
                script = scripts / "gold_too_messy_to_melt_script.py"
                shutil.copy2(Path(__file__).with_name(script.name), script)
                pd.DataFrame({"Team": ["Club"], "Club_City": ["Town"]}).to_csv(
                    data / "club_city_lookup.csv", index=False
                )
                pd.DataFrame({"Team": ["Club"], "Season": ["2025-26"], "Tier": [2],
                              "Observation_ID": ["Club_2025"]}).to_parquet(
                    data / "silver_relegation_attendance.parquet", index=False
                )
                lookup.to_csv(data / "stadium_capacity_lookup_template.csv", index=False)
                output = data / "gold_relegation_attendance.csv"
                output.write_text("existing output", encoding="utf-8")
                result = subprocess.run([sys.executable, str(script)], cwd=root, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace", timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), "existing output")

    def test_invalid_club_city_lookup_stops_before_outputs_are_overwritten(self):
        cases = [
            (pd.DataFrame({"Team": ["Club", "Club"], "Club_City": ["A", "B"]}), "duplicate"),
            (pd.DataFrame({"Team": ["Club"], "Club_City": [None]}), "blank"),
            (pd.DataFrame({"Team": ["Other club"], "Club_City": ["City"]}), "Add these teams"),
        ]
        for lookup, error in cases:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                scripts = root / "assets" / "scripts" / "too_messy_to_melt"
                data = root / "assets" / "files" / "datasets" / "too_messy_to_melt"
                scripts.mkdir(parents=True)
                data.mkdir(parents=True)
                script = scripts / "gold_too_messy_to_melt_script.py"
                shutil.copy2(Path(__file__).with_name(script.name), script)
                pd.DataFrame({"Team": ["Club"], "Season": ["2025-26"], "Tier": [2],
                              "Observation_ID": ["Club_2025"]}).to_parquet(
                    data / "silver_relegation_attendance.parquet", index=False
                )
                lookup.to_csv(data / "club_city_lookup.csv", index=False)
                output = data / "gold_relegation_attendance.csv"
                output.write_text("existing output", encoding="utf-8")
                result = subprocess.run([sys.executable, str(script)], cwd=root, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace", timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), "existing output")


if __name__ == "__main__":
    unittest.main()
