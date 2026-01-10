#!/usr/bin/env python3
"""
Socket.IO Refactor Testing - Comprehensive Test Suite
Tests the Socket.IO refactor implementation focusing on:
1. League Room Management (join_league, leave_league, rejoin_rooms, sync_members)
2. Real-Time Member Updates (member_joined events)
3. Auction Room Management (join_auction, sync_state)
4. Critical User-Reported Issues (Enter Auction Room button, bid visibility)
5. Backend Event Emissions (league and auction room events)
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
BASE_URL = "https://bidding-tester.preview.emergentagent.com/api"
SOCKET_URL = "https://bidding-tester.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class SocketIORefactorTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_clients = {}  # Multiple clients for testing
        self.socket_events = {}  # Events per client
        self.test_results = {}
        
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
        for i in range(3):  # Create 3 users for multi-user testing
            user_data = {
                "name": f"Test Manager {i+1}",
                "email": f"manager{i+1}@sockettest.com"
            }
            
            result = self.test_api_endpoint("POST", "/users", user_data)
            if "error" in result:
                self.log(f"Failed to create user {i+1}", "ERROR")
                return False
            
            users.append(result)
            self.log(f"Created user {i+1}: {result['id']}")
        
        self.test_data["users"] = users
        
        # Create league with first user as commissioner
        league_data = {
            "name": "Socket.IO Test League",
            "commissionerId": users[0]["id"],
            "budget": 500000000.0,  # £500m budget
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
        
        # Join league with all users
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
        
        # Seed clubs if needed
        clubs_result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" not in clubs_result:
            self.log("Clubs seeded successfully")
        
        self.log("✅ Test data setup complete")
        return True
    
    def create_socket_client(self, client_id: str, user_id: str) -> bool:
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
                self.log(f"Client {client_id} joined room: {data}")
                self.socket_events[client_id].append(("joined", data))
            
            @client.event
            def room_joined(data):
                self.log(f"Client {client_id} joined league room: {data}")
                self.socket_events[client_id].append(("room_joined", data))
            
            @client.event
            def member_joined(data):
                self.log(f"Client {client_id} received member_joined: {data}")
                self.socket_events[client_id].append(("member_joined", data))
            
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
            def timer_update(data):
                self.log(f"Client {client_id} received timer_update: {data.get('timeRemaining', 0)}s")
                self.socket_events[client_id].append(("timer_update", data))
            
            # Connect
            client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(1)  # Wait for connection
            
            # Check if connected
            if not any(event[0] == "connected" for event in self.socket_events[client_id]):
                self.log(f"Client {client_id} failed to connect", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create client {client_id}: {str(e)}", "ERROR")
            return False
    
    def test_league_room_management(self) -> bool:
        """Test League Room Management: join_league, leave_league, rejoin_rooms, sync_members"""
        self.log("=== Testing League Room Management ===")
        
        if not self.test_data.get("league") or not self.test_data.get("users"):
            self.log("No test data available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        users = self.test_data["users"]
        
        # Create socket clients for first two users
        if not self.create_socket_client("user1", users[0]["id"]):
            return False
        if not self.create_socket_client("user2", users[1]["id"]):
            return False
        
        client1 = self.socket_clients["user1"]
        client2 = self.socket_clients["user2"]
        
        # Test 1: join_league event
        self.log("Testing join_league event...")
        client1.emit('join_league', {'leagueId': league_id})
        time.sleep(1)
        
        # Check if user1 joined league room
        user1_events = [event[0] for event in self.socket_events["user1"]]
        if "room_joined" not in user1_events:
            self.log("User1 failed to join league room", "ERROR")
            return False
        
        self.log("✅ join_league event working")
        
        # Test 2: Real-time member updates when second user joins
        self.log("Testing real-time member updates...")
        
        # Clear events
        self.socket_events["user1"] = []
        self.socket_events["user2"] = []
        
        # User2 joins league room
        client2.emit('join_league', {'leagueId': league_id})
        time.sleep(2)  # Wait for events to propagate
        
        # Check if user1 received member updates
        user1_events = [event[0] for event in self.socket_events["user1"]]
        user2_events = [event[0] for event in self.socket_events["user2"]]
        
        # User2 should receive sync_members when joining
        if "sync_members" not in user2_events:
            self.log("User2 did not receive sync_members on join", "ERROR")
            return False
        
        self.log("✅ Real-time member updates working")
        
        # Test 3: sync_members event broadcasts to all users
        self.log("Testing sync_members broadcast...")
        
        # Trigger a new member join (user3)
        if not self.create_socket_client("user3", users[2]["id"]):
            return False
        
        client3 = self.socket_clients["user3"]
        
        # Clear events
        self.socket_events["user1"] = []
        self.socket_events["user2"] = []
        self.socket_events["user3"] = []
        
        # User3 joins
        client3.emit('join_league', {'leagueId': league_id})
        time.sleep(2)
        
        # Check if all users received sync_members
        for user_id in ["user1", "user2", "user3"]:
            events = [event[0] for event in self.socket_events[user_id]]
            if "sync_members" not in events:
                self.log(f"{user_id} did not receive sync_members broadcast", "ERROR")
                return False
        
        self.log("✅ sync_members broadcasts to all users in room")
        
        # Test 4: leave_league event
        self.log("Testing leave_league event...")
        client3.emit('leave_league', {'leagueId': league_id})
        time.sleep(1)
        
        # Test 5: rejoin_rooms handler (simulate reconnect)
        self.log("Testing rejoin_rooms handler...")
        
        # Disconnect and reconnect user1
        client1.disconnect()
        time.sleep(1)
        
        # Reconnect
        client1.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
        time.sleep(1)
        
        # Send rejoin_rooms event
        client1.emit('rejoin_rooms', {
            'leagueId': league_id,
            'auctionId': None  # No auction yet
        })
        time.sleep(1)
        
        # Check if rejoined successfully
        recent_events = [event[0] for event in self.socket_events["user1"][-5:]]
        if "joined" not in recent_events and "sync_members" not in recent_events:
            self.log("rejoin_rooms handler not working properly", "ERROR")
            return False
        
        self.log("✅ rejoin_rooms handler working")
        
        self.log("✅ League Room Management tests passed")
        return True
    
    def test_auction_room_management(self) -> bool:
        """Test Auction Room Management: join_auction, sync_state, room isolation"""
        self.log("=== Testing Auction Room Management ===")
        
        if not self.test_data.get("league"):
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        
        # Start auction
        self.log("Starting auction...")
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Failed to start auction", "ERROR")
            return False
        
        auction_id = result["auctionId"]
        self.test_data["auction_id"] = auction_id
        self.log(f"Started auction: {auction_id}")
        
        # Test 1: join_auction event
        self.log("Testing join_auction event...")
        
        if "user1" not in self.socket_clients:
            if not self.create_socket_client("user1", self.test_data["users"][0]["id"]):
                return False
        
        client1 = self.socket_clients["user1"]
        
        # Clear events
        self.socket_events["user1"] = []
        
        # Join auction room
        client1.emit('join_auction', {'auctionId': auction_id})
        time.sleep(2)
        
        # Check if joined auction room and received sync_state
        user1_events = [event[0] for event in self.socket_events["user1"]]
        
        if "joined" not in user1_events:
            self.log("Failed to join auction room", "ERROR")
            return False
        
        if "sync_state" not in user1_events:
            self.log("Did not receive sync_state on auction join", "ERROR")
            return False
        
        self.log("✅ join_auction event working")
        
        # Test 2: sync_state provides correct initial state
        self.log("Testing sync_state initial state...")
        
        sync_state_event = next((event[1] for event in self.socket_events["user1"] if event[0] == "sync_state"), None)
        if not sync_state_event:
            self.log("No sync_state event data", "ERROR")
            return False
        
        # Check if sync_state contains expected auction data
        required_fields = ["auction", "currentClub", "participants"]
        for field in required_fields:
            if field not in sync_state_event:
                self.log(f"sync_state missing field: {field}", "ERROR")
                return False
        
        self.log("✅ sync_state provides correct initial state")
        
        # Test 3: Auction room isolation (events only go to auction participants)
        self.log("Testing auction room isolation...")
        
        # Create another client that joins league but not auction
        if not self.create_socket_client("observer", self.test_data["users"][2]["id"]):
            return False
        
        observer_client = self.socket_clients["observer"]
        
        # Observer joins league room only
        observer_client.emit('join_league', {'leagueId': league_id})
        time.sleep(1)
        
        # Clear events
        self.socket_events["user1"] = []
        self.socket_events["observer"] = []
        
        # Place a bid to trigger auction-specific events
        bid_data = {
            "userId": self.test_data["users"][0]["id"],
            "clubId": sync_state_event["currentClub"]["id"],
            "amount": 1500000.0  # £1.5m
        }
        
        bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in bid_result:
            self.log("Failed to place test bid", "ERROR")
            return False
        
        time.sleep(2)  # Wait for events
        
        # Check events
        user1_events = [event[0] for event in self.socket_events["user1"]]
        observer_events = [event[0] for event in self.socket_events["observer"]]
        
        # User1 (in auction room) should receive bid events
        if "bid_placed" not in user1_events and "bid_update" not in user1_events:
            self.log("Auction participant did not receive bid events", "ERROR")
            return False
        
        # Observer (not in auction room) should NOT receive auction-specific events
        auction_events = ["bid_placed", "bid_update", "sync_state"]
        observer_auction_events = [event for event in observer_events if event in auction_events]
        
        if observer_auction_events:
            self.log(f"Observer received auction events they shouldn't: {observer_auction_events}", "ERROR")
            return False
        
        self.log("✅ Auction room isolation working")
        
        # Test 4: Multiple users in auction room see bid visibility
        self.log("Testing bid visibility for all auction users...")
        
        # Add second user to auction
        if "user2" not in self.socket_clients:
            if not self.create_socket_client("user2", self.test_data["users"][1]["id"]):
                return False
        
        client2 = self.socket_clients["user2"]
        client2.emit('join_auction', {'auctionId': auction_id})
        time.sleep(1)
        
        # Clear events
        self.socket_events["user1"] = []
        self.socket_events["user2"] = []
        
        # Place another bid
        bid_data["amount"] = 2000000.0  # £2m
        bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in bid_result:
            self.log("Failed to place second test bid", "ERROR")
            return False
        
        time.sleep(2)
        
        # Both users should see the bid
        user1_events = [event[0] for event in self.socket_events["user1"]]
        user2_events = [event[0] for event in self.socket_events["user2"]]
        
        bid_events = ["bid_placed", "bid_update"]
        user1_has_bid = any(event in user1_events for event in bid_events)
        user2_has_bid = any(event in user2_events for event in bid_events)
        
        if not user1_has_bid:
            self.log("User1 did not see bid event", "ERROR")
            return False
        
        if not user2_has_bid:
            self.log("User2 did not see bid event", "ERROR")
            return False
        
        self.log("✅ Bid visibility working for all auction users")
        
        self.log("✅ Auction Room Management tests passed")
        return True
    
    def test_backend_event_emissions(self) -> bool:
        """Test Backend Event Emissions to correct rooms"""
        self.log("=== Testing Backend Event Emissions ===")
        
        if not self.test_data.get("league") or not self.test_data.get("auction_id"):
            self.log("No league or auction available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        auction_id = self.test_data["auction_id"]
        
        # Ensure we have clients in both league and auction rooms
        if "user1" not in self.socket_clients:
            if not self.create_socket_client("user1", self.test_data["users"][0]["id"]):
                return False
        
        client1 = self.socket_clients["user1"]
        
        # Join both rooms
        client1.emit('join_league', {'leagueId': league_id})
        time.sleep(1)
        client1.emit('join_auction', {'auctionId': auction_id})
        time.sleep(1)
        
        # Test 1: Backend emits to league:{leagueId} rooms
        self.log("Testing backend emissions to league rooms...")
        
        # Clear events
        self.socket_events["user1"] = []
        
        # Trigger a league-level event (new member joining)
        # Create a new user and join league
        new_user_data = {
            "name": "New Test Manager",
            "email": "newmanager@sockettest.com"
        }
        
        new_user_result = self.test_api_endpoint("POST", "/users", new_user_data)
        if "error" in new_user_result:
            self.log("Failed to create new user for league event test", "ERROR")
            return False
        
        # Join league (this should trigger member_joined and sync_members events)
        join_data = {
            "userId": new_user_result["id"],
            "inviteToken": self.test_data["league"]["inviteToken"]
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join league for event test", "ERROR")
            return False
        
        time.sleep(2)  # Wait for events
        
        # Check if existing league members received the events
        user1_events = [event[0] for event in self.socket_events["user1"]]
        
        expected_league_events = ["member_joined", "sync_members"]
        received_league_events = [event for event in expected_league_events if event in user1_events]
        
        if not received_league_events:
            self.log("No league-level events received", "ERROR")
            return False
        
        self.log(f"✅ Backend emits to league rooms: {received_league_events}")
        
        # Test 2: Backend emits to auction:{auctionId} rooms
        self.log("Testing backend emissions to auction rooms...")
        
        # Clear events
        self.socket_events["user1"] = []
        
        # Place a bid to trigger auction-level events
        current_club_id = None
        
        # Get current auction state to find current club
        auction_result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" not in auction_result:
            current_club = auction_result.get("currentClub")
            if current_club:
                current_club_id = current_club["id"]
        
        if not current_club_id:
            self.log("No current club available for bid test", "ERROR")
            return False
        
        # Place bid
        bid_data = {
            "userId": self.test_data["users"][0]["id"],
            "clubId": current_club_id,
            "amount": 2500000.0  # £2.5m
        }
        
        bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in bid_result:
            self.log("Failed to place bid for auction event test", "ERROR")
            return False
        
        time.sleep(2)
        
        # Check if auction events were received
        user1_events = [event[0] for event in self.socket_events["user1"]]
        
        expected_auction_events = ["bid_placed", "bid_update"]
        received_auction_events = [event for event in expected_auction_events if event in user1_events]
        
        if not received_auction_events:
            self.log("No auction-level events received", "ERROR")
            return False
        
        self.log(f"✅ Backend emits to auction rooms: {received_auction_events}")
        
        self.log("✅ Backend Event Emissions tests passed")
        return True
    
    def test_critical_user_issues(self) -> bool:
        """Test Critical User-Reported Issues"""
        self.log("=== Testing Critical User-Reported Issues ===")
        
        # This test focuses on the backend Socket.IO functionality
        # The "Enter Auction Room" button and UI updates are frontend issues
        # but we can test the backend events that should trigger them
        
        if not self.test_data.get("league"):
            self.log("No league available", "ERROR")
            return False
        
        league_id = self.test_data["league"]["id"]
        
        # Test 1: Auction started event should be emitted to league room
        self.log("Testing auction_started event emission...")
        
        # Create a fresh league for this test
        fresh_league_data = {
            "name": "Fresh Socket Test League",
            "commissionerId": self.test_data["users"][0]["id"],
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "football"
        }
        
        fresh_league_result = self.test_api_endpoint("POST", "/leagues", fresh_league_data)
        if "error" in fresh_league_result:
            self.log("Failed to create fresh league", "ERROR")
            return False
        
        fresh_league_id = fresh_league_result["id"]
        
        # Join the fresh league
        join_data = {
            "userId": self.test_data["users"][0]["id"],
            "inviteToken": fresh_league_result["inviteToken"]
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{fresh_league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join fresh league", "ERROR")
            return False
        
        # Create client and join league room
        if not self.create_socket_client("fresh_user", self.test_data["users"][0]["id"]):
            return False
        
        fresh_client = self.socket_clients["fresh_user"]
        fresh_client.emit('join_league', {'leagueId': fresh_league_id})
        time.sleep(1)
        
        # Clear events
        self.socket_events["fresh_user"] = []
        
        # Start auction (this should emit auction_started to league room)
        auction_result = self.test_api_endpoint("POST", f"/leagues/{fresh_league_id}/auction/start")
        if "error" in auction_result:
            self.log("Failed to start fresh auction", "ERROR")
            return False
        
        time.sleep(2)  # Wait for events
        
        # Check if auction_started event was received
        fresh_events = [event[0] for event in self.socket_events["fresh_user"]]
        
        if "auction_started" not in fresh_events:
            self.log("auction_started event not received in league room", "ERROR")
            return False
        
        self.log("✅ auction_started event emitted to league room")
        
        # Test 2: Real-time bid visibility (all users see bids immediately)
        self.log("Testing real-time bid visibility...")
        
        fresh_auction_id = auction_result["auctionId"]
        
        # Join auction room
        fresh_client.emit('join_auction', {'auctionId': fresh_auction_id})
        time.sleep(1)
        
        # Get current club for bidding
        auction_state = self.test_api_endpoint("GET", f"/auction/{fresh_auction_id}")
        if "error" in auction_state:
            self.log("Failed to get auction state", "ERROR")
            return False
        
        current_club = auction_state.get("currentClub")
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
        
        # Clear events
        self.socket_events["fresh_user"] = []
        
        # Place multiple bids rapidly to test real-time updates
        bid_amounts = [1000000.0, 1200000.0, 1500000.0]  # £1m, £1.2m, £1.5m
        
        for amount in bid_amounts:
            bid_data = {
                "userId": self.test_data["users"][0]["id"],
                "clubId": current_club["id"],
                "amount": amount
            }
            
            bid_result = self.test_api_endpoint("POST", f"/auction/{fresh_auction_id}/bid", bid_data)
            if "error" in bid_result:
                self.log(f"Failed to place bid of £{amount:,.0f}", "ERROR")
                return False
            
            time.sleep(0.5)  # Small delay between bids
        
        time.sleep(2)  # Wait for all events
        
        # Count bid events received
        fresh_events = [event[0] for event in self.socket_events["fresh_user"]]
        bid_event_count = fresh_events.count("bid_placed") + fresh_events.count("bid_update")
        
        if bid_event_count < len(bid_amounts):
            self.log(f"Not all bid events received: expected {len(bid_amounts)}, got {bid_event_count}", "ERROR")
            return False
        
        self.log(f"✅ Real-time bid visibility working: {bid_event_count} bid events received")
        
        self.log("✅ Critical User-Reported Issues tests passed")
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
        
        # Clean up test leagues
        if "league" in self.test_data:
            league_id = self.test_data["league"]["id"]
            result = self.test_api_endpoint("DELETE", f"/leagues/{league_id}")
            if "error" not in result:
                self.log("Test league deleted")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Socket.IO refactor tests"""
        self.log("🚀 Starting Socket.IO Refactor Tests")
        
        results = {}
        
        # Setup test data
        if not self.setup_test_data():
            self.log("❌ Test data setup failed", "ERROR")
            return {"setup": False}
        
        results["setup"] = True
        
        # Run test suites
        test_suites = [
            ("league_room_management", self.test_league_room_management),
            ("auction_room_management", self.test_auction_room_management),
            ("backend_event_emissions", self.test_backend_event_emissions),
            ("critical_user_issues", self.test_critical_user_issues),
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
    tester = SocketIORefactorTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("SOCKET.IO REFACTOR TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Socket.IO refactor tests passed!")
        return True
    else:
        print("⚠️  Some Socket.IO refactor tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)