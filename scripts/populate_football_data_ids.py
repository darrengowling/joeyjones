#!/usr/bin/env python3
"""
Populate Football-Data.org IDs for all teams in the database.

This script:
1. Fetches team data from Football-Data.org API for various competitions
2. Matches teams by name (fuzzy matching)
3. Updates the database with correct footballDataId

Usage: python populate_football_data_ids.py [--dry-run]
"""

import asyncio
import aiohttp
import os
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from difflib import SequenceMatcher

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb+srv://darts_admin:Anniepip1315@cluster0.edjfwnl.mongodb.net/?appName=Cluster0')
DB_NAME = os.environ.get('DB_NAME', 'sport_x_poc')
FOOTBALL_DATA_TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN', 'eddf5fb8a13a4e2c9c5808265cd28579')

DRY_RUN = "--dry-run" in sys.argv

# Football-Data.org competition codes
COMPETITIONS = {
    # Club competitions
    'PL': 'Premier League',
    'PD': 'La Liga',
    'BL1': 'Bundesliga',
    'SA': 'Serie A',
    'FL1': 'Ligue 1',
    'DED': 'Eredivisie',
    'PPL': 'Primeira Liga',
    'CL': 'Champions League',
    'ELC': 'Championship',
    # National team competition
    'WC': 'World Cup',
    'EC': 'European Championship',
}

# Name normalization mappings for better matching
NAME_MAPPINGS = {
    # Our DB name -> Football-Data.org name variations
    'FC Bayern München': ['FC Bayern München', 'Bayern Munich', 'Bayern München'],
    'FC Internazionale Milano': ['FC Internazionale Milano', 'Inter Milan', 'Inter'],
    'Tottenham Hotspur FC': ['Tottenham Hotspur FC', 'Tottenham Hotspur', 'Spurs'],
    'Wolverhampton Wanderers FC': ['Wolverhampton Wanderers FC', 'Wolves'],
    'Brighton & Hove Albion FC': ['Brighton & Hove Albion FC', 'Brighton'],
    'AFC Bournemouth': ['AFC Bournemouth', 'Bournemouth'],
    'Club Atlético de Madrid': ['Club Atlético de Madrid', 'Atlético Madrid', 'Atletico Madrid'],
    'Sport Lisboa e Benfica': ['Sport Lisboa e Benfica', 'SL Benfica', 'Benfica'],
    'Sporting Clube de Portugal': ['Sporting Clube de Portugal', 'Sporting CP', 'Sporting Lisbon'],
    'Paris Saint-Germain FC': ['Paris Saint-Germain FC', 'Paris Saint-Germain', 'PSG'],
    'Olympique de Marseille': ['Olympique de Marseille', 'Olympique Marseille', 'Marseille'],
    'Stade Brestois 29': ['Stade Brestois 29', 'Brest'],
    'FK Bodø/Glimt': ['FK Bodø/Glimt', 'Bodø/Glimt', 'Bodo/Glimt'],
    'PAE Olympiakos SFP': ['Olympiacos FC', 'Olympiakos', 'Olympiacos'],
    'Qarabağ Ağdam FK': ['Qarabağ FK', 'Qarabag FK', 'Qarabag'],
    'SK Slavia Praha': ['SK Slavia Praha', 'Slavia Prague', 'Slavia Praha'],
    'Royale Union Saint-Gilloise': ['Royale Union Saint-Gilloise', 'Union SG', 'Union Saint-Gilloise'],
    'FC København': ['FC København', 'FC Copenhagen', 'Copenhagen'],
    'GNK Dinamo Zagreb': ['GNK Dinamo Zagreb', 'Dinamo Zagreb'],
    'BSC Young Boys': ['BSC Young Boys', 'Young Boys'],
    'FK Crvena Zvezda': ['FK Crvena Zvezda', 'Red Star Belgrade', 'Crvena Zvezda'],
    'FC Shakhtar Donetsk': ['FC Shakhtar Donetsk', 'Shakhtar Donetsk', 'Shakhtar'],
    'AC Sparta Praha': ['AC Sparta Praha', 'Sparta Prague', 'Sparta Praha'],
    'SK Sturm Graz': ['SK Sturm Graz', 'Sturm Graz'],
    # National teams
    'South Korea': ['Korea Republic', 'South Korea', 'Korea'],
    'United States': ['United States', 'USA'],
    'Côte d\'Ivoire': ['Côte d\'Ivoire', 'Ivory Coast', 'Cote d\'Ivoire'],
    'Netherlands': ['Netherlands', 'Holland'],
}


