#!/usr/bin/env python3
"""
Prompt A: Add recommended indexes to auctions collection
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

async def add_indexes():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("Adding indexes to auctions collection...")
    
    # Add id index (unique)
    try:
        await db.auctions.create_index("id", unique=True)
        print("✅ Created index on 'id' (unique)")
    except Exception as e:
        print(f"⚠️  Index on 'id': {str(e)}")
    
    # Add status index (non-unique)
    try:
        await db.auctions.create_index("status")
        print("✅ Created index on 'status'")
    except Exception as e:
        print(f"⚠️  Index on 'status': {str(e)}")
    
    # Verify
    indexes = await db.auctions.list_indexes().to_list(None)
    print(f"\n📋 Final indexes:")
    for idx in indexes:
        print(f"  - {idx.get('name')}: {idx.get('key')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_indexes())
