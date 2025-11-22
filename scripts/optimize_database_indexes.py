#!/usr/bin/env python3
"""
Database Optimization Script - Production Hardening Day 3
Adds all critical indexes for 150-user pilot readiness

Missing indexes identified in pilot readiness assessment:
1. bids: auctionId + createdAt
2. league_stats: leagueId + playerExternalId (if not exists)
3. fixtures: leagueId + startsAt (if not exists)
4. assets: sportKey
5. clubs: leagueId
6. Additional performance indexes

This script is idempotent - safe to run multiple times.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import sys

# Load environment variables
backend_dir = Path(__file__).parent.parent / "backend"
load_dotenv(backend_dir / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

class IndexCreationResult:
    def __init__(self):
        self.created = []
        self.already_exists = []
        self.errors = []
    
    def print_summary(self):
        print("\n" + "="*80)
        print("DATABASE INDEX OPTIMIZATION SUMMARY")
        print("="*80)
        
        if self.created:
            print(f"\n✅ CREATED ({len(self.created)} indexes):")
            for idx in self.created:
                print(f"   - {idx}")
        
        if self.already_exists:
            print(f"\n⏭️  ALREADY EXISTS ({len(self.already_exists)} indexes):")
            for idx in self.already_exists:
                print(f"   - {idx}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for idx, error in self.errors:
                print(f"   - {idx}: {error}")
        
        total = len(self.created) + len(self.already_exists)
        print(f"\n📊 TOTAL INDEXES: {total}")
        print("="*80 + "\n")

async def create_index_safe(collection, index_spec, name, result, **kwargs):
    """
    Safely create an index, handling existing indexes
    
    Args:
        collection: MongoDB collection
        index_spec: Index specification (list of tuples or string)
        name: Index name
        result: IndexCreationResult object
        **kwargs: Additional index options (unique, sparse, etc.)
    """
    try:
        await collection.create_index(index_spec, name=name, **kwargs)
        result.created.append(f"{collection.name}.{name}")
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "index with name" in error_str:
            result.already_exists.append(f"{collection.name}.{name}")
            return True
        else:
            result.errors.append((f"{collection.name}.{name}", str(e)))
            return False

async def optimize_database():
    """Main function to create all missing indexes"""
    
    print(f"🔗 Connecting to MongoDB at {MONGO_URL}/{DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    result = IndexCreationResult()
    
    try:
        print("\n🚀 Starting database optimization...\n")
        
        # ===== CRITICAL #1: Bids Collection =====
        print("📋 Optimizing 'bids' collection...")
        
        # Index for auction-specific bid queries (most common)
        await create_index_safe(
            db.bids,
            [("auctionId", 1), ("createdAt", -1)],
            "bids_auction_time",
            result
        )
        
        # Index for user bid history
        await create_index_safe(
            db.bids,
            [("userId", 1), ("createdAt", -1)],
            "bids_user_time",
            result
        )
        
        # Index for current highest bid queries
        await create_index_safe(
            db.bids,
            [("auctionId", 1), ("amount", -1)],
            "bids_auction_amount",
            result
        )
        
        # ===== CRITICAL #2: League Stats Collection =====
        print("📋 Optimizing 'league_stats' collection...")
        
        # Unique constraint to prevent duplicate scoring
        await create_index_safe(
            db.league_stats,
            [("leagueId", 1), ("matchId", 1), ("playerExternalId", 1)],
            "league_stats_unique_key",
            result,
            unique=True
        )
        
        # Index for leaderboard queries
        await create_index_safe(
            db.league_stats,
            [("leagueId", 1), ("points", -1)],
            "league_stats_leaderboard",
            result
        )
        
        # Index for player-specific queries
        await create_index_safe(
            db.league_stats,
            [("leagueId", 1), ("playerExternalId", 1)],
            "league_stats_player",
            result
        )
        
        # ===== CRITICAL #3: Fixtures Collection =====
        print("📋 Optimizing 'fixtures' collection...")
        
        # Index for league fixture list (by time)
        await create_index_safe(
            db.fixtures,
            [("leagueId", 1), ("startsAt", 1)],
            "fixtures_league_time",
            result
        )
        
        # Index for status filtering
        await create_index_safe(
            db.fixtures,
            [("leagueId", 1), ("status", 1)],
            "fixtures_league_status",
            result
        )
        
        # Index for externalMatchId lookups (CSV upload matching)
        await create_index_safe(
            db.fixtures,
            [("leagueId", 1), ("externalMatchId", 1)],
            "fixtures_external_match",
            result
        )
        
        # ===== CRITICAL #4: Assets Collection =====
        print("📋 Optimizing 'assets' collection...")
        
        # Index for sport filtering
        await create_index_safe(
            db.assets,
            "sportKey",
            "assets_sport",
            result
        )
        
        # Index for search queries
        await create_index_safe(
            db.assets,
            [("sportKey", 1), ("name", 1)],
            "assets_sport_name",
            result
        )
        
        # Index for externalId lookups (fixture imports, roster display)
        await create_index_safe(
            db.assets,
            [("sportKey", 1), ("externalId", 1)],
            "assets_sport_external",
            result
        )
        
        # ===== CRITICAL #5: Clubs Collection =====
        print("📋 Optimizing 'clubs' collection...")
        
        # Index for league roster queries
        await create_index_safe(
            db.clubs,
            "leagueId",
            "clubs_league",
            result
        )
        
        # Index for owner queries
        await create_index_safe(
            db.clubs,
            [("leagueId", 1), ("owner", 1)],
            "clubs_league_owner",
            result
        )
        
        # Index for UEFA ID lookups
        await create_index_safe(
            db.clubs,
            "uefaId",
            "clubs_uefa_id",
            result
        )
        
        # ===== Additional Performance Indexes =====
        print("📋 Optimizing 'auctions' collection...")
        
        # Index for league auctions
        await create_index_safe(
            db.auctions,
            "leagueId",
            "auctions_league",
            result
        )
        
        # Index for auction status queries
        await create_index_safe(
            db.auctions,
            [("leagueId", 1), ("status", 1)],
            "auctions_league_status",
            result
        )
        
        print("📋 Optimizing 'leagues' collection...")
        
        # Index for sport filtering
        await create_index_safe(
            db.leagues,
            "sportKey",
            "leagues_sport",
            result
        )
        
        # Index for commissioner queries
        await create_index_safe(
            db.leagues,
            "commissionerId",
            "leagues_commissioner",
            result
        )
        
        # Index for invite token lookups
        await create_index_safe(
            db.leagues,
            "inviteToken",
            "leagues_invite",
            result,
            sparse=True
        )
        
        print("📋 Optimizing 'league_participants' collection...")
        
        # Index for user's leagues
        await create_index_safe(
            db.league_participants,
            "userId",
            "participants_user",
            result
        )
        
        # Index for league participants
        await create_index_safe(
            db.league_participants,
            [("leagueId", 1), ("joinedAt", 1)],
            "participants_league_joined",
            result
        )
        
        print("📋 Optimizing 'standings' collection...")
        
        # Unique index for league standings
        await create_index_safe(
            db.standings,
            "leagueId",
            "standings_league",
            result,
            unique=True
        )
        
        print("📋 Optimizing 'users' collection...")
        
        # Index for email lookups (auth)
        await create_index_safe(
            db.users,
            "email",
            "users_email",
            result,
            unique=True
        )
        
        print("📋 Optimizing 'magic_links' collection...")
        
        # Index for token lookups with TTL expiration
        await create_index_safe(
            db.magic_links,
            [("email", 1), ("tokenHash", 1)],
            "magic_links_email_token",
            result
        )
        
        # TTL index for automatic cleanup
        await create_index_safe(
            db.magic_links,
            "expiresAt",
            "magic_links_ttl",
            result,
            expireAfterSeconds=0
        )
        
        # Print summary
        result.print_summary()
        
        # List all indexes for verification
        print("🔍 VERIFICATION - Listing all indexes by collection:\n")
        collections_to_check = [
            'bids', 'league_stats', 'fixtures', 'assets', 'clubs',
            'auctions', 'leagues', 'league_participants', 'standings',
            'users', 'magic_links'
        ]
        
        for coll_name in collections_to_check:
            try:
                indexes = await db[coll_name].list_indexes().to_list(None)
                print(f"📁 {coll_name} ({len(indexes)} indexes):")
                for idx in indexes:
                    print(f"   - {idx.get('name')}: {idx.get('key')}")
            except Exception as e:
                print(f"📁 {coll_name}: {e}")
        
        print("\n✅ Database optimization complete!")
        return len(result.errors) == 0
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(optimize_database())
    sys.exit(0 if success else 1)
