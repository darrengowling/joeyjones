"""
Seed Ashes 2025/26 Players into Database
Seeds Australian and English cricket players for The Ashes competition
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from uuid import uuid4

# Australia Squad
AUSTRALIA_SQUAD = [
    {"name": "Steven Smith", "role": "Batsman", "bowling": "Legbreak Googly", "captain": True},
    {"name": "Alex Carey", "role": "Wicketkeeper", "bowling": None},
    {"name": "Travis Head", "role": "Batsman", "bowling": "Right arm Offbreak"},
    {"name": "Josh Inglis", "role": "Wicketkeeper", "bowling": None},
    {"name": "Usman Khawaja", "role": "Batsman", "bowling": "Right arm Medium"},
    {"name": "Marnus Labuschagne", "role": "Batsman", "bowling": "Right arm Medium fast"},
    {"name": "Jake Weatherald", "role": "Batsman", "bowling": "Legbreak"},
    {"name": "Cameron Green", "role": "All-rounder", "bowling": "Right arm Fast medium"},
    {"name": "Michael Neser", "role": "All-rounder", "bowling": "Right arm Medium fast"},
    {"name": "Beau Webster", "role": "All-rounder", "bowling": "Right arm Medium"},
    {"name": "Scott Boland", "role": "Bowler", "bowling": "Right arm Fast medium"},
    {"name": "Brendan Doggett", "role": "Bowler", "bowling": "Right arm Fast medium"},
    {"name": "Nathan Lyon", "role": "Bowler", "bowling": "Right arm Offbreak"},
    {"name": "Mitchell Starc", "role": "Bowler", "bowling": "Left arm Fast"},
]

# England Squad
ENGLAND_SQUAD = [
    {"name": "Harry Brook", "role": "Batsman", "bowling": "Right arm Medium", "vice_captain": True},
    {"name": "Zak Crawley", "role": "Batsman", "bowling": "Right arm Offbreak"},
    {"name": "Ben Duckett", "role": "Batsman", "bowling": "Right arm Offbreak"},
    {"name": "Ollie Pope", "role": "Batsman", "bowling": None},
    {"name": "Joe Root", "role": "Batsman", "bowling": "Right arm Offbreak"},
    {"name": "Jamie Smith", "role": "Wicketkeeper", "bowling": None},
    {"name": "Ben Stokes", "role": "All-rounder", "bowling": "Right arm Fast medium", "captain": True},
    {"name": "Jacob Bethell", "role": "All-rounder", "bowling": "Slow Left arm Orthodox"},
    {"name": "Brydon Carse", "role": "All-rounder", "bowling": "Right arm Fast medium"},
    {"name": "Will Jacks", "role": "All-rounder", "bowling": "Right arm Offbreak"},
    {"name": "Jofra Archer", "role": "Bowler", "bowling": "Right arm Fast"},
    {"name": "Gus Atkinson", "role": "Bowler", "bowling": "Right arm Fast medium"},
    {"name": "Matthew Potts", "role": "Bowler", "bowling": "Right arm Fast medium"},
    {"name": "Shoaib Bashir", "role": "Bowler", "bowling": "Right arm Offbreak"},
    {"name": "Josh Tongue", "role": "Bowler", "bowling": "Right arm Fast medium"},
    {"name": "Mark Wood", "role": "Bowler", "bowling": "Right arm Fast"},
]


async def seed_ashes_players():
    """Seed Ashes players into the assets collection"""
    
    # Connect to database
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🏏 Seeding Ashes 2025/26 Players...")
    print("=" * 60)
    
    # Clear existing Ashes players (optional - remove if you want to keep old data)
    deleted = await db.assets.delete_many({
        "sportKey": "cricket",
        "meta.nationality": {"$in": ["Australia", "England"]}
    })
    print(f"🗑️  Cleared {deleted.deleted_count} existing Ashes players\n")
    
    players_added = []
    
    # Seed Australia squad
    print("🇦🇺 AUSTRALIA SQUAD")
    print("-" * 60)
    for player_data in AUSTRALIA_SQUAD:
        player = {
            "id": str(uuid4()),
            "sportKey": "cricket",
            "name": player_data["name"],
            "externalId": player_data["name"].lower().replace(" ", "-"),
            "meta": {
                "nationality": "Australia",
                "role": player_data["role"],
                "bowling": player_data["bowling"],
                "team": "Australia",
            },
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        # Add captain/vice-captain flag if present
        if player_data.get("captain"):
            player["meta"]["captain"] = True
        if player_data.get("vice_captain"):
            player["meta"]["vice_captain"] = True
        
        await db.assets.insert_one(player)
        players_added.append(player)
        
        role_emoji = "🏏" if "Batsman" in player_data["role"] else "🧤" if "Wicket" in player_data["role"] else "⚡" if "All-rounder" in player_data["role"] else "🎯"
        captain_mark = " (C)" if player_data.get("captain") else ""
        print(f"  {role_emoji} {player_data['name']}{captain_mark} - {player_data['role']}")
    
    print()
    
    # Seed England squad
    print("🏴 ENGLAND SQUAD")
    print("-" * 60)
    for player_data in ENGLAND_SQUAD:
        player = {
            "id": str(uuid4()),
            "sportKey": "cricket",
            "name": player_data["name"],
            "externalId": player_data["name"].lower().replace(" ", "-"),
            "meta": {
                "nationality": "England",
                "role": player_data["role"],
                "bowling": player_data["bowling"],
                "team": "England",
            },
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        # Add captain/vice-captain flag if present
        if player_data.get("captain"):
            player["meta"]["captain"] = True
        if player_data.get("vice_captain"):
            player["meta"]["vice_captain"] = True
        
        await db.assets.insert_one(player)
        players_added.append(player)
        
        role_emoji = "🏏" if "Batsman" in player_data["role"] else "🧤" if "Wicket" in player_data["role"] else "⚡" if "All-rounder" in player_data["role"] else "🎯"
        captain_mark = " (C)" if player_data.get("captain") else " (VC)" if player_data.get("vice_captain") else ""
        print(f"  {role_emoji} {player_data['name']}{captain_mark} - {player_data['role']}")
    
    print()
    print("=" * 60)
    print(f"✅ Successfully seeded {len(players_added)} Ashes players!")
    print(f"   - Australia: {len(AUSTRALIA_SQUAD)} players")
    print(f"   - England: {len(ENGLAND_SQUAD)} players")
    print()
    print("🎯 Players are ready for The Ashes competition!")
    print("   Commissioners can now select these players during league creation.")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_ashes_players())
