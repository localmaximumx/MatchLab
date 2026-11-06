"""
Inspect StatsBomb Open Data
Fetches the competition catalog, identifies all English league and cup competitions,
downloads and inspects match catalogs, lineups, detailed events, and 360 data schemas.
"""

import os
import sys
import json
import urllib.request
import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://raw.githubusercontent.com/hudl/open-data/master"
RAW_DIR = os.path.join("data", "raw", "statsbomb")
DATA_DIR = os.path.join(RAW_DIR, "data")
REPORTS_DIR = "reports"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "matches"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "lineups"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "events"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "three-sixty"), exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def fetch_json(endpoint_path):
    url = f"{BASE_URL}/{endpoint_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def inspect_statsbomb():
    print("Fetching StatsBomb competitions.json...")
    comps_data = fetch_json("data/competitions.json")
    
    # Save raw competitions.json locally
    with open(os.path.join(DATA_DIR, "competitions.json"), "w", encoding="utf-8") as f:
        json.dump(comps_data, f, indent=2)
        
    comps_df = pd.DataFrame(comps_data)
    
    results = {
        "dataset_name": "StatsBomb Open Data",
        "repository": "https://github.com/statsbomb/open-data (hudl/open-data)",
        "download_date": "2026-11-05",
        "total_competitions_cataloged": len(comps_df)
    }
    
    # Filter for all English competitions
    england_mask = (
        (comps_df["country_name"] == "England") | 
        (comps_df["competition_name"].str.contains("Premier League|Championship|FA Women", case=False, na=False))
    )
    england_comps = comps_df[england_mask].copy()
    
    results["england_competitions"] = england_comps[[
        "competition_id", "season_id", "country_name", "competition_name", 
        "competition_gender", "season_name", "match_available", "match_available_360"
    ]].to_dict(orient="records")
    
    # Specifically inspect Premier League and Championship entries
    pl_entries = england_comps[
        (england_comps["competition_name"].str.contains("Premier League", case=False)) &
        (england_comps["competition_gender"] == "male")
    ]
    
    champ_entries = england_comps[
        england_comps["competition_name"].str.contains("Championship", case=False)
    ]
    
    results["premier_league_entries_count"] = len(pl_entries)
    results["championship_entries_count"] = len(champ_entries)
    
    print(f"Premier League entries found: {len(pl_entries)}")
    print(f"Championship entries found: {len(champ_entries)}")
    
    # Download match catalogs for all English male Premier League / Championship seasons
    pl_matches_all = []
    sample_match_id = None
    
    for _, row in pl_entries.iterrows():
        comp_id = int(row["competition_id"])
        season_id = int(row["season_id"])
        season_name = row["season_name"]
        
        matches_endpoint = f"data/matches/{comp_id}/{season_id}.json"
        print(f"Fetching matches for PL season {season_name} ({matches_endpoint})...")
        try:
            m_data = fetch_json(matches_endpoint)
            # Save raw file
            comp_matches_dir = os.path.join(DATA_DIR, "matches", str(comp_id))
            os.makedirs(comp_matches_dir, exist_ok=True)
            with open(os.path.join(comp_matches_dir, f"{season_id}.json"), "w", encoding="utf-8") as f:
                json.dump(m_data, f, indent=2)
                
            for m in m_data:
                m_info = {
                    "match_id": m.get("match_id"),
                    "match_date": m.get("match_date"),
                    "kickoff": m.get("kickoff"),
                    "competition": m.get("competition", {}).get("competition_name"),
                    "season": m.get("season", {}).get("season_name"),
                    "home_team": m.get("home_team", {}).get("home_team_name"),
                    "away_team": m.get("away_team", {}).get("away_team_name"),
                    "home_score": m.get("home_score"),
                    "away_score": m.get("away_score"),
                    "match_status": m.get("match_status"),
                    "has_360": m.get("match_status_360") is not None
                }
                pl_matches_all.append(m_info)
                if sample_match_id is None:
                    sample_match_id = m.get("match_id")
        except Exception as e:
            print(f"Error fetching matches for {matches_endpoint}: {e}")
            
    results["pl_matches_cataloged"] = len(pl_matches_all)
    results["pl_matches_list"] = pl_matches_all
    
    # Download sample match data (Events, Lineup, and 360 if available)
    if sample_match_id:
        print(f"Inspecting sample match {sample_match_id}...")
        # 1. Lineup
        lineup_endpoint = f"data/lineups/{sample_match_id}.json"
        try:
            lineup_data = fetch_json(lineup_endpoint)
            with open(os.path.join(DATA_DIR, "lineups", f"{sample_match_id}.json"), "w", encoding="utf-8") as f:
                json.dump(lineup_data, f, indent=2)
                
            # Analyze lineup structure
            team_lineup_summary = []
            for team in lineup_data:
                team_lineup_summary.append({
                    "team_name": team.get("team_name"),
                    "players_count": len(team.get("lineup", [])),
                    "sample_player": team.get("lineup", [])[0] if team.get("lineup") else None
                })
            results["sample_lineup"] = {
                "match_id": sample_match_id,
                "teams": team_lineup_summary
            }
        except Exception as e:
            print(f"Error fetching lineup {sample_match_id}: {e}")
            
        # 2. Events
        events_endpoint = f"data/events/{sample_match_id}.json"
        try:
            events_data = fetch_json(events_endpoint)
            with open(os.path.join(DATA_DIR, "events", f"{sample_match_id}.json"), "w", encoding="utf-8") as f:
                json.dump(events_data, f, indent=2)
                
            events_df = pd.DataFrame(events_data)
            event_type_counts = events_df["type"].apply(lambda x: x.get("name") if isinstance(x, dict) else str(x)).value_counts().to_dict()
            
            # Inspect shots and xG specifically
            shots = [e for e in events_data if e.get("type", {}).get("name") == "Shot"]
            shot_sample = []
            for s in shots[:3]:
                shot_sample.append({
                    "minute": s.get("minute"),
                    "second": s.get("second"),
                    "player": s.get("player", {}).get("name"),
                    "team": s.get("team", {}).get("name"),
                    "location": s.get("location"),
                    "statsbomb_xg": s.get("shot", {}).get("statsbomb_xg"),
                    "outcome": s.get("shot", {}).get("outcome", {}).get("name"),
                    "technique": s.get("shot", {}).get("technique", {}).get("name"),
                    "body_part": s.get("shot", {}).get("body_part", {}).get("name"),
                    "freeze_frame_count": len(s.get("shot", {}).get("freeze_frame", [])) if "freeze_frame" in s.get("shot", {}) else 0
                })
                
            results["sample_events"] = {
                "match_id": sample_match_id,
                "total_events_in_match": len(events_data),
                "event_type_breakdown": event_type_counts,
                "total_shots_in_match": len(shots),
                "shot_sample": shot_sample
            }
        except Exception as e:
            print(f"Error fetching events {sample_match_id}: {e}")
            
    # Save summary report JSON
    out_json = os.path.join(REPORTS_DIR, "statsbomb_inspection_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Inspection complete. Summary saved to {out_json}")
    
    return results

if __name__ == "__main__":
    inspect_statsbomb()
