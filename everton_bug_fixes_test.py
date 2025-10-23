#!/usr/bin/env python3
"""
Everton Bug Fixes Testing - Comprehensive Backend Testing
Tests the specific bug fixes requested in the review:
1. Budget Reserve Enforcement (Bug 3) - £1m reserve per remaining roster slot
2. Auction Start Control (Bug 2) - waiting room and manual start functionality  
3. Roster Visibility (Bug 5) - enhanced summary endpoint with all managers' rosters
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://auction-buddy-8.preview.emergentagent.com/api"
SOCKET_URL = "https://auction-buddy-8.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class EvertonBugFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_client = None
        self.socket_events = []
        
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

    def setup_test_environment(self) -> bool:
        """Set up users, league, and basic auction environment"""
        self.log("=== Setting Up Test Environment ===")
        
        # Create commissioner user
        commissioner_data = {
            "name": "Commissioner Alice",
            "email": "alice.commissioner@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", commissioner_data)
        if "error" in result:
            self.log("Commissioner creation failed", "ERROR")
            return False
            
        self.test_data["commissioner_id"] = result.get("id")
        self.test_data["commissioner"] = result
        self.log(f"Created commissioner: {self.test_data['commissioner_id']}")
        
        # Create participant user
        participant_data = {
            "name": "Manager Bob",
            "email": "bob.manager@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", participant_data)
        if "error" in result:
            self.log("Participant creation failed", "ERROR")
            return False
            
        self.test_data["participant_id"] = result.get("id")
        self.test_data["participant"] = result
        self.log(f"Created participant: {self.test_data['participant_id']}")
        
        # Seed clubs if needed
        result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" in result:
            self.log("Club seeding failed", "ERROR")
            return False
        
        self.log("✅ Test environment setup complete")
        return True

    def test_budget_reserve_enforcement(self) -> bool:
        """
        Test Case 1: Budget Reserve Enforcement (Bug 3)
        Test the bid validation that enforces £1m reserve per remaining roster slot.
        """
        self.log("=== Testing Budget Reserve Enforcement (Bug 3) ===")
        
        # Create a league with 3 slots and £150m budget (adjusted to trigger reserve enforcement)
        league_data = {
            "name": "Budget Reserve Test League",
            "commissionerId": self.test_data["commissioner_id"],
            "budget": 150000000.0,  # £150m budget (adjusted for proper testing)
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3  # 3 slots total
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        invite_token = result.get("inviteToken")
        self.test_data["budget_league_id"] = league_id
        self.test_data["budget_invite_token"] = invite_token
        self.log(f"Created budget test league: {league_id}")
        
        # Commissioner joins league
        join_data = {
            "userId": self.test_data["commissioner_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Commissioner join failed", "ERROR")
            return False
        
        # Participant joins league
        join_data = {
            "userId": self.test_data["participant_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Participant join failed", "ERROR")
            return False
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
            
        auction_id = result.get("auctionId")
        self.test_data["budget_auction_id"] = auction_id
        self.log(f"Started budget test auction: {auction_id}")
        
        # Begin auction (commissioner starts it)
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/begin?commissionerId={self.test_data['commissioner_id']}")
        if "error" in result:
            self.log("Auction begin failed", "ERROR")
            return False
        
        self.log("Auction begun by commissioner")
        
        # Get current auction state
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction failed", "ERROR")
            return False
        
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No current club found", "ERROR")
            return False
        
        self.log(f"Current club: {current_club.get('name')}")
        
        # Test Scenario: User wins first team for £100m (budget: £50m remaining, slots: 1/3, remaining: 2 slots)
        self.log("Step 1: User wins first team for £100m...")
        
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 100000000.0  # £100m
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("First bid failed", "ERROR")
            return False
        
        # Complete the lot to win the team
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Complete first lot failed", "ERROR")
            return False
        
        self.log("✅ First team won for £100m")
        
        # Wait for next lot to start
        time.sleep(3)
        
        # Get updated auction state
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction after first lot failed", "ERROR")
            return False
        
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No current club found after first lot", "ERROR")
            return False
        
        self.log(f"Second club: {current_club.get('name')}")
        
        # Test: Try to bid £50m on next team → SHOULD BE REJECTED (must reserve £1m for last slot, max bid £49m)
        self.log("Step 2: Testing £50m bid (should be REJECTED - must reserve £1m for last slot)...")
        
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 50000000.0  # £50m - should be rejected
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data, expected_status=400)
        if "error" not in result and "detail" not in result:
            self.log("£150m bid should have been rejected but was accepted", "ERROR")
            return False
        
        # Check error message mentions budget reserve
        if result is None:
            self.log("Result is None when checking budget reserve error", "ERROR")
            return False
        
        error_detail = result.get("detail", result.get("text", ""))
        if error_detail and ("reserve" in error_detail.lower() or "remaining" in error_detail.lower()):
            self.log("✅ £50m bid correctly rejected (budget reserve enforcement)")
        else:
            self.log(f"Error message doesn't mention budget reserve: {error_detail}", "ERROR")
            return False
        
        self.log("✅ £150m bid correctly rejected (budget reserve enforcement)")
        
        # Test: Bid £49m and win (budget: £1m, slots: 2/3, remaining: 1 slot)
        self.log("Step 3: Bidding £49m (should be ACCEPTED)...")
        
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 49000000.0  # £49m - should be accepted
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log(f"£149m bid should have been accepted but was rejected: {result.get('text')}", "ERROR")
            return False
        
        # Complete the lot to win the team
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Complete second lot failed", "ERROR")
            return False
        
        self.log("✅ Second team won for £149m")
        
        # Wait for next lot to start
        time.sleep(3)
        
        # Get updated auction state
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction after second lot failed", "ERROR")
            return False
        
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No current club found after second lot", "ERROR")
            return False
        
        self.log(f"Third club: {current_club.get('name')}")
        
        # Test: Try to bid £52m on final team → SHOULD BE REJECTED (max bid £51m)
        self.log("Step 4: Testing £52m bid on final team (should be REJECTED - max bid £51m)...")
        
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 52000000.0  # £52m - should be rejected
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data, expected_status=400)
        if "error" not in result and "detail" not in result:
            self.log("£52m bid should have been rejected but was accepted", "ERROR")
            return False
        
        self.log("✅ £52m bid correctly rejected (insufficient budget)")
        
        # Test: Bid £51m and win (budget: £0, slots: 3/3)
        self.log("Step 5: Bidding £51m on final team (should be ACCEPTED)...")
        
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 51000000.0  # £51m - should be accepted
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log(f"£51m bid should have been accepted but was rejected: {result.get('text')}", "ERROR")
            return False
        
        # Complete the lot to win the team
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Complete third lot failed", "ERROR")
            return False
        
        self.log("✅ Third team won for £51m")
        
        # Verify auction completes successfully
        time.sleep(3)
        
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get final auction state failed", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        auction_status = auction_data.get("status")
        
        if auction_status == "completed":
            self.log("✅ Auction completed successfully")
        else:
            self.log(f"Auction not completed, status: {auction_status}", "ERROR")
            return False
        
        self.log("✅ Budget Reserve Enforcement (Bug 3) - ALL TESTS PASSED")
        return True

    def test_auction_start_control(self) -> bool:
        """
        Test Case 2: Auction Start Control (Bug 2)
        Test the waiting room and manual start functionality.
        """
        self.log("=== Testing Auction Start Control (Bug 2) ===")
        
        # Create a league for auction start testing
        league_data = {
            "name": "Auction Start Control Test League",
            "commissionerId": self.test_data["commissioner_id"],
            "budget": 500000000.0,  # £500m budget
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        invite_token = result.get("inviteToken")
        self.test_data["start_league_id"] = league_id
        self.test_data["start_invite_token"] = invite_token
        self.log(f"Created auction start test league: {league_id}")
        
        # Commissioner joins league
        join_data = {
            "userId": self.test_data["commissioner_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Commissioner join failed", "ERROR")
            return False
        
        # Participant joins league
        join_data = {
            "userId": self.test_data["participant_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Participant join failed", "ERROR")
            return False
        
        # Start auction → auction should be created with status "waiting"
        self.log("Step 1: Starting auction (should create with status 'waiting')...")
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
            
        auction_id = result.get("auctionId")
        auction_status = result.get("status")
        self.test_data["start_auction_id"] = auction_id
        
        if auction_status != "waiting":
            self.log(f"Expected auction status 'waiting', got '{auction_status}'", "ERROR")
            return False
        
        self.log("✅ Auction created with status 'waiting'")
        
        # Verify GET /auction/{auction_id} returns status "waiting"
        self.log("Step 2: Verifying auction status via GET endpoint...")
        
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction failed", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        if auction_data.get("status") != "waiting":
            self.log(f"Expected auction status 'waiting', got '{auction_data.get('status')}'", "ERROR")
            return False
        
        self.log("✅ GET /auction/{auction_id} returns status 'waiting'")
        
        # Non-commissioner should NOT be able to start auction (403)
        self.log("Step 3: Testing non-commissioner start (should return 403)...")
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/begin?commissionerId={self.test_data['participant_id']}", expected_status=403)
        
        if "error" not in result and "detail" not in result:
            self.log("Non-commissioner should not be able to start auction", "ERROR")
            return False
        
        error_detail = result.get("detail", result.get("text", ""))
        if "commissioner" not in error_detail.lower():
            self.log(f"Error message should mention commissioner: {error_detail}", "ERROR")
            return False
        
        self.log("✅ Non-commissioner correctly blocked from starting auction (403)")
        
        # Commissioner calls POST /auction/{auction_id}/begin → auction status changes to "active"
        self.log("Step 4: Commissioner starts auction (should change status to 'active')...")
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/begin?commissionerId={self.test_data['commissioner_id']}")
        
        if "error" in result:
            self.log(f"Commissioner should be able to start auction: {result.get('text')}", "ERROR")
            return False
        
        self.log("✅ Commissioner successfully started auction")
        
        # Verify first lot starts with timer countdown
        self.log("Step 5: Verifying first lot started with timer...")
        
        time.sleep(2)  # Wait for auction to fully start
        
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction after start failed", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        current_club = result.get("currentClub")
        
        if auction_data.get("status") != "active":
            self.log(f"Expected auction status 'active', got '{auction_data.get('status')}'", "ERROR")
            return False
        
        if not current_club:
            self.log("No current club found after auction start", "ERROR")
            return False
        
        if auction_data.get("currentLot", 0) < 1:
            self.log("Current lot should be at least 1", "ERROR")
            return False
        
        timer_ends_at = auction_data.get("timerEndsAt")
        if not timer_ends_at:
            self.log("No timer end time found", "ERROR")
            return False
        
        self.log(f"✅ First lot started: {current_club.get('name')}, Lot: {auction_data.get('currentLot')}")
        self.log("✅ Timer countdown active")
        
        self.log("✅ Auction Start Control (Bug 2) - ALL TESTS PASSED")
        return True

    def test_roster_visibility(self) -> bool:
        """
        Test Case 3: Roster Visibility (Bug 5)
        Test enhanced summary endpoint that returns all managers' rosters.
        """
        self.log("=== Testing Roster Visibility (Bug 5) ===")
        
        # Create a league with multiple participants
        league_data = {
            "name": "Roster Visibility Test League",
            "commissionerId": self.test_data["commissioner_id"],
            "budget": 500000000.0,  # £500m budget
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 2  # 2 slots for faster testing
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        invite_token = result.get("inviteToken")
        self.test_data["roster_league_id"] = league_id
        self.test_data["roster_invite_token"] = invite_token
        self.log(f"Created roster visibility test league: {league_id}")
        
        # Create additional participant for multiple managers
        participant2_data = {
            "name": "Manager Charlie",
            "email": "charlie.manager@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", participant2_data)
        if "error" in result:
            self.log("Second participant creation failed", "ERROR")
            return False
            
        participant2_id = result.get("id")
        self.test_data["participant2_id"] = participant2_id
        self.log(f"Created second participant: {participant2_id}")
        
        # All users join league
        for user_id in [self.test_data["commissioner_id"], self.test_data["participant_id"], participant2_id]:
            join_data = {
                "userId": user_id,
                "inviteToken": invite_token
            }
            
            result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
            if "error" in result:
                self.log(f"User {user_id} join failed", "ERROR")
                return False
        
        self.log("All participants joined league")
        
        # Start and begin auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
            
        auction_id = result.get("auctionId")
        self.test_data["roster_auction_id"] = auction_id
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/begin?commissionerId={self.test_data['commissioner_id']}")
        if "error" in result:
            self.log("Auction begin failed", "ERROR")
            return False
        
        self.log("Auction started for roster testing")
        
        # Run auction where different managers win teams
        self.log("Step 1: Running auction with different winners...")
        
        # Get first club
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction failed", "ERROR")
            return False
        
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No current club found", "ERROR")
            return False
        
        # Commissioner wins first team
        bid_data = {
            "userId": self.test_data["commissioner_id"],
            "clubId": current_club["id"],
            "amount": 100000000.0  # £100m
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Commissioner bid failed", "ERROR")
            return False
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Complete first lot failed", "ERROR")
            return False
        
        self.log(f"Commissioner won: {current_club.get('name')}")
        
        # Wait for next lot
        time.sleep(3)
        
        # Get second club
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction for second lot failed", "ERROR")
            return False
        
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No second club found", "ERROR")
            return False
        
        # Participant wins second team
        bid_data = {
            "userId": self.test_data["participant_id"],
            "clubId": current_club["id"],
            "amount": 150000000.0  # £150m
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Participant bid failed", "ERROR")
            return False
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Complete second lot failed", "ERROR")
            return False
        
        self.log(f"Participant won: {current_club.get('name')}")
        
        # Wait for auction to complete or stabilize
        time.sleep(3)
        
        # Test GET /leagues/{league_id}/summary?userId={userId}
        self.log("Step 2: Testing enhanced summary endpoint...")
        
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/summary?userId={self.test_data['commissioner_id']}")
        if "error" in result:
            self.log("Get league summary failed", "ERROR")
            return False
        
        # Verify response includes yourRoster (requesting user's roster with team names and prices)
        your_roster = result.get("yourRoster")
        if not isinstance(your_roster, list):
            self.log("yourRoster should be a list", "ERROR")
            return False
        
        if len(your_roster) > 0:
            roster_item = your_roster[0]
            required_fields = ["id", "name", "price"]
            for field in required_fields:
                if field not in roster_item:
                    self.log(f"yourRoster item missing field: {field}", "ERROR")
                    return False
            
            self.log(f"✅ yourRoster includes team: {roster_item.get('name')} for £{roster_item.get('price'):,.0f}")
        
        # Verify response includes managers array
        managers = result.get("managers")
        if not isinstance(managers, list):
            self.log("managers should be a list", "ERROR")
            return False
        
        if len(managers) < 2:
            self.log("Should have at least 2 managers", "ERROR")
            return False
        
        # Verify EACH manager object includes required fields
        self.log("Step 3: Verifying manager roster data...")
        
        for manager in managers:
            # Check manager has id, name
            if "id" not in manager or "name" not in manager:
                self.log("Manager missing id or name", "ERROR")
                return False
            
            # Check manager has roster (array of teams with id, name, price)
            roster = manager.get("roster")
            if not isinstance(roster, list):
                self.log(f"Manager {manager.get('name')} roster should be a list", "ERROR")
                return False
            
            # Check manager has budgetRemaining
            if "budgetRemaining" not in manager:
                self.log(f"Manager {manager.get('name')} missing budgetRemaining", "ERROR")
                return False
            
            # If manager has teams, verify roster structure
            if len(roster) > 0:
                roster_item = roster[0]
                required_fields = ["id", "name", "price"]
                for field in required_fields:
                    if field not in roster_item:
                        self.log(f"Manager {manager.get('name')} roster item missing field: {field}", "ERROR")
                        return False
                
                self.log(f"✅ Manager {manager.get('name')} roster: {roster_item.get('name')} for £{roster_item.get('price'):,.0f}")
            
            self.log(f"✅ Manager {manager.get('name')} budget remaining: £{manager.get('budgetRemaining'):,.0f}")
        
        # Verify all managers' rosters are populated correctly
        managers_with_teams = [m for m in managers if len(m.get("roster", [])) > 0]
        if len(managers_with_teams) < 2:
            self.log("Expected at least 2 managers to have teams", "ERROR")
            return False
        
        self.log("✅ All managers' rosters populated correctly")
        
        # Test with different user to ensure consistent data
        self.log("Step 4: Testing summary from different user perspective...")
        
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/summary?userId={self.test_data['participant_id']}")
        if "error" in result:
            self.log("Get league summary from participant failed", "ERROR")
            return False
        
        # Verify same managers data is returned
        participant_managers = result.get("managers", [])
        if len(participant_managers) != len(managers):
            self.log("Manager count should be consistent across users", "ERROR")
            return False
        
        # Verify yourRoster is different for different user
        participant_roster = result.get("yourRoster", [])
        commissioner_roster = your_roster
        
        # If both have teams, they should be different
        if len(participant_roster) > 0 and len(commissioner_roster) > 0:
            if participant_roster[0].get("id") == commissioner_roster[0].get("id"):
                self.log("Different users should have different rosters", "ERROR")
                return False
        
        self.log("✅ Summary endpoint returns correct data for different users")
        
        self.log("✅ Roster Visibility (Bug 5) - ALL TESTS PASSED")
        return True

    def cleanup(self):
        """Clean up test data and connections"""
        self.log("=== Cleaning Up ===")
        
        # Disconnect socket if connected
        if self.socket_client and self.socket_client.connected:
            self.socket_client.disconnect()
        
        # Delete test leagues if created
        leagues_to_delete = [
            ("budget_league_id", "commissioner_id"),
            ("start_league_id", "commissioner_id"),
            ("roster_league_id", "commissioner_id")
        ]
        
        for league_key, user_key in leagues_to_delete:
            if league_key in self.test_data and user_key in self.test_data:
                result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data[league_key]}?user_id={self.test_data[user_key]}")
                if "error" not in result:
                    self.log(f"Deleted test league: {league_key}")

    def run_everton_bug_tests(self) -> Dict[str, bool]:
        """Run all Everton bug fix tests"""
        self.log("🚀 Starting Everton Bug Fixes Tests")
        
        results = {}
        
        # Test basic API connectivity
        root_result = self.test_api_endpoint("GET", "/")
        if "error" in root_result:
            self.log("❌ API not accessible", "ERROR")
            return {"api_connectivity": False}
        
        self.log("✅ API connectivity working")
        results["api_connectivity"] = True
        
        # Setup test environment
        if not self.setup_test_environment():
            self.log("❌ Test environment setup failed", "ERROR")
            return {"setup": False}
        
        results["setup"] = True
        
        # Run Everton bug fix tests
        test_suites = [
            ("budget_reserve_enforcement", self.test_budget_reserve_enforcement),
            ("auction_start_control", self.test_auction_start_control),
            ("roster_visibility", self.test_roster_visibility),
        ]
        
        for test_name, test_func in test_suites:
            try:
                results[test_name] = test_func()
                if not results[test_name]:
                    self.log(f"❌ {test_name} failed", "ERROR")
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
    tester = EvertonBugFixesTester()
    results = tester.run_everton_bug_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("EVERTON BUG FIXES TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Everton bug fix tests passed!")
        return True
    else:
        print("⚠️  Some Everton bug fix tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)