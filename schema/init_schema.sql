-- MatchLab Relational Database Schema
-- Compatible with SQLite 3.24+ and PostgreSQL 12+
-- Designed for Football Machine Learning & Betting Market Intelligence

-- 1. Competitions Table
CREATE TABLE IF NOT EXISTS competitions (
    competition_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    code VARCHAR(16) NOT NULL UNIQUE,
    country VARCHAR(32) NOT NULL DEFAULT 'England',
    tier INTEGER NOT NULL
);

-- 2. Seasons Table
CREATE TABLE IF NOT EXISTS seasons (
    season_id VARCHAR(64) PRIMARY KEY,
    competition_id VARCHAR(32) NOT NULL,
    season_name VARCHAR(16) NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    FOREIGN KEY (competition_id) REFERENCES competitions(competition_id)
);

-- 3. Canonical Teams Table
CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(64) PRIMARY KEY,
    canonical_name VARCHAR(128) NOT NULL,
    common_name VARCHAR(64) NOT NULL,
    fjelstul_team_id VARCHAR(32),
    country VARCHAR(32) NOT NULL DEFAULT 'England',
    is_premier_league_historical BOOLEAN NOT NULL DEFAULT 0,
    is_championship_historical BOOLEAN NOT NULL DEFAULT 0
);

-- 4. Team Aliases Table (Entity Resolution Map)
CREATE TABLE IF NOT EXISTS team_aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id VARCHAR(64) NOT NULL,
    alias_raw VARCHAR(128) NOT NULL,
    normalized_alias VARCHAR(128) NOT NULL,
    source VARCHAR(64) NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE(team_id, alias_raw)
);

-- 5. Point Deductions Table (Disciplinary Reality)
CREATE TABLE IF NOT EXISTS point_deductions (
    deduction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_name VARCHAR(16) NOT NULL,
    deduction_date DATE NOT NULL,
    team_id VARCHAR(64) NOT NULL,
    points_deducted INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 6. Core Matches Calendar & Ground Truth Outcomes
CREATE TABLE IF NOT EXISTS matches (
    match_id VARCHAR(128) PRIMARY KEY,
    competition_id VARCHAR(32) NOT NULL,
    season_id VARCHAR(64) NOT NULL,
    season_name VARCHAR(16) NOT NULL,
    match_date DATE NOT NULL,
    kickoff_time VARCHAR(8),
    home_team_id VARCHAR(64) NOT NULL,
    away_team_id VARCHAR(64) NOT NULL,
    home_team_name VARCHAR(128) NOT NULL,
    away_team_name VARCHAR(128) NOT NULL,
    full_time_home_goals INTEGER NOT NULL,
    full_time_away_goals INTEGER NOT NULL,
    full_time_result VARCHAR(1) NOT NULL CHECK (full_time_result IN ('H', 'D', 'A')),
    half_time_home_goals INTEGER,
    half_time_away_goals INTEGER,
    half_time_result VARCHAR(1) CHECK (half_time_result IN ('H', 'D', 'A') OR half_time_result IS NULL),
    referee VARCHAR(64),
    data_source VARCHAR(64) NOT NULL DEFAULT 'reconciled_elvidge_football_data',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (competition_id) REFERENCES competitions(competition_id),
    FOREIGN KEY (season_id) REFERENCES seasons(season_id),
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

-- 7. In-Match Tactical Statistics (Strictly Post-Match / Lagged-Only for ML)
CREATE TABLE IF NOT EXISTS match_stats (
    match_id VARCHAR(128) PRIMARY KEY,
    home_shots INTEGER,
    away_shots INTEGER,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_corners INTEGER,
    away_corners INTEGER,
    home_fouls INTEGER,
    away_fouls INTEGER,
    home_yellow_cards INTEGER,
    away_yellow_cards INTEGER,
    home_red_cards INTEGER,
    away_red_cards INTEGER,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
);

-- 8. Continuous Elo Ratings & Probabilities
CREATE TABLE IF NOT EXISTS match_elo_ratings (
    match_id VARCHAR(128) PRIMARY KEY,
    home_elo_before REAL NOT NULL,
    away_elo_before REAL NOT NULL,
    elo_home_win_prob REAL NOT NULL,
    elo_draw_prob REAL NOT NULL,
    elo_away_win_prob REAL NOT NULL,
    home_elo_after REAL NOT NULL,
    away_elo_after REAL NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
);

-- 9. Multi-Bookmaker Betting Market Odds
CREATE TABLE IF NOT EXISTS match_betting_odds (
    match_id VARCHAR(128) PRIMARY KEY,
    -- Retail Opening Lines (Bet365)
    b365_home REAL,
    b365_draw REAL,
    b365_away REAL,
    -- Sharp Opening Lines (Pinnacle)
    pinnacle_home REAL,
    pinnacle_draw REAL,
    pinnacle_away REAL,
    -- Sharp Closing Lines (Pinnacle Closing - Primary CLV Benchmark)
    pinnacle_close_home REAL,
    pinnacle_close_draw REAL,
    pinnacle_close_away REAL,
    -- Retail Closing Lines (Bet365 Closing)
    b365_close_home REAL,
    b365_close_draw REAL,
    b365_close_away REAL,
    -- Market Consensus Lines (Average & Maximum)
    market_avg_home REAL,
    market_avg_draw REAL,
    market_avg_away REAL,
    market_max_home REAL,
    market_max_draw REAL,
    market_max_away REAL,
    -- Over / Under 2.5 Totals
    market_avg_over_2_5 REAL,
    market_avg_under_2_5 REAL,
    -- Asian Handicap Spread Lines
    asian_handicap_line REAL,
    market_avg_handicap_home REAL,
    market_avg_handicap_away REAL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
);

-- Indexes for Fast Time-Series and Analytical Queries
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition_id);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_fixture ON matches(home_team_id, away_team_id, match_date);
CREATE INDEX IF NOT EXISTS idx_aliases_lookup ON team_aliases(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_deductions_team ON point_deductions(team_id);
