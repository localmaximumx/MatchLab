"""
Inspect OpenFootball England Database
Analyzes all raw text files across all season directories in data/raw/openfootball_england/
Parses fixtures, matchdays, dates, kickoff times, full-time & half-time scores,
squad rosters, and cross-checks coverage against Fjelstul.
"""

import os
import re
import sys
import glob
import json
import pandas as pd
from datetime import datetime

# Set utf-8 output encoding for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = os.path.join("data", "raw", "openfootball_england")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    "January": 1, "February": 2, "March": 3, "April": 4, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}

def parse_football_txt(file_path, comp_name, season_str):
    """
    Parses a single openfootball .txt match schedule.
    Returns list of parsed match records.
    """
    # Extract start year and end year
    # E.g. "1992-93" -> start_year=1992, end_year=1993
    # "2000-01" -> start_year=2000, end_year=2001
    parts = season_str.split("-")
    if len(parts) == 2:
        start_year = int(parts[0])
        century = (start_year // 100) * 100
        end_suffix = int(parts[1])
        end_year = century + end_suffix
        if end_year < start_year:
            end_year += 100
    else:
        start_year = int(parts[0])
        end_year = start_year + 1

    matches = []
    current_matchday = None
    current_date = None
    current_iso_date = None
    
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        
    for line in lines:
        raw_line = line.strip()
        if not raw_line or raw_line.startswith("#") or raw_line.startswith("="):
            continue
            
        # Matchday detection: e.g. "▪ Matchday 1" or "Matchday 1" or "Round 1"
        m_day = re.search(r'(?:Matchday|Round|Spieltag|Journée)\s+(\d+)', raw_line, re.IGNORECASE)
        if m_day:
            current_matchday = int(m_day.group(1))
            continue
            
        # Date detection: ONLY if line does not contain a scoreline
        # e.g. "Sat Aug 15", "Fri Aug 11 2023", "Sat Aug 15 1992", "[Sat Aug 15]"
        clean_date_line = re.sub(r'[\[\]]', '', raw_line).strip()
        if not re.search(r'\d+[-–:]\d+', clean_date_line):
            m_date = re.match(
                r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?\b\.?\s+([A-Za-z]+)\.?\s+(\d+)(?:\s+(\d{4}))?',
                clean_date_line,
                re.IGNORECASE
            )
            if m_date:
                month_str = m_date.group(1).title()
                day_num = int(m_date.group(2))
                year_override = m_date.group(3)
                
                if month_str in MONTH_MAP:
                    m_num = MONTH_MAP[month_str]
                    if year_override:
                        y_num = int(year_override)
                    else:
                        # In English football, Aug-Dec is start_year, Jan-Jul is end_year
                        y_num = start_year if m_num >= 7 else end_year
                    try:
                        current_iso_date = f"{y_num:04d}-{m_num:02d}-{day_num:02d}"
                        current_date = f"{month_str} {day_num}"
                    except Exception:
                        current_iso_date = None
                continue
            
        # Match line detection
        # Format variations:
        # [time] HomeTeam score [(ht_score)] AwayTeam
        # e.g.: "20:00  Burnley FC               0-3 (0-2)  Manchester City FC"
        # e.g.: "  Arsenal FC               2-4  Norwich City FC"
        # e.g.: "Everton FC  1-1 (0-0)  West Ham United FC"
        # e.g.: "Arsenal FC  postp.  Chelsea FC"
        
        # Check for postponed / cancelled
        if "postp." in raw_line.lower() or "canc." in raw_line.lower():
            m_postp = re.search(r'(?:(\d{1,2}:\d{2})\s+)?([A-Za-z0-9&.\'\-\s]+?)\s+(?:postp\.|canc\.)\s+([A-Za-z0-9&.\'\-\s]+)$', raw_line)
            if m_postp:
                matches.append({
                    "season": season_str,
                    "season_start_year": start_year,
                    "competition": comp_name,
                    "matchday": current_matchday,
                    "date": current_date,
                    "iso_date": current_iso_date,
                    "kickoff_time": m_postp.group(1),
                    "home_team": m_postp.group(2).strip(),
                    "away_team": m_postp.group(3).strip(),
                    "score": None,
                    "home_score": None,
                    "away_score": None,
                    "ht_score": None,
                    "ht_home_score": None,
                    "ht_away_score": None,
                    "status": "postponed"
                })
            continue

        # Standard played match line
        m_match = re.search(
            r'(?:(\d{1,2}:\d{2})\s+)?([A-Za-z0-9&.\'\-\s/]+?)\s+(\d+)[-–:](\d+)(?:\s+\((\d+)[-–:](\d+)\))?\s+([A-Za-z0-9&.\'\-\s/]+)$',
            raw_line
        )
        if m_match:
            time_str = m_match.group(1)
            home_team = m_match.group(2).strip()
            home_score = int(m_match.group(3))
            away_score = int(m_match.group(4))
            ht_home = int(m_match.group(5)) if m_match.group(5) is not None else None
            ht_away = int(m_match.group(6)) if m_match.group(6) is not None else None
            away_team = m_match.group(7).strip()
            
            ht_score_str = f"{ht_home}-{ht_away}" if ht_home is not None else None
            
            matches.append({
                "season": season_str,
                "season_start_year": start_year,
                "competition": comp_name,
                "matchday": current_matchday,
                "date": current_date,
                "iso_date": current_iso_date,
                "kickoff_time": time_str,
                "home_team": home_team,
                "away_team": away_team,
                "score": f"{home_score}-{away_score}",
                "home_score": home_score,
                "away_score": away_score,
                "ht_score": ht_score_str,
                "ht_home_score": ht_home,
                "ht_away_score": ht_away,
                "status": "played"
            })
            
    return matches

def inspect_openfootball():
    print("Starting OpenFootball inspection...")
    results = {
        "dataset_name": "OpenFootball England",
        "repository": "https://github.com/openfootball/england",
        "license": "CC0-1.0 (Public Domain)",
        "download_date": "2026-11-05"
    }
    
    # 1. Discover all season directories
    root_seasons = [d for d in os.listdir(RAW_DIR) if re.match(r'^\d{4}-\d{2}$', d) and os.path.isdir(os.path.join(RAW_DIR, d))]
    archive_paths = glob.glob(os.path.join(RAW_DIR, "archive", "*", "*"))
    archive_seasons = [d for d in archive_paths if os.path.isdir(d)]
    
    all_season_dirs = {}
    for s in root_seasons:
        all_season_dirs[s] = os.path.join(RAW_DIR, s)
    for p in archive_seasons:
        s_name = os.path.basename(p)
        all_season_dirs[s_name] = p
        
    sorted_seasons = sorted(all_season_dirs.keys())
    results["total_season_folders"] = len(sorted_seasons)
    results["seasons_available"] = sorted_seasons
    
    # 2. Parse Premier League across all seasons
    pl_matches_all = []
    pl_seasons_summary = {}
    
    for s_name in sorted_seasons:
        s_dir = all_season_dirs[s_name]
        # Look for premier league file
        candidate_files = [
            "1-premierleague.txt",
            "1-premierleague-full.txt",
            "premierleague.txt",
            "1-division1.txt" # in 1880s/1890s
        ]
        pl_file = None
        for cf in candidate_files:
            target = os.path.join(s_dir, cf)
            if os.path.exists(target):
                pl_file = target
                break
                
        if pl_file:
            m_list = parse_football_txt(pl_file, "Premier League", s_name)
            if m_list:
                pl_matches_all.extend(m_list)
                pl_seasons_summary[s_name] = {
                    "matches_count": len(m_list),
                    "with_dates": sum(1 for m in m_list if m["iso_date"] is not None),
                    "with_times": sum(1 for m in m_list if m["kickoff_time"] is not None),
                    "with_ht_scores": sum(1 for m in m_list if m["ht_score"] is not None),
                    "file_path": os.path.relpath(pl_file, RAW_DIR)
                }
                
    results["premier_league"] = {
        "total_matches_parsed": len(pl_matches_all),
        "seasons_count": len(pl_seasons_summary),
        "seasons": pl_seasons_summary
    }
    
    # 3. Parse Championship / Division 1 (Tier 2) across all seasons
    champ_matches_all = []
    champ_seasons_summary = {}
    
    for s_name in sorted_seasons:
        s_dir = all_season_dirs[s_name]
        candidate_files = [
            "2-championship.txt",
            "2-division1.txt",
            "2-division2.txt"
        ]
        champ_file = None
        for cf in candidate_files:
            target = os.path.join(s_dir, cf)
            if os.path.exists(target):
                champ_file = target
                break
                
        if champ_file:
            m_list = parse_football_txt(champ_file, "Championship", s_name)
            if m_list:
                champ_matches_all.extend(m_list)
                champ_seasons_summary[s_name] = {
                    "matches_count": len(m_list),
                    "with_dates": sum(1 for m in m_list if m["iso_date"] is not None),
                    "with_times": sum(1 for m in m_list if m["kickoff_time"] is not None),
                    "with_ht_scores": sum(1 for m in m_list if m["ht_score"] is not None),
                    "file_path": os.path.relpath(champ_file, RAW_DIR)
                }
                
    results["championship"] = {
        "total_matches_parsed": len(champ_matches_all),
        "seasons_count": len(champ_seasons_summary),
        "seasons": champ_seasons_summary
    }
    
    # 4. Convert PL matches to DataFrame for data quality checks
    pl_df = pd.DataFrame(pl_matches_all)
    champ_df = pd.DataFrame(champ_matches_all)
    
    # Check data quality for Premier League
    if not pl_df.empty:
        pl_dates_pct = round(pl_df["iso_date"].notnull().mean() * 100, 2)
        pl_times_pct = round(pl_df["kickoff_time"].notnull().mean() * 100, 2)
        pl_ht_pct = round(pl_df["ht_score"].notnull().mean() * 100, 2)
        pl_dups = int(pl_df.duplicated(subset=["season", "home_team", "away_team"]).sum())
        
        results["pl_quality"] = {
            "total_matches": len(pl_df),
            "date_coverage_pct": pl_dates_pct,
            "kickoff_time_coverage_pct": pl_times_pct,
            "ht_score_coverage_pct": pl_ht_pct,
            "duplicate_matches": pl_dups,
            "unique_home_teams": int(pl_df["home_team"].nunique()),
            "sample_records": pl_df.head(3).to_dict(orient="records")
        }
        
    if not champ_df.empty:
        champ_dates_pct = round(champ_df["iso_date"].notnull().mean() * 100, 2)
        champ_times_pct = round(champ_df["kickoff_time"].notnull().mean() * 100, 2)
        champ_ht_pct = round(champ_df["ht_score"].notnull().mean() * 100, 2)
        champ_dups = int(champ_df.duplicated(subset=["season", "home_team", "away_team"]).sum())
        
        results["championship_quality"] = {
            "total_matches": len(champ_df),
            "date_coverage_pct": champ_dates_pct,
            "kickoff_time_coverage_pct": champ_times_pct,
            "ht_score_coverage_pct": champ_ht_pct,
            "duplicate_matches": champ_dups,
            "unique_home_teams": int(champ_df["home_team"].nunique()),
            "sample_records": champ_df.head(3).to_dict(orient="records")
        }
        
    # 5. Inspect Squads directories
    squad_files = glob.glob(os.path.join(RAW_DIR, "*", "squads", "*.txt"))
    squad_seasons = set()
    total_player_rows = 0
    sample_players = []
    
    for sf in squad_files:
        # parent directory of squads is season
        s_name = os.path.basename(os.path.dirname(os.path.dirname(sf)))
        squad_seasons.add(s_name)
        with open(sf, "r", encoding="utf-8", errors="replace") as f:
            for l in f:
                l_s = l.strip()
                if l_s and not l_s.startswith("=") and not l_s.startswith("#"):
                    parts = [p.strip() for p in l_s.split(",")]
                    if len(parts) >= 3:
                        total_player_rows += 1
                        if len(sample_players) < 3:
                            sample_players.append({
                                "file": os.path.basename(sf),
                                "raw": l_s
                            })
                            
    results["squads_summary"] = {
        "seasons_with_squads": sorted(list(squad_seasons)),
        "total_squad_files": len(squad_files),
        "total_player_records": total_player_rows,
        "sample_players": sample_players
    }
    
    # 6. Cross-Check with Fjelstul for Premier League
    # Load Fjelstul matches
    fjelstul_path = os.path.join("data", "raw", "fjelstul", "data-csv", "matches.csv")
    if os.path.exists(fjelstul_path) and not pl_df.empty:
        fj_m = pd.read_csv(fjelstul_path, low_memory=False)
        fj_pl = fj_m[fj_m["division"] == "Premier League"]
        
        # Check overlap seasons (e.g. 1992-93 to 2023-24)
        fj_seasons = set(fj_pl["season"].unique())
        op_seasons = set(pl_df["season_start_year"].unique())
        overlap = fj_seasons.intersection(op_seasons)
        
        results["fjelstul_crosscheck"] = {
            "fjelstul_pl_seasons": len(fj_seasons),
            "openfootball_pl_seasons": len(op_seasons),
            "overlapping_seasons": len(overlap),
            "overlap_range": f"{min(overlap)} to {max(overlap)}" if overlap else None,
            "fjelstul_matches_in_overlap": int(len(fj_pl[fj_pl["season"].isin(overlap)])),
            "openfootball_matches_in_overlap": int(len(pl_df[pl_df["season_start_year"].isin(overlap)]))
        }

    # Save summary JSON
    out_json = os.path.join(REPORTS_DIR, "openfootball_inspection_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Inspection complete. Summary saved to {out_json}")
    
    return results

if __name__ == "__main__":
    inspect_openfootball()
