"""
Phase 3 - Comprehensive Relational Database Verification Testbench
Executes rigorous integrity audits, foreign key validation, probability checks,
odds margin calculations, and complex multi-table analytical queries on data/matchlab.db.
"""

import sys
import os
import sqlite3
import json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "matchlab.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def verify_database():
    print("=" * 80)
    print("PHASE 3 - RUNNING DATABASE VERIFICATION TESTBENCH")
    print(f"Target Database: {DB_PATH}")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    results = {}

    # 1. Structural PRAGMA Integrity Checks
    print("\n1. Running PRAGMA Integrity and Foreign Key Checks...")
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchall()
    print(f"  PRAGMA integrity_check: {integrity[0][0]}")

    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    print(f"  PRAGMA foreign_key_check: {len(fk_violations)} violations found")
    if fk_violations:
        print("  WARNING - Foreign Key Violations:", fk_violations[:5])

    results["integrity_check"] = integrity[0][0]
    results["foreign_key_violations_count"] = len(fk_violations)

    # 2. Table Row Counts
    print("\n2. Auditing Table Row Counts...")
    tables = [
        'competitions', 'seasons', 'teams', 'team_aliases',
        'point_deductions', 'matches', 'match_stats',
        'match_elo_ratings', 'match_betting_odds'
    ]
    row_counts = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        row_counts[t] = cnt
        print(f"  Table {t:<22}: {cnt:>8,} rows")
    results["row_counts"] = row_counts

    # 3. Competition & Season Breakdown
    print("\n3. Matches Breakdown by Competition...")
    cursor.execute("""
        SELECT c.name, c.tier, COUNT(m.match_id), MIN(m.match_date), MAX(m.match_date)
        FROM matches m
        JOIN competitions c ON m.competition_id = c.competition_id
        GROUP BY c.competition_id;
    """)
    comp_stats = []
    for row in cursor.fetchall():
        comp_stats.append({
            "competition": row[0],
            "tier": row[1],
            "matches": row[2],
            "first_match": row[3],
            "last_match": row[4]
        })
        print(f"  {row[0]} (Tier {row[1]}): {row[2]:,} matches (From {row[3]} to {row[4]})")
    results["competitions_summary"] = comp_stats

    # 4. Data Quality & Constraint Checks
    print("\n4. Checking Data Quality Constraints...")
    
    # Null or invalid result audit
    cursor.execute("""
        SELECT COUNT(*) FROM matches 
        WHERE match_date IS NULL OR full_time_home_goals IS NULL 
           OR full_time_away_goals IS NULL OR full_time_result NOT IN ('H', 'D', 'A');
    """)
    invalid_matches = cursor.fetchone()[0]
    print(f"  Invalid core match records: {invalid_matches} (Expected: 0)")

    # Score bounds check
    cursor.execute("""
        SELECT MIN(full_time_home_goals), MAX(full_time_home_goals),
               MIN(full_time_away_goals), MAX(full_time_away_goals),
               AVG(full_time_home_goals + full_time_away_goals)
        FROM matches;
    """)
    min_hg, max_hg, min_ag, max_ag, avg_goals = cursor.fetchone()
    print(f"  Goals range: Home [{min_hg} to {max_hg}], Away [{min_ag} to {max_ag}]")
    print(f"  Historical Average Goals per Match: {avg_goals:.3f}")
    results["goals_distribution"] = {
        "min_home_goals": min_hg, "max_home_goals": max_hg,
        "min_away_goals": min_ag, "max_away_goals": max_ag,
        "avg_goals_per_match": round(avg_goals, 3)
    }

    # 5. Elo Ratings & Probability Sum Verification
    print("\n5. Verifying Pre-Match Elo Ratings and Probabilities...")
    cursor.execute("""
        SELECT MIN(home_elo_before), MAX(home_elo_before),
               MIN(elo_home_win_prob + elo_draw_prob + elo_away_win_prob),
               MAX(elo_home_win_prob + elo_draw_prob + elo_away_win_prob)
        FROM match_elo_ratings;
    """)
    min_elo, max_elo, min_prob_sum, max_prob_sum = cursor.fetchone()
    print(f"  Elo Rating Range: [{min_elo:.1f} to {max_elo:.1f}]")
    print(f"  Probability Sum Bounds: Min = {min_prob_sum:.6f}, Max = {max_prob_sum:.6f}")
    prob_valid = abs(min_prob_sum - 1.0) < 1e-4 and abs(max_prob_sum - 1.0) < 1e-4
    print(f"  ✓ Elo probability sum = 1.0 verification: {'PASSED' if prob_valid else 'FAILED'}")
    results["elo_verification"] = {
        "min_elo": round(min_elo, 1),
        "max_elo": round(max_elo, 1),
        "min_prob_sum": round(min_prob_sum, 6),
        "max_prob_sum": round(max_prob_sum, 6),
        "passed": prob_valid
    }

    # 6. Bookmaker Odds & Margin (Vig) Verification
    print("\n6. Auditing Bookmaker Odds & Margins...")
    cursor.execute("""
        SELECT 
            COUNT(b365_home),
            COUNT(pinnacle_home),
            COUNT(pinnacle_close_home),
            AVG(1.0/b365_home + 1.0/b365_draw + 1.0/b365_away),
            AVG(1.0/pinnacle_home + 1.0/pinnacle_draw + 1.0/pinnacle_away),
            AVG(1.0/pinnacle_close_home + 1.0/pinnacle_close_draw + 1.0/pinnacle_close_away)
        FROM match_betting_odds
        WHERE b365_home IS NOT NULL AND pinnacle_home IS NOT NULL;
    """)
    b365_cnt, pin_cnt, pin_close_cnt, avg_b365_margin, avg_pin_margin, avg_pin_close_margin = cursor.fetchone()
    print(f"  Matches with Bet365 Odds:           {b365_cnt:,}")
    print(f"  Matches with Pinnacle Odds:         {pin_cnt:,}")
    print(f"  Matches with Pinnacle Closing Odds: {pin_close_cnt:,}")
    print(f"  Average Bet365 Bookmaker Margin (Overround):   {avg_b365_margin:.4f} ({(avg_b365_margin - 1.0)*100:.2f}% Vig)")
    print(f"  Average Pinnacle Opening Margin (Overround):   {avg_pin_margin:.4f} ({(avg_pin_margin - 1.0)*100:.2f}% Vig)")
    print(f"  Average Pinnacle Closing Margin (Overround):   {avg_pin_close_margin:.4f} ({(avg_pin_close_margin - 1.0)*100:.2f}% Vig)")
    
    results["betting_margins"] = {
        "b365_avg_margin": round(avg_b365_margin, 4),
        "b365_avg_vig_pct": round((avg_b365_margin - 1.0) * 100, 2),
        "pinnacle_open_avg_margin": round(avg_pin_margin, 4),
        "pinnacle_open_avg_vig_pct": round((avg_pin_margin - 1.0) * 100, 2),
        "pinnacle_close_avg_margin": round(avg_pin_close_margin, 4),
        "pinnacle_close_avg_vig_pct": round((avg_pin_close_margin - 1.0) * 100, 2)
    }

    # 7. Sample Multi-Table Analytical SQL Query
    print("\n7. Executing End-to-End Analytical Query (Sample Modern Match View)...")
    cursor.execute("""
        SELECT 
            m.match_date, m.kickoff_time,
            ht.canonical_name AS home_team,
            at.canonical_name AS away_team,
            m.full_time_home_goals || '-' || m.full_time_away_goals AS score,
            m.full_time_result,
            s.home_shots || '-' || s.away_shots AS shots,
            s.home_shots_on_target || '-' || s.away_shots_on_target AS sot,
            s.home_corners || '-' || s.away_corners AS corners,
            ROUND(e.elo_home_win_prob, 3) AS elo_h_prob,
            ROUND(e.elo_away_win_prob, 3) AS elo_a_prob,
            o.b365_home, o.b365_draw, o.b365_away,
            o.pinnacle_close_home, o.pinnacle_close_away
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        LEFT JOIN match_stats s ON m.match_id = s.match_id
        LEFT JOIN match_elo_ratings e ON m.match_id = e.match_id
        LEFT JOIN match_betting_odds o ON m.match_id = o.match_id
        WHERE m.competition_id = 'premier-league' AND m.season_name = '2023/2024'
        ORDER BY m.match_date DESC
        LIMIT 5;
    """)
    sample_rows = cursor.fetchall()
    df_sample = pd.DataFrame(sample_rows, columns=[
        'Date', 'Time', 'Home Team', 'Away Team', 'Score', 'Res',
        'Shots', 'SoT', 'Corners', 'Elo H%', 'Elo A%',
        'B365H', 'B365D', 'B365A', 'PinCloseH', 'PinCloseA'
    ])
    print(df_sample.to_string(index=False))

    # Save summary to disk
    summary_path = os.path.join(REPORTS_DIR, "database_verification_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nVerification summary saved to: {summary_path}")

    conn.close()
    return results

if __name__ == "__main__":
    verify_database()
