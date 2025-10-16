#!/usr/bin/env python3
"""
Focused Socket.IO Testing - Core Functionality
Tests the essential Socket.IO refactor areas that are working
"""

import asyncio
import json
import requests
import socketio
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration from environment
BASE_URL = "https://bidmaster-9.preview.emergentagent.com/api"
SOCKET_URL = "https://bidmaster-9.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class FocusedSocketIOTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_clients = {}
        self.socket_events = {}
        
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
    
    def setup_test_data(self) -> bool:
        """Set up test users, league, and auction"""
        self.log("=== Setting Up Test Data ===")
        
        # Create test users
        users = []
        for i in range(2):
            user_data = {
                "name": f"Socket Test Manager {i+1}",
                "email": f"socketmanager{i+1}@test.com"
            }
            
            result = self.test_api_endpoint("POST", "/users", user_data)
            if "error" in result:
                self.log(f"Failed to create user {i+1}", "ERROR")
                return False
            
            users.append(result)
            self.log(f"Created user {i+1}: {result['id']}")
        
        self.test_data["users"] = users
        
        # Create league
        league_data = {
            "name": "Socket.IO Focused Test League",
            "commissionerId": users[0]["id"],
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "football"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Failed to create league", "ERROR")
            return False
        
        self.test_data["league"] = result
        self.log(f"Created league: {result['id']}")
        
        # Join league with both users
        for i, user in enumerate(users):
            join_data = {
                "userId": user["id"],
                "inviteToken": result["inviteToken"]
            }
            
            join_result = self.test_api_endpoint("POST", f"/leagues/{result['id']}/join", join_data)
            if "error" in join_result:
                self.log(f"Failed to join league with user {i+1}", "ERROR")
                return False
            
            self.log(f"User {i+1} joined league")
        
        # Seed clubs
        clubs_result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" not in clubs_result:
            self.log("Clubs seeded successfully")
        
        self.log("✅ Test data setup complete")
        return True
    
    def create_socket_client(self, client_id: str) -> bool:
        """Create and configure a Socket.IO client"""
        try:
            client = socketio.Client(logger=False, engineio_logger=False)
            self.socket_clients[client_id] = client
            self.socket_events[client_id] = []
            
            # Set up event handlers
            @client.event
            def connect():
                self.log(f"Client {client_id} connected")
                self.socket_events[client_id].append(("connected", {}))
            
            @client.event
            def disconnect():
                self.log(f"Client {client_id} disconnected")
                self.socket_events[client_id].append(("disconnected", {}))
            
            @client.event
            def joined(data):
                self.log(f"Client {client_id} joined auction room: {data}")
                self.socket_events[client_id].append(("joined", data))
            
            @client.event
            def room_joined(data):
                self.log(f"Client {client_id} joined league room: {data}")
                self.socket_events[client_id].append(("room_joined", data))
            
            @client.event
            def sync_members(data):
                self.log(f"Client {client_id} received sync_members: {len(data.get('members', []))} members")
                self.socket_events[client_id].append(("sync_members", data))
            
            @client.event
            def sync_state(data):
                self.log(f"Client {client_id} received sync_state")
                self.socket_events[client_id].append(("sync_state", data))
            
            @client.event
            def bid_placed(data):
                self.log(f"Client {client_id} received bid_placed: £{data.get('bid', {}).get('amount', 0):,.0f}")
                self.socket_events[client_id].append(("bid_placed", data))
            
            @client.event
            def bid_update(data):
                self.log(f"Client {client_id} received bid_update: £{data.get('amount', 0):,.0f}")
                self.socket_events[client_id].append(("bid_update", data))
            
            @client.event
            def auction_started(data):
                self.log(f"Client {client_id} received auction_started")
                self.socket_events[client_id].append(("auction_started", data))
            
            @client.event
            def member_joined(data):
                self.log(f"Client {client_id} received member_joined: {data}")
                self.socket_events[client_id].append(("member_joined", data))
            
            # Connect
            client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(1)
            
            # Check if connected
            if not any(event[0] == "connected" for event in self.socket_events[client_id]):
                self.log(f"Client {client_id} failed to connect", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create client {client_id}: {str(e)}", "ERROR")
            return False
    
    def test_socket_connection(self) -> bool:
        """Test basic Socket.IO connection"""
        self.log("=== Testing Socket.IO Connection ===")
        
        if not self.create_socket_client("test_client"):
            return False
        
        self.log("✅ Socket.IO connection working")
        return True
    
    def test_league_room_joining(self) -> bool:
        """Test joining league rooms"""
        self.log("=== Testing League Room Joining ===")
        
        if not self.test_data.get("league"):
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        
        if not self.create_socket_client("league_client"):
            return False
        
        client = self.socket_clients["league_client"]
        
        # Clear events
        self.socket_events["league_client"] = []
        
        # Join league room
        client.emit('join_league', {'leagueId': league_id})
        time.sleep(2)
        
        # Check if joined and received sync_members
        events = [event[0] for event in self.socket_events["league_client"]]
        
        if "room_joined" not in events:
            self.log("Failed to join league room", "ERROR")
            return False
        
        if "sync_members" not in events:
            self.log("Did not receive sync_members", "ERROR")
            return False
        
        self.log("✅ League room joining working")
        return True
    
    def test_auction_room_functionality(self) -> bool:
        """Test auction room joining and sync_state"""
        self.log("=== Testing Auction Room Functionality ===")
        
        if not self.test_data.get("league"):
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Failed to start auction", "ERROR")
            return False
        
        auction_id = result["auctionId"]
        self.test_data["auction_id"] = auction_id
        self.log(f"Started auction: {auction_id}")
        
        if not self.create_socket_client("auction_client"):
            return False
        
        client = self.socket_clients["auction_client"]
        
        # Clear events
        self.socket_events["auction_client"] = []
        
        # Join auction room
        client.emit('join_auction', {'auctionId': auction_id})
        time.sleep(2)
        
        # Check events
        events = [event[0] for event in self.socket_events["auction_client"]]
        
        if "joined" not in events:
            self.log("Failed to join auction room", "ERROR")
            return False
        
        if "sync_state" not in events:
            self.log("Did not receive sync_state", "ERROR")
            return False
        
        # Check sync_state data
        sync_state_event = next((event[1] for event in self.socket_events["auction_client"] if event[0] == "sync_state"), None)
        if not sync_state_event:
            self.log("No sync_state data", "ERROR")
            return False
        
        required_fields = ["auction", "currentClub", "participants"]
        for field in required_fields:
            if field not in sync_state_event:
                self.log(f"sync_state missing field: {field}", "ERROR")
                return False
        
        self.log("✅ Auction room functionality working")
        return True
    
    def test_real_time_bidding(self) -> bool:
        """Test real-time bidding events"""
        self.log("=== Testing Real-Time Bidding ===")
        
        if not self.test_data.get("auction_id"):
            self.log("No auction available", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        
        # Get auction state to find current club
        auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_result:
            self.log("Failed to get auction state", "ERROR")
            return False
        
        current_club = auction_result.get("currentClub")
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
        
        # Create client and join auction
        if not self.create_socket_client("bidding_client"):
            return False
        
        client = self.socket_clients["bidding_client"]
        client.emit('join_auction', {'auctionId': auction_id})
        time.sleep(1)
        
        # Clear events
        self.socket_events["bidding_client"] = []
        
        # Place a bid
        bid_data = {
            "userId": self.test_data["users"][0]["id"],
            "clubId": current_club["id"],
            "amount": 1500000.0  # £1.5m
        }
        
        bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in bid_result:
            self.log("Failed to place bid", "ERROR")
            return False
        
        time.sleep(2)  # Wait for events
        
        # Check if bid events were received
        events = [event[0] for event in self.socket_events["bidding_client"]]
        
        bid_events = ["bid_placed", "bid_update"]
        received_bid_events = [event for event in bid_events if event in events]
        
        if not received_bid_events:
            self.log("No bid events received", "ERROR")
            return False
        
        self.log(f"✅ Real-time bidding working: received {received_bid_events}")
        return True
    
    def test_member_join_events(self) -> bool:
        """Test member_joined events when new users join via API"""
        self.log("=== Testing Member Join Events ===")
        
        if not self.test_data.get("league"):
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        
        # Create client and join league room
        if not self.create_socket_client("member_watcher"):
            return False
        
        client = self.socket_clients["member_watcher"]
        client.emit('join_league', {'leagueId': league_id})
        time.sleep(1)
        
        # Clear events
        self.socket_events["member_watcher"] = []
        
        # Create new user and join league (this should trigger member_joined)
        new_user_data = {
            "name": "New Socket Test Manager",
            "email": "newsocketmanager@test.com"
        }
        
        new_user_result = self.test_api_endpoint("POST", "/users", new_user_data)
        if "error" in new_user_result:
            self.log("Failed to create new user", "ERROR")
            return False
        
        # Join league
        join_data = {
            "userId": new_user_result["id"],
            "inviteToken": self.test_data["league"]["inviteToken"]
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join league", "ERROR")
            return False
        
        time.sleep(2)  # Wait for events
        
        # Check if member_joined and sync_members events were received
        events = [event[0] for event in self.socket_events["member_watcher"]]
        
        expected_events = ["member_joined", "sync_members"]
        received_events = [event for event in expected_events if event in events]
        
        if not received_events:
            self.log("No member join events received", "ERROR")
            return False
        
        self.log(f"✅ Member join events working: received {received_events}")
        return True
    
    def cleanup(self):
        """Clean up socket connections and test data"""
        self.log("=== Cleaning Up ===")
        
        # Disconnect all socket clients
        for client_id, client in self.socket_clients.items():
            try:
                if client.connected:
                    client.disconnect()
                self.log(f"Disconnected client {client_id}")
            except Exception as e:
                self.log(f"Error disconnecting client {client_id}: {str(e)}", "ERROR")
        
        # Clean up test league
        if "league" in self.test_data:
            league_id = self.test_data["league"]["id"]
            result = self.test_api_endpoint("DELETE", f"/leagues/{league_id}")
            if "error" not in result:
                self.log("Test league deleted")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all focused Socket.IO tests"""
        self.log("🚀 Starting Focused Socket.IO Tests")
        
        results = {}
        
        # Setup test data
        if not self.setup_test_data():
            self.log("❌ Test data setup failed", "ERROR")
            return {"setup": False}
        
        results["setup"] = True
        
        # Run test suites
        test_suites = [
            ("socket_connection", self.test_socket_connection),
            ("league_room_joining", self.test_league_room_joining),
            ("auction_room_functionality", self.test_auction_room_functionality),
            ("real_time_bidding", self.test_real_time_bidding),
            ("member_join_events", self.test_member_join_events),
        ]
        
        for test_name, test_func in test_suites:
            try:
                self.log(f"\n--- Running {test_name} ---")
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
    tester = FocusedSocketIOTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("FOCUSED SOCKET.IO TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All focused Socket.IO tests passed!")
        return True
    else:
        print("⚠️  Some focused Socket.IO tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)