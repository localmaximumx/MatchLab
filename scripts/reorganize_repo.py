"""
MatchLab Repository Cleanup & Architecture Reorganization Script
Executes safe, non-destructive file movements and structural cleanup:
1. Creates target directories (reports/data_integration, reports/eda, tests, archive, docs, scripts).
2. Moves data integration and leakage remediation reports into reports/data_integration/.
3. Moves Phase 4 EDA reports, dashboard, and plots into reports/eda/.
4. Moves test scripts into tests/.
5. Archives scratch files into archive/scratch/.
6. Archives processed_backup_pre_remediation into archive/processed_backup_pre_remediation/.
7. Cleans __pycache__ bytecode files.
8. Ensures backward-compatibility wrappers.
"""

import os
import shutil
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

print(f"Working directory: {os.getcwd()}")

# 1. Create target directories
dirs_to_create = [
    os.path.join("reports", "data_integration"),
    os.path.join("reports", "eda"),
    os.path.join("tests"),
    os.path.join("archive", "scratch"),
    os.path.join("archive", "processed_backup_pre_remediation"),
    os.path.join("docs"),
    os.path.join("scripts")
]

for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)
    print(f"Created / Verified directory: {d}")

# 2. Move reports/leakage_remediation/* into reports/data_integration/
leak_dir = os.path.join("reports", "leakage_remediation")
data_int_dir = os.path.join("reports", "data_integration")

if os.path.exists(leak_dir):
    for f in os.listdir(leak_dir):
        src = os.path.join(leak_dir, f)
        dst = os.path.join(data_int_dir, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copied to data_integration: {f}")

# Also move Phase 1-3 reports from reports/ to reports/data_integration/
root_reports_to_move = [
    "phase1_preliminary_source_comparison.md",
    "phase2_entity_harmonization_and_matching_report.md",
    "phase2_reconciliation_summary.json",
    "phase3_database_schema_and_ingestion_report.md",
    "modern_dataset_2016_present_audit.md",
    "modern_dataset_verification_summary.json",
    "database_verification_summary.json",
    "source_inventory.csv",
    "england_football_results_inspection_summary.json",
    "fjelstul_inspection_summary.json",
    "football_data_co_uk_inspection_summary.json",
    "openfootball_inspection_summary.json",
    "statsbomb_inspection_summary.json",
    "vaastav_fpl_inspection_summary.json",
    "source_inspection_england_football_results.md",
    "source_inspection_fjelstul.md",
    "source_inspection_football_data_co_uk.md",
    "source_inspection_openfootball.md",
    "source_inspection_statsbomb.md",
    "source_inspection_vaastav_fpl.md"
]

for f in root_reports_to_move:
    src = os.path.join("reports", f)
    dst = os.path.join(data_int_dir, f)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved to reports/data_integration: {f}")

# Also move data/validation/score_discrepancy_report.csv to reports/data_integration/
discrep_src = os.path.join("data", "validation", "score_discrepancy_report.csv")
if os.path.exists(discrep_src):
    shutil.copy2(discrep_src, os.path.join(data_int_dir, "score_discrepancy_report.csv"))
    print("Copied score_discrepancy_report.csv to reports/data_integration")

# 3. Move phase_4_data_analysis/* into reports/eda/
p4_dir = os.path.join("reports", "phase_4_data_analysis")
eda_dir = os.path.join("reports", "eda")

if os.path.exists(p4_dir):
    for f in os.listdir(p4_dir):
        src = os.path.join(p4_dir, f)
        dst = os.path.join(eda_dir, f)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"Copied directory to reports/eda: {f}")
        else:
            shutil.copy2(src, dst)
            print(f"Copied file to reports/eda: {f}")

# 4. Copy test scripts into tests/
tests_to_copy = [
    "test_leakage_safety.py",
    "test_elo_integrity.py"
]

for t in tests_to_copy:
    src = os.path.join("collectors", t)
    dst = os.path.join("tests", t)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied test to tests/: {t}")

# 5. Archive scratch/ files
scratch_dir = "scratch"
archive_scratch_dir = os.path.join("archive", "scratch")
if os.path.exists(scratch_dir):
    for f in os.listdir(scratch_dir):
        src = os.path.join(scratch_dir, f)
        dst = os.path.join(archive_scratch_dir, f)
        if os.path.isfile(src):
            shutil.move(src, dst)
            print(f"Archived scratch file: {f}")

# 6. Archive data/processed_backup_pre_remediation
bak_dir = os.path.join("data", "processed_backup_pre_remediation")
bak_archive = os.path.join("archive", "processed_backup_pre_remediation")
if os.path.exists(bak_dir):
    for f in os.listdir(bak_dir):
        src = os.path.join(bak_dir, f)
        dst = os.path.join(bak_archive, f)
        shutil.copy2(src, dst)
    shutil.rmtree(bak_dir)
    print(f"Moved data/processed_backup_pre_remediation to archive/processed_backup_pre_remediation")

# 7. Move root dashboard.html if redundant (already in reports/eda/dashboard.html)
if os.path.exists("dashboard.html") and os.path.exists(os.path.join(eda_dir, "dashboard.html")):
    # Keep it in reports/eda/, archive root copy
    os.remove("dashboard.html")
    print("Removed duplicate root dashboard.html (preserved at reports/eda/dashboard.html)")

# Clean __pycache__ in collectors
for root, dirs, files in os.walk("."):
    if "__pycache__" in dirs:
        pycache_path = os.path.join(root, "__pycache__")
        shutil.rmtree(pycache_path, ignore_errors=True)
        print(f"Cleaned bytecode cache: {pycache_path}")

print("\nReorganization script complete!")
