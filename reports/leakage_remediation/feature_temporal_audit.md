# MatchLab: Complete Feature Temporal Audit & Availability Specification

**Audit Horizon:** T - 24 Hours Before Kickoff  
**Cutoff Rule:** `prediction_cutoff = kickoff_timestamp - 24 hours`  
**Dataset Audited:** [`data/processed/matches_prematch_24h_features.parquet`](file:///c:/Users/biniy/Desktop/MatchLab/data/processed/matches_prematch_24h_features.parquet) (9,578 rows, 159 columns)  
**Registry File:** [`reports/leakage_remediation/feature_availability_registry.csv`](file:///c:/Users/biniy/Desktop/MatchLab/reports/leakage_remediation/feature_availability_registry.csv)  

---

## 1. The 24-Hour Prediction Horizon Invariant

In MatchLab, every pre-match predictive model must operate under a strict temporal constraint:

$$\text{Information Available} \le T_{\text{cutoff}} = T_{\text{kickoff}} - 24\text{ hours}$$

Any data point whose generation, recording, or publication occurs after $T_{\text{cutoff}}$ is mathematically quarantined from the feature matrix $X$.

### Information Classification Hierarchy:
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Temporal Information Classification Matrix                      │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Classification Category  │ Definition & Temporal State │ Permitted Analytical Role     │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 1. Verified Safe         │ Proven available before     │ Primary Pre-Match Model Input │
│                          │ prediction cutoff           │ Features (X)                  │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 2. Unknown /             │ Pre-closing snapshot, but   │ Conditional Feature;          │
│    Insufficient Evidence │ exact scrape time unlogged  │ Documented with warning tag   │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 3. Target Variables      │ Generated at final whistle  │ Supervised Training Labels    │
│                          │ (T + 95 to 105 mins)        │ (Y) ONLY                      │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 4. Benchmark /           │ Closing odds (T - 0 min) or │ Retrospective Evaluation &    │
│    Quarantined Post-Match│ in-match box scores         │ CLV Analysis ONLY             │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

---

## 2. Complete Inventory of Features by Domain

The 159 columns of the leakage-safe pre-match dataset are categorized below:

### Group 1: Identifiers & Temporal Anchors (15 Columns) — *Verified Safe*
- **Fields:** `match_id`, `competition_id`, `competition_name`, `season_id`, `season_name`, `season_start_year`, `match_date`, `kickoff_time`, `kickoff_timestamp`, `prediction_cutoff`, `has_exact_kickoff_timestamp`, `home_team_id`, `home_team_name`, `away_team_id`, `away_team_name`.
- **Availability Rule:** Match fixtures, dates, and canonical clubs are published weeks or months in advance by the FA and EFL.
- **Timestamp Precision:** 
  - Premier League: **100.0% exact UTC kickoff timestamps** (derived from FPL API & Football-Data).
  - Championship (2019/20–2026/27): **100.0% exact kickoff timestamps** (Football-Data `Time`).
  - Championship (2016/17–2018/19): Standardized canonical schedule times (15:00 weekend / 19:45 weekday), explicitly flagged with `has_exact_kickoff_timestamp = False`.

---

### Group 2: Pre-Match Team Rolling Features (88 Columns) — *Verified Safe*
For both Home and Away teams independently, features are computed over trailing historical windows ($W \in [3, 5, 10]$):

1. **Overall Form (Last 3, 5, 10 Matches):**
   - `goals_scored_roll{3,5,10}`: Mean goals scored across prior matches.
   - `goals_conceded_roll{3,5,10}`: Mean goals conceded across prior matches.
   - `goal_diff_roll{3,5,10}`: Mean goal differential.
   - `shots_roll{3,5,10}`: Mean total shots taken.
   - `sot_roll{3,5,10}`: Mean shots on target taken.
   - `corners_roll{3,5,10}`: Mean corner kicks won.
   - `fouls_roll5`, `cards_roll5`: Discipline and aggression metrics.
   - `points_roll{3,5,10}`: Trailing points per game (3 for Win, 1 for Draw, 0 for Loss).
   - `win_rate_roll{3,5,10}`, `draw_rate_roll{3,5,10}`, `loss_rate_roll{3,5,10}`: Outcome frequencies.
2. **Venue-Specific Form (Last 3 and 5 Matches at Home/Away):**
   - Home team: `home_venue_goals_scored_roll{3,5}`, `home_venue_goals_conceded_roll{3,5}`, `home_venue_shots_roll5`, `home_venue_sot_roll5`, `home_venue_corners_roll5`, `home_venue_points_roll5`, `home_venue_win_rate_roll5`.
   - Away team: `away_venue_goals_scored_roll{3,5}`, `away_venue_goals_conceded_roll{3,5}`, `away_venue_shots_roll5`, `away_venue_sot_roll5`, `away_venue_corners_roll5`, `away_venue_points_roll5`, `away_venue_win_rate_roll5`.
3. **Rest & Congestion:**
   - `home_rest_days`, `away_rest_days`: Days elapsed since the team's most recent prior match.
4. **Sample Count Anchors:**
   - `home_prior_matches_count`, `away_prior_matches_count`: Exact count of prior matches available. When count is 0 (Matchday 1), all rolling averages are strictly `NaN` (no artificial imputation).

- **Temporal Availability Proof:** Every prior match included in team $T$'s rolling window was verified to have:
  $$T_{\text{match\_end}} = T_{\text{kickoff}} + 2\text{ hours} \le T_{\text{cutoff}}$$
  This completely rules out same-day leakage and enforces a strict lag ($\ge 1$).

---

### Group 3: Pre-Match Elo Ratings & Probabilities (6 Columns) — *Verified Safe*
- **Fields:** `home_elo_before`, `away_elo_before`, `elo_difference`, `elo_home_win_prob`, `elo_draw_prob`, `elo_away_win_prob`.
- **Availability Rule:** Computed strictly from the posterior ratings of both clubs after their immediately preceding matches.
- **Evidence:** Automated continuity audit confirmed **0 mismatches (0.0%)** across 9,578 matches. The rating update formula does not incorporate the current match outcome.

---

### Group 4: Pre-Match Bookmaker Odds (14 Columns) — *Unknown / Insufficient Timestamp Evidence*
- **Fields:** `b365_home_open`, `b365_draw_open`, `b365_away_open`, `b365_open_overround`, `b365_open_implied_home_prob`, `b365_open_implied_draw_prob`, `b365_open_implied_away_prob`, `pinnacle_home_open`, `pinnacle_draw_open`, `pinnacle_away_open`, `pinnacle_open_overround`, `pinnacle_open_implied_home_prob`, `pinnacle_open_implied_draw_prob`, `pinnacle_open_implied_away_prob`.
- **Availability Rule:** Football-Data.co.uk captures these odds mid-week as pre-closing prices (typically Friday afternoon for Saturday fixtures).
- **Classification & Caution:** Classified as **Unknown Timestamp Evidence** because Football-Data does not log row-level timestamp seconds. While industry knowledge confirms they are collected 24–48 hours before kickoff, models that demand 100% strict timestamp proof should train an odds-free model variant.

---

### Group 5: Pre-Match Player Intelligence (10 Columns, Premier League Only) — *Verified Safe*
- **Fields:** 
  - `home_squad_prior_goals_sum`, `away_squad_prior_goals_sum`: Cumulative goals scored by the club's active squad in prior gameweeks of that season.
  - `home_squad_prior_assists_sum`, `away_squad_prior_assists_sum`: Cumulative assists.
  - `home_top_scorer_prior_goals`, `away_top_scorer_prior_goals`: Prior goals of the club's leading scorer.
  - `home_squad_prior_xg_sum`, `away_squad_prior_xg_sum`: Cumulative squad xG prior to this matchday (2022/23+).
  - `home_squad_minutes_14d`, `away_squad_minutes_14d`: Total squad minutes played in trailing 14 days (fatigue/congestion proxy).
- **Availability Rule:** Derived strictly from gameweeks completed prior to $T_{\text{cutoff}}$.
- **Leakage Prevention:** **Zero in-match player minutes or fielded lineup selections are used**. This eliminates the severe lineup leakage present in earlier iterations.

---

### Group 6: Target Variables (10 Columns) — *Target Labels (Y Only)*
- **Fields:** `target_full_time_home_goals`, `target_full_time_away_goals`, `target_full_time_result`, `target_home_win`, `target_draw`, `target_away_win`, `target_total_goals`, `target_over_2_5`, `target_btts`, `target_goal_difference`.
- **Role:** Supervised training targets. Strictly segregated by the `target_*` prefix.

---

### Group 7: Retrospective Benchmarks & Post-Match Outcomes (16 Columns) — *Quarantined*
- **Fields:** 
  - Closing odds: `benchmark_pinnacle_close_home`, `benchmark_pinnacle_close_draw`, `benchmark_pinnacle_close_away`, `benchmark_pinnacle_close_overround`, `benchmark_pinnacle_close_implied_home`, `benchmark_b365_close_home`, `benchmark_b365_close_draw`, `benchmark_b365_close_away`.
  - In-match box scores: `benchmark_match_home_shots`, `benchmark_match_away_shots`, `benchmark_match_home_sot`, `benchmark_match_away_sot`, `benchmark_match_home_corners`, `benchmark_match_away_corners`.
  - Post-match Elo: `benchmark_home_elo_after`, `benchmark_away_elo_after`.
- **Role:** Exclusively reserved for Closing Line Value (CLV) evaluation and retrospective benchmarking. **Strictly forbidden from entering feature matrix X**.
