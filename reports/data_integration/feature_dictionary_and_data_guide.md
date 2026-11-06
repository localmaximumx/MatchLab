# MatchLab — Feature Dictionary & Pre-Modeling Data Guide

**Document Date:** 2026-11-06  
**Primary Dataset (Tier 1):** `data/processed/matches_prematch_24h_tier1.parquet` (7,922 matches x 161 columns)  
**Full Historical Master Dataset:** `data/processed/matches_prematch_24h_features.parquet` (9,578 matches x 161 columns)  
**SQLite Access:** `matches_prematch_24h` table & `matches_prematch_24h_tier1` view in `data/matchlab.db`  
**Prediction Horizon:** Strict 24.0 Hours Before Kickoff ($T - 24.000\text{h}$)  
**Author:** MatchLab Machine Learning Engineering Team

---

## 1. Executive Summary & Dataset Architecture

This document provides a comprehensive, field-by-field reference guide for the 161 engineered features, targets, benchmarks, and temporal metadata in Project MatchLab.

The dataset is partitioned into two analytical layers:
1. **Primary Dataset — Tier 1 Only (7,922 Matches):** Contains only fixtures with **verified exact historical kickoff timestamps** (100% of Premier League from 2016/17 to 2026/27, and EFL Championship from 2019/20 to 2026/27). This constitutes the gold standard for initial pre-match machine learning experiments.
2. **Master Historical Dataset (9,578 Matches):** Preserves all 7,922 Tier 1 fixtures plus 1,656 Tier 2 Championship fixtures (2016/17–2018/19) where kickoff times are based on documented scheduling heuristics. This dataset is reserved for controlled sample-expansion experiments.

### Summary of Feature Families

| Feature Family | Columns | Modeling Role | Temporal Status | Tier 1 Missingness |
| :--- | :---: | :--- | :--- | :---: |
| **1. Metadata & Temporal Anchors** | 17 | Match Identifiers & Provenance | Pre-Match Metadata | 0.0% (Timestamp) |
| **2. Pre-Match Elo Ratings** | 6 | Team Strength & Probabilities | Verified Exact Pre-Match | 0.0% |
| **3. Pre-Match Opening Betting Odds** | 14 | Market Wisdom & Implied Prob | Mid-Week Market Snapshot | 0.0% (B365) / 9.1% (Pin) |
| **4. Team-Level Overall Rolling Form** | 68 | Lagged Form (Last 3, 5, 10 games) | Strictly Pre-Cutoff ($T - 24\text{h}$) | 0.0% – 0.2% |
| **5. Venue-Specific Rolling Form** | 20 | Home/Away Lagged Form (Last 3, 5) | Strictly Pre-Cutoff ($T - 24\text{h}$) | 0.0% – 0.4% |
| **6. Squad Player Intelligence** | 10 | Squad Goals, Assists, Fatigue (14d) | Premier League Only | 50.9% (All Champ = NaN) |
| **7. Target Variables** | 10 | Supervised Prediction Targets | Strictly Post-Match | 0.0% |
| **8. Retrospective Benchmarks** | 16 | Closing Lines & In-Match Stats | Strictly Post-Cutoff Evaluation | 0.0% – 14.4% |
| **Total Features & Columns** | **161** | | | |

---

## 2. Family 1: Metadata & Temporal Anchors (17 Columns)

These columns establish the canonical entity identity, competition context, and strict chronological prediction boundary for each fixture.

| Column Name | Data Type | Description | Values / Format | Role in Modeling |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | string | Canonical unique match identifier | `{season}_{home}_{away}` | Entity Key |
| `competition_id` | string | Normalized competition slug | `premier-league` or `championship` | Stratification Key |
| `competition_name` | string | Display competition title | English Premier League / EFL Championship | Display |
| `season_id` | string | Canonical season slug | `2016-2017` to `2026-2027` | Splitting Key |
| `season_name` | string | Canonical season display | `2016/2017` to `2026/2027` | Splitting Key |
| `season_start_year`| int64 | Calendar year season began | 2016 to 2026 | Temporal Index |
| `match_date` | string | Canonical match date | `YYYY-MM-DD` | Temporal Index |
| `kickoff_time` | string | Original source kickoff time | `HH:MM:SS` (or null if FPL UTC) | Provenance |
| `kickoff_timestamp`| datetime64 | Exact UTC/local kickoff datetime | ISO-8601 Datetime | Temporal Ordering |
| `prediction_cutoff` | datetime64 | Strict decision cutoff ($T_{\text{ko}} - 24\text{h}$) | ISO-8601 Datetime | Hard Boundary |
| `has_exact_kickoff_timestamp` | bool | Whether kickoff is verified exact | `True` (Tier 1) / `False` (Tier 2) | Data Filter |
| `temporal_tier` | string | Explicit confidence classification | `tier_1_verified_exact` / `tier_2_safe_assumptions` | Primary Slicing Key |
| `kickoff_time_source` | string | Provenance of kickoff timestamp | `fpl_official_utc`, `football_data_recorded`, `synthetic_default_1500_1945` | Audit Provenance |
| `home_team_id` | string | Canonical slug for home club | e.g. `arsenal`, `brentford` | Categorical Entity |
| `home_team_name` | string | Canonical display for home club | e.g. Arsenal, Brentford | Display |
| `away_team_id` | string | Canonical slug for away club | e.g. `chelsea`, `fulham` | Categorical Entity |
| `away_team_name` | string | Canonical display for away club | e.g. Chelsea, Fulham | Display |

