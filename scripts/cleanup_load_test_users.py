import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Patterns that identify load test users
LOAD_TEST_USER_PATTERNS = [
    "loadtest",
    "load_test",
    "test@",
    "@test.com",
    "socketio",
    "locust"
]

async def cleanup_load_test_users():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("CLEANING UP LOAD TEST USERS")
    print("=" * 70)
    print()
    
    all_users = await db.users.find({}).to_list(length=None)
    print(f"Total users in database: {len(all_users)}")
    
    load_test_users = []
    real_users = []
    
    for user in all_users:
        email = user.get('email', '').lower()
        name = user.get('name', '').lower()
        is_load_test = any(pattern.lower() in email or pattern.lower() in name for pattern in LOAD_TEST_USER_PATTERNS)
        
        if is_load_test:
            load_test_users.append(user)
        else:
            real_users.append(user)
    
    print(f"Load test users identified: {len(load_test_users)}")
    print(f"Real users to keep: {len(real_users)}")
    print()
    
    if len(load_test_users) == 0:
        print("✓ No load test users found. Database is clean!")
        return
    
    print("Sample load test users to be deleted:")
    print("-" * 70)
    for user in load_test_users[:10]:
        print(f"  - {user.get('email')} ({user.get('name', 'N/A')})")
    if len(load_test_users) > 10:
        print(f"  ... and {len(load_test_users) - 10} more")
    print()
    
    print("Real users to keep:")
    print("-" * 70)
    for user in real_users[:10]:
        print(f"  - {user.get('email')} ({user.get('name', 'N/A')})")
    if len(real_users) > 10:
        print(f"  ... and {len(real_users) - 10} more")
    print()
    
    # Delete load test users
    load_test_user_ids = [user['id'] for user in load_test_users]
    
    if load_test_user_ids:
        result = await db.users.delete_many({"id": {"$in": load_test_user_ids}})
        print(f"✓ Deleted {result.deleted_count} load test users")
    
    print()
    print("=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    
    final_users = await db.users.count_documents({})
    print(f"\nTotal users remaining: {final_users}")

asyncio.run(cleanup_load_test_users())
