# Source Inspection Report: Fjelstul English Football Database

**Inspection Date:** 2026-11-05  
**Inspector:** Automated Inspection Pipeline (`collectors/inspect_fjelstul.py`)  
**Status:** Completed & Validated  

---

## 1. Executive Summary & Core Discovery

The **Fjelstul English Football Database** is an exceptionally clean, relational historical record of English league football spanning from the inaugural 1888/89 season through 2023/24 (125 completed seasons across 4 tiers).

### Crucial Findings for Our ML System:
1. **Zero Data Corruption:** Across all 208,028 match records, there are **0 duplicate rows**, **0 duplicate primary keys**, and **0 missing values** in core statistical columns (scores, margins, outcomes).
2. **Complete Match Coverage:** Contains every scheduled league match in Premier League history (12,406 matches across 32 seasons) and EFL Championship history (11,040 modern Championship matches, 55,804 all-time Tier 2 matches).
3. **CRITICAL LIMITATION — No Match Dates or Kickoff Times:** The dataset does **not** record kickoff dates, matchdays, or times. Matches are ordered alphabetically by team names. Therefore, **Fjelstul alone cannot establish chronological order within a season** and cannot independently compute rolling pre-match form (e.g. "last 5 matches"). Match dates must be merged from complementary sources (e.g., OpenFootball or Football-Data.co.uk) during Phase 2.

---

## 2. Basic Information

| Attribute | Details |
|---|---|
| **Dataset Name** | Fjelstul English Football Database |
| **Repository URL** | https://github.com/jfjelstul/englishfootball |
| **Author** | Joshua C. Fjelstul (ORCID: `0000-0002-9494-260X`) |
| **Package Version** | 1.1.0 (Date: 2024-05-26) |
| **Git Commit** | `ff3c37698065476e1852243685da6b756a580b9f` |
| **Download Date** | 2026-11-05 |
| **Local Storage Path** | `data/raw/fjelstul/` (unmodified original files preserved) |
| **File Formats Provided** | CSV (`data-csv/`), SQLite 3 (`data-sqlite/`), R Data (`data/`), PDF/CSV Codebooks (`codebook/`) |
| **License** | **CC BY-SA 4.0** (Creative Commons Attribution-ShareAlike 4.0 International) |
| **Permitted Uses** | Commercial and non-commercial use, adaptation, and sharing permitted with proper attribution; adaptations must share under the same license if redistributed. |

### Raw File Inventory:

| File Name | Location | Size | Rows | Description |
|---|---|---|---|---|
| `seasons.csv` | `data-csv/` | 24.9 KB | 439 | Season-level metadata (tier, division, winner, team count) |
| `teams.csv` | `data-csv/` | 6.0 KB | 144 | Historical club master catalog (status, former names, debut) |
| `matches.csv` | `data-csv/` | 31.3 MB | 208,028 | One row per match (final scores, margins, outcome flags) |
| `appearances.csv` | `data-csv/` | 59.7 MB | 416,056 | Team-match perspective (2 rows per match: home and away) |
| `standings.csv` | `data-csv/` | 858.5 KB | 9,740 | End-of-season league tables (points, GD, adjustments) |
| `englishfootball.db` | `data-sqlite/` | 64.5 MB | — | SQLite database containing all 5 relational tables |
| `variables.csv` | `codebook/csv/` | 9.5 KB | 66 | Official variable definitions, data types, and notes |
| `datasets.csv` | `codebook/csv/` | 1.9 KB | 5 | Official table descriptions |

---

## 3. Competition and Season Coverage

The database spans season years **1888 to 2023** (1888/89 to 2023/24). Note: Seasons were suspended during WWI (1915–1919) and WWII (1939–1946).

### Matches by League Tier:
- **Tier 1 (Top Flight):** 50,570 matches
  - *Premier League (1992–2023):* 12,406 matches
  - *First Division (1888–1991):* 38,164 matches
- **Tier 2 (Second Flight):** 55,804 matches
  - *Second Division (1892–1991):* 38,140 matches
  - *First Division (1992–2003):* 6,624 matches
  - *Championship (2004–2023):* 11,040 matches
- **Tier 3:** 65,708 matches (Third Division, Third Division North/South, League One)
- **Tier 4:** 35,946 matches (Fourth Division, League Two)
- **Total Historical Matches:** **208,028 matches**

### Target Competitions In-Depth:

#### A. English Premier League (PL)
- **Seasons:** 32 (1992/93 through 2023/24).
- **Match Counts per Season:**
  - 1992–1994 (22 teams): 462 matches/season (3 × 462 = 1,386).
  - 1995–2023 (20 teams): 380 matches/season (29 × 380 = 11,020).
- **Total PL Matches:** **12,406** (100% complete, 0 missing fixtures).

#### B. EFL Championship (Tier 2)
- **Modern Championship (2004–2023):** 20 seasons, 24 teams, 552 matches/season = **11,040 matches** (100% complete).
- **All-Time Tier 2 (1892–2023):** 121 seasons = **55,804 matches**.

---

## 4. Schema and Data Structure

The dataset adheres to a normalized relational architecture:

