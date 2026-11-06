"""
Comprehensive Inspection Script for Football-Data.co.uk Historical Datasets
Analyzes Premier League (E0) and Championship (E1) across all downloaded seasons.
Handles ragged CSVs (variable column counts across rows), encodings, bookmaker odds evolution,
in-match statistics coverage, and data leakage audits for MatchLab.
"""

import sys
import os
import glob
import json
import csv
import pandas as pd
import numpy as np

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "football_data_co_uk")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def safe_read_csv(filepath):
    """
    Safely reads Football-Data.co.uk CSVs, handling:
    1. Ragged rows (variable column counts across rows within the same file)
    2. Encodings (latin1/cp1252/utf-8)
    3. Blank trailing rows/commas
    """
    for enc in ['latin1', 'cp1252', 'utf-8']:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
            if not rows:
                return None

            raw_header = [c.strip() for c in rows[0]]
            max_cols = max(len(r) for r in rows)

            # Sanitize duplicate or empty column headers
            header = []
            seen = {}
            for i in range(max_cols):
                if i < len(raw_header) and raw_header[i]:
                    name = raw_header[i]
                else:
                    name = f"Unnamed_{i}"
                if name in seen:
                    seen[name] += 1
                    name = f"{name}_{seen[name]}"
                else:
                    seen[name] = 0
                header.append(name)

            padded_rows = [r + [''] * (max_cols - len(r)) for r in rows[1:]]
            df = pd.DataFrame(padded_rows, columns=header)

            # Drop rows without HomeTeam or Date
            if 'HomeTeam' in df.columns:
                df = df[df['HomeTeam'].astype(str).str.strip() != '']
            if 'Date' in df.columns:
                df = df[df['Date'].astype(str).str.strip() != '']

            # Strip whitespace on string columns safely
            for col in list(df.columns):
                # Ensure it's a series
                s = df[col]
                if isinstance(s, pd.Series) and s.dtype == object:
                    df[col] = s.astype(str).str.strip().replace({'': np.nan})

            return df
        except Exception as e:
            continue
    return None