def normalize_name(name):
    """Normalize team name for comparison"""
    if not name:
        return ""
    # Remove common suffixes
    normalized = name.lower().strip()
    for suffix in [' fc', ' cf', ' sc', ' sk', ' fk', ' ac', ' bc', ' afc']:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
    return normalized


def similarity_score(name1, name2):
    """Calculate similarity between two names"""
    return SequenceMatcher(None, normalize_name(name1), normalize_name(name2)).ratio()


def find_best_match(db_name, api_teams):
    """Find the best matching team from API results"""
    best_match = None
    best_score = 0
    
    # Check direct name mappings first
    if db_name in NAME_MAPPINGS:
        for variant in NAME_MAPPINGS[db_name]:
            for team in api_teams:
                if normalize_name(team['name']) == normalize_name(variant):
                    return team, 1.0
                if team.get('shortName') and normalize_name(team['shortName']) == normalize_name(variant):
                    return team, 1.0
    
    # Fuzzy matching
    for team in api_teams:
        # Check main name
        score = similarity_score(db_name, team['name'])
        if score > best_score:
            best_score = score
            best_match = team
        
        # Check short name
        if team.get('shortName'):
            score = similarity_score(db_name, team['shortName'])
            if score > best_score:
                best_score = score
                best_match = team
        
        # Check TLA (three letter abbreviation)
        if team.get('tla'):
            score = similarity_score(db_name, team['tla'])
            if score > best_score:
                best_score = score
                best_match = team
    
    return best_match, best_score


async def fetch_teams_from_competition(session, competition_code):
    """Fetch teams from a specific competition"""
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/teams"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('teams', [])
            else:
                print(f"  ⚠️  Failed to fetch {competition_code}: {response.status}")
                return []
    except Exception as e:
        print(f"  ❌ Error fetching {competition_code}: {e}")
        return []


async def fetch_all_api_teams():
    """Fetch teams from all competitions"""
    all_teams = {}
    
    async with aiohttp.ClientSession() as session:
        for code, name in COMPETITIONS.items():
            print(f"  Fetching {name} ({code})...")
            teams = await fetch_teams_from_competition(session, code)
            for team in teams:
                # Use team ID as key to avoid duplicates
                all_teams[team['id']] = team
            await asyncio.sleep(0.5)  # Rate limiting
    
    return list(all_teams.values())


async def main():
    print(f"{'=' * 60}")
    print(f"Football-Data.org ID Population Script {'(DRY RUN)' if DRY_RUN else ''}")
    print(f"{'=' * 60}\n")
    
    # Connect to MongoDB
    print("📊 Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all football assets from DB
    db_teams = await db.assets.find({'sportKey': 'football'}).to_list(length=200)
    print(f"   Found {len(db_teams)} teams in database\n")
    
    # Fetch teams from Football-Data.org API
    print("🌐 Fetching teams from Football-Data.org API...")
    api_teams = await fetch_all_api_teams()
    print(f"   Fetched {len(api_teams)} teams from API\n")
    
    # Match and update
    print("🔄 Matching teams...\n")
    
    updated = 0
    already_set = 0
    matched = 0
    unmatched = []
    
    for db_team in db_teams:
        name = db_team['name']
        
        # Skip if already has footballDataId
        if db_team.get('footballDataId'):
            already_set += 1
            continue
        
        # Find best match
        match, score = find_best_match(name, api_teams)
        
        if match and score >= 0.7:
            matched += 1
            if not DRY_RUN:
                await db.assets.update_one(
                    {'_id': db_team['_id']},
                    {'$set': {'footballDataId': match['id']}}
                )
                updated += 1
            print(f"   ✅ {name} → ID {match['id']} ({match['name']}) [score: {score:.2f}]")
        else:
            unmatched.append(name)
            if match:
                print(f"   ⚠️  {name} → Best match: {match['name']} [score: {score:.2f}] - TOO LOW")
            else:
                print(f"   ❌ {name} → No match found")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY")
    print(f"{'=' * 60}")
    print(f"   Total teams in DB: {len(db_teams)}")
    print(f"   Already had ID: {already_set}")
    print(f"   Matched: {matched}")
    print(f"   Updated: {updated if not DRY_RUN else f'{matched} (dry run)'}")
    print(f"   Unmatched: {len(unmatched)}")
    
    if unmatched:
        print(f"\n⚠️  Unmatched teams ({len(unmatched)}):")
        for name in unmatched:
            print(f"   - {name}")
    
    client.close()
    print(f"\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
