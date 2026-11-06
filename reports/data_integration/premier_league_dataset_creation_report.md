# MatchLab — Premier League Dataset Creation Report

**Creation Date:** 2026-11-06  
**Destination Directory:** `data/processed/premier_league/`  
**Sources:** `data/processed/matches_prematch_24h_features.parquet` and `matches_prematch_24h_tier1.parquet`  
**Filter Applied:** `competition_id == 'premier-league'`  
**Status:** Certified & Verified Exact

---

## 1. Executive Summary

Separate, standalone Premier League datasets were prepared from the verified Master and Tier 1 integrated datasets.
Because 100% of Premier League fixtures have verified exact kickoff timestamps (derived from official Fantasy Premier League UTC feeds and Football-Data recorded times), all 3,890 Premier League matches belong to **Tier 1 (Verified Exact)**.

Consequently, `pl_matches_master.parquet` and `pl_matches_tier1.parquet` contain the identical, verified set of **3,890 historical Premier League matches** spanning the 2016/17 through 2026/27 seasons.

---

## 2. Generated Artifacts

| Dataset Artifact | File Path | Format | Row Count | Column Count | File Size |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **PL Master Parquet** | `data/processed/premier_league/pl_matches_master.parquet` | Parquet | **3,890** | **161** | ~850 KB |
| **PL Master CSV** | `data/processed/premier_league/pl_matches_master.csv` | CSV | **3,890** | **161** | ~3.6 MB |
| **PL Tier 1 Parquet** | `data/processed/premier_league/pl_matches_tier1.parquet` | Parquet | **3,890** | **161** | ~850 KB |
| **PL Tier 1 CSV** | `data/processed/premier_league/pl_matches_tier1.csv` | CSV | **3,890** | **161** | ~3.6 MB |

---

## 3. Season-by-Season Breakdown (Premier League)

| Season Name | Season Slug | Total Matches | Tier 1 Count | Tier 2 Count | Exact Kickoff % | Kickoff Time Source |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **2016/2017** | `2016-2017` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2017/2018** | `2017-2018` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2018/2019** | `2018-2019` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2019/2020** | `2019-2020` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2020/2021** | `2020-2021` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2021/2022** | `2021-2022` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2022/2023** | `2022-2023` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2023/2024** | `2023-2024` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2024/2025** | `2024-2025` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2025/2026** | `2025-2026` | 380 | 380 | 0 | 100.0% | Official FPL UTC Feed |
| **2026/2027** | `2026-2027` | 90 | 90 | 0 | 100.0% | Official FPL UTC Feed |
| **Total** | **All 11 Seasons** | **3,890** | **3,890** | **0** | **100.0%** | **100% Verified Exact** |

---

## 4. Verification Check Matrix

| Check ID | Verification Rule | Expected Result | Observed Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **CHK-01** | Competition Isolation | `['premier-league']` | `['premier-league']` | **PASS** |
| **CHK-02** | PL Master Row Count | 3,890 | 3,890 | **PASS** |
| **CHK-03** | PL Tier 1 Row Count | 3,890 | 3,890 | **PASS** |
| **CHK-04** | Duplicate Match IDs | 0 duplicates | 0 duplicates (3,890 distinct) | **PASS** |
| **CHK-05** | Column Count & Order | 161 columns | 161 columns (100% matched) | **PASS** |
| **CHK-06** | Value-Level Data Fidelity | Identical to source | Identical (bit-exact assertions) | **PASS** |
| **CHK-07** | Source Preservation | 9,578 and 7,922 rows | Master: 9,578; Tier 1: 7,922 | **PASS** |

---

## 5. Usage in Future Phases

- **Dedicated Premier League Models:** Can be loaded directly from `data/processed/premier_league/pl_matches_tier1.parquet`.
- **Player Feature Analysis:** Full access to all 10 squad-level player intelligence features (goals, assists, 14-day fatigue, xG from 2022/23), which have 100% non-null coverage for Premier League fixtures.
- **Controlled Comparison:** Enables seamless benchmarking against joint PL + Championship models without filtering overhead.
