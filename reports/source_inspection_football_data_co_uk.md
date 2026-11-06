# Source Inspection Report: Football-Data.co.uk Historical Match & Odds Archives

**Date of Inspection:** 2026-11-05  
**Data Source:** Football-Data.co.uk England League Archives  
**Source URL:** [https://www.football-data.co.uk/englandm.php](https://www.football-data.co.uk/englandm.php)  
**Local Storage Path:** `data/raw/football_data_co_uk/`  
**License / Terms:** Free for personal use, research, and educational analytics. No commercial resale or distribution. (Full terms documented in `data/raw/football_data_co_uk/notes.txt`).

---

## 1. Executive Summary & Significance for MatchLab

Football-Data.co.uk is the foundational data spine for MatchLab's financial and predictive modeling objectives. It provides a unique bridge between on-pitch in-match performance metrics (shots, shots on target, corners, fouls, cards) and betting market pricing across more than three decades.

### Core Quantitative Metrics:
- **Premier League (Div `E0`):** **12,794 matches** across 34 complete seasons (1993/1994 through 2026/2027).
- **Championship (Div `E1`):** **18,384 matches** across 34 complete seasons (1993/1994 through 2026/2027).
- **Total Completed Matches Downloaded:** **31,178 matches** across 68 CSV files.
- **In-Match Stats Availability:** 100% complete for all 9,970 Premier League matches from 2000/01 onwards.
- **Bookmaker Odds Availability:** 9,210 Premier League matches with Bet365 odds; 5,320 matches with Pinnacle opening and closing odds; 2,750 matches with market maximum closing lines.

---

## 2. Temporal & Generational Evolution of the Schema

Football-Data.co.uk has grown organically over 30 years. Our inspection identified three distinct structural eras across the dataset:

```
Era 1: Early Era (1993/94 – 1999/00)
├── Columns: 20–30
├── Content: Basic results (Div, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR)
├── Half-time scores: Introduced in 1995/96
└── Odds: Early UK bookmakers (William Hill, Ladbrokes, Interwetten) introduced ~1998

Era 2: Statistical & Exchange Era (2000/01 – 2018/19)
├── Columns: 60–80
├── Content: Addition of match events (HS, AS, HST, AST, HC, AC, HF, AF, HY, AY, HR, AR)
├── Referees: Named referee recorded for every fixture
└── Odds: Rise of Asian Handicap, Bet365 (B365), Pinnacle (PS/PH), Betfair, Gamebookers, Stan James

Era 3: High-Frequency & Market-Closing Era (2019/20 – Present)
├── Columns: 105–140
├── Content: Addition of kickoff time (`Time`), Over/Under 2.5 goal totals (`Avg>2.5`, `Max>2.5`)
├── Market Consensus: Explicit calculation of `AvgH`, `AvgD`, `AvgA`, `MaxH`, `MaxD`, `MaxA`
└── Closing Lines: Separate tracking of opening odds vs. kickoff closing odds (`PSCH`, `PSCD`, `PSCA`, `B365CH`)
```

---

## 3. Data Leakage & Feature Boundary Audit

A strict boundary must be enforced between features available prior to match commencement and post-match event statistics:

| Category | Columns | Usable for Pre-Match Prediction? | Role in MatchLab Pipeline |
| :--- | :--- | :---: | :--- |
| **Match Identifiers** | `Div`, `Date`, `Time`, `HomeTeam`, `AwayTeam` | **YES** | Match identification and calendar alignment |
| **Pre-Match Officials** | `Referee` | **YES** | Referee tendency modeling (card/penalty propensity) |
| **Opening Market Odds** | `B365H/D/A`, `PSH/D/A`, `WHH/D/A`, `AvgH/D/A` | **YES** | Market-implied baseline probabilities (\(P_{\text{market}}\)) |
| **Closing Market Odds** | `PSCH/D/A`, `B365CH/D/A`, `MaxCH/D/A` | **CONDITIONAL** | Closing line value (CLV) benchmark; usable only right before kickoff |
| **Match Outcome** | `FTHG`, `FTAG`, `FTR`, `HTHG`, `HTAG`, `HTR` | **NO (Target Only)** | Ground truth labels for loss functions & evaluations |
| **In-Match Team Stats** | `HS`, `AS`, `HST`, `AST`, `HC`, `AC`, `HF`, `AF`, `HY`, `AY`, `HR`, `AR` | **NO (Historical Lag Only)** | Compute rolling historical averages (\(t-1\)) for team strength |

> [!WARNING]
> **Data Leakage Risk:**  
> In-match statistics (e.g. Shots on Target `HST`/`AST`, Corners `HC`/`AC`) must **never** be passed into a prediction model for the match in which they occurred. They are strictly post-match observations. In MatchLab, they will be transformed into rolling, exponentially weighted historical features (e.g. `home_team_rolling_sot_last_5`) computed solely from historical matches \(\le t-1\).

---

## 4. Bookmaker Coverage Breakdown (Premier League)

| Bookmaker / Market Column | Matches Covered | Active Historical Period | Model Role |
| :--- | :---: | :---: | :--- |
| **Bet365 (`B365H`, `B365D`, `B365A`)** | **9,210** (72.0%) | 2002/03 – Present | Most consistent retail bookmaker pricing series |
| **Pinnacle (`PSH`, `PSD`, `PSA`)** | **5,320** (41.6%) | 2011/12 – Present | Sharpest market baseline; gold standard for market efficiency |
| **Pinnacle Closing (`PSCH`, `PSCD`, `PSCA`)** | **5,320** (41.6%) | 2011/12 – Present | Definitive Closing Line Value (CLV) verification metric |
| **Market Average (`AvgH`, `AvgD`, `AvgA`)** | **2,750** (21.5%) | 2019/20 – Present | Consensus market price removing single-bookmaker bias |
| **Market Maximum (`MaxH`, `MaxD`, `MaxA`)** | **2,750** (21.5%) | 2019/20 – Present | Best available retail execution price |
| **Over/Under 2.5 (`Avg>2.5`, `Avg<2.5`)** | **2,750** (21.5%) | 2019/20 – Present | Totals market pricing for goal expectancy benchmarks |
| **Asian Handicap (`AHh`, `AvgAHH`, `AvgAHA`)** | **2,750** (21.5%) | 2019/20 – Present | Spread market pricing for handicap performance evaluation |

---

## 5. Technical Data Cleaning Insights

1. **Ragged Column Lengths:** Early seasons (notably 1993/94 through 1999/00 and 2003/04) contain variable column lengths across rows within the same file (e.g. line 1 has 57 columns, line 305 has 72 columns due to mid-season bookmaker additions). The parser implemented in `collectors/inspect_football_data_co_uk.py` automatically pads ragged rows and sanitizes duplicate column headers.
2. **Date Format Variations:** Older seasons use 2-digit years (`DD/MM/YY`), while modern seasons use 4-digit years (`DD/MM/YYYY`). Dates will be standardized to ISO-8601 (`YYYY-MM-DD`) during Phase 2 ingestion.
3. **Team Name Aliases:** Football-Data uses abbreviated team names (e.g. `Man United`, `Man City`, `Nott'm Forest`, `Spurs`, `Wolves`, `Sheff Utd`). These must be mapped to canonical entity IDs using our team harmonization dictionary.
