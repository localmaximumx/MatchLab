"""
Inspect Fjelstul English Football Database
Analyzes all raw CSV files in data/raw/fjelstul/data-csv/
Produces comprehensive summary statistics, schema checks, coverage breakdown,
missing value analysis, and duplicate detection.
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np

RAW_CSV_DIR = os.path.join("data", "raw", "fjelstul", "data-csv")
RAW_SQLITE_PATH = os.path.join("data", "raw", "fjelstul", "data-sqlite", "englishfootball.db")
CODEBOOK_DIR = os.path.join("data", "raw", "fjelstul", "codebook", "csv")
REPORTS_DIR = "reports"

os.makedirs(REPORTS_DIR, exist_ok=True)

def inspect_dataset():
    results = {}
    
    # 1. Inspect Files and Sizes
    files_info = []
    for fname in sorted(os.listdir(RAW_CSV_DIR)):
        if fname.endswith(".csv"):
            fpath = os.path.join(RAW_CSV_DIR, fname)
            fsize_bytes = os.path.getsize(fpath)
            files_info.append({
                "file": fname,
                "size_bytes": fsize_bytes,
                "size_mb": round(fsize_bytes / (1024 * 1024), 2)
            })
    results["files"] = files_info
    
    # 2. Inspect Variables Codebook
    var_codebook_path = os.path.join(CODEBOOK_DIR, "variables.csv")
    if os.path.exists(var_codebook_path):
        var_df = pd.read_csv(var_codebook_path)
        results["codebook_variables"] = var_df.to_dict(orient="records")
    
    # 3. Load Tables
    print("Loading seasons.csv...")
    seasons_df = pd.read_csv(os.path.join(RAW_CSV_DIR, "seasons.csv"))
    
    print("Loading teams.csv...")
    teams_df = pd.read_csv(os.path.join(RAW_CSV_DIR, "teams.csv"))
    
    print("Loading standings.csv...")
    standings_df = pd.read_csv(os.path.join(RAW_CSV_DIR, "standings.csv"))
    
    print("Loading matches.csv (this is ~32MB)...")
    matches_df = pd.read_csv(os.path.join(RAW_CSV_DIR, "matches.csv"), low_memory=False)
    
    print("Loading appearances.csv (this is ~62MB)...")
    appearances_df = pd.read_csv(os.path.join(RAW_CSV_DIR, "appearances.csv"), low_memory=False)
    
    dfs = {
        "seasons": seasons_df,
        "teams": teams_df,
        "matches": matches_df,
        "appearances": appearances_df,
        "standings": standings_df
    }
    
    # Table record counts & basic stats
    tables_summary = {}
    for name, df in dfs.items():
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df) * 100).round(3)
        missing_dict = {
            col: {"null_count": int(missing_counts[col]), "null_pct": float(missing_pct[col])}
            for col in df.columns if missing_counts[col] > 0
        }
        
        # Primary key duplicates check based on author's schema
        pk_cols = {
            "seasons": ["season_id"],
            "teams": ["team_id"],
            "matches": ["match_id"],
            "appearances": ["season_id", "match_id", "team_id"],
            "standings": ["season_id", "team_id"]
        }.get(name, [])
        
        pk_duplicates = int(df.duplicated(subset=pk_cols).sum()) if pk_cols else 0
        total_exact_duplicates = int(df.duplicated().sum())
        
        tables_summary[name] = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "pk": pk_cols,
            "pk_duplicates": pk_duplicates,
            "exact_duplicates": total_exact_duplicates,
            "missing_values": missing_dict,
            "sample_head": df.head(2).to_dict(orient="records")
        }
    
    results["tables"] = tables_summary
    
    # 4. Detailed Match & Season Breakdown
    # Check seasons coverage
    results["season_range"] = {
        "min_season": int(seasons_df["season"].min()),
        "max_season": int(seasons_df["season"].max()),
        "total_seasons_listed": int(len(seasons_df)),
        "unique_years": int(seasons_df["season"].nunique())
    }
    
    # Tier and Division Breakdown in matches
    # In matches table, let's see what columns exist:
    # Does matches have season, tier, division directly, or via season_id join?
    print("Matches columns:", matches_df.columns.tolist())
    
    # Join matches with seasons to get tier and division if not already present
    if "tier" not in matches_df.columns and "season_id" in matches_df.columns:
        matches_merged = matches_df.merge(
            seasons_df[["season_id", "season", "tier", "division", "subdivision"]],
            on="season_id",
            how="left"
        )
    else:
        matches_merged = matches_df
        
    tier_counts = matches_merged["tier"].value_counts().sort_index().to_dict()
    division_counts = matches_merged["division"].value_counts().to_dict()
    
    results["matches_by_tier"] = {int(k): int(v) for k, v in tier_counts.items()}
    results["matches_by_division"] = {str(k): int(v) for k, v in division_counts.items()}
    
    # Focus on Tier 1 (Premier League / Football League First Division)
    # and Tier 2 (Championship / Football League Second Division)
    tier1_matches = matches_merged[matches_merged["tier"] == 1]
    tier2_matches = matches_merged[matches_merged["tier"] == 2]
    
    results["tier1_total_matches"] = len(tier1_matches)
    results["tier2_total_matches"] = len(tier2_matches)
    
    # Premier League specifically (Tier 1 from 1992 onwards)
    pl_matches = matches_merged[
        (matches_merged["tier"] == 1) & 
        (matches_merged["division"].str.contains("Premier League", case=False, na=False))
    ]
    
    # Championship specifically (Tier 2)
    championship_matches = matches_merged[matches_merged["tier"] == 2]
    
    results["pl_matches_count"] = len(pl_matches)
    results["pl_seasons_count"] = int(pl_matches["season"].nunique())
    results["pl_season_min"] = int(pl_matches["season"].min()) if len(pl_matches) > 0 else None
    results["pl_season_max"] = int(pl_matches["season"].max()) if len(pl_matches) > 0 else None
    
    results["tier2_seasons_count"] = int(tier2_matches["season"].nunique())
    results["tier2_season_min"] = int(tier2_matches["season"].min()) if len(tier2_matches) > 0 else None
    results["tier2_season_max"] = int(tier2_matches["season"].max()) if len(tier2_matches) > 0 else None
    
    # Recent Premier League seasons matches per season
    pl_per_season = pl_matches.groupby("season")["match_id"].count().tail(10).to_dict()
    results["pl_recent_matches_per_season"] = {int(k): int(v) for k, v in pl_per_season.items()}
    
    # Date / Time columns inspection in matches
    # Check date column in matches
    date_cols = [col for col in matches_df.columns if "date" in col.lower() or "time" in col.lower()]
    results["date_columns"] = date_cols
    
    # Check score distributions and anomalies
    results["matches_stats"] = {
        "total_matches": len(matches_df),
        "total_goals": int(matches_df["home_team_score"].sum() + matches_df["away_team_score"].sum()),
        "avg_home_goals": float(matches_df["home_team_score"].mean().round(3)),
        "avg_away_goals": float(matches_df["away_team_score"].mean().round(3)),
        "home_win_rate": float(matches_df["home_team_win"].mean().round(4)),
        "away_win_rate": float(matches_df["away_team_win"].mean().round(4)),
        "draw_rate": float(matches_df["draw"].mean().round(4)),
        "max_home_score": int(matches_df["home_team_score"].max()),
        "max_away_score": int(matches_df["away_team_score"].max()),
        "negative_scores": int((matches_df["home_team_score"] < 0).sum() + (matches_df["away_team_score"] < 0).sum())
    }
    
    # Check teams
    results["teams_stats"] = {
        "total_teams": len(teams_df),
        "current_count": int(teams_df["current"].sum()) if "current" in teams_df.columns else None,
        "former_count": int(teams_df["former"].sum()) if "former" in teams_df.columns else None,
        "defunct_count": int(teams_df["defunct"].sum()) if "defunct" in teams_df.columns else None
    }
    
    # Save results to json for detailed reporting
    out_json_path = os.path.join(REPORTS_DIR, "fjelstul_inspection_summary.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Inspection complete. Summary saved to {out_json_path}")
    
    return results

if __name__ == "__main__":
    inspect_dataset()
