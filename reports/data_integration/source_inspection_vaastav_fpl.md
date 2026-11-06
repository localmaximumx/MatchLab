# Source Inspection Report: Vaastav Fantasy Premier League Historical Dataset

**Inspection Date:** 2026-11-05  
**Inspector:** Automated Inspection Pipeline (`collectors/inspect_vaastav_fpl.py`)  
**Status:** Completed & Validated  

---

## 1. Executive Summary & Core Discovery

The **Vaastav Fantasy Premier League (FPL) Historical Dataset** is an extensive, longitudinal record of individual player performance, minutes played, gameweek statistics, fantasy market trends, and Expected Goals (xG) covering **11 Premier League seasons** (2016/17 through 2026/27).

### Major Findings for Our Prediction System:
1. **Massive Player-Level Depth:** Contains **257,783 individual player gameweek observations** across 11 seasons. Every week, every player on every 20 Premier League rosters is tracked.
2. **Integrated Understat xG Archive:** The repository contains an archived `understat/` subfolder per season, mapping individual player performance to match-level **Expected Goals (xG)**, **Expected Assists (xA)**, **Non-Penalty xG (npxG)**, **xGChain**, and **xGBuildup**. This provides the Understat coverage we identified in our candidate sources without needing a separate scraper.
3. **Official Opta xG Integration (2022+):** Starting from the 2022/23 season, official FPL integrated Opta expected metrics directly into `merged_gw.csv` (`expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded`).
4. **Strict Scope Limitation:** Covers **English Premier League only**. There is **zero coverage for the EFL Championship**.
5. **Data Leakage Safeguard Requirement:** Distinguishing pre-gameweek information (player price, transfer volume, historical rolling minutes, injury flags) from in-gameweek outcome statistics (actual minutes played, goals scored, FPL points) is mandatory to prevent look-ahead bias during Phase 5 feature engineering.

---

## 2. Basic Information

| Attribute | Details |
|---|---|
| **Dataset Name** | Vaastav Fantasy Premier League Historical Dataset |
| **Repository URL** | https://github.com/vaastav/Fantasy-Premier-League |
| **Creator / Maintainer** | Vaastav Anand & Community Contributors |
| **Git Commit** | `d7b05b51d137bfefef4b692386d18c610975b9b9` (Oct 2026) |
| **Download Date** | 2026-11-05 |
| **Local Storage Path** | `data/raw/vaastav_fpl/` (unmodified original files preserved) |
| **Volume & Size** | ~180 MB across 11 season directories + aggregated master tables |
| **File Formats** | CSV (`merged_gw.csv`, `fixtures.csv`, `cleaned_players.csv`, `understat/*.csv`) |
| **License & Provenance** | **MIT License** for the scraper/repository code. Underlying data is explicitly attributed to the official Fantasy Premier League API (`fantasy.premierleague.com`) and Understat (`understat.com`). Free for personal research and academic ML; cannot be resold as a commercial proprietary feed. |

---

## 3. Season Coverage Breakdown

The dataset covers **11 Premier League seasons** (2016/17 to 2026/27):

| Season | Completed Matchdays | Player GW Records | Distinct Columns | Understat Player Files | Key Features Available |
|---|---|---|---|---|---|
| **2016/17** | 38 GWs | 23,679 | 56 cols | — | Detailed on-pitch actions (tackles, key passes, dribbles) |
| **2017/18** | 38 GWs | 22,467 | 56 cols | — | Detailed passing, recoveries, big chances created/missed |
| **2018/19** | 38 GWs | 21,790 | 56 cols | — | Fixtures, ICT index, clearances, blocks, interceptions |
| **2019/20** | 47 GWs (Covid restart) | 22,560 | 33 cols | 22 players | ICT index, kickoff times, fixture difficulty |
| **2020/21** | 38 GWs | 24,365 | 36 cols | 24 players | Expected points (`xP`), team codes, positions |
| **2021/22** | 38 GWs | 25,447 | 36 cols | 736 players | Extensive Understat match-level xG archives |
| **2022/23** | 38 GWs | 26,505 | 41 cols | 575 players | Official Opta xG (`expected_goals`, `expected_assists`) |
| **2023/24** | 38 GWs | 29,725 | 41 cols | 798 players | Opta xG + full Understat xGChain & xGBuildup |
| **2024/25** | 38 GWs | 27,605 | 49 cols | 789 players | Complete season xG, xA, starts, minutes |
| **2025/26** | 38 GWs | 29,757 | 46 cols | — | Recent completed season gameweek data |
| **2026/27** | Active (GW 1–6) | 3,883 | 46 cols | — | Ongoing active season collection |
| **Total** | **380+ Matchdays** | **257,783** | — | **2,944 files** | **11 Seasons of Player-Level Tracking** |

---

## 4. Key Files & Data Architecture

Inside each season directory (`data/{YYYY-YY}/`):

