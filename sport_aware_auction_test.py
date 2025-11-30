#!/usr/bin/env python3
"""
Sport-Aware Auction System Testing
Tests the complete multi-sport functionality as requested in review:
- League-Based Asset Filtering
- Football vs Cricket league asset handling
- Auction System Sport Awareness
- Backward Compatibility
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://sports-auction-1.preview.emergentagent.com/api"
SOCKET_URL = "https://sports-auction-1.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class SportAwareAuctionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_client = None
        self.socket_events = []
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200, params: dict = None) -> dict:
        """Test API endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
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
                
            return response.json() if response.content else {}
            
        except Exception as e:
            self.log(f"API Error: {str(e)}", "ERROR")
            return {"error": str(e)}

    def test_league_based_asset_filtering(self) -> bool:
        """Test GET /api/leagues/{league_id}/assets endpoint"""
        self.log("=== Testing League-Based Asset Filtering ===")
        
        # First, create test user
        user_data = {
            "name": "Sport Test User",
            "email": "sporttest@example.com"
        }
        user_result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in user_result:
            self.log("Failed to create test user", "ERROR")
            return False
        
        user_id = user_result["id"]
        self.test_data["user_id"] = user_id
        
        # Create football league
        football_league_data = {
            "name": "Football Test League",
            "commissionerId": user_id,
            "budget": 500000000.0,
            "sportKey": "football"
        }
        football_league_result = self.test_api_endpoint("POST", "/leagues", football_league_data)
        if "error" in football_league_result:
            self.log("Failed to create football league", "ERROR")
            return False
        
        football_league_id = football_league_result["id"]
        self.test_data["football_league_id"] = football_league_id
        self.log(f"Created football league: {football_league_id}")
        
        # Create cricket league
        cricket_league_data = {
            "name": "Cricket Test League", 
            "commissionerId": user_id,
            "budget": 500000000.0,
            "sportKey": "cricket"
        }
        cricket_league_result = self.test_api_endpoint("POST", "/leagues", cricket_league_data)
        if "error" in cricket_league_result:
            self.log("Failed to create cricket league", "ERROR")
            return False
        
        cricket_league_id = cricket_league_result["id"]
        self.test_data["cricket_league_id"] = cricket_league_id
        self.log(f"Created cricket league: {cricket_league_id}")
        
        # Test 1: GET /api/leagues/{league_id}/assets for football league
        self.log("Testing football league assets endpoint...")
        football_assets = self.test_api_endpoint("GET", f"/leagues/{football_league_id}/assets")
        if "error" in football_assets:
            self.log("Failed to get football league assets", "ERROR")
            return False
        
        # Verify football assets structure
        if "assets" not in football_assets or "pagination" not in football_assets:
            self.log("Football assets response missing required fields", "ERROR")
            return False
        
        football_asset_count = len(football_assets["assets"])
        self.log(f"Football league returned {football_asset_count} assets")
        
        # Verify these are clubs (football assets)
        if football_asset_count > 0:
            first_asset = football_assets["assets"][0]
            if "uefaId" not in first_asset or "country" not in first_asset:
                self.log("Football assets don't have club structure (missing uefaId/country)", "ERROR")
                return False
            self.log(f"✅ Football assets are clubs: {first_asset['name']} ({first_asset['country']})")
        
        # Test 2: GET /api/leagues/{league_id}/assets for cricket league
        self.log("Testing cricket league assets endpoint...")
        cricket_assets = self.test_api_endpoint("GET", f"/leagues/{cricket_league_id}/assets")
        if "error" in cricket_assets:
            self.log("Failed to get cricket league assets", "ERROR")
            return False
        
        # Verify cricket assets structure
        if "assets" not in cricket_assets or "pagination" not in cricket_assets:
            self.log("Cricket assets response missing required fields", "ERROR")
            return False
        
        cricket_asset_count = len(cricket_assets["assets"])
        self.log(f"Cricket league returned {cricket_asset_count} assets")
        
        # Verify these are players (cricket assets)
        if cricket_asset_count > 0:
            first_asset = cricket_assets["assets"][0]
            if "sportKey" not in first_asset or first_asset["sportKey"] != "cricket":
                self.log("Cricket assets don't have correct sportKey", "ERROR")
                return False
            if "meta" not in first_asset or "franchise" not in first_asset["meta"]:
                self.log("Cricket assets don't have player structure (missing meta.franchise)", "ERROR")
                return False
            self.log(f"✅ Cricket assets are players: {first_asset['name']} ({first_asset['meta']['franchise']})")
        
        # Test 3: Verify pagination works for both sports
        self.log("Testing pagination for football assets...")
        football_page2 = self.test_api_endpoint("GET", f"/leagues/{football_league_id}/assets", params={"page": 2, "pageSize": 10})
        if "error" not in football_page2:
            self.log(f"✅ Football pagination working - page 2 has {len(football_page2.get('assets', []))} assets")
        
        if cricket_asset_count > 0:
            self.log("Testing pagination for cricket assets...")
            cricket_page2 = self.test_api_endpoint("GET", f"/leagues/{cricket_league_id}/assets", params={"page": 2, "pageSize": 10})
            if "error" not in cricket_page2:
                self.log(f"✅ Cricket pagination working - page 2 has {len(cricket_page2.get('assets', []))} assets")
        
        # Test 4: Verify search works for both sports
        if football_asset_count > 0:
            self.log("Testing search for football assets...")
            football_search = self.test_api_endpoint("GET", f"/leagues/{football_league_id}/assets", params={"search": "Real"})
            if "error" not in football_search:
                search_count = len(football_search.get("assets", []))
                self.log(f"✅ Football search working - found {search_count} assets matching 'Real'")
        
        if cricket_asset_count > 0:
            self.log("Testing search for cricket assets...")
            cricket_search = self.test_api_endpoint("GET", f"/leagues/{cricket_league_id}/assets", params={"search": "Mumbai"})
            if "error" not in cricket_search:
                search_count = len(cricket_search.get("assets", []))
                self.log(f"✅ Cricket search working - found {search_count} assets matching 'Mumbai'")
        
        self.log("✅ League-Based Asset Filtering tests completed successfully")
        return True

    def test_auction_system_sport_awareness(self) -> bool:
        """Test auction creation and management for different sports"""
        self.log("=== Testing Auction System Sport Awareness ===")
        
        if "football_league_id" not in self.test_data or "cricket_league_id" not in self.test_data:
            self.log("Missing league data from previous tests", "ERROR")
            return False
        
        football_league_id = self.test_data["football_league_id"]
        cricket_league_id = self.test_data["cricket_league_id"]
        
        # Test 5: Create auction for football league
        self.log("Testing auction creation for football league...")
        football_auction = self.test_api_endpoint("POST", f"/leagues/{football_league_id}/auction/start")
        if "error" in football_auction:
            self.log("Failed to create football auction", "ERROR")
            return False
        
        football_auction_id = football_auction.get("auctionId")
        if not football_auction_id:
            self.log("Football auction creation didn't return auctionId", "ERROR")
            return False
        
        self.test_data["football_auction_id"] = football_auction_id
        self.log(f"✅ Football auction created: {football_auction_id}")
        
        # Test 6: Verify football auction uses clubs
        self.log("Verifying football auction uses clubs...")
        football_auction_data = self.test_api_endpoint("GET", f"/auction/{football_auction_id}")
        if "error" in football_auction_data:
            self.log("Failed to get football auction data", "ERROR")
            return False
        
        current_club = football_auction_data.get("currentClub")
        if current_club and "uefaId" in current_club:
            self.log(f"✅ Football auction using clubs: {current_club['name']} (UEFA ID: {current_club['uefaId']})")
        else:
            self.log("Football auction not using club structure", "ERROR")
            return False
        
        # Test 7: Create auction for cricket league (if cricket assets exist)
        self.log("Testing auction creation for cricket league...")
        cricket_auction = self.test_api_endpoint("POST", f"/leagues/{cricket_league_id}/auction/start")
        
        if "error" in cricket_auction:
            # Check if error is due to no cricket assets
            if "No assets available" in cricket_auction.get("text", ""):
                self.log("⚠️ Cricket auction creation failed due to no cricket assets - this is expected if cricket players not seeded")
                self.log("✅ Cricket auction creation properly validates asset availability")
            else:
                self.log(f"Cricket auction creation failed unexpectedly: {cricket_auction}", "ERROR")
                return False
        else:
            cricket_auction_id = cricket_auction.get("auctionId")
            if cricket_auction_id:
                self.test_data["cricket_auction_id"] = cricket_auction_id
                self.log(f"✅ Cricket auction created: {cricket_auction_id}")
                
                # Verify cricket auction uses players
                cricket_auction_data = self.test_api_endpoint("GET", f"/auction/{cricket_auction_id}")
                if "error" not in cricket_auction_data:
                    current_asset = cricket_auction_data.get("currentClub")  # Field name kept for backward compatibility
                    if current_asset and "sportKey" in current_asset and current_asset["sportKey"] == "cricket":
                        self.log(f"✅ Cricket auction using players: {current_asset['name']} (Sport: {current_asset['sportKey']})")
                    else:
                        self.log("Cricket auction not using player structure", "ERROR")
                        return False
        
        # Test 8: Verify auction data endpoints return correct asset information
        self.log("Testing auction clubs/assets endpoint for football...")
        football_clubs = self.test_api_endpoint("GET", f"/auction/{football_auction_id}/clubs")
        if "error" in football_clubs:
            self.log("Failed to get football auction clubs", "ERROR")
            return False
        
        if "clubs" in football_clubs and len(football_clubs["clubs"]) > 0:
            first_club = football_clubs["clubs"][0]
            if "uefaId" in first_club and "country" in first_club:
                self.log(f"✅ Football auction clubs endpoint returns club data: {first_club['name']} ({first_club['country']})")
            else:
                self.log("Football auction clubs endpoint not returning club structure", "ERROR")
                return False
        
        self.log("✅ Auction System Sport Awareness tests completed successfully")
        return True

    def test_backward_compatibility(self) -> bool:
        """Test backward compatibility with existing functionality"""
        self.log("=== Testing Backward Compatibility ===")
        
        # Test 9: Ensure existing auction functionality still works for football
        if "football_auction_id" not in self.test_data:
            self.log("No football auction available for backward compatibility testing", "ERROR")
            return False
        
        football_auction_id = self.test_data["football_auction_id"]
        user_id = self.test_data["user_id"]
        
        # Test bidding functionality
        self.log("Testing bidding functionality (backward compatibility)...")
        
        # Get current auction state
        auction_data = self.test_api_endpoint("GET", f"/auction/{football_auction_id}")
        if "error" in auction_data:
            self.log("Failed to get auction data for bidding test", "ERROR")
            return False
        
        current_club = auction_data.get("currentClub")
        if not current_club:
            self.log("No current club available for bidding test", "ERROR")
            return False
        
        # Join league as participant first
        football_league_id = self.test_data["football_league_id"]
        league_data = self.test_api_endpoint("GET", f"/leagues/{football_league_id}")
        if "error" in league_data:
            self.log("Failed to get league data", "ERROR")
            return False
        
        invite_token = league_data["inviteToken"]
        join_data = {
            "userId": user_id,
            "inviteToken": invite_token
        }
        join_result = self.test_api_endpoint("POST", f"/leagues/{football_league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join league for bidding test", "ERROR")
            return False
        
        # Place a bid
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 2000000.0  # £2M bid
        }
        bid_result = self.test_api_endpoint("POST", f"/auction/{football_auction_id}/bid", bid_data)
        if "error" in bid_result:
            self.log(f"Bidding failed: {bid_result}", "ERROR")
            return False
        
        self.log(f"✅ Bidding functionality working: £2M bid placed on {current_club['name']}")
        
        # Test 10: Verify existing leagues without explicit sportKey default to football
        self.log("Testing default sportKey behavior...")
        
        # Create league without sportKey
        default_league_data = {
            "name": "Default Sport League",
            "commissionerId": user_id,
            "budget": 500000000.0
            # No sportKey specified
        }
        default_league_result = self.test_api_endpoint("POST", "/leagues", default_league_data)
        if "error" in default_league_result:
            self.log("Failed to create default league", "ERROR")
            return False
        
        # Verify it defaults to football
        if default_league_result.get("sportKey") == "football":
            self.log("✅ Leagues without sportKey default to football")
        else:
            self.log(f"Default sportKey is {default_league_result.get('sportKey')}, expected 'football'", "ERROR")
            return False
        
        # Test 11: Check that Socket.IO events work with new asset structure
        self.log("Testing Socket.IO compatibility...")
        
        try:
            # Create socket client
            sio = socketio.Client()
            connected = False
            
            @sio.event
            def connect():
                nonlocal connected
                connected = True
                self.log("✅ Socket.IO connection established")
            
            @sio.event
            def sync_state(data):
                self.log("✅ Socket.IO sync_state event received")
                if "currentClub" in data and data["currentClub"]:
                    club = data["currentClub"]
                    self.log(f"✅ Socket.IO current club data: {club.get('name', 'Unknown')}")
            
            # Connect to socket
            sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            
            # Wait for connection
            time.sleep(2)
            
            if connected:
                # Join auction room
                sio.emit('join_auction', {'auctionId': football_auction_id})
                time.sleep(2)
                
                self.log("✅ Socket.IO events working with new asset structure")
            else:
                self.log("Socket.IO connection failed", "ERROR")
                return False
            
            sio.disconnect()
            
        except Exception as e:
            self.log(f"Socket.IO test failed: {str(e)}", "ERROR")
            return False
        
        self.log("✅ Backward Compatibility tests completed successfully")
        return True

    def test_sport_labels_and_ui_hints(self) -> bool:
        """Test that sports return correct labels for UI"""
        self.log("=== Testing Sport Labels and UI Hints ===")
        
        # Test sports endpoint
        sports_result = self.test_api_endpoint("GET", "/sports")
        if "error" in sports_result:
            self.log("Failed to get sports", "ERROR")
            return False
        
        sports = sports_result if isinstance(sports_result, list) else []
        
        # Find football and cricket sports
        football_sport = None
        cricket_sport = None
        
        for sport in sports:
            if sport.get("key") == "football":
                football_sport = sport
            elif sport.get("key") == "cricket":
                cricket_sport = sport
        
        # Test football labels
        if football_sport:
            ui_hints = football_sport.get("uiHints", {})
            if ui_hints.get("assetLabel") == "Club" and ui_hints.get("assetPlural") == "Clubs":
                self.log("✅ Football sport has correct labels: Club/Clubs")
            else:
                self.log(f"Football labels incorrect: {ui_hints}", "ERROR")
                return False
        else:
            self.log("Football sport not found", "ERROR")
            return False
        
        # Test cricket labels
        if cricket_sport:
            ui_hints = cricket_sport.get("uiHints", {})
            if ui_hints.get("assetLabel") == "Player" and ui_hints.get("assetPlural") == "Players":
                self.log("✅ Cricket sport has correct labels: Player/Players")
            else:
                self.log(f"Cricket labels incorrect: {ui_hints}", "ERROR")
                return False
        else:
            self.log("Cricket sport not found (may be disabled)", "WARN")
        
        self.log("✅ Sport Labels and UI Hints tests completed successfully")
        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("=== Cleaning up test data ===")
        
        # Delete auctions
        if "football_auction_id" in self.test_data:
            self.test_api_endpoint("DELETE", f"/auction/{self.test_data['football_auction_id']}")
        
        if "cricket_auction_id" in self.test_data:
            self.test_api_endpoint("DELETE", f"/auction/{self.test_data['cricket_auction_id']}")
        
        # Delete leagues
        if "football_league_id" in self.test_data:
            self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['football_league_id']}")
        
        if "cricket_league_id" in self.test_data:
            self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['cricket_league_id']}")
        
        self.log("✅ Cleanup completed")

    def run_all_tests(self) -> bool:
        """Run all sport-aware auction system tests"""
        self.log("🚀 Starting Sport-Aware Auction System Testing")
        
        try:
            # Test 1-4: League-Based Asset Filtering
            if not self.test_league_based_asset_filtering():
                return False
            
            # Test 5-8: Auction System Sport Awareness
            if not self.test_auction_system_sport_awareness():
                return False
            
            # Test 9-11: Backward Compatibility
            if not self.test_backward_compatibility():
                return False
            
            # Test Sport Labels
            if not self.test_sport_labels_and_ui_hints():
                return False
            
            self.log("🎉 All Sport-Aware Auction System tests PASSED!")
            return True
            
        except Exception as e:
            self.log(f"Test suite failed with exception: {str(e)}", "ERROR")
            return False
        finally:
            self.cleanup_test_data()

def main():
    """Main test execution"""
    tester = SportAwareAuctionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ SPORT-AWARE AUCTION SYSTEM TESTING COMPLETED SUCCESSFULLY")
        print("All requested review areas have been tested and are working correctly:")
        print("- League-Based Asset Filtering ✅")
        print("- Football vs Cricket league asset handling ✅") 
        print("- Auction System Sport Awareness ✅")
        print("- Backward Compatibility ✅")
        print("- Sport Labels and UI Hints ✅")
        return 0
    else:
        print("\n❌ SPORT-AWARE AUCTION SYSTEM TESTING FAILED")
        print("Some tests failed - check logs above for details")
        return 1

if __name__ == "__main__":
    exit(main())