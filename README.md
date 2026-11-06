# MatchLab — Football Match Prediction Engine

MatchLab is an advanced machine-learning and sports analytics research platform designed to predict outcomes in professional English football (Premier League and EFL Championship) under strict **24-hour pre-match prediction horizons** ($T - 24.000\text{h}$) with zero data leakage.

---

## 1. Project Overview & Architectural Principles

MatchLab solves the core challenge of historical sports modeling: **temporal leakage**. In standard sports modeling, models often inadvertently condition on in-match statistics, closing betting odds, post-deadline player transfers, or delayed publication feeds. 

MatchLab enforces:
- **Strict 24-Hour Horizon:** Every feature is calculated exclusively using information demonstrably available at least 24 hours prior to kickoff.
- **Two-Tier Stratification:** 
  - **Tier 1 (7,922 matches):** Verified exact historical kickoff timestamps from official feeds (100% of Premier League from 2016/17 to 2026/27, and Championship from 2019/20 to 2026/27).
  - **Tier 2 (1,656 matches):** Safe under documented turnaround assumptions (Championship 2016/17–2018/19 with day-of-week canonical kickoffs).
- **Zero Leakage Segregation:** Post-match goals are segregated to `target_*`, and closing betting odds and in-match statistics are segregated to `benchmark_*`.

---

## 2. Directory Architecture

```text
MatchLab/
│
├── data/
│   ├── raw/                                # Immutable raw historical datasets (Football-Data, FPL, etc.)
│   ├── processed/                          # Partitioned, leakage-safe datasets (Parquet and CSV)
│   │   ├── matches_prematch_24h_tier1.*    # Primary dataset: 7,922 rows x 161 cols (Verified Exact)
│   │   ├── matches_prematch_24h_features.* # Master dataset: 9,578 rows x 161 cols (Tier 1 + Tier 2)
│   │   ├── matches_modern_2016_present.*   # Consolidated modern match archive
│   │   ├── player_gameweeks_2016_present.* # Cleaned FPL player observations
│   │   └── canonical_teams.csv             # Entity-harmonized club identifiers & aliases
│   └── matchlab.db                         # Unified SQLite database (table: matches_prematch_24h, view: tier1)
│
├── collectors/                             # Historical collection, entity harmonization & ingestion scripts
│   ├── download_football_data_co_uk.py     # Football-Data.co.uk scraper
│   ├── reconcile_matches.py                # Cross-source entity matching engine
│   ├── populate_database.py                # SQLite database ingestion
│   └── build_leakage_safe_features.py      # Pre-match 24h feature generation pipeline
│
├── features/                               # Feature engineering pipelines & transformers (Phase 5+)
├── models/                                 # Predictive model architectures & training scripts (Phase 6+)
├── evaluation/                             # Out-of-sample backtesting & betting efficiency simulation
├── notebooks/                              # Interactive research & exploratory analysis notebooks
├── config/                                 # Global constants, hyperparameter grids & competition configs
├── docs/                                   # Architectural diagrams, methodology specs & design docs
├── scripts/                                # Utility scripts & maintenance routines
│
├── reports/
│   ├── data_integration/                  # Phase 1-4 audit reports, registries, CSVs & test results
│   │   ├── final_data_integration_audit.md # Final sign-off audit report
│   │   ├── feature_dictionary_and_data_guide.md # 161-column detailed data dictionary
│   │   ├── feature_metadata_registry.csv   # Machine-readable column definitions & missingness
│   │   ├── player_data_final_verification.md # Audit of 1,080 transfer fixes & 62 overlap fixes
│   │   ├── season_coverage_audit.csv       # 22-season count reconciliation
│   │   ├── feature_temporal_provenance.csv # Source provenance & availability audit
│   │   └── leakage_validation_results.csv  # 16-test automated validation results
│   └── eda/                                # Phase 5 Exploratory Data Analysis outputs, plots & dashboard
│       ├── dashboard.html                  # Interactive analytics dashboard
│       └── plots/                          # Visualizations (goals, Elo, overround, shots)
│
├── tests/                                  # Automated adversarial test suite
│   ├── run_all_tests.py                    # Master test runner
│   ├── test_leakage_safety.py              # 16 value-level and structural leakage tests
│   └── test_elo_integrity.py               # Pre-match Elo rating calibration test
│
├── archive/                                # Archived scratch scripts & pre-remediation backups
├── requirements.txt                        # Pinned dependencies
├── README.md                               # This documentation
└── .gitignore                              # Git exclusion rules
```

