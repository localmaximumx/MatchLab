import pandas as pd
import numpy as np

df = pd.read_parquet('data/processed/matches_modern_2016_present.parquet')
print('Total modern matches:', len(df))

# Test across multiple teams
sample_teams = ['arsenal', 'manchester-city', 'liverpool', 'chelsea', 'fulham', 'norwich-city']
results = {}

for team in sample_teams:
    team_matches = df[(df['home_team_id'] == team) | (df['away_team_id'] == team)].sort_values(['match_date', 'kickoff_time'])
    mismatches = 0
    total = len(team_matches) - 1
    
    for i in range(1, len(team_matches)):
        prev = team_matches.iloc[i-1]
        curr = team_matches.iloc[i]
        
        prev_after = prev['home_elo_after'] if prev['home_team_id'] == team else prev['away_elo_after']
        curr_before = curr['home_elo_before'] if curr['home_team_id'] == team else curr['away_elo_before']
        
        if abs(prev_after - curr_before) > 0.01:
            mismatches += 1
            if mismatches <= 2:
                print(f"[{team}] Mismatch: {prev['match_date']} after={prev_after} -> {curr['match_date']} before={curr_before}")
                
    results[team] = (mismatches, total)

print("\nContinuity Summary (mismatches / total transitions):")
for t, (m, tot) in results.items():
    print(f"  {t:<18}: {m} / {tot} mismatches ({m/tot*100:.1f}%)")
