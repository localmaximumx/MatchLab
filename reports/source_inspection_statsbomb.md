# Source Inspection Report: StatsBomb Open Data

**Inspection Date:** 2026-11-05  
**Inspector:** Automated Inspection Pipeline (`collectors/inspect_statsbomb.py`)  
**Status:** Completed & Validated  

---

## 1. Executive Summary & Reality Check

**StatsBomb Open Data** (now maintained under Hudl) is the undisputed industry gold standard for granular, event-level football data. It captures every touch, pass, carry, tackle, pressure, and shot with high-precision pitch coordinates, defender freeze-frames, starting lineups, and proprietary Expected Goals (xG).

### Crucial Findings for Our Project:
1. **Severe Coverage Limitation:** 
   - **Premier League:** Only **2 seasons** are available in the open repository:
     - `2003/2004` (Arsenal "Invincibles" campaign: 38 matches).
     - `2015/2016` (Leicester City title-winning season: 380 matches).
     - **Total PL Matches:** **418 matches**.
   - **EFL Championship:** **0 matches.** There is no open Championship data provided by StatsBomb.
2. **Unmatched Event Granularity:** For the covered matches, it provides ~3,700 events per match (passes, ball receipts, pressures, recoveries, duels, fouls, cards, and shots).
3. **True Spatial Coordinates & Shot Freeze Frames:** Every event has $(x, y)$ coordinates on a standardized $120 \times 80$ meter coordinate system. Shots include full 3D end-locations $(x, y, z)$ and the exact coordinates and roles of all visible teammates and defenders at the millisecond of the shot (`shot.freeze_frame`).
4. **License & Terms of Use:** Governed by the **StatsBomb Open Data User Agreement**. Free for public research and personal analytics; requires explicit attribution and StatsBomb logo on published outputs. Not licensed for commercial resale or automated commercial betting feeds.

---

## 2. Basic Information

| Attribute | Details |
|---|---|
| **Dataset Name** | StatsBomb Open Data |
| **Repository URL** | https://github.com/statsbomb/open-data (redirects to `https://github.com/hudl/open-data`) |
| **Organization** | StatsBomb / Hudl |
| **Download Date** | 2026-11-05 |
| **Local Storage Path** | `data/raw/statsbomb/` (catalog, match index, lineups, events) |
| **Full Remote Size** | ~7.64 GB across all worldwide leagues |
| **File Formats** | JSON (`competitions.json`, `matches/{comp}/{season}.json`, `events/{id}.json`, `lineups/{id}.json`) |
| **License** | **StatsBomb Open Data User Agreement** |
| **Permitted Uses** | Free for non-commercial academic research, public analytics, and open projects. Requires explicit attribution ("Data provided by StatsBomb") and inclusion of StatsBomb logo on visual artifacts. Cannot be redistributed commercially. |

---

## 3. English Competition & Season Coverage

Across the 80 global competition-season entries in `competitions.json`, English football coverage is strictly selective:

| Competition Name | Gender | Competition ID | Season ID | Season Name | Matches Available |
|---|---|---|---|---|---|
| **Premier League** | Male | **2** | **44** | **2003/2004** | **38 matches** (Arsenal Invincibles) |
| **Premier League** | Male | **2** | **27** | **2015/2016** | **380 matches** (Full 20-team season) |
| **EFL Championship** | Male | — | — | — | **0 matches (None)** |
| **FA Women's Super League** | Female | 37 | 281 | 2023/2024 | 132 matches |
| **FA Women's Super League** | Female | 37 | 90 | 2020/2021 | 131 matches |
| **FA Women's Super League** | Female | 37 | 42 | 2019/2020 | 87 matches |
| **FA Women's Super League** | Female | 37 | 4 | 2018/2019 | 108 matches |

---

## 4. Schema and Data Granularity (Sample Match: Chelsea 2–0 Arsenal)

Inspected match: `match_id = 3754217` (Premier League 2015/16, Stamford Bridge).

### 4.1 Lineup Data (`lineups/3754217.json`)
- Provides exact starting XI and bench for both squads (18 players per squad).
- Player identifiers: `player_id`, `player_name`, `player_nickname`, `jersey_number`, `country`.
- Tactical positioning: starting position name (e.g., `Left Wing`, `Centre Back`), position ID, minute entered (`from: "00:00"`), substitution minute (`to: "74:32"`), and tactical substitution reason.

### 4.2 In-Match Events (`events/3754217.json`)
The sample match contains **3,732 discrete events**:

