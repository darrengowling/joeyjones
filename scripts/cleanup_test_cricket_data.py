#!/usr/bin/env python3
"""
Clean up test cricket leagues and related data
USE CAREFULLY: This deletes test leagues, auctions, bids, fixtures, and scoring data
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

async def cleanup_test_data(league_name_pattern=None, sport_key="cricket", dry_run=True):
    """
    Clean up test cricket data
    
    Args:
        league_name_pattern: Only delete leagues matching this pattern (e.g., "test", "debug")
        sport_key: Sport to clean up (default: cricket)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"🧹 Cricket Data Cleanup {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"Sport: {sport_key}")
    if league_name_pattern:
        print(f"Pattern: leagues containing '{league_name_pattern}'")
    print("-" * 60)
    
    # Find leagues to delete
    query = {"sportKey": sport_key}
    if league_name_pattern:
        query["name"] = {"$regex": league_name_pattern, "$options": "i"}
    
    leagues = await db.leagues.find(query).to_list(None)
    league_ids = [league["id"] for league in leagues]
    
    print(f"\n📋 Found {len(leagues)} leagues to clean:")
    for league in leagues:
        print(f"  - {league['name']} (ID: {league['id'][:8]}...)")
    
    if not leagues:
        print("✅ No leagues found to clean up")
        client.close()
        return
    
    # Count related data
    auctions = await db.auctions.find({"leagueId": {"$in": league_ids}}).to_list(None)
    auction_ids = [a["id"] for a in auctions]
    
    bids_count = await db.bids.count_documents({"auctionId": {"$in": auction_ids}}) if auction_ids else 0
    participants_count = await db.league_participants.count_documents({"leagueId": {"$in": league_ids}})
    fixtures_count = await db.fixtures.count_documents({"leagueId": {"$in": league_ids}})
    standings_count = await db.standings.count_documents({"leagueId": {"$in": league_ids}})
    league_stats_count = await db.league_stats.count_documents({"leagueId": {"$in": league_ids}})
    
    print(f"\n📊 Related data to be deleted:")
    print(f"  - {len(auctions)} auctions")
    print(f"  - {bids_count} bids")
    print(f"  - {participants_count} participants")
    print(f"  - {fixtures_count} fixtures")
    print(f"  - {standings_count} standings")
    print(f"  - {league_stats_count} player stats")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - No data will be deleted")
        print(f"Run with dry_run=False to actually delete")
        client.close()
        return
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: This will permanently delete:")
    print(f"  - {len(leagues)} leagues")
    print(f"  - All related auctions, bids, participants, fixtures, standings, and stats")
    print(f"\nType 'DELETE' to confirm: ", end="")
    
    # For script usage, skip confirmation if running non-interactively
    try:
        confirmation = input()
        if confirmation != "DELETE":
            print("❌ Deletion cancelled")
            client.close()
            return
    except EOFError:
        print("Running non-interactively, proceeding with deletion...")
    
    # Delete in order (to avoid foreign key issues)
    print(f"\n🗑️  Deleting data...")
    
    # Delete league stats
    if league_stats_count > 0:
        result = await db.league_stats.delete_many({"leagueId": {"$in": league_ids}})
        print(f"✅ Deleted {result.deleted_count} player stats")
    
    # Delete standings
    if standings_count > 0:
        result = await db.standings.delete_many({"leagueId": {"$in": league_ids}})
        print(f"✅ Deleted {result.deleted_count} standings")
    
    # Delete fixtures
    if fixtures_count > 0:
        result = await db.fixtures.delete_many({"leagueId": {"$in": league_ids}})
        print(f"✅ Deleted {result.deleted_count} fixtures")
    
    # Delete bids
    if bids_count > 0:
        result = await db.bids.delete_many({"auctionId": {"$in": auction_ids}})
        print(f"✅ Deleted {result.deleted_count} bids")
    
    # Delete auctions
    if auction_ids:
        result = await db.auctions.delete_many({"leagueId": {"$in": league_ids}})
        print(f"✅ Deleted {result.deleted_count} auctions")
    
    # Delete participants
    result = await db.league_participants.delete_many({"leagueId": {"$in": league_ids}})
    print(f"✅ Deleted {result.deleted_count} participants")
    
    # Delete leagues
    result = await db.leagues.delete_many({"id": {"$in": league_ids}})
    print(f"✅ Deleted {result.deleted_count} leagues")
    
    print(f"\n🎉 Cleanup complete!")
    client.close()

async def list_all_cricket_leagues():
    """List all cricket leagues for review"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🏏 All Cricket Leagues:")
    print("-" * 60)
    
    leagues = await db.leagues.find({"sportKey": "cricket"}).to_list(None)
    
    if not leagues:
        print("No cricket leagues found")
    else:
        for league in leagues:
            participants = await db.league_participants.count_documents({"leagueId": league["id"]})
            auction = await db.auctions.find_one({"leagueId": league["id"]})
            
            print(f"\n📋 {league['name']}")
            print(f"   ID: {league['id']}")
            print(f"   Status: {league.get('status', 'unknown')}")
            print(f"   Participants: {participants}")
            print(f"   Budget: £{league['budget'] / 1_000_000:.0f}m")
            print(f"   Players/Manager: {league['clubSlots']}")
            if auction:
                print(f"   Auction: {auction.get('status', 'unknown')}")
    
    client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            # List all cricket leagues
            asyncio.run(list_all_cricket_leagues())
        
        elif command == "clean-test":
            # Clean leagues with "test" or "debug" in name
            dry_run = "--confirm" not in sys.argv
            asyncio.run(cleanup_test_data(
                league_name_pattern="test|debug|demo",
                sport_key="cricket",
                dry_run=dry_run
            ))
        
        elif command == "clean-all":
            # Clean ALL cricket leagues (dangerous!)
            dry_run = "--confirm" not in sys.argv
            asyncio.run(cleanup_test_data(
                league_name_pattern=None,
                sport_key="cricket",
                dry_run=dry_run
            ))
        
        else:
            print("Unknown command. Available commands:")
            print("  list          - List all cricket leagues")
            print("  clean-test    - Delete test/debug/demo leagues (dry run)")
            print("  clean-test --confirm - Actually delete test leagues")
            print("  clean-all     - Delete ALL cricket leagues (dry run)")
            print("  clean-all --confirm - Actually delete ALL cricket leagues")
    else:
        print("Usage: python cleanup_test_cricket_data.py <command>")
        print("\nCommands:")
        print("  list          - List all cricket leagues")
        print("  clean-test    - Delete test/debug/demo leagues")
        print("  clean-all     - Delete ALL cricket leagues")
        print("\nAdd --confirm to actually delete (otherwise dry run)")
