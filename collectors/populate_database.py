"""
Phase 3 - Database Populator & ETL Ingestion Pipeline
Initializes SQLite database schema and populates:
1. competitions & seasons
2. canonical teams & team aliases
3. point deductions
4. matches, match_stats, match_elo_ratings, match_betting_odds (31,178 reconciled matches)
"""

import sys
import os
import sqlite3
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "matchlab.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema", "init_schema.sql")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

def clean_val(v):
    if pd.isna(v) or v is None or v == '' or str(v).strip().lower() in ['nan', 'none', 'null']:
        return None
    return v

def clean_int(v):
    val = clean_val(v)
    if val is None:
        return None
    try:
        return int(float(val))
    except Exception:
        return None

def clean_float(v):
    val = clean_val(v)
    if val is None:
        return None
    try:
        return float(val)
    except Exception:
        return None

def clean_str(v):
    val = clean_val(v)
    if val is None:
        return None
    return str(val).strip()

def populate_database():
    print("=" * 80)
    print("PHASE 3 - POPULATING MATCHLAB RELATIONAL DATABASE")
    print(f"Database Path: {DB_PATH}")
    print("=" * 80)

    # Remove existing db file if fresh build
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed existing database for a clean build.")
        except Exception as e:
            print(f"Note: Could not remove existing db ({e}), recreating tables.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Initialize Schema
    print("\n1. Applying DDL Schema from schema/init_schema.sql...")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        ddl = f.read()
    cursor.executescript(ddl)
    print("✓ Schema initialized successfully.")

    # 2. Insert Competitions
    print("\n2. Inserting Competitions...")
    competitions = [
        ('premier-league', 'Premier League', 'PL', 'England', 1),
        ('championship', 'EFL Championship', 'EFLC', 'England', 2)
    ]
    cursor.executemany("""
        INSERT INTO competitions (competition_id, name, code, country, tier)
        VALUES (?, ?, ?, ?, ?)
    """, competitions)
    print(f"✓ Inserted {len(competitions)} competitions.")

    # 3. Insert Canonical Teams
    print("\n3. Inserting Canonical Teams...")
    df_teams = pd.read_csv(os.path.join(PROCESSED_DIR, "canonical_teams.csv"))
    teams_data = []
    for _, r in df_teams.iterrows():
        teams_data.append((
            clean_str(r['team_id']),
            clean_str(r['canonical_name']),
            clean_str(r['common_name']),
            clean_str(r['fjelstul_team_id']),
            clean_str(r['country']),
            1 if r['is_premier_league_historical'] else 0,
            1 if r['is_championship_historical'] else 0
        ))
    cursor.executemany("""
        INSERT INTO teams (team_id, canonical_name, common_name, fjelstul_team_id, country, is_premier_league_historical, is_championship_historical)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, teams_data)
    print(f"✓ Inserted {len(teams_data)} canonical teams.")

    # 4. Insert Team Aliases
    print("\n4. Inserting Team Aliases...")
    df_aliases = pd.read_csv(os.path.join(PROCESSED_DIR, "team_aliases.csv"))
    aliases_data = []
    for _, r in df_aliases.iterrows():
        aliases_data.append((
            clean_str(r['team_id']),
            clean_str(r['alias_raw']),
            clean_str(r['normalized_alias']),
            clean_str(r['source'])
        ))
    cursor.executemany("""
        INSERT OR IGNORE INTO team_aliases (team_id, alias_raw, normalized_alias, source)
        VALUES (?, ?, ?, ?)
    """, aliases_data)
    print(f"✓ Inserted {len(aliases_data)} team aliases.")

    # 5. Insert Point Deductions
    print("\n5. Inserting Historical Point Deductions...")
    deductions_path = os.path.join(RAW_DIR, "england_football_results", "EnglishTeamPointDeductions.csv")
    with open(os.path.join(PROCESSED_DIR, "team_dictionary.json"), "r", encoding="utf-8") as f:
        team_lookup = json.load(f)

    def resolve_team_id(t_name):
        if not t_name: return None
        c = t_name.lower().replace("'", "").replace(".", "").replace("-", " ")
        c = " ".join(c.split())
        if c in team_lookup: return team_lookup[c]["team_id"]
        if t_name.lower() in team_lookup: return team_lookup[t_name.lower()]["team_id"]
        return None

    df_ded = pd.read_csv(deductions_path)
    ded_data = []
    for _, r in df_ded.iterrows():
        tid = resolve_team_id(str(r['Team']))
        if tid:
            ded_data.append((
                clean_str(r['Season']),
                clean_str(r['Date']),
                tid,
                clean_int(r['Pts_deducted']),
                clean_str(r['Notes'])
            ))
    cursor.executemany("""
        INSERT INTO point_deductions (season_name, deduction_date, team_id, points_deducted, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ded_data)
    print(f"✓ Inserted {len(ded_data)} verified point deductions.")

    # 6. Load Reconciled Matches & Insert Seasons & Matches
    print("\n6. Ingesting Reconciled Matches (Premier League & Championship)...")
    
    tier_files = [
        ('premier-league', 1, os.path.join(PROCESSED_DIR, "reconciled_premier_league.csv")),
        ('championship', 2, os.path.join(PROCESSED_DIR, "reconciled_championship.csv"))
    ]

    seasons_inserted = set()
    total_matches = 0
    total_stats = 0
    total_elo = 0
    total_odds = 0

    for comp_id, tier, fpath in tier_files:
        print(f"\nProcessing {comp_id} from {os.path.basename(fpath)}...")
        df = pd.read_csv(fpath, low_memory=False)
        print(f"  Rows to ingest: {len(df):,}")

        # Ingest Seasons
        for s_name in df['Season'].dropna().unique():
            parts = str(s_name).split('/')
            start_y = int(parts[0])
            end_y = int(parts[1]) if len(parts) > 1 else start_y + 1
            season_slug = f"{comp_id}_{start_y}-{end_y}"
            
            if season_slug not in seasons_inserted:
                cursor.execute("""
                    INSERT OR IGNORE INTO seasons (season_id, competition_id, season_name, start_year, end_year)
                    VALUES (?, ?, ?, ?, ?)
                """, (season_slug, comp_id, s_name, start_y, end_y))
                seasons_inserted.add(season_slug)

        # Batch prepare tables
        matches_batch = []
        stats_batch = []
        elo_batch = []
        odds_batch = []

        for _, r in df.iterrows():
            s_name = str(r['Season'])
            parts = s_name.split('/')
            start_y = int(parts[0])
            end_y = int(parts[1]) if len(parts) > 1 else start_y + 1
            season_slug = f"{comp_id}_{start_y}-{end_y}"

            m_id = str(r['match_key'])
            m_date = clean_str(r['match_date'])
            time_str = clean_str(r['kickoff_time'])
            h_id = clean_str(r['home_team_id'])
            a_id = clean_str(r['away_team_id'])
            h_name = clean_str(r['home_team_name'])
            a_name = clean_str(r['away_team_name'])
            fthg = clean_int(r['full_time_home_goals'])
            ftag = clean_int(r['full_time_away_goals'])
            ftr = clean_str(r['full_time_result'])
            hthg = clean_int(r['half_time_home_goals'])
            htag = clean_int(r['half_time_away_goals'])
            htr = clean_str(r['half_time_result'])
            ref = clean_str(r['referee'])

            # Core match
            matches_batch.append((
                m_id, comp_id, season_slug, s_name, m_date, time_str,
                h_id, a_id, h_name, a_name,
                fthg, ftag, ftr,
                hthg, htag, htr,
                ref, 'reconciled_elvidge_football_data'
            ))

            # Match Stats
            hs = clean_int(r.get('home_shots'))
            as_ = clean_int(r.get('away_shots'))
            hst = clean_int(r.get('home_shots_on_target'))
            ast = clean_int(r.get('away_shots_on_target'))
            hc = clean_int(r.get('home_corners'))
            ac = clean_int(r.get('away_corners'))
            hf = clean_int(r.get('home_fouls'))
            af = clean_int(r.get('away_fouls'))
            hy = clean_int(r.get('home_yellow_cards'))
            ay = clean_int(r.get('away_yellow_cards'))
            hr = clean_int(r.get('home_red_cards'))
            ar = clean_int(r.get('away_red_cards'))

            if hs is not None or hst is not None or hc is not None:
                stats_batch.append((
                    m_id, hs, as_, hst, ast, hc, ac, hf, af, hy, ay, hr, ar
                ))

            # Elo Ratings
            helo_b = clean_float(r.get('home_elo_before'))
            aelo_b = clean_float(r.get('away_elo_before'))
            ehw = clean_float(r.get('elo_home_win_prob'))
            ed = clean_float(r.get('elo_draw_prob'))
            eaw = clean_float(r.get('elo_away_win_prob'))
            helo_a = clean_float(r.get('home_elo_after'))
            aelo_a = clean_float(r.get('away_elo_after'))

            if helo_b is not None:
                elo_batch.append((
                    m_id, helo_b, aelo_b, ehw, ed, eaw, helo_a, aelo_a
                ))

            # Betting Odds
            b365h = clean_float(r.get('B365H'))
            b365d = clean_float(r.get('B365D'))
            b365a = clean_float(r.get('B365A'))
            psh = clean_float(r.get('PSH'))
            psd = clean_float(r.get('PSD'))
            psa = clean_float(r.get('PSA'))
            psch = clean_float(r.get('PSCH'))
            pscd = clean_float(r.get('PSCD'))
            psca = clean_float(r.get('PSCA'))
            b365ch = clean_float(r.get('B365CH'))
            b365cd = clean_float(r.get('B365CD'))
            b365ca = clean_float(r.get('B365CA'))
            avgh = clean_float(r.get('AvgH'))
            avgd = clean_float(r.get('AvgD'))
            avga = clean_float(r.get('AvgA'))
            maxh = clean_float(r.get('MaxH'))
            maxd = clean_float(r.get('MaxD'))
            maxa = clean_float(r.get('MaxA'))
            avg_o25 = clean_float(r.get('Avg>2.5'))
            avg_u25 = clean_float(r.get('Avg<2.5'))
            ahh = clean_float(r.get('AHh'))
            avg_ahh = clean_float(r.get('AvgAHH'))
            avg_aha = clean_float(r.get('AvgAHA'))

            if b365h is not None or psh is not None or avgh is not None or psch is not None:
                odds_batch.append((
                    m_id,
                    b365h, b365d, b365a,
                    psh, psd, psa,
                    psch, pscd, psca,
                    b365ch, b365cd, b365ca,
                    avgh, avgd, avga,
                    maxh, maxd, maxa,
                    avg_o25, avg_u25,
                    ahh, avg_ahh, avg_aha
                ))

        # Insert matches batch
        cursor.executemany("""
            INSERT OR REPLACE INTO matches (
                match_id, competition_id, season_id, season_name, match_date, kickoff_time,
                home_team_id, away_team_id, home_team_name, away_team_name,
                full_time_home_goals, full_time_away_goals, full_time_result,
                half_time_home_goals, half_time_away_goals, half_time_result,
                referee, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, matches_batch)
        total_matches += len(matches_batch)

        # Insert stats batch
        cursor.executemany("""
            INSERT OR REPLACE INTO match_stats (
                match_id, home_shots, away_shots, home_shots_on_target, away_shots_on_target,
                home_corners, away_corners, home_fouls, away_fouls,
                home_yellow_cards, away_yellow_cards, home_red_cards, away_red_cards
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, stats_batch)
        total_stats += len(stats_batch)

        # Insert elo batch
        cursor.executemany("""
            INSERT OR REPLACE INTO match_elo_ratings (
                match_id, home_elo_before, away_elo_before,
                elo_home_win_prob, elo_draw_prob, elo_away_win_prob,
                home_elo_after, away_elo_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, elo_batch)
        total_elo += len(elo_batch)

        # Insert odds batch
        cursor.executemany("""
            INSERT OR REPLACE INTO match_betting_odds (
                match_id,
                b365_home, b365_draw, b365_away,
                pinnacle_home, pinnacle_draw, pinnacle_away,
                pinnacle_close_home, pinnacle_close_draw, pinnacle_close_away,
                b365_close_home, b365_close_draw, b365_close_away,
                market_avg_home, market_avg_draw, market_avg_away,
                market_max_home, market_max_draw, market_max_away,
                market_avg_over_2_5, market_avg_under_2_5,
                asian_handicap_line, market_avg_handicap_home, market_avg_handicap_away
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, odds_batch)
        total_odds += len(odds_batch)

        conn.commit()
        print(f"  ✓ Ingested {len(matches_batch):,} matches ({len(stats_batch):,} with stats, {len(elo_batch):,} with Elo, {len(odds_batch):,} with odds)")

    # 7. Summary
    print("\n" + "=" * 80)
    print("DATABASE INGESTION SUMMARY:")
    print("=" * 80)
    print(f"Competitions:       2")
    print(f"Seasons:            {len(seasons_inserted)}")
    print(f"Canonical Teams:    {len(teams_data):,}")
    print(f"Team Aliases:       {len(aliases_data):,}")
    print(f"Point Deductions:   {len(ded_data):,}")
    print(f"Matches:            {total_matches:,}")
    print(f"Match Stats:        {total_stats:,}")
    print(f"Elo Ratings:        {total_elo:,}")
    print(f"Betting Odds:       {total_odds:,}")

    db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"Final SQLite Database Size: {db_size_mb:.2f} MB")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    populate_database()
