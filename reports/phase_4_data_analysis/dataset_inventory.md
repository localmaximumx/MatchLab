# MatchLab Phase 4: Master Dataset Inventory & Schema Specification

**Generated Date:** 2026-11-05  
**Version:** Phase 4 Production Benchmark  
**Database File:** [`data/matchlab.db`](file:///c:/Users/biniy/Desktop/MatchLab/data/matchlab.db) (SQLite 3.x, 26.5 MB)  
**Processed Master Files:**  
- [`data/processed/matches_modern_2016_present.parquet`](file:///c:/Users/biniy/Desktop/MatchLab/data/processed/matches_modern_2016_present.parquet) (1.56 MB, 9,578 matches, 87 columns)  
- [`data/processed/matches_modern_2016_present.csv`](file:///c:/Users/biniy/Desktop/MatchLab/data/processed/matches_modern_2016_present.csv) (5.23 MB)  
- [`data/processed/player_gameweeks_2016_present.parquet`](file:///c:/Users/biniy/Desktop/MatchLab/data/processed/player_gameweeks_2016_present.parquet) (5.62 MB, 257,783 rows, 35 columns)  

---

## 1. Executive Summary & Provenance Architecture

The MatchLab data repository contains multi-tiered, longitudinally reconciled football data spanning **1888 to 2026/27 (historical archive: 31,178 matches)** with a primary machine learning focus on the **Modern Era (2016/17 to 2026/27: 9,578 matches and 257,783 player records)**.

### Data Lineage & Ingestion Flow:
```
Raw Candidate Feeds (data/raw/)
├── 1. Sean Elvidge England Results (1888-2027) ──> Historical Date & Elo Anchor
├── 2. Football-Data.co.uk (68 CSVs, 1993-2027) ─> Box-Scores & Bookmaker Odds
├── 3. Fjelstul League Tables (1888-2023) ────────> Canonical Entity Foundation
├── 4. OpenFootball Datasets (1992-2024) ─────────> Cross-Validation Anchor
├── 5. Vaastav Fantasy PL (2016-2027) ────────────> Player-Level Gameweek Tracking
└── 6. StatsBomb Open Data (418 matches) ──────────> Spatial & Event Baseline
                          │
                          ▼ Entity Resolution & Cross-Validation
             [collectors/build_team_dictionary.py]
             [collectors/reconcile_matches.py]
                          │
                          ▼ Normalized Relational Ingestion
             [collectors/populate_database.py]
                          │
                          ▼ data/matchlab.db (SQLite, 26.5 MB)
                          │
                          ▼ Modern Filtering (>= 2016/17) & Implied Metric Synthesis
             [collectors/build_modern_dataset_2016_present.py]
                          │
                          ▼ Production Deliverables (data/processed/)
             - matches_modern_2016_present.parquet (9,578 matches, 87 cols)
             - player_gameweeks_2016_present.parquet (257,783 rows, 35 cols)
```

---

## 2. Relational Database Tables (`data/matchlab.db`)

The relational database enforces Third Normal Form (3NF) across historical and modern matches, linked via integer/slug foreign keys:

| Table Name | Rows | Primary Key | Description & Lineage |
|---|:---:|---|---|
| `competitions` | 2 | `competition_id` | England Tier 1 (`premier-league`) and Tier 2 (`championship`). |
| `seasons` | 138 | `season_id` | Competition season slugs (e.g. `premier-league_2016-2017`). |
| `teams` | 247 | `team_id` | Canonical clubs with Fjelstul IDs and historical tier flags. |
| `team_aliases` | 479 | `(alias_raw, source)` | Harmonization lookup mapping variations to canonical IDs. |
| `point_deductions` | 85 | `id` | Historical league disciplinary point adjustments (1890–2024). |
| `matches` | 31,178 | `match_id` | Master fixture table (1888–2027). Reconciled scores and dates. |
| `match_stats` | 24,489 | `match_id` | Box-scores (shots, corners, fouls, cards). |
| `match_elo_ratings` | 31,178 | `match_id` | Pre-match Elo ratings, win/draw/away probabilities, post-match Elo. |
| `match_betting_odds` | 22,620 | `match_id` | Bookmaker odds (Bet365, Pinnacle, opening, closing, market avg). |
| `matches_modern_2016_present` | 9,578 | `match_id` | Denormalized, enriched modern analytical table (2016/17+). |

---

## 3. Detailed Field Specifications: `matches_modern_2016_present`

The master modern dataset contains **87 fields** structured across 6 logical domains:

### Domain 1: Identifiers & Fixture Metadata (12 Columns)
| Column Name | SQL Type | Null Count | Description & Value Range |
|---|:---:|:---:|---|
| `match_id` | TEXT | 0 (0.0%) | Canonical unique key: `{COMP}_{YYYY}_{DATE}_{HOME}_{AWAY}` |
| `competition_id` | TEXT | 0 (0.0%) | Competition slug: `premier-league` or `championship` |
| `competition_name` | TEXT | 0 (0.0%) | Human-readable name: `Premier League` or `EFL Championship` |
| `season_id` | TEXT | 0 (0.0%) | Foreign key to `seasons` table |
| `season_name` | TEXT | 0 (0.0%) | Season string: `2016/2017` through `2026/2027` |
| `season_start_year`| INTEGER | 0 (0.0%) | Starting calendar year: `2016` to `2026` |
| `match_date` | TEXT | 0 (0.0%) | ISO Date: `YYYY-MM-DD` |
| `kickoff_time` | TEXT | 0 (0.0%) | Local kickoff time: `HH:MM:SS` (or `HH:MM`) |
| `home_team_id` | TEXT | 0 (0.0%) | Canonical home club slug (e.g. `manchester-city`) |
| `home_team_name` | TEXT | 0 (0.0%) | Formatted display name (e.g. `Manchester City`) |
| `away_team_id` | TEXT | 0 (0.0%) | Canonical away club slug (e.g. `liverpool`) |
| `away_team_name` | TEXT | 0 (0.0%) | Formatted display name (e.g. `Liverpool`) |

### Domain 2: Target Variables & Outcomes (13 Columns)
| Column Name | SQL Type | Null Count | Description & Value Range |
|---|:---:|:---:|---|
| `full_time_home_goals` | INTEGER | 0 (0.0%) | Full-time goals scored by home club (0 to 9) |
| `full_time_away_goals` | INTEGER | 0 (0.0%) | Full-time goals scored by away club (0 to 9) |
| `full_time_result` | TEXT | 0 (0.0%) | Outcome code: `H` (Home Win), `D` (Draw), `A` (Away Win) |
| `half_time_home_goals` | INTEGER | 1 (0.01%) | Half-time home goals (0 to 5) |
| `half_time_away_goals` | INTEGER | 1 (0.01%) | Half-time away goals (0 to 5) |
| `half_time_result` | TEXT | 1 (0.01%) | Half-time outcome code (`H`, `D`, `A`) |
| `referee` | TEXT | 1 (0.01%) | Match referee name |
| `target_home_win` | INTEGER | 0 (0.0%) | Binary classification target: 1 if Home Win, else 0 |
| `target_draw` | INTEGER | 0 (0.0%) | Binary classification target: 1 if Draw, else 0 |
| `target_away_win` | INTEGER | 0 (0.0%) | Binary classification target: 1 if Away Win, else 0 |
| `target_total_goals` | INTEGER | 0 (0.0%) | Total match goals (`home_goals + away_goals`) |
| `target_over_2_5` | INTEGER | 0 (0.0%) | Binary total goals target: 1 if total > 2.5, else 0 |
| `target_btts` | INTEGER | 0 (0.0%) | Both Teams To Score: 1 if (home > 0 and away > 0), else 0 |
| `target_goal_difference`| INTEGER | 0 (0.0%) | Home goal margin (`home_goals - away_goals`) |

### Domain 3: Match Statistics (12 Columns)
| Column Name | SQL Type | Null Count | Description |
|---|:---:|:---:|---|
| `home_shots` / `away_shots` | REAL | 1 (0.01%) | Total attempts on goal |
| `home_shots_on_target` / `away_shots_on_target` | REAL | 1 (0.01%) | Attempts on goal requiring goalkeeper save or scoring |
| `home_corners` / `away_corners` | REAL | 1 (0.01%) | Corner kicks awarded |
| `home_fouls` / `away_fouls` | REAL | 1 (0.01%) | Fouls committed |
| `home_yellow_cards` / `away_yellow_cards` | REAL | 1 (0.01%) | Yellow cards issued |
| `home_red_cards` / `away_red_cards` | REAL | 1 (0.01%) | Red cards issued |

### Domain 4: Elo Strength & Calibrated Probabilities (8 Columns)
| Column Name | SQL Type | Null Count | Description |
|---|:---:|:---:|---|
| `home_elo_before` | REAL | 0 (0.0%) | Home club Elo rating prior to kickoff (1000–2100) |
| `away_elo_before` | REAL | 0 (0.0%) | Away club Elo rating prior to kickoff (1000–2100) |
| `elo_difference` | REAL | 0 (0.0%) | `home_elo_before - away_elo_before` |
| `elo_home_win_prob` | REAL | 0 (0.0%) | Prior predicted probability of Home Win |
| `elo_draw_prob` | REAL | 0 (0.0%) | Prior predicted probability of Draw |
| `elo_away_win_prob` | REAL | 0 (0.0%) | Prior predicted probability of Away Win |
| `home_elo_after` | REAL | 0 (0.0%) | Posterior Elo rating after match update |
| `away_elo_after` | REAL | 0 (0.0%) | Posterior Elo rating after match update |

### Domain 5: Bookmaker Betting Odds & Synthesized Implied Probabilities (36 Columns)
| Column Group | Available Rows | Coverage % | Key Metrics Contained |
|---|:---:|:---:|---|
| **Bet365 Opening** | 9,578 | **100.0%** | `b365_home`, `b365_draw`, `b365_away`, `b365_overround`, normalized true implied probabilities |
| **Pinnacle Opening** | 8,855 | **92.45%** | `pinnacle_home`, `pinnacle_draw`, `pinnacle_away`, `pinnacle_overround`, implied probabilities |
| **Pinnacle Closing** | 8,867 | **92.58%** | `pinnacle_close_home`, `pinnacle_close_draw`, `pinnacle_close_away`, closing overround |
| **Bet365 Closing** | 8,867 | **92.58%** | `b365_close_home`, `b365_close_draw`, `b365_close_away` |
| **Market Averages** | 6,782 | **70.81%** | `market_avg_home`, `market_avg_draw`, `market_avg_away`, `market_max_home`, `market_max_draw`, `market_max_away` |
| **Goal Totals & Handicap** | 6,782 | **70.81%** | `market_avg_over_2_5`, `market_avg_under_2_5`, `asian_handicap_line`, `market_avg_handicap_home`, `market_avg_handicap_away` |

### Domain 6: Match-Level Squad Aggregations (6 Columns, Premier League Only)
| Column Name | SQL Type | PL Coverage | Description |
|---|:---:|:---:|---|
| `home_players_fielded` | REAL | 99.2% | Count of players who took the pitch for home team |
| `away_players_fielded` | REAL | 99.2% | Count of players who took the pitch for away team |
| `home_lineup_value_m` | REAL | 99.2% | Total market value (£M) of fielded home players |
| `away_lineup_value_m` | REAL | 99.2% | Total market value (£M) of fielded away players |
| `home_squad_xg` | REAL | 48.2% | Summed player xG (available 2022/23+ natively) |
| `away_squad_xg` | REAL | 48.2% | Summed player xG (available 2022/23+ natively) |

---

## 4. Detailed Field Specifications: `player_gameweeks_2016_present`

Contains **257,783 rows** covering **4,490 unique players** across 11 Premier League seasons (2016/17 to 2026/27):

| Field Name | Type | Description |
|---|:---:|---|
| `season_name` | String | Formatted season: `2016/2017` to `2026/2027` |
| `gameweek` | Integer | Round number (GW 1 to 38, up to 47 during Covid restart) |
| `kickoff_time` | String | ISO Timestamp (UTC) of fixture kickoff |
| `match_date` | String | ISO Date (`YYYY-MM-DD`) |
| `player_id` | Integer | Official FPL integer identifier (`element`) |
| `player_name` | String | Normalized player name (e.g. `Mohamed Salah`) |
| `position` | String | Categorical role: `GKP`, `DEF`, `MID`, `FWD` |
| `team_id` | String | Canonical club slug (`arsenal`, `manchester-city`) |
| `team_name` | String | Club display name |
| `opponent_team_id`| String | Canonical opponent slug |
| `was_home` | Boolean | `True` if home club; `False` if away |
| `minutes` | Integer | Actual minutes played on pitch (0 to 90+) |
| `goals_scored` | Integer | Official goals scored in gameweek |
| `assists` | Integer | Official assists awarded |
| `clean_sheets` | Integer | Clean sheet credit (60+ mins without conceding) |
| `goals_conceded` | Integer | Goals conceded while on pitch |
| `own_goals` | Integer | Own goals scored |
| `yellow_cards` | Integer | Yellow cards received (0 or 1) |
| `red_cards` | Integer | Red cards received (0 or 1) |
| `saves` | Integer | Goalkeeper saves made |
| `expected_goals` | Float | Official Opta xG (available 2022/23+) |
| `expected_assists`| Float | Official Opta xA (available 2022/23+) |
| `expected_goal_involvements`| Float | Cumulative Opta xGI (`xG + xA`) |
| `expected_goals_conceded` | Float | Defensive xGC while player on pitch |
| `ict_index` | Float | FPL Influence, Creativity, Threat composite score |
| `player_price_m` | Float | Player market valuation in £M (e.g. 12.5) |
| `transfers_balance`| Integer | Net weekly fantasy transfer volume (sentiment) |
| `selected_by_percent`| Float | Ownership percentage across all managers |
| `total_points` | Integer | Total official FPL points scored in gameweek |
