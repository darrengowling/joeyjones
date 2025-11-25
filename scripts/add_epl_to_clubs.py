import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

EPL_TEAMS = [
    {"name": "Arsenal", "api_football_id": 42, "country": "England"},
    {"name": "Aston Villa", "api_football_id": 66, "country": "England"},
    {"name": "AFC Bournemouth", "api_football_id": 35, "country": "England"},
    {"name": "Brentford", "api_football_id": 55, "country": "England"},
    {"name": "Brighton & Hove Albion", "api_football_id": 51, "country": "England"},
    {"name": "Burnley", "api_football_id": 44, "country": "England"},
    {"name": "Chelsea", "api_football_id": 49, "country": "England"},
    {"name": "Crystal Palace", "api_football_id": 52, "country": "England"},
    {"name": "Everton", "api_football_id": 45, "country": "England"},
    {"name": "Fulham", "api_football_id": 36, "country": "England"},
    {"name": "Leeds United", "api_football_id": 63, "country": "England"},
    {"name": "Liverpool", "api_football_id": 40, "country": "England"},
    {"name": "Manchester City", "api_football_id": 50, "country": "England"},
    {"name": "Manchester United", "api_football_id": 33, "country": "England"},
    {"name": "Newcastle United", "api_football_id": 34, "country": "England"},
    {"name": "Nottingham Forest", "api_football_id": 65, "country": "England"},
    {"name": "Sunderland", "api_football_id": 71, "country": "England"},
    {"name": "Tottenham Hotspur", "api_football_id": 47, "country": "England"},
    {"name": "West Ham United", "api_football_id": 48, "country": "England"},
    {"name": "Wolverhampton Wanderers", "api_football_id": 39, "country": "England"}
]

async def add_epl_to_clubs():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print(f"ADDING EPL TEAMS TO CLUBS COLLECTION: {db_name}")
    print("=" * 70)
    print()
    
    # Check current clubs
    current_clubs = await db.clubs.count_documents({})
    print(f"Current clubs in collection: {current_clubs}")
    print()
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    for team_data in EPL_TEAMS:
        # Check if club already exists
        existing = await db.clubs.find_one({"name": team_data["name"]})
        
        if existing:
            # Check if it has uefaId or needs API-FOOTBALL ID
            if existing.get('uefaId'):
                # Already exists with UEFA ID (Champions League team)
                # Add API-FOOTBALL ID as alternate ID
                await db.clubs.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"apiFootballId": str(team_data["api_football_id"])}}
                )
                print(f"✓ Updated CL team: {team_data['name']} (added API-FOOTBALL ID: {team_data['api_football_id']})")
                updated_count += 1
            else:
                print(f"- Exists: {team_data['name']}")
                skipped_count += 1
        else:
            # Add new EPL team to clubs
            club_doc = {
                "id": str(uuid.uuid4()),
                "name": team_data["name"],
                "uefaId": f"EPL_{team_data['api_football_id']}",  # Use API-FOOTBALL ID with EPL prefix
                "apiFootballId": str(team_data["api_football_id"]),  # Store for API lookups
                "country": team_data["country"],
                "logo": None
            }
            
            await db.clubs.insert_one(club_doc)
            print(f"✓ Added: {team_data['name']} (API-FOOTBALL ID: {team_data['api_football_id']})")
            added_count += 1
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {added_count} added, {updated_count} updated, {skipped_count} skipped")
    print("=" * 70)
    
    # Verify final count
    final_count = await db.clubs.count_documents({})
    print(f"\nTotal clubs in {db_name}.clubs: {final_count}")
    print(f"  - Original CL clubs: {current_clubs}")
    print(f"  - New EPL clubs: {added_count}")
    print(f"  - Total: {final_count}")

asyncio.run(add_epl_to_clubs())
