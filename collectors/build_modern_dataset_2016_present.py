"""
Build Modern Master Dataset (2016/17 to 2026/27)
Extracts, harmonizes, enriches, and validates:
1. All 9,578 matches from Premier League & EFL Championship (2016/17 - 2026/27).
2. All 257,783 player gameweek records from Vaastav FPL (2016/17 - 2026/27).
3. Computes market implied probabilities, bookmaker overrounds, and ML target columns.
4. Generates match-level squad aggregations (lineup market value, players fielded).
5. Exports:
   - data/processed/matches_modern_2016_present.csv
   - data/processed/matches_modern_2016_present.parquet
   - data/processed/player_gameweeks_2016_present.parquet
   - Table 'matches_modern' and 'player_gameweeks_modern' in data/matchlab.db
"""

import sys
import os
import sqlite3
import json
import glob
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")
DB_PATH = os.path.join(DATA_DIR, "matchlab.db")
FPL_DIR = os.path.join(RAW_DIR, "vaastav_fpl", "data")

def clean_str(v):
    if pd.isna(v) or v is None or str(v).strip().lower() in ['nan', 'none', 'null', '']:
        return None
    return str(v).strip()

def clean_float(v):
    if pd.isna(v) or v is None or str(v).strip().lower() in ['nan', 'none', 'null', '']:
        return None
    try:
        return float(v)
    except Exception:
        return None

def clean_int(v):
    if pd.isna(v) or v is None or str(v).strip().lower() in ['nan', 'none', 'null', '']:
        return None
    try:
        return int(float(v))
    except Exception:
        return None

def compute_implied_probs(h_odds, d_odds, a_odds):
    """
    Computes overround and normalized implied probabilities (removing vigorish proportionally).
    """
    if h_odds is None or d_odds is None or a_odds is None or h_odds <= 1.0 or d_odds <= 1.0 or a_odds <= 1.0:
        return None, None, None, None
    raw_h = 1.0 / h_odds
    raw_d = 1.0 / d_odds
    raw_a = 1.0 / a_odds
    sum_raw = raw_h + raw_d + raw_a
    overround = sum_raw - 1.0
    return round(raw_h / sum_raw, 5), round(raw_d / sum_raw, 5), round(raw_a / sum_raw, 5), round(overround, 5)

