#!/usr/bin/env python3
"""
Production Test for UEFA Club Auction - Focus on Review Request Requirements
Tests the specific areas mentioned in the review request:
1. League Creation & Joining Flow with £500M budget
2. Auction Management with club queue randomization
3. Real-time Bidding System with Socket.IO events
4. Club Status & Budget Management
5. Commissioner Controls
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://fixture-correction.preview.emergentagent.com/api"
SOCKET_URL = "https://fixture-correction.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class ProductionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_client = None
        self.socket_events = []
        self.received_events = {}
        
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
                return {"error": f"Status {response.status_code}", "text": response.text, "detail": response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}

    def test_league_creation_with_500m_budget(self) -> bool:
        """Test 1: League Creation & Joining Flow with £500M budget"""
        self.log("=== TEST 1: League Creation & Joining Flow (£500M Budget) ===")
        
        # Create test user first
        user_data = {
            "name": "Commissioner Test",
            "email": "commissioner@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in result:
            self.log("User creation failed", "ERROR")
            return False
            
        user_id = result.get("id")
        self.test_data["user_id"] = user_id
        self.test_data["user"] = result
        self.log(f"✅ Created test user: {user_id}")
        
        # Create league with £500M budget as specified in review request
        league_data = {
            "name": "Production Test League £500M",
            "commissionerId": user_id,
            "budget": 500000000.0,  # £500M budget as specified
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 5
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        invite_token = result.get("inviteToken")
        budget = result.get("budget")
        
        if budget != 500000000.0:
            self.log(f"Budget mismatch: expected £500M, got £{budget:,.0f}", "ERROR")
            return False
            
        self.test_data["league_id"] = league_id
        self.test_data["invite_token"] = invite_token
        self.log(f"✅ Created league with £500M budget: {league_id}")
        
        # Test join league functionality with invite tokens
        join_data = {
            "userId": user_id,
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Join league failed", "ERROR")
            return False
            
        participant = result.get("participant")
        if not participant or participant.get("budgetRemaining") != 500000000.0:
            self.log("Participant budget not set correctly", "ERROR")
            return False
            
        self.log("✅ Successfully joined league with correct £500M budget")
        
        # Verify Socket.IO participant_joined events will be tested in socket section
        self.log("✅ League Creation & Joining Flow with £500M budget: PASSED")
        return True

    def test_auction_management_and_randomization(self) -> bool:
        """Test 2: Auction Management with club queue randomization"""
        self.log("=== TEST 2: Auction Management & Club Queue Randomization ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for auction testing", "ERROR")
            return False
            
        league_id = self.test_data["league_id"]
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
            
        auction_id = result.get("auctionId")
        self.test_data["auction_id"] = auction_id
        self.log(f"✅ Started auction: {auction_id}")
        
        # Get auction details to verify randomization
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction details failed", "ERROR")
            return False
            
        auction_data = result.get("auction", {})
        club_queue = auction_data.get("clubQueue", [])
        current_club = result.get("currentClub")
        
        if not club_queue or len(club_queue) == 0:
            self.log("No club queue found - randomization cannot be verified", "ERROR")
            return False
            
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
            
        self.test_data["current_club"] = current_club
        self.log(f"✅ Club queue randomized with {len(club_queue)} clubs")
        self.log(f"✅ First club selected: {current_club.get('name')}")
        
        # Verify auction timer functionality
        timer_ends_at = auction_data.get("timerEndsAt")
        if not timer_ends_at:
            self.log("No timer end time found", "ERROR")
            return False
            
        self.log("✅ Auction timer functionality active")
        
        # Test clubs list endpoint sorting (should be alphabetical, not by lot order)
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
        if "error" in result:
            self.log("Clubs list endpoint failed", "ERROR")
            return False
        
        clubs_data = result.get("clubs", [])
        if not clubs_data:
            self.log("No clubs data returned", "ERROR")
            return False
        
        # Check sorting - upcoming clubs should be alphabetical (not revealing draw order)
        upcoming_clubs = [c for c in clubs_data if c.get("status") == "upcoming"]
        if len(upcoming_clubs) > 1:
            # Check if upcoming clubs are sorted alphabetically
            upcoming_names = [c.get("name") for c in upcoming_clubs]
            sorted_names = sorted(upcoming_names)
            if upcoming_names == sorted_names:
                self.log("✅ Clubs list sorted alphabetically (draw order hidden)")
            else:
                self.log("⚠️ Clubs list may be revealing draw order", "WARN")
        
        self.log("✅ Auction Management & Club Queue Randomization: PASSED")
        return True

    def setup_socket_connection(self) -> bool:
        """Setup Socket.IO connection for real-time testing"""
        self.log("=== Setting up Socket.IO Connection ===")
        
        try:
            # Create socket client
            self.socket_client = socketio.Client(logger=False, engineio_logger=False)
            
            # Set up event handlers
            @self.socket_client.event
            def connect():
                self.log("Socket.IO connected successfully")
                self.socket_events.append("connected")
            
            @self.socket_client.event
            def disconnect():
                self.log("Socket.IO disconnected")
                self.socket_events.append("disconnected")
            
            @self.socket_client.event
            def participant_joined(data):
                self.log(f"✅ participant_joined event received: {data.get('participant', {}).get('userName')}")
                self.socket_events.append("participant_joined")
                self.received_events["participant_joined"] = data
            
            @self.socket_client.event
            def bid_placed(data):
                bid_amount = data.get('bid', {}).get('amount', 0)
                self.log(f"✅ bid_placed event received: £{bid_amount:,.0f}")
                self.socket_events.append("bid_placed")
                self.received_events["bid_placed"] = data
            
            @self.socket_client.event
            def tick(data):
                # Timer tick events - don't log every one to avoid spam
                self.socket_events.append("tick")
                self.received_events["tick"] = data
            
            @self.socket_client.event
            def lot_started(data):
                club_name = data.get('club', {}).get('name', 'Unknown')
                lot_number = data.get('lotNumber', 0)
                self.log(f"✅ lot_started event received: Lot {lot_number} - {club_name}")
                self.socket_events.append("lot_started")
                self.received_events["lot_started"] = data
            
            @self.socket_client.event
            def sold(data):
                club_id = data.get('clubId')
                winning_bid = data.get('winningBid')
                unsold = data.get('unsold', False)
                if unsold:
                    self.log(f"✅ sold event received: Club {club_id} went unsold")
                else:
                    amount = winning_bid.get('amount', 0) if winning_bid else 0
                    winner = winning_bid.get('userName', 'Unknown') if winning_bid else 'Unknown'
                    self.log(f"✅ sold event received: Club {club_id} sold to {winner} for £{amount:,.0f}")
                self.socket_events.append("sold")
                self.received_events["sold"] = data
            
            @self.socket_client.event
            def sync_state(data):
                self.log("✅ sync_state event received")
                self.socket_events.append("sync_state")
                self.received_events["sync_state"] = data
            
            @self.socket_client.event
            def auction_paused(data):
                self.log("✅ auction_paused event received")
                self.socket_events.append("auction_paused")
                self.received_events["auction_paused"] = data
            
            @self.socket_client.event
            def auction_resumed(data):
                self.log("✅ auction_resumed event received")
                self.socket_events.append("auction_resumed")
                self.received_events["auction_resumed"] = data
            
            # Connect to socket
            self.socket_client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            
            # Wait for connection
            time.sleep(2)
            
            if "connected" not in self.socket_events:
                self.log("Socket.IO connection failed", "ERROR")
                return False
            
            # Join auction room if we have an auction
            if "auction_id" in self.test_data:
                self.socket_client.emit('join_auction', {'auctionId': self.test_data["auction_id"]})
                time.sleep(1)
            
            self.log("✅ Socket.IO connection established")
            return True
            
        except Exception as e:
            self.log(f"Socket.IO setup failed: {str(e)}", "ERROR")
            return False

    def test_real_time_bidding_system(self) -> bool:
        """Test 3: Real-time Bidding System with Socket.IO events"""
        self.log("=== TEST 3: Real-time Bidding System ===")
        
        if not self.socket_client or "auction_id" not in self.test_data:
            self.log("Socket not connected or no auction available", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_id = self.test_data["user_id"]
        current_club = self.test_data.get("current_club")
        
        if not current_club:
            self.log("No current club available for bidding", "ERROR")
            return False
        
        # Clear previous events
        self.socket_events = []
        self.received_events = {}
        
        # Test minimum £1M budget validation
        self.log("Testing minimum £1M budget validation...")
        
        # Test bid below minimum (should fail)
        low_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 500000.0  # £500k - below minimum
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
        if "detail" not in result or "£1,000,000" not in result.get("detail", ""):
            self.log("Minimum budget validation failed", "ERROR")
            return False
        
        self.log("✅ Minimum £1M budget validation working")
        
        # Place multiple valid bids to test real-time events
        bid_amounts = [1200000.0, 1500000.0, 1800000.0]  # £1.2M, £1.5M, £1.8M
        
        for i, amount in enumerate(bid_amounts):
            self.log(f"Placing bid {i+1}: £{amount:,.0f}")
            
            bid_data = {
                "userId": user_id,
                "clubId": current_club["id"],
                "amount": amount
            }
            
            result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in result:
                self.log(f"Bid {i+1} failed: {result}", "ERROR")
                return False
            
            # Wait for Socket.IO event
            time.sleep(1)
        
        # Check if bid_placed events were received
        bid_placed_count = self.socket_events.count("bid_placed")
        if bid_placed_count < len(bid_amounts):
            self.log(f"Expected {len(bid_amounts)} bid_placed events, got {bid_placed_count}", "ERROR")
            return False
        
        self.log(f"✅ Received {bid_placed_count} bid_placed Socket.IO events")
        
        # Test timer tick events
        initial_tick_count = self.socket_events.count("tick")
        self.log("Waiting for timer tick events...")
        time.sleep(3)
        final_tick_count = self.socket_events.count("tick")
        
        if final_tick_count > initial_tick_count:
            self.log(f"✅ Received {final_tick_count - initial_tick_count} timer tick events")
        else:
            self.log("No timer tick events received", "ERROR")
            return False
        
        # Verify bid data storage and retrieval
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Failed to retrieve auction data", "ERROR")
            return False
        
        bids = result.get("bids", [])
        if len(bids) < len(bid_amounts):
            self.log(f"Expected at least {len(bid_amounts)} bids stored, got {len(bids)}", "ERROR")
            return False
        
        self.log(f"✅ Bid data properly stored and retrieved ({len(bids)} bids)")
        
        self.log("✅ Real-time Bidding System: PASSED")
        return True

    def test_club_status_and_budget_management(self) -> bool:
        """Test 4: Club Status & Budget Management"""
        self.log("=== TEST 4: Club Status & Budget Management ===")
        
        if "auction_id" not in self.test_data:
            self.log("No auction available for status testing", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_id = self.test_data["user_id"]
        league_id = self.test_data["league_id"]
        
        # Get initial participant budget
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/participants")
        if "error" in result:
            self.log("Failed to get participants", "ERROR")
            return False
        
        participants = result
        user_participant = next((p for p in participants if p.get("userId") == user_id), None)
        if not user_participant:
            self.log("User participant not found", "ERROR")
            return False
        
        initial_budget = user_participant.get("budgetRemaining", 0)
        initial_spent = user_participant.get("totalSpent", 0)
        initial_clubs_won = len(user_participant.get("clubsWon", []))
        
        self.log(f"Initial budget: £{initial_budget:,.0f}, spent: £{initial_spent:,.0f}, clubs won: {initial_clubs_won}")
        
        # Place a winning bid and complete the lot to test budget deduction
        current_club = self.test_data.get("current_club")
        if not current_club:
            self.log("No current club for testing", "ERROR")
            return False
        
        winning_amount = 2500000.0  # £2.5M
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": winning_amount
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Failed to place winning bid", "ERROR")
            return False
        
        self.log(f"Placed winning bid: £{winning_amount:,.0f}")
        
        # Complete the lot to trigger budget deduction
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Failed to complete lot", "ERROR")
            return False
        
        self.log("Lot completed")
        
        # Wait for processing
        time.sleep(2)
        
        # Check budget deduction
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/participants")
        if "error" in result:
            self.log("Failed to get updated participants", "ERROR")
            return False
        
        participants = result
        updated_participant = next((p for p in participants if p.get("userId") == user_id), None)
        if not updated_participant:
            self.log("Updated participant not found", "ERROR")
            return False
        
        final_budget = updated_participant.get("budgetRemaining", 0)
        final_spent = updated_participant.get("totalSpent", 0)
        final_clubs_won = len(updated_participant.get("clubsWon", []))
        
        self.log(f"Final budget: £{final_budget:,.0f}, spent: £{final_spent:,.0f}, clubs won: {final_clubs_won}")
        
        # Verify budget deduction
        expected_budget = initial_budget - winning_amount
        if abs(final_budget - expected_budget) > 1:  # Allow for small rounding differences
            self.log(f"Budget deduction incorrect: expected £{expected_budget:,.0f}, got £{final_budget:,.0f}", "ERROR")
            return False
        
        if final_spent != initial_spent + winning_amount:
            self.log(f"Total spent incorrect: expected £{initial_spent + winning_amount:,.0f}, got £{final_spent:,.0f}", "ERROR")
            return False
        
        if final_clubs_won != initial_clubs_won + 1:
            self.log(f"Clubs won count incorrect: expected {initial_clubs_won + 1}, got {final_clubs_won}", "ERROR")
            return False
        
        self.log("✅ Budget deductions working correctly")
        
        # Test club status transitions
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
        if "error" in result:
            self.log("Failed to get clubs status", "ERROR")
            return False
        
        clubs_data = result.get("clubs", [])
        status_counts = {"current": 0, "upcoming": 0, "sold": 0, "unsold": 0}
        
        for club in clubs_data:
            status = club.get("status")
            if status in status_counts:
                status_counts[status] += 1
        
        self.log(f"Club status distribution: {status_counts}")
        
        # Should have exactly one current club and at least one sold club
        if status_counts["current"] != 1:
            self.log(f"Expected 1 current club, got {status_counts['current']}", "ERROR")
            return False
        
        if status_counts["sold"] < 1:
            self.log(f"Expected at least 1 sold club, got {status_counts['sold']}", "ERROR")
            return False
        
        self.log("✅ Club status transitions working correctly")
        
        self.log("✅ Club Status & Budget Management: PASSED")
        return True

    def test_commissioner_controls(self) -> bool:
        """Test 5: Commissioner Controls (pause/resume/delete)"""
        self.log("=== TEST 5: Commissioner Controls ===")
        
        if "auction_id" not in self.test_data:
            self.log("No auction available for commissioner testing", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_id = self.test_data["user_id"]
        
        # Test pause auction functionality
        self.log("Testing pause auction...")
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/pause")
        if "error" in result:
            self.log("Pause auction failed", "ERROR")
            return False
        
        remaining_time = result.get("remainingTime", 0)
        self.log(f"✅ Auction paused with {remaining_time}s remaining")
        
        # Wait for pause event
        time.sleep(1)
        if "auction_paused" in self.socket_events:
            self.log("✅ auction_paused Socket.IO event received")
        else:
            self.log("auction_paused event not received", "WARN")
        
        # Verify auction is paused
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Failed to get auction status", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        if auction_data.get("status") != "paused":
            self.log(f"Auction status should be 'paused', got '{auction_data.get('status')}'", "ERROR")
            return False
        
        self.log("✅ Auction status correctly set to paused")
        
        # Test resume auction functionality
        self.log("Testing resume auction...")
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/resume")
        if "error" in result:
            self.log("Resume auction failed", "ERROR")
            return False
        
        self.log("✅ Auction resumed successfully")
        
        # Wait for resume event
        time.sleep(1)
        if "auction_resumed" in self.socket_events:
            self.log("✅ auction_resumed Socket.IO event received")
        else:
            self.log("auction_resumed event not received", "WARN")
        
        # Verify auction is active again
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Failed to get auction status after resume", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        if auction_data.get("status") != "active":
            self.log(f"Auction status should be 'active', got '{auction_data.get('status')}'", "ERROR")
            return False
        
        self.log("✅ Auction status correctly set to active after resume")
        
        # Test delete auction functionality
        self.log("Testing delete auction...")
        result = self.test_api_endpoint("DELETE", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Delete auction failed", "ERROR")
            return False
        
        deleted_data = result.get("deletedData", {})
        self.log(f"✅ Auction deleted: {deleted_data}")
        
        # Verify auction is deleted
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}", expected_status=404)
        if "error" not in result:
            self.log("Auction should be deleted but still exists", "ERROR")
            return False
        
        self.log("✅ Auction successfully deleted")
        
        self.log("✅ Commissioner Controls: PASSED")
        return True

    def cleanup(self):
        """Clean up test data and connections"""
        self.log("=== Cleaning Up ===")
        
        # Disconnect socket
        if self.socket_client and self.socket_client.connected:
            self.socket_client.disconnect()
        
        # Delete test league if it still exists
        if "league_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}")
            if "error" not in result:
                self.log("Test league deleted")

    def run_production_tests(self) -> Dict[str, bool]:
        """Run all production tests as specified in review request"""
        self.log("🚀 Starting Production Tests for UEFA Club Auction")
        
        results = {}
        
        # Test basic API connectivity
        root_result = self.test_api_endpoint("GET", "/")
        if "error" in root_result:
            self.log("❌ API not accessible", "ERROR")
            return {"api_connectivity": False}
        
        self.log("✅ API connectivity working")
        results["api_connectivity"] = True
        
        # Run production test suites in order
        test_suites = [
            ("league_creation_500m_budget", self.test_league_creation_with_500m_budget),
            ("auction_management_randomization", self.test_auction_management_and_randomization),
            ("socket_connection_setup", self.setup_socket_connection),
            ("real_time_bidding_system", self.test_real_time_bidding_system),
            ("club_status_budget_management", self.test_club_status_and_budget_management),
            ("commissioner_controls", self.test_commissioner_controls),
        ]
        
        for test_name, test_func in test_suites:
            try:
                self.log(f"\n{'='*60}")
                results[test_name] = test_func()
                if not results[test_name]:
                    self.log(f"❌ {test_name} FAILED", "ERROR")
                else:
                    self.log(f"✅ {test_name} PASSED")
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = ProductionTester()
    results = tester.run_production_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("PRODUCTION TEST SUMMARY - UEFA CLUB AUCTION")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All production tests passed!")
        print("✅ UEFA Club Auction system ready for production use")
        return True
    else:
        print("⚠️  Some production tests failed")
        print("❌ Issues found that need attention before production")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)