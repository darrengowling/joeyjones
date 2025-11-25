import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load env to get correct database
load_dotenv('/app/backend/.env')

# EPL teams with API-FOOTBALL team IDs
EPL_TEAMS = [
    {"name": "Arsenal", "api_football_id": 42, "city": "London"},
    {"name": "Aston Villa", "api_football_id": 66, "city": "Birmingham"},
    {"name": "AFC Bournemouth", "api_football_id": 35, "city": "Bournemouth"},
    {"name": "Brentford", "api_football_id": 55, "city": "London"},
    {"name": "Brighton & Hove Albion", "api_football_id": 51, "city": "Brighton"},
    {"name": "Burnley", "api_football_id": 44, "city": "Burnley"},
    {"name": "Chelsea", "api_football_id": 49, "city": "London"},
    {"name": "Crystal Palace", "api_football_id": 52, "city": "London"},
    {"name": "Everton", "api_football_id": 45, "city": "Liverpool"},
    {"name": "Fulham", "api_football_id": 36, "city": "London"},
    {"name": "Leeds United", "api_football_id": 63, "city": "Leeds"},
    {"name": "Liverpool", "api_football_id": 40, "city": "Liverpool"},
    {"name": "Manchester City", "api_football_id": 50, "city": "Manchester"},
    {"name": "Manchester United", "api_football_id": 33, "city": "Manchester"},
    {"name": "Newcastle United", "api_football_id": 34, "city": "Newcastle"},
    {"name": "Nottingham Forest", "api_football_id": 65, "city": "Nottingham"},
    {"name": "Sunderland", "api_football_id": 71, "city": "Sunderland"},
    {"name": "Tottenham Hotspur", "api_football_id": 47, "city": "London"},
    {"name": "West Ham United", "api_football_id": 48, "city": "London"},
    {"name": "Wolverhampton Wanderers", "api_football_id": 39, "city": "Wolverhampton"}
]

async def seed_epl_teams():
    # Use CORRECT database from .env
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print(f"SEEDING EPL TEAMS TO CORRECT DATABASE: {db_name}")
    print("=" * 70)
    print()
    
    added_count = 0
    updated_count = 0
    
    for team_data in EPL_TEAMS:
        # Check if team already exists
        existing = await db.assets.find_one({
            "sportKey": "football",
            "name": team_data["name"]
        })
        
        team_doc = {
            "id": str(uuid.uuid4()),
            "sportKey": "football",
            "name": team_data["name"],
            "externalId": str(team_data["api_football_id"]),
            "city": team_data["city"],
            "selected": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            # Update with API-FOOTBALL ID
            await db.assets.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "externalId": str(team_data["api_football_id"]),
                    "city": team_data.get("city"),
                    "updatedAt": datetime.now(timezone.utc).isoformat()
                }}
            )
            print(f"✓ Updated: {team_data['name']} (API ID: {team_data['api_football_id']})")
            updated_count += 1
        else:
            await db.assets.insert_one(team_doc)
            print(f"✓ Added: {team_data['name']} (API ID: {team_data['api_football_id']})")
            added_count += 1
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {added_count} added, {updated_count} updated")
    print(f"Database: {db_name}")
    print("=" * 70)
    
    # Verify
    total = await db.assets.count_documents({"sportKey": "football"})
    print(f"\nTotal football teams in {db_name}: {total}")
    
    # Also check clubs
    clubs_count = await db.clubs.count_documents({})
    print(f"Champions League clubs in {db_name}: {clubs_count}")

asyncio.run(seed_epl_teams())