def build_modern_matches():
    print("=" * 80)
    print("STEP 1: EXTRACTING & ENRICHING MODERN MATCHES (2016/17 - PRESENT)")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        m.match_id,
        m.competition_id,
        c.name AS competition_name,
        m.season_id,
        m.season_name,
        s.start_year AS season_start_year,
        m.match_date,
        m.kickoff_time,
        m.home_team_id,
        m.home_team_name,
        m.away_team_id,
        m.away_team_name,
        m.full_time_home_goals,
        m.full_time_away_goals,
        m.full_time_result,
        m.half_time_home_goals,
        m.half_time_away_goals,
        m.half_time_result,
        m.referee,
        -- Match Stats
        ms.home_shots,
        ms.away_shots,
        ms.home_shots_on_target,
        ms.away_shots_on_target,
        ms.home_corners,
        ms.away_corners,
        ms.home_fouls,
        ms.away_fouls,
        ms.home_yellow_cards,
        ms.away_yellow_cards,
        ms.home_red_cards,
        ms.away_red_cards,
        -- Elo Ratings
        me.home_elo_before,
        me.away_elo_before,
        me.elo_home_win_prob,
        me.elo_draw_prob,
        me.elo_away_win_prob,
        me.home_elo_after,
        me.away_elo_after,
        -- Betting Odds
        bo.b365_home,
        bo.b365_draw,
        bo.b365_away,
        bo.pinnacle_home,
        bo.pinnacle_draw,
        bo.pinnacle_away,
        bo.pinnacle_close_home,
        bo.pinnacle_close_draw,
        bo.pinnacle_close_away,
        bo.b365_close_home,
        bo.b365_close_draw,
        bo.b365_close_away,
        bo.market_avg_home,
        bo.market_avg_draw,
        bo.market_avg_away,
        bo.market_max_home,
        bo.market_max_draw,
        bo.market_max_away,
        bo.market_avg_over_2_5,
        bo.market_avg_under_2_5,
        bo.asian_handicap_line,
        bo.market_avg_handicap_home,
        bo.market_avg_handicap_away
    FROM matches m
    JOIN competitions c ON m.competition_id = c.competition_id
    JOIN seasons s ON m.season_id = s.season_id
    LEFT JOIN match_stats ms ON m.match_id = ms.match_id
    LEFT JOIN match_elo_ratings me ON m.match_id = me.match_id
    LEFT JOIN match_betting_odds bo ON m.match_id = bo.match_id
    WHERE m.season_name >= '2016/2017'
    ORDER BY m.match_date ASC, m.kickoff_time ASC, m.match_id ASC;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Loaded {len(df):,} modern matches from database.")
    print(f"Premier League: {len(df[df['competition_id'] == 'premier-league']):,}")
    print(f"Championship:   {len(df[df['competition_id'] == 'championship']):,}")

    # Add Analytical & Target Columns
    df['target_home_win'] = (df['full_time_result'] == 'H').astype(int)
    df['target_draw'] = (df['full_time_result'] == 'D').astype(int)
    df['target_away_win'] = (df['full_time_result'] == 'A').astype(int)
    df['target_total_goals'] = df['full_time_home_goals'] + df['full_time_away_goals']
    df['target_over_2_5'] = (df['target_total_goals'] > 2.5).astype(int)
    df['target_btts'] = ((df['full_time_home_goals'] > 0) & (df['full_time_away_goals'] > 0)).astype(int)
    df['target_goal_difference'] = df['full_time_home_goals'] - df['full_time_away_goals']

    # Elo Difference
    df['elo_difference'] = df['home_elo_before'] - df['away_elo_before']

    # Implied Probabilities & Overrounds
    b365_impl = [compute_implied_probs(h, d, a) for h, d, a in zip(df['b365_home'], df['b365_draw'], df['b365_away'])]
    df['b365_implied_home_prob'] = [x[0] for x in b365_impl]
    df['b365_implied_draw_prob'] = [x[1] for x in b365_impl]
    df['b365_implied_away_prob'] = [x[2] for x in b365_impl]
    df['b365_overround'] = [x[3] for x in b365_impl]

    pin_impl = [compute_implied_probs(h, d, a) for h, d, a in zip(df['pinnacle_home'], df['pinnacle_draw'], df['pinnacle_away'])]
    df['pinnacle_implied_home_prob'] = [x[0] for x in pin_impl]
    df['pinnacle_implied_draw_prob'] = [x[1] for x in pin_impl]
    df['pinnacle_implied_away_prob'] = [x[2] for x in pin_impl]
    df['pinnacle_overround'] = [x[3] for x in pin_impl]

    pin_c_impl = [compute_implied_probs(h, d, a) for h, d, a in zip(df['pinnacle_close_home'], df['pinnacle_close_draw'], df['pinnacle_close_away'])]
    df['pinnacle_close_implied_home_prob'] = [x[0] for x in pin_c_impl]
    df['pinnacle_close_implied_draw_prob'] = [x[1] for x in pin_c_impl]
    df['pinnacle_close_implied_away_prob'] = [x[2] for x in pin_c_impl]
    df['pinnacle_close_overround'] = [x[3] for x in pin_c_impl]

    return df

