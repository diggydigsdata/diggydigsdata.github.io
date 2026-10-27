import argparse
import tempfile

import pandas as pd
import numpy as np
import re
import time
from io import StringIO
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# -----------------------------
# CONFIGURATION
# -----------------------------
EN_DASH = "\u2013"
START_YEAR = 1992
END_YEAR = 2026  # scrapes 1992–93 through 2025–26 (exclusive end)
COUNTRY = "England"

LEAGUE_MAP = {
    1: [(1992, 2026, "Premier_League")],
    2: [
        (1992, 2004, "Football_League_First_Division"),
        (2004, 2016, "Football_League_Championship"),
        (2016, 2026, "EFL_Championship"),
    ],
    3: [
        (1992, 2004, "Football_League_Second_Division"),
        (2004, 2016, "Football_League_One"),
        (2016, 2026, "EFL_League_One"),
    ],
    4: [
        (1992, 2004, "Football_League_Third_Division"),
        (2004, 2016, "Football_League_Two"),
        (2016, 2026, "EFL_League_Two"),
    ],
}

USER_AGENT = "Mozilla/5.0 (compatible; stadium-scraper/1.0; +https://example.com) pandas-read-html"
REQUEST_TIMEOUT = 30
BASE_SLEEP = 1.2

BASE_DIR = Path(__file__).resolve().parents[2]  # .../assets
DATASETS_DIR = BASE_DIR / "files" / "datasets" / "too_messy_to_melt"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = DATASETS_DIR / "gold_dim_stadiums_pyramid_checkpoint.csv"
OUTPUT_PATH = DATASETS_DIR / "gold_dim_stadiums_pyramid.csv"
ISSUES_PATH = DATASETS_DIR / "gold_dim_stadiums_pyramid_issues.csv"

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
    s = s.strip()
    return np.nan if s.casefold() in ("", "-", "–", "—", "n/a", "unknown", "tbc") else s


def clean_capacity(val):
    if isinstance(val, (int, float, np.number)):
        return int(val) if pd.notna(val) and np.isfinite(val) else np.nan
    s = clean_value(val)
    if pd.isna(s):
        return np.nan
    # Parse one capacity, rather than concatenating footnotes/ranges/decimals.
    match = re.fullmatch(r"\s*(\d[\d,\s]*)(?:\.0)?\s*", s)
    return int(re.sub(r"\D", "", match.group(1))) if match else np.nan


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
            r = requests.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            time.sleep((backoff**attempt) + np.random.uniform(0, 0.4))
    raise last_err


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = flatten_columns(df)

    rename_map = {}
    for col in df.columns:
        c_low = str(col).lower()
        if "capacity" in c_low:
            if not any(x in c_low for x in ("%", "percent", "utilisation", "utilization")):
                rename_map[col] = "Capacity_raw"
            continue
        if any(x in c_low for x in ["team", "club"]):
            rename_map[col] = "Team"
        elif any(x in c_low for x in ["stadium", "ground"]):
            rename_map[col] = "Stadium"
        elif any(x in c_low for x in ["location", "town", "city", "borough", "county"]):
            rename_map[col] = "Location"

    out = df.rename(columns=rename_map)
    # Flattening alone cannot prevent different headers mapping to the same label.
    return pd.DataFrame({
        col: out.loc[:, out.columns == col].bfill(axis=1).iloc[:, 0]
        for col in dict.fromkeys(out.columns)
    })


def read_division_tables(html: str, tier: int, year: int) -> list[pd.DataFrame]:
    """Read every table, restricting combined league pages to one division."""
    soup = BeautifulSoup(html, "html.parser")
    division_names = {"first": 1, "second": 2, "third": 3, "fourth": 4}

    def division(heading):
        text = heading.get_text(" ", strip=True).lower()
        match = re.fullmatch(r"(first|second|third|fourth) division(?:\s*\[?edit\]?)?", text)
        return division_names[match.group(1)] if match else None

    headings = soup.find_all(re.compile(r"^h[2-6]$"))
    combined = len({division(h) for h in headings if division(h) is not None}) > 1
    requested_division = tier - 1 if year >= 1992 else tier
    current_division = None
    division_level = None
    tables = []
    for node in soup.find_all(["h2", "h3", "h4", "h5", "h6", "table"]):
        if node.name != "table":
            found = division(node)
            level = int(node.name[1])
            if found is not None:
                current_division, division_level = found, level
            elif division_level is not None and level <= division_level:
                current_division, division_level = None, None
            continue
        if node.find_parent("table") is not None:
            continue
        if combined and current_division != requested_division:
            continue
        try:
            tables.extend(pd.read_html(StringIO(str(node)), flavor="html5lib"))
        except ValueError:
            continue
    return tables


