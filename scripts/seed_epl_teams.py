import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone

# EPL teams with API-FOOTBALL team IDs (Season 2024-2025)
EPL_TEAMS = [
    {"name": "Arsenal", "api_football_id": 42, "city": "London"},
    {"name": "Aston Villa", "api_football_id": 66, "city": "Birmingham"},
    {"name": "AFC Bournemouth", "api_football_id": 35, "city": "Bournemouth"},  # Updated official name
    {"name": "Brentford", "api_football_id": 55, "city": "London"},
    {"name": "Brighton & Hove Albion", "api_football_id": 51, "city": "Brighton"},  # Full official name
    {"name": "Burnley", "api_football_id": 44, "city": "Burnley"},
    {"name": "Chelsea", "api_football_id": 49, "city": "London"},
    {"name": "Crystal Palace", "api_football_id": 52, "city": "London"},
    {"name": "Everton", "api_football_id": 45, "city": "Liverpool"},
    {"name": "Fulham", "api_football_id": 36, "city": "London"},
    {"name": "Leeds United", "api_football_id": 63, "city": "Leeds"},  # Full official name
    {"name": "Liverpool", "api_football_id": 40, "city": "Liverpool"},
    {"name": "Manchester City", "api_football_id": 50, "city": "Manchester"},
    {"name": "Manchester United", "api_football_id": 33, "city": "Manchester"},
    {"name": "Newcastle United", "api_football_id": 34, "city": "Newcastle"},  # Full official name
    {"name": "Nottingham Forest", "api_football_id": 65, "city": "Nottingham"},  # Updated official name
    {"name": "Sunderland", "api_football_id": 71, "city": "Sunderland"},
    {"name": "Tottenham Hotspur", "api_football_id": 47, "city": "London"},  # Full official name
    {"name": "West Ham United", "api_football_id": 48, "city": "London"},  # Full official name
    {"name": "Wolverhampton Wanderers", "api_football_id": 39, "city": "Wolverhampton"}  # Full official name
]

async def seed_epl_teams():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/auction_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client.auction_db
    
    print("=" * 70)
    print("SEEDING EPL TEAMS FOR NOVEMBER 29-30, 2025 TOURNAMENT")
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
            "externalId": str(team_data["api_football_id"]),  # API-FOOTBALL team ID
            "city": team_data["city"],
            "selected": True,  # Available for selection by default
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            # Update existing team with API-FOOTBALL ID
            await db.assets.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "externalId": str(team_data["api_football_id"]),
                    "city": team_data.get("city"),
                    "updatedAt": datetime.now(timezone.utc).isoformat()
                }}
            )
            print(f"✓ Updated: {team_data['name']} (API-FOOTBALL ID: {team_data['api_football_id']})")
            updated_count += 1
        else:
            # Insert new team
            await db.assets.insert_one(team_doc)
            print(f"✓ Added: {team_data['name']} (API-FOOTBALL ID: {team_data['api_football_id']})")
            added_count += 1
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {added_count} teams added, {updated_count} teams updated")
    print(f"Total EPL teams in database: {len(EPL_TEAMS)}")
    print("=" * 70)
    print()
    print("Teams are ready for commissioners to select when creating leagues!")
    
    # Verify final count
    total_football_teams = await db.assets.count_documents({"sportKey": "football"})
    print(f"\nTotal football teams in database: {total_football_teams}")

asyncio.run(seed_epl_teams())