def inspect_dataset():
    print("=" * 80)
    print("INSPECTING FOOTBALL-DATA.CO.UK HISTORICAL DATASETS")
    print("=" * 80)

    # 1. Read notes.txt
    notes_path = os.path.join(DATA_DIR, "notes.txt")
    notes_summary = ""
    if os.path.exists(notes_path):
        with open(notes_path, "r", encoding="utf-8", errors="replace") as f:
            notes_text = f.read()
        print(f"Notes.txt found: {len(notes_text):,} characters")
        notes_summary = notes_text[:1000]

    # 2. Discover all CSV files
    all_files = sorted(glob.glob(os.path.join(DATA_DIR, "*", "*.csv")))
    print(f"Total CSV files found: {len(all_files)}")

    pl_files = [f for f in all_files if os.path.basename(f) == "E0.csv"]
    champ_files = [f for f in all_files if os.path.basename(f) == "E1.csv"]
    print(f"  Premier League (E0.csv): {len(pl_files)} files")
    print(f"  Championship (E1.csv):   {len(champ_files)} files")

    # 3. Analyze Premier League (E0)
    print("\n--- Inspecting Premier League (E0) ---")
    pl_dfs = []
    pl_seasons_stats = []

    for fpath in pl_files:
        season_dir = os.path.basename(os.path.dirname(fpath))
        df = safe_read_csv(fpath)
        if df is None or len(df) == 0:
            print(f"  Warning: Empty or unreadable file: {fpath}")
            continue

        df = df.copy()
        df['season'] = season_dir
        pl_dfs.append(df)

        has_ht = 'HTHG' in df.columns and 'HTAG' in df.columns
        has_shots = 'HS' in df.columns and 'AS' in df.columns
        has_sot = 'HST' in df.columns and 'AST' in df.columns
        has_corners = 'HC' in df.columns and 'AC' in df.columns
        has_fouls = 'HF' in df.columns and 'AF' in df.columns
        has_cards = 'HY' in df.columns and 'AY' in df.columns and 'HR' in df.columns and 'AR' in df.columns
        has_b365 = 'B365H' in df.columns
        has_pinnacle = 'PSH' in df.columns or 'PH' in df.columns
        has_closing = 'PSCH' in df.columns or 'B365CH' in df.columns
        has_time = 'Time' in df.columns
        has_totals = any(c in df.columns for c in ['BbAv>2.5', 'Avg>2.5', 'B365>2.5', 'P>2.5'])
        has_asian_handicap = any(c in df.columns for c in ['BbAHh', 'AHh', 'B365AHH'])

        pl_seasons_stats.append({
            "season": season_dir,
            "matches": len(df),
            "columns_count": len(df.columns),
            "has_half_time": has_ht,
            "has_shots": has_shots,
            "has_sot": has_sot,
            "has_corners": has_corners,
            "has_fouls": has_fouls,
            "has_cards": has_cards,
            "has_b365": has_b365,
            "has_pinnacle": has_pinnacle,
            "has_closing_odds": has_closing,
            "has_totals_over_under": has_totals,
            "has_asian_handicap": has_asian_handicap,
            "has_kickoff_time": has_time
        })

    # Combine PL
    df_pl_all = pd.concat(pl_dfs, ignore_index=True, sort=False) if pl_dfs else pd.DataFrame()
    print(f"Total Premier League Matches: {len(df_pl_all):,}")
    print(f"Total PL Seasons: {len(pl_dfs)}")
    print(f"Unique PL Columns across history: {len(df_pl_all.columns)}")

    # 4. Analyze Championship (E1)
    print("\n--- Inspecting Championship (E1) ---")
    champ_dfs = []
    champ_seasons_stats = []

    for fpath in champ_files:
        season_dir = os.path.basename(os.path.dirname(fpath))
        df = safe_read_csv(fpath)
        if df is None or len(df) == 0:
            print(f"  Warning: Empty or unreadable file: {fpath}")
            continue

        df = df.copy()
        df['season'] = season_dir
        champ_dfs.append(df)

        has_ht = 'HTHG' in df.columns and 'HTAG' in df.columns
        has_shots = 'HS' in df.columns and 'AS' in df.columns
        has_sot = 'HST' in df.columns and 'AST' in df.columns
        has_corners = 'HC' in df.columns and 'AC' in df.columns
        has_fouls = 'HF' in df.columns and 'AF' in df.columns
        has_cards = 'HY' in df.columns and 'AY' in df.columns and 'HR' in df.columns and 'AR' in df.columns
        has_b365 = 'B365H' in df.columns
        has_pinnacle = 'PSH' in df.columns or 'PH' in df.columns
        has_closing = 'PSCH' in df.columns or 'B365CH' in df.columns
        has_time = 'Time' in df.columns
        has_totals = any(c in df.columns for c in ['BbAv>2.5', 'Avg>2.5', 'B365>2.5', 'P>2.5'])
        has_asian_handicap = any(c in df.columns for c in ['BbAHh', 'AHh', 'B365AHH'])

        champ_seasons_stats.append({
            "season": season_dir,
            "matches": len(df),
            "columns_count": len(df.columns),
            "has_half_time": has_ht,
            "has_shots": has_shots,
            "has_sot": has_sot,
            "has_corners": has_corners,
            "has_fouls": has_fouls,
            "has_cards": has_cards,
            "has_b365": has_b365,
            "has_pinnacle": has_pinnacle,
            "has_closing_odds": has_closing,
            "has_totals_over_under": has_totals,
            "has_asian_handicap": has_asian_handicap,
            "has_kickoff_time": has_time
        })

    df_champ_all = pd.concat(champ_dfs, ignore_index=True, sort=False) if champ_dfs else pd.DataFrame()
    print(f"Total Championship Matches: {len(df_champ_all):,}")
    print(f"Total Championship Seasons: {len(champ_dfs)}")
    print(f"Unique Championship Columns across history: {len(df_champ_all.columns)}")

    # 5. Bookmakers and Market Analysis
    bookmaker_prefixes = ['B365', 'BW', 'IW', 'LB', 'PS', 'PH', 'SO', 'SB', 'SJ', 'SY', 'VC', 'WH', 'GB', 'BS', 'Bb']
    found_bm_cols = [c for c in df_pl_all.columns if any(c.startswith(p) for p in bookmaker_prefixes)]
    print(f"\nDiscovered {len(found_bm_cols)} Bookmaker Odds / Market columns across history!")

    # Count odds coverage in PL
    b365_matches = df_pl_all['B365H'].notnull().sum() if 'B365H' in df_pl_all.columns else 0
    
    # Pinnacle check
    pinnacle_cols = [c for c in ['PSH', 'PH'] if c in df_pl_all.columns]
    if len(pinnacle_cols) == 2:
        pinnacle_matches = int((df_pl_all['PSH'].notnull() | df_pl_all['PH'].notnull()).sum())
    elif len(pinnacle_cols) == 1:
        pinnacle_matches = int(df_pl_all[pinnacle_cols[0]].notnull().sum())
    else:
        pinnacle_matches = 0

    closing_pinnacle = int(df_pl_all['PSCH'].notnull().sum()) if 'PSCH' in df_pl_all.columns else 0
    closing_b365 = int(df_pl_all['B365CH'].notnull().sum()) if 'B365CH' in df_pl_all.columns else 0
    closing_max = int(df_pl_all['MaxCH'].notnull().sum()) if 'MaxCH' in df_pl_all.columns else 0

    print(f"PL Matches with Bet365 1X2 odds: {b365_matches:,} ({b365_matches/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Pinnacle 1X2 odds: {pinnacle_matches:,} ({pinnacle_matches/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Pinnacle Closing odds: {closing_pinnacle:,} ({closing_pinnacle/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Bet365 Closing odds: {closing_b365:,} ({closing_b365/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Market Max Closing odds: {closing_max:,} ({closing_max/len(df_pl_all)*100:.1f}%)")

    # In-match stats coverage
    shots_matches = int(df_pl_all['HS'].notnull().sum()) if 'HS' in df_pl_all.columns else 0
    corners_matches = int(df_pl_all['HC'].notnull().sum()) if 'HC' in df_pl_all.columns else 0
    fouls_matches = int(df_pl_all['HF'].notnull().sum()) if 'HF' in df_pl_all.columns else 0
    cards_matches = int(df_pl_all['HY'].notnull().sum()) if 'HY' in df_pl_all.columns else 0

    print(f"PL Matches with Shots (HS/AS): {shots_matches:,} ({shots_matches/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Corners (HC/AC): {corners_matches:,} ({corners_matches/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Fouls (HF/AF): {fouls_matches:,} ({fouls_matches/len(df_pl_all)*100:.1f}%)")
    print(f"PL Matches with Yellow/Red Cards: {cards_matches:,} ({cards_matches/len(df_pl_all)*100:.1f}%)")

    # Sample records
    print("\nSample modern Premier League record (2023-2024):")
    sample_modern = df_pl_all[df_pl_all['season'] == '2023-2024'].head(1)
    cols_to_print = [c for c in ['Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'B365H', 'B365D', 'B365A', 'PSH', 'PSD', 'PSA', 'PSCH', 'PSCD', 'PSCA'] if c in sample_modern.columns]
    print(sample_modern[cols_to_print].to_string())

    # 6. Save JSON Summary
    summary = {
        "dataset_name": "Football-Data.co.uk Historical Match & Odds Archives",
        "source_url": "https://www.football-data.co.uk/englandm.php",
        "license_notes": "Free for personal use, research, and non-commercial educational analytics. No commercial resale or distribution.",
        "premier_league": {
            "total_matches": int(len(df_pl_all)),
            "seasons_count": len(pl_dfs),
            "seasons_list": [s["season"] for s in pl_seasons_stats],
            "total_columns": int(len(df_pl_all.columns)),
            "matches_with_b365_odds": int(b365_matches),
            "matches_with_pinnacle_odds": int(pinnacle_matches),
            "matches_with_pinnacle_closing_odds": int(closing_pinnacle),
            "matches_with_b365_closing_odds": int(closing_b365),
            "matches_with_market_max_closing_odds": int(closing_max),
            "matches_with_shots": int(shots_matches),
            "matches_with_corners": int(corners_matches),
            "matches_with_fouls": int(fouls_matches),
            "matches_with_cards": int(cards_matches),
            "season_breakdown": pl_seasons_stats
        },
        "championship": {
            "total_matches": int(len(df_champ_all)),
            "seasons_count": len(champ_dfs),
            "seasons_list": [s["season"] for s in champ_seasons_stats],
            "total_columns": int(len(df_champ_all.columns)),
            "season_breakdown": champ_seasons_stats
        },
        "total_matches_combined": int(len(df_pl_all) + len(df_champ_all)),
        "discovered_bookmaker_columns_count": len(found_bm_cols)
    }

    summary_file = os.path.join(REPORTS_DIR, "football_data_co_uk_inspection_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nInspection summary written to {summary_file}")

    return summary

if __name__ == "__main__":
    inspect_dataset()
