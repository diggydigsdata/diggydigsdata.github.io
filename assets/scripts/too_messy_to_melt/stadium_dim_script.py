import pandas as pd
import numpy as np
import re
import time
from io import StringIO
import requests
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------
EN_DASH = "\u2013"
START_YEAR = 1992
END_YEAR = 2025  # scrapes 1992–93 through 2024–25 (exclusive end)
COUNTRY = "England"

LEAGUE_MAP = {
    1: [(1992, 2026, "Premier_League")],
    2: [(1992, 2004, "Football_League_First_Division"),
        (2004, 2016, "Football_League_Championship"),
        (2016, 2026, "EFL_Championship")],
    3: [(1992, 2004, "Football_League_Second_Division"),
        (2004, 2016, "Football_League_One"),
        (2016, 2026, "EFL_League_One")],
    4: [(1992, 2004, "Football_League_Third_Division"),
        (2004, 2016, "Football_League_Two"),
        (2016, 2026, "EFL_League_Two")]
}

USER_AGENT = "Mozilla/5.0 (compatible; stadium-scraper/1.0; +https://example.com) pandas-read-html"
REQUEST_TIMEOUT = 30
BASE_SLEEP = 1.2

BASE_DIR = Path(__file__).resolve().parents[2]   # .../assets
DATASETS_DIR = BASE_DIR / "files" / "datasets" / "too_messy_to_melt"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = DATASETS_DIR / "gold_dim_stadiums_pyramid_checkpoint.csv"
OUTPUT_PATH     = DATASETS_DIR / "gold_dim_stadiums_pyramid.csv"
ISSUES_PATH     = DATASETS_DIR / "gold_dim_stadiums_pyramid_issues.csv"

EXPECTED_ROWS_BY_TIER = {
    1: (18, 24),
    2: (18, 30),
    3: (18, 30),
    4: (18, 30),
}
MAX_NULL_RATE = {
    "Team": 0.05,
    "Stadium": 0.10,
    "Capacity": 0.60,
    "GeoPlace": 0.10,
}

# -----------------------------
# BASIC HELPERS
# -----------------------------
def season_str(year: int) -> str:
    if year % 100 == 99:
        return f"{year}{EN_DASH}{year + 1}"
    next_yr = str(year + 1)[2:]
    return f"{year}{EN_DASH}{next_yr}"


