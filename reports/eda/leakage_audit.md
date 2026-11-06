# MatchLab Phase 4: Data Leakage, Temporal Integrity & Look-Ahead Risk Audit

**Audit Date:** 2026-11-05  
**Context:** Pre-Match Prediction & Systematic Betting Modeling  
**Primary Warning:** Merely sorting fixtures chronologically does **not** ensure zero data leakage. Every input variable must be strictly evaluated against the exact timeline of pre-match information availability.

---

## 1. The Pre-Match Prediction Timeline & Leakage Taxonomy

In systematic sports betting, predictions are executed at specific decision points before kickoff:
- **T-72 to T-24 Hours (Early Market):** Opening odds available; early team news; no official lineups.
- **T-75 to T-60 Minutes (Lineup Release):** Official starting XIs announced; closing odds begin sharp price discovery.
- **T-0 (Kickoff Whistle):** Closing odds locked; all pre-match betting ceases.
- **T+90 to T+105 Minutes (Final Whistle):** Final score, actual match statistics, player minutes, substitutions, and referee cards are recorded.

Any feature derived from events occurring after the prediction decision point constitutes **look-ahead bias (data leakage)**. Models trained on leaked data will produce inflated backtest profits but will catastrophically fail in real-time execution.

---

## 2. Field-by-Field Temporal Classification of the Master Dataset