---

## 3. Data Storage & Primary Datasets

All processed data is distributed in dual **Parquet** (optimized for ML training) and **CSV** formats in `data/processed/`:

1. **Primary Dataset (`matches_prematch_24h_tier1.parquet`):**
   - **Rows:** 7,922 matches
   - **Columns:** 161 (118 predictive features, 10 targets, 16 benchmarks, 17 metadata fields)
   - **Scope:** 100% of Premier League (2016–2027) and Championship (2019–2027) with exact recorded kickoffs.
2. **Master Dataset (`matches_prematch_24h_features.parquet`):**
   - **Rows:** 9,578 matches
   - **Columns:** 161
   - **Scope:** Complete modern archive (includes 1,656 Tier 2 Championship matches from 2016–2018).
3. **SQLite Database (`data/matchlab.db`):**
   - Table `matches_prematch_24h` (9,578 rows)
   - View `matches_prematch_24h_tier1` (`SELECT * FROM matches_prematch_24h WHERE temporal_tier = 'tier_1_verified_exact'`)

---

## 4. The 161-Feature Architecture

| Family | Columns | Description |
| :--- | :---: | :--- |
| **1. Metadata & Temporal Anchors** | 17 | `match_id`, dates, exact timestamps, `temporal_tier`, club IDs |
| **2. Pre-Match Elo Ratings** | 6 | `home_elo_before`, `away_elo_before`, `elo_difference`, win/draw/loss probs |
| **3. Pre-Match Opening Betting Odds** | 14 | Bet365 & Pinnacle open, bookmaker overrounds, fair implied probabilities |
| **4. Team Overall Rolling Form** | 68 | Windows 3, 5, 10: goals, shots, sot, corners, points, win/draw rates, rest days |
| **5. Venue-Specific Rolling Form** | 20 | Windows 3, 5: home-at-home / away-at-away goals, shots, points, win rates |
| **6. Squad Player Intelligence** | 10 | Premier League only: squad goals, assists, top scorer goals, 14d fatigue |
| **7. Supervised Target Variables** | 10 | Post-match outcomes: goals, `target_full_time_result` (`H`/`D`/`A`), over 2.5, BTTS |
| **8. Retrospective Benchmarks** | 16 | Closing odds, in-match box scores, post-match Elo ratings |

*For complete definitions, consult [`reports/data_integration/feature_dictionary_and_data_guide.md`](reports/data_integration/feature_dictionary_and_data_guide.md).*

---

## 5. How to Run the Pipeline and Validation Suite

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Rebuild Features
To rebuild the leakage-safe pre-match feature datasets from the modern match archive:
```bash
python collectors/build_leakage_safe_features.py
```

### Execute Test Suite
To run the automated adversarial leakage tests (16 tests across structural and numerical values):
```bash
python tests/run_all_tests.py
```
Or execute individually:
```bash
python tests/test_leakage_safety.py
python tests/test_elo_integrity.py
```

---

## 6. Audit & Sign-Off Documentation

- **Final Sign-Off Audit:** [`reports/data_integration/final_data_integration_audit.md`](reports/data_integration/final_data_integration_audit.md)
- **Feature Metadata Registry:** [`reports/data_integration/feature_metadata_registry.csv`](reports/data_integration/feature_metadata_registry.csv)
- **Player Data Verification:** [`reports/data_integration/player_data_final_verification.md`](reports/data_integration/player_data_final_verification.md)
- **Season Coverage Reconciliation:** [`reports/data_integration/season_coverage_audit.csv`](reports/data_integration/season_coverage_audit.csv)
- **Temporal Provenance Matrix:** [`reports/data_integration/feature_temporal_provenance.csv`](reports/data_integration/feature_temporal_provenance.csv)
- **Interactive EDA Dashboard:** [`reports/eda/dashboard.html`](reports/eda/dashboard.html)
