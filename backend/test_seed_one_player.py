"""
Test seeding ONE Ashes player to verify format
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from uuid import uuid4

async def test_seed_one_player():
    """Seed one test player to verify datetime format"""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    print("🧪 Testing Ashes player seeding with ONE player...")
    
    # Create test player
    test_player = {
        "id": str(uuid4()),
        "sportKey": "cricket",
        "name": "TEST Steven Smith",
        "externalId": "test-steven-smith",
        "meta": {
            "nationality": "Australia",
            "role": "Batsman",
            "bowling": "Legbreak Googly",
            "team": "Australia",
            "captain": True
        },
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    
    # Insert test player
    await db.assets.insert_one(test_player)
    print(f"✅ Inserted test player: {test_player['name']}")
    
    # Retrieve and verify format
    retrieved = await db.assets.find_one({"id": test_player['id']}, {"_id": 0})
    
    print("\n📋 Retrieved player data:")
    print(f"  Name: {retrieved['name']}")
    print(f"  createdAt type: {type(retrieved['createdAt'])}")
    print(f"  createdAt value: {retrieved['createdAt']}")
    print(f"  updatedAt type: {type(retrieved['updatedAt'])}")
    print(f"  updatedAt value: {retrieved['updatedAt']}")
    
    # Compare with working fopifa1 player
    fopifa1_player = await db.assets.find_one({"name": "Adil Rashid"}, {"_id": 0})
    
    if fopifa1_player:
        print("\n🔍 Comparison with fopifa1 player:")
        print(f"  fopifa1 createdAt type: {type(fopifa1_player['createdAt'])}")
        print(f"  TEST player createdAt type: {type(retrieved['createdAt'])}")
        
        if isinstance(fopifa1_player['createdAt'], type(retrieved['createdAt'])):
            print("  ✅ Types MATCH!")
        else:
            print("  ❌ Types DO NOT MATCH!")
    
    # Clean up test player
    await db.assets.delete_one({"id": test_player['id']})
    print("\n🗑️  Deleted test player")
    
    client.close()
    
    # Return result
    if isinstance(retrieved['createdAt'], str):
        print("\n✅ SUCCESS: Datetime stored as string (correct format)")
        return True
    else:
        print(f"\n❌ FAILURE: Datetime stored as {type(retrieved['createdAt'])} (wrong format)")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_seed_one_player())
    exit(0 if result else 1)
