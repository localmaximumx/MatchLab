"""
MatchLab Test Suite Runner
Executes:
1. Leakage Safety Test Suite (16 adversarial tests)
2. Elo Rating Integrity Tests
"""

import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

print("=" * 80)
print("MATCHLAB: EXECUTING COMPLETE TEST SUITE")
print("=" * 80)

# Run 1: Leakage safety test suite
print("\n[RUNNING SUITE 1] Leakage Safety Tests (16 Tests)...")
ret1 = subprocess.run([sys.executable, os.path.join("tests", "test_leakage_safety.py")])

# Run 2: Elo integrity tests
print("\n[RUNNING SUITE 2] Elo Integrity Tests...")
ret2 = subprocess.run([sys.executable, os.path.join("tests", "test_elo_integrity.py")])

print("\n" + "=" * 80)
if ret1.returncode == 0 and ret2.returncode == 0:
    print("ALL MATCHLAB TEST SUITES PASSED SUCCESSFULLY (0 FAILURES)")
else:
    print(f"TEST FAILURES DETECTED: Suite 1 exit code {ret1.returncode}, Suite 2 exit code {ret2.returncode}")
print("=" * 80)

sys.exit(max(ret1.returncode, ret2.returncode))