| Event Type | Count in Match | Key Event Attributes |
|---|---|---|
| **Pass** | 1,046 | Recipient, length, angle, pass height, pass type, outcome |
| **Ball Receipt*** | 963 | Target location, whether under pressure |
| **Carry** | 814 | Start coordinate $[x_1, y_1]$, end coordinate $[x_2, y_2]$ |
| **Pressure** | 320 | Opponent pressed, defensive action zone |
| **Ball Recovery** | 106 | Loose ball regain location |
| **Duel** | 78 | Aerial vs ground, duel type, outcome |
| **Dribble** | 52 | Successful vs unsuccessful takeover |
| **Clearance** | 42 | Aerial/foot clearance under pressure |
| **Block** | 41 | Blocked shot or pass |
| **Shot** | 33 | Coordinates, xG, body part, technique, freeze frame |
| **Fouls Committed / Won** | 61 | Card issued, foul type, tactical foul |
| **Interceptions** | 20 | Pass cut-off |
| **Substitutions** | 6 | Player off, player on, tactical reasoning |

### 4.3 Shot Schema and Expected Goals (xG)
StatsBomb records the most detailed shot data available anywhere in football analytics:

```json
{
  "minute": 1,
  "second": 47,
  "player": "Aaron Ramsey",
  "team": "Arsenal",
  "location": [94.5, 42.9],
  "shot": {
    "statsbomb_xg": 0.03883,
    "end_location": [116.3, 40.2, 0.4],
    "outcome": {"name": "Blocked"},
    "technique": {"name": "Normal"},
    "body_part": {"name": "Left Foot"},
    "type": {"name": "Open Play"},
    "freeze_frame": [
      {"location": [118.2, 38.6], "player": {"name": "Asmir Begović"}, "teammate": false, "position": {"name": "Goalkeeper"}},
      {"location": [97.5, 42.1], "player": {"name": "Kurt Zouma"}, "teammate": false, "position": {"name": "Right Centre Back"}}
    ]
  }
}
```

- **Coordinates:** Pitch origin is top-left $(0, 0)$; opposing goal is at $(120, 40)$. Ramsey's shot was taken from $x=94.5, y=42.9$ (approx 25.5 meters out).
- **`statsbomb_xg`:** Pre-computed statistical probability of scoring from this exact game situation ($P(\text{Goal}) \approx 3.88\%$).
- **`freeze_frame`:** Lists all 16 visible players with their exact coordinates and roles at the instant the boot hit the ball.

---

## 5. Potential Machine Learning Usefulness & Strategic Role

### What StatsBomb Is Best Suited For:
1. **Teaching and Benchmarking xG Models (Phase 6):**
   - We can train our own independent logistic regression and XGBoost xG models using the $(x, y)$ coordinates, distance to goal, angle to goal, shot technique, and body part, and benchmark our predictions directly against StatsBomb's proprietary `statsbomb_xg`.
2. **Feature Engineering Reference:**
   - Understanding what metrics correlate with winning (pressure frequency, high-turnover recoveries, deep completions).
3. **Shot Freeze-Frame Spatial Analysis:**
   - Visualizing defensive coverage density and goalkeeper positioning.

### What StatsBomb Cannot Do for Us:
1. **Cannot Be Our Match Prediction Backbone:** Because it only covers 418 PL matches and 0 Championship matches, we **cannot** use StatsBomb to train a multi-season match outcome prediction model across 1992–2024.
2. **No Bookmaker Odds:** Contains zero betting quotes or odds data.
3. **No Championship Coverage:** Leaves the second tier completely unaddressed.

---

## 6. Synthesis Across the 3 Inspected Candidates

| Source | Seasons Covered | Total Matches | Granularity | Role in Our Architecture |
|---|---|---|---|---|
| **Fjelstul** | 1888–2023 (125 yrs) | 208,028 (12,406 PL; 55,804 Tier 2) | Match results & standings | **Master Historical Catalog & ID backbone** |
| **OpenFootball** | 1992–2024 (35 yrs) | 13,011 PL; 14,463 Tier 2 | Match dates, times, HT scores, playoffs | **Chronological Sequencing & Time Anchor** |
| **StatsBomb** | 2003/04, 2015/16 (2 yrs) | 418 PL; 0 Tier 2 | Event-level ($x,y$, xG, freeze frames) | **Micro-Level Validation & xG Modeling Lab** |

The next candidate in Phase 1 is **Vaastav Fantasy Premier League Historical Dataset** (`https://github.com/vaastav/Fantasy-Premier-League`), which provides historical player-level minutes, FPL points, goals, assists, and gameweek form across 2016–2025.