def build_player_gameweeks():
    print("\n" + "=" * 80)
    print("STEP 2: HARMONIZING PLAYER-GAMEWEEK DATA (2016/17 - PRESENT)")
    print("=" * 80)

    with open(os.path.join(PROCESSED_DIR, "team_dictionary.json"), "r", encoding="utf-8") as f:
        team_dict = json.load(f)

    def resolve_team(name):
        if not name or pd.isna(name):
            return None
        s = str(name).strip()
        k1 = s.lower()
        k2 = k1.replace("'", "").replace(".", "").replace("-", " ")
        k2 = " ".join(k2.split())
        if k1 in team_dict:
            return team_dict[k1]['team_id']
        if k2 in team_dict:
            return team_dict[k2]['team_id']
        return None

    # Load master team lists
    master_teams_df = pd.read_csv(os.path.join(FPL_DIR, "master_team_list.csv"))
    master_team_map = {}
    for _, r in master_teams_df.iterrows():
        s = r['season']
        tid_int = int(r['team'])
        tname = r['team_name']
        canon_id = resolve_team(tname)
        master_team_map[(s, tid_int)] = (canon_id, tname)

    # Season team maps for recent seasons
    for s in ['2024-25', '2025-26', '2026-27']:
        tp = os.path.join(FPL_DIR, s, "teams.csv")
        if os.path.exists(tp):
            df_t = pd.read_csv(tp)
            for _, r in df_t.iterrows():
                tid_int = int(r['id'])
                tname = r['name']
                canon_id = resolve_team(tname)
                master_team_map[(s, tid_int)] = (canon_id, tname)

    # Position map helper
    pos_map = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}

    seasons = [d for d in os.listdir(FPL_DIR) if os.path.isdir(os.path.join(FPL_DIR, d)) and '-' in d]
    all_player_rows = []

    total_gw_files = 0
    for s in sorted(seasons):
        s_canonical = f"{s[:4]}/{int(s[:4])+1}"
        s_dir = os.path.join(FPL_DIR, s)
        gw_path = os.path.join(s_dir, "gws", "merged_gw.csv")
        if not os.path.exists(gw_path):
            continue

        total_gw_files += 1
        # Read players_raw for element_type / team if early season
        players_raw_path = os.path.join(s_dir, "players_raw.csv")
        player_info = {}
        if os.path.exists(players_raw_path):
            try:
                df_pr = pd.read_csv(players_raw_path, encoding='latin1')
                for _, pr in df_pr.iterrows():
                    pid = pr['id']
                    el_type = pr.get('element_type')
                    p_pos = pos_map.get(el_type, 'UNK')
                    p_team_int = pr.get('team')
                    player_info[pid] = {
                        'position': p_pos,
                        'team_int': int(p_team_int) if pd.notna(p_team_int) else None
                    }
            except Exception as e:
                print(f"Warning reading players_raw for {s}: {e}")

        # Read merged_gw
        try:
            df_gw = pd.read_csv(gw_path, encoding='utf-8', low_memory=False)
        except Exception:
            df_gw = pd.read_csv(gw_path, encoding='latin1', low_memory=False)

        print(f"  Ingesting {s} ({s_canonical}): {len(df_gw):,} player records...")

        for _, row in df_gw.iterrows():
            pid = clean_int(row.get('element'))
            pname = clean_str(row.get('name'))
            gw_round = clean_int(row.get('round'))
            ko_time = clean_str(row.get('kickoff_time'))
            was_home = bool(row.get('was_home')) if pd.notna(row.get('was_home')) else None

            # Resolve team
            team_val = row.get('team')
            team_canon = None
            team_disp = None
            if pd.notna(team_val):
                # Could be string or int
                if isinstance(team_val, str) and not team_val.isdigit():
                    team_canon = resolve_team(team_val)
                    team_disp = team_val
                else:
                    tid_int = int(float(team_val))
                    if (s, tid_int) in master_team_map:
                        team_canon, team_disp = master_team_map[(s, tid_int)]
            elif pid in player_info and player_info[pid]['team_int'] is not None:
                tid_int = player_info[pid]['team_int']
                if (s, tid_int) in master_team_map:
                    team_canon, team_disp = master_team_map[(s, tid_int)]

            # Resolve opponent team
            opp_val = row.get('opponent_team')
            opp_canon = None
            opp_disp = None
            if pd.notna(opp_val):
                try:
                    opp_int = int(float(opp_val))
                    if (s, opp_int) in master_team_map:
                        opp_canon, opp_disp = master_team_map[(s, opp_int)]
                except Exception:
                    opp_canon = resolve_team(opp_val)
                    opp_disp = str(opp_val)

            # Position
            pos = clean_str(row.get('position'))
            if not pos and pid in player_info:
                pos = player_info[pid]['position']

            # Metrics
            mins = clean_int(row.get('minutes')) or 0
            goals = clean_int(row.get('goals_scored')) or 0
            assists = clean_int(row.get('assists')) or 0
            clean_sheets = clean_int(row.get('clean_sheets')) or 0
            goals_conceded = clean_int(row.get('goals_conceded')) or 0
            own_goals = clean_int(row.get('own_goals')) or 0
            pens_missed = clean_int(row.get('penalties_missed')) or 0
            pens_saved = clean_int(row.get('penalties_saved')) or 0
            yellows = clean_int(row.get('yellow_cards')) or 0
            reds = clean_int(row.get('red_cards')) or 0
            saves = clean_int(row.get('saves')) or 0

            # xG & Expected stats
            xg = clean_float(row.get('expected_goals'))
            xa = clean_float(row.get('expected_assists'))
            xgi = clean_float(row.get('expected_goal_involvements'))
            xgc = clean_float(row.get('expected_goals_conceded'))

            # ICT & Value
            ict = clean_float(row.get('ict_index'))
            influence = clean_float(row.get('influence'))
            creativity = clean_float(row.get('creativity'))
            threat = clean_float(row.get('threat'))
            val = clean_float(row.get('value'))
            price = round(val / 10.0, 1) if val is not None else None
            transfers_balance = clean_int(row.get('transfers_balance'))
            selected = clean_int(row.get('selected'))
            total_points = clean_int(row.get('total_points')) or 0

            all_player_rows.append({
                'season_name': s_canonical,
                'gameweek': gw_round,
                'kickoff_time': ko_time,
                'match_date': ko_time[:10] if ko_time else None,
                'player_id': pid,
                'player_name': pname,
                'position': pos,
                'team_id': team_canon,
                'team_name': team_disp,
                'opponent_team_id': opp_canon,
                'opponent_team_name': opp_disp,
                'was_home': was_home,
                'minutes': mins,
                'goals_scored': goals,
                'assists': assists,
                'clean_sheets': clean_sheets,
                'goals_conceded': goals_conceded,
                'own_goals': own_goals,
                'penalties_missed': pens_missed,
                'penalties_saved': pens_saved,
                'yellow_cards': yellows,
                'red_cards': reds,
                'saves': saves,
                'expected_goals': xg,
                'expected_assists': xa,
                'expected_goal_involvements': xgi,
                'expected_goals_conceded': xgc,
                'ict_index': ict,
                'influence': influence,
                'creativity': creativity,
                'threat': threat,
                'player_price_m': price,
                'transfers_balance': transfers_balance,
                'selected_by_percent': selected,
                'total_points': total_points
            })

    df_players = pd.DataFrame(all_player_rows)
    print(f"\n✓ Successfully harmonized {len(df_players):,} player gameweek rows across {total_gw_files} seasons.")
    return df_players

