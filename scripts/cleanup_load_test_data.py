import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Patterns that identify load test leagues
LOAD_TEST_PATTERNS = [
    "Load Test",
    "Socket.IO",
    "load test",
    "socketio",
    "test league",
    "auction_socketio",
    "loadtest"
]

async def cleanup_load_tests():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("CLEANING UP LOAD TEST DATA")
    print("=" * 70)
    print()
    
    # Step 1: Identify load test leagues
    all_leagues = await db.leagues.find({}).to_list(length=None)
    print(f"Total leagues in database: {len(all_leagues)}")
    
    load_test_leagues = []
    real_leagues = []
    
    for league in all_leagues:
        name = league.get('name', '').lower()
        is_load_test = any(pattern.lower() in name for pattern in LOAD_TEST_PATTERNS)
        
        if is_load_test:
            load_test_leagues.append(league)
        else:
            real_leagues.append(league)
    
    print(f"Load test leagues identified: {len(load_test_leagues)}")
    print(f"Real leagues to keep: {len(real_leagues)}")
    print()
    
    if len(load_test_leagues) == 0:
        print("✓ No load test leagues found. Database is clean!")
        return
    
    print("Load test leagues to be deleted:")
    print("-" * 70)
    for league in load_test_leagues[:10]:  # Show first 10
        print(f"  - {league.get('name')} (ID: {league.get('id')[:8]}...)")
    if len(load_test_leagues) > 10:
        print(f"  ... and {len(load_test_leagues) - 10} more")
    print()
    
    print("Real leagues to keep:")
    print("-" * 70)
    for league in real_leagues[:10]:  # Show first 10
        print(f"  - {league.get('name')} (ID: {league.get('id')[:8]}...)")
    if len(real_leagues) > 10:
        print(f"  ... and {len(real_leagues) - 10} more")
    print()
    
    # Step 2: Delete load test leagues
    load_test_ids = [league['id'] for league in load_test_leagues]
    
    if load_test_ids:
        # Delete leagues
        result = await db.leagues.delete_many({"id": {"$in": load_test_ids}})
        print(f"✓ Deleted {result.deleted_count} load test leagues")
        
        # Delete related participants
        participants_result = await db.league_participants.delete_many({"leagueId": {"$in": load_test_ids}})
        print(f"✓ Deleted {participants_result.deleted_count} load test participants")
        
        # Delete related auctions
        auctions_result = await db.auctions.delete_many({"leagueId": {"$in": load_test_ids}})
        print(f"✓ Deleted {auctions_result.deleted_count} load test auctions")
        
        # Delete related bids
        bids_result = await db.bids.delete_many({"leagueId": {"$in": load_test_ids}})
        print(f"✓ Deleted {bids_result.deleted_count} load test bids")
    
    print()
    print("=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    
    # Verify final counts
    final_leagues = await db.leagues.count_documents({})
    final_participants = await db.league_participants.count_documents({})
    final_auctions = await db.auctions.count_documents({})
    final_bids = await db.bids.count_documents({})
    
    print(f"\nDatabase Status After Cleanup:")
    print(f"  Leagues: {final_leagues}")
    print(f"  Participants: {final_participants}")
    print(f"  Auctions: {final_auctions}")
    print(f"  Bids: {final_bids}")

asyncio.run(cleanup_load_tests())
