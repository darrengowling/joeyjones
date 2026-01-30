#!/usr/bin/env python3
"""
Merge duplicate team entries in the database.

For teams that appear in multiple competitions (e.g., Arsenal in both PL and CL),
this script:
1. Finds duplicate entries (same name)
2. Merges their competitions arrays
3. Keeps one entry, deletes duplicates

Safe to run multiple times (idempotent).

Usage: python merge_duplicate_teams.py <MONGO_URL> [--dry-run]
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict
import sys

MONGO_URL = sys.argv[1] if len(sys.argv) > 1 else None
DRY_RUN = "--dry-run" in sys.argv

if not MONGO_URL:
    print("Usage: python merge_duplicate_teams.py <MONGO_URL> [--dry-run]")
    sys.exit(1)

DB_NAME = "sport_x_poc"


async def merge_duplicates():
    print(f"Connecting to MongoDB {'(DRY RUN)' if DRY_RUN else ''}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Get all football teams
    teams = await db.assets.find({"sportKey": "football"}).to_list(length=200)
    print(f"📋 Found {len(teams)} total football team entries\n")
    
    # Group by name to find duplicates
    teams_by_name = defaultdict(list)
    for team in teams:
        teams_by_name[team["name"]].append(team)
    
    # Find duplicates
    duplicates = {name: entries for name, entries in teams_by_name.items() if len(entries) > 1}
    
    if not duplicates:
        print("✅ No duplicates found!")
        client.close()
        return
    
    print(f"🔍 Found {len(duplicates)} teams with duplicate entries:\n")
    
    merged_count = 0
    deleted_count = 0
    
    for name, entries in duplicates.items():
        print(f"   📌 {name} ({len(entries)} entries)")
        
        # Collect all competitions from all entries
        all_competitions = set()
        all_competition_codes = set()
        
        for entry in entries:
            comps = entry.get("competitions", [])
            if isinstance(comps, list):
                all_competitions.update(comps)
            elif comps:
                all_competitions.add(comps)
            
            code = entry.get("competitionCode")
            if code:
                all_competition_codes.add(code)
            
            short = entry.get("competitionShort")
            if short:
                all_competition_codes.add(short)
        
        # Remove empty strings
        all_competitions.discard("")
        all_competition_codes.discard("")
        
        print(f"      Merged competitions: {list(all_competitions)}")
        
        # Keep the first entry, update it with merged data
        keeper = entries[0]
        to_delete = entries[1:]
        
        if not DRY_RUN:
            # Update the keeper with merged competitions
            await db.assets.update_one(
                {"_id": keeper["_id"]},
                {
                    "$set": {
                        "competitions": list(all_competitions),
                        "competitionShort": "MULTI" if len(all_competition_codes) > 1 else (list(all_competition_codes)[0] if all_competition_codes else ""),
                    }
                }
            )
            merged_count += 1
            
            # Delete duplicates
            for dup in to_delete:
                await db.assets.delete_one({"_id": dup["_id"]})
                deleted_count += 1
                print(f"      ❌ Deleted duplicate (id: {dup.get('id', 'unknown')[:8]}...)")
        else:
            print(f"      Would keep: id={keeper.get('id', 'unknown')[:8]}...")
            for dup in to_delete:
                print(f"      Would delete: id={dup.get('id', 'unknown')[:8]}...")
    
    print(f"\n📊 Summary:")
    if DRY_RUN:
        print(f"   Would merge: {len(duplicates)} teams")
        print(f"   Would delete: {sum(len(e) - 1 for e in duplicates.values())} duplicate entries")
        print(f"\n💡 Run without --dry-run to apply changes")
    else:
        print(f"   Merged: {merged_count} teams")
        print(f"   Deleted: {deleted_count} duplicate entries")
        
        # Show final count
        final_count = await db.assets.count_documents({"sportKey": "football"})
        print(f"\n📋 Final team count: {final_count}")
    
    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(merge_duplicates())