---

## 3. Family 2: Pre-Match Elo Ratings & Probabilities (6 Columns)

Elo ratings provide an objective, zero-parameter-leakage measurement of long-term team strength. 
Ratings are calculated chronologically prior to kickoff using $K=20$, dynamic margin-of-victory multipliers, and a $+65$ Elo home advantage adjustment.

| Column Name | Data Type | Range / Distribution | Description | Calculation Logic |
| :--- | :--- | :--- | :--- | :--- |
| `home_elo_before` | float64 | $[1280.0, 2045.0]$ | Home team pre-match Elo rating | Rating updated after team's prior match |
| `away_elo_before` | float64 | $[1275.0, 2038.0]$ | Away team pre-match Elo rating | Rating updated after team's prior match |
| `elo_difference` | float64 | $[-580.0, +620.0]$ | Net pre-match rating differential | `home_elo_before - away_elo_before` |
| `elo_home_win_prob`| float64 | $[0.08, 0.91]$ | Model probability of home victory | Logistic formula with $+65$ home advantage |
| `elo_draw_prob` | float64 | $[0.11, 0.32]$ | Model probability of draw | Gaussian draw margin formula |
| `elo_away_win_prob`| float64 | $[0.04, 0.82]$ | Model probability of away victory | `1.0 - (elo_home_win_prob + elo_draw_prob)` |

*Note:* All probabilities are mathematically guaranteed to sum to exactly 1.000 across all 9,578 matches.

---

## 4. Family 3: Pre-Match Opening Betting Odds (14 Columns)

Opening market prices captured mid-week prior to kickoff. Implied probabilities are normalized to eliminate bookmaker vigorish ($\sum P = 1.0$).

