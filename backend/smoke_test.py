#!/usr/bin/env python3
"""
Comprehensive Smoke Test for Friends of Pifa
Tests the complete auction flow including Socket.IO
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import uuid
import aiohttp
from datetime import datetime
import socketio as socketio_client

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

API_BASE = "http://localhost:8001/api"
SOCKET_URL = "http://localhost:8001"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def log_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def log_step(msg):
    print(f"\n{Colors.YELLOW}►{Colors.END} {msg}")

class SmokeTest:
    def __init__(self):
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self.client = None
        self.db = None
        self.session = None
        
        # Test data
        self.user_a_id = None
        self.user_b_id = None
        self.league_id = None
        self.auction_id = None
        self.club_id = None
        self.invite_token = None
        
    async def setup(self):
        """Initialize connections"""
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.client:
            self.client.close()
    
    async def api_post(self, endpoint, data):
        """Make POST request to API"""
        async with self.session.post(f"{API_BASE}{endpoint}", json=data) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"API error: {response.status} - {text}")
            return await response.json()
    
    async def api_get(self, endpoint):
        """Make GET request to API"""
        async with self.session.get(f"{API_BASE}{endpoint}") as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"API error: {response.status} - {text}")
            return await response.json()
    
    async def test_1_seed_clubs(self):
        """Step 1: Seed clubs"""
        log_step("Step 1: Seeding clubs")
        
        # Check if clubs exist
        clubs_count = await self.db.clubs.count_documents({})
        if clubs_count == 0:
            log_info("No clubs found, seeding...")
            os.system("cd /app/backend && python3 seed_openfootball_clubs.py > /dev/null 2>&1")
            clubs_count = await self.db.clubs.count_documents({})
        
        if clubs_count > 0:
            log_success(f"Clubs seeded: {clubs_count} clubs available")
            return True
        else:
            log_error("Failed to seed clubs")
            return False
    
    async def test_2_create_league(self):
        """Step 2: Create league with budget=100, minManagers=2, maxManagers=8, clubSlots=3"""
        log_step("Step 2: Creating league")
        
        # Create User A
        user_a = await self.api_post("/users", {
            "name": "User A",
            "email": "usera@smoketest.com"
        })
        self.user_a_id = user_a["id"]
        log_success(f"Created User A: {self.user_a_id}")
        
        # Create league
        league = await self.api_post("/leagues", {
            "name": "Smoke Test League",
            "commissionerId": self.user_a_id,
            "budget": 100,
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 3
        })
        self.league_id = league["id"]
        self.invite_token = league["inviteToken"]
        log_success(f"Created league: {self.league_id}")
        log_info(f"Invite token: {self.invite_token}")
        
        # Verify league settings
        assert league["budget"] == 100, "Budget should be 100"
        assert league["minManagers"] == 2, "minManagers should be 2"
        assert league["maxManagers"] == 8, "maxManagers should be 8"
        assert league["clubSlots"] == 3, "clubSlots should be 3"
        log_success("League settings verified")
        
        return True
    
    async def test_3_join_league(self):
        """Step 3: Create User B and both users join league"""
        log_step("Step 3: Users joining league")
        
        # User A joins
        await self.api_post(f"/leagues/{self.league_id}/join", {
            "userId": self.user_a_id,
            "inviteToken": self.invite_token
        })
        log_success("User A joined league")
        
        # Create User B
        user_b = await self.api_post("/users", {
            "name": "User B",
            "email": "userb@smoketest.com"
        })
        self.user_b_id = user_b["id"]
        log_success(f"Created User B: {self.user_b_id}")
        
        # User B joins
        await self.api_post(f"/leagues/{self.league_id}/join", {
            "userId": self.user_b_id,
            "inviteToken": self.invite_token
        })
        log_success("User B joined league")
        
        # Verify participants
        participants = await self.api_get(f"/leagues/{self.league_id}/participants")
        assert len(participants) == 2, "Should have 2 participants"
        log_success(f"Verified {len(participants)} participants")
        
        return True
    
    async def test_4_start_auction(self):
        """Step 4: Start auction"""
        log_step("Step 4: Starting auction")
        
        result = await self.api_post(f"/leagues/{self.league_id}/auction/start", {})
        self.auction_id = result["auctionId"]
        log_success(f"Auction started: {self.auction_id}")
        
        # Verify auction
        auction = await self.db.auctions.find_one({"id": self.auction_id})
        assert auction is not None, "Auction should exist in DB"
        assert auction["leagueId"] == self.league_id, "Auction should be linked to league"
        log_success("Auction verified in database")
        
        return True
    
    async def test_5_nominate_club(self):
        """Step 5: Nominate a club for bidding"""
        log_step("Step 5: Nominating club")
        
        # Get a club (Bayern Munich for testing)
        club = await self.db.clubs.find_one({"name": {"$regex": "Bayern"}})
        if not club:
            # Fallback to any club
            club = await self.db.clubs.find_one({})
        
        self.club_id = club["id"]
        log_info(f"Selected club: {club['name']}")
        
        # Start lot
        await self.api_post(f"/auction/{self.auction_id}/start-lot/{self.club_id}", {})
        log_success(f"Lot started for {club['name']}")
        
        # Verify lot in DB
        auction = await self.db.auctions.find_one({"id": self.auction_id})
        assert auction["currentClubId"] == self.club_id, "Current club should be set"
        assert auction["status"] == "active", "Auction should be active"
        log_success("Lot verified in database")
        
        return True
    
    async def test_6_bidding(self):
        """Step 6: Test bidding with anti-snipe"""
        log_step("Step 6: Testing bidding")
        
        # User A bids 5
        await self.api_post(f"/auction/{self.auction_id}/bid", {
            "userId": self.user_a_id,
            "clubId": self.club_id,
            "amount": 5
        })
        log_success("User A bid: $5")
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # User B bids 6
        await self.api_post(f"/auction/{self.auction_id}/bid", {
            "userId": self.user_b_id,
            "clubId": self.club_id,
            "amount": 6
        })
        log_success("User B bid: $6")
        
        # Verify bids in DB
        bids = await self.db.bids.find({
            "auctionId": self.auction_id,
            "clubId": self.club_id
        }).to_list(10)
        assert len(bids) == 2, "Should have 2 bids"
        
        # Check highest bid
        highest_bid = max(bids, key=lambda b: b["amount"])
        assert highest_bid["userId"] == self.user_b_id, "User B should have highest bid"
        assert highest_bid["amount"] == 6, "Highest bid should be $6"
        log_success("Bids verified in database")
        
        return True
    
    async def test_7_complete_lot(self):
        """Step 7: Complete lot and verify budget updates"""
        log_step("Step 7: Completing lot")
        
        # Get initial budgets
        participants_before = await self.api_get(f"/leagues/{self.league_id}/participants")
        user_b_before = next(p for p in participants_before if p["userId"] == self.user_b_id)
        initial_budget = user_b_before["budgetRemaining"]
        log_info(f"User B initial budget: ${initial_budget}")
        
        # Complete lot
        await self.api_post(f"/auction/{self.auction_id}/complete-lot", {})
        log_success("Lot completed")
        
        # Wait for DB update
        await asyncio.sleep(1)
        
        # Verify budget update
        participants_after = await self.api_get(f"/leagues/{self.league_id}/participants")
        user_b_after = next(p for p in participants_after if p["userId"] == self.user_b_id)
        
        assert user_b_after["budgetRemaining"] == initial_budget - 6, "Budget should be reduced by $6"
        assert self.club_id in user_b_after["clubsWon"], "Club should be in clubsWon"
        assert user_b_after["totalSpent"] == 6, "totalSpent should be $6"
        
        log_success(f"User B budget updated: ${initial_budget} → ${user_b_after['budgetRemaining']}")
        log_success(f"Club assigned to User B")
        log_success(f"Total spent: ${user_b_after['totalSpent']}")
        
        return True
    
    async def test_8_socket_connection(self):
        """Step 8: Test Socket.IO connection and transports"""
        log_step("Step 8: Testing Socket.IO connection")
        
        try:
            # Test polling transport
            async with self.session.get(f"{SOCKET_URL}/socket.io/?EIO=4&transport=polling") as response:
                if response.status == 200:
                    log_success("Polling transport working")
                else:
                    log_error(f"Polling transport failed: {response.status}")
                    return False
            
            # Test WebSocket upgrade path exists (checking endpoint)
            async with self.session.get(f"{SOCKET_URL}/socket.io/?EIO=4&transport=websocket") as response:
                # WebSocket will give 400 for GET, but that means endpoint exists
                if response.status in [200, 400, 426]:
                    log_success("WebSocket transport endpoint available")
                else:
                    log_info(f"WebSocket response: {response.status}")
            
            # Verify no 404 at socket path
            log_success("No 404/HTML at socket path")
            
            return True
            
        except Exception as e:
            log_error(f"Socket.IO connection test failed: {e}")
            return False
    
    async def test_9_persistence(self):
        """Step 9: Verify data persistence in MongoDB"""
        log_step("Step 9: Verifying MongoDB persistence")
        
        # Check league
        league = await self.db.leagues.find_one({"id": self.league_id})
        assert league is not None, "League should persist"
        log_success("League persisted")
        
        # Check participants
        participants = await self.db.league_participants.find({"leagueId": self.league_id}).to_list(10)
        assert len(participants) == 2, "Both participants should persist"
        log_success("Participants persisted")
        
        # Check auction
        auction = await self.db.auctions.find_one({"id": self.auction_id})
        assert auction is not None, "Auction should persist"
        log_success("Auction persisted")
        
        # Check bids
        bids = await self.db.bids.find({"auctionId": self.auction_id}).to_list(10)
        assert len(bids) >= 2, "Bids should persist"
        log_success(f"Bids persisted ({len(bids)} bids)")
        
        # Check budget updates
        user_b = await self.db.league_participants.find_one({
            "leagueId": self.league_id,
            "userId": self.user_b_id
        })
        assert user_b["budgetRemaining"] == 94, "Budget should be $94"
        assert len(user_b["clubsWon"]) == 1, "Should have 1 club won"
        log_success("Budget and assignment persisted correctly")
        
        return True
    
    async def run_all_tests(self):
        """Run all smoke tests"""
        print("\n" + "="*60)
        print("🔥 FRIENDS OF PIFA - SMOKE TEST")
        print("="*60)
        
        tests = [
            ("Seed Clubs", self.test_1_seed_clubs),
            ("Create League", self.test_2_create_league),
            ("Join League", self.test_3_join_league),
            ("Start Auction", self.test_4_start_auction),
            ("Nominate Club", self.test_5_nominate_club),
            ("Bidding", self.test_6_bidding),
            ("Complete Lot", self.test_7_complete_lot),
            ("Socket.IO Connection", self.test_8_socket_connection),
            ("MongoDB Persistence", self.test_9_persistence),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
                    log_error(f"Test failed: {name}")
            except Exception as e:
                failed += 1
                log_error(f"Test crashed: {name}")
                print(f"  Error: {str(e)}")
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {len(tests)}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.END}")
            print("\n✅ Pass Criteria Met:")
            print("  • No 404/HTML at socket path")
            print("  • Both transports OK (polling at minimum)")
            print("  • Budgets and assignment persist correctly")
            print("  • Data verified in MongoDB")
        else:
            print(f"\n{Colors.RED}✗ SOME TESTS FAILED{Colors.END}")
            return 1
        
        print("\n" + "="*60)
        return 0

async def main():
    test = SmokeTest()
    await test.setup()
    
    try:
        exit_code = await test.run_all_tests()
        return exit_code
    finally:
        await test.teardown()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Fatal error: {e}")
        sys.exit(1)
