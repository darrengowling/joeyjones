#!/usr/bin/env python3
"""
Waiting Room + Auction Flow Test
Tests the complete waiting room coordination and auction flow as requested in review.

Scenario: 2 users, 4 team slots, waiting room coordination
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://auction-room-wizard.preview.emergentagent.com/api"
SOCKET_URL = "https://auction-room-wizard.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class WaitingRoomAuctionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_clients = {}  # Multiple clients for multi-user testing
        self.socket_events = {}   # Events per client
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> dict:
        """Test API endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                self.log(f"Expected {expected_status}, got {response.status_code}: {response.text}", "ERROR")
                return {"error": f"Status {response.status_code}", "text": response.text, "detail": response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}

    def setup_test_users(self) -> bool:
        """Setup: Create 2 test users (User1 = commissioner, User2 = participant)"""
        self.log("=== SETUP: Creating 2 Test Users ===")
        
        # Create User1 (Commissioner)
        user1_data = {
            "name": "Commissioner Alice",
            "email": "alice.commissioner@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user1_data)
        if "error" in result:
            self.log("User1 creation failed", "ERROR")
            return False
            
        user1_id = result.get("id")
        if not user1_id:
            self.log("No user1 ID returned", "ERROR")
            return False
            
        self.test_data["user1_id"] = user1_id
        self.test_data["user1"] = result
        self.log(f"✅ Created User1 (Commissioner): {user1_id}")
        
        # Create User2 (Participant)
        user2_data = {
            "name": "Manager Bob",
            "email": "bob.manager@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user2_data)
        if "error" in result:
            self.log("User2 creation failed", "ERROR")
            return False
            
        user2_id = result.get("id")
        if not user2_id:
            self.log("No user2 ID returned", "ERROR")
            return False
            
        self.test_data["user2_id"] = user2_id
        self.test_data["user2"] = result
        self.log(f"✅ Created User2 (Participant): {user2_id}")
        
        return True

    def setup_league_and_join(self) -> bool:
        """Setup: Create league with 2 managers, 4 slots each, £200m budget, football + User2 joins"""
        self.log("=== SETUP: Creating League and User2 Joins ===")
        
        if "user1_id" not in self.test_data or "user2_id" not in self.test_data:
            self.log("Users not created", "ERROR")
            return False
        
        # Create league with specified parameters
        league_data = {
            "name": "Waiting Room Test League",
            "commissionerId": self.test_data["user1_id"],
            "budget": 200000000.0,  # £200m budget
            "minManagers": 2,
            "maxManagers": 2,  # Exactly 2 managers
            "clubSlots": 4,    # 4 slots each
            "sportKey": "football"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        invite_token = result.get("inviteToken")
        if not league_id or not invite_token:
            self.log("No league ID or invite token returned", "ERROR")
            return False
            
        self.test_data["league_id"] = league_id
        self.test_data["invite_token"] = invite_token
        self.log(f"✅ Created league: {league_id} (2 managers, 4 slots, £200M budget)")
        
        # User1 (Commissioner) joins league
        join_data1 = {
            "userId": self.test_data["user1_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data1)
        if "error" in result:
            self.log("User1 join league failed", "ERROR")
            return False
        
        self.log("✅ User1 (Commissioner) joined league")
        
        # User2 joins league
        join_data2 = {
            "userId": self.test_data["user2_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data2)
        if "error" in result:
            self.log("User2 join league failed", "ERROR")
            return False
        
        self.log("✅ User2 (Participant) joined league")
        
        # Verify both participants are in league
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/participants")
        if "error" in result:
            self.log("Get participants failed", "ERROR")
            return False
        
        participants = result
        if len(participants) != 2:
            self.log(f"Expected 2 participants, got {len(participants)}", "ERROR")
            return False
        
        # Verify budgets are set correctly
        for participant in participants:
            if participant.get("budgetRemaining") != 200000000.0:
                self.log(f"Participant budget incorrect: {participant.get('budgetRemaining')}", "ERROR")
                return False
        
        self.log("✅ Both users in league with correct £200M budgets")
        return True

    def test_auction_creation_waiting_room(self) -> bool:
        """Test: User1 calls POST /leagues/{league_id}/start-auction - should create auction with status="waiting" """
        self.log("=== TEST: Auction Creation (Waiting Room) ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # Seed clubs first
        seed_result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" in seed_result:
            self.log("Club seeding failed", "ERROR")
            return False
        
        # User1 (Commissioner) starts auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
        
        auction_id = result.get("auctionId")
        status = result.get("status")
        
        if not auction_id:
            self.log("No auction ID returned", "ERROR")
            return False
        
        self.test_data["auction_id"] = auction_id
        
        # Verify auction created with status="waiting"
        if status != "waiting":
            self.log(f"Expected status 'waiting', got '{status}'", "ERROR")
            return False
        
        self.log("✅ Auction created with status='waiting'")
        
        # Get auction details to verify setup
        auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_result:
            self.log("Get auction details failed", "ERROR")
            return False
        
        auction_data = auction_result.get("auction", {})
        
        # Verify clubQueue populated
        club_queue = auction_data.get("clubQueue", [])
        if not club_queue or len(club_queue) == 0:
            self.log("clubQueue not populated", "ERROR")
            return False
        
        self.log(f"✅ clubQueue populated with {len(club_queue)} teams")
        
        # Verify currentLot = 0 (not started)
        current_lot = auction_data.get("currentLot", -1)
        if current_lot != 0:
            self.log(f"Expected currentLot=0, got {current_lot}", "ERROR")
            return False
        
        self.log("✅ currentLot = 0 (not started)")
        
        # Verify auction status is "waiting"
        auction_status = auction_data.get("status")
        if auction_status != "waiting":
            self.log(f"Auction status should be 'waiting', got '{auction_status}'", "ERROR")
            return False
        
        self.log("✅ Auction status confirmed as 'waiting'")
        
        return True

    def test_auction_begin_commissioner_starts(self) -> bool:
        """Test: User1 calls POST /auction/{auction_id}/begin - should change status to "active" """
        self.log("=== TEST: Auction Begin (Commissioner Starts) ===")
        
        if "auction_id" not in self.test_data or "user1_id" not in self.test_data:
            self.log("No auction or user1 available", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user1_id = self.test_data["user1_id"]
        
        # User1 (Commissioner) begins auction
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/begin?commissionerId={user1_id}")
        if "error" in result:
            self.log("Auction begin failed", "ERROR")
            return False
        
        self.log("✅ Commissioner successfully started auction")
        
        # Verify auction status changed to "active"
        auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_result:
            self.log("Get auction details after begin failed", "ERROR")
            return False
        
        auction_data = auction_result.get("auction", {})
        
        # Check status is now "active"
        auction_status = auction_data.get("status")
        if auction_status != "active":
            self.log(f"Expected status 'active', got '{auction_status}'", "ERROR")
            return False
        
        self.log("✅ Auction status changed to 'active'")
        
        # Verify currentLot = 1
        current_lot = auction_data.get("currentLot", 0)
        if current_lot != 1:
            self.log(f"Expected currentLot=1, got {current_lot}", "ERROR")
            return False
        
        self.log("✅ currentLot = 1")
        
        # Verify first team is set as currentClubId
        current_club_id = auction_data.get("currentClubId")
        if not current_club_id:
            self.log("No currentClubId set", "ERROR")
            return False
        
        self.log("✅ First team set as currentClubId")
        
        # Verify timer is running (timerEndsAt should be set)
        timer_ends_at = auction_data.get("timerEndsAt")
        if not timer_ends_at:
            self.log("Timer not running (no timerEndsAt)", "ERROR")
            return False
        
        self.log("✅ Timer is running")
        
        return True

    def test_non_commissioner_begin_403(self) -> bool:
        """Test: User2 (non-commissioner) tries to begin auction - should get 403"""
        self.log("=== TEST: Non-Commissioner Begin Attempt (Should Get 403) ===")
        
        if "auction_id" not in self.test_data or "user2_id" not in self.test_data:
            self.log("No auction or user2 available", "ERROR")
            return False
        
        # First, create a new auction in waiting state for this test
        # (since we already started the previous one)
        
        # Create a new league for this test
        league_data = {
            "name": "403 Test League",
            "commissionerId": self.test_data["user1_id"],
            "budget": 200000000.0,
            "minManagers": 2,
            "maxManagers": 2,
            "clubSlots": 4,
            "sportKey": "football"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Test league creation failed", "ERROR")
            return False
        
        test_league_id = result.get("id")
        
        # Start auction to get it in waiting state
        result = self.test_api_endpoint("POST", f"/leagues/{test_league_id}/auction/start")
        if "error" in result:
            self.log("Test auction start failed", "ERROR")
            return False
        
        test_auction_id = result.get("auctionId")
        
        # User2 (non-commissioner) tries to begin auction
        user2_id = self.test_data["user2_id"]
        result = self.test_api_endpoint("POST", f"/auction/{test_auction_id}/begin?commissionerId={user2_id}", expected_status=403)
        
        # Should get 403 error
        if "error" not in result and "detail" not in result:
            self.log("Expected 403 error but request succeeded", "ERROR")
            return False
        
        # Check error message
        error_detail = result.get("detail", result.get("text", ""))
        if "commissioner" not in error_detail.lower():
            self.log(f"Error message should mention commissioner: {error_detail}", "ERROR")
            return False
        
        self.log("✅ Non-commissioner correctly gets 403 error")
        
        # Clean up test league
        self.test_api_endpoint("DELETE", f"/leagues/{test_league_id}")
        
        return True

    def test_auction_flow_8_teams(self) -> bool:
        """Test: Run through auction with 8 teams total, 4 per user, verify budget deductions and reserve enforcement"""
        self.log("=== TEST: Auction Flow (8 teams total, 4 per user) ===")
        
        if "auction_id" not in self.test_data:
            self.log("No active auction available", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user1_id = self.test_data["user1_id"]
        user2_id = self.test_data["user2_id"]
        
        # Track teams won by each user
        user1_teams = []
        user2_teams = []
        
        # Simulate 8 rounds of bidding (4 teams each)
        for round_num in range(1, 9):
            self.log(f"--- Round {round_num} ---")
            
            # Get current auction state
            auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
            if "error" in auction_result:
                self.log(f"Failed to get auction state in round {round_num}", "ERROR")
                return False
            
            auction_data = auction_result.get("auction", {})
            current_club_id = auction_data.get("currentClubId")
            
            if not current_club_id:
                self.log(f"No current club in round {round_num}", "ERROR")
                return False
            
            # Get current club details
            current_club = auction_result.get("currentClub")
            if current_club is None:
                current_club = {}
            club_name = current_club.get("name", "Unknown")
            
            self.log(f"Current club: {club_name}")
            
            # Alternate winners: User1 gets odd rounds, User2 gets even rounds
            if round_num % 2 == 1:
                # User1 wins this round
                winning_user = user1_id
                winning_user_name = "User1"
                user1_teams.append(club_name)
            else:
                # User2 wins this round
                winning_user = user2_id
                winning_user_name = "User2"
                user2_teams.append(club_name)
            
            # Calculate bid amount (start at £10M, increase by £5M each round)
            bid_amount = 10000000.0 + (round_num - 1) * 5000000.0
            
            # Check budget reserve enforcement before bidding
            # Get participant budget
            participants_result = self.test_api_endpoint("GET", f"/leagues/{self.test_data['league_id']}/participants")
            if "error" in participants_result:
                self.log("Failed to get participants", "ERROR")
                return False
            
            winning_participant = None
            for p in participants_result:
                if p.get("userId") == winning_user:
                    winning_participant = p
                    break
            
            if not winning_participant:
                self.log(f"Winning participant not found", "ERROR")
                return False
            
            current_budget = winning_participant.get("budgetRemaining", 0)
            teams_won_so_far = len(winning_participant.get("clubsWon", []))
            remaining_slots = 4 - teams_won_so_far
            
            # Budget reserve: £1m per remaining slot
            max_bid = current_budget - (remaining_slots - 1) * 1000000.0  # -1 because we're bidding on current slot
            
            self.log(f"{winning_user_name} budget: £{current_budget/1000000:.1f}M, remaining slots: {remaining_slots}, max bid: £{max_bid/1000000:.1f}M")
            
            # Ensure bid doesn't exceed budget reserve
            if bid_amount > max_bid:
                bid_amount = max_bid - 1000000.0  # Leave some margin
                self.log(f"Adjusted bid to respect budget reserve: £{bid_amount/1000000:.1f}M")
            
            # Place winning bid
            bid_data = {
                "userId": winning_user,
                "clubId": current_club_id,
                "amount": bid_amount
            }
            
            bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in bid_result:
                self.log(f"Bid failed in round {round_num}: {bid_result.get('text', '')}", "ERROR")
                return False
            
            self.log(f"✅ {winning_user_name} bid £{bid_amount/1000000:.1f}M for {club_name}")
            
            # Complete the lot to move to next
            complete_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
            if "error" in complete_result:
                self.log(f"Lot completion failed in round {round_num}", "ERROR")
                return False
            
            self.log(f"✅ Lot {round_num} completed")
            
            # Wait for next lot to start (except on last round)
            if round_num < 8:
                time.sleep(2)
        
        # Verify final distribution
        if len(user1_teams) != 4:
            self.log(f"User1 should have 4 teams, got {len(user1_teams)}", "ERROR")
            return False
        
        if len(user2_teams) != 4:
            self.log(f"User2 should have 4 teams, got {len(user2_teams)}", "ERROR")
            return False
        
        self.log(f"✅ User1 teams: {user1_teams}")
        self.log(f"✅ User2 teams: {user2_teams}")
        self.log("✅ Auction flow completed - 4 teams per user")
        
        return True

    def test_budget_reserve_enforcement(self) -> bool:
        """Test: Verify budget reserve enforcement (£1m per remaining slot)"""
        self.log("=== TEST: Budget Reserve Enforcement ===")
        
        # Create a separate test to verify budget reserve logic
        # This will test the edge case where a user tries to bid more than allowed
        
        # Create new league and auction for this test
        league_data = {
            "name": "Budget Reserve Test League",
            "commissionerId": self.test_data["user1_id"],
            "budget": 10000000.0,  # £10M budget (small for testing)
            "minManagers": 2,
            "maxManagers": 2,
            "clubSlots": 3,  # 3 slots
            "sportKey": "football"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Budget test league creation failed", "ERROR")
            return False
        
        test_league_id = result.get("id")
        invite_token = result.get("inviteToken")
        
        # Join league
        join_data = {
            "userId": self.test_data["user1_id"],
            "inviteToken": invite_token
        }
        self.test_api_endpoint("POST", f"/leagues/{test_league_id}/join", join_data)
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{test_league_id}/auction/start")
        if "error" in result:
            self.log("Budget test auction start failed", "ERROR")
            return False
        
        test_auction_id = result.get("auctionId")
        
        # Begin auction
        result = self.test_api_endpoint("POST", f"/auction/{test_auction_id}/begin?commissionerId={self.test_data['user1_id']}")
        if "error" in result:
            self.log("Budget test auction begin failed", "ERROR")
            return False
        
        # Get auction state
        auction_result = self.test_api_endpoint("GET", f"/auction/{test_auction_id}")
        if "error" in auction_result:
            self.log("Failed to get budget test auction state", "ERROR")
            return False
        
        current_club_id = auction_result.get("auction", {}).get("currentClubId")
        
        # Try to bid £9M (should fail because user needs £1M reserve for each of 2 remaining slots after this one)
        # With £10M budget and 3 slots, max bid on first slot should be £10M - 2*£1M = £8M
        high_bid_data = {
            "userId": self.test_data["user1_id"],
            "clubId": current_club_id,
            "amount": 9000000.0  # £9M - should exceed budget reserve
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{test_auction_id}/bid", high_bid_data, expected_status=400)
        
        # Should get error about budget reserve
        if "error" not in result and "detail" not in result:
            self.log("Expected budget reserve error but bid was accepted", "ERROR")
            return False
        
        error_detail = result.get("detail", result.get("text", ""))
        if "reserve" not in error_detail.lower() and "remaining" not in error_detail.lower():
            self.log(f"Error should mention reserve/remaining: {error_detail}", "ERROR")
            return False
        
        self.log("✅ Budget reserve enforcement working - high bid rejected")
        
        # Try valid bid (£7M should work)
        valid_bid_data = {
            "userId": self.test_data["user1_id"],
            "clubId": current_club_id,
            "amount": 7000000.0  # £7M - should be within budget reserve
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{test_auction_id}/bid", valid_bid_data)
        if "error" in result:
            self.log(f"Valid bid within budget reserve was rejected: {result.get('text', '')}", "ERROR")
            return False
        
        self.log("✅ Budget reserve enforcement working - valid bid accepted")
        
        # Clean up
        self.test_api_endpoint("DELETE", f"/leagues/{test_league_id}")
        
        return True

    def test_auction_completion(self) -> bool:
        """Test: After 8th team sold, verify auction completes with correct final state"""
        self.log("=== TEST: Auction Completion ===")
        
        if "auction_id" not in self.test_data:
            self.log("No auction available for completion test", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        league_id = self.test_data["league_id"]
        
        # Get final auction state
        auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_result:
            self.log("Failed to get final auction state", "ERROR")
            return False
        
        auction_data = auction_result.get("auction", {})
        
        # Verify auction status = "completed"
        auction_status = auction_data.get("status")
        if auction_status != "completed":
            self.log(f"Expected auction status 'completed', got '{auction_status}'", "ERROR")
            return False
        
        self.log("✅ Auction status = 'completed'")
        
        # Get participants to verify final state
        participants_result = self.test_api_endpoint("GET", f"/leagues/{league_id}/participants")
        if "error" in participants_result:
            self.log("Failed to get final participants", "ERROR")
            return False
        
        participants = participants_result
        
        # Verify both users have 4 teams in clubsWon
        for participant in participants:
            clubs_won = participant.get("clubsWon", [])
            if len(clubs_won) != 4:
                self.log(f"Participant {participant.get('userName')} has {len(clubs_won)} teams, expected 4", "ERROR")
                return False
        
        self.log("✅ Both users have 4 teams in clubsWon")
        
        # Verify budget deductions happened
        for participant in participants:
            budget_remaining = participant.get("budgetRemaining", 0)
            total_spent = participant.get("totalSpent", 0)
            
            if budget_remaining + total_spent != 200000000.0:  # Original £200M budget
                self.log(f"Budget math doesn't add up for {participant.get('userName')}: remaining={budget_remaining}, spent={total_spent}", "ERROR")
                return False
            
            if total_spent == 0:
                self.log(f"No spending recorded for {participant.get('userName')}", "ERROR")
                return False
        
        self.log("✅ Budget deductions recorded correctly")
        
        # Verify final team is recorded (check that 8 teams total were sold)
        clubs_result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
        if "error" in clubs_result:
            self.log("Failed to get final clubs state", "ERROR")
            return False
        
        clubs_data = clubs_result.get("clubs", [])
        sold_clubs = [c for c in clubs_data if c.get("status") == "sold"]
        
        if len(sold_clubs) != 8:
            self.log(f"Expected 8 sold clubs, got {len(sold_clubs)}", "ERROR")
            return False
        
        self.log("✅ All 8 teams distributed correctly")
        
        # Verify each sold club has winner and winning bid
        for club in sold_clubs:
            if not club.get("winner") or not club.get("winningBid"):
                self.log(f"Sold club {club.get('name')} missing winner or winning bid info", "ERROR")
                return False
        
        self.log("✅ All sold clubs have winner and winning bid information")
        
        return True

    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Delete test league if created
        if "league_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}")
            if "error" not in result:
                self.log("Test league deleted")

    def run_waiting_room_auction_test(self) -> Dict[str, bool]:
        """Run the complete waiting room + auction flow test"""
        self.log("🚀 Starting Waiting Room + Auction Flow Test")
        self.log("Scenario: 2 users, 4 team slots, waiting room coordination")
        
        results = {}
        
        # Test API connectivity first
        root_result = self.test_api_endpoint("GET", "/")
        if "error" in root_result:
            self.log("❌ API not accessible", "ERROR")
            return {"api_connectivity": False}
        
        self.log("✅ API connectivity working")
        results["api_connectivity"] = True
        
        # Run test sequence
        test_sequence = [
            ("setup_users", self.setup_test_users),
            ("setup_league_and_join", self.setup_league_and_join),
            ("auction_creation_waiting_room", self.test_auction_creation_waiting_room),
            ("auction_begin_commissioner", self.test_auction_begin_commissioner_starts),
            ("non_commissioner_403", self.test_non_commissioner_begin_403),
            ("auction_flow_8_teams", self.test_auction_flow_8_teams),
            ("budget_reserve_enforcement", self.test_budget_reserve_enforcement),
            ("auction_completion", self.test_auction_completion),
        ]
        
        for test_name, test_func in test_sequence:
            try:
                self.log(f"\n--- Running {test_name} ---")
                results[test_name] = test_func()
                if not results[test_name]:
                    self.log(f"❌ {test_name} failed", "ERROR")
                    # Continue with remaining tests even if one fails
                else:
                    self.log(f"✅ {test_name} passed")
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = WaitingRoomAuctionTester()
    results = tester.run_waiting_room_auction_test()
    
    # Print summary
    print("\n" + "="*60)
    print("WAITING ROOM + AUCTION FLOW TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All waiting room + auction flow tests passed!")
        print("\n✅ CRITICAL CHECKS VERIFIED:")
        print("  - Waiting room: Auction starts with status='waiting', not 'active'")
        print("  - Begin auction: Only commissioner can call /begin endpoint")
        print("  - Non-commissioner gets 403 if they try to begin")
        print("  - Budget reserve: Users cannot bid more than (budget - remaining_slots * £1m)")
        print("  - Completion: All 8 teams distributed correctly")
        return True
    else:
        print("⚠️  Some waiting room + auction flow tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)