| Column Name | Data Type | Range | Description | Missingness (Tier 1) |
| :--- | :--- | :--- | :--- | :---: |
| `b365_home_open` | float64 | $[1.07, 26.00]$ | Bet365 opening decimal odds for Home Win | 0.01% (1 match: #2450) |
| `b365_draw_open` | float64 | $[2.60, 15.00]$ | Bet365 opening decimal odds for Draw | 0.01% (1 match: #2450) |
| `b365_away_open` | float64 | $[1.12, 34.00]$ | Bet365 opening decimal odds for Away Win | 0.01% (1 match: #2450) |
| `b365_open_overround` | float64 | $[0.038, 0.082]$ | Bet365 bookmaker overround (margin) | 0.01% |
| `b365_open_implied_home_prob` | float64 | $[0.035, 0.895]$ | Fair implied probability of Home Win | 0.01% |
| `b365_open_implied_draw_prob` | float64 | $[0.062, 0.355]$ | Fair implied probability of Draw | 0.01% |
| `b365_open_implied_away_prob` | float64 | $[0.026, 0.852]$ | Fair implied probability of Away Win | 0.01% |
| `pinnacle_home_open` | float64 | $[1.09, 29.50]$ | Pinnacle opening decimal odds for Home Win | 9.11% |
| `pinnacle_draw_open` | float64 | $[2.65, 17.00]$ | Pinnacle opening decimal odds for Draw | 9.11% |
| `pinnacle_away_open` | float64 | $[1.14, 36.00]$ | Pinnacle opening decimal odds for Away Win | 9.11% |
| `pinnacle_open_overround` | float64 | $[0.018, 0.052]$ | Pinnacle bookmaker overround (sharper market) | 9.11% |
| `pinnacle_open_implied_home_prob` | float64 | $[0.031, 0.885]$ | Pinnacle fair implied probability Home Win | 9.11% |
| `pinnacle_open_implied_draw_prob` | float64 | $[0.055, 0.348]$ | Pinnacle fair implied probability Draw | 9.11% |
| `pinnacle_open_implied_away_prob` | float64 | $[0.024, 0.841]$ | Pinnacle fair implied probability Away Win | 9.11% |

> [!IMPORTANT]
> **Match 2450 Handling:** Bet365 opening odds for Match 2450 (Brentford vs Blackburn Rovers, 2019-02-02) was an impossible `0.0` in the raw data. To comply with strict verification rules, this inferred quote is set to `NaN` in all `b365_*_open` feature columns.

---

## 5. Family 4: Team-Level Overall Rolling Form (68 Columns)

These features measure rolling team performance across all competitions up to the strict prediction cutoff ($T - 24\text{h}$). Each metric is generated symmetrically for `home_*` and `away_*` across windows of 3, 5, and 10 matches.

### Sub-Features for Each Team (`home_` and `away_` prefixes):
- `prior_matches_count`: Integer count of completed historical matches available before cutoff. (Missing = 0).
- `rest_days`: Days elapsed since the team's previous completed match. (Range: 1.9 to 112 days).
- **Window 3 Features:**
  - `goals_scored_roll3`, `goals_conceded_roll3`, `goal_diff_roll3`
  - `shots_roll3`, `sot_roll3`, `corners_roll3`, `points_roll3`
  - `win_rate_roll3`, `draw_rate_roll3`, `loss_rate_roll3`
- **Window 5 Features:**
  - `goals_scored_roll5`, `goals_conceded_roll5`, `goal_diff_roll5`
  - `shots_roll5`, `sot_roll5`, `corners_roll5`, `fouls_roll5`, `cards_roll5`, `points_roll5`
  - `win_rate_roll5`, `draw_rate_roll5`, `loss_rate_roll5`
- **Window 10 Features:**
  - `goals_scored_roll10`, `goals_conceded_roll10`, `goal_diff_roll10`
  - `shots_roll10`, `sot_roll10`, `corners_roll10`, `points_roll10`
  - `win_rate_roll10`, `draw_rate_roll10`, `loss_rate_roll10`

*Missingness:* Exactly 0.21% across Tier 1, corresponding strictly to opening fixtures of the 2016/17 season where no prior history exists in the modern archive.

---

## 6. Family 5: Venue-Specific Rolling Form (20 Columns)

Captures home-advantage persistence and away-form resilience by filtering prior matches by venue (`is_home == is_home_fixture`). Generated symmetrically for `home_venue_*` and `away_venue_*`.

### Sub-Features for Each Team:
- `venue_prior_matches_count`: Total prior matches played at that venue before cutoff.
- **Window 3 Features:**
  - `venue_goals_scored_roll3`, `venue_goals_conceded_roll3`
- **Window 5 Features:**
  - `venue_goals_scored_roll5`, `venue_goals_conceded_roll5`
  - `venue_shots_roll5`, `venue_sot_roll5`, `venue_corners_roll5`, `venue_points_roll5`
  - `venue_win_rate_roll5`

*Missingness:* 0.39% in Tier 1, strictly representing opening venue fixtures with zero prior venue history.

---

## 7. Family 6: Squad-Level Pre-Match Player Intelligence (10 Columns)

Captures attacking depth, goal threat concentration, and physical congestion from individual player records.

| Feature Name | League Scope | Description | Aggregation Window | Missingness |
| :--- | :---: | :--- | :--- | :---: |
| `home_squad_prior_goals_sum` | PL Only | Total goals scored by current squad members in current season | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `away_squad_prior_goals_sum` | PL Only | Total goals scored by current squad members in current season | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `home_squad_prior_assists_sum` | PL Only | Total assists registered by squad members | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `away_squad_prior_assists_sum` | PL Only | Total assists registered by squad members | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `home_top_scorer_prior_goals` | PL Only | Goals scored by team's leading individual scorer | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `away_top_scorer_prior_goals` | PL Only | Goals scored by team's leading individual scorer | Season to Date ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `home_squad_prior_xg_sum` | PL Only | Squad cumulative Expected Goals (xG) | Available 2022/23+ | 78.9% (Earliest PL = NaN) |
| `away_squad_prior_xg_sum` | PL Only | Squad cumulative Expected Goals (xG) | Available 2022/23+ | 78.9% (Earliest PL = NaN) |
| `home_squad_minutes_14d` | PL Only | Total minutes accumulated by squad in past 14 days (fatigue) | Past 14 Days ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |
| `away_squad_minutes_14d` | PL Only | Total minutes accumulated by squad in past 14 days (fatigue) | Past 14 Days ($T - 24\text{h}$) | 50.9% (All Champ = NaN) |

### Key Forensic Safeguards Applied:
1. **Match Completion Rule:** Prior player matches are admitted if and only if $\text{kickoff\_ts} + 2.0\text{h} \le \text{cutoff}$, eliminating all 62 in-progress fixture overlaps.
2. **Transfer Resolution:** Player records are mapped to their actual club at the time of each match via fixture lookup, eliminating 1,080 retroactive mid-season transfer lookahead errors.

---

## 8. Family 7: Target Variables (10 Columns — Strictly Segregated)

These are the ground-truth outcomes of the match being predicted. **They must never be used as predictive inputs.**

| Target Column Name | Target Type | Values / Classes | Description |
| :--- | :--- | :--- | :--- |
| `target_full_time_home_goals` | Regression | Integer $[0, 9]$ | Full-time goals scored by home club |
| `target_full_time_away_goals` | Regression | Integer $[0, 9]$ | Full-time goals scored by away club |
| `target_full_time_result` | Multiclass | `'H'`, `'D'`, `'A'` | Canonical match result label |
| `target_home_win` | Binary | `1` (Home Win) or `0` | Binary target for home win classification |
| `target_draw` | Binary | `1` (Draw) or `0` | Binary target for draw classification |
| `target_away_win` | Binary | `1` (Away Win) or `0` | Binary target for away win classification |
| `target_total_goals` | Regression | Integer $[0, 12]$ | Total goals scored in match |
| `target_over_2_5` | Binary | `1` ($> 2.5$ goals) or `0` | Over/Under 2.5 goals market target |
| `target_btts` | Binary | `1` (Both Scored) or `0` | Both Teams To Score market target |
| `target_goal_difference` | Regression | Integer $[-9, +9]$ | Home goals minus away goals |

---

## 9. Family 8: Retrospective Benchmark Variables (16 Columns — Strictly Segregated)

These variables capture post-cutoff market closing prices and in-match performance box scores. **They are used exclusively for post-hoc model evaluation and betting market efficiency testing.**

- `benchmark_pinnacle_close_home`, `benchmark_pinnacle_close_draw`, `benchmark_pinnacle_close_away`
- `benchmark_pinnacle_close_overround`, `benchmark_pinnacle_close_implied_home`
- `benchmark_b365_close_home`, `benchmark_b365_close_draw`, `benchmark_b365_close_away`
- `benchmark_match_home_shots`, `benchmark_match_away_shots`
- `benchmark_match_home_sot`, `benchmark_match_away_sot`
- `benchmark_match_home_corners`, `benchmark_match_away_corners`
- `benchmark_home_elo_after`, `benchmark_away_elo_after`

---

## 10. Missingness Architecture & EDA Preparation Guidelines

### 10.1 Structured Missingness Patterns
1. **Opening Season Matches (0.21%):** For the first 1–2 fixtures of a season, 3-, 5-, and 10-match rolling features are genuinely `NaN`. In Phase 5, these should be handled by tree-native NaN handling (LightGBM/XGBoost) or filled with prior-season terminal averages, rather than mean-imputed across the entire dataset.
2. **Pinnacle Opening Odds (9.11%):** In certain early-season or low-liquidity matches, Pinnacle opening quotes were not recorded. Bet365 opening odds serve as a complete alternative ($< 0.02\%$ missing).
3. **Championship Player Features (100% NaN for Championship):** Because FPL tracks only the Premier League, joint models across both leagues must either omit player features or use league-specific models.
4. **FPL xG Features (54.6% in PL):** xG was only tracked from 2022/23 onwards. For long-term 2016–2026 models, basic player goals/assists/minutes provide continuous coverage.

### 10.2 Controlled Experiment Design: Tier 1 vs Master
To rigorously evaluate the impact of synthetic kickoff times on ML generalization:
- **Experiment A (Tier 1 Baseline):** Train and evaluate models strictly on the 7,922 Tier 1 matches.
- **Experiment B (Expanded Master):** Train models on all 9,578 matches, evaluating whether adding the 1,656 Tier 2 Championship matches improves out-of-sample performance on modern test sets or introduces noise.

---

## 11. Deliverables Index

1. **`data/processed/matches_prematch_24h_tier1.parquet`** (Primary Dataset: 7,922 rows x 161 cols)
2. **`data/processed/matches_prematch_24h_features.parquet`** (Full Master Dataset: 9,578 rows x 161 cols)
3. **`reports/leakage_remediation/feature_metadata_registry.csv`** (Machine-readable catalog of all 161 features)
4. **`reports/leakage_remediation/feature_dictionary_and_data_guide.md`** (This comprehensive documentation)
5. **`collectors/test_leakage_safety.py`** (16-test automated verification suite)
