# Club city lookup

`club_city_lookup.csv` assigns one consistent home city or town to each team name in
`standings.csv`, `standings24_25.csv`, `gold_dim_stadiums_pyramid.csv` and
`silver_relegation_attendance.parquet`. It contains 171 team-name keys, including
historical names and spelling variants. Multiple keys can refer to the same club.

`Team` is the join key. `Club_City` is the club's home location under that name,
independent of where its stadium was in a particular season. London boroughs use
`London`; district labels such as `Birmingham (Bordesley)` use their broader city.
Towns are included even though the column is named `Club_City`.

For example, Coventry City consistently maps to Coventry, Bolton Wanderers to
Bolton and Wimbledon to London. Milton Keynes Dons has its own Milton Keynes key.
The season-specific stadium `City` is retained separately. In the gold outputs,
`GeoPlace` uses `Club_City, United Kingdom` for every observation, including those
without a stadium record. This supports city-level mapping for English and Welsh
clubs without requiring the exact stadium location.
`Coventry City1` is retained as a source-name variant and maps to Coventry.

Most mappings use the existing stadium records, with districts standardised and
temporary grounds excluded from the club's home location. Records without a city
include Chester/Chester City and Darlington; their home towns are supported by
[Chester's history](https://chesterfc.com/our-history/) and
[Darlington's history](https://darlingtonfc.co.uk/history/brief-history/).
[Grimsby Town describes its base as Cleethorpes](https://gtfc.co.uk/about-us/), so
its mapping uses Cleethorpes. The historical
[Rushden & Diamonds club](https://en.wikipedia.org/wiki/Rushden_%26_Diamonds_F.C.)
maps to Irthlingborough. Merthyr Town maps to Merthyr Tydfil, supported by the
[club's description of its home](https://www.merthyrtownfc.co.uk/club).

The gold script validates unique, populated team keys and requires a mapping for
every team in the silver panel. Add a row here when introducing a new team, then
rerun `gold_too_messy_to_melt_script.py`; it exports `Club_City` to both CSV and
Parquet and to the stadium event comparison report.
