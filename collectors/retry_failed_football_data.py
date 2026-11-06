"""
Targeted Retry Downloader for Missing Football-Data.co.uk Files
Uses retries, exponential backoff, and increased timeout (25s) to cleanly fetch any missing season CSVs.
"""

import sys
import os
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "football_data_co_uk")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MatchLab/1.0 Football-Data-Harvester'
}

def season_to_code(season_str):
    # e.g. "1993-1994" -> "9394", "2000-2001" -> "0001", "2023-2024" -> "2324"
    parts = season_str.split('-')
    y1 = int(parts[0]) % 100
    y2 = int(parts[1]) % 100
    return f"{y1:02d}{y2:02d}"

def download_with_retry(url, dest_path, max_retries=4, timeout=25):
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 100:
                        with open(dest_path, "wb") as f:
                            f.write(data)
                        return True, len(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, f"HTTP 404 Not Found"
            print(f"    Attempt {attempt} HTTPError: {e}")
        except Exception as e:
            print(f"    Attempt {attempt} Error: {e}")
        time.sleep(2 * attempt)
    return False, "Exceeded retries"

def main():
    print("=" * 80)
    print("RETRYING MISSING FOOTBALL-DATA.CO.UK CSVS")
    print("=" * 80)

    seasons = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    missing = []
    for s in sorted(seasons):
        for div in ['E0', 'E1']:
            fpath = os.path.join(DATA_DIR, s, f"{div}.csv")
            if not os.path.exists(fpath):
                missing.append((s, div, fpath))

    print(f"Found {len(missing)} missing files to retry.")

    recovered = 0
    not_available = 0

    for s, div, fpath in missing:
        code = season_to_code(s)
        url = f"https://www.football-data.co.uk/mmz4281/{code}/{div}.csv"
        print(f"Fetching {s} {div} from {url}...")
        success, info = download_with_retry(url, fpath)
        if success:
            print(f"  ✓ Recovered {s}/{div}.csv ({info:,} bytes)")
            recovered += 1
        else:
            print(f"  - Could not download {s}/{div}.csv: {info}")
            not_available += 1
        time.sleep(1.0)

    print("\n" + "=" * 80)
    print(f"RETRY COMPLETE: Recovered {recovered} files | Not available: {not_available}")
    print("=" * 80)

if __name__ == "__main__":
    main()
