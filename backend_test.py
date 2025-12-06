#!/usr/bin/env python3
"""
Comprehensive Backend Readiness Test for Pilot Report
Tests all core backend functionality as requested in the review.
"""

import requests
import json
import uuid
import time
import csv
import io
from datetime import datetime, timezone

# Backend URL from frontend/.env
BACKEND_URL = "https://restart-auction.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.test_results = {
            "multi_sport_foundation": {},
            "asset_management": {},
            "league_creation_management": {},
            "auction_core_functionality": {},
            "cricket_specific_features": {},
            "my_competitions_endpoints": {}
        }
        self.test_user_id = None
        self.test_league_id = None
        self.test_auction_id = None
        self.invite_token = None
        
    def log_test(self, category, test_name, success, details="", response_code=None):
        """Log test result"""
        self.test_results[category][test_name] = {
            "success": success,
            "details": details,
            "response_code": response_code,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category}.{test_name}: {details}")
        
    def create_test_user(self):
        """Create a test user for authentication"""
        try:
            user_data = {
                "name": f"TestUser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com"
            }
            
            response = requests.post(f"{BACKEND_URL}/users", json=user_data)
            if response.status_code == 200:
                user = response.json()
                self.test_user_id = user["id"]
                print(f"✅ Created test user: {user['name']} (ID: {self.test_user_id})")
                return True
            else:
                print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating test user: {str(e)}")
            return False
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}
    
    def test_user_endpoints(self) -> bool:
        """Test all user-related endpoints"""
        self.log("=== Testing User Endpoints ===")
        
        # Test user creation
        user_data = {
            "name": "John Manager",
            "email": "john.manager@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in result:
            self.log("User creation failed", "ERROR")
            return False
            
        user_id = result.get("id")
        if not user_id:
            self.log("No user ID returned", "ERROR")
            return False
            
        self.test_data["user_id"] = user_id
        self.test_data["user"] = result
        self.log(f"Created user: {user_id}")
        
        # Test get user
        result = self.test_api_endpoint("GET", f"/users/{user_id}")
        if "error" in result:
            self.log("Get user failed", "ERROR")
            return False
            
        # Test magic link auth
        magic_result = self.test_api_endpoint("POST", "/auth/magic-link", {"email": user_data["email"]})
        if "error" in magic_result:
            self.log("Magic link generation failed", "ERROR")
            return False
            
        # Test magic link verification
        verify_result = self.test_api_endpoint("POST", "/auth/verify-magic-link", {
            "email": user_data["email"],
            "token": magic_result.get("token", "test-token")
        })
        if "error" in verify_result:
            self.log("Magic link verification failed", "ERROR")
            return False
            
        self.log("✅ User endpoints working")
        return True
    
    def test_club_endpoints(self) -> bool:
        """Test club-related endpoints"""
        self.log("=== Testing Club Endpoints ===")
        
        # Test club seeding
        result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" in result:
            self.log("Club seeding failed", "ERROR")
            return False
            
        # Test get clubs
        result = self.test_api_endpoint("GET", "/clubs")
        if "error" in result:
            self.log("Get clubs failed", "ERROR")
            return False
            
        if not isinstance(result, list) or len(result) == 0:
            self.log("No clubs returned", "ERROR")
            return False
            
        self.test_data["clubs"] = result
        self.log(f"Retrieved {len(result)} clubs")
        
        self.log("✅ Club endpoints working")
        return True
    
    def test_league_endpoints(self) -> bool:
        """Test league-related endpoints"""
        self.log("=== Testing League Endpoints ===")
        
        if "user_id" not in self.test_data:
            self.log("No user ID available for league testing", "ERROR")
            return False
            
        # Create league
        league_data = {
            "name": "Test Champions League",
            "commissionerId": self.test_data["user_id"],
            "budget": 50000000.0,  # £50m budget to allow for minimum £1m bids
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
        if not league_id or not invite_token:
            self.log("No league ID or invite token returned", "ERROR")
            return False
            
        self.test_data["league_id"] = league_id
        self.test_data["invite_token"] = invite_token
        self.log(f"Created league: {league_id}")
        
        # Test get leagues
        result = self.test_api_endpoint("GET", "/leagues")
        if "error" in result:
            self.log("Get leagues failed", "ERROR")
            return False
            
        # Test get specific league
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}")
        if "error" in result:
            self.log("Get specific league failed", "ERROR")
            return False
            
        # Test join league
        join_data = {
            "userId": self.test_data["user_id"],
            "inviteToken": invite_token
        }
        
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in result:
            self.log("Join league failed", "ERROR")
            return False
            
        # Test get participants
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/participants")
        if "error" in result:
            self.log("Get participants failed", "ERROR")
            return False
            
        if not isinstance(result, list) or len(result) == 0:
            self.log("No participants returned", "ERROR")
            return False
            
        self.log("✅ League endpoints working")
        return True
    
    def test_auction_endpoints(self) -> bool:
        """Test auction-related endpoints"""
        self.log("=== Testing Auction Endpoints ===")
        
        if "league_id" not in self.test_data:
            self.log("No league ID available for auction testing", "ERROR")
            return False
            
        league_id = self.test_data["league_id"]
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Auction start failed", "ERROR")
            return False
            
        auction_id = result.get("auctionId")
        if not auction_id:
            self.log("No auction ID returned", "ERROR")
            return False
            
        self.test_data["auction_id"] = auction_id
        self.log(f"Started auction: {auction_id}")
        
        # Test get league auction
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/auction")
        if "error" in result:
            self.log("Get league auction failed", "ERROR")
            return False
            
        # Test get auction details
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Get auction details failed", "ERROR")
            return False
            
        auction_data = result.get("auction", {})
        current_club = result.get("currentClub")
        
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
            
        self.test_data["current_club"] = current_club
        self.log(f"Current club: {current_club.get('name')}")
        
        self.log("✅ Auction endpoints working")
        return True
    
    def test_bidding_endpoints(self) -> bool:
        """Test bidding functionality"""
        self.log("=== Testing Bidding Endpoints ===")
        
        if "auction_id" not in self.test_data or "current_club" not in self.test_data:
            self.log("No auction or current club available for bidding", "ERROR")
            return False
            
        auction_id = self.test_data["auction_id"]
        current_club = self.test_data["current_club"]
        user_id = self.test_data["user_id"]
        
        # Place a bid (must be at least £1m)
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 1200000.0  # £1.2m
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Bid placement failed", "ERROR")
            return False
            
        bid = result.get("bid")
        if not bid:
            self.log("No bid returned", "ERROR")
            return False
            
        self.log(f"Placed bid: ${bid.get('amount')} for {current_club.get('name')}")
        
        # Place another bid (higher)
        bid_data["amount"] = 1500000.0  # £1.5m
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Second bid placement failed", "ERROR")
            return False
            
        self.log("✅ Bidding endpoints working")
        return True
    
    def test_minimum_budget_enforcement(self) -> bool:
        """Test minimum budget enforcement (£1m minimum bid)"""
        self.log("=== Testing Minimum Budget Enforcement ===")
        
        if "auction_id" not in self.test_data or "current_club" not in self.test_data:
            self.log("No auction or current club available for minimum budget testing", "ERROR")
            return False
            
        auction_id = self.test_data["auction_id"]
        current_club = self.test_data["current_club"]
        user_id = self.test_data["user_id"]
        
        # Test 1: Bid below £1m should be rejected
        self.log("Testing bid below £1m minimum...")
        low_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 500000.0  # £500k - below minimum
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
        # For 400 status, we should get the error detail directly
        if "detail" not in result:
            self.log(f"Low bid should have been rejected but was accepted. Result: {result}", "ERROR")
            return False
        
        # Check error message contains proper currency formatting
        error_detail = result.get("detail", "")
        if "£1,000,000" not in error_detail:
            self.log(f"Error message doesn't contain proper currency formatting: {error_detail}", "ERROR")
            return False
        
        self.log("✅ Bid below £1m correctly rejected with proper error message")
        
        # Test 2: Bid exactly at £1m should be accepted
        self.log("Testing bid exactly at £1m minimum...")
        min_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 1000000.0  # £1m - exactly at minimum
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", min_bid_data, expected_status=200)
        if "error" in result:
            self.log(f"Minimum bid should have been accepted but was rejected: {result.get('text')}", "ERROR")
            return False
        
        bid = result.get("bid")
        if not bid or bid.get("amount") != 1000000.0:
            self.log("Minimum bid not properly recorded", "ERROR")
            return False
        
        self.log("✅ Bid exactly at £1m correctly accepted")
        
        # Test 3: Bid above £1m should be accepted
        self.log("Testing bid above £1m minimum...")
        high_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 1500000.0  # £1.5m - above minimum
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", high_bid_data, expected_status=200)
        if "error" in result:
            self.log(f"High bid should have been accepted but was rejected: {result.get('text')}", "ERROR")
            return False
        
        bid = result.get("bid")
        if not bid or bid.get("amount") != 1500000.0:
            self.log("High bid not properly recorded", "ERROR")
            return False
        
        self.log("✅ Bid above £1m correctly accepted")
        
        # Note: Budget remaining validation also works alongside minimum budget enforcement
        
        self.log("✅ Minimum budget enforcement working correctly")
        return True
    
    def test_clubs_list_endpoint(self) -> bool:
        """Test clubs list endpoint with status information"""
        self.log("=== Testing Clubs List Endpoint ===")
        
        if "auction_id" not in self.test_data:
            self.log("No auction available for clubs list testing", "ERROR")
            return False
            
        auction_id = self.test_data["auction_id"]
        
        # Test clubs list endpoint
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
        if "error" in result:
            self.log("Clubs list endpoint failed", "ERROR")
            return False
        
        clubs_data = result.get("clubs")
        if not clubs_data or not isinstance(clubs_data, list):
            self.log("No clubs data returned or invalid format", "ERROR")
            return False
        
        self.log(f"Retrieved {len(clubs_data)} clubs with status information")
        
        # Verify required fields are present
        required_fields = ["id", "name", "status", "lotNumber"]
        for club in clubs_data[:3]:  # Check first 3 clubs
            for field in required_fields:
                if field not in club:
                    self.log(f"Missing required field '{field}' in club data", "ERROR")
                    return False
        
        # Check status values are valid
        valid_statuses = ["current", "upcoming", "sold", "unsold"]
        status_counts = {"current": 0, "upcoming": 0, "sold": 0, "unsold": 0}
        
        for club in clubs_data:
            status = club.get("status")
            if status not in valid_statuses:
                self.log(f"Invalid status '{status}' found in club data", "ERROR")
                return False
            status_counts[status] += 1
        
        self.log(f"Status distribution: {status_counts}")
        
        # Should have exactly one current club
        if status_counts["current"] != 1:
            self.log(f"Expected exactly 1 current club, found {status_counts['current']}", "ERROR")
            return False
        
        # Should have upcoming clubs
        if status_counts["upcoming"] == 0:
            self.log("Expected some upcoming clubs, found none", "ERROR")
            return False
        
        # Check sorting - current should be first
        first_club = clubs_data[0]
        if first_club.get("status") != "current":
            self.log(f"First club should be current, but is {first_club.get('status')}", "ERROR")
            return False
        
        # Check lot numbers are present and valid
        current_club = first_club
        if not current_club.get("lotNumber") or current_club.get("lotNumber") < 1:
            self.log("Current club should have valid lot number", "ERROR")
            return False
        
        # Check summary statistics
        total_clubs = result.get("totalClubs", 0)
        sold_clubs = result.get("soldClubs", 0)
        unsold_clubs = result.get("unsoldClubs", 0)
        remaining_clubs = result.get("remainingClubs", 0)
        
        if total_clubs != len(clubs_data):
            self.log(f"Total clubs mismatch: summary says {total_clubs}, actual {len(clubs_data)}", "ERROR")
            return False
        
        if sold_clubs != status_counts["sold"]:
            self.log(f"Sold clubs mismatch: summary says {sold_clubs}, actual {status_counts['sold']}", "ERROR")
            return False
        
        if unsold_clubs != status_counts["unsold"]:
            self.log(f"Unsold clubs mismatch: summary says {unsold_clubs}, actual {status_counts['unsold']}", "ERROR")
            return False
        
        expected_remaining = status_counts["current"] + status_counts["upcoming"]
        if remaining_clubs != expected_remaining:
            self.log(f"Remaining clubs mismatch: summary says {remaining_clubs}, expected {expected_remaining}", "ERROR")
            return False
        
        self.log("✅ Clubs list endpoint working correctly")
        
        # Test with sold clubs (place some bids and complete lots to create sold clubs)
        self.log("Testing clubs list with sold clubs...")
        
        # Place a winning bid on current club
        if "user_id" in self.test_data and "current_club" in self.test_data:
            winning_bid_data = {
                "userId": self.test_data["user_id"],
                "clubId": self.test_data["current_club"]["id"],
                "amount": 2000000.0  # £2m
            }
            
            bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", winning_bid_data)
            if bid_result and "error" not in bid_result:
                self.log("Placed winning bid for clubs list testing")
                
                # Complete the lot to create a sold club
                complete_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
                if complete_result and "error" not in complete_result:
                    self.log("Completed lot to create sold club")
                    
                    # Wait a moment for the lot to process
                    time.sleep(2)
                    
                    # Check clubs list again
                    updated_result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
                    if updated_result and "error" not in updated_result:
                        updated_clubs = updated_result.get("clubs", [])
                        sold_count = len([c for c in updated_clubs if c.get("status") == "sold"])
                        
                        if sold_count > 0:
                            self.log("✅ Clubs list correctly shows sold clubs")
                            
                            # Check that sold club has winner and winning bid info
                            sold_club = next((c for c in updated_clubs if c.get("status") == "sold"), None)
                            if sold_club:
                                winner = sold_club.get("winner")
                                winning_bid = sold_club.get("winningBid")
                                if winner and winning_bid:
                                    self.log("✅ Sold club includes winner and winning bid information")
                                else:
                                    self.log("Sold club missing winner or winning bid information", "ERROR")
                                    return False
                        else:
                            self.log("No sold clubs found after completing lot", "ERROR")
                            return False
        
        self.log("✅ Clubs list endpoint fully working")
        return True
    
    def test_socket_connection(self) -> bool:
        """Test Socket.IO connection and events"""
        self.log("=== Testing Socket.IO Connection ===")
        
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
            def joined(data):
                self.log(f"Joined auction room: {data}")
                self.socket_events.append("joined")
            
            @self.socket_client.event
            def sync_state(data):
                self.log("Received sync_state event")
                self.socket_events.append("sync_state")
            
            @self.socket_client.event
            def bid_placed(data):
                self.log(f"Bid placed event: {data.get('bid', {}).get('amount')}")
                self.socket_events.append("bid_placed")
            
            @self.socket_client.event
            def timer_update(data):
                self.log(f"Timer update: {data.get('timeRemaining')}s")
                self.socket_events.append("timer_update")
            
            @self.socket_client.event
            def lot_started(data):
                self.log(f"Lot started: {data.get('club', {}).get('name')}")
                self.socket_events.append("lot_started")
            
            @self.socket_client.event
            def lot_complete(data):
                self.log("Lot completed")
                self.socket_events.append("lot_complete")
            
            @self.socket_client.event
            def anti_snipe_triggered(data):
                self.log(f"Anti-snipe triggered: +{data.get('extensionSeconds')}s")
                self.socket_events.append("anti_snipe_triggered")
            
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
                
                if "joined" not in self.socket_events:
                    self.log("Failed to join auction room", "ERROR")
                    return False
            
            self.log("✅ Socket.IO connection working")
            return True
            
        except Exception as e:
            self.log(f"Socket.IO test failed: {str(e)}", "ERROR")
            return False
    
    def test_real_time_auction_flow(self) -> bool:
        """Test complete real-time auction workflow"""
        self.log("=== Testing Real-time Auction Flow ===")
        
        if not self.socket_client or "auction_id" not in self.test_data:
            self.log("Socket not connected or no auction available", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_id = self.test_data["user_id"]
        
        try:
            # Clear previous events
            self.socket_events = []
            
            # Place a bid to trigger events
            if "current_club" in self.test_data:
                bid_data = {
                    "userId": user_id,
                    "clubId": self.test_data["current_club"]["id"],
                    "amount": 1300000.0  # £1.3m
                }
                
                result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
                if "error" not in result:
                    self.log("Placed bid to test real-time events")
                    
                    # Wait for socket events
                    time.sleep(3)
                    
                    if "bid_placed" in self.socket_events:
                        self.log("✅ Real-time bid events working")
                    else:
                        self.log("No bid_placed event received", "ERROR")
                        return False
            
            # Test timer updates
            initial_timer_events = self.socket_events.count("timer_update")
            time.sleep(5)  # Wait for timer updates
            final_timer_events = self.socket_events.count("timer_update")
            
            if final_timer_events > initial_timer_events:
                self.log("✅ Timer updates working")
            else:
                self.log("No timer updates received", "ERROR")
                return False
            
            self.log("✅ Real-time auction flow working")
            return True
            
        except Exception as e:
            self.log(f"Real-time auction flow test failed: {str(e)}", "ERROR")
            return False
    
    def test_lot_management(self) -> bool:
        """Test lot completion and progression"""
        self.log("=== Testing Lot Management ===")
        
        if "auction_id" not in self.test_data:
            self.log("No auction available for lot testing", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        
        # Test complete lot
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in result:
            self.log("Lot completion failed", "ERROR")
            return False
        
        self.log("Lot completed successfully")
        
        # Wait for next lot to start
        time.sleep(3)
        
        # Check if next lot started
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Failed to get auction after lot completion", "ERROR")
            return False
        
        auction_data = result.get("auction", {})
        current_lot = auction_data.get("currentLot", 0)
        
        if current_lot > 1:
            self.log(f"✅ Lot progression working (now on lot {current_lot})")
        else:
            self.log("Lot did not progress", "ERROR")
            return False
        
        return True
    
    def test_scoring_endpoints(self) -> bool:
        """Test scoring system endpoints"""
        self.log("=== Testing Scoring Endpoints ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for scoring tests", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # Test recompute scores
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/score/recompute")
        if "error" in result:
            self.log("Score recomputation failed", "ERROR")
            return False
        
        # Test get standings
        result = self.test_api_endpoint("GET", f"/leagues/{league_id}/standings")
        if "error" in result:
            self.log("Get standings failed", "ERROR")
            return False
        
        self.log("✅ Scoring endpoints working")
        return True
    
    def cleanup(self):
        """Clean up test data and connections"""
        self.log("=== Cleaning Up ===")
        
        # Disconnect socket
        if self.socket_client and self.socket_client.connected:
            self.socket_client.disconnect()
        
        # Delete test league if created
        if "league_id" in self.test_data and "user_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}?user_id={self.test_data['user_id']}")
            if "error" not in result:
                self.log("Test league deleted")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all backend tests"""
        self.log("🚀 Starting Backend API Tests")
        
        results = {}
        
        # Test basic API connectivity
        root_result = self.test_api_endpoint("GET", "/")
        if "error" in root_result:
            self.log("❌ API not accessible", "ERROR")
            return {"api_connectivity": False}
        
        self.log("✅ API connectivity working")
        results["api_connectivity"] = True
        
        # Run all test suites
        test_suites = [
            ("user_endpoints", self.test_user_endpoints),
            ("club_endpoints", self.test_club_endpoints),
            ("league_endpoints", self.test_league_endpoints),
            ("auction_endpoints", self.test_auction_endpoints),
            ("bidding_endpoints", self.test_bidding_endpoints),
            ("minimum_budget_enforcement", self.test_minimum_budget_enforcement),
            ("clubs_list_endpoint", self.test_clubs_list_endpoint),
            ("socket_connection", self.test_socket_connection),
            ("real_time_auction_flow", self.test_real_time_auction_flow),
            ("lot_management", self.test_lot_management),
            ("scoring_endpoints", self.test_scoring_endpoints),
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
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*50)
    print("BACKEND TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend tests passed!")
        return True
    else:
        print("⚠️  Some backend tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)