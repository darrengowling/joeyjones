#!/usr/bin/env python3
"""
Create unique index for league_stats collection
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
backend_dir = Path(__file__).parent.parent / "backend"
load_dotenv(backend_dir / '.env')

async def create_league_stats_index():
    """Create unique index on league_stats collection"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    print(f"Connecting to MongoDB at {mongo_url}/{db_name}")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Create unique compound index on (leagueId, matchId, playerExternalId)
        result = await db.league_stats.create_index([
            ("leagueId", 1),
            ("matchId", 1), 
            ("playerExternalId", 1)
        ], unique=True, name="league_stats_unique_key")
        
        print(f"✅ Created unique index: {result}")
        
        # Also create indexes for efficient leaderboard queries
        await db.league_stats.create_index([("leagueId", 1), ("points", -1)], name="league_leaderboard")
        print("✅ Created leaderboard index")
        
    except Exception as e:
        print(f"⚠️  Index creation result: {str(e)}")
        # Index might already exist, which is fine
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_league_stats_index())