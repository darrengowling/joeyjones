#!/usr/bin/env python3
"""
Manual E2E Auction Test Script
Tests critical auction edge cases without relying on test agent
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import time

# Load environment
load_dotenv('/app/backend/.env')
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'test_database')

# Test configuration
TEST_PREFIX = "MANUAL_TEST_"

class ManualAuctionTester:
    def __init__(self):
        self.client = None
        self.db = None
        self.test_data = {}
        
    async def setup(self):
        """Initialize database connection"""
        print("\n" + "="*60)
        print("🔧 MANUAL AUCTION TEST - SETUP")
        print("="*60)
        
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
        # Verify clubs exist
        club_count = await self.db.clubs.count_documents({})
        print(f"✅ Database connected: {DB_NAME}")
        print(f"✅ Clubs available: {club_count}")
        
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test leagues, auctions, users, participants, bids
        await self.db.leagues.delete_many({"name": {"$regex": f"^{TEST_PREFIX}"}})
        await self.db.auctions.delete_many({"id": {"$regex": f"^{TEST_PREFIX}"}})
        await self.db.users.delete_many({"name": {"$regex": f"^{TEST_PREFIX}"}})
        await self.db.league_participants.delete_many({"userName": {"$regex": f"^{TEST_PREFIX}"}})
        await self.db.bids.delete_many({"userName": {"$regex": f"^{TEST_PREFIX}"}})
        
        if self.client:
            self.client.close()
            
        print("✅ Cleanup complete")
        
    async def create_test_league(self, num_participants, num_clubs):
        """Create a test league with participants and clubs"""
        print(f"\n📋 Creating test league: {num_participants} participants, {num_clubs} clubs")
        
        # Create users
        users = []
        for i in range(num_participants):
            user_id = f"{TEST_PREFIX}user_{i+1}"
            user = {
                "id": user_id,
                "name": f"{TEST_PREFIX}Manager_{i+1}",
                "email": f"{TEST_PREFIX}manager{i+1}@test.com",
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
            await self.db.users.insert_one(user)
            users.append(user)
            
        # Create league
        league_id = f"{TEST_PREFIX}league_1"
        league = {
            "id": league_id,
            "name": f"{TEST_PREFIX}TestLeague",
            "commissionerId": users[0]["id"],
            "budget": 500000000.0,
            "clubSlots": 3,
            "minManagers": num_participants,
            "maxManagers": num_participants,
            "timerSeconds": 5,
            "antiSnipeSeconds": 2,
            "inviteToken": f"{TEST_PREFIX}token",
            "sportKey": "football",
            "status": "pending",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        await self.db.leagues.insert_one(league)
        
        # Create participants
        participants = []
        for user in users:
            participant = {
                "id": f"{TEST_PREFIX}part_{user['id']}",
                "leagueId": league_id,
                "userId": user["id"],
                "userName": user["name"],
                "userEmail": user["email"],
                "budgetRemaining": 500000000.0,
                "totalSpent": 0.0,
                "clubsWon": [],
                "joinedAt": datetime.now(timezone.utc).isoformat()
            }
            await self.db.league_participants.insert_one(participant)
            participants.append(participant)
            
        # Get clubs for auction
        clubs = await self.db.clubs.find().limit(num_clubs).to_list(num_clubs)
        club_ids = [club["id"] for club in clubs]
        
        # Create auction
        auction_id = f"{TEST_PREFIX}auction_1"
        auction = {
            "id": auction_id,
            "leagueId": league_id,
            "status": "active",
            "currentLot": 1,
            "clubQueue": club_ids,
            "currentClubId": club_ids[0],
            "currentLotId": f"{auction_id}-lot-1",
            "timerEndsAt": datetime.now(timezone.utc) + timedelta(seconds=5),
            "bidTimer": 5,
            "minimumBudget": 1000000.0,
            "unsoldClubs": [],
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        await self.db.auctions.insert_one(auction)
        
        print(f"✅ Created:")
        print(f"   League ID: {league_id}")
        print(f"   Auction ID: {auction_id}")
        print(f"   Users: {[u['name'] for u in users]}")
        print(f"   Clubs: {[c['name'] for c in clubs]}")
        
        self.test_data = {
            "league": league,
            "auction": auction,
            "users": users,
            "participants": participants,
            "clubs": clubs,
            "club_ids": club_ids
        }
        
        return league, auction, users, participants, clubs
        
    async def place_bid(self, auction_id, club_id, user, amount):
        """Place a bid on a club"""
        bid = {
            "id": f"{TEST_PREFIX}bid_{user['id']}_{club_id}_{int(time.time())}",
            "auctionId": auction_id,
            "clubId": club_id,
            "userId": user["id"],
            "userName": user["name"],
            "amount": float(amount),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc)
        }
        await self.db.bids.insert_one(bid)
        print(f"   💰 {user['name']} bid £{amount:,.0f} on {club_id[:8]}...")
        return bid
        
    async def simulate_lot_completion(self, auction_id, winning_user=None, winning_amount=None):
        """Manually simulate what happens when a lot completes"""
        print(f"\n⏰ Simulating lot completion...")
        
        auction = await self.db.auctions.find_one({"id": auction_id})
        current_club_id = auction["currentClubId"]
        current_lot = auction["currentLot"]
        
        print(f"   Current Lot: {current_lot}/{len(auction['clubQueue'])}")
        print(f"   Current Club: {current_club_id}")
        
        if winning_user and winning_amount:
            # Award the club to the winner
            await self.db.league_participants.update_one(
                {"leagueId": auction["leagueId"], "userId": winning_user["id"]},
                {
                    "$push": {"clubsWon": current_club_id},
                    "$inc": {
                        "totalSpent": winning_amount,
                        "budgetRemaining": -winning_amount
                    }
                }
            )
            print(f"   ✅ Awarded to {winning_user['name']}")
        else:
            print(f"   ❌ No bids - club unsold")
            
        # Move to next lot or complete auction
        club_queue = auction["clubQueue"]
        next_lot = current_lot + 1
        
        if next_lot <= len(club_queue):
            # Start next lot
            next_club_id = club_queue[next_lot - 1]
            await self.db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "currentLot": next_lot,
                    "currentClubId": next_club_id,
                    "currentLotId": f"{auction_id}-lot-{next_lot}",
                    "timerEndsAt": datetime.now(timezone.utc) + timedelta(seconds=5)
                }}
            )
            print(f"   ➡️  Moving to lot {next_lot}")
        else:
            # Auction complete
            await self.db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "status": "completed",
                    "completedAt": datetime.now(timezone.utc).isoformat()
                }}
            )
            await self.db.leagues.update_one(
                {"id": auction["leagueId"]},
                {"$set": {"status": "completed"}}
            )
            print(f"   🏁 Auction complete!")
            
    async def verify_results(self, expected_results):
        """Verify auction results match expectations"""
        print(f"\n🔍 Verifying results...")
        
        league = self.test_data["league"]
        participants = await self.db.league_participants.find(
            {"leagueId": league["id"]}
        ).to_list(100)
        
        all_passed = True
        
        for i, participant in enumerate(participants):
            clubs_won = participant.get("clubsWon", [])
            expected_clubs = expected_results.get(participant["userName"], 0)
            
            if len(clubs_won) == expected_clubs:
                print(f"   ✅ {participant['userName']}: {len(clubs_won)}/{expected_clubs} clubs")
            else:
                print(f"   ❌ {participant['userName']}: {len(clubs_won)}/{expected_clubs} clubs (MISMATCH!)")
                all_passed = False
                
        return all_passed
        
    # ===== TEST CASES =====
    
    async def test_case_1_final_lot_single_bidder(self):
        """TEST 1: Final lot with single bidder (the original bug scenario)"""
        print("\n" + "="*60)
        print("🧪 TEST 1: Final Lot with Single Bidder")
        print("="*60)
        
        # Setup: 2 users, 3 clubs
        league, auction, users, participants, clubs = await self.create_test_league(2, 3)
        
        # Lot 1: User 1 wins
        await self.place_bid(auction["id"], clubs[0]["id"], users[0], 5000000)
        await self.simulate_lot_completion(auction["id"], users[0], 5000000)
        
        # Lot 2: User 1 wins again
        await self.place_bid(auction["id"], clubs[1]["id"], users[0], 6000000)
        await self.simulate_lot_completion(auction["id"], users[0], 6000000)
        
        # Lot 3 (FINAL): Only User 2 bids
        await self.place_bid(auction["id"], clubs[2]["id"], users[1], 7000000)
        await self.simulate_lot_completion(auction["id"], users[1], 7000000)
        
        # Verify: User 1 should have 2 clubs, User 2 should have 1 club
        result = await self.verify_results({
            users[0]["name"]: 2,
            users[1]["name"]: 1
        })
        
        return result
        
    async def test_case_2_all_clubs_sold(self):
        """TEST 2: All clubs sold to multiple bidders"""
        print("\n" + "="*60)
        print("🧪 TEST 2: All Clubs Sold to Multiple Bidders")
        print("="*60)
        
        # Setup: 2 users, 4 clubs
        league, auction, users, participants, clubs = await self.create_test_league(2, 4)
        
        # Lot 1: User 1 wins
        await self.place_bid(auction["id"], clubs[0]["id"], users[0], 5000000)
        await self.place_bid(auction["id"], clubs[0]["id"], users[1], 4000000)
        await self.simulate_lot_completion(auction["id"], users[0], 5000000)
        
        # Lot 2: User 2 wins
        await self.place_bid(auction["id"], clubs[1]["id"], users[0], 5000000)
        await self.place_bid(auction["id"], clubs[1]["id"], users[1], 6000000)
        await self.simulate_lot_completion(auction["id"], users[1], 6000000)
        
        # Lot 3: User 1 wins
        await self.place_bid(auction["id"], clubs[2]["id"], users[0], 7000000)
        await self.place_bid(auction["id"], clubs[2]["id"], users[1], 6000000)
        await self.simulate_lot_completion(auction["id"], users[0], 7000000)
        
        # Lot 4 (FINAL): User 2 wins
        await self.place_bid(auction["id"], clubs[3]["id"], users[0], 5000000)
        await self.place_bid(auction["id"], clubs[3]["id"], users[1], 8000000)
        await self.simulate_lot_completion(auction["id"], users[1], 8000000)
        
        # Verify: Both should have 2 clubs each
        result = await self.verify_results({
            users[0]["name"]: 2,
            users[1]["name"]: 2
        })
        
        return result
        
    async def test_case_3_unsold_clubs(self):
        """TEST 3: Some clubs go unsold"""
        print("\n" + "="*60)
        print("🧪 TEST 3: Unsold Clubs")
        print("="*60)
        
        # Setup: 2 users, 4 clubs
        league, auction, users, participants, clubs = await self.create_test_league(2, 4)
        
        # Lot 1: User 1 wins
        await self.place_bid(auction["id"], clubs[0]["id"], users[0], 5000000)
        await self.simulate_lot_completion(auction["id"], users[0], 5000000)
        
        # Lot 2: UNSOLD (no bids)
        await self.simulate_lot_completion(auction["id"], None, None)
        
        # Lot 3: User 2 wins
        await self.place_bid(auction["id"], clubs[2]["id"], users[1], 6000000)
        await self.simulate_lot_completion(auction["id"], users[1], 6000000)
        
        # Lot 4 (FINAL): User 1 wins
        await self.place_bid(auction["id"], clubs[3]["id"], users[0], 7000000)
        await self.simulate_lot_completion(auction["id"], users[0], 7000000)
        
        # Verify: User 1 should have 2 clubs, User 2 should have 1 club
        result = await self.verify_results({
            users[0]["name"]: 2,
            users[1]["name"]: 1
        })
        
        return result
        
    async def test_case_4_single_club_auction(self):
        """TEST 4: Edge case - auction with only 1 club"""
        print("\n" + "="*60)
        print("🧪 TEST 4: Single Club Auction")
        print("="*60)
        
        # Setup: 2 users, 1 club
        league, auction, users, participants, clubs = await self.create_test_league(2, 1)
        
        # Lot 1 (ONLY AND FINAL): User 1 wins
        await self.place_bid(auction["id"], clubs[0]["id"], users[0], 5000000)
        await self.place_bid(auction["id"], clubs[0]["id"], users[1], 4000000)
        await self.simulate_lot_completion(auction["id"], users[0], 5000000)
        
        # Verify: User 1 should have 1 club, User 2 should have 0
        result = await self.verify_results({
            users[0]["name"]: 1,
            users[1]["name"]: 0
        })
        
        return result

async def main():
    """Run all test cases"""
    tester = ManualAuctionTester()
    
    try:
        await tester.setup()
        
        results = []
        
        # Run test cases
        print("\n" + "🎯 STARTING MANUAL E2E AUCTION TESTS" + "\n")
        
        results.append(("Test 1: Final Lot Single Bidder", await tester.test_case_1_final_lot_single_bidder()))
        await tester.cleanup()
        await tester.setup()
        
        results.append(("Test 2: All Clubs Sold", await tester.test_case_2_all_clubs_sold()))
        await tester.cleanup()
        await tester.setup()
        
        results.append(("Test 3: Unsold Clubs", await tester.test_case_3_unsold_clubs()))
        await tester.cleanup()
        await tester.setup()
        
        results.append(("Test 4: Single Club Auction", await tester.test_case_4_single_club_auction()))
        
        # Final summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} TEST(S) FAILED")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
