import sqlite3
import pandas as pd

conn = sqlite3.connect("data/raw/fjelstul/data-sqlite/englishfootball.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("SQLite Tables:", tables)
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cur.fetchone()[0]:,} rows")
conn.close()

# Premier league seasons check
m = pd.read_csv("data/raw/fjelstul/data-csv/matches.csv", low_memory=False)
pl = m[m["division"] == "Premier League"]
print("\nPremier League Seasons Breakdown:")
pl_counts = pl.groupby("season").agg(
    matches=("match_id", "count"),
    teams=("home_team_id", "nunique"),
    home_goals=("home_team_score", "sum"),
    away_goals=("away_team_score", "sum")
)
print(pl_counts.to_string())

# Championship seasons check
champ = m[m["division"] == "Championship"]
print("\nChampionship (2004-2023) Seasons Breakdown:")
champ_counts = champ.groupby("season").agg(
    matches=("match_id", "count"),
    teams=("home_team_id", "nunique"),
    home_goals=("home_team_score", "sum"),
    away_goals=("away_team_score", "sum")
)
print(champ_counts.to_string())

# Tier 2 overall
tier2 = m[m["tier"] == 2]
print(f"\nTotal Tier 2 matches: {len(tier2):,}")
print(f"Tier 2 divisions: {tier2['division'].value_counts().to_dict()}")
