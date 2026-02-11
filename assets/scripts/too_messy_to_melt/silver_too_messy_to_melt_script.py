# --- Loading libraries
import pandas as pd
import numpy as np
# Make sure you have this installed in your environment: pip install thefuzz
try:
    from thefuzz import process
except ImportError as e:
    raise ImportError("Missing dependency: pip install thefuzz") from e
# --- 1. LOAD MESSY DATA ---
# Path is relative from the 'posts' directory: up two levels (../../) then down.
try:
    df_wide = pd.read_excel("../../files/datasets/too_messy_to_melt/Relegation Attendance Churn_copy.xlsx", sheet_name=0, header=0)
except FileNotFoundError:
    print("Error: '../../files/datasets/too_messy_to_melt/Relegation Attendance Churn_copy.xlsx' not found.")

# --- Polished Cleaning ---
# Find only the attendance columns first
attendance_cols = [c for c in df_wide.columns if "Attendance" in c]

# Now, loop *only* through that smaller list
for col in attendance_cols:
    s = df_wide[col].astype(str).str.replace(",", "", regex=False).str.strip()
    s = s.replace({"COVID": pd.NA, "covid": pd.NA, "nan": pd.NA, "": pd.NA})
    df_wide[col] = pd.to_numeric(s, errors="coerce")

# --- End Fix ---

print("Step 1: Messy data loaded and attendance columns cleaned.")
# --- 2. LOAD HISTORY DATA FOR AUDIT ---
try:
    # Load 'season' as string to be safe
    df_history = pd.read_csv('../../files/datasets/too_messy_to_melt/standings.csv', dtype={'season': str})

    # --- Load patch file and combine ---
    try:
        df_patch = pd.read_csv('../../files/datasets/too_messy_to_melt/standings24_25.csv', dtype={'season': str})
        # Append patch data to history data
        df_history = pd.concat([df_history, df_patch], ignore_index=True)
        print("Step 2a: Loaded and applied 'standings24_25.csv'.")
    except FileNotFoundError:
        print("Step 2a: 'standings24_25.csv' not found. Skipping patch.")
    # --- End new patch logic ---

    print("Step 2b: Loaded historical data for auditing.")

    # Create the cleaned df_positions here for later use
    df_positions = df_history.rename(columns={
        'team_name': 'Team',
        'season': 'Season',
        'position': 'Position_History',
        'played': 'Games_Played_History',
        'wins': 'Wins_History',
        'goals_for': 'Goals_For_History',
        'goals_against': 'Goals_Against_History',
        'points': 'Points_History',
        'tier': 'Tier_History'
    })[['Team', 'Season', 'Position_History', 'Games_Played_History', 'Wins_History',
        'Goals_For_History', 'Goals_Against_History', 'Points_History', 'Tier_History']]

    # Convert new history columns to numeric
    numeric_cols = ['Position_History', 'Games_Played_History', 'Wins_History',
                    'Goals_For_History', 'Goals_Against_History', 'Points_History', 'Tier_History']
    for col in numeric_cols:
        df_positions[col] = pd.to_numeric(df_positions[col], errors='coerce')

    # --- 3. AUDIT TEAM NAMES (NOW WITH AUTO-MAPPING) ---
    # We audit the RAW, DIRTY team names from df_wide
    # --- FIRST, REMOVE COVID TEMPLATE DUPLICATES (ASTERISK ROWS) ---
    # These rows are duplicated template rows where "COVID" appears in the wrong place.
    # We keep the clean rows (no asterisk) and quarantine the bad ones for inspection.

    asterisk_mask = df_wide["Relegated Team"].astype(str).str.contains(r"\*", na=False)

    df_quarantine = df_wide[asterisk_mask].copy()
    df_wide = df_wide[~asterisk_mask].copy()

    if not df_quarantine.empty:
        quarantine_path = "../../files/datasets/too_messy_to_melt/quarantine_covid_template_rows.csv"
        df_quarantine.to_csv(quarantine_path, index=False)
        print(f"Saved quarantined (*) rows to: {quarantine_path}")

    print(f"Step 4.6: Quarantined and removed {len(df_quarantine)} asterisk (*) rows (COVID template duplicates).")

    teams_in_wide_df = set(df_wide['Relegated Team'].astype(str).unique())
    teams_in_history_df = set(df_positions['Team'].astype(str).unique())

    unmatched_teams = teams_in_wide_df.difference(teams_in_history_df)

    # Create an empty map to build automatically
    auto_team_name_map = {}

    if unmatched_teams:
        print("--- AUDIT: TEAM NAME MISMATCHES FOUND ---")
        print("The following teams from your file do not match the history file.")
        print("Attempting to build an automatic mapping...")

        # Loop through each unique unmatched team and find the best match
        for team in sorted(unmatched_teams):
            # process.extractOne returns a tuple: (best_match, score)
            suggestion = process.extractOne(team, teams_in_history_df)

            # Auto-map spaces, asterisks, and high-confidence matches
            if suggestion[1] > 85:
                print(f"  - Auto-mapping: \"{team}\" -> \"{suggestion[0]}\" (Score: {suggestion[1]})")
                auto_team_name_map[team] = suggestion[0]
            else:
                # Don't map low-confidence or junk data
                if team not in ['nan', 'TEAM', 'Relegated Team']:
                    print(
                        f"  - WARNING: \"{team}\" has no confident match. (Best: \"{suggestion[0]}\" at {suggestion[1]}%)")
                    print(f"    -> Please add a fix for \"{team}\" to 'manual_overrides_map' in Step 4.")

        print("---------------------------------------------")
    else:
        print("--- AUDIT: TEAM NAMES OK ---")
        print("All team names in your file match the history file.")