Every column in `matches_modern_2016_present.parquet` has been audited and classified into four distinct temporal categories:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           Temporal Information Classification                           │
├────────────────────┬──────────────────────────────────────┬─────────────────────────────┤
│ Category           │ Description                          │ Analytical Usage Permitted  │
├────────────────────┼──────────────────────────────────────┼─────────────────────────────┤
│ 1. TARGETS         │ Post-match match outcomes to predict │ Model labels (Y) ONLY       │
│ 2. IN-MATCH STATS  │ Box-score actions during 90 minutes  │ Post-match outcome / Target │
│                    │                                      │ (NEVER raw pre-match feature│
│ 3. CLOSING ODDS    │ Market prices at T-0 minutes         │ Benchmark / CLV metric ONLY │
│ 4. PRE-MATCH PURE  │ Known prior to match day             │ SAFE Pre-Match Features (X) │
└────────────────────┴──────────────────────────────────────┴─────────────────────────────┘
```

### Complete Field Classification Table:

| Column Name | Actual Timing | Category | Can Be Used as Raw Model Feature? | Required Transformation |
|---|:---:|:---:|:---:|---|
| `full_time_home_goals` | T + 95 min | **Target** | **NO (Target)** | Predictand only |
| `full_time_away_goals` | T + 95 min | **Target** | **NO (Target)** | Predictand only |
| `full_time_result` | T + 95 min | **Target** | **NO (Target)** | Predictand only |
| `half_time_home_goals` | T + 45 min | **Target** | **NO (Target)** | HT predictand only |
| `home_shots` / `away_shots` | T + 95 min | **In-Match** | **NO (LEAKAGE)** | Trailing rolling average (lag $\ge 1$) |
| `home_shots_on_target` | T + 95 min | **In-Match** | **NO (LEAKAGE)** | Trailing rolling average (lag $\ge 1$) |
| `home_corners` / `away_corners` | T + 95 min | **In-Match** | **NO (LEAKAGE)** | Trailing rolling average (lag $\ge 1$) |
| `home_fouls` / `away_fouls` | T + 95 min | **In-Match** | **NO (LEAKAGE)** | Trailing rolling average (lag $\ge 1$) |
| `home_yellow_cards` / `red_cards` | T + 95 min | **In-Match** | **NO (LEAKAGE)** | Trailing rolling average (lag $\ge 1$) |
| `home_elo_before` | T - 24 hrs | **Pre-Match Pure** | **YES** | Safe pre-match strength anchor |
| `away_elo_before` | T - 24 hrs | **Pre-Match Pure** | **YES** | Safe pre-match strength anchor |
| `elo_home_win_prob` | T - 24 hrs | **Pre-Match Pure** | **YES** | Safe baseline probability |
| `home_elo_after` | T + 95 min | **Post-Match** | **NO (LEAKAGE)** | Post-match posterior update |
| `b365_home` (Opening) | T - 48 hrs | **Pre-Match Pure** | **YES** | Safe early market price |
| `pinnacle_home` (Opening) | T - 24 hrs | **Pre-Match Pure** | **YES** | Safe early sharp price |
| `pinnacle_close_home` | T - 1 min | **Closing Market** | **CONDITIONAL** | Benchmark only; NOT for early models |
| `home_lineup_value_m` | T + 95 min | **In-Match Leakage** | **NO (LEAKAGE)** | Must use trailing squad value |
| `home_players_fielded` | T + 95 min | **In-Match Leakage** | **NO (LEAKAGE)** | Must use historical squad depth |
| `home_squad_xg` | T + 95 min | **In-Match Leakage** | **NO (LEAKAGE)** | Must use trailing player xG |

---

## 3. Forensic Leakage Investigations & Risk Analysis

### Risk 1: In-Match Box-Score Contamination (`LEAK_01`)
*Severity: Critical*

- **Hazard:** The columns `home_shots`, `home_shots_on_target`, `home_corners`, and `home_fouls` represent the **actual physical events of the match being predicted**.
- **The Pitfall:** If an analyst trains a model predicting `target_home_win` using `home_shots` as an input feature, the model will discover that teams with 15+ shots win 75% of the time. The model will appear to achieve an 80% accuracy score. But in the real world, **you do not know how many shots a team will take before the match begins**.
- **Enforced Correction for Phase 5:**
  - Raw in-match statistics must **never** be included in feature matrix $X$.
  - All box-score metrics must be converted into **historical rolling statistics** using strictly past matches:
    $$\text{RollingShots}_{t} = \frac{1}{K}\sum_{i=1}^{K} \text{Shots}_{t-i}$$
  - A strict **lag of at least 1 match** ($t-1$) must be applied.

---

### Risk 2: Closing Line Value (CLV) Look-Ahead Bias (`LEAK_02`)
*Severity: Critical*

- **Hazard:** `pinnacle_close_home`, `pinnacle_close_draw`, and `pinnacle_close_away` are recorded minutes before kickoff.
- **The Pitfall:** If MatchLab is designed to recommend betting selections on Friday evening (when users place bets), using Sunday afternoon's Pinnacle closing odds as an input feature would represent look-ahead bias. The closing line embodies all market information that emerged over the weekend.
- **Enforced Correction for Phase 5:**
  - If predicting at market open (T - 24h to T - 48h): **Use opening odds only (`b365_home`, `pinnacle_home`)**.
  - Closing odds (`pinnacle_close_home`) must be reserved exclusively as an **evaluation benchmark**:
    $$\text{CLV} = \frac{\text{Closing Odds}}{\text{Bet Odds}} - 1.0$$
    Beating the closing line is the gold standard of betting alpha.

---

### Risk 3: Player Lineup Aggregation Contamination (`LEAK_03`)
*Severity: High*

- **Hazard:** In `build_modern_dataset_2016_present.py`, the aggregated columns `home_lineup_value_m` and `home_squad_xg` were constructed by filtering `player_gameweeks` to players with `minutes > 0` in that specific game.
- **The Pitfall:**
  1. Official team lineups are only announced 60–75 minutes before kickoff.
  2. Substitutes who play 15 minutes cannot be known before the 75th minute of the actual match.
  3. `home_squad_xg` was the sum of xG generated *in that match*.
- **Enforced Correction for Phase 5:**
  - Drop `home_squad_xg` and `home_lineup_value_m` from the pre-match fixture feature table.
  - In Phase 5, engineer **Pre-Match Player Availability Features**:
    - Trailing 5-game xG of the club's top 3 goalscorers.
    - Injury/suspension status prior to kickoff.
    - Historical squad rotation metrics based on trailing minutes.

---

### Risk 4: Elo Rating Purity Audit (`LEAK_04`)
*Severity: Low (Verified Clean)*

- **Investigation:** We audited whether `home_elo_before` could have inadvertently incorporated the result of the target match.
- **Findings:**
  - In Sean Elvidge's methodology, `HomeRank_before` is identical to the posterior rating (`HomeRank_after`) of that club's immediately preceding fixture.
  - The rating update occurs strictly post-match:
    $$\text{Elo}_{t} = \text{Elo}_{t-1} + K \cdot (\text{Actual} - \text{Expected})$$
  - The probabilities (`elo_home_win_prob`) are derived solely from `home_elo_before`, `away_elo_before`, and a historical home field constant (+65 Elo).
- **Status:** **Zero leakage detected**. Pre-match Elo ratings are safe for feature engineering.

---

## 4. Mandatory Pre-Modeling Rules for Phase 5

To ensure 100% scientific validity during Phase 5 feature engineering and Phase 6 modeling, the following rules must be codified into the pipeline:

1. **Strict Temporal Splitting (No Random K-Fold):**
   - Cross-validation must use **Walk-Forward Expanding Window Validation** (e.g. Train on 2016–2020, Validate on 2020/21; Train on 2016–2021, Validate on 2021/22).
   - Standard randomized $K$-fold cross-validation is strictly forbidden as it shuffles future matches into training folds.
2. **Lag-1 Minimum for All Rolling Aggregates:**
   - Every moving average (points per game, shots per game, goals conceded) must exclude match $t$.
3. **Rest Days Calculation Boundary:**
   - Rest days must be calculated from the previous official match date to the current match date.
4. **Explicit Decision Time Parameter:**
   - The modeling pipeline must accept a configuration flag: `--prediction-horizon [open_market | confirmed_lineups]`.
   - If `open_market` is selected, all features depending on confirmed starting XIs or closing prices are mathematically stripped from the training pipeline.
