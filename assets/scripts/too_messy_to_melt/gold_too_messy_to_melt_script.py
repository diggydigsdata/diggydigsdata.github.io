# --- GOLD PHASE: analysis-ready dataset (COVID-safe baseline substitution)
# Drop this into your existing GOLD script starting right after:
#   df_gold = pd.read_parquet(silver_parquet_path)
#
# Key change vs your current GOLD:
# - No COVID attendance imputation.
# - Instead, for events whose relegation season (Year_vs=0) is 2020-21, we *substitute the baseline*
#   from Year_vs=-1 (2019-20) IF the club stayed in the same tier AND stadium/capacity are comparable.
# - Everything is explicitly flagged so the dashboard can exclude substituted baselines by default.

import pandas as pd
import numpy as np
from pathlib import Path

# --- paths (same pattern as yours) ---
ASSETS_DIR   = Path(__file__).resolve().parents[2]
DATASETS_DIR = ASSETS_DIR / "files" / "datasets" / "too_messy_to_melt"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

print("--- PREPARING DATA FOR ANALYSIS (GOLD) ---")
silver_parquet_path = DATASETS_DIR / "silver_relegation_attendance.parquet"
df_gold = pd.read_parquet(silver_parquet_path).copy()

# -----------------------------
# 0) (Optional) Stadium join (unchanged from your script, but keep it BEFORE COVID baseline logic)
# -----------------------------
stadium_dim_path = DATASETS_DIR / "gold_dim_stadiums_pyramid.csv"

def norm_team(s):
    return (
        s.astype(str)
         .str.replace(r"\s+", " ", regex=True)
         .str.strip()
    )

def norm_season(s):
    return (
        s.astype(str)
         .str.replace("\u2013", "-", regex=False)
         .str.replace("–", "-", regex=False)
         .str.strip()
    )