```
seasons (season_id PK)
   │
   ├──< matches (match_id PK, season_id FK, home_team_id FK, away_team_id FK)
   │       │
   │       └──< appearances (season_id, match_id, team_id PK)
   │
   └──< standings (season_id, team_id PK)

teams (team_id PK)
   │
   ├──< matches (home_team_id, away_team_id)
   ├──< appearances (team_id, opponent_id)
   └──< standings (team_id)
```

### Table Details:

### `matches` (Primary Table)
- **Primary Key:** `match_id` (format: `M-{season}-{counter}`, e.g., `M-1992-1-001`)
- **Foreign Keys:** `season_id` -> `seasons`, `home_team_id` -> `teams`, `away_team_id` -> `teams`
- **Columns:**
  - Identifiers: `key_id`, `season_id`, `season`, `tier`, `division`, `subdivision`, `match_id`, `match_name`
  - Teams: `home_team_id`, `home_team_name`, `away_team_id`, `away_team_name`
  - Scorelines: `score` (text, e.g. "2-1"), `home_team_score` (int), `away_team_score` (int)
  - Margins: `home_team_score_margin` (int), `away_team_score_margin` (int)
  - Outcome: `result` (enum: `home team win`, `away team win`, `draw`), `home_team_win` (0/1), `away_team_win` (0/1), `draw` (0/1)

### `appearances` (Team-Centric Unpivoted Table)
- **Primary Key:** `(season_id, match_id, team_id)`
- **Row count:** 416,056 (exactly 2 rows per match)
- **Unique fields:** `home_team` (bool), `away_team` (bool), `goals_for`, `goals_against`, `goal_difference`, `win`, `lose`, `draw`, `points` (correctly handles 2 points for a win prior to 1981, 3 points from 1981 onwards).

### `teams` (Club Master Table)
- **Primary Key:** `team_id` (format: `T-###`, e.g., `T-002` for Aston Villa, `T-013` for Arsenal)
- **Row count:** 144 unique clubs
- **Fields:** `team_id`, `team_name`, `former_team_names`, `current` (92 EFL/PL clubs), `former` (26 clubs), `defunct` (26 clubs), `first_appearance` (year).

### `standings` (Official Final League Tables)
- **Primary Key:** `(season_id, team_id)`
- **Row count:** 9,740 team-seasons
- **Fields:** `position`, `played`, `wins`, `draws`, `losses`, `goals_for`, `goals_against`, `goal_difference`, `points`, `point_adjustment` (tracks league penalties/deductions).

---

## 5. Data Quality and Validation Findings

### Missing Value Analysis:
- `matches`: **0 missing values** across all columns except `subdivision` (86.08% null).
  - *Note:* Subdivisions (North/South) only existed in Tier 3 between 1921 and 1958. This missingness is structural and correct.
- `seasons`: 0 missing values except `subdivision`.
- `teams`: 0 missing values except `former_team_names` (87.5% null, because most clubs retained their original names).
- `appearances`: 0 missing values except `subdivision`.
- `standings`: 0 missing values except `subdivision`.

### Integrity Checks:
- **Duplicates:** 0 duplicate rows across all tables. 0 duplicate primary keys.
- **Score Validity:**
  - Negative goals: 0 found.
  - Score parse check: In 100% of rows, `score == f"{home_team_score}-{away_team_score}"`.
  - Margins check: In 100% of rows, `home_team_score_margin == home_team_score - away_team_score`.
  - Result consistency: All boolean flags (`home_team_win`, `away_team_win`, `draw`) strictly match scores.
- **Aggregate Statistics:**
  - Total historical goals: 594,974 goals across 208,028 matches.
  - Overall home win rate: 50.37%
  - Overall away win rate: 24.36%
  - Overall draw rate: 25.27%
  - Average home goals: 1.742
  - Average away goals: 1.119

---

## 6. Machine Learning Usefulness & Limitations

### What This Dataset Contributes (High Value):
1. **Authoritative Canonical League Anchor:** Establishes the exact universe of valid league fixtures. We know with certainty whether any English league match existed or was omitted.
2. **Standardized Club Catalog:** 144 canonical clubs with consistent naming and stability across 136 years.
3. **End-of-Season Ground Truth:** Official league tables with points deductions (`point_adjustment`) for validating table simulations.
4. **Historical Base Rates:** Long-term prior probabilities for home advantage, draw rates, and goal scoring distributions.

### What This Dataset Lacks (Must Be Sourced Elsewhere):
1. **Match Dates & Times:** No timestamps or sequence identifiers exist. To prevent look-ahead bias and build time-series features (e.g. rolling 5-game goal averages), match dates must be joined from another source.
2. **In-Match Metrics:** No half-time scores, shots, shots on target, corners, fouls, or bookings.
3. **Expected Goals (xG):** No chance quality or spatial shot data.
4. **Player & Lineup Data:** No starting eleven, substitutes, minutes, or individual contributions.
5. **Bookmaker Odds:** No opening or closing market pricing.

---

## 7. Match Resolution Strategy for Phase 2

Because Fjelstul lacks match dates, how will we join it with OpenFootball or Football-Data.co.uk?

In league football, **each pair of teams plays each other at home exactly once per season**.
Therefore, the natural composite key:
$$\text{Natural Key} = (\text{Season}, \text{Tier}, \text{Canonical Home Team}, \text{Canonical Away Team})$$
is **unique and deterministic**.

When we inspect OpenFootball next, we will verify this key mapping to attach kickoff dates to Fjelstul's match records.
