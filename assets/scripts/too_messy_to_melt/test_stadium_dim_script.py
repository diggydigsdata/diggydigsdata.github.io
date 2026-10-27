"""Offline regression checks for stadium updates and saved-data recovery."""

import io
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import stadium_dim_script as scraper


def saved_table(year, tier=1, count=20, stadium="Saved ground"):
    return pd.DataFrame({
        "Season": [scraper.season_str(year)] * count,
        "Tier": [tier] * count,
        "Team": [f"Club {number}" for number in range(count)],
        "Stadium": [stadium] * count,
        "Location": ["Test town"] * count,
        "Capacity_raw": ["20000"] * count,
        "Capacity": [20000] * count,
        "GeoPlace": [f"{stadium}, Test town, England"] * count,
    })


def page_html(stadium="New ground", count=20):
    return saved_table(2025, count=count, stadium=stadium)[
        ["Team", "Stadium", "Location", "Capacity_raw"]
    ].rename(columns={"Capacity_raw": "Capacity"}).to_html(index=False)


class StadiumScraperTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        for name in ("OUTPUT_PATH", "CHECKPOINT_PATH", "ISSUES_PATH"):
            self.stack.enter_context(patch.object(scraper, name, directory / f"{name}.csv"))
        self.output = self.stack.enter_context(redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(scraper.time, "sleep"))

    def test_tied_stadium_tables_keep_first_without_comparing_dataframes(self):
        tables = pd.read_html(io.StringIO(page_html("First") + page_html("Second")),
                              flavor="html5lib")
        result = scraper.extract_stadia_table(tables)
        self.assertEqual(len(result), 20)
        self.assertEqual(set(result["Stadium"]), {"First"})

    def test_fields_merge_from_stadium_attendance_and_location_tables(self):
        teams = [f"Club {n}" for n in range(20)]
        stadiums = pd.DataFrame({"Team": teams, "Ground": [f"Ground {n}" for n in range(20)]})
        attendance = pd.DataFrame({"Club": [team + " F.C." for team in reversed(teams)],
                                   "Capacity": list(reversed(range(20000, 20020))),
                                   "Average attendance": [1234] * 20})
        locations = pd.DataFrame({"Club": teams, "Town": ["Town"] * 20})
        result = scraper.extract_stadia_table([stadiums, attendance, locations])
        self.assertEqual(len(result), 20)
        self.assertEqual(result.loc[result["Team"].eq("Club 0"), "Capacity_raw"].iloc[0], "20000")
        self.assertEqual(set(result["Location"]), {"Town"})
        self.assertEqual(result.loc[result["Team"].eq("Club 0"), "Stadium"].iloc[0], "Ground 0")

    def test_capacity_only_table_is_kept_without_stadium(self):
        attendance = pd.DataFrame({"Club": [f"Club {n}" for n in range(24)],
                                   "Capacity": [21000.0] * 24, "Average": [10000] * 24})
        result = scraper.extract_stadia_table([attendance])
        self.assertEqual(len(result), 24)
        self.assertTrue(result["Stadium"].isna().all())
        self.assertEqual(set(result["Capacity_raw"].map(scraper.clean_capacity)), {21000})

    def test_attendance_without_capacity_is_not_capacity_evidence(self):
        attendance = pd.DataFrame({"Club": [f"Club {n}" for n in range(24)],
                                   "Average attendance": [10000] * 24, "Highest": [22000] * 24})
        self.assertIsNone(scraper.extract_stadia_table([attendance]))
        attendance["% of capacity"] = 75
        self.assertIsNone(scraper.extract_stadia_table([attendance]))

    def test_combined_page_stays_inside_requested_division(self):
        html = ('<div class="mw-heading"><h2>First Division</h2><span>[edit]</span></div>'
                + page_html("Tier two", 24) + '<h3>Attendances</h3>'
                + pd.DataFrame({"Club": [f"Club {n}" for n in range(24)],
                                "Capacity": [99000] * 24}).to_html(index=False)
                + '<h2>Second Division</h2>' + page_html("Tier three", 24)
                + '<h2>Third Division</h2>' + page_html("Tier four", 24)
                + '<h2>References</h2>' + page_html("Outside", 24))
        for tier, stadium in ((2, "Tier two"), (3, "Tier three"), (4, "Tier four")):
            result = scraper.extract_stadia_table(scraper.read_division_tables(html, tier, 1992))
            self.assertEqual(set(result["Stadium"]), {stadium})
            self.assertEqual(set(result["Capacity_raw"]), {"20000"})

    def test_partial_metadata_uses_league_table_roster(self):
        teams = [f"Club {n}" for n in range(24)]
        league = pd.DataFrame({"Team": teams, "Pld": [46] * 24, "Pts": [50] * 24})
        partial = pd.DataFrame({"Club": ["Club 3"], "Capacity": [23000]})
        result = scraper.extract_stadia_table([league, partial])
        self.assertEqual(len(result), 24)
        self.assertEqual(result["Capacity_raw"].notna().sum(), 1)
        self.assertEqual(result.loc[result["Team"].eq("Club 3"), "Capacity_raw"].iloc[0], "23000")

    def test_duplicate_normalized_headers_are_coalesced(self):
        table = pd.DataFrame({"Club": ["Club"], "City": [None], "Town": ["Town"],
                              "Stadium capacity": [25000]})
        normalized = scraper.normalize_columns(table)
        self.assertTrue(normalized.columns.is_unique)
        self.assertEqual(normalized["Location"].iloc[0], "Town")
        self.assertEqual(normalized["Capacity_raw"].iloc[0], 25000)

    def test_city_fill_records_provenance_and_skips_conflicting_donors(self):
        data = pd.DataFrame({"Season": [scraper.season_str(2000)] * 5,
                             "Tier": [2] * 5, "Team": ["A", "A", "B", "B", "B"],
                             "Stadium": ["Ground A"] * 2 + ["Ground B"] * 3,
                             "City": ["Town A", None, "Town B", "Other town", None],
                             "SourceURL": ["https://example.test/direct"] * 5,
                             "Capacity": [20000, None, 30000, 32000, None]})
        result = scraper.impute_stadium_cities(data)
        self.assertEqual(result.loc[1, "City"], "Town A")
        self.assertTrue(result.loc[1, "City_Imputed"])
        self.assertEqual(result.loc[1, "City_SourceURL"], "https://example.test/direct")
        self.assertEqual(result.loc[1, "City_Donor_Season"], scraper.season_str(2000))
        self.assertTrue(pd.isna(result.loc[4, "City"]))
        pd.testing.assert_series_equal(result["Capacity"], data["Capacity"])
        pd.testing.assert_frame_equal(scraper.impute_stadium_cities(result), result)

    def test_partial_refresh_preserves_saved_stadium_and_source(self):
        saved_table(2025).to_csv(scraper.OUTPUT_PATH, index=False)
        capacity_html = pd.DataFrame({"Club": [f"Club {n}" for n in range(20)],
                                      "Capacity": [21000] * 20}).to_html(index=False)
        with patch.object(scraper, "fetch_html", return_value=capacity_html):
            result = scraper.scrape_pyramid_dim(2025, 2026, tiers=(1,), refresh=True, sleep_s=0)
        self.assertEqual(set(result["Stadium"]), {"Saved ground"})
        self.assertEqual(set(result["Capacity"]), {21000})

    def test_capacity_parser_does_not_concatenate_numbers(self):
        self.assertEqual(scraper.clean_capacity(21000.0), 21000)
        self.assertEqual(scraper.clean_capacity("21,000[1]"), 21000)
        self.assertTrue(pd.isna(scraper.clean_capacity("21,000–25,000")))

    def test_missing_markers_allow_capacity_to_be_supplemented(self):
        base = saved_table(2025)[["Team", "Stadium", "Capacity_raw"]].copy()
        base["Capacity_raw"] = "—"
        donor = base[["Team"]].assign(Capacity=22000)
        result = scraper.extract_stadia_table([base, donor])
        self.assertEqual(set(result["Capacity_raw"]), {"22000"})

    def test_city_only_run_does_not_fetch_or_touch_checkpoint(self):
        data = saved_table(2025)
        data["City"] = ["Test town"] + [None] * 19
        data.to_csv(scraper.OUTPUT_PATH, index=False)
        data = pd.read_csv(scraper.OUTPUT_PATH)
        saved_table(2024).to_csv(scraper.CHECKPOINT_PATH, index=False)
        checkpoint = scraper.CHECKPOINT_PATH.read_bytes()
        with patch.object(scraper, "fetch_html") as fetch:
            scraper.main(["--impute-cities-only"])
        fetch.assert_not_called()
        result = pd.read_csv(scraper.OUTPUT_PATH)
        self.assertEqual(result["City"].notna().sum(), 20)
        self.assertEqual(result["City_Imputed"].sum(), 19)
        self.assertEqual(scraper.CHECKPOINT_PATH.read_bytes(), checkpoint)
        pd.testing.assert_frame_equal(result[data.columns].drop(columns="City"),
                                      data.drop(columns="City"), check_dtype=False)

    def test_stadium_change_does_not_inherit_old_capacity(self):
        saved_table(2025).to_csv(scraper.OUTPUT_PATH, index=False)
        venues = pd.DataFrame({"Club": [f"Club {n}" for n in range(20)],
                               "Stadium": ["Different ground"] * 20}).to_html(index=False)
        with patch.object(scraper, "fetch_html", return_value=venues):
            result = scraper.scrape_pyramid_dim(2025, 2026, tiers=(1,), refresh=True, sleep_s=0)
        self.assertEqual(set(result["Stadium"]), {"Different ground"})
        self.assertTrue(result["Capacity"].isna().all())

    def test_new_season_preserves_historical_rows(self):
        historical = saved_table(1992, count=22)
        historical.to_csv(scraper.OUTPUT_PATH, index=False)
        historical = pd.read_csv(scraper.OUTPUT_PATH)
        original_bytes = scraper.OUTPUT_PATH.read_bytes()
        with patch.object(scraper, "fetch_html", return_value=page_html()) as fetch:
            result = scraper.scrape_pyramid_dim(2025, 2026, tiers=(1,), sleep_s=0)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(len(result), 42)
        old = result.loc[result["Season"] == scraper.season_str(1992)]
        pd.testing.assert_frame_equal(old[historical.columns].reset_index(drop=True),
                                      historical, check_dtype=False)
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), original_bytes)

    def test_missing_output_is_allowed(self):
        self.assertTrue(scraper.load_existing_output().empty)

    def test_unreadable_output_aborts_before_fetch_or_checkpoint_cleanup(self):
        scraper.OUTPUT_PATH.write_text("", encoding="utf-8")
        saved_table(2025).to_csv(scraper.CHECKPOINT_PATH, index=False)
        checkpoint_bytes = scraper.CHECKPOINT_PATH.read_bytes()
        with patch.object(scraper, "fetch_html") as fetch:
            with self.assertRaisesRegex(RuntimeError, "Cannot read saved data"):
                scraper.main(["--start-year", "2025", "--end-year", "2026"])
        fetch.assert_not_called()
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), b"")
        self.assertEqual(scraper.CHECKPOINT_PATH.read_bytes(), checkpoint_bytes)

    def test_missing_required_columns_abort(self):
        scraper.OUTPUT_PATH.write_text("Season,Tier\n2025–26,1\n", encoding="utf-8")
        original_bytes = scraper.OUTPUT_PATH.read_bytes()
        with self.assertRaisesRegex(ValueError, "Team"):
            scraper.load_existing_output()
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), original_bytes)

    def test_failed_temporary_write_preserves_output(self):
        saved_table(1992).to_csv(scraper.OUTPUT_PATH, index=False)
        original_bytes = scraper.OUTPUT_PATH.read_bytes()

        def partial_write(df, file, **kwargs):
            file.write("unfinished CSV")
            raise OSError("disk write failed")

        with patch.object(pd.DataFrame, "to_csv", partial_write):
            with self.assertRaisesRegex(OSError, "disk write failed"):
                scraper.save_csv_atomic(saved_table(2025), scraper.OUTPUT_PATH)
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), original_bytes)
        self.assertEqual(list(scraper.OUTPUT_PATH.parent.glob("*.tmp")), [])

    def test_failed_replace_preserves_output_and_checkpoint(self):
        saved_table(1992).to_csv(scraper.OUTPUT_PATH, index=False)
        saved_table(2025).to_csv(scraper.CHECKPOINT_PATH, index=False)
        original_bytes = scraper.OUTPUT_PATH.read_bytes()
        checkpoint_bytes = scraper.CHECKPOINT_PATH.read_bytes()
        with patch.object(Path, "replace", side_effect=PermissionError("file is locked")):
            with self.assertRaisesRegex(PermissionError, "file is locked"):
                scraper.main(["--start-year", "2025", "--end-year", "2026", "--tiers", "1"])
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), original_bytes)
        self.assertEqual(scraper.CHECKPOINT_PATH.read_bytes(), checkpoint_bytes)
        self.assertEqual(list(scraper.OUTPUT_PATH.parent.glob("*.tmp")), [])

    def test_main_resumes_checkpoint_and_clears_it_after_save(self):
        saved_table(1992).to_csv(scraper.OUTPUT_PATH, index=False)
        saved_table(2025).to_csv(scraper.CHECKPOINT_PATH, index=False)
        with patch.object(scraper, "fetch_html") as fetch:
            scraper.main(["--start-year", "2025", "--end-year", "2026", "--tiers", "1"])
        fetch.assert_not_called()
        saved = pd.read_csv(scraper.OUTPUT_PATH)
        self.assertEqual(len(saved), 40)
        self.assertEqual(set(saved["Season"]), {scraper.season_str(1992), scraper.season_str(2025)})
        self.assertFalse(scraper.CHECKPOINT_PATH.exists())

    def test_interrupted_run_resumes_without_rescraping_completed_tier(self):
        saved_table(1992).to_csv(scraper.OUTPUT_PATH, index=False)
        original_bytes = scraper.OUTPUT_PATH.read_bytes()
        args = ["--start-year", "2025", "--end-year", "2026", "--tiers", "1", "2"]
        with patch.object(scraper, "fetch_html", side_effect=[page_html(), KeyboardInterrupt]):
            with self.assertRaises(KeyboardInterrupt):
                scraper.main(args)
        self.assertEqual(scraper.OUTPUT_PATH.read_bytes(), original_bytes)
        checkpoint = pd.read_csv(scraper.CHECKPOINT_PATH)
        self.assertEqual(set(checkpoint["Tier"]), {1})
        self.assertEqual(len(checkpoint), 20)

        with patch.object(scraper, "fetch_html", return_value=page_html(count=24)) as fetch:
            scraper.main(args)
        self.assertEqual(fetch.call_count, 1)
        self.assertIn("EFL_Championship", fetch.call_args.args[0])
        self.assertEqual(len(pd.read_csv(scraper.OUTPUT_PATH)), 64)
        self.assertFalse(scraper.CHECKPOINT_PATH.exists())

    def test_narrow_run_preserves_unrelated_checkpoint_groups(self):
        checkpoint = pd.concat([saved_table(2024), saved_table(2025)], ignore_index=True)
        checkpoint.to_csv(scraper.CHECKPOINT_PATH, index=False)
        with patch.object(scraper, "fetch_html") as fetch:
            scraper.main(["--start-year", "2025", "--end-year", "2026", "--tiers", "1"])
        fetch.assert_not_called()
        self.assertEqual(set(pd.read_csv(scraper.OUTPUT_PATH)["Season"]), {scraper.season_str(2025)})
        remaining = pd.read_csv(scraper.CHECKPOINT_PATH)
        self.assertEqual(set(remaining["Season"]), {scraper.season_str(2024)})
        self.assertEqual(len(remaining), 20)

    def test_refresh_replaces_entire_checkpoint_group_and_preserves_other_groups(self):
        old = saved_table(2025, count=21, stadium="Old ground")
        old.loc[20, "Team"] = "Obsolete club"
        checkpoint = pd.concat([old, saved_table(2024)], ignore_index=True)
        checkpoint.to_csv(scraper.CHECKPOINT_PATH, index=False)
        old.to_csv(scraper.OUTPUT_PATH, index=False)
        with patch.object(scraper, "fetch_html", return_value=page_html()) as fetch:
            result = scraper.scrape_pyramid_dim(2025, 2026, tiers=(1,), sleep_s=0, refresh=True)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(len(result), 20)
        self.assertEqual(set(result["Stadium"]), {"New ground"})
        self.assertNotIn("Obsolete club", set(result["Team"]))
        checkpoint = pd.read_csv(scraper.CHECKPOINT_PATH)
        self.assertEqual(len(checkpoint), 40)
        refreshed = checkpoint.loc[checkpoint["Season"] == scraper.season_str(2025)]
        self.assertEqual(set(refreshed["Stadium"]), {"New ground"})
        self.assertEqual(len(refreshed), 20)

    def test_completed_output_is_skipped_unless_refresh_is_requested(self):
        saved_table(2025).to_csv(scraper.OUTPUT_PATH, index=False)
        with patch.object(scraper, "fetch_html") as fetch:
            result = scraper.scrape_pyramid_dim(2025, 2026, tiers=(1,))
        fetch.assert_not_called()
        self.assertEqual(len(result), 20)

    def test_validation_counts_only_requested_range_and_tiers(self):
        data = pd.concat([saved_table(1992), saved_table(2025),
                          saved_table(2025, tier=2, count=24)], ignore_index=True)
        scraper.final_validation_report(data, 2025, 2026, tiers=(1,))
        self.assertIn("requested season-tier keys collected = 1 / 1", self.output.getvalue())
        self.assertIn("saved season-tier keys total = 3", self.output.getvalue())

    def test_cli_range_tiers_and_refresh(self):
        args = scraper.parse_args(["--start-year", "2025", "--end-year", "2026",
                                   "--tiers", "2", "2", "4", "--refresh"])
        self.assertEqual((args.start_year, args.end_year), (2025, 2026))
        self.assertEqual(args.tiers, (2, 4))
        self.assertTrue(args.refresh)
        self.assertEqual(scraper.requested_keys(2025, 2026, args.tiers),
                         {(scraper.season_str(2025), 2), (scraper.season_str(2025), 4)})

    def test_invalid_ranges_are_rejected(self):
        with self.assertRaises(ValueError):
            scraper.scrape_pyramid_dim(2026, 2025)
        with patch("sys.stderr", new=io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                scraper.parse_args(["--start-year", "2026", "--end-year", "2025"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