def aggregate_player_stats_to_matches(df_matches, df_players):
    print("\n" + "=" * 80)
    print("STEP 3: COMPUTING SQUAD & LINEUP AGGREGATIONS FOR PREMIER LEAGUE")
    print("=" * 80)

    # Filter to players who played (minutes > 0)
    df_active = df_players[df_players['minutes'] > 0].copy()

    # Pre-index player matches by (match_date, team_id)
    # Each match has a home team and away team on a specific date
    print("Aggregating active player minutes, squad values, and offensive output...")
    
    # Group by (season_name, match_date, team_id)
    team_match_grp = df_active.groupby(['season_name', 'match_date', 'team_id']).agg(
        players_fielded=('player_id', 'count'),
        total_lineup_value=('player_price_m', 'sum'),
        total_xg=('expected_goals', 'sum'),
        total_xa=('expected_assists', 'sum'),
        total_ict=('ict_index', 'sum')
    ).reset_index()

    team_match_dict = {}
    for _, r in team_match_grp.iterrows():
        key = (r['season_name'], r['match_date'], r['team_id'])
        team_match_dict[key] = {
            'players_fielded': int(r['players_fielded']),
            'total_lineup_value': round(float(r['total_lineup_value']), 1) if pd.notna(r['total_lineup_value']) else None,
            'total_xg': round(float(r['total_xg']), 2) if pd.notna(r['total_xg']) else None,
            'total_xa': round(float(r['total_xa']), 2) if pd.notna(r['total_xa']) else None,
            'total_ict': round(float(r['total_ict']), 1) if pd.notna(r['total_ict']) else None,
        }

    # Map to matches
    home_fielded = []
    away_fielded = []
    home_val = []
    away_val = []
    home_xg = []
    away_xg = []

    for _, row in df_matches.iterrows():
        if row['competition_id'] != 'premier-league':
            home_fielded.append(None)
            away_fielded.append(None)
            home_val.append(None)
            away_val.append(None)
            home_xg.append(None)
            away_xg.append(None)
            continue

        s = row['season_name']
        d = row['match_date']
        ht = row['home_team_id']
        at = row['away_team_id']

        h_stat = team_match_dict.get((s, d, ht))
        a_stat = team_match_dict.get((s, d, at))

        home_fielded.append(h_stat['players_fielded'] if h_stat else None)
        away_fielded.append(a_stat['players_fielded'] if a_stat else None)
        home_val.append(h_stat['total_lineup_value'] if h_stat else None)
        away_val.append(a_stat['total_lineup_value'] if a_stat else None)
        home_xg.append(h_stat['total_xg'] if h_stat else None)
        away_xg.append(a_stat['total_xg'] if a_stat else None)

    df_matches['home_players_fielded'] = home_fielded
    df_matches['away_players_fielded'] = away_fielded
    df_matches['home_lineup_value_m'] = home_val
    df_matches['away_lineup_value_m'] = away_val
    df_matches['home_squad_xg'] = home_xg
    df_matches['away_squad_xg'] = away_xg

    pl_cov = df_matches[df_matches['competition_id'] == 'premier-league']['home_lineup_value_m'].notna().mean()
    print(f"✓ Premier League Squad Aggregation Coverage: {pl_cov*100:.1f}%")

    return df_matches

