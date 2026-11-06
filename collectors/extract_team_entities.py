"""
Phase 2 - Step 2.1: Extract Distinct Team Entities across all Data Sources
Extracts all unique team names from:
1. Sean Elvidge (League Results + Team Name Periods)
2. Fjelstul (teams.csv + matches.csv)
3. Football-Data.co.uk (E0.csv and E1.csv across all 34 seasons)
4. OpenFootball (England league match files)
5. Vaastav FPL (seasons teams.csv)
6. StatsBomb (matches JSONs)
Outputs comprehensive extraction summary to data/processed/raw_teams_extracted.json
"""

import sys
import os
import glob
import json
import csv
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(DATA_PROCESSED, exist_ok=True)

def extract_teams():
    print("=" * 80)
    print("PHASE 2 - EXTRACTING TEAM STRINGS ACROSS ALL DATASETS")
    print("=" * 80)

    extracted = {}

    # 1. Sean Elvidge
    print("1. Extracting from Sean Elvidge...")
    elv_teams = set()
    elv_name_periods_path = os.path.join(DATA_RAW, "england_football_results", "EnglishTeamNamePeriods.csv")
    if os.path.exists(elv_name_periods_path):
        df_np = pd.read_csv(elv_name_periods_path)
        for t in df_np['Team'].dropna().unique():
            elv_teams.add(t.strip())
        for p in df_np['Name'].dropna().unique():
            elv_teams.add(p.strip())

    elv_matches_path = os.path.join(DATA_RAW, "england_football_results", "EnglandLeagueResults.csv")
    if os.path.exists(elv_matches_path):
        # Focus on Tier 1 and Tier 2 from 1992 to present
        df_m = pd.read_csv(elv_matches_path, low_memory=False)
        tier1_2 = df_m[(df_m['Tier'].isin([1, 2])) & (df_m['Season'] >= '1992/1993')]
        pl_teams_elv = sorted(set(tier1_2[tier1_2['Tier'] == 1]['HomeTeam'].dropna().unique()) | set(tier1_2[tier1_2['Tier'] == 1]['AwayTeam'].dropna().unique()))
        champ_teams_elv = sorted(set(tier1_2[tier1_2['Tier'] == 2]['HomeTeam'].dropna().unique()) | set(tier1_2[tier1_2['Tier'] == 2]['AwayTeam'].dropna().unique()))
        for t in tier1_2['HomeTeam'].dropna().unique():
            elv_teams.add(t.strip())
        for t in tier1_2['AwayTeam'].dropna().unique():
            elv_teams.add(t.strip())
    else:
        pl_teams_elv, champ_teams_elv = [], []

    extracted['elvidge'] = {
        "total_distinct": len(elv_teams),
        "pl_teams_1992_present": pl_teams_elv,
        "champ_teams_1992_present": champ_teams_elv,
        "all_extracted": sorted(elv_teams)
    }
    print(f"  ✓ Elvidge: {len(elv_teams)} unique names (PL: {len(pl_teams_elv)}, Champ: {len(champ_teams_elv)})")

    # 2. Fjelstul
    print("\n2. Extracting from Fjelstul...")
    fj_teams = set()
    fj_teams_path = os.path.join(DATA_RAW, "fjelstul", "data-csv", "teams.csv")
    if os.path.exists(fj_teams_path):
        df_fjt = pd.read_csv(fj_teams_path)
        for t in df_fjt['team_name'].dropna().unique():
            fj_teams.add(t.strip())

    fj_matches_path = os.path.join(DATA_RAW, "fjelstul", "data-csv", "matches.csv")
    if os.path.exists(fj_matches_path):
        df_fjm = pd.read_csv(fj_matches_path, low_memory=False)
        pl_fjm = df_fjm[(df_fjm['tier'] == 1) & (df_fjm['season'] >= 1992)]
        pl_teams_fj = sorted(set(pl_fjm['home_team_name'].dropna().unique()) | set(pl_fjm['away_team_name'].dropna().unique()))
        champ_fjm = df_fjm[(df_fjm['tier'] == 2) & (df_fjm['season'] >= 1992)]
        champ_teams_fj = sorted(set(champ_fjm['home_team_name'].dropna().unique()) | set(champ_fjm['away_team_name'].dropna().unique()))
    else:
        pl_teams_fj, champ_teams_fj = [], []

    extracted['fjelstul'] = {
        "total_distinct": len(fj_teams),
        "pl_teams_1992_present": pl_teams_fj,
        "champ_teams_1992_present": champ_teams_fj,
        "all_extracted": sorted(fj_teams)
    }
    print(f"  ✓ Fjelstul: {len(fj_teams)} unique names (PL: {len(pl_teams_fj)}, Champ: {len(champ_teams_fj)})")

    # 3. Football-Data.co.uk
    print("\n3. Extracting from Football-Data.co.uk...")
    fd_pl_teams = set()
    fd_champ_teams = set()

    for fpath in glob.glob(os.path.join(DATA_RAW, "football_data_co_uk", "*", "E0.csv")):
        try:
            with open(fpath, 'r', encoding='latin1', errors='replace') as f:
                rows = list(csv.reader(f))
            if rows:
                h = rows[0]
                if 'HomeTeam' in h and 'AwayTeam' in h:
                    hi = h.index('HomeTeam')
                    ai = h.index('AwayTeam')
                    for r in rows[1:]:
                        if len(r) > max(hi, ai):
                            if r[hi].strip(): fd_pl_teams.add(r[hi].strip())
                            if r[ai].strip(): fd_pl_teams.add(r[ai].strip())
        except Exception:
            pass

    for fpath in glob.glob(os.path.join(DATA_RAW, "football_data_co_uk", "*", "E1.csv")):
        try:
            with open(fpath, 'r', encoding='latin1', errors='replace') as f:
                rows = list(csv.reader(f))
            if rows:
                h = rows[0]
                if 'HomeTeam' in h and 'AwayTeam' in h:
                    hi = h.index('HomeTeam')
                    ai = h.index('AwayTeam')
                    for r in rows[1:]:
                        if len(r) > max(hi, ai):
                            if r[hi].strip(): fd_champ_teams.add(r[hi].strip())
                            if r[ai].strip(): fd_champ_teams.add(r[ai].strip())
        except Exception:
            pass

    extracted['football_data'] = {
        "pl_teams": sorted(fd_pl_teams),
        "champ_teams": sorted(fd_champ_teams),
        "all_extracted": sorted(fd_pl_teams | fd_champ_teams)
    }
    print(f"  ✓ Football-Data: {len(fd_pl_teams | fd_champ_teams)} unique names (PL: {len(fd_pl_teams)}, Champ: {len(fd_champ_teams)})")

    # 4. OpenFootball
    print("\n4. Extracting from OpenFootball...")
    of_pl_teams = set()
    of_champ_teams = set()
    
    # Use parse_football_txt from inspect_openfootball
    try:
        from collectors.inspect_openfootball import parse_football_txt
        of_dir = os.path.join(DATA_RAW, "openfootball_england")
        for root, dirs, files in os.walk(of_dir):
            for f in files:
                if f.endswith(".txt") and not f.startswith("README") and not f.startswith("TODO"):
                    fpath = os.path.join(root, f)
                    season_folder = os.path.basename(root)
                    fname_lower = f.lower()
                    if "1-premierleague" in fname_lower or "premier" in fname_lower:
                        matches = parse_football_txt(fpath, "Premier League", season_folder)
                        for m in matches:
                            of_pl_teams.add(m["home_team"].strip())
                            of_pl_teams.add(m["away_team"].strip())
                    elif "2-championship" in fname_lower or "championship" in fname_lower:
                        matches = parse_football_txt(fpath, "Championship", season_folder)
                        for m in matches:
                            of_champ_teams.add(m["home_team"].strip())
                            of_champ_teams.add(m["away_team"].strip())
    except Exception as e:
        print(f"  Warning during OpenFootball extraction: {e}")

    extracted['openfootball'] = {
        "pl_teams": sorted(of_pl_teams),
        "champ_teams": sorted(of_champ_teams),
        "all_extracted": sorted(of_pl_teams | of_champ_teams)
    }
    print(f"  ✓ OpenFootball: {len(of_pl_teams | of_champ_teams)} unique names (PL: {len(of_pl_teams)}, Champ: {len(of_champ_teams)})")

    # 5. Vaastav FPL
    print("\n5. Extracting from Vaastav FPL...")
    fpl_teams = set()
    for team_file in glob.glob(os.path.join(DATA_RAW, "vaastav_fpl", "data", "*", "teams.csv")):
        try:
            df_t = pd.read_csv(team_file)
            if 'name' in df_t.columns:
                for n in df_t['name'].dropna().unique():
                    fpl_teams.add(n.strip())
        except Exception:
            pass

    extracted['vaastav_fpl'] = {
        "pl_teams": sorted(fpl_teams),
        "all_extracted": sorted(fpl_teams)
    }
    print(f"  ✓ Vaastav FPL: {len(fpl_teams)} unique PL names")

    # 6. StatsBomb
    print("\n6. Extracting from StatsBomb...")
    sb_teams = set()
    sb_matches_dir = os.path.join(DATA_RAW, "statsbomb", "data", "matches", "2")
    if os.path.exists(sb_matches_dir):
        for mf in glob.glob(os.path.join(sb_matches_dir, "*.json")):
            with open(mf, 'r', encoding='utf-8') as f:
                matches_data = json.load(f)
            for m in matches_data:
                sb_teams.add(m['home_team']['home_team_name'].strip())
                sb_teams.add(m['away_team']['away_team_name'].strip())

    extracted['statsbomb'] = {
        "pl_teams": sorted(sb_teams),
        "all_extracted": sorted(sb_teams)
    }
    print(f"  ✓ StatsBomb: {len(sb_teams)} unique PL names")

    # Save to disk
    out_path = os.path.join(DATA_PROCESSED, "raw_teams_extracted.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2)

    print(f"\nExtracted raw team lists written to: {out_path}")
    return extracted

if __name__ == "__main__":
    extract_teams()
