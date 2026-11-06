# MatchLab Phase 4: Exploratory Data Analysis & Empirical Football Analytics

**Analysis Scope:** 9,578 Matches across Premier League & EFL Championship (2016/17 – 2026/27)  
**Player Scope:** 257,783 Player Gameweek Observations (11 Seasons)  
**Visualizations Directory:** [`reports/phase_4_data_analysis/plots/`](file:///c:/Users/biniy/Desktop/MatchLab/reports/phase_4_data_analysis/plots/)  

---

## 1. Executive Statistical Profile

Empirical analysis of 9,578 matches across 11 modern English football seasons establishes robust statistical baselines that will govern our Phase 5 machine learning modeling:

```
┌────────────────────────────────────────────────────────────────────────┐
│               Modern Era English Football Statistical Baseline         │
├──────────────────────────────────────┬─────────────────────────────────┤
│ Metric                               │ Value (9,578 Modern Matches)    │
├──────────────────────────────────────┼─────────────────────────────────┤
│ Home Win Frequency                   │ 43.86% (4,201 matches)          │
│ Draw Frequency                       │ 25.05% (2,399 matches)          │
│ Away Win Frequency                   │ 31.09% (2,978 matches)          │
│ Home Goal Advantage (Avg Goals)      │ 1.52 Home vs 1.15 Away (+0.37)  │
│ Over 2.5 Goals Frequency             │ 50.48% (Near 50/50 equilibrium) │
│ Both Teams To Score (BTTS) Frequency │ 51.94% (4,975 matches)          │
│ Premier League Average Goals/Game    │ 2.832 goals per game            │
│ EFL Championship Average Goals/Game  │ 2.557 goals per game            │
│ Shot Conversion Rate (SOT -> Goal)   │ ~31.8% of shots on target       │
│ Bet365 Average Bookmaker Vig         │ 4.89% (Opening market margin)   │
│ Pinnacle Closing Average Vig         │ 2.72% (Sharp market margin)     │
└──────────────────────────────────────┴─────────────────────────────────┘
```

---

## 2. Competition & Season Dynamics

### A. Goals per Match: Premier League vs EFL Championship
Across all 11 modern seasons, the **Premier League exhibits a statistically significant higher goal scoring environment** than the EFL Championship ($p < 10^{-12}$):

- **Premier League (Tier 1):** Mean **2.832 goals** per match.
- **EFL Championship (Tier 2):** Mean **2.557 goals** per match.
- **Goal Gap:** The Premier League averages **+0.275 more goals per game** (approximately 105 more goals per 380-game season).

![Goal Distributions](plots/01_goals_distribution_pl_vs_championship.png)

### B. Result Distribution Stability
The distribution of 1X2 outcomes across the 11-season period demonstrates strong macro stability:

| Outcome | Matches | Percentage | Typical Decimal Fair Odds |
|---|:---:|:---:|:---:|
| **Home Win (H)** | 4,201 | **43.86%** | 2.28 |
| **Draw (D)** | 2,399 | **25.05%** | 3.99 |
| **Away Win (A)** | 2,978 | **31.09%** | 3.22 |
| **Total** | 9,578 | **100.00%** | — |

*Key Modeling Takeaway:* A naive baseline that always predicts "Home Win" achieves 43.86% accuracy, but would lose money against bookmakers due to the 4.89% vigorish. An ML classifier must beat the market-implied probabilities, not simply maximize raw accuracy.

---

## 3. Goals & Scoring Distributions

### A. Exact Total Goals Frequency
Football goals follow an over-dispersed Poisson distribution. In our 9,578 matches, exact total goals occurred with the following empirical frequencies:

| Total Goals | Match Count | Percentage | Cumulative |
|:---:|:---:|:---:|:---:|
| **0 Goals (0-0)** | 748 | **7.81%** | 7.81% |
| **1 Goal** | 1,592 | **16.62%** | 24.43% |
| **2 Goals** | 2,408 | **25.14%** | 49.57% |
| **3 Goals** | 2,139 | **22.33%** | 71.90% |
| **4 Goals** | 1,413 | **14.75%** | 86.65% |
| **5+ Goals** | 1,278 | **13.34%** | 100.00% |

![Goal Frequencies & Betting Targets](plots/02_goal_frequencies_and_betting_targets.png)

### B. Binary Betting Market Thresholds
- **Over 1.5 Goals:** **75.57%** (only 24.4% of games end with 0 or 1 goal).
- **Over 2.5 Goals:** **50.48%** (virtually an even-money market across the entire 11-year dataset).
- **Over 3.5 Goals:** **28.10%**.
- **Both Teams To Score (BTTS - Yes):** **51.94%**.

---

## 4. In-Match Box-Score Statistics

Analysis of 9,577 modern matches with complete box-scores reveals the physical mechanics underlying goal generation:

![Shots, Corners & Dominance](plots/03_shots_corners_and_home_dominance.png)

### A. Home Field Dominance Across In-Match Statistics
Home teams systematically outperform away teams across every offensive category:

| In-Match Metric | Home Team Mean | Away Team Mean | Home Advantage Ratio |
|---|:---:|:---:|:---:|
| **Goals** | **1.52** | 1.15 | **+32.2%** |
| **Total Shots** | **13.56** | 11.23 | **+20.7%** |
| **Shots on Target** | **4.64** | 3.82 | **+21.5%** |
| **Corner Kicks** | **5.71** | 4.69 | **+21.7%** |
| **Fouls Committed**| 10.98 | **11.45** | Away teams commit +4.3% more fouls |
| **Yellow Cards** | 1.74 | **1.96** | Away teams receive +12.6% more yellows |

### B. The Shot-to-Goal Conversion Law
- On average, clubs score **0.318 goals per shot on target** (roughly 1 goal for every 3.15 shots on target).
- The correlation between **Shots on Target and Goals** ($r = 0.584$) is significantly stronger than the correlation between **Total Shots and Goals** ($r = 0.381$).
- Corners have a modest correlation with goals ($r = 0.162$), reflecting that only ~2.8% of corner kicks result directly in a goal in modern professional football.

---

## 5. Elo Rating Dynamics & Calibration

The dataset includes longitudinal Elo ratings derived from the World Football Elo framework, initialized prior to kickoff for all 9,578 matches.

![Elo Rating Distribution & Calibration](plots/04_elo_rating_distribution_and_calibration.png)

### A. Elo Rating Range Across English Tiers
- **Premier League Elite (Manchester City, Liverpool, Arsenal):** Peak ratings between **1,850 and 2,080**.
- **Premier League Mid-Table:** **1,500 to 1,680**.
- **Championship Top-Tier:** **1,350 to 1,520**.
- **Championship Relegation Candidates:** **1,050 to 1,220**.

### B. Mathematical Calibration & Home Field Parameter
- When two clubs have equal ratings (`elo_difference ~ 0`), the Elo system issues a **43.0% Home Win probability** vs a **28.8% Away Win probability** (and 28.2% Draw). This corresponds to a built-in home advantage parameter of approximately **+65 to +70 Elo points**.
- **Reliability Diagram:** The empirical win rate across 8 predicted probability bins aligns closely with the $y = x$ perfect calibration diagonal, confirming that the historical Elo probabilities are mathematically sound.
- **Brier Score:** The Elo Home Win Brier score is **0.2253**.

---

## 6. Betting Markets, Margins & Price Efficiency

![Betting Overrounds & Market Drift](plots/05_betting_overround_and_market_drift.png)

### A. Bookmaker Vigorish (Overround) Comparison
- **Bet365 Opening Odds Margin:** Mean **4.89%** (standard deviation: 1.12%).
  - Lowest margin: 1.69% (high-profile PL broadcast games).
  - Highest margin: 16.67% (isolated lower-tier anomalies).
- **Pinnacle Closing Odds Margin:** Mean **2.72%** (standard deviation: 0.64%).
  - Pinnacle operates with almost half the margin of retail bookmakers, confirming its status as the world's sharpest market.

### B. Informational Hierarchy & Model Benchmarking
We evaluated the predictive power of each source using the **Brier Score** on Home Wins (lower score indicates superior probabilistic accuracy):

| Benchmark Predictor | Brier Score (Home Win) | Predictive Rank |
|---|:---:|:---:|
| **Pinnacle Closing Implied Probability** | **0.21958** | **#1 (Sharpest Global Benchmark)** |
| **Bet365 Opening Implied Probability** | **0.22018** | **#2 (Strong Retail Market)** |
| **Pre-Match Team Elo Rating** | **0.22531** | **#3 (Statistical Baseline)** |

*Critical Insight:* Pinnacle closing odds reflect all late-breaking information (lineups, weather, sharp betting volume). Any ML model that hopes to generate genuine betting alpha must achieve a Brier score and log loss competitive with Bet365 opening odds, using only pre-match information available prior to market close.

### C. Odds Drift (Movement Between Open and Close)
- In 92% of matches, Pinnacle odds moved less than $\pm 10\%$ between opening and closing.
- In **7 matches (0.08%)**, extreme odds movements ($> 50\%$) occurred. Forensic inspection revealed that these matches coincided with catastrophic breaking news (e.g., star starting goalkeepers or strikers ruled out with COVID-19/injuries an hour before kickoff).

---

## 7. Player Gameweek Tracking & Distributions

![Player Minutes & xG](plots/06_player_minutes_and_xg_distribution.png)

### A. Participation Profiles
Across 257,783 player gameweek records:
- **Zero Minutes (Benched / Unused Subs / Reserves):** **70.2%** of all weekly player records. In any given gameweek, only ~280 out of ~800 rostered players log minutes on the pitch.
- **Full 90 Minutes:** **20.4%** of active appearances.
- **Substitutes (1 to 45 mins):** **9.4%** of active appearances.

### B. Expected Goals (xG) Characteristics
- When an active player registers non-zero expected goals in a match, the distribution is heavily right-skewed:
  - Median xG: **0.18**.
  - 75th Percentile: **0.42**.
  - 95th Percentile: **0.95**.
  - Outliers ($> 1.5$ xG): Elite strikers with multiple big chances (e.g., Erling Haaland, Mohamed Salah).
- **Scope Restriction:** Official Opta player xG is natively populated in FPL records from **2022/23 onwards**. For 2016–2021, player goal output must rely on actual goals/assists or archived Understat metrics.