### 1. `gws/merged_gw.csv` (Primary Player-Gameweek Table)
Tracks every player's weekly participation, physical output, and fantasy valuation:
- **Identifiers:** `name`, `element` (FPL player ID), `fixture` (fixture ID), `round` (Gameweek number), `team`, `opponent_team`, `was_home` (bool).
- **Match Context:** `kickoff_time`, `team_h_score`, `team_a_score`.
- **Match Actions:** `minutes` (actual minutes played), `goals_scored`, `assists`, `clean_sheets`, `goals_conceded`, `own_goals`, `penalties_missed`, `penalties_saved`, `yellow_cards`, `red_cards`, `saves`.
- **Underlying Shot & Creation Metrics:**
  - `expected_goals` (xG): Probability of player's shots converting to goals.
  - `expected_assists` (xA): Probability of player's passes converting to goals.
  - `expected_goal_involvements` (xGI): Cumulative xG + xA.
  - `expected_goals_conceded` (xGC): Defensive expectation while the player was on the pitch.
- **Form & Sentiment:** `transfers_in`, `transfers_out`, `transfers_balance`, `selected` (% ownership), `value` (price in tenths of £M), `total_points`, `bonus`, `bps`.

### 2. `understat/{Player_Name}_{ID}.csv` (Granular xG Archive)
For each player, records their match-by-match metrics from Understat:
- `goals`, `shots`, `xG`
- `xA`, `assists`, `key_passes`
- `npg` (non-penalty goals), `npxG` (non-penalty expected goals)
- `xGChain`: Total xG of every possession sequence the player participated in.
- `xGBuildup`: Total xG of possession sequences excluding the key pass and shot (measures deep playmaking value).

### 3. `fixtures.csv` (Official Fixture Schedule)
- Complete 380 match schedule per season with kickoff timestamps, team IDs, final scores, and FPL difficulty ratings (`team_h_difficulty`, `team_a_difficulty` on a 1–5 scale).

---

## 5. Data Quality, Encodings & Validation Checks

1. **Character Encoding:**
   - Older seasons (`2016-17`, `2017-18`) are encoded in `latin1` / `cp1252` due to European accents in player names (e.g. `Cesc Fàbregas`, `Érik Lamela`).
   - Modern seasons (`2021-22` onwards) are encoded in standard `utf-8`.
   - Ingestion pipelines must specify `encoding_errors='replace'` or inspect encoding per season.
2. **Column Consistency:**
   - The schema expanded over time from 33 columns to 56 columns, and stabilized at 41–49 columns from 2022 onwards as xG was natively added.
3. **Player Identity Resolution:**
   - Player names are formatted as strings (`name`), but each player also has an integer `element` ID within each season, plus a master ID list in `player_idlist.csv`.

---

## 6. Machine Learning Usefulness & Strict Leakage Rules

### How Player Data Empowers Our Match Prediction Model (Phase 5):
In traditional match prediction, models only look at team-level rolling goal averages. With Vaastav FPL data, we can construct **Player-Informed Team Features**:
1. **Starting Lineup Available xG:** Sum of expected goals generated by the starting 11 over their previous 5 matches.
2. **Missing Key Player Penalty:** If a striker who accounts for 40% of a team's xG is flagged as injured/suspended, the team's predicted goal expectancy is systematically downgraded.
3. **Squad Fatigue / Rotation:** Minutes played by key starters over the trailing 14 days (detecting European fixture congestion).
4. **Goalkeeper Shot-Stopping Form:** Ratio of actual goals conceded vs expected goals conceded (`goals_conceded` vs `expected_goals_conceded`).

### Strict Rule to Prevent Data Leakage:
> [!CAUTION]
> **Zero Future Information:**
> When predicting a match in Gameweek $K$, our feature pipeline **must only** aggregate player data from Gameweeks $1, \dots, K-1$.  
> Using Gameweek $K$'s actual minutes played, goals, or gameweek points as input features would represent catastrophic look-ahead data leakage.

---

## 7. Complete Summary of the 4 Phase 1 Datasets

We have now inspected all 4 primary historical candidate datasets:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Unified Multi-Source Architecture                     │
├──────────────────────┬──────────────────────┬──────────────────────────┤
│ Dataset              │ Coverage             │ Primary Contribution     │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ 1. Fjelstul          │ 1888–2023 (125 yrs)  │ Canonical fixture anchor │
│                      │ 208,028 matches      │ Clean club master IDs    │
│                      │ (PL + Tier 2, 3, 4)  │ Official league tables   │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ 2. OpenFootball      │ 1992–2024 (35 yrs)   │ 100% Kickoff dates       │
│                      │ 13,011 PL, 14k Tier 2│ Kickoff times, HT scores │
│                      │ (Public Domain CC0)  │ Promotion playoffs       │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ 3. StatsBomb         │ 2003/04, 2015/16     │ In-match pitch (x,y)     │
│                      │ 418 PL matches       │ Defender freeze frames   │
│                      │                      │ xG validation lab        │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ 4. Vaastav FPL       │ 2016–2027 (11 yrs)   │ 257,783 Player-GW stats  │
│                      │ PL only              │ Understat xG/xA archive  │
│                      │                      │ Player availability/form │
└──────────────────────┴──────────────────────┴──────────────────────────┘
```

The next candidates on our roadmap are:
- **Football-Data.co.uk:** The vital source for **historical bookmaker odds** (1X2, Asian handicap, over/under) and match statistics (shots, shots on target, corners, cards).
- **England Football Results:** Supplementary validation source.
