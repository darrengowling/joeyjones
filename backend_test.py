#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Friends of Pifa UEFA Club Auction
Tests all CRUD operations, Socket.IO connections, and real-time auction flow
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"
SOCKET_URL = "https://ucl-bidding.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class BackendTester:
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
                return {"error": f"Status {response.status_code}", "text": response.text}
                
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
            "budget": 100.0,
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
        
        # Place a bid
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 15.0
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
        bid_data["amount"] = 25.0
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log("Second bid placement failed", "ERROR")
            return False
            
        self.log("✅ Bidding endpoints working")
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
                    "amount": 35.0
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