def clean_value(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = re.sub(r"\[.*?\]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def clean_capacity(val):
    s = clean_value(val)
    if pd.isna(s):
        return np.nan
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else np.nan


def extract_city(loc):
    loc = clean_value(loc)
    if pd.isna(loc) or loc == "":
        return np.nan
    return loc.split(",")[0].strip()


def build_geoplace(stadium, city, country=COUNTRY):
    stadium = clean_value(stadium)
    city = clean_value(city)
    if (pd.isna(stadium) or stadium == "") and (pd.isna(city) or city == ""):
        return np.nan
    parts = [p for p in [stadium, city, country] if p and not pd.isna(p)]
    return ", ".join(parts)

# -----------------------------
# WIKIPEDIA TABLE HELPERS
# -----------------------------
def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        cols = [
            " ".join([str(x) for x in tup if x and str(x).lower() != "nan"]).strip()
            for tup in df.columns
        ]
    else:
        cols = [str(c).strip() for c in df.columns]

    # Dedupe column names
    seen = {}
    new_cols = []
    for c in cols:
        if c not in seen:
            seen[c] = 0
            new_cols.append(c)
        else:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
    df.columns = new_cols
    return df


def choose_base_slug(tier: int, year: int) -> str | None:
    for start, end, slug in LEAGUE_MAP[tier]:
        if start <= year < end:
            return slug
    return None


def candidate_slugs(tier: int, year: int) -> list[str]:
    base = choose_base_slug(tier, year)
    if not base:
        return []
    cands = [base]
    if tier == 1:
        cands = ["FA_Premier_League", "Premier_League"] + cands

    # safety net
    if base == "Football_League_One":
        cands = ["Football_League_One", "Football_League_League_One"] + cands
    if base == "Football_League_Two":
        cands = ["Football_League_Two", "Football_League_League_Two"] + cands

    seen, out = set(), []
    for s in cands:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return out


def candidate_urls(season: str, tier: int, year: int) -> list[str]:
    """
    Try normal per-division pages first, then for 1992–2004 (tiers 2–4),
    also try the container season page: {season}_Football_League
    """
    urls = []
    for slug in candidate_slugs(tier, year):
        urls.append(f"https://en.wikipedia.org/wiki/{season}_{slug}")

    # container page fallback for old Football League seasons
    if 1992 <= year < 2004 and tier in (2, 3, 4):
        urls.append(f"https://en.wikipedia.org/wiki/{season}_Football_League")

    # de-dup
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out


def fetch_html(url: str, retries: int = 3, backoff: float = 1.8) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            time.sleep((backoff ** attempt) + np.random.uniform(0, 0.4))
    raise last_err


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = flatten_columns(df)

    rename_map = {}
    for col in df.columns:
        c_low = str(col).lower()
        if any(x in c_low for x in ["team", "club"]):
            rename_map[col] = "Team"
        if any(x in c_low for x in ["stadium", "ground"]):
            rename_map[col] = "Stadium"
        if any(x in c_low for x in ["location", "town", "city", "borough", "county"]):
            rename_map[col] = "Location"
        if "capacity" in c_low:
            rename_map[col] = "Capacity_raw"

    out = df.rename(columns=rename_map)
    return out


def looks_like_stadia_table(df: pd.DataFrame) -> bool:
    cols = [c.lower() for c in df.columns]

    has_team = ("Team" in df.columns) or ("team" in cols) or ("club" in cols)
    has_stadium = ("Stadium" in df.columns) or any(("stadium" in c or "ground" in c) for c in cols)

    has_capacity = ("Capacity_raw" in df.columns) or any("capacity" in c for c in cols)
    has_location = ("Location" in df.columns) or any(("location" in c or "town" in c or "city" in c) for c in cols)

    n = len(df)
    row_ok = 14 <= n <= 30

    return bool(has_team and has_stadium and (has_capacity or has_location) and row_ok)


def extract_stadia_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    candidates = []
    for t in tables:
        tt = normalize_columns(t)
        if not looks_like_stadia_table(tt):
            continue

        score = 0
        score += 2 if "Team" in tt.columns else 0
        score += 2 if "Stadium" in tt.columns else 0
        score += 1 if "Location" in tt.columns else 0
        score += 2 if "Capacity_raw" in tt.columns else 0

        size_penalty = abs(len(tt) - 22)
        candidates.append((score, -size_penalty, tt))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][2]

# -----------------------------
# INCREMENTAL SKIP LOGIC
# -----------------------------
def load_existing_output() -> pd.DataFrame:
    if OUTPUT_PATH.exists():
        try:
            df = pd.read_csv(OUTPUT_PATH)
            if "Season" in df.columns and "Tier" in df.columns:
                return df
        except Exception:
            pass
    return pd.DataFrame()


def build_done_keys(existing_df: pd.DataFrame) -> set[tuple[str, int]]:
    """
    Mark (Season, Tier) as 'done' if the output already contains a plausible table
    for that season-tier (based on expected rowcount bounds).
    This allows missing Stadium/Capacity cells and supports later imputation.
    """
    if existing_df.empty:
        return set()

    required = {"Season", "Tier", "Team"}
    if not required.issubset(existing_df.columns):
        return set()

    done = set()

    # Ensure tier is numeric-ish for grouping reliability
    df = existing_df.copy()
    df["Tier"] = pd.to_numeric(df["Tier"], errors="coerce")

    for (season, tier), g in df.groupby(["Season", "Tier"], dropna=False):
        if pd.isna(season) or pd.isna(tier):
            continue
        tier = int(tier)

        lo, hi = EXPECTED_ROWS_BY_TIER.get(tier, (14, 30))
        if lo <= len(g) <= hi:
            done.add((season, tier))

    return done

# -----------------------------
# VALIDATION / ERROR LOGGING
# -----------------------------
def validate_season_tier(df: pd.DataFrame, season: str, tier: int, source_url: str) -> list[dict]:
    issues = []
    if df is None or df.empty:
        issues.append({"Season": season, "Tier": tier, "SourceURL": source_url,
                       "IssueType": "EMPTY_RESULT", "Details": "No rows extracted."})
        return issues

    lo, hi = EXPECTED_ROWS_BY_TIER.get(tier, (14, 30))
    n = len(df)
    if not (lo <= n <= hi):
        issues.append({"Season": season, "Tier": tier, "SourceURL": source_url,
                       "IssueType": "ROWCOUNT_OUT_OF_RANGE",
                       "Details": f"Rows={n} expected_range=[{lo},{hi}]"})


    for col, max_rate in MAX_NULL_RATE.items():
        if col in df.columns:
            null_rate = float(df[col].isna().mean())
            if null_rate > max_rate:
                issues.append({"Season": season, "Tier": tier, "SourceURL": source_url,
                               "IssueType": "HIGH_NULL_RATE",
                               "Details": f"{col} null_rate={null_rate:.2%} > {max_rate:.2%}"})

    if "Team" in df.columns:
        dup_teams = df["Team"].duplicated().sum()
        if dup_teams > 0:
            issues.append({"Season": season, "Tier": tier, "SourceURL": source_url,
                           "IssueType": "DUPLICATE_TEAMS",
                           "Details": f"Duplicate Team rows in extracted table: {dup_teams}"})

    if "Capacity" in df.columns:
        caps = df["Capacity"].dropna()
        if not caps.empty:
            too_low = int((caps < 500).sum())
            too_high = int((caps > 150000).sum())
            if too_low or too_high:
                issues.append({"Season": season, "Tier": tier, "SourceURL": source_url,
                               "IssueType": "CAPACITY_OUTLIERS",
                               "Details": f"Cap<500: {too_low}, Cap>150000: {too_high}"})
    return issues


def append_issues(issue_rows: list[dict]):
    if not issue_rows:
        return
    df_issues = pd.DataFrame(issue_rows)
    if ISSUES_PATH.exists():
        df_issues.to_csv(ISSUES_PATH, mode="a", header=False, index=False)
    else:
        df_issues.to_csv(ISSUES_PATH, index=False)

# -----------------------------
# MAIN SCRAPE
# -----------------------------
def scrape_pyramid_dim(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
    tiers: list[int] = [1, 2, 3, 4],
    sleep_s: float = BASE_SLEEP,
    use_checkpoint: bool = True,
) -> pd.DataFrame:
    master = []

    existing_output = load_existing_output()
    done_keys_output = build_done_keys(existing_output)

    done_keys_checkpoint = set()
    if use_checkpoint and CHECKPOINT_PATH.exists():
        prev = pd.read_csv(CHECKPOINT_PATH)
        master.append(prev)
        done_keys_checkpoint = build_done_keys(prev)
        print(f"Loaded checkpoint: {len(prev):,} rows; {len(done_keys_checkpoint):,} season-tier keys done (checkpoint).")


    done_keys = set(done_keys_output) | set((s, int(t)) for s, t in done_keys_checkpoint)
    if done_keys_output:
        print(f"Loaded output: {len(existing_output):,} rows; {len(done_keys_output):,} season-tier keys done (output).")

    for tier in tiers:
        for year in range(start_year, end_year):
            season = season_str(year)

            if (season, tier) in done_keys:
                continue

            urls = candidate_urls(season, tier, year)
            if not urls:
                append_issues([{
                    "Season": season, "Tier": tier, "SourceURL": "",
                    "IssueType": "NO_URLS", "Details": "No URL candidates built for this season-tier."
                }])
                print(f"Skipped (no urls): {season} Tier {tier}")
                continue

            success = False
            last_url = None
            last_err = None

            for url in urls:
                last_url = url
                try:
                    html = fetch_html(url)
                    tables = pd.read_html(StringIO(html), flavor="html5lib")
                    stadia = extract_stadia_table(tables)
                    if stadia is None:
                        last_err = "No suitable stadia table found."
                        continue

                    # normalize + guard against duplicate col labels returning DataFrame
                    stadia = normalize_columns(stadia)

                    for col in ["Team", "Stadium", "Location", "Capacity_raw"]:
                        if col not in stadia.columns:
                            stadia[col] = np.nan

                    # If duplicates slipped through, take first column instance
                    for col in ["Team", "Stadium", "Location", "Capacity_raw"]:
                        if isinstance(stadia[col], pd.DataFrame):
                            stadia[col] = stadia[col].iloc[:, 0]

                    stadia = stadia[["Team", "Stadium", "Location", "Capacity_raw"]].copy()

                    stadia["Season"] = season
                    stadia["Tier"] = tier
                    stadia["Country"] = COUNTRY
                    stadia["SourceURL"] = url

                    stadia["Team"] = stadia["Team"].apply(clean_value)
                    stadia["Stadium"] = stadia["Stadium"].apply(clean_value)
                    stadia["Location"] = stadia["Location"].apply(clean_value)

                    stadia["Capacity_raw"] = stadia["Capacity_raw"].apply(clean_value)
                    stadia["Capacity"] = stadia["Capacity_raw"].apply(clean_capacity)

                    stadia["City"] = stadia["Location"].apply(extract_city)
                    stadia["GeoPlace"] = [build_geoplace(s, c, COUNTRY) for s, c in zip(stadia["Stadium"], stadia["City"])]

                    stadia["MapLabel"] = (
                        stadia["Stadium"].fillna("").astype(str).str.strip()
                        + " (" + stadia["Team"].fillna("").astype(str).str.strip() + ")"
                        + " — " + stadia["City"].fillna("").astype(str).str.strip()
                    ).str.replace(r"\s+", " ", regex=True).str.strip(" —")

                    stadia = stadia.drop_duplicates(subset=["Team"], keep="first")

                    append_issues(validate_season_tier(stadia, season, tier, url))

                    master.append(stadia)
                    success = True
                    print(f"Success: {season} Tier {tier} rows={len(stadia)} from {url}")
                    time.sleep(sleep_s)
                    break

                except Exception as e:
                    last_err = repr(e)
                    continue

            if not success:
                append_issues([{
                    "Season": season, "Tier": tier, "SourceURL": last_url or "",
                    "IssueType": "SCRAPE_FAILED",
                    "Details": last_err or "Unknown error"
                }])
                print(f"Skipped: {season} Tier {tier}  last_tried={last_url}  err={last_err}")

            if use_checkpoint and master:
                pd.concat(master, ignore_index=True).to_csv(CHECKPOINT_PATH, index=False)

    if not master and not existing_output.empty:
        return existing_output

    if not master:
        return pd.DataFrame(columns=[
            "Team", "Stadium", "Location", "Capacity_raw", "Capacity",
            "Season", "Tier", "Country", "SourceURL",
            "City", "GeoPlace", "MapLabel"
        ])

    new_out = pd.concat(master, ignore_index=True).drop_duplicates(
        subset=["Season", "Tier", "Team", "Stadium", "Location", "Capacity_raw"], keep="first"
    )

    if not existing_output.empty and {"Season", "Tier"}.issubset(existing_output.columns):
        updated_pairs = set(zip(new_out["Season"], new_out["Tier"]))
        keep_mask = ~existing_output.apply(lambda r: (r["Season"], r["Tier"]) in updated_pairs, axis=1)
        return pd.concat([existing_output[keep_mask], new_out], ignore_index=True)

    return new_out


def final_validation_report(df: pd.DataFrame) -> None:
    if df.empty:
        print("Final validation: output is empty.")
        return

    got = df[["Season", "Tier"]].drop_duplicates()
    expected = (END_YEAR - START_YEAR) * 4
    print(f"Final validation: season-tier keys collected = {len(got):,} / ~{expected:,} (some skips expected).")

    geo_null = df["GeoPlace"].isna().mean() if "GeoPlace" in df.columns else np.nan
    print(f"Final validation: GeoPlace null rate = {geo_null:.2%}" if pd.notna(geo_null) else "Final validation: GeoPlace null rate = n/a")


if __name__ == "__main__":
    # IMPORTANT: make issues reflect THIS run only
    if ISSUES_PATH.exists():
        ISSUES_PATH.unlink()

    # If you changed scrape logic and want a fresh attempt, clear checkpoint too.
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()

    df_dim_stadiums = scrape_pyramid_dim()
    df_dim_stadiums.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved: {len(df_dim_stadiums):,} rows -> {OUTPUT_PATH.resolve()}")

    final_validation_report(df_dim_stadiums)
    if ISSUES_PATH.exists():
        print(f"Issues logged to: {ISSUES_PATH.resolve()}")