except FileNotFoundError:
    print("Error: '../../files/datasets/too_messy_to_melt/standings.csv' not found. Skipping audit and enrichment.")
    # Create empty dataframes if file not found
    df_positions = pd.DataFrame(columns=['Team', 'Season', 'Position_History', 'Games_Played_History',
                                         'Wins_History', 'Goals_For_History', 'Goals_Against_History',
                                         'Points_History', 'Tier_History'])
    auto_team_name_map = {}

# --- 4. STANDARDIZE TEAM NAMES (THE FIX) ---
# Manual overrides for tricky names the fuzzy match might get wrong
# or for low-confidence matches found in the audit.
manual_overrides_map = {
    "Man Utd": "Manchester United",
    "Man City": "Manchester City",
    "Spurs": "Tottenham Hotspur",
    "QPR": "Queens Park Rangers",
    "Wolves": "Wolverhampton Wanderers",
    "Sheff Utd": "Sheffield United",
    "Sheff Wed": "Sheffield Wednesday",
    "Nott'm Forest": "Nottingham Forest",
    "Notts County": "Nottingham Forest"
    # e.g., if audit warns about "Bradford", add:
    # "Bradford": "Bradford City",
}

# Combine the auto-generated map with the manual overrides
# This is where we combine the two dictionaries.
# The 'manual_overrides_map' will overwrite any conflicting keys from 'auto_team_name_map'.
final_team_map = {**auto_team_name_map, **manual_overrides_map}

map_path = "../../files/datasets/too_messy_to_melt/silver_team_name_map.csv"
pd.DataFrame(
    [{"raw_team": k, "mapped_team": v, "method": ("manual" if k in manual_overrides_map else "auto")} 
     for k, v in final_team_map.items()]
).sort_values(["method","raw_team"]).to_csv(map_path, index=False)
print(f"Saved team name map: {map_path}")

df_wide['Relegated Team'] = df_wide['Relegated Team'].replace(final_team_map)
print("Step 4: Standardized 'Relegated Team' names using auto-mapping and manual overrides.")
# --- 4.5. FILTERING STEP ---
# Now that names are mapped, we can filter out junk rows that didn't get mapped
teams_in_history_df = set(df_positions['Team'].astype(str).unique())
df_wide = df_wide[df_wide['Relegated Team'].isin(teams_in_history_df)]
print("Step 4.5: Filtered out junk rows (e.g., 'nan', 'TEAM').")

