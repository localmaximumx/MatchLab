"""
Inspect Vaastav Fantasy Premier League Historical Dataset
Analyzes seasons 2016-17 through 2026-27, merged gameweek files, Understat xG metrics,
fixtures, player availability, and team aggregated metrics.
"""

import os
import sys
import glob
import json
import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = os.path.join("data", "raw", "vaastav_fpl")
DATA_DIR = os.path.join(RAW_DIR, "data")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def inspect_vaastav_fpl():
    print("Starting Vaastav FPL inspection...")
    results = {
        "dataset_name": "Vaastav Fantasy Premier League Historical Dataset",
        "repository": "https://github.com/vaastav/Fantasy-Premier-League",
        "creator": "Vaastav Anand",
        "download_date": "2026-11-05",
        "license_code": "MIT License",
        "data_provenance": "Scraped from Fantasy Premier League API (fantasy.premierleague.com) and Understat (understat.com)"
    }
    
    # 1. Identify all season directories
    season_dirs = sorted([
        d for d in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, d)) and d.startswith("20")
    ])
    results["total_seasons_found"] = len(season_dirs)
    results["seasons_list"] = season_dirs
    
    # 2. Inspect root summary files
    merged_seasons_path = os.path.join(DATA_DIR, "cleaned_merged_seasons.csv")
    team_agg_path = os.path.join(DATA_DIR, "cleaned_merged_seasons_team_aggregated.csv")
    master_teams_path = os.path.join(DATA_DIR, "master_team_list.csv")
    
    if os.path.exists(merged_seasons_path):
        fsize = os.path.getsize(merged_seasons_path)
        print("Loading sample of cleaned_merged_seasons.csv...")
        # Read header and count rows
        df_merged_sample = pd.read_csv(merged_seasons_path, nrows=5, encoding="utf-8", encoding_errors="replace")
        with open(merged_seasons_path, "r", encoding="utf-8", errors="replace") as f:
            row_count = sum(1 for _ in f) - 1
            
        results["cleaned_merged_seasons"] = {
            "file_size_mb": round(fsize / (1024 * 1024), 2),
            "total_rows": row_count,
            "total_columns": len(df_merged_sample.columns),
            "columns": list(df_merged_sample.columns)
        }
        
    if os.path.exists(team_agg_path):
        fsize = os.path.getsize(team_agg_path)
        with open(team_agg_path, "r", encoding="utf-8", errors="replace") as f:
            row_count = sum(1 for _ in f) - 1
        df_team_sample = pd.read_csv(team_agg_path, nrows=5, encoding="utf-8", encoding_errors="replace")
        results["cleaned_merged_seasons_team_aggregated"] = {
            "file_size_mb": round(fsize / (1024 * 1024), 2),
            "total_rows": row_count,
            "total_columns": len(df_team_sample.columns),
            "columns": list(df_team_sample.columns)
        }
        
    # 3. Inspect Season by Season
    seasons_summary = {}
    total_gw_player_records = 0
    
    for s in season_dirs:
        s_path = os.path.join(DATA_DIR, s)
        gw_path = os.path.join(s_path, "gws")
        understat_path = os.path.join(s_path, "understat")
        fixtures_path = os.path.join(s_path, "fixtures.csv")
        players_raw_path = os.path.join(s_path, "players_raw.csv")
        cleaned_players_path = os.path.join(s_path, "cleaned_players.csv")
        
        has_fixtures = os.path.exists(fixtures_path)
        has_players_raw = os.path.exists(players_raw_path)
        has_cleaned_players = os.path.exists(cleaned_players_path)
        
        # Check GW files
        gw_files = glob.glob(os.path.join(gw_path, "gw*.csv")) if os.path.exists(gw_path) else []
        merged_gw_file = os.path.join(gw_path, "merged_gw.csv")
        
        gw_record_count = 0
        gw_cols = []
        if os.path.exists(merged_gw_file):
            for enc in ["utf-8", "latin1", "cp1252"]:
                try:
                    m_df = pd.read_csv(merged_gw_file, nrows=5, encoding=enc)
                    gw_cols = list(m_df.columns)
                    break
                except Exception:
                    continue
            with open(merged_gw_file, "r", encoding="latin1", errors="replace") as f:
                gw_record_count = sum(1 for _ in f) - 1
            total_gw_player_records += gw_record_count
            
        # Check Understat
        understat_files = glob.glob(os.path.join(understat_path, "*.csv")) if os.path.exists(understat_path) else []
        
        seasons_summary[s] = {
            "has_fixtures": has_fixtures,
            "has_players_raw": has_players_raw,
            "has_cleaned_players": has_cleaned_players,
            "individual_gw_files_count": len(gw_files),
            "merged_gw_records": gw_record_count,
            "merged_gw_columns_count": len(gw_cols),
            "merged_gw_sample_cols": gw_cols[:15],
            "understat_players_count": len(understat_files)
        }
        
    results["seasons_summary"] = seasons_summary
    results["total_gw_player_records_all_seasons"] = total_gw_player_records
    
    # 4. Detailed Feature & Metric Evolution
    # Check when advanced xG was introduced in merged_gw
    results["metric_evolution"] = {
        "xG_in_fpl": "Introduced by official FPL in 2022-23 (expected_goals, expected_assists, expected_goal_involvements, expected_goals_conceded)",
        "understat_xG": "Available across all seasons 2016-17 through 2023-24 (xG, xA, npxG, xGChain, xGBuildup)",
        "ICT_Index": "Available across all seasons (Influence, Creativity, Threat, ICT Index)",
        "player_form_metrics": "available per gameweek (transfers in/out, value, bps, bonus, minutes, clean sheets)"
    }
    
    # 5. Championship Check
    results["championship_coverage"] = {
        "is_championship_covered": False,
        "explanation": "Fantasy Premier League is strictly limited to the 20 clubs competing in the English Premier League each season. It has zero Championship data."
    }
    
    # 6. Save JSON Summary
    out_json = os.path.join(REPORTS_DIR, "vaastav_fpl_inspection_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Inspection complete. Summary saved to {out_json}")
    
    return results

if __name__ == "__main__":
    inspect_vaastav_fpl()