def norm_tier(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64")

df_gold["Team"] = norm_team(df_gold["Team"])
df_gold["Season"] = norm_season(df_gold["Season"])
df_gold["Tier"] = norm_tier(df_gold["Tier"])

dup = df_gold.duplicated(["Observation_ID"]).sum()
if dup:
    raise AssertionError(f"Fact grain broken in silver: {dup} duplicate Observation_ID rows.")

if stadium_dim_path.exists():
    df_stad = pd.read_csv(stadium_dim_path)

    df_stad["Team"] = norm_team(df_stad["Team"])
    df_stad["Season"] = norm_season(df_stad["Season"])
    df_stad["Tier"] = norm_tier(df_stad["Tier"])

    keep_cols = [c for c in ["Team","Season","Tier","Stadium","Capacity","City","GeoPlace","SourceURL"] if c in df_stad.columns]
    df_stad = df_stad[keep_cols].copy()

    if "Capacity" in df_stad.columns:
        df_stad["Capacity"] = pd.to_numeric(df_stad["Capacity"], errors="coerce").astype("Int64")

    df_stad["_score"] = (
        df_stad.get("Stadium", pd.Series([pd.NA]*len(df_stad))).notna().astype(int) +
        df_stad.get("Capacity", pd.Series([pd.NA]*len(df_stad))).notna().astype(int)
    )
    df_stad = (
        df_stad.sort_values(["Team","Season","Tier","_score"], ascending=[True,True,True,False])
              .drop_duplicates(["Team","Season","Tier"], keep="first")
              .drop(columns=["_score"])
    )

    JOIN_KEYS = ["Team","Season","Tier"]
    df_gold = df_gold.merge(df_stad, on=JOIN_KEYS, how="left", validate="m:1")

    cov_stadium = df_gold["Stadium"].notna().mean() if "Stadium" in df_gold.columns else 0
    cov_capacity = df_gold["Capacity"].notna().mean() if "Capacity" in df_gold.columns else 0
    print(f"[JOIN] Stadium coverage={cov_stadium:.1%} | Capacity coverage={cov_capacity:.1%}")

else:
    print(f"[JOIN] Stadium dim not found at {stadium_dim_path}. Skipping stadium enrichment.")

# -----------------------------
# 1) Flag COVID season rows (row-level)
# -----------------------------
df_gold["Is_Covid_Affected"] = df_gold["Season"].eq("2020-21")

# -----------------------------
# 2) Build event-level baselines (default: Year 0 attendance)
# -----------------------------
y0 = (
    df_gold.loc[df_gold["Year_vs_Relegation"] == 0,
                ["Relegation_Event_ID","Season","Attendance","Tier","Stadium","Capacity"]]
    .rename(columns={
        "Season": "Event_Season",
        "Attendance": "Attendance_Y0",
        "Tier": "Tier_Y0",
        "Stadium": "Stadium_Y0",
        "Capacity": "Capacity_Y0",
    })
)

y_1 = (
    df_gold.loc[df_gold["Year_vs_Relegation"] == -1,
                ["Relegation_Event_ID","Season","Attendance","Tier","Stadium","Capacity"]]
    .rename(columns={
        "Season": "Season_Ym1",
        "Attendance": "Attendance_Ym1",
        "Tier": "Tier_Ym1",
        "Stadium": "Stadium_Ym1",
        "Capacity": "Capacity_Ym1",
    })
)

event_base = y0.merge(y_1, on="Relegation_Event_ID", how="left")

event_base["Baseline_Year_Used"] = 0
event_base["Baseline_Attendance"] = event_base["Attendance_Y0"]
event_base["Baseline_Substitution_Reason"] = pd.NA
event_base["Covid_Baseline_Not_Comparable"] = False
event_base["Covid_Baseline_Review_Flag"] = False

# -----------------------------
# 3) COVID baseline substitution rule
# If relegation season (Y0) is 2020-21: use Y-1 as baseline IF comparable
# Comparable = same tier AND stadium/capacity match (treat NA==NA as match)
# If Stadium+Capacity are NA in both donor+target, still allow but flag for review.
# -----------------------------
is_covid_event = event_base["Event_Season"].eq("2020-21")

tier_match = event_base["Tier_Y0"].eq(event_base["Tier_Ym1"])

def na_equal(a, b):
    return (a.eq(b)) | (a.isna() & b.isna())

stad_match = na_equal(event_base["Stadium_Y0"].astype("string"), event_base["Stadium_Ym1"].astype("string"))
cap_match  = na_equal(event_base["Capacity_Y0"], event_base["Capacity_Ym1"])

comparable = is_covid_event & tier_match & stad_match & cap_match

# review flag if we’re matching on “both NA” for stadium/capacity (allowed, but visible)
stad_both_na = is_covid_event & event_base["Stadium_Y0"].isna() & event_base["Stadium_Ym1"].isna()
cap_both_na  = is_covid_event & event_base["Capacity_Y0"].isna() & event_base["Capacity_Ym1"].isna()
needs_review = comparable & (stad_both_na | cap_both_na)

# apply substitution
event_base.loc[comparable, "Baseline_Year_Used"] = -1
event_base.loc[comparable, "Baseline_Attendance"] = event_base.loc[comparable, "Attendance_Ym1"]
event_base.loc[comparable, "Baseline_Substitution_Reason"] = "covid_y0_no_fans_use_y-1_if_comparable"
event_base.loc[needs_review, "Covid_Baseline_Review_Flag"] = True

# if it’s a covid relegation event but not comparable, we keep baseline as Y0 (likely NA) and flag that it couldn't be substituted
event_base.loc[is_covid_event & ~comparable, "Covid_Baseline_Not_Comparable"] = True
event_base.loc[is_covid_event & ~comparable, "Baseline_Substitution_Reason"] = "covid_y0_no_fans_no_safe_y-1_baseline"

# merge event baseline back onto all rows
df_plot = df_gold.merge(
    event_base[["Relegation_Event_ID","Event_Season","Baseline_Attendance","Baseline_Year_Used",
               "Baseline_Substitution_Reason","Covid_Baseline_Not_Comparable","Covid_Baseline_Review_Flag"]],
    on="Relegation_Event_ID",
    how="left"
)

# -----------------------------
# 4) Compute % change vs baseline (baseline may be Y0 or Y-1 depending on flags)
# -----------------------------
df_plot["Pct_Change_vs_Baseline"] = (
    (df_plot["Attendance"] - df_plot["Baseline_Attendance"]) / df_plot["Baseline_Attendance"]
)
df_plot["Pct_Change_vs_Baseline_Display"] = df_plot["Pct_Change_vs_Baseline"] * 100

# Analysis column: still exclude Y<=0 to isolate post-relegation churn.
# IMPORTANT: we do NOT blank just because it's COVID; baseline substitution handles COVID relegations.
df_plot["Pct_Change_Analysis"] = df_plot["Pct_Change_vs_Baseline_Display"]
df_plot.loc[df_plot["Year_vs_Relegation"] <= 0, "Pct_Change_Analysis"] = np.nan

# -----------------------------
# 5) Outcome_Group (event-level) vs Year_End_Outcome (row-level)
# Outcome_Group = the Year+1 outcome for the event (same label repeated on all 4 rows for grouping in charts)
# Year_End_Outcome remains per-row (already in silver)
# -----------------------------
df_y1_outcome = (
    df_plot.loc[df_plot["Year_vs_Relegation"] == 1, ["Relegation_Event_ID","Year_End_Outcome"]]
    .rename(columns={"Year_End_Outcome": "Outcome_Group"})
)

df_plot = df_plot.merge(df_y1_outcome, on="Relegation_Event_ID", how="left")

# (Optional) if you want Outcome_Group to be present only once per event, you’d keep it separate.
# For BI, repeating it across the panel is usually exactly what you want.

# -----------------------------
# 6) Per-game metrics (your existing logic)
# -----------------------------
df_plot["Goals_For_Per_Game"] = df_plot["Goals_For_History"] / df_plot["Games_Played_History"]
df_plot["Points_Per_Game"] = df_plot["Points_History"] / df_plot["Games_Played_History"]

# -----------------------------
# 7) Structural anomalies + plot labels (your existing logic)
# -----------------------------
anomaly_events = [
    "Middlesbrough 1992-93",
    "Sunderland 1996-97",
    "Leicester City 2001-02",
    "Bolton Wanderers 1995-96",
]
df_plot["Is_Structural_Anomaly"] = df_plot["Relegation_Event_ID"].isin(anomaly_events)

label_map = {
    "Promoted":  "Promoted (Back in PL)",
    "Survived":  "Survived (Still in Champ)",
    "Relegated": "Relegated (Down to L1)",
}
df_plot["Plot_Group_Label"] = df_plot["Outcome_Group"].map(label_map)

# -----------------------------
# 8) Recommended dashboard-default filters (implemented as flags, not hard exclusions)
# -----------------------------
# Use these in Power BI defaults:
# - Exclude substituted baselines by default: Baseline_Year_Used == 0
# - Or: Baseline_Substitution_Reason is blank
df_plot["Is_Baseline_Substituted"] = df_plot["Baseline_Year_Used"].eq(-1)

# -----------------------------
# 9) Quick notebook exploration helpers (prints only)
# -----------------------------
print("\n--- QUICK CHECKS ---")
print("Rows:", len(df_plot), "| Events:", df_plot["Relegation_Event_ID"].nunique())
print("COVID rows (Season==2020-21):", int(df_plot["Is_Covid_Affected"].sum()))
print("Events with substituted baseline:", int(df_plot.loc[df_plot["Is_Baseline_Substituted"], "Relegation_Event_ID"].nunique()))

# show which events got a substituted baseline
subbed = (
    df_plot.loc[df_plot["Is_Baseline_Substituted"], ["Relegation_Event_ID","Event_Season","Baseline_Year_Used","Baseline_Substitution_Reason","Covid_Baseline_Review_Flag"]]
    .drop_duplicates()
    .sort_values(["Event_Season","Relegation_Event_ID"])
)
print("\nSubstituted baseline events (preview):")
print(subbed.head(20).to_string(index=False))

# sanity: baseline attendance should be non-null for substituted events (otherwise you’re substituting to NA)
bad_sub = df_plot.loc[df_plot["Is_Baseline_Substituted"] & df_plot["Baseline_Attendance"].isna(),
                      ["Relegation_Event_ID","Team","Season","Year_vs_Relegation","Baseline_Attendance"]].drop_duplicates()
if not bad_sub.empty:
    print("\nWARNING: Some substituted baselines are NA (check Year -1 attendance):")
    print(bad_sub.head(20).to_string(index=False))

# -----------------------------
# 10) Save GOLD
# -----------------------------
gold_path = DATASETS_DIR / "gold_relegation_attendance.parquet"
df_plot.to_parquet(gold_path, index=False)
print(f"\nSaved GOLD parquet: {gold_path}")
