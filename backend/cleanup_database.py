#!/usr/bin/env python3
"""
Database cleanup script to remove all test data from MongoDB
This will clear: users, leagues, auctions, bids, and club data
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_database():
    """Clear all collections to provide a clean slate"""
    
    # Get database connection details
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    print(f"Connecting to MongoDB at: {mongo_url}")
    print(f"Database: {db_name}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # List of collections to clear
        collections_to_clear = [
            'users',
            'leagues', 
            'auctions',
            'bids',
            'clubs',
            'participants'
        ]
        
        print("\nCleaning up database...")
        
        for collection_name in collections_to_clear:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            
            # Clear the collection
            result = await collection.delete_many({})
            
            print(f"Collection '{collection_name}': Deleted {result.deleted_count} documents (was {count_before})")
        
        print("\n✅ Database cleanup completed successfully!")
        print("The application now has a clean slate with no test data.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        raise
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_database())