def team_key(value):
    value = clean_value(value)
    if pd.isna(value) or not value:
        return None
    value = re.sub(r"\s*\([A-Z,\s]+\)\s*$", "", value)
    value = re.sub(r"\bF\.?\s*C\.?$", "", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip().casefold()


def looks_like_stadia_table(df: pd.DataFrame) -> bool:
    """Accept normalized tables with a club roster and any stadium metadata."""
    return bool("Team" in df.columns and 14 <= len(df) <= 30
                and any(field in df.columns for field in ("Stadium", "Capacity_raw", "Location")))


def extract_stadia_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    """Combine independent metadata tables by club; never use attendance as capacity."""
    fields = ("Stadium", "Location", "Capacity_raw")
    normalized = [normalize_columns(table) for table in tables]
    candidates = []
    has_metadata = any("Team" in table and any(field in table for field in fields)
                       for table in normalized)
    if not has_metadata:
        return None
    for tt in normalized:
        columns = " ".join(str(col).lower() for col in tt.columns)
        is_roster = ("Team" in tt and 14 <= len(tt) <= 30
                     and re.search(r"\b(pld|played)\b", columns)
                     and re.search(r"\b(pts|points)\b", columns))
        if not looks_like_stadia_table(tt) and not is_roster:
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

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    base = candidates[0][2].copy()
    base["Team"] = base["Team"].apply(clean_value)
    base["_team_key"] = base["Team"].map(team_key)
    base = base.loc[base["_team_key"].notna()].drop_duplicates("_team_key")
    base = base.set_index("_team_key")
    for field in fields:
        if field not in base:
            base[field] = np.nan
        base[field] = base[field].map(clean_value).replace("", np.nan)

    # Supplement the anchor's club roster with fields from attendance/location tables.
    for table in normalized:
        if "Team" not in table or not any(field in table for field in fields):
            continue
        donor = table.copy()
        donor["_team_key"] = donor["Team"].map(team_key)
        donor = donor.loc[donor["_team_key"].notna()]
        for field in fields:
            if field not in donor:
                continue
            donor[field] = donor[field].map(clean_value).replace("", np.nan)
            # Multiple grounds/capacities for a club need review, not an arbitrary pick.
            unique = donor.groupby("_team_key")[field].agg(
                lambda values: values.dropna().iloc[0] if values.dropna().nunique() == 1 else np.nan
            )
            base[field] = base[field].fillna(base.index.to_series().map(unique))
    result = base[["Team", *fields]].reset_index(drop=True)
    if result[list(fields)].isna().all().all():
        return None
    return result


def impute_stadium_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Fill city only where direct records agree for the same stadium name."""
    out = df.copy()
    if out.empty or not {"Stadium", "City"}.issubset(out.columns):
        return out
    for col in ("City", "City_SourceURL", "City_Donor_Season", "City_Imputed"):
        if col not in out:
            out[col] = False if col == "City_Imputed" else pd.Series(index=out.index, dtype="object")
        out[col] = out[col].astype("object")
    keys = out["Stadium"].map(team_key)
    direct = out["City"].notna() & out["City"].astype("string").str.strip().ne("")
    # Existing imputed values cannot become new independent evidence.
    imputed = out["City_Imputed"].astype("string").str.lower().eq("true").fillna(False)
    donors = out.loc[direct & ~imputed].copy()
    donors["_stadium_key"] = keys.loc[donors.index]
    for key, group in donors.groupby("_stadium_key"):
        cities = group["City"].map(clean_value).str.casefold().unique()
        if len(cities) != 1:
            continue
        missing = keys.eq(key) & ~direct
        if not missing.any():
            continue
        donor = group.iloc[0]
        out.loc[missing, "City"] = donor["City"]
        out.loc[missing, "City_Imputed"] = True
        out.loc[missing, "City_SourceURL"] = donor.get("SourceURL", np.nan)
        out.loc[missing, "City_Donor_Season"] = donor.get("Season", np.nan)
        for index in out.index[missing]:
            out.at[index, "GeoPlace"] = build_geoplace(
                out.at[index, "Stadium"], donor["City"], out.loc[index].get("Country", COUNTRY)
            )
            out.at[index, "MapLabel"] = f"{out.at[index, 'Stadium']} ({out.at[index, 'Team']}) — {donor['City']}"
    return out


# -----------------------------
# INCREMENTAL SKIP LOGIC
# -----------------------------
def load_existing_output() -> pd.DataFrame:
    return load_saved_data(OUTPUT_PATH)


def load_saved_data(path: Path) -> pd.DataFrame:
    """A missing file is normal; unreadable saved data must stop the run."""
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise RuntimeError(f"Cannot read saved data at {path}; aborting.") from exc

    missing = {"Season", "Tier", "Team"} - set(df.columns)
    if missing:
        raise ValueError(
            f"Saved data at {path} is missing columns {sorted(missing)}; aborting."
        )
    return df


def save_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    """Replace a CSV only after its temporary file has been fully written."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            df.to_csv(temp_file, index=False)
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def season_tier_mask(df: pd.DataFrame, keys: set[tuple[str, int]]) -> pd.Series:
    if df.empty:
        return pd.Series(False, index=df.index, dtype=bool)
    numeric_tiers = pd.to_numeric(df["Tier"], errors="coerce")
    return pd.Series(
        [(season, tier) in keys for season, tier in zip(df["Season"], numeric_tiers)],
        index=df.index, dtype=bool,
    )


def merge_season_tiers(existing: pd.DataFrame, updates: pd.DataFrame) -> pd.DataFrame:
    """New tables replace whole season/tier groups, preserving other groups."""
    if updates.empty:
        return existing.copy()
    if existing.empty:
        return updates.copy()
    updated_pairs = set(zip(updates["Season"], updates["Tier"]))
    remaining = existing.loc[~season_tier_mask(existing, updated_pairs)]
    return pd.concat([remaining, updates], ignore_index=True)


def preserve_saved_metadata(existing: pd.DataFrame, updates: pd.DataFrame) -> pd.DataFrame:
    """A partial refresh must not erase sourced fields for the same club-season."""
    if existing.empty or updates.empty:
        return updates
    old = existing.copy()
    old["_key"] = list(zip(old["Season"], pd.to_numeric(old["Tier"], errors="coerce"),
                           old["Team"].map(team_key)))
    old = old.drop_duplicates("_key", keep="last").set_index("_key")
    out = updates.copy()
    for field in ("GeoPlace", "MapLabel"):
        out[field] = out[field].astype("object")
    for index, row in out.iterrows():
        key = (row["Season"], row["Tier"], team_key(row["Team"]))
        if key not in old.index:
            continue
        saved = old.loc[[key]].iloc[0]
        new_stadium, old_stadium = team_key(row.get("Stadium")), team_key(saved.get("Stadium"))
        if new_stadium and old_stadium and new_stadium != old_stadium:
            continue
        for field in ("Stadium", "Location", "Capacity_raw", "Capacity", "City"):
            if pd.isna(row.get(field)) and pd.notna(saved.get(field)):
                out[field] = out[field].astype("object")
                out.at[index, field] = saved[field]
                source_col = {"Capacity_raw": "Capacity_SourceURL", "Capacity": "Capacity_SourceURL",
                              "Location": "Location_SourceURL", "Stadium": "Stadium_SourceURL",
                              "City": "City_SourceURL"}[field]
                out[source_col] = out[source_col].astype("object")
                out.at[index, source_col] = saved.get(source_col, saved.get("SourceURL", np.nan))
                if field == "City":
                    out.at[index, "City_Imputed"] = saved.get("City_Imputed", False)
                    out["City_Donor_Season"] = out["City_Donor_Season"].astype("object")
                    out.at[index, "City_Donor_Season"] = saved.get("City_Donor_Season", np.nan)
        if pd.isna(out.at[index, "City"]):
            out["City"] = out["City"].astype("object")
            out.at[index, "City"] = extract_city(out.at[index, "Location"])
            out["City_SourceURL"] = out["City_SourceURL"].astype("object")
            out.at[index, "City_SourceURL"] = out.at[index, "Location_SourceURL"]
        out.at[index, "GeoPlace"] = build_geoplace(out.at[index, "Stadium"], out.at[index, "City"],
                                                    out.at[index, "Country"])
        out.at[index, "MapLabel"] = f"{out.at[index, 'Stadium']} ({row['Team']}) — {out.at[index, 'City']}"
    return out


def requested_keys(start_year: int, end_year: int, tiers) -> set[tuple[str, int]]:
    if start_year >= end_year:
        raise ValueError("start_year must be less than the exclusive end_year.")
    if not tiers or any(tier not in LEAGUE_MAP for tier in tiers):
        raise ValueError("Select at least one tier from 1, 2, 3, 4.")
    return {(season_str(year), tier) for year in range(start_year, end_year) for tier in tiers}


def clear_saved_checkpoint(keys: set[tuple[str, int]]) -> None:
    """Discard committed groups only; leave other pending ranges available."""
    if not CHECKPOINT_PATH.exists():
        return
    checkpoint = load_saved_data(CHECKPOINT_PATH)
    remaining = checkpoint.loc[~season_tier_mask(checkpoint, keys)]
    if remaining.empty:
        CHECKPOINT_PATH.unlink()
    else:
        save_csv_atomic(remaining, CHECKPOINT_PATH)


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
def validate_season_tier(
    df: pd.DataFrame, season: str, tier: int, source_url: str
) -> list[dict]:
    issues = []
    if df is None or df.empty:
        issues.append(
            {
                "Season": season,
                "Tier": tier,
                "SourceURL": source_url,
                "IssueType": "EMPTY_RESULT",
                "Details": "No rows extracted.",
            }
        )
        return issues

    lo, hi = EXPECTED_ROWS_BY_TIER.get(tier, (14, 30))
    n = len(df)
    if not (lo <= n <= hi):
        issues.append(
            {
                "Season": season,
                "Tier": tier,
                "SourceURL": source_url,
                "IssueType": "ROWCOUNT_OUT_OF_RANGE",
                "Details": f"Rows={n} expected_range=[{lo},{hi}]",
            }
        )

    for col, max_rate in MAX_NULL_RATE.items():
        if col in df.columns:
            null_rate = float(df[col].isna().mean())
            if null_rate > max_rate:
                issues.append(
                    {
                        "Season": season,
                        "Tier": tier,
                        "SourceURL": source_url,
                        "IssueType": "HIGH_NULL_RATE",
                        "Details": f"{col} null_rate={null_rate:.2%} > {max_rate:.2%}",
                    }
                )

    if "Team" in df.columns:
        dup_teams = df["Team"].duplicated().sum()
        if dup_teams > 0:
            issues.append(
                {
                    "Season": season,
                    "Tier": tier,
                    "SourceURL": source_url,
                    "IssueType": "DUPLICATE_TEAMS",
                    "Details": f"Duplicate Team rows in extracted table: {dup_teams}",
                }
            )

    if "Capacity" in df.columns:
        caps = df["Capacity"].dropna()
        if not caps.empty:
            too_low = int((caps < 500).sum())
            too_high = int((caps > 150000).sum())
            if too_low or too_high:
                issues.append(
                    {
                        "Season": season,
                        "Tier": tier,
                        "SourceURL": source_url,
                        "IssueType": "CAPACITY_OUTLIERS",
                        "Details": f"Cap<500: {too_low}, Cap>150000: {too_high}",
                    }
                )
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
    tiers: tuple[int, ...] = (1, 2, 3, 4),
    sleep_s: float = BASE_SLEEP,
    use_checkpoint: bool = True,
    refresh: bool = False,
) -> pd.DataFrame:
    tiers = tuple(dict.fromkeys(tiers))
    selected_keys = requested_keys(start_year, end_year, tiers)
    pending = pd.DataFrame()
    checkpoint = pd.DataFrame()

    existing_output = load_existing_output()
    done_keys_output = build_done_keys(existing_output)

    done_keys_checkpoint = set()
    if use_checkpoint and CHECKPOINT_PATH.exists():
        checkpoint = load_saved_data(CHECKPOINT_PATH)
        pending = checkpoint.loc[season_tier_mask(checkpoint, selected_keys)].copy()
        done_keys_checkpoint = build_done_keys(pending)
        print(
            f"Loaded checkpoint: {len(pending):,} rows in requested range; {len(done_keys_checkpoint):,} season-tier keys done (checkpoint)."
        )

    done_keys = set(done_keys_output) | set(
        (s, int(t)) for s, t in done_keys_checkpoint
    )
    if done_keys_output:
        print(
            f"Loaded output: {len(existing_output):,} rows; {len(done_keys_output):,} season-tier keys done (output)."
        )

    for tier in tiers:
        for year in range(start_year, end_year):
            season = season_str(year)

            if not refresh and (season, tier) in done_keys:
                continue

            urls = candidate_urls(season, tier, year)
            if not urls:
                append_issues(
                    [
                        {
                            "Season": season,
                            "Tier": tier,
                            "SourceURL": "",
                            "IssueType": "NO_URLS",
                            "Details": "No URL candidates built for this season-tier.",
                        }
                    ]
                )
                print(f"Skipped (no urls): {season} Tier {tier}")
                continue

            success = False
            last_url = None
            last_err = None

            for url in urls:
                last_url = url
                try:
                    html = fetch_html(url)
                    tables = read_division_tables(html, tier, year)
                    stadia = extract_stadia_table(tables)
                    if stadia is None:
                        last_err = "No suitable stadium/capacity/location tables found in the requested division."
                        continue

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
                    stadia["City_Imputed"] = False
                    stadia["City_SourceURL"] = stadia["City"].map(lambda value: url if pd.notna(value) else np.nan)
                    stadia["City_Donor_Season"] = np.nan
                    for field, source_col in (("Stadium", "Stadium_SourceURL"),
                                              ("Capacity", "Capacity_SourceURL"),
                                              ("Location", "Location_SourceURL")):
                        stadia[source_col] = stadia[field].map(lambda value: url if pd.notna(value) else np.nan)
                    stadia["GeoPlace"] = [
                        build_geoplace(s, c, COUNTRY)
                        for s, c in zip(stadia["Stadium"], stadia["City"])
                    ]

                    stadia["MapLabel"] = (
                        (
                            stadia["Stadium"].fillna("").astype(str).str.strip()
                            + " ("
                            + stadia["Team"].fillna("").astype(str).str.strip()
                            + ")"
                            + " — "
                            + stadia["City"].fillna("").astype(str).str.strip()
                        )
                        .str.replace(r"\s+", " ", regex=True)
                        .str.strip(" —")
                    )

                    stadia = stadia.drop_duplicates(subset=["Team"], keep="first")
                    stadia = preserve_saved_metadata(
                        merge_season_tiers(existing_output, pending), stadia
                    )

                    append_issues(validate_season_tier(stadia, season, tier, url))

                    pending = merge_season_tiers(pending, stadia)
                    success = True
                    print(
                        f"Success: {season} Tier {tier} rows={len(stadia)} from {url}"
                    )
                    time.sleep(sleep_s)
                    break

                except Exception as e:
                    last_err = repr(e)
                    continue

            if not success:
                append_issues(
                    [
                        {
                            "Season": season,
                            "Tier": tier,
                            "SourceURL": last_url or "",
                            "IssueType": "SCRAPE_FAILED",
                            "Details": last_err or "Unknown error",
                        }
                    ]
                )
                print(
                    f"Skipped: {season} Tier {tier}  last_tried={last_url}  err={last_err}"
                )

            if use_checkpoint and success:
                # Keep unrelated pending seasons, with fresh tables taking precedence.
                checkpoint = merge_season_tiers(checkpoint, pending)
                save_csv_atomic(checkpoint, CHECKPOINT_PATH)

    if pending.empty and not existing_output.empty:
        return impute_stadium_cities(existing_output)

    if pending.empty:
        return pd.DataFrame(
            columns=[
                "Team",
                "Stadium",
                "Location",
                "Capacity_raw",
                "Capacity",
                "Season",
                "Tier",
                "Country",
                "SourceURL",
                "City",
                "GeoPlace",
                "MapLabel",
            ]
        )

    return impute_stadium_cities(merge_season_tiers(existing_output, pending))


