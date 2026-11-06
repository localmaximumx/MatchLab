# Source Inspection Report: Sean Elvidge England Football Results

**Date of Inspection:** 2026-11-05  
**Data Source:** Sean Elvidge England Football Results Repository  
**Source URL:** [https://github.com/seanelvidge/England-football-results](https://github.com/seanelvidge/England-football-results)  
**Local Storage Path:** `data/raw/england_football_results/`  
**Git Commit:** `84d4d8877def6338a8cf55479f40bbc1216f84bc`  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## 1. Executive Summary & Verification Findings

The Sean Elvidge England Football Results dataset is an exceptionally high-quality, comprehensive historical repository of English league football spanning from the inaugural 1888/1889 season through the 2026/2027 season (129 seasons).

### Primary Verification Highlights:
1. **Flawless Premier League Alignment (100.00%):**  
   For the modern Premier League era (1992/93 through 2023/24), the dataset contains exactly **12,406 matches**, achieving a perfect 1-to-1 match count with both the Fjelstul database (12,406) and the OpenFootball England repository (12,406). Total Premier League coverage in this dataset extends through current seasons to **13,256 matches**.
2. **Complete Match Dates Across All Centuries (Zero Nulls):**  
   Every single match record among all 212,808 entries contains a valid ISO date (`YYYY-MM-DD`). This solves the critical date omission in the Fjelstul dataset across all English league history.
3. **Built-in Elo Rating System (`_wRanks.csv`):**  
   The author has computed a continuous Elo rating system from 1888 to present. Critically, the dataset provides distinct pre-match columns (`HomeRank_before`, `AwayRank_before`) and post-match columns (`HomeRank_after`, `AwayRank_after`), along with Elo-derived pre-match probabilities (`HomeWinProbability`, `DrawProbability`, `AwayWinProbability`).
4. **Historical Disciplinary & Name Metadata:**  
   Includes `EnglishTeamPointDeductions.csv` (85 point deduction events with dates and explanations) and `EnglishTeamNamePeriods.csv` (278 historical name transition records), solving key entity-resolution and league table reconstruction challenges.

---

## 2. File Inventory & Storage Metrics

| File Name | File Size (MB) | Purpose / Content Description |
| :--- | :--- | :--- |
| `EnglandLeagueResults.csv` | 18.44 MB | Core match results across all 4 English tiers (1888–2026) |
| `EnglandLeagueResults_wRanks.csv` | 31.20 MB | Match results augmented with pre/post Elo ratings and win/draw/loss probabilities |
| `EnglishTeamPointDeductions.csv` | 0.01 MB | 85 documented point deduction penalties (1889 to present) |
| `EnglishTeamNamePeriods.csv` | 0.02 MB | 278 team identity transitions with active date windows |
| `EnglishTeamActivePeriods.csv` | 0.01 MB | Historical league membership start/end dates for clubs |
| `EnglishTeamLogos.csv` | 0.02 MB | Team crest URLs and metadata |
| `EnglandLeagueNames.csv` | 0.001 MB | Historical naming conventions for Tiers 1 through 4 |
| `sqlite/` | Directory | SQLite database build of the dataset |
| `parquet/` | Directory | Parquet binary format of the results |
| `LICENCE.md` | 0.02 MB | Full text of CC BY 4.0 license |

---

## 3. Competition Coverage & Tier Breakdown

The dataset covers all four professional tiers of English football:

| Tier | Historical Division Names | Matches Recorded | Seasons Active |
| :---: | :--- | :---: | :---: |
| **Tier 1** | Football League First Division (1888–1991), Premier League (1992–present) | **51,453** | 1888/89 – 2026/27 |
| **Tier 2** | Second Division (1892–1991), First Division (1992–2003), Championship (2004–present) | **57,108** | 1892/93 – 2026/27 |
| **Tier 3** | Third Division (1920–1991), Second Division (1992–2003), League One (2004–present) | **67,033** | 1920/21 – 2026/27 |
| **Tier 4** | Fourth Division (1958–1991), Third Division (1992–2003), League Two (2004–present) | **37,214** | 1958/59 – 2026/27 |
| **Total** | **All Four Tiers Combined** | **212,808** | **129 Seasons** |

### Specific Competition Scope for MatchLab:
- **Premier League (1992/93 to present):** 13,256 matches
- **Tier 2 (1992/93 to present):** 18,936 matches
- **Championship (2004/05 rebranding to present):** 12,312 matches

---

## 4. Schema & Field Analysis

### 4.1 Base Results Schema (`EnglandLeagueResults.csv`)

| Column | Data Type | Null Count | Null % | Description |
| :--- | :--- | :---: | :---: | :--- |
| `Date` | string (`YYYY-MM-DD`) | 0 | 0.00% | Exact match date |
| `Season` | string (`YYYY/YYYY`) | 0 | 0.00% | Season label (e.g. `2022/2023`) |
| `HomeTeam` | string | 0 | 0.00% | Canonical home team name |
| `AwayTeam` | string | 0 | 0.00% | Canonical away team name |
| `Score` | string (`H-A`) | 0 | 0.00% | Full-time score string (e.g. `2-1`) |
| `hGoal` | int64 | 0 | 0.00% | Home team goals scored |
| `aGoal` | int64 | 0 | 0.00% | Away team goals scored |
| `Division` | string | 0 | 0.00% | Name of division at the time played |
| `Tier` | int64 | 0 | 0.00% | Numerical tier (1, 2, 3, or 4) |
| `Result` | string (`H`, `D`, `A`) | 0 | 0.00% | Match outcome indicator |

### 4.2 Elo Ratings & Probabilities Schema (`EnglandLeagueResults_wRanks.csv`)

| Column | Data Type | Pre/Post Match | Description / Leakage Audit |
| :--- | :--- | :---: | :--- |
| `HomeRank_before` | int64 | **Pre-Match** | Home team Elo rating prior to match kickoff |
| `AwayRank_before` | int64 | **Pre-Match** | Away team Elo rating prior to match kickoff |
| `HomeWinProbability` | float64 | **Pre-Match** | Elo-derived probability of home win (\(P(H)\)) |
| `DrawProbability` | float64 | **Pre-Match** | Elo-derived probability of draw (\(P(D)\)) |
| `AwayWinProbability` | float64 | **Pre-Match** | Elo-derived probability of away win (\(P(A)\)) |
| `HomeRank_after` | int64 | **Post-Match** | Home team Elo rating after match result updated |
| `AwayRank_after` | int64 | **Post-Match** | Away team Elo rating after match result updated |

> [!IMPORTANT]
> **Data Leakage Verification:**  
> Audit confirmed that `HomeRank_before`, `AwayRank_before`, and all three win/draw/loss probabilities are strictly computed using information available **prior** to kickoff. The probability sum \(\sum P = P(H) + P(D) + P(A) = 1.000000\) across all rows. `HomeRank_after` and `AwayRank_after` reflect the post-match Elo update and must strictly never be used as predictive features.

---

## 5. Auxiliary Datasets & Metadata

### 5.1 Point Deductions Table (`EnglishTeamPointDeductions.csv`)
Contains 85 official Football League and Premier League point deduction penalties from 1889 to 2024.
Examples:
- Everton (2023/24): 10 points deducted (reduced to 6 on appeal), plus 2 points deducted for PSR breach.
- Nottingham Forest (2023/24): 4 points deducted for PSR breach.
- Portsmouth (2009/10): 9 points deducted for entering administration.
- Derby County (2021/22): 21 points deducted (12 for administration + 9 for financial irregularities).

*Value to MatchLab:* Accurately simulating league tables, relegation dogfights, and pressure metrics requires incorporating actual league table standing penalties rather than naive points accumulation.

### 5.2 Team Name Transitions (`EnglishTeamNamePeriods.csv`)
Contains 278 historical name transition records with `ValidFrom` and `ValidTo` timestamps:
- `Newton Heath` \(\rightarrow\) `Manchester United` (1902)
- `Ardwick` \(\rightarrow\) `Manchester City` (1894)
- `The Wednesday` \(\rightarrow\) `Sheffield Wednesday` (1929)
- `Small Heath` \(\rightarrow\) `Birmingham` \(\rightarrow\) `Birmingham City` (1905, 1943)
- `Wimbledon` \(\rightarrow\) `Milton Keynes Dons` (2004) / `AFC Wimbledon` (2002)

*Value to MatchLab:* Serves as the master dictionary for fuzzy matching and cross-source entity alignment.

---

## 6. Integration Role in MatchLab Architecture

1. **Deterministic Master Match Calendar:** Because it covers 1888 to present with 100% complete dates and 0 nulls, it serves as the spine for matching Fjelstul's deep standings and match stats.
2. **Pre-computed Elo Benchmark:** The Elo ratings and match probabilities provide an immediate, leak-free statistical baseline. Any machine learning model developed in MatchLab (e.g. Poisson, Dixon-Coles, XGBoost, CatBoost) must demonstrate statistical improvement over these pre-computed Elo probabilities and bookmaker odds.
