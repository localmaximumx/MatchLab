"""
Downloader Script for Football-Data.co.uk Historical Datasets
Downloads Premier League (E0) and Championship (E1) CSVs across all available seasons.
Saves raw, untouched files into data/raw/football_data_co_uk/{season}/
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_DIR = os.path.join(BASE_DIR, "data", "raw", "football_data_co_uk")
os.makedirs(DEST_DIR, exist_ok=True)

# Generate list of seasons from 1993/94 (9394) to 2026/27 (2627)
def generate_seasons():
    seasons = []
    # 1993/94 to 1999/00
    for y in range(93, 100):
        next_y = (y + 1) % 100
        code = f"{y:02d}{next_y:02d}"
        label = f"19{y:02d}-{'2000' if next_y == 0 else f'19{next_y:02d}'}"
        seasons.append((code, label))
    # 2000/01 to 2026/27
    for y in range(0, 27):
        next_y = (y + 1) % 100
        code = f"{y:02d}{next_y:02d}"
        label = f"20{y:02d}-20{next_y:02d}"
        seasons.append((code, label))
    return seasons

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MatchLab-Data-Collector/1.0'
}

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)

def download_football_data():
    print("=" * 80)
    print("STARTING FOOTBALL-DATA.CO.UK HISTORICAL DOWNLOAD")
    print(f"Target Directory: {DEST_DIR}")
    print("=" * 80)

    # 1. Download notes.txt (Codebook / Data Dictionary)
    notes_url = "https://www.football-data.co.uk/notes.txt"
    print(f"\nFetching data dictionary from {notes_url}...")
    status, notes_content = fetch_url(notes_url)
    if status == 200 and notes_content:
        notes_dest = os.path.join(DEST_DIR, "notes.txt")
        with open(notes_dest, "wb") as f:
            f.write(notes_content)
        print(f"✓ Saved notes.txt ({len(notes_content):,} bytes)")
    else:
        print(f"✗ Failed to download notes.txt (Status: {status})")

    # 2. Iterate through seasons for E0 (Premier League) and E1 (Championship)
    seasons = generate_seasons()
    print(f"\nChecking {len(seasons)} candidate seasons (1993/94 through 2026/27)...")

    leagues = [
        ("E0", "Premier League"),
        ("E1", "Championship")
    ]

    download_log = []
    total_downloaded = 0
    total_bytes = 0

    for code, label in seasons:
        season_dir = os.path.join(DEST_DIR, label)
        os.makedirs(season_dir, exist_ok=True)

        for div_code, div_name in leagues:
            file_name = f"{div_code}.csv"
            url = f"https://www.football-data.co.uk/mmz4281/{code}/{file_name}"
            dest_file = os.path.join(season_dir, file_name)

            status, content = fetch_url(url)
            if status == 200 and content and len(content) > 100:
                with open(dest_file, "wb") as f:
                    f.write(content)
                size = len(content)
                total_bytes += size
                total_downloaded += 1
                download_log.append({
                    "season_code": code,
                    "season_label": label,
                    "division": div_code,
                    "competition_name": div_name,
                    "url": url,
                    "status": "success",
                    "bytes": size,
                    "file_path": os.path.relpath(dest_file, BASE_DIR)
                })
                print(f"  ✓ [{label}] {div_code} ({div_name:<14}): {size:>8,} bytes downloaded")
            else:
                download_log.append({
                    "season_code": code,
                    "season_label": label,
                    "division": div_code,
                    "competition_name": div_name,
                    "url": url,
                    "status": f"HTTP {status}" if status else "error",
                    "bytes": 0,
                    "file_path": None
                })
                if status == 404:
                    # Season not available yet or not released
                    pass
                else:
                    print(f"  - [{label}] {div_code} ({div_name:<14}): Not available (Status {status})")

            # Polite pause to avoid hammering the free web server
            time.sleep(0.3)

    log_path = os.path.join(DEST_DIR, "download_manifest.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_files_downloaded": total_downloaded,
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "manifest": download_log
        }, f, indent=2)

    print("\n" + "=" * 80)
    print(f"DOWNLOAD COMPLETE: {total_downloaded} files downloaded ({round(total_bytes / (1024 * 1024), 2)} MB)")
    print(f"Manifest written to: {log_path}")
    print("=" * 80)

if __name__ == "__main__":
    download_football_data()