def final_validation_report(
    df: pd.DataFrame,
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
    tiers: tuple[int, ...] = (1, 2, 3, 4),
) -> None:
    expected_keys = requested_keys(start_year, end_year, tiers)
    if df.empty:
        print("Final validation: output is empty.")
        return

    selected = df.loc[season_tier_mask(df, expected_keys)]
    got = selected[["Season", "Tier"]].drop_duplicates()
    print(
        f"Final validation: requested season-tier keys collected = {len(got):,} / {len(expected_keys):,}."
    )
    total_keys = len(df[["Season", "Tier"]].drop_duplicates())
    print(f"Final validation: saved season-tier keys total = {total_keys:,}.")

    geo_null = df["GeoPlace"].isna().mean() if "GeoPlace" in df.columns else np.nan
    print(
        f"Final validation: GeoPlace null rate = {geo_null:.2%}"
        if pd.notna(geo_null)
        else "Final validation: GeoPlace null rate = n/a"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrape stadium data while preserving other saved seasons."
    )
    parser.add_argument("--start-year", type=int, default=START_YEAR,
                        help="First season's starting year (inclusive).")
    parser.add_argument("--end-year", type=int, default=END_YEAR,
                        help="Exclusive end year; 2026 includes the 2025/26 season.")
    parser.add_argument("--tiers", nargs="+", type=int, choices=sorted(LEAGUE_MAP),
                        default=[1, 2, 3, 4], help="Divisions to scrape (default: all four).")
    parser.add_argument("--refresh", action="store_true",
                        help="Retry selected seasons even when output or checkpoint data exists.")
    parser.add_argument("--impute-cities-only", action="store_true",
                        help="Fill unambiguous cities in saved data without fetching Wikipedia.")
    args = parser.parse_args(argv)
    if args.start_year >= args.end_year:
        parser.error("--start-year must be less than --end-year.")
    args.tiers = tuple(dict.fromkeys(args.tiers))
    return args


