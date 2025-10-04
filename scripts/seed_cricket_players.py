#!/usr/bin/env python3
"""
Cricket Players Seeding Script
Reads from seed_cricket_players.csv and inserts into assets collection
"""

import csv
import asyncio
import sys
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

async def seed_cricket_players():
    """Seed cricket players from CSV into assets collection"""
    
    # Get database connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    print(f"Connecting to MongoDB at {mongo_url}/{db_name}")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Path to CSV file
    csv_path = Path(__file__).parent / "seed_cricket_players.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    print(f"📖 Reading cricket players from {csv_path}")
    
    players_inserted = 0
    players_updated = 0
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                external_id = row['externalId'].strip()
                name = row['name'].strip()
                franchise = row['franchise'].strip()
                role = row['role'].strip()
                
                if not all([external_id, name, franchise, role]):
                    print(f"⚠️  Skipping incomplete row: {row}")
                    continue
                
                # Create player document
                player_doc = {
                    "id": str(uuid.uuid4()),
                    "sportKey": "cricket",
                    "externalId": external_id,
                    "name": name,
                    "meta": {
                        "franchise": franchise,
                        "role": role
                    },
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc)
                }
                
                # Upsert on (sportKey, externalId)
                filter_query = {
                    "sportKey": "cricket",
                    "externalId": external_id
                }
                
                # Update the updatedAt timestamp for existing records
                update_doc = player_doc.copy()
                update_doc["updatedAt"] = datetime.now(timezone.utc)
                
                result = await db.assets.update_one(
                    filter_query,
                    {"$set": update_doc},
                    upsert=True
                )
                
                if result.upserted_id:
                    players_inserted += 1
                    print(f"✅ Inserted: {name} ({role}) - {franchise}")
                else:
                    players_updated += 1
                    print(f"🔄 Updated: {name} ({role}) - {franchise}")
    
    except Exception as e:
        print(f"❌ Error reading CSV or inserting data: {str(e)}")
        return False
    
    print(f"\n🏏 Cricket Player Seeding Complete!")
    print(f"   Inserted: {players_inserted} new players")
    print(f"   Updated: {players_updated} existing players")
    print(f"   Total: {players_inserted + players_updated} players processed")
    
    # Verify the seeding by counting cricket assets
    cricket_count = await db.assets.count_documents({"sportKey": "cricket"})
    print(f"   Database now contains {cricket_count} cricket players")
    
    await client.close()
    return True

if __name__ == "__main__":
    print("🏏 Starting Cricket Players Seeding...")
    
    # Load environment variables
    from dotenv import load_dotenv
    backend_dir = Path(__file__).parent.parent / "backend"
    load_dotenv(backend_dir / '.env')
    
    # Run the seeding
    success = asyncio.run(seed_cricket_players())
    
    if success:
        print("✅ Seeding completed successfully!")
        sys.exit(0)
    else:
        print("❌ Seeding failed!")
        sys.exit(1)