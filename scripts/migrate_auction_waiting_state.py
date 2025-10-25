#!/usr/bin/env python3
"""
Prompt A: Migration utility to backfill auction status field
Ensures existing auctions have proper status values without breaking behavior
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

async def migrate_auction_status():
    """
    Backfill auction status field for existing auctions
    
    Rules:
    - If status is missing and currentLot > 0 → set status = "active"
    - If status is missing and currentLot = 0 → set status = "waiting"
    - If status = "pending" → convert to "waiting"
    - If status = "completed" → leave as is (do NOT modify)
    - Add currentLot = 0 if missing
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("Auction Status Migration (Prompt A)")
    print("=" * 60)
    
    # Find all auctions
    auctions = await db.auctions.find({}).to_list(None)
    print(f"\n📊 Found {len(auctions)} total auctions")
    
    if not auctions:
        print("✅ No auctions to migrate")
        client.close()
        return
    
    # Analyze current state
    needs_update = []
    already_correct = []
    completed_count = 0
    
    for auction in auctions:
        auction_id = auction.get("id", "unknown")
        current_status = auction.get("status")
        current_lot = auction.get("currentLot", 0)
        
        # Skip completed auctions
        if current_status == "completed":
            completed_count += 1
            continue
        
        # Determine what status should be
        if current_lot > 0:
            expected_status = "active"
        else:
            expected_status = "waiting"
        
        # Check if update needed
        if current_status != expected_status or current_status == "pending":
            needs_update.append({
                "id": auction_id,
                "current_status": current_status,
                "current_lot": current_lot,
                "new_status": expected_status,
                "league_id": auction.get("leagueId", "unknown")
            })
        else:
            already_correct.append(auction_id)
    
    print(f"\n📈 Migration Analysis:")
    print(f"  - Already correct: {len(already_correct)}")
    print(f"  - Need update: {len(needs_update)}")
    print(f"  - Completed (skipped): {completed_count}")
    
    if not needs_update:
        print("\n✅ All auctions already have correct status")
        client.close()
        return
    
    # Show what will be updated
    print(f"\n🔧 Auctions to update:")
    for item in needs_update[:10]:  # Show first 10
        print(f"  - {item['id'][:8]}... (League: {item['league_id'][:8]}...)")
        print(f"    Current: status={item['current_status']}, lot={item['current_lot']}")
        print(f"    New: status={item['new_status']}")
    
    if len(needs_update) > 10:
        print(f"  ... and {len(needs_update) - 10} more")
    
    # Confirm
    print(f"\n⚠️  Ready to update {len(needs_update)} auctions")
    print("Type 'MIGRATE' to proceed: ", end="")
    
    try:
        confirmation = input()
        if confirmation != "MIGRATE":
            print("❌ Migration cancelled")
            client.close()
            return
    except EOFError:
        print("Running non-interactively, proceeding...")
    
    # Perform migration
    print(f"\n🚀 Starting migration...")
    updated_count = 0
    
    for item in needs_update:
        update_doc = {
            "$set": {
                "status": item["new_status"]
            }
        }
        
        # Also ensure currentLot exists
        if "current_lot" not in item or item["current_lot"] is None:
            update_doc["$set"]["currentLot"] = 0
        
        result = await db.auctions.update_one(
            {"id": item["id"]},
            update_doc
        )
        
        if result.modified_count > 0:
            updated_count += 1
            print(f"  ✅ Updated {item['id'][:8]}... → status={item['new_status']}")
    
    print(f"\n🎉 Migration complete!")
    print(f"  - Updated: {updated_count}/{len(needs_update)} auctions")
    
    # Verify
    print(f"\n🔍 Verifying migration...")
    verification = await db.auctions.find({
        "status": {"$exists": True},
        "status": {"$in": ["waiting", "active", "paused", "completed"]}
    }).to_list(None)
    
    bad_status = await db.auctions.find({
        "status": {"$nin": ["waiting", "active", "paused", "completed"]}
    }).to_list(None)
    
    print(f"  - Valid status: {len(verification)} auctions")
    print(f"  - Invalid status: {len(bad_status)} auctions")
    
    if bad_status:
        print(f"\n⚠️  Found {len(bad_status)} auctions with invalid status:")
        for auction in bad_status[:5]:
            print(f"    - {auction['id'][:8]}... status={auction.get('status')}")
    else:
        print(f"\n✅ All auctions have valid status values")
    
    client.close()

async def verify_indexes():
    """
    Prompt A: Verify required indexes exist on auctions collection
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("\n" + "=" * 60)
    print("Index Verification")
    print("=" * 60)
    
    # Get existing indexes
    indexes = await db.auctions.list_indexes().to_list(None)
    
    print(f"\n📋 Current indexes on 'auctions' collection:")
    for idx in indexes:
        name = idx.get("name")
        keys = idx.get("key", {})
        unique = idx.get("unique", False)
        print(f"  - {name}: {keys} {'(unique)' if unique else ''}")
    
    # Check required indexes
    required = {
        "id": False,  # Not unique if using external system
        "leagueId": False,
        "status": False  # Optional but recommended
    }
    
    existing_fields = set()
    for idx in indexes:
        keys = idx.get("key", {})
        for field in keys.keys():
            existing_fields.add(field)
    
    print(f"\n✅ Index coverage:")
    for field, should_be_unique in required.items():
        has_index = field in existing_fields
        status_emoji = "✅" if has_index else "⚠️"
        print(f"  {status_emoji} {field}: {'Indexed' if has_index else 'Not indexed'}")
    
    # Recommendations
    missing = [f for f in required.keys() if f not in existing_fields]
    if missing:
        print(f"\n💡 Recommended indexes to add:")
        for field in missing:
            print(f"  - db.auctions.create_index('{field}')")
    else:
        print(f"\n✅ All recommended indexes exist")
    
    client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify-only":
        # Just verify indexes
        asyncio.run(verify_indexes())
    else:
        # Run migration + verification
        asyncio.run(migrate_auction_status())
        asyncio.run(verify_indexes())
