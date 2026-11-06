"""
Inspection and Validation Script for Sean Elvidge's England Football Results Dataset
Repository: https://github.com/seanelvidge/England-football-results
License: CC BY 4.0
"""

import sys
import os
import json
import pandas as pd
import numpy as np

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "england_football_results")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def inspect_dataset():
    print("=" * 80)
    print("INSPECTING SEAN ELVIDGE ENGLAND FOOTBALL RESULTS DATASET")
    print("=" * 80)

    # 1. Check directory contents and sizes
    files_info = {}
    for fname in sorted(os.listdir(DATA_DIR)):
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.isfile(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            files_info[fname] = {
                "size_mb": round(size_mb, 3),
                "size_bytes": os.path.getsize(fpath)
            }
            print(f"File: {fname:<35} | Size: {size_mb:>8.3f} MB")
        elif os.path.isdir(fpath):
            print(f"Directory: {fname}/")

    # 2. Inspect EnglandLeagueNames.csv
    names_path = os.path.join(DATA_DIR, "EnglandLeagueNames.csv")
    df_names = pd.read_csv(names_path)
    print("\n--- EnglandLeagueNames.csv ---")
    print(f"Shape: {df_names.shape}")
    print(df_names.to_string())

    # 3. Inspect EnglishTeamPointDeductions.csv
    deductions_path = os.path.join(DATA_DIR, "EnglishTeamPointDeductions.csv")
    df_deductions = pd.read_csv(deductions_path)
    print(f"\n--- EnglishTeamPointDeductions.csv (Shape: {df_deductions.shape}) ---")
    print(df_deductions.head(10).to_string())
    print(f"Total point deduction records: {len(df_deductions)}")

    # 4. Inspect EnglishTeamNamePeriods.csv
    name_periods_path = os.path.join(DATA_DIR, "EnglishTeamNamePeriods.csv")
    df_name_periods = pd.read_csv(name_periods_path)
    print(f"\n--- EnglishTeamNamePeriods.csv (Shape: {df_name_periods.shape}) ---")
    print(df_name_periods.head(10).to_string())
    print(f"Total team name period records: {len(df_name_periods)}")

    # 5. Inspect EnglandLeagueResults.csv
    results_path = os.path.join(DATA_DIR, "EnglandLeagueResults.csv")
    print(f"\n--- Loading EnglandLeagueResults.csv ({files_info['EnglandLeagueResults.csv']['size_mb']} MB) ---")
    df_results = pd.read_csv(results_path, low_memory=False)
    print(f"Total rows: {len(df_results):,}")
    print(f"Columns ({len(df_results.columns)}): {list(df_results.columns)}")
    print("\nSample records:")
    print(df_results.head(5).to_string())

    # Check data types and null counts
    print("\nColumn Null Counts and Types in EnglandLeagueResults.csv:")
    null_counts = {}
    for col in df_results.columns:
        nc = int(df_results[col].isnull().sum())
        null_counts[col] = {
            "null_count": nc,
            "null_pct": round(nc / len(df_results) * 100, 2),
            "dtype": str(df_results[col].dtype)
        }
        print(f"  {col:<20} | Dtype: {str(df_results[col].dtype):<10} | Nulls: {nc:>8,} ({null_counts[col]['null_pct']:>5.2f}%)")

    # Tiers and Seasons
    tier_counts = df_results['Tier'].value_counts().sort_index().to_dict()
    print("\nMatches by Tier:")
    for tier, count in tier_counts.items():
        print(f"  Tier {tier}: {count:,} matches")

    seasons = sorted(df_results['Season'].dropna().unique().tolist())
    print(f"\nSeasons covered: {len(seasons)} seasons (From {seasons[0]} to {seasons[-1]})")

    # Filter Premier League matches (Tier 1, Season >= 1992 or Season >= 1992-1993)
    # Let's inspect format of Season column
    print(f"Sample season values: {seasons[:5]} ... {seasons[-5:]}")

    # Inspect Tier 1 modern era
    # Check how seasons are coded (e.g. 1992 or 1992-93 or 1992-1993)
    # Convert or filter
    if isinstance(seasons[0], (int, np.integer)) or (isinstance(seasons[0], str) and str(seasons[0]).isdigit()):
        pl_mask = (df_results['Tier'] == 1) & (df_results['Season'].astype(int) >= 1992)
        tier2_mask = (df_results['Tier'] == 2)
        champ_mask = (df_results['Tier'] == 2) & (df_results['Season'].astype(int) >= 2004) # modern Championship
        tier2_modern_mask = (df_results['Tier'] == 2) & (df_results['Season'].astype(int) >= 1992)
    else:
        # String season matching
        pl_mask = (df_results['Tier'] == 1) & (df_results['Season'].astype(str) >= '1992')
        tier2_mask = (df_results['Tier'] == 2)
        champ_mask = (df_results['Tier'] == 2) & (df_results['Season'].astype(str) >= '2004')
        tier2_modern_mask = (df_results['Tier'] == 2) & (df_results['Season'].astype(str) >= '1992')

    pl_matches = df_results[pl_mask]
    tier2_matches = df_results[tier2_mask]
    champ_matches = df_results[champ_mask]
    tier2_modern_matches = df_results[tier2_modern_mask]

    print(f"\nPremier League matches (Tier 1, 1992+): {len(pl_matches):,}")
    print(f"Tier 2 matches (1992+): {len(tier2_modern_matches):,}")
    print(f"Championship matches (Tier 2, 2004+): {len(champ_matches):,}")
    print(f"All-time Tier 2 matches: {len(tier2_matches):,}")

    # Check Date column in df_results
    if 'Date' in df_results.columns:
        print("\nDate Column Inspection:")
        print(f"Sample dates: {df_results['Date'].head(10).tolist()}")
        print(f"Null dates in total: {df_results['Date'].isnull().sum():,}")
        print(f"Null dates in PL (1992+): {pl_matches['Date'].isnull().sum():,}")

    # 6. Inspect EnglandLeagueResults_wRanks.csv
    ranks_path = os.path.join(DATA_DIR, "EnglandLeagueResults_wRanks.csv")
    print(f"\n--- Loading EnglandLeagueResults_wRanks.csv ({files_info['EnglandLeagueResults_wRanks.csv']['size_mb']} MB) ---")
    df_ranks = pd.read_csv(ranks_path, low_memory=False, nrows=50000)
    print(f"Sample columns ({len(df_ranks.columns)}): {list(df_ranks.columns)}")
    print("\nSample records with ranks:")
    rank_cols_to_show = ['Season', 'Tier', 'Date', 'HomeTeam', 'AwayTeam', 'HomeRank_before', 'AwayRank_before', 'HomeRank_after', 'AwayRank_after', 'HomeWinProbability', 'DrawProbability', 'AwayWinProbability']
    print(df_ranks[rank_cols_to_show].head(10).to_string())

    # Check ranks columns across entire dataset
    df_ranks_full = pd.read_csv(ranks_path, low_memory=False)
    print(f"Full df_ranks shape: {df_ranks_full.shape}")
    ranks_new_cols = [c for c in df_ranks_full.columns if c not in df_results.columns]
    print(f"Extra columns in _wRanks: {ranks_new_cols}")

    # Critical Leakage Check:
    # Are HomeRank_before and AwayRank_before truly pre-match?
    # Let's inspect Match 1 of season 2022/2023 (Tier 1)
    sample_first_matches = df_ranks_full[(df_ranks_full['Tier'] == 1) & (df_ranks_full['Season'] == '2022/2023')].sort_values('Date').head(10)
    print("\n--- Critical Data Leakage Check on _wRanks (Season 2022/2023, Tier 1 first 10 matches) ---")
    print(sample_first_matches[['Date', 'HomeTeam', 'AwayTeam', 'Score', 'HomeRank_before', 'AwayRank_before', 'HomeRank_after', 'AwayRank_after', 'HomeWinProbability', 'DrawProbability', 'AwayWinProbability']].to_string())

    # Check probability sum (should be ~1.0)
    prob_sum = sample_first_matches['HomeWinProbability'] + sample_first_matches['DrawProbability'] + sample_first_matches['AwayWinProbability']
    print(f"\nSample probability sums: {prob_sum.head(5).tolist()}")

    # Compare with Fjelstul for PL (1992/1993 to 2023/2024)
    # Note: In Elvidge, seasons are formatted as '1992/1993'
    fjelstul_matches_path = os.path.join(BASE_DIR, "data", "raw", "fjelstul", "data-csv", "matches.csv")
    fjelstul_overlap_report = {}
    if os.path.exists(fjelstul_matches_path):
        df_fj_matches = pd.read_csv(fjelstul_matches_path, low_memory=False)
        df_fj_pl = df_fj_matches[(df_fj_matches['tier'] == 1) & (df_fj_matches['season'] >= 1992) & (df_fj_matches['season'] <= 2023)]
        
        # Elvidge seasons up to 2023/2024
        elv_pl_overlap = pl_matches[pl_matches['Season'] <= '2023/2024']
        print(f"\n--- Cross-Checking against Fjelstul ---")
        print(f"Fjelstul PL matches (1992-2023): {len(df_fj_pl):,}")
        print(f"Elvidge PL matches (1992/1993 to 2023/2024): {len(elv_pl_overlap):,}")
        fjelstul_overlap_report = {
            "fjelstul_pl_1992_2023": len(df_fj_pl),
            "elvidge_pl_1992_2023": int(len(elv_pl_overlap)),
            "difference": int(len(elv_pl_overlap) - len(df_fj_pl))
        }

    # Summary structure
    summary = {
        "dataset_name": "Sean Elvidge England Football Results",
        "repository": "https://github.com/seanelvidge/England-football-results",
        "license": "CC BY 4.0",
        "files": files_info,
        "total_matches_all_tiers": len(df_results),
        "total_matches_w_ranks": len(df_ranks_full),
        "seasons_range": [str(seasons[0]), str(seasons[-1])],
        "total_seasons": len(seasons),
        "tiers_breakdown": {int(k): int(v) for k, v in tier_counts.items()},
        "pl_matches_total": int(len(pl_matches)),
        "tier2_matches_total": int(len(tier2_matches)),
        "tier2_matches_1992_present": int(len(tier2_modern_matches)),
        "champ_matches_2004_present": int(len(champ_matches)),
        "columns_base": list(df_results.columns),
        "extra_columns_in_ranks": ranks_new_cols,
        "null_counts": null_counts,
        "team_point_deductions_count": int(len(df_deductions)),
        "team_name_periods_count": int(len(df_name_periods)),
        "fjelstul_cross_check": fjelstul_overlap_report
    }

    summary_file = os.path.join(REPORTS_DIR, "england_football_results_inspection_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nInspection summary written to {summary_file}")

    return summary

if __name__ == "__main__":
    inspect_dataset()