# --- 5. CREATE RELEGATION_EVENT_ID ---
# Now uses the CLEANED and FILTERED team names
df_wide['Relegation_Event_ID'] = df_wide['Relegated Team'] + ' ' + df_wide['Season']
print("Step 5: Created 'Relegation_Event_ID'.")

# --- VALIDATION (WIDE): One row per relegation event in df_wide ---
wide_dupes = (
    df_wide.groupby("Relegation_Event_ID")
    .size()
    .reset_index(name="n")
    .query("n > 1")
)

if not wide_dupes.empty:
    p = "../../files/datasets/too_messy_to_melt/quarantine_duplicate_events_in_wide.csv"
    df_wide.merge(wide_dupes[["Relegation_Event_ID"]], on="Relegation_Event_ID").to_csv(p, index=False)
    raise AssertionError(f"Duplicate Relegation_Event_ID rows exist in df_wide. See {p}")

print("Validation passed: df_wide has one row per Relegation_Event_ID.")
# --- Step 6: Tidying data safely ---
print("Step 6: Tidying data using robust pd.concat method...")

def make_slice(df, team_col, season_col, att_col, year_vs):
    df = df.copy()

    if season_col not in df.columns:
        df[season_col] = pd.NA

    if att_col not in df.columns:
        df = df.assign(Attendance_tmp=pd.NA)
    else:
        df = df.rename(columns={att_col: "Attendance_tmp"})

    slice_df = df.rename(columns={team_col: "Team", season_col: "Season_tmp"}).assign(Year_vs_Relegation=year_vs)
    slice_df = slice_df[['Relegation_Event_ID', 'Team', 'Season_tmp', 'Attendance_tmp', 'Year_vs_Relegation']].copy()
    slice_df.columns = ['Relegation_Event_ID', 'Team', 'Season', 'Attendance', 'Year_vs_Relegation']
    return slice_df

# Create slices (Only up to Year 2)
slice_minus1 = make_slice(df_wide, "Relegated Team", "Year Before", "Year Before Att", -1)
slice_0      = make_slice(df_wide, "Relegated Team", "Season", "Attendance", 0)
slice_1      = make_slice(df_wide, "Relegated Team", "Year After", "Attendance year after", 1)
slice_2      = make_slice(df_wide, "Relegated Team", "2 years after", "Attendance 2 years after", 2)

# Concatenate slices safely
df_tidy = pd.concat([slice_minus1, slice_0, slice_1, slice_2], ignore_index=True)

print("Step 6: Data has been 'tidied' successfully!")

# --- 7. STANDARDIZE JOIN KEY (SEASON) ---

# --- HELPER FUNCTION 1 ---
def format_season(season_str):
    if pd.isna(season_str):
        return pd.NA
    season_str = str(season_str).replace("–", "-").replace("\u2013", "-").strip()
    parts = season_str.split("-")
    if len(parts) == 2:
        if len(parts[1]) == 4:
            return f"{parts[0]}-{parts[1][-2:]}"
        return season_str
    return season_str


# --- HELPER FUNCTION 2 ---
def increment_season(season_str):
    if pd.isna(season_str):
        return pd.NA
    try:
        start_year = int(season_str.split('-')[0])
        next_start_year = start_year + 1
        next_end_short = str(next_start_year + 1)[-2:]
        return f"{next_start_year}-{next_end_short}"
    except Exception as e:
        print(f"Error incrementing season '{season_str}': {e}")
        return pd.NA

# Apply the formatting
df_tidy['Season'] = df_tidy['Season'].apply(format_season)
print("Step 7: Standardized 'Season' key to 'YYYY-YY' format (e.g., '1992-93').")


# --- NEW STEP 7.5: CREATE TEMPORARY Y3 ROWS ---
print("Step 7.5: Generating temporary Year 3 rows for outcome calculation...")

# 1. Find all Year 2 rows
df_y2_rows = df_tidy[df_tidy['Year_vs_Relegation'] == 2].copy()