def main(argv=None) -> None:
    args = parse_args(argv)
    selected_keys = requested_keys(args.start_year, args.end_year, args.tiers)
    # Check saved data before changing any run artifacts.
    existing = load_existing_output()
    load_saved_data(CHECKPOINT_PATH)
    if args.impute_cities_only:
        if existing.empty:
            raise ValueError("No saved stadium data available for city imputation.")
        before = existing["City"].notna().sum() if "City" in existing else 0
        result = impute_stadium_cities(existing)
        save_csv_atomic(result, OUTPUT_PATH)
        after = result["City"].notna().sum() if "City" in result else 0
        print(f"Filled {after - before:,} missing cities; saved {len(result):,} stadium rows -> {OUTPUT_PATH}")
        return

    # IMPORTANT: make issues reflect THIS run only
    if ISSUES_PATH.exists():
        ISSUES_PATH.unlink()

    df_dim_stadiums = scrape_pyramid_dim(
        start_year=args.start_year, end_year=args.end_year,
        tiers=args.tiers, refresh=args.refresh,
    )
    save_csv_atomic(df_dim_stadiums, OUTPUT_PATH)
    print(f"Saved: {len(df_dim_stadiums):,} rows -> {OUTPUT_PATH.resolve()}")
    clear_saved_checkpoint(selected_keys)

    final_validation_report(df_dim_stadiums, args.start_year, args.end_year, args.tiers)
    if ISSUES_PATH.exists():
        print(f"Issues logged to: {ISSUES_PATH.resolve()}")


if __name__ == "__main__":
    main()
