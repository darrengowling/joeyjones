#!/usr/bin/env python3
"""
Seed New Zealand and England ODI squad players for Oct 2025 series
Replaces existing cricket players with actual squad members
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import uuid

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# England ODI Squad
ENGLAND_PLAYERS = [
    # Batters
    {"name": "Harry Brook", "role": "Batsman", "team": "England"},
    {"name": "Joe Root", "role": "Batsman", "team": "England"},
    {"name": "Ben Duckett", "role": "Batsman", "team": "England"},
    {"name": "Tom Banton", "role": "Batsman", "team": "England"},
    
    # All-rounders
    {"name": "Sam Curran", "role": "All-rounder", "team": "England"},
    {"name": "Liam Dawson", "role": "All-rounder", "team": "England"},
    {"name": "Jacob Bethell", "role": "All-rounder", "team": "England"},
    {"name": "Jamie Overton", "role": "All-rounder", "team": "England"},
    
    # Wicketkeepers
    {"name": "Jos Buttler", "role": "Wicketkeeper", "team": "England"},
    {"name": "Jamie Smith", "role": "Wicketkeeper", "team": "England"},
    
    # Bowlers
    {"name": "Jofra Archer", "role": "Bowler", "team": "England"},
    {"name": "Brydon Carse", "role": "Bowler", "team": "England"},
    {"name": "Adil Rashid", "role": "Bowler", "team": "England"},
    {"name": "Rehan Ahmed", "role": "Bowler", "team": "England"},
    {"name": "Luke Wood", "role": "Bowler", "team": "England"},
    {"name": "Sonny Baker", "role": "Bowler", "team": "England"},
]

# New Zealand ODI Squad
NEW_ZEALAND_PLAYERS = [
    # Batters
    {"name": "Kane Williamson", "role": "Batsman", "team": "New Zealand"},
    {"name": "Devon Conway", "role": "Batsman", "team": "New Zealand"},
    {"name": "Will Young", "role": "Batsman", "team": "New Zealand"},
    
    # All-rounders
    {"name": "Mitchell Santner", "role": "All-rounder", "team": "New Zealand"},
    {"name": "Michael Bracewell", "role": "All-rounder", "team": "New Zealand"},
    {"name": "Mark Chapman", "role": "All-rounder", "team": "New Zealand"},
    {"name": "Daryl Mitchell", "role": "All-rounder", "team": "New Zealand"},
    {"name": "Rachin Ravindra", "role": "All-rounder", "team": "New Zealand"},
    
    # Wicketkeeper
    {"name": "Tom Latham", "role": "Wicketkeeper", "team": "New Zealand"},
    
    # Bowlers
    {"name": "Matt Henry", "role": "Bowler", "team": "New Zealand"},
    {"name": "Kyle Jamieson", "role": "Bowler", "team": "New Zealand"},
    {"name": "Jacob Duffy", "role": "Bowler", "team": "New Zealand"},
    {"name": "Zak Foulkes", "role": "Bowler", "team": "New Zealand"},
    {"name": "Nathan Smith", "role": "Bowler", "team": "New Zealand"},
]

async def seed_players():
    """Replace existing cricket players with NZ & England squads"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🏏 Seeding NZ vs England ODI players...")
    
    # Delete existing cricket players
    result = await db.assets.delete_many({"sportKey": "cricket"})
    print(f"✅ Deleted {result.deleted_count} existing cricket players")
    
    # Combine all players
    all_players = ENGLAND_PLAYERS + NEW_ZEALAND_PLAYERS
    
    # Insert new players
    inserted_count = 0
    for player in all_players:
        player_doc = {
            "id": str(uuid.uuid4()),
            "sportKey": "cricket",
            "externalId": player["name"].lower().replace(" ", "-"),
            "name": player["name"],
            "meta": {
                "team": player["team"],
                "role": player["role"]
            },
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.assets.insert_one(player_doc)
        inserted_count += 1
    
    print(f"✅ Inserted {inserted_count} players")
    print(f"   - England: {len(ENGLAND_PLAYERS)} players")
    print(f"   - New Zealand: {len(NEW_ZEALAND_PLAYERS)} players")
    
    # Update cricket scoring schema to remove milestones and adjust points
    sports = await db.sports.find_one({"key": "cricket"})
    if sports:
        update_result = await db.sports.update_one(
            {"key": "cricket"},
            {"$set": {
                "scoringSchema.rules.run": 1,
                "scoringSchema.rules.wicket": 20,
                "scoringSchema.rules.catch": 10,
                "scoringSchema.rules.stumping": 25,  # UPDATED: 25 points
                "scoringSchema.rules.runOut": 20,
                "scoringSchema.milestones": {}  # Remove all milestones
            }}
        )
        print(f"✅ Updated cricket scoring rules (run: 1pt, wicket: 20pts, catch: 10pts, stumping: 25pts, runOut: 20pts, no milestones)")
    
    client.close()
    print("🎉 Cricket players seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_players())