# 2. Transform them into Year 3 rows
df_y2_rows['Year_vs_Relegation'] = 3
df_y2_rows['Attendance'] = pd.NA # Attendance data is not needed
df_y2_rows['Season'] = df_y2_rows['Season'].apply(increment_season)

# 3. Concatenate these helper rows back onto the main tidy dataframe
df_tidy = pd.concat([df_tidy, df_y2_rows], ignore_index=True)
print("Step 7.5: Temporary Year 3 rows created and added.")

# --- 8. ENRICH WITH POSITION DATA ---
if not df_positions.empty:
    # --- Upgrade the history file's 'Season' column ---
    season_numeric = pd.to_numeric(df_positions['Season'], errors='coerce').dropna()
    season_end_year = (season_numeric + 1).astype(int).astype(str).str.zfill(4).str[-2:]
    df_positions.loc[season_numeric.index, 'Season'] = season_numeric.astype(int).astype(str) + '-' + season_end_year
    print("Step 8a: Upgraded history file 'Season' key.")

    # --- MODIFICATION ---
    # We are NO LONGER calculating per-game metrics here.
    # We are ONLY merging the raw values.
    df_positions_merge = df_positions[[
        'Team', 'Season', 'Position_History', 'Tier_History',
        'Games_Played_History', 'Wins_History', 'Goals_For_History', 
        'Goals_Against_History', 'Points_History'
    ]]
    # --- END MODIFICATION ---

    # --- Merge the data ---
    print("Step 8b: Merging tidy data with position data...")
    df_final = pd.merge(
        df_tidy,
        df_positions_merge,  # Use the merge-ready dataframe with raw columns
        on=['Team', 'Season'],
        how='left'
    )
    df_final['Position'] = df_final['Position_History']
    df_final['Tier'] = df_final['Tier_History']
    print("Step 8: Data enriched. 'df_final' created and 'Tier' column added.")

else:
    print("Step 8: Skipping merge as 'standings.csv' was not loaded.")
    df_final = df_tidy.copy() 
    # Add empty columns
    for col in ['Position', 'Tier', 'Games_Played_History', 'Wins_History', 'Goals_For_History', 'Goals_Against_History', 'Points_History']:
        df_final[col] = pd.NA


# --- NEW STEP 8.5: CALCULATE TIER OUTCOME (Promoted, Survived, Relegated) ---
print("Step 8.5: Calculating 'Year_End_Outcome' based on precise timeline...")

# 1. Calculate the Tier Change (Tier_Next_Year - Tier_Current_Year)
df_final = df_final.sort_values(["Relegation_Event_ID", "Year_vs_Relegation"]).copy()
df_final['Tier_Next_Year'] = df_final.groupby('Relegation_Event_ID')['Tier'].shift(-1)
df_final['Tier_Change'] = df_final['Tier_Next_Year'] - df_final['Tier']

# 2. Map the Tier Change to the Outcome Label
def map_tier_change_to_outcome(row):
    """Maps the outcome based on the user's exact timeline definition."""
    
    year_vs_relegation = row['Year_vs_Relegation'] 
    current_tier = row['Tier']
    tier_change = row['Tier_Change']

    # --- 1. Handle Year -1 (Based on CURRENT Tier) ---
    if year_vs_relegation == -1:
        if current_tier == 1:
            return 'Survived'
        if current_tier == 2:
            return 'Promoted'
        return pd.NA

    # --- 2. Handle Year 0 (The Relegation Event) ---
    if year_vs_relegation == 0:
        return 'Relegated'

    # --- 3. Handle Year +1 and +2 (Based on TIER CHANGE) ---
    if year_vs_relegation in [1, 2]:
        if pd.isna(tier_change):
            return pd.NA 
        
        if tier_change == -1:
            return 'Promoted'
        if tier_change == 0:
            return 'Survived'
        if tier_change == 1:
            return 'Relegated'
        
        return pd.NA

    return pd.NA # Catches Y3 row

# Apply the function
df_final['Year_End_Outcome'] = df_final.apply(map_tier_change_to_outcome, axis=1)
print("Step 8.5: 'Year_End_Outcome' column successfully created.")

