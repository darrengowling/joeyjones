#!/usr/bin/env python3
"""
Quick script to delete all fixtures from a league
Usage: python delete_fixtures.py <league-name-or-id>
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

async def delete_fixtures(league_identifier):
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    
    # Try to find league by name or ID
    league = await db.leagues.find_one({
        "$or": [
            {"id": league_identifier},
            {"name": {"$regex": league_identifier, "$options": "i"}}
        ]
    })
    
    if not league:
        print(f"❌ League not found: {league_identifier}")
        return
    
    print(f"Found league: {league['name']} (ID: {league['id']})")
    
    # Count existing fixtures
    count = await db.fixtures.count_documents({"leagueId": league['id']})
    print(f"Found {count} fixtures to delete")
    
    if count == 0:
        print("✅ No fixtures to delete")
        return
    
    # Delete all fixtures
    result = await db.fixtures.delete_many({"leagueId": league['id']})
    
    print(f"✅ Deleted {result.deleted_count} fixtures")
    
    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_fixtures.py <league-name-or-id>")
        print("Example: python delete_fixtures.py nz12")
        sys.exit(1)
    
    league_id = sys.argv[1]
    asyncio.run(delete_fixtures(league_id))
