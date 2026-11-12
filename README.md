# MatchLab — Premier League Predictive Modeling & Bivariate Dixon-Coles Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![NumPy](https://img.shields.io/badge/NumPy-Foundational%20Math-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![SciPy](https://img.shields.io/badge/SciPy-Optimization%20%26%20GLM-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://scipy.org)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Leakage Tests](https://img.shields.io/badge/Leakage%20Tests-16%2F16%20Passed-10b981?style=for-the-badge&logo=checkmarx&logoColor=white)](tests/)
[![Dataset](https://img.shields.io/badge/Dataset-6%2C930%20Matches%20%7C%200%20Nulls-6366f1?style=for-the-badge)](data/processed/premier_league/)

> ⚽ **MatchLab** is an open-source machine learning and sports analytics engine for professional football. It implements an $L_2$-regularized **Dixon-Coles Bivariate Poisson Regression** model built on pure NumPy and SciPy foundations, trained across **18 Premier League seasons** (2008/09 to 2025/26) under strict, verifiable **24-hour pre-match zero-leakage horizons**.

---

## 🎯 Current Status & Final Goals

### 📊 Project Status (Where We Are Today)

MatchLab has completed **Phase 1 through Phase 6** of its research architecture:

- [x] **Unified Multi-Decade Dataset:** Cleaned, validated, and merged **6,930 Premier League matches** (2008/09 – 2025/26) across 116 strictly audited columns with **zero nulls, zero NaNs, and zero placeholders**.
- [x] **Adversarial Leakage Quarantine:** Built and verified a **16-test automated adversarial safety suite** ensuring zero temporal leakage—all features respect the strict 24-hour pre-match cutoff horizon ($T - 24.000\text{h}$). Closing odds and in-match statistics are isolated to retrospective benchmarks.
- [x] **Longitudinal Pre-Match Elo System:** Continuous club-level rating system tracking relative team strengths across promotion/relegation cycles without seasonal resets.
- [x] **Regularized Poisson GLM ($L_2$ Ridge):** Vectorized gradient descent estimating home and away goal intensities ($\lambda_h, \lambda_a$) with explicit parameter regularization to eliminate overfitting.
- [x] **Dixon-Coles Low-Score Correction:** Optimization of the bivariate correlation parameter $\rho \approx -0.0408$, correcting standard Poisson underestimation of low draws ($0-0, 1-1$).
- [x] **Full $10 \times 10$ Joint Probability Tensor:** Derives exact scoreline distributions, 1X2 match outcome probabilities, Over/Under 2.5 goals, and Both Teams to Score (BTTS).
- [x] **Empirical Benchmark Evaluation:** Out-of-sample 1X2 Ranked Probability Score (RPS) evaluated at **0.2055** against the **0.1956** Bet365 bookmaker consensus benchmark.

### 🚀 Final Goals (Where We Are Going)

- [ ] **Phase 7 — Automated Value Detection & Market Edge Identification:** Compute model fair odds against market opening prices to identify statistically significant positive expected value ($+EV$) opportunities.
- [ ] **Phase 8 — Dynamic Bankroll Management (Kelly Criterion):** Fractional Kelly staking simulation backtested against historical opening and closing market odds.
- [ ] **Phase 9 — $T - 1\text{h}$ Confirmed Lineup Module:** Real-time ingestion of confirmed 60-minute lineups and starting XI ratings to adjust pre-match $\lambda$ values.
- [ ] **Phase 10 — Multi-League Expansion:** Port the pipeline to other major European leagues (EFL Championship, La Liga, Serie A, and Bundesliga).
- [ ] **Phase 11 — Live Prediction API & Web Dashboard:** Lightweight FastAPI service serving real-time weekend match forecasts and scoreline matrices.

---

## 🏗️ System Architecture

```text
[ Raw Data Sources ]
  ├── Historical European Soccer Archive (2008–2016)
  └── Modern Premier League & Betting Archives (2016–2026)
            │
            ▼
[ Preprocessing & Zero-Leakage Pipeline ]
  ├── Canonical Club Harmonization & Aliases
  ├── Pre-Match Cutoff Verification (T - 24.000h)
  └── Rolling Form (5/10 Matches), Shots, Corners & Rest Days
            │
            ▼
[ Unified Clean Dataset: 6,930 Matches x 116 Features ]
  ├── Train Split: 2008/09 – 2023/24 (6,080 matches)
  └── Test Split:  2024/25 – 2025/26 (760 matches)
            │
            ▼
[ Core Mathematical Engine (NumPy / SciPy) ]
  ├── Home Poisson GLM: log(λ_h) = β_0^h + X β^h  (L2 Ridge)
  ├── Away Poisson GLM: log(λ_a) = β_0^a + X β^a  (L2 Ridge)
  └── Dixon-Coles Bivariate Correlation Layer: τ_ρ(x, y)
            │
            ▼
[ 10 x 10 Joint Probability Matrix per Match ]
  ├── 1X2 Win / Draw / Loss Probabilities (RPS = 0.2055)
  ├── Over / Under 2.5 Goals (Brier = 0.2486)
  ├── Both Teams To Score (BTTS Brier = 0.2473)
  └── Exact Score Guessing (Top-1: 11.7%, Top-3: 32.4%)
```

---

## 📈 Empirical Model Performance

Tested out-of-sample on **760 matches** across the 2024/25 and 2025/26 seasons:

| Metric | Naive League Average | Baseline Poisson | MatchLab Dixon-Coles | Bet365 Market Consensus |
|:---|:---:|:---:|:---:|:---:|
| **Features Conditioned** | None | Raw Goal Counts | **19 Curated Fundamentals** | Full Market Liquidity |
| **Optimization** | Sample Mean | Standard GD | **Vectorized GD + $L_2$ Regularization** | Continuous Bookmaker Pricing |
| **Home Test NLL** | 1.5507 | 1.5302 | **1.5035** | — |
| **Away Test NLL** | 1.4625 | 1.4299 | **1.4212** | — |
| **Joint Test NLL** | 3.0132 | 2.9589 | **2.9234** | — |
| **Dixon-Coles $\rho$** | — | -0.0385 | **-0.0408** | — |
| **1X2 Ranked Probability Score (RPS)** | 0.2285 | 0.2142 | **0.2055** | **0.1956** |
| **Top-1 Exact Score Hit Rate** | 4.00% (random) | 9.4% | **11.71%** (89 / 760) | — |
| **Top-3 Scorelines Hit Rate** | 12.00% (random) | 26.1% | **32.37%** (246 / 760) | — |
| **Top-5 Scorelines Hit Rate** | 20.00% (random) | 38.5% | **45.92%** (349 / 760) | — |
| **1X2 Direction Accuracy** | 33.33% (random) | 46.2% | **51.18%** (389 / 760) | — |

---

## 📁 Repository Structure

```text
MatchLab/
├── data/
│   └── processed/
│       └── premier_league/
│           ├── pl_matches_all_seasons_clean.parquet   # 6,930 matches x 116 clean features
│           ├── pl_matches_all_seasons_clean.csv       # Dual CSV export
│           └── column_names.txt                       # Catalog of all 116 audited columns
│
├── notebooks/
│   ├── 01_exploring_pl_dataset_numpy_draft.ipynb      # Clean, runnable student/practitioner draft notebook
│   └── 01_exploring_pl_dataset_numpy.ipynb            # Extended reference notebook with diagnostic plots
│
├── scripts/
│   ├── train_dixon_coles_model.py                     # Headless model training & evaluation runner
│   └── build_merged_pl_dataset.py                     # Dataset creation and data verification script
│
├── tests/
│   ├── run_all_tests.py                               # Master test suite runner (16/16 passing)
│   ├── test_leakage_safety.py                         # Adversarial temporal leakage test suite
│   └── test_elo_integrity.py                          # Longitudinal Elo continuity tests
│
├── reports/
│   ├── eda/plots/                                     # Diagnostic visualizations (loss curves, calibration, heatmaps)
│   └── data_integration/                              # Audits, feature catalogs, and leakage validation logs
│
├── requirements.txt                                   # Python dependencies
└── README.md                                          # Project documentation
```

---

## 🛠️ Quickstart & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/localmaximumx/MatchLab.git
cd MatchLab
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run the Adversarial Test Suite
Verify that all 16 zero-leakage constraints pass:
```bash
python tests/run_all_tests.py
```

### 4. Train the Dixon-Coles Model Headlessly
```bash
python scripts/train_dixon_coles_model.py
```

### 5. Open the Notebooks
To explore the implementation step-by-step:
```bash
jupyter notebook notebooks/01_exploring_pl_dataset_numpy_draft.ipynb
```

---

## 🔬 Mathematical Methodology

### 1. Regularized Poisson Goal Intensity
Each match's expected goals $\lambda_i = \exp(\mathbf{x}_i^T \boldsymbol{\beta})$ is trained by minimizing the $L_2$-penalized negative log-likelihood:
$$\mathcal{L}(\boldsymbol{\beta}) = \frac{1}{N} \sum_{i=1}^N \left( \exp(\mathbf{x}_i^T \boldsymbol{\beta}) - y_i (\mathbf{x}_i^T \boldsymbol{\beta}) + \ln(y_i!) \right) + \frac{1}{2} \alpha \sum_{j=1}^p \beta_j^2$$
Where the intercept $\beta_0$ remains unpenalized to preserve the natural league scoring rate.

### 2. Dixon-Coles Bivariate Adjustment
To correct for interdependence in low-scoring games, the joint probability is modified by $\tau_\rho(x, y)$:
$$P(X=x, Y=y) = \tau_\rho(x, y) \cdot P_{\text{Poisson}}(X=x \mid \lambda_h) \cdot P_{\text{Poisson}}(Y=y \mid \lambda_a)$$
$$\tau_\rho(x, y) = \begin{cases}
1 - \lambda_h \lambda_a \rho & x=0, y=0 \\
1 + \lambda_h \rho & x=0, y=1 \\
1 + \lambda_a \rho & x=1, y=0 \\
1 - \rho & x=1, y=1 \\
1 & \text{otherwise}
\end{cases}$$
With optimal $\rho \approx -0.0408$, low draws ($0-0$ and $1-1$) are boosted by $+4\%$ to $+6\%$, while $1-0$ and $0-1$ are slightly damped, providing superior calibration.

---

## 📜 License
This project is open-source under the MIT License. Data sourced from Football-Data.co.uk and open sports analytics repositories for research and non-commercial educational purposes.