# --- NEW STEP 8.6: BLANK OUT FUTURE YEARS (data horizon) ---
print("Step 8.6: Blanking out future rows beyond final known season...")

FINAL_SEASON_START = 2024  # last known season is 2024-25

def season_start_year(season):
    if pd.isna(season):
        return pd.NA
    try:
        return int(str(season).split("-")[0])
    except Exception:
        return pd.NA

# make sure within-event ordering is correct for shift logic + outcome calc
df_final = df_final.sort_values(["Relegation_Event_ID", "Year_vs_Relegation"]).copy()

# event baseline start year = start year of the Year 0 season
event_base = (
    df_final.loc[df_final["Year_vs_Relegation"] == 0, ["Relegation_Event_ID", "Season"]]
      .assign(Event_Season_Start=lambda d: d["Season"].apply(season_start_year))
)

df_final = df_final.merge(event_base[["Relegation_Event_ID", "Event_Season_Start"]],
                          on="Relegation_Event_ID", how="left")

# implied season start for each relative year
df_final["Implied_Season_Start"] = df_final["Event_Season_Start"] + df_final["Year_vs_Relegation"]

# anything whose implied season is after 2024-25 is future (Y+1 for 2024-25 relegations, Y+2 for 2023-24 relegations, etc.)
mask_future = (df_final["Year_vs_Relegation"] > 0) & (df_final["Implied_Season_Start"] > FINAL_SEASON_START)

cols_to_null = [
    "Attendance",
    "Tier",
    "Position",
    "Tier_Next_Year",
    "Tier_Change",
    "Year_End_Outcome",
    "Games_Played_History",
    "Wins_History",
    "Goals_For_History",
    "Goals_Against_History",
    "Points_History",
]

for c in cols_to_null:
    if c in df_final.columns:
        df_final.loc[mask_future, c] = pd.NA

if "Data_Availability_Flag" not in df_final.columns:
    df_final["Data_Availability_Flag"] = "observed"
df_final.loc[mask_future, "Data_Availability_Flag"] = "future_not_available"

print(f"Step 8.6 complete: blanked {int(mask_future.sum())} future rows.")

df_final = df_final.drop(columns=["Event_Season_Start","Implied_Season_Start"], errors="ignore")

# --- 9. FINAL POLISH AND SAVE ---
print("Step 9: Adding Primary Key and polishing final data...")

# Create the unique Observation ID (Primary Key)
# This uniquely identifies each row (Event + specific Year)
df_final['Observation_ID'] = df_final['Relegation_Event_ID'] + "_" + df_final['Year_vs_Relegation'].astype(str)

# Update final_columns list to include Observation_ID at the start
final_columns = [
    'Observation_ID', 'Relegation_Event_ID', 'Team', 'Season', 'Tier',
    'Position', 'Attendance', 'Year_vs_Relegation', 'Year_End_Outcome',
    'Games_Played_History', 'Wins_History', 'Goals_For_History', 
    'Goals_Against_History', 'Points_History'
]

# Ensure final columns exist
for col in final_columns:
    if col not in df_final.columns:
        df_final[col] = pd.NA

# Cast numeric columns to Int64
for col in ['Attendance', 'Position', 'Tier', 'Games_Played_History', 'Wins_History', 'Goals_For_History', 'Goals_Against_History', 'Points_History']:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').astype('Int64')

# DROP THE HELPER ROW (Year 3 was only for calculations)
df_final = df_final[df_final['Year_vs_Relegation'] != 3].copy()

# Sort and select columns
df_final = df_final[final_columns].sort_values(by=['Relegation_Event_ID', 'Year_vs_Relegation'])

# --- Step 10: VALIDATIONS ---
# 1: GRAIN VALIDATION (Now testing your new Primary Key)
dup = df_final[df_final.duplicated("Observation_ID", keep=False)]

if not dup.empty:
    bad_path = "../../files/datasets/too_messy_to_melt/quarantine_duplicates_grain.csv"
    dup.to_csv(bad_path, index=False)
    raise AssertionError(
        f"Primary Key Violated: Duplicate Observation_ID rows found. See {bad_path}"
    )