def save_and_persist(df_matches, df_players):
    print("\n" + "=" * 80)
    print("STEP 4: SAVING UNIFIED MODERN DATASETS")
    print("=" * 80)

    # 1. Matches CSV & Parquet
    matches_csv = os.path.join(PROCESSED_DIR, "matches_modern_2016_present.csv")
    matches_parquet = os.path.join(PROCESSED_DIR, "matches_modern_2016_present.parquet")
    print(f"Exporting modern matches to CSV: {matches_csv}...")
    df_matches.to_csv(matches_csv, index=False, encoding='utf-8')
    print(f"Exporting modern matches to Parquet: {matches_parquet}...")
    df_matches.to_parquet(matches_parquet, index=False)

    # 2. Player Gameweeks Parquet
    players_parquet = os.path.join(PROCESSED_DIR, "player_gameweeks_2016_present.parquet")
    print(f"Exporting player gameweeks to Parquet: {players_parquet}...")
    df_players.to_parquet(players_parquet, index=False)

    # 3. Write dedicated tables into SQLite
    print(f"Updating SQLite database {DB_PATH} with dedicated modern tables...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    df_matches.to_sql('matches_modern_2016_present', conn, if_exists='replace', index=False)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mod_mdate ON matches_modern_2016_present(match_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mod_comp ON matches_modern_2016_present(competition_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mod_season ON matches_modern_2016_present(season_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mod_home ON matches_modern_2016_present(home_team_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mod_away ON matches_modern_2016_present(away_team_id);")

    conn.commit()
    conn.close()
    print("✓ SQLite tables and indexes updated successfully.")

    print("\n" + "=" * 80)
    print("DATASET GENERATION SUMMARY:")
    print(f"Total Matches:            {len(df_matches):,}")
    print(f"Premier League Matches:   {len(df_matches[df_matches['competition_id'] == 'premier-league']):,}")
    print(f"Championship Matches:     {len(df_matches[df_matches['competition_id'] == 'championship']):,}")
    print(f"Total Columns in Matches: {len(df_matches.columns)}")
    print(f"Total Player Records:     {len(df_players):,}")
    print(f"Distinct Players:         {df_players['player_id'].nunique():,}")
    print(f"Unique Teams Tracked:     {df_matches['home_team_id'].nunique()}")
    print("=" * 80)

if __name__ == '__main__':
    df_m = build_modern_matches()
    df_p = build_player_gameweeks()
    df_m_agg = aggregate_player_stats_to_matches(df_m, df_p)
    save_and_persist(df_m_agg, df_p)
