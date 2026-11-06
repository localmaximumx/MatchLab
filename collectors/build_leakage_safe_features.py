"""
MatchLab Phase 4: Leakage-Safe Pre-Match Feature Generation Pipeline (Upgraded)
Prediction Horizon: Strict 24 Hours Before Kickoff (T-24h)

Enforces strict temporal integrity & forensic precision:
1. Every historical feature is computed strictly using information finalized before:
   prediction_cutoff = kickoff_timestamp - 24 hours
2. Current match in-match box-scores and scores are strictly excluded from pre-match features.
3. Rolling team form (last 3, 5, 10 matches) is calculated using team-centric histories with match_end <= cutoff.
4. Venue-specific rolling features (last 3, 5 matches) are calculated similarly.
5. In-match player minutes and fielded lineup aggregations are completely eliminated.
6. Player True Team Resolution: Eliminates retroactive terminal-season club labeling by matching each
   observation to official fixture participants (resolves 1,080 transfer lookahead anomalies).
7. Strict Player Match Completion: Enforces match_end_ts <= prediction_cutoff for player features,
   eliminating the 62 boundary instances where matches were in-progress at cutoff.
8. Excludes inferred Bet365 odds for Match 2450 from strict odds features (set to NaN).
9. Classifies full dataset into Tier 1 (7,922 verified exact) and Tier 2 (1,656 safe assumptions).
10. Exports both complete master dataset (9,578 rows) and primary Tier 1 dataset (7,922 rows).

Outputs:
- data/processed/matches_prematch_24h_features.parquet (9,578 matches)
- data/processed/matches_prematch_24h_features.csv
- data/processed/matches_prematch_24h_tier1.parquet (7,922 matches)
- data/processed/matches_prematch_24h_tier1.csv
- Table 'matches_prematch_24h' and View 'matches_prematch_24h_tier1' in data/matchlab.db
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "data_integration")

os.makedirs(REPORTS_DIR, exist_ok=True)

def build_leakage_safe_dataset():
    print("=" * 80)
    print("MATCHLAB: BUILDING LEAKAGE-SAFE PRE-MATCH (T-24H) FEATURE DATASET (UPGRADED)")
    print("=" * 80)

    # 1. Load Modern Matches & Player Gameweeks
    matches_path = os.path.join(PROCESSED_DIR, "matches_modern_2016_present.parquet")
    players_path = os.path.join(PROCESSED_DIR, "player_gameweeks_2016_present.parquet")

    df_matches = pd.read_parquet(matches_path)
    df_players = pd.read_parquet(players_path)

    print(f"Loaded raw modern matches: {len(df_matches):,} rows")
    print(f"Loaded raw player records:  {len(df_players):,} rows")

    # =========================================================================
    # STEP 1: APPLY FORENSIC DATA QUALITY CORRECTIONS
    # =========================================================================
    print("\n[Step 1] Applying verified forensic data quality corrections...")
    
    # 1. Match 2450 (Brentford vs Blackburn, 2019-02-02): b365_home 0.0 typo
    # Exclude inferred odds from strict odds features: set to NaN
    idx_odds_typo = df_matches[(df_matches['b365_home'] == 0.0) & (df_matches['home_team_id'] == 'brentford')].index
    if len(idx_odds_typo) > 0:
        df_matches.loc[idx_odds_typo, 'b365_home'] = np.nan
        df_matches.loc[idx_odds_typo, 'b365_overround'] = np.nan
        df_matches.loc[idx_odds_typo, 'b365_implied_home_prob'] = np.nan
        df_matches.loc[idx_odds_typo, 'b365_implied_draw_prob'] = np.nan
        df_matches.loc[idx_odds_typo, 'b365_implied_away_prob'] = np.nan
        print("  ✓ Set Match 2450 Bet365 home odds & implied prob to NaN (strictly excluded inferred quote)")

    # 2. Correct Match 4692 (Newcastle vs West Ham, 2021-08-15): Away SOT (9) > Shots (8)
    idx_sot_1 = df_matches[(df_matches['match_date'] == '2021-08-15') & (df_matches['home_team_id'] == 'newcastle-united')].index
    if len(idx_sot_1) > 0:
        df_matches.loc[idx_sot_1, 'away_shots'] = 18.0
        print("  ✓ Corrected Match 4692 away shots from 8.0 to 18.0 (Opta verified)")

    # 3. Correct Match 7744 (Burnley vs Swansea, 2024-11-10): Home shots (2) and SOT (7) transposed
    idx_sot_2 = df_matches[(df_matches['match_date'] == '2024-11-10') & (df_matches['home_team_id'] == 'burnley')].index
    if len(idx_sot_2) > 0:
        df_matches.loc[idx_sot_2, 'home_shots'] = 7.0
        df_matches.loc[idx_sot_2, 'home_shots_on_target'] = 2.0
        print("  ✓ Corrected Match 7744 Burnley shots (7.0) and SOT (2.0) transposed columns")

    # 4. Deduplicate FPL player records (10 duplicates in 2025/26)
    len_before_p = len(df_players)
    df_players = df_players.drop_duplicates(subset=['season_name', 'gameweek', 'player_id', 'match_date']).copy()
    print(f"  ✓ Deduplicated FPL player records: {len_before_p - len(df_players)} duplicate rows removed ({len(df_players):,} remaining)")

    # =========================================================================
    # STEP 2: CONSTRUCT STANDARDIZED KICKOFF & PREDICTION CUTOFF TIMESTAMPS
    # =========================================================================
    print("\n[Step 2] Standardizing Kickoff Timestamps & 24h Prediction Cutoff...")

    # Build FPL exact UTC kickoff timestamp lookup for Premier League
    fpl_ko = df_players[df_players['was_home'] == True][['match_date', 'team_id', 'kickoff_time']].dropna().drop_duplicates(subset=['match_date', 'team_id'])
    fpl_dict = dict(zip(zip(fpl_ko['match_date'], fpl_ko['team_id']), fpl_ko['kickoff_time']))

    kickoff_timestamps = []
    has_exact_ko = []
    prediction_cutoffs = []
    kickoff_sources = []

    for _, r in df_matches.iterrows():
        m_date = str(r['match_date'])
        k_time = r['kickoff_time']
        comp = r['competition_id']
        ht = r['home_team_id']

        ts = None
        exact = False
        source = 'unknown'

        # If PL and in FPL dict, use exact UTC timestamp
        if comp == 'premier-league' and (m_date, ht) in fpl_dict:
            fpl_ts = fpl_dict[(m_date, ht)]
            try:
                ts = pd.to_datetime(fpl_ts).tz_localize(None)
                exact = True
                source = 'fpl_official_utc'
            except Exception:
                pass

        # If not matched or Championship, check Football-Data kickoff_time
        if ts is None and pd.notna(k_time) and str(k_time).strip() != '':
            time_str = str(k_time).strip()
            if len(time_str) == 5:
                time_str += ":00"
            try:
                ts = pd.to_datetime(f"{m_date} {time_str}")
                exact = True
                source = 'football_data_recorded'
            except Exception:
                pass

        # If still null (Championship 2016-2018), apply documented canonical default
        if ts is None:
            day_of_week = pd.to_datetime(m_date).dayofweek
            def_time = "15:00:00" if day_of_week in [5, 6] else "19:45:00"
            ts = pd.to_datetime(f"{m_date} {def_time}")
            exact = False
            source = 'synthetic_default_1500_1945'

        kickoff_timestamps.append(ts)
        has_exact_ko.append(exact)
        prediction_cutoffs.append(ts - pd.Timedelta(hours=24))
        kickoff_sources.append(source)

    df_matches['kickoff_timestamp'] = kickoff_timestamps
    df_matches['has_exact_kickoff_timestamp'] = has_exact_ko
    df_matches['prediction_cutoff'] = prediction_cutoffs
    df_matches['kickoff_time_source'] = kickoff_sources
    df_matches['temporal_tier'] = np.where(df_matches['has_exact_kickoff_timestamp'], 'tier_1_verified_exact', 'tier_2_safe_assumptions')

    n_tier1 = (df_matches['temporal_tier'] == 'tier_1_verified_exact').sum()
    n_tier2 = (df_matches['temporal_tier'] == 'tier_2_safe_assumptions').sum()
    print(f"  Exact Kickoff Timestamps: {sum(has_exact_ko):,} / {len(df_matches):,} ({sum(has_exact_ko)/len(df_matches)*100:.1f}%)")
    print(f"  Tier 1 Verified Exact:    {n_tier1:,} matches")
    print(f"  Tier 2 Safe Assumptions:  {n_tier2:,} matches")

    # Sort strictly chronologically by kickoff_timestamp
    df_matches = df_matches.sort_values(by=['kickoff_timestamp', 'match_id']).reset_index(drop=True)

    # =========================================================================
    # STEP 3: ASSEMBLE CHRONOLOGICAL TEAM APPEARANCE HISTORY
    # =========================================================================
    print("\n[Step 3] Building chronological team appearance histories...")

    team_appearances = []
    for idx, row in df_matches.iterrows():
        ko = row['kickoff_timestamp']
        m_end = ko + pd.Timedelta(hours=2) # Match finishes 2 hours after kickoff
        m_id = row['match_id']
        comp = row['competition_id']
        season = row['season_name']

        fthg = row['full_time_home_goals']
        ftag = row['full_time_away_goals']
        hs = row['home_shots'] if pd.notna(row['home_shots']) else 0.0
        as_ = row['away_shots'] if pd.notna(row['away_shots']) else 0.0
        hst = row['home_shots_on_target'] if pd.notna(row['home_shots_on_target']) else 0.0
        ast = row['away_shots_on_target'] if pd.notna(row['away_shots_on_target']) else 0.0
        hc = row['home_corners'] if pd.notna(row['home_corners']) else 0.0
        ac = row['away_corners'] if pd.notna(row['away_corners']) else 0.0
        hf = row['home_fouls'] if pd.notna(row['home_fouls']) else 0.0
        af = row['away_fouls'] if pd.notna(row['away_fouls']) else 0.0
        hy = row['home_yellow_cards'] if pd.notna(row['home_yellow_cards']) else 0.0
        ay = row['away_yellow_cards'] if pd.notna(row['away_yellow_cards']) else 0.0
        hr = row['home_red_cards'] if pd.notna(row['home_red_cards']) else 0.0
        ar = row['away_red_cards'] if pd.notna(row['away_red_cards']) else 0.0

        # Home team appearance
        h_res = 'W' if fthg > ftag else ('D' if fthg == ftag else 'L')
        h_pts = 3 if h_res == 'W' else (1 if h_res == 'D' else 0)
        team_appearances.append({
            'team_id': row['home_team_id'],
            'opponent_id': row['away_team_id'],
            'is_home': True,
            'match_id': m_id,
            'competition_id': comp,
            'season_name': season,
            'kickoff_timestamp': ko,
            'match_end_timestamp': m_end,
            'goals_scored': fthg,
            'goals_conceded': ftag,
            'goal_diff': fthg - ftag,
            'shots': hs,
            'sot': hst,
            'corners': hc,
            'fouls': hf,
            'cards': hy + hr,
            'result': h_res,
            'points': h_pts
        })

        # Away team appearance
        a_res = 'W' if ftag > fthg else ('D' if ftag == fthg else 'L')
        a_pts = 3 if a_res == 'W' else (1 if a_res == 'D' else 0)
        team_appearances.append({
            'team_id': row['away_team_id'],
            'opponent_id': row['home_team_id'],
            'is_home': False,
            'match_id': m_id,
            'competition_id': comp,
            'season_name': season,
            'kickoff_timestamp': ko,
            'match_end_timestamp': m_end,
            'goals_scored': ftag,
            'goals_conceded': fthg,
            'goal_diff': ftag - fthg,
            'shots': as_,
            'sot': ast,
            'corners': ac,
            'fouls': af,
            'cards': ay + ar,
            'result': a_res,
            'points': a_pts
        })

    df_appearances = pd.DataFrame(team_appearances).sort_values('kickoff_timestamp').reset_index(drop=True)
    team_history_map = {}
    for team, grp in df_appearances.groupby('team_id'):
        team_history_map[team] = grp.to_dict(orient='records')

    print(f"  Indexed {len(team_appearances):,} team appearances across {len(team_history_map)} clubs.")

    # =========================================================================
    # STEP 4: GENERATE STRICTLY LAGGED PRE-MATCH ROLLING FEATURES
    # =========================================================================
    print("\n[Step 4] Computing strictly lagged pre-match rolling features (T-24h Cutoff)...")

    def compute_team_rolling_features(team_id, cutoff_ts, current_ko_ts, is_home_fixture):
        records = team_history_map.get(team_id, [])
        prior = [r for r in records if r['match_end_timestamp'] <= cutoff_ts]

        out = {}
        n_prior = len(prior)
        out['prior_matches_count'] = n_prior

        # Rest days calculation
        if n_prior > 0:
            last_ko = prior[-1]['kickoff_timestamp']
            out['rest_days'] = round((current_ko_ts - last_ko).total_seconds() / 86400.0, 1)
        else:
            out['rest_days'] = np.nan

        # Windows: 3, 5, 10
        for w in [3, 5, 10]:
            if n_prior == 0:
                out[f'goals_scored_roll{w}'] = np.nan
                out[f'goals_conceded_roll{w}'] = np.nan
                out[f'goal_diff_roll{w}'] = np.nan
                out[f'shots_roll{w}'] = np.nan
                out[f'sot_roll{w}'] = np.nan
                out[f'corners_roll{w}'] = np.nan
                out[f'points_roll{w}'] = np.nan
                out[f'win_rate_roll{w}'] = np.nan
                out[f'draw_rate_roll{w}'] = np.nan
                out[f'loss_rate_roll{w}'] = np.nan
                if w == 5:
                    out['fouls_roll5'] = np.nan
                    out['cards_roll5'] = np.nan
            else:
                subset = prior[-w:]
                k = len(subset)
                out[f'goals_scored_roll{w}'] = round(sum(r['goals_scored'] for r in subset) / k, 3)
                out[f'goals_conceded_roll{w}'] = round(sum(r['goals_conceded'] for r in subset) / k, 3)
                out[f'goal_diff_roll{w}'] = round(sum(r['goal_diff'] for r in subset) / k, 3)
                out[f'shots_roll{w}'] = round(sum(r['shots'] for r in subset) / k, 3)
                out[f'sot_roll{w}'] = round(sum(r['sot'] for r in subset) / k, 3)
                out[f'corners_roll{w}'] = round(sum(r['corners'] for r in subset) / k, 3)
                out[f'points_roll{w}'] = round(sum(r['points'] for r in subset) / k, 3)
                out[f'win_rate_roll{w}'] = round(sum(1 for r in subset if r['result'] == 'W') / k, 3)
                out[f'draw_rate_roll{w}'] = round(sum(1 for r in subset if r['result'] == 'D') / k, 3)
                out[f'loss_rate_roll{w}'] = round(sum(1 for r in subset if r['result'] == 'L') / k, 3)
                if w == 5:
                    out['fouls_roll5'] = round(sum(r['fouls'] for r in subset) / k, 3)
                    out['cards_roll5'] = round(sum(r['cards'] for r in subset) / k, 3)

        # Venue-specific rolling features
        venue_prior = [r for r in prior if r['is_home'] == is_home_fixture]
        n_venue_prior = len(venue_prior)
        out['venue_prior_matches_count'] = n_venue_prior

        for w in [3, 5]:
            prefix = "venue_"
            if n_venue_prior == 0:
                out[f'{prefix}goals_scored_roll{w}'] = np.nan
                out[f'{prefix}goals_conceded_roll{w}'] = np.nan
                if w == 5:
                    out[f'{prefix}shots_roll5'] = np.nan
                    out[f'{prefix}sot_roll5'] = np.nan
                    out[f'{prefix}corners_roll5'] = np.nan
                    out[f'{prefix}points_roll5'] = np.nan
                    out[f'{prefix}win_rate_roll5'] = np.nan
            else:
                subset = venue_prior[-w:]
                k = len(subset)
                out[f'{prefix}goals_scored_roll{w}'] = round(sum(r['goals_scored'] for r in subset) / k, 3)
                out[f'{prefix}goals_conceded_roll{w}'] = round(sum(r['goals_conceded'] for r in subset) / k, 3)
                if w == 5:
                    out[f'{prefix}shots_roll5'] = round(sum(r['shots'] for r in subset) / k, 3)
                    out[f'{prefix}sot_roll5'] = round(sum(r['sot'] for r in subset) / k, 3)
                    out[f'{prefix}corners_roll5'] = round(sum(r['corners'] for r in subset) / k, 3)
                    out[f'{prefix}points_roll5'] = round(sum(r['points'] for r in subset) / k, 3)
                    out[f'{prefix}win_rate_roll5'] = round(sum(1 for r in subset if r['result'] == 'W') / k, 3)

        return out

    home_rolling_list = []
    away_rolling_list = []

    for idx, row in df_matches.iterrows():
        cutoff = row['prediction_cutoff']
        ko = row['kickoff_timestamp']

        h_feat = compute_team_rolling_features(row['home_team_id'], cutoff, ko, is_home_fixture=True)
        a_feat = compute_team_rolling_features(row['away_team_id'], cutoff, ko, is_home_fixture=False)

        home_rolling_list.append(h_feat)
        away_rolling_list.append(a_feat)

    df_h_roll = pd.DataFrame(home_rolling_list).add_prefix('home_')
    df_a_roll = pd.DataFrame(away_rolling_list).add_prefix('away_')

    print(f"  ✓ Generated {len(df_h_roll.columns) + len(df_a_roll.columns)} rolling features per match.")

    # =========================================================================
    # STEP 5: INTEGRATE PRE-MATCH PLAYER INTELLIGENCE (UPGRADED)
    # =========================================================================
    print("\n[Step 5] Integrating pre-gameweek player intelligence (PL Only, strictly pre-cutoff)...")

    # 1. Resolve true match-day team for each player record to eliminate retroactive terminal season club labeling
    pl_matches = df_matches[df_matches['competition_id'] == 'premier-league']
    fixture_to_team = {}
    for _, pr in pl_matches.iterrows():
        d = str(pr['match_date'])
        h = pr['home_team_id']
        a = pr['away_team_id']
        fixture_to_team[(d, a, True)] = h
        fixture_to_team[(d, h, False)] = a

    # Map true team_id
    true_teams = [fixture_to_team.get((str(d), opp, bool(wh)), tid) 
                  for d, opp, wh, tid in zip(df_players['match_date'], df_players['opponent_team_id'], df_players['was_home'], df_players['team_id'])]
    changed_teams = sum(1 for orig, true_t in zip(df_players['team_id'], true_teams) if orig != true_t)
    df_players['team_id'] = true_teams
    print(f"  ✓ Resolved {changed_teams:,} retroactive mid-season transfer club mismatches to player true clubs.")

    # 2. Compute exact timestamps and match completion timestamps
    df_players['kickoff_ts'] = pd.to_datetime(df_players['kickoff_time']).dt.tz_localize(None)
    df_players['match_end_ts'] = df_players['kickoff_ts'] + pd.Timedelta(hours=2)

    # Pre-index player records by (season_name, team_id)
    player_history_map = {}
    for (season, team), grp in df_players.groupby(['season_name', 'team_id']):
        player_history_map[(season, team)] = grp.sort_values('kickoff_ts').to_dict(orient='records')

    home_player_feats = []
    away_player_feats = []

    for idx, row in df_matches.iterrows():
        comp = row['competition_id']
        cutoff = row['prediction_cutoff']
        season = row['season_name']

        if comp != 'premier-league':
            home_player_feats.append({
                'home_squad_prior_goals_sum': np.nan,
                'home_squad_prior_assists_sum': np.nan,
                'home_top_scorer_prior_goals': np.nan,
                'home_squad_prior_xg_sum': np.nan,
                'home_squad_minutes_14d': np.nan
            })
            away_player_feats.append({
                'away_squad_prior_goals_sum': np.nan,
                'away_squad_prior_assists_sum': np.nan,
                'away_top_scorer_prior_goals': np.nan,
                'away_squad_prior_xg_sum': np.nan,
                'away_squad_minutes_14d': np.nan
            })
            continue

        # Compute for home team (STRICT: match_end_ts <= cutoff eliminates unfinished matches)
        h_team = row['home_team_id']
        h_recs = [r for r in player_history_map.get((season, h_team), []) if r['match_end_ts'] <= cutoff]
        if len(h_recs) == 0:
            h_p_out = {
                'home_squad_prior_goals_sum': 0.0,
                'home_squad_prior_assists_sum': 0.0,
                'home_top_scorer_prior_goals': 0.0,
                'home_squad_prior_xg_sum': 0.0,
                'home_squad_minutes_14d': 0.0
            }
        else:
            tot_g = float(sum(r['goals_scored'] for r in h_recs))
            tot_a = float(sum(r['assists'] for r in h_recs))
            xg_vals = [r['expected_goals'] for r in h_recs if pd.notna(r['expected_goals'])]
            tot_xg = float(sum(xg_vals)) if len(xg_vals) > 0 else np.nan
            cut_14d = cutoff - pd.Timedelta(days=14)
            mins_14d = float(sum(r['minutes'] for r in h_recs if r['kickoff_ts'] >= cut_14d))
            p_goals = {}
            for r in h_recs:
                p_goals[r['player_id']] = p_goals.get(r['player_id'], 0) + r['goals_scored']
            top_g = float(max(p_goals.values())) if len(p_goals) > 0 else 0.0

            h_p_out = {
                'home_squad_prior_goals_sum': tot_g,
                'home_squad_prior_assists_sum': tot_a,
                'home_top_scorer_prior_goals': top_g,
                'home_squad_prior_xg_sum': tot_xg,
                'home_squad_minutes_14d': mins_14d
            }
        home_player_feats.append(h_p_out)

        # Compute for away team (STRICT: match_end_ts <= cutoff)
        a_team = row['away_team_id']
        a_recs = [r for r in player_history_map.get((season, a_team), []) if r['match_end_ts'] <= cutoff]
        if len(a_recs) == 0:
            a_p_out = {
                'away_squad_prior_goals_sum': 0.0,
                'away_squad_prior_assists_sum': 0.0,
                'away_top_scorer_prior_goals': 0.0,
                'away_squad_prior_xg_sum': 0.0,
                'away_squad_minutes_14d': 0.0
            }
        else:
            tot_g_a = float(sum(r['goals_scored'] for r in a_recs))
            tot_a_a = float(sum(r['assists'] for r in a_recs))
            xg_vals_a = [r['expected_goals'] for r in a_recs if pd.notna(r['expected_goals'])]
            tot_xg_a = float(sum(xg_vals_a)) if len(xg_vals_a) > 0 else np.nan
            cut_14d_a = cutoff - pd.Timedelta(days=14)
            mins_14d_a = float(sum(r['minutes'] for r in a_recs if r['kickoff_ts'] >= cut_14d_a))
            p_goals_a = {}
            for r in a_recs:
                p_goals_a[r['player_id']] = p_goals_a.get(r['player_id'], 0) + r['goals_scored']
            top_g_a = float(max(p_goals_a.values())) if len(p_goals_a) > 0 else 0.0

            a_p_out = {
                'away_squad_prior_goals_sum': tot_g_a,
                'away_squad_prior_assists_sum': tot_a_a,
                'away_top_scorer_prior_goals': top_g_a,
                'away_squad_prior_xg_sum': tot_xg_a,
                'away_squad_minutes_14d': mins_14d_a
            }
        away_player_feats.append(a_p_out)

    df_h_player = pd.DataFrame(home_player_feats)
    df_a_player = pd.DataFrame(away_player_feats)

    print(f"  ✓ Engineered 10 pre-match player features with strict match completion (0 in-progress overlaps).")

    # =========================================================================
    # STEP 6: ASSEMBLE LEAKAGE-SAFE PRE-MATCH DATASET
    # =========================================================================
    print("\n[Step 6] Assembling and structuring finalized pre-match dataset...")

    # Core metadata
    core_cols = [
        'match_id', 'competition_id', 'competition_name', 'season_id', 'season_name',
        'season_start_year', 'match_date', 'kickoff_time', 'kickoff_timestamp',
        'prediction_cutoff', 'has_exact_kickoff_timestamp', 'temporal_tier', 'kickoff_time_source',
        'home_team_id', 'home_team_name', 'away_team_id', 'away_team_name'
    ]
    df_core = df_matches[core_cols].copy()

    # Pre-Match Elo (Verified Safe)
    elo_cols = [
        'home_elo_before', 'away_elo_before', 'elo_difference',
        'elo_home_win_prob', 'elo_draw_prob', 'elo_away_win_prob'
    ]
    df_elo = df_matches[elo_cols].copy()

    # Pre-Match Betting Odds (Opening Snapshots - Documented as Pre-Closing Snapshot)
    odds_open_cols = {
        'b365_home': 'b365_home_open',
        'b365_draw': 'b365_draw_open',
        'b365_away': 'b365_away_open',
        'b365_overround': 'b365_open_overround',
        'b365_implied_home_prob': 'b365_open_implied_home_prob',
        'b365_implied_draw_prob': 'b365_open_implied_draw_prob',
        'b365_implied_away_prob': 'b365_open_implied_away_prob',
        'pinnacle_home': 'pinnacle_home_open',
        'pinnacle_draw': 'pinnacle_draw_open',
        'pinnacle_away': 'pinnacle_away_open',
        'pinnacle_overround': 'pinnacle_open_overround',
        'pinnacle_implied_home_prob': 'pinnacle_open_implied_home_prob',
        'pinnacle_implied_draw_prob': 'pinnacle_open_implied_draw_prob',
        'pinnacle_implied_away_prob': 'pinnacle_open_implied_away_prob'
    }
    df_odds_open = df_matches[list(odds_open_cols.keys())].rename(columns=odds_open_cols).copy()

    # Targets (Strictly Segregated)
    target_cols = {
        'full_time_home_goals': 'target_full_time_home_goals',
        'full_time_away_goals': 'target_full_time_away_goals',
        'full_time_result': 'target_full_time_result',
        'target_home_win': 'target_home_win',
        'target_draw': 'target_draw',
        'target_away_win': 'target_away_win',
        'target_total_goals': 'target_total_goals',
        'target_over_2_5': 'target_over_2_5',
        'target_btts': 'target_btts',
        'target_goal_difference': 'target_goal_difference'
    }
    df_targets = df_matches[list(target_cols.keys())].rename(columns=target_cols).copy()

    # Retrospective Benchmarks & Post-Match Outcomes (Strictly Segregated)
    benchmark_cols = {
        'pinnacle_close_home': 'benchmark_pinnacle_close_home',
        'pinnacle_close_draw': 'benchmark_pinnacle_close_draw',
        'pinnacle_close_away': 'benchmark_pinnacle_close_away',
        'pinnacle_close_overround': 'benchmark_pinnacle_close_overround',
        'pinnacle_close_implied_home_prob': 'benchmark_pinnacle_close_implied_home',
        'b365_close_home': 'benchmark_b365_close_home',
        'b365_close_draw': 'benchmark_b365_close_draw',
        'b365_close_away': 'benchmark_b365_close_away',
        'home_shots': 'benchmark_match_home_shots',
        'away_shots': 'benchmark_match_away_shots',
        'home_shots_on_target': 'benchmark_match_home_sot',
        'away_shots_on_target': 'benchmark_match_away_sot',
        'home_corners': 'benchmark_match_home_corners',
        'away_corners': 'benchmark_match_away_corners',
        'home_elo_after': 'benchmark_home_elo_after',
        'away_elo_after': 'benchmark_away_elo_after'
    }
    df_benchmarks = df_matches[list(benchmark_cols.keys())].rename(columns=benchmark_cols).copy()

    # Combine all into Master Leakage-Safe DataFrame
    df_prematch_master = pd.concat([
        df_core,
        df_elo,
        df_odds_open,
        df_h_roll,
        df_a_roll,
        df_h_player,
        df_a_player,
        df_targets,
        df_benchmarks
    ], axis=1)

    print(f"Final Master Feature DataFrame: {df_prematch_master.shape[0]:,} rows x {df_prematch_master.shape[1]} columns")

    # Partition Tier 1 primary dataset
    df_tier1 = df_prematch_master[df_prematch_master['temporal_tier'] == 'tier_1_verified_exact'].reset_index(drop=True)
    print(f"Tier 1 Primary Dataset:        {df_tier1.shape[0]:,} rows x {df_tier1.shape[1]} columns")

    # =========================================================================
    # STEP 7: SAVE DELIVERABLES & DATABASE INTEGRATION
    # =========================================================================
    print("\n[Step 7] Exporting leakage-safe deliverables...")

    # Master dataset (9,578 rows)
    out_master_parquet = os.path.join(PROCESSED_DIR, "matches_prematch_24h_features.parquet")
    out_master_csv = os.path.join(PROCESSED_DIR, "matches_prematch_24h_features.csv")
    df_prematch_master.to_parquet(out_master_parquet, index=False)
    df_prematch_master.to_csv(out_master_csv, index=False, encoding='utf-8')
    print(f"  ✓ Saved Master Parquet: {out_master_parquet}")
    print(f"  ✓ Saved Master CSV:     {out_master_csv}")

    # Tier 1 dataset (7,922 rows)
    out_tier1_parquet = os.path.join(PROCESSED_DIR, "matches_prematch_24h_tier1.parquet")
    out_tier1_csv = os.path.join(PROCESSED_DIR, "matches_prematch_24h_tier1.csv")
    df_tier1.to_parquet(out_tier1_parquet, index=False)
    df_tier1.to_csv(out_tier1_csv, index=False, encoding='utf-8')
    print(f"  ✓ Saved Tier 1 Parquet: {out_tier1_parquet}")
    print(f"  ✓ Saved Tier 1 CSV:     {out_tier1_csv}")

    # SQLite Database Integration
    conn = sqlite3.connect(os.path.join(DATA_DIR, "matchlab.db"))
    df_sql = df_prematch_master.copy()
    df_sql['kickoff_timestamp'] = df_sql['kickoff_timestamp'].astype(str)
    df_sql['prediction_cutoff'] = df_sql['prediction_cutoff'].astype(str)
    df_sql.to_sql('matches_prematch_24h', conn, if_exists='replace', index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prematch_date ON matches_prematch_24h(match_date);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prematch_comp ON matches_prematch_24h(competition_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prematch_tier ON matches_prematch_24h(temporal_tier);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prematch_ht ON matches_prematch_24h(home_team_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prematch_at ON matches_prematch_24h(away_team_id);")
    
    # Create SQLite view for Tier 1
    conn.execute("DROP VIEW IF EXISTS matches_prematch_24h_tier1;")
    conn.execute("CREATE VIEW matches_prematch_24h_tier1 AS SELECT * FROM matches_prematch_24h WHERE temporal_tier = 'tier_1_verified_exact';")
    conn.commit()
    conn.close()
    print("  ✓ Persisted 'matches_prematch_24h' table and 'matches_prematch_24h_tier1' view in data/matchlab.db")

    print("\n" + "=" * 80)
    print("LEAKAGE-SAFE PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return df_prematch_master

if __name__ == '__main__':
    build_leakage_safe_dataset()
