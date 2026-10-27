# Stadium and capacity lookup

`stadium_capacity_lookup_template.csv` now contains the user-supplied stadium and
capacity records for 52 historical club-season-tier combinations. Keep this file
as the maintained lookup; despite its original template name, the gold script
reads it on every run.

Rows match `Team`, `Season` and `Tier`. The gold script fills missing `Stadium` and
`Capacity` independently, preserving populated values from the scraped dimension.
It applies the lookup before stadium/capacity comparisons used in baseline rules.
Repeated observations of the same club-season receive the same lookup values.

Keys must be unique and populated. Seasons use `YYYY-YY` (en dashes and full end
years are normalised). Tier must be an integer from 1 to 4, and capacity a whole
number from 500 to 150000. Decimal representations such as `23287.00` are accepted.
Incomplete or invalid rows stop the run before gold outputs are overwritten.

Gold CSV, Parquet and the event comparison report expose `Stadium_Lookup_Applied`,
`Capacity_Lookup_Applied`, `Stadium_SourceURL`, `Capacity_SourceURL` and
`Stadium_Capacity_Lookup_Notes`. These flags identify user-supplied fills. Source
URLs and notes are preserved as provided; most URLs currently refer to homepages
and do not independently establish the capacity for the stated historical season.
Use the specific supporting page when updating a record's evidence.

Run `gold_too_messy_to_melt_script.py` after editing the lookup. This rebuilds gold
CSV/Parquet, the event comparison report and `missing_fields_by_team_season.csv`.
The scraper's dimension and the populated lookup file are separate inputs.
