"""
Phase 2 - Step 2.2: Master Canonical Team Dictionary Builder
Builds the definitive entity harmonization mapping across all candidate sources:
1. Sean Elvidge England League Results & Team Name Periods
2. Fjelstul English Football Database
3. Football-Data.co.uk Match Archives
4. OpenFootball England
5. Vaastav Fantasy Premier League
6. StatsBomb Open Data

Generates:
- data/processed/canonical_teams.csv
- data/processed/team_aliases.csv
- data/processed/team_dictionary.json
"""

import sys
import os
import json
import re
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'\b(fc|afc|cf)\b', '', text)
    text = re.sub(r'[\'&/\.]', '', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def clean_team_string(s):
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r'\b(fc|afc|cf)\b', '', s)
    s = re.sub(r'[\'\.\-\&]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def build_team_dictionary():
    print("=" * 80)
    print("PHASE 2 - BUILDING MASTER CANONICAL TEAM DICTIONARY")
    print("=" * 80)

    # 1. Load Fjelstul teams table
    fj_teams_path = os.path.join(DATA_RAW, "fjelstul", "data-csv", "teams.csv")
    df_fj_teams = pd.read_csv(fj_teams_path) if os.path.exists(fj_teams_path) else pd.DataFrame()
    print(f"Loaded {len(df_fj_teams)} teams from Fjelstul")

    # 2. Load Sean Elvidge Team Name Periods
    elv_periods_path = os.path.join(DATA_RAW, "england_football_results", "EnglishTeamNamePeriods.csv")
    df_elv_periods = pd.read_csv(elv_periods_path) if os.path.exists(elv_periods_path) else pd.DataFrame()
    print(f"Loaded {len(df_elv_periods)} name transitions from Sean Elvidge")

    # 3. Load raw extracted teams from Step 2.1
    with open(os.path.join(DATA_PROCESSED, "raw_teams_extracted.json"), "r", encoding="utf-8") as f:
        extracted = json.load(f)

    # Core normalization synonym dictionary
    SYNONYMS = {
        'man utd': 'manchester-united',
        'man united': 'manchester-united',
        'man city': 'manchester-city',
        'spurs': 'tottenham-hotspur',
        'tottenham': 'tottenham-hotspur',
        'wolves': 'wolverhampton-wanderers',
        'wolverhampton': 'wolverhampton-wanderers',
        'nottm forest': 'nottingham-forest',
        'notts forest': 'nottingham-forest',
        'sheff utd': 'sheffield-united',
        'sheff wed': 'sheffield-wednesday',
        'sheffield weds': 'sheffield-wednesday',
        'west brom': 'west-bromwich-albion',
        'wba': 'west-bromwich-albion',
        'west ham': 'west-ham-united',
        'newcastle': 'newcastle-united',
        'leeds': 'leeds-united',
        'leicester': 'leicester-city',
        'norwich': 'norwich-city',
        'cardiff': 'cardiff-city',
        'swansea': 'swansea-city',
        'stoke': 'stoke-city',
        'hull': 'hull-city',
        'birmingham': 'birmingham-city',
        'blackburn': 'blackburn-rovers',
        'bolton': 'bolton-wanderers',
        'bradford': 'bradford-city',
        'charlton': 'charlton-athletic',
        'coventry': 'coventry-city',
        'derby': 'derby-county',
        'huddersfield': 'huddersfield-town',
        'ipswich': 'ipswich-town',
        'luton': 'luton-town',
        'oldham': 'oldham-athletic',
        'qpr': 'queens-park-rangers',
        'queens park rangers': 'queens-park-rangers',
        'swindon': 'swindon-town',
        'wigan': 'wigan-athletic',
        'brighton': 'brighton-and-hove-albion',
        'brighton & hove albion': 'brighton-and-hove-albion',
        'brighton and hove albion': 'brighton-and-hove-albion',
        'brighton-hove-albion': 'brighton-and-hove-albion',
        'bournemouth': 'afc-bournemouth',
        'afc bournemouth': 'afc-bournemouth',
        'rotherham': 'rotherham-united',
        'peterborough': 'peterborough-united',
        'peterboro': 'peterborough-united',
        'plymouth': 'plymouth-argyle',
        'preston': 'preston-north-end',
        'preston north end': 'preston-north-end',
        'mk dons': 'milton-keynes-dons',
        'milton keynes dons': 'milton-keynes-dons',
        'oxford': 'oxford-united',
        'crewe': 'crewe-alexandra',
        'scunthorpe': 'scunthorpe-united',
        'stockport': 'stockport-county',
        'tranmere': 'tranmere-rovers',
        'yeovil': 'yeovil-town',
        'burton': 'burton-albion',
        'bristol c': 'bristol-city',
        'bristol city': 'bristol-city',
        'bristol r': 'bristol-rovers',
        'bristol rovers': 'bristol-rovers',
        'colchester': 'colchester-united',
        'doncaster': 'doncaster-rovers',
        'grimsby': 'grimsby-town',
        'lincoln': 'lincoln-city',
        'southend': 'southend-united',
        'wycombe': 'wycombe-wanderers',
        'dag and red': 'dagenham-and-redbridge',
        'dagenham & redbridge': 'dagenham-and-redbridge',
        'rushden & d': 'rushden-and-diamonds',
        'rushden and diamonds': 'rushden-and-diamonds',
        'macclesfield': 'macclesfield-town',
        'chesterfield': 'chesterfield',
        'hartlepool': 'hartlepool-united',
        'carlisle': 'carlisle-united',
        'cheltenham': 'cheltenham-town',
        'exeter': 'exeter-city',
        'morecambe': 'morecambe',
        'shrewsbury': 'shrewsbury-town',
        'stevenage': 'stevenage',
        'crawley': 'crawley-town',
        'fleetwood': 'fleetwood-town',
        'accrington': 'accrington-stanley',
        'accrington stanley': 'accrington-stanley',
        'forest green': 'forest-green-rovers',
        'salford': 'salford-city',
        'harrogate': 'harrogate-town',
        'barrow': 'barrow',
        'sutton': 'sutton-united',
        'bromley': 'bromley',
    }

    canonical_teams = {}
    aliases = []

    # Helper to resolve or create a canonical team_id
    def get_or_create_team_id(raw_str, source_type=None, is_pl=False, is_champ=False):
        if not raw_str or not isinstance(raw_str, str):
            return None
        raw_str = raw_str.strip()
        cleaned = clean_team_string(raw_str)
        slug = slugify(raw_str)

        # Check synonyms
        if cleaned in SYNONYMS:
            slug = SYNONYMS[cleaned]
        elif slug in SYNONYMS:
            slug = SYNONYMS[slug]
        # Common suffixes
        elif slug.endswith('-utd'):
            slug = slug[:-4] + '-united'
        elif slug.endswith('-weds') or slug.endswith('-wed'):
            slug = slug.split('-wed')[0] + '-wednesday'

        if slug not in canonical_teams:
            canonical_teams[slug] = {
                "team_id": slug,
                "canonical_name": raw_str,
                "common_name": raw_str,
                "fjelstul_team_id": None,
                "country": "England",
                "is_premier_league_historical": is_pl,
                "is_championship_historical": is_champ
            }
        else:
            if is_pl:
                canonical_teams[slug]["is_premier_league_historical"] = True
            if is_champ:
                canonical_teams[slug]["is_championship_historical"] = True
            # Prefer longer/more descriptive formal name
            current_name = canonical_teams[slug]["canonical_name"]
            if len(raw_str) > len(current_name) and not raw_str.endswith('FC'):
                canonical_teams[slug]["canonical_name"] = raw_str

        return slug

    # Helper to register an alias
    def register_alias(raw_str, team_id, source):
        if not raw_str or not isinstance(raw_str, str) or not team_id:
            return
        raw_str = raw_str.strip()
        cleaned = clean_team_string(raw_str)
        aliases.append({
            "alias_raw": raw_str,
            "normalized_alias": cleaned,
            "team_id": team_id,
            "source": source
        })

    # 4. Ingest Sean Elvidge clubs as baseline canonical names
    for t in extracted['elvidge']['all_extracted']:
        is_pl = t in extracted['elvidge']['pl_teams_1992_present']
        is_champ = t in extracted['elvidge']['champ_teams_1992_present']
        tid = get_or_create_team_id(t, "elvidge", is_pl, is_champ)
        register_alias(t, tid, "elvidge")

    # Ingest historical period names from Sean Elvidge
    if not df_elv_periods.empty:
        for _, row in df_elv_periods.iterrows():
            main_team = row['Team'].strip()
            period_name = row['Name'].strip()
            main_slug = get_or_create_team_id(main_team, "elvidge_period")
            register_alias(period_name, main_slug, "elvidge_period")

    # 5. Ingest Fjelstul teams
    if not df_fj_teams.empty:
        for _, row in df_fj_teams.iterrows():
            t_name = row['team_name'].strip()
            fj_id = str(row['team_id']).strip()
            is_pl = t_name in extracted['fjelstul']['pl_teams_1992_present']
            is_champ = t_name in extracted['fjelstul']['champ_teams_1992_present']
            tid = get_or_create_team_id(t_name, "fjelstul", is_pl, is_champ)
            canonical_teams[tid]['fjelstul_team_id'] = fj_id
            register_alias(t_name, tid, "fjelstul")

    # 6. Ingest Football-Data.co.uk teams
    for t in extracted['football_data']['all_extracted']:
        is_pl = t in extracted['football_data']['pl_teams']
        is_champ = t in extracted['football_data']['champ_teams']
        tid = get_or_create_team_id(t, "football_data", is_pl, is_champ)
        register_alias(t, tid, "football_data")

    # 7. Ingest OpenFootball teams
    for t in extracted['openfootball']['all_extracted']:
        is_pl = t in extracted['openfootball']['pl_teams']
        is_champ = t in extracted['openfootball']['champ_teams']
        tid = get_or_create_team_id(t, "openfootball", is_pl, is_champ)
        register_alias(t, tid, "openfootball")

    # 8. Ingest Vaastav FPL teams
    for t in extracted['vaastav_fpl']['all_extracted']:
        is_pl = t in extracted['vaastav_fpl']['pl_teams']
        tid = get_or_create_team_id(t, "vaastav_fpl", is_pl, False)
        register_alias(t, tid, "vaastav_fpl")

    # 9. Ingest StatsBomb teams
    for t in extracted['statsbomb']['all_extracted']:
        is_pl = t in extracted['statsbomb']['pl_teams']
        tid = get_or_create_team_id(t, "statsbomb", is_pl, False)
        register_alias(t, tid, "statsbomb")

    # Build DataFrames
    df_canonical = pd.DataFrame(list(canonical_teams.values())).sort_values('team_id')
    df_aliases = pd.DataFrame(aliases).drop_duplicates(subset=['alias_raw', 'team_id']).sort_values(['team_id', 'alias_raw'])

    # Build fast lookup dictionary: normalized_string -> {team_id, canonical_name}
    lookup_dict = {}
    for _, row in df_aliases.iterrows():
        norm = row['normalized_alias']
        tid = row['team_id']
        cname = canonical_teams[tid]['canonical_name']
        lookup_dict[norm] = {
            "team_id": tid,
            "canonical_name": cname
        }
        # Also register exact raw lowercase
        lookup_dict[row['alias_raw'].lower()] = {
            "team_id": tid,
            "canonical_name": cname
        }

    # Enforce priority overrides from SYNONYMS to prevent historical period collisions
    for term, target_slug in SYNONYMS.items():
        if target_slug in canonical_teams:
            lookup_dict[term] = {
                "team_id": target_slug,
                "canonical_name": canonical_teams[target_slug]['canonical_name']
            }

    # Save outputs
    canonical_csv_path = os.path.join(DATA_PROCESSED, "canonical_teams.csv")
    aliases_csv_path = os.path.join(DATA_PROCESSED, "team_aliases.csv")
    dict_json_path = os.path.join(DATA_PROCESSED, "team_dictionary.json")

    df_canonical.to_csv(canonical_csv_path, index=False)
    df_aliases.to_csv(aliases_csv_path, index=False)
    with open(dict_json_path, "w", encoding="utf-8") as f:
        json.dump(lookup_dict, f, indent=2)

    print(f"\n✓ Generated {len(df_canonical)} canonical team entities -> {canonical_csv_path}")
    print(f"✓ Generated {len(df_aliases)} team alias mappings -> {aliases_csv_path}")
    print(f"✓ Generated fast lookup dictionary ({len(lookup_dict)} entries) -> {dict_json_path}")

    # Verification: Check coverage of Premier League 51 clubs
    pl_51_canonical = df_canonical[df_canonical['is_premier_league_historical'] == True]
    print(f"\nVerified Canonical Premier League Clubs: {len(pl_51_canonical)} clubs")
    print(list(pl_51_canonical['canonical_name'].head(15)))

    return df_canonical, df_aliases, lookup_dict

if __name__ == "__main__":
    build_team_dictionary()
