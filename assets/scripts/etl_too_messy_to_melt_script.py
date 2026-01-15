# --- Loading libraries
import pandas as pd
import numpy as np
# Make sure you have this installed in your environment: pip install thefuzz
from thefuzz import process
# --- 1. LOAD MESSY DATA ---
# Path is relative from the 'posts' directory: up two levels (../../) then down.
try:
    df_wide = pd.read_excel("../../assets/files/datasets/Relegation Attendance Churn_copy.xlsx", sheet_name=0, header=0)
except FileNotFoundError:
    print("Error: '../../assets/files/datasets/Relegation Attendance Churn_copy.xlsx' not found. Using example data.")
    # Example data in case the file isn't found
    df_wide = pd.DataFrame({
        'Season': ['1992-93'], 'Relegated Team': ['Nottingham Forest'], 'Position': ['Last'],
        'Year Before': ['1991-1992'], 'Year Before Div': ['PL'], 'Year Before Att': '23,721',
        'Attendance': '21,910', 'Year After': ['1993-94'], 'Year After Division': ['Championship'],
        'Attendance year after': '23,051', '2 years after': ['1994-95'], '2 Years After Div': ['PL'],
        'Attendance 2 years after': '23,633'
    })

# --- Polished Cleaning ---
# Find only the attendance columns first
attendance_cols = [c for c in df_wide.columns if "Attendance" in c]

# Now, loop *only* through that smaller list
for col in attendance_cols:
    # Convert *just this column* to string before cleaning
    df_wide[col] = df_wide[col].astype(str).str.replace(',', '').replace('COVID', pd.NA).replace('nan', pd.NA)
    df_wide[col] = pd.to_numeric(df_wide[col], errors='coerce')
# --- End Fix ---

print("Step 1: Messy data loaded and attendance columns cleaned.")
# --- 2. LOAD HISTORY DATA FOR AUDIT ---
try:
    # Load 'season' as string to be safe
    df_history = pd.read_csv('../../assets/files/datasets/standings.csv', dtype={'season': str})

    # --- Load patch file and combine ---
    try:
        df_patch = pd.read_csv('../../assets/files/datasets/standings24_25.csv', dtype={'season': str})
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
    print("Error: '../../assets/files/datasets/standings.csv' not found. Skipping audit and enrichment.")
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
# --- Step 6: Tidying data safely ---
print("Step 6: Tidying data using robust pd.concat method...")

def make_slice(df, team_col, season_col, att_col, year_vs):
    # --- Check if att_col exists, otherwise use pd.NA ---
    # This makes the function robust for the missing Y3 attendance
    if att_col not in df.columns:
        # Create a temporary column of NAs if the attendance col doesn't exist
        df = df.assign(Attendance_tmp=pd.NA) 
    else:
        # If the col *does* exist, rename it
        df = df.rename(columns={att_col: "Attendance_tmp"})
        
    slice_df = df.rename(columns={
        team_col: "Team",
        season_col: "Season_tmp"
    }).assign(Year_vs_Relegation=year_vs)

    # Select and rename final columns
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
    """Converts '1991-1992' to '1991-92' and leaves '1992-93' as is."""
    if pd.isna(season_str):
        return pd.NA
    parts = str(season_str).split('-')
    if len(parts) == 2:
        if len(parts[1]) == 4:  # Format is '1991-1992'
            return f"{parts[0]}-{parts[1][-2:]}"
        else:  # Format is '1992-93'
            return season_str
    return season_str  # Return as-is if not in expected format

# --- HELPER FUNCTION 2 ---
def increment_season(season_str):
    """Converts a season string like '1995-96' to '1996-97'."""
    if pd.isna(season_str):
        return pd.NA
    try:
        start_year = int(season_str.split('-')[0])
        next_start_year = start_year + 1
        
        # Handle the '1999-00' case
        if next_start_year == 1999:
            return "1999-00"
        
        next_end_year_short = str(next_start_year + 1)[-2:] # e.g., 97
        return f"{next_start_year}-{next_end_year_short}"
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


# --- 9. FINAL POLISH AND SAVE ---
print("Step 9: Polishing final data...")

# --- MODIFICATION: Added all _History columns ---
final_columns = [
    'Relegation_Event_ID', 'Team', 'Season', 'Tier',
    'Position', 'Attendance', 'Year_vs_Relegation', 'Year_End_Outcome',
    'Games_Played_History', 'Wins_History', 'Goals_For_History', 
    'Goals_Against_History', 'Points_History'
]
# --- END MODIFICATION ---

# Ensure final columns exist before slicing
for col in final_columns:
    if col not in df_final.columns:
        df_final[col] = pd.NA

# --- MODIFICATION: Cast all numeric columns to Int64 ---
for col in ['Attendance', 'Position', 'Tier', 'Games_Played_History', 'Wins_History', 'Goals_For_History', 'Goals_Against_History', 'Points_History']:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').astype('Int64')
# --- END MODIFICATION ---

# --- DROP THE HELPER ROW ---
df_final = df_final[df_final['Year_vs_Relegation'] != 3].copy()

# Keep only the final columns and sort
df_final = df_final[final_columns].sort_values(by=['Relegation_Event_ID', 'Year_vs_Relegation'])

# Save the final, perfect data to a new CSV in the 'datasets' folder
output_path = "../../assets/files/datasets/perfect_tidy_data.csv"
df_final.to_csv(output_path, index=False)
import os
print(f"Step 9: Success! Final table saved to '{output_path}'")