print("Validation passed: Observation_ID is unique (Primary Key confirmed).")

# --- VALIDATION 2: Panel shape (rows exist for -1,0,1,2) ---
expected_years = {-1, 0, 1, 2}

panel_check = (
    df_final.groupby("Relegation_Event_ID")["Year_vs_Relegation"]
    .apply(lambda s: set(map(int, s.dropna().unique())))
    .reset_index(name="years_present")
)

bad_panel = panel_check[panel_check["years_present"] != expected_years]

if not bad_panel.empty:
    bad_panel_path = "../../files/datasets/too_messy_to_melt/quarantine_panel_shape.csv"
    bad_panel.to_csv(bad_panel_path, index=False)
    raise AssertionError(
        f"Some events do not have exactly years {expected_years}. "
        f"See {bad_panel_path}"
    )

print("Validation passed: every event has rows for years -1,0,1,2.")

# --- VALIDATION 3: SANITY RANGES ---
# Attendance: allow NA, otherwise should be positive and not insane
bad_att = df_final[df_final["Attendance"].notna() & ((df_final["Attendance"] <= 0) | (df_final["Attendance"] > 120000))]
if not bad_att.empty:
    p = "../../files/datasets/too_messy_to_melt/quarantine_bad_attendance.csv"
    bad_att.to_csv(p, index=False)
    raise AssertionError(f"Attendance sanity check failed. See {p}")

# Tier: allow NA, otherwise 1..4 (adjust if needed)
bad_tier = df_final[df_final["Tier"].notna() & ~df_final["Tier"].isin([1,2,3,4])]
if not bad_tier.empty:
    p = "../../files/datasets/too_messy_to_melt/quarantine_bad_tier.csv"
    bad_tier.to_csv(p, index=False)
    raise AssertionError(f"Tier sanity check failed. See {p}")

print("Validation passed: numeric sanity checks look OK.")

# --- VALIDATION 4: ENRICHMENT COVERAGE ---
merge_rate = df_final["Tier"].notna().mean()
print(f"Enrichment coverage: {merge_rate:.1%} of rows have Tier populated.")

if merge_rate < 0.95:
    # Save rows where merge failed
    miss = df_final[df_final["Tier"].isna()][["Relegation_Event_ID","Team","Season","Year_vs_Relegation"]].drop_duplicates()
    p = "../../files/datasets/too_messy_to_melt/quarantine_merge_misses.csv"
    miss.to_csv(p, index=False)
    raise AssertionError(f"Tier merge coverage too low (<95%). See {p}")

# Keep only the final columns and sort
df_final = df_final[final_columns].sort_values(by=['Relegation_Event_ID', 'Year_vs_Relegation'])

dupes = (
    df_final.groupby(["Relegation_Event_ID", "Year_vs_Relegation"])
    .size()
    .reset_index(name="n")
    .query("n > 1")
)

print(dupes.sort_values("n", ascending=False).head(50))

# Save the final data to a new CSV in the 'datasets' folder
silver_csv_path = "../../files/datasets/too_messy_to_melt/silver_relegation_attendance.csv"
df_final.to_csv(silver_csv_path, index=False)
print(f"Step 9: Success! Final CSV table saved to '{silver_csv_path}'")

silver_parquet_path = "../../files/datasets/too_messy_to_melt/silver_relegation_attendance.parquet"
df_final.to_parquet(silver_parquet_path, index=False)   
print(f"Step 9: Success! Final Parquet table saved to '{silver_parquet_path}'")

# --- TIDYING COMPLETE: END OF SILVER PHASE ---

run_log_path = "../../files/datasets/too_messy_to_melt/silver_run_log.csv"
pd.DataFrame([{
    "rows": len(df_final),
    "events": df_final["Relegation_Event_ID"].nunique(),
    "generated_at": pd.Timestamp.utcnow().isoformat(),
    "tier_merge_coverage": float(df_final["Tier"].notna().mean()),
}]).to_csv(run_log_path, index=False)
print(f"Saved silver run log: {run_log_path}")
