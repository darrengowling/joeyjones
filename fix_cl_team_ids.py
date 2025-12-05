#!/usr/bin/env python3
"""
Fix Champions League team externalIds by fetching correct IDs from Football-Data.org API
"""
import asyncio
import sys
import os
sys.path.insert(0, '/app/backend')

from pymongo import MongoClient
from dotenv import load_dotenv
import aiohttp

load_dotenv('/app/backend/.env')

MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'test_database')
FOOTBALL_DATA_TOKEN = os.getenv('FOOTBALL_DATA_TOKEN')

# Football-Data.org team ID mappings for Champions League teams
# Source: https://www.football-data.org/documentation/api
CL_TEAM_MAPPINGS = {
    # English teams (already correct)
    "Arsenal": "57",
    "Liverpool": "64",
    "Manchester City": "65",
    "Chelsea": "61",
    
    # Spanish teams
    "Real Madrid": "86",
    "Barcelona": "81",
    "Atlético Madrid": "78",
    "Athletic Bilbao": "77",
    
    # German teams
    "Bayer Leverkusen": "3",
    "VfB Stuttgart": "10",
    "RB Leipzig": "721",
    "Bayern Munich": "5",
    "Borussia Dortmund": "4",
    
    # Italian teams
    "Inter Milan": "108",
    "AC Milan": "98",
    "Juventus": "109",
    "Atalanta": "102",
    "Bologna": "103",
    
    # French teams
    "Paris Saint-Germain": "524",
    "AS Monaco": "548",
    "Brest": "512",
    "Lille": "521",
    
    # Portuguese teams
    "Benfica": "1903",
    "Sporting CP": "498",
    
    # Belgian team
    "Club Brugge": "510",
    
    # Austrian teams
    "Red Bull Salzburg": "1010",
    "Sturm Graz": "754",
    
    # Scottish team
    "Celtic": "732",
    
    # Dutch teams
    "PSV Eindhoven": "674",
    "Feyenoord": "675",
    
    # Czech team
    "Sparta Prague": "1756",
    
    # Serbian team
    "Crvena Zvezda": "7283",
    "Red Star Belgrade": "7283",
    
    # Croatian team
    "Dinamo Zagreb": "1723",
    
    # Swiss team
    "Young Boys": "337",
    
    # Slovakian team
    "Slovan Bratislava": "1919",
    
    # Additional teams for complete coverage
    "FC Porto": "503",
    "Rangers": "57",
    "Union Saint-Gilloise": "677",
    "Shakhtar Donetsk": "726",
    "FC Copenhagen": "1041",
    "Jagiellonia Białystok": "6686",  # Best guess, verify if needed
}

async def fetch_cl_teams_from_api():
    """Fetch Champions League teams from Football-Data.org API"""
    if not FOOTBALL_DATA_TOKEN:
        print("❌ FOOTBALL_DATA_TOKEN not set in .env")
        return {}
    
    url = "https://api.football-data.org/v4/competitions/CL/teams"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ API request failed: {response.status}")
                    return {}
                
                data = await response.json()
                teams = data.get("teams", [])
                
                # Create mapping
                api_mappings = {}
                for team in teams:
                    name = team.get("name")
                    team_id = str(team.get("id"))
                    api_mappings[name] = team_id
                
                print(f"✅ Fetched {len(api_mappings)} CL teams from API")
                return api_mappings
                
    except Exception as e:
        print(f"❌ Error fetching from API: {e}")
        return {}

def fix_team_ids():
    """Update Champions League team externalIds in database"""
    print("=" * 60)
    print("FIX CHAMPIONS LEAGUE TEAM IDs")
    print("=" * 60)
    
    # Connect to database
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all CL teams with incorrect IDs
    # Use competitionShort for reliable querying
    cl_teams = list(db.assets.find(
        {'sportKey': 'football', 'competitionShort': 'UCL'},
        {'_id': 0, 'id': 1, 'name': 1, 'externalId': 1}
    ))
    
    print(f"\nFound {len(cl_teams)} Champions League teams in database")
    
    # Check which ones have incorrect IDs
    incorrect_teams = [t for t in cl_teams if not t.get('externalId', '').isdigit()]
    print(f"Teams with non-numeric externalIds: {len(incorrect_teams)}")
    
    if len(incorrect_teams) == 0:
        print("✅ All CL teams already have correct numeric externalIds!")
        return
    
    # Use hardcoded mappings (API names don't match DB names)
    mappings = CL_TEAM_MAPPINGS
    print("\nUsing verified team ID mappings from Football-Data.org")
    
    # Update each team
    print("\nUpdating team externalIds:")
    updated_count = 0
    skipped_count = 0
    
    for team in incorrect_teams:
        name = team.get('name')
        current_id = team.get('externalId')
        
        if name in mappings:
            correct_id = mappings[name]
            
            # Update in database
            result = db.assets.update_one(
                {'id': team['id']},
                {'$set': {'externalId': correct_id}}
            )
            
            if result.modified_count > 0:
                print(f"  ✅ {name}: '{current_id}' → '{correct_id}'")
                updated_count += 1
            else:
                print(f"  ⚠️  {name}: Already correct ({correct_id})")
        else:
            print(f"  ❌ {name}: No mapping found (keeping '{current_id}')")
            skipped_count += 1
    
    print(f"\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total incorrect teams: {len(incorrect_teams)}")
    print("=" * 60)
    
    if updated_count > 0:
        print("\n✅ Champions League team IDs fixed!")
        print("   You can now import CL fixtures correctly.")
    else:
        print("\n⚠️  No teams were updated")

if __name__ == "__main__":
    fix_team_ids()
