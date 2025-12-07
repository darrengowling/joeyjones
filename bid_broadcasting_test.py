#!/usr/bin/env python3
"""
Bid Broadcasting System Test with Monotonic Sequence Numbers
Tests robust bid broadcasting system with sequence numbers for real-time auction synchronization
"""

import asyncio
import json
import requests
import socketio
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "https://prod-auction-fix.preview.emergentagent.com/api"
SOCKET_URL = "https://prod-auction-fix.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class BidBroadcastingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_clients = []
        self.received_events = []
        self.bid_sequences = []
        self.sync_states = []
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
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
    
    def setup_test_environment(self) -> bool:
        """Set up users, league, and auction for testing"""
        self.log("=== Setting Up Test Environment ===")
        
        # Create two test users
        users = []
        for i in range(2):
            user_data = {
                "name": f"Bidder {i+1}",
                "email": f"bidder{i+1}@test.com"
            }
            
            result = self.test_api_endpoint("POST", "/users", user_data)
            if "error" in result:
                self.log(f"Failed to create user {i+1}", "ERROR")
                return False
                
            users.append(result)
            self.log(f"Created user: {result['id']}")
        
        self.test_data["users"] = users
        
        # Seed clubs
        result = self.test_api_endpoint("POST", "/clubs/seed")
        if "error" in result:
            self.log("Failed to seed clubs", "ERROR")
            return False
        
        # Create league
        league_data = {
            "name": "Bid Broadcasting Test League",
            "commissionerId": users[0]["id"],
            "budget": 100000000.0,  # £100m budget
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 5,
            "timerSeconds": 30,
            "antiSnipeSeconds": 10
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Failed to create league", "ERROR")
            return False
            
        league_id = result["id"]
        invite_token = result["inviteToken"]
        self.test_data["league_id"] = league_id
        self.test_data["invite_token"] = invite_token
        self.log(f"Created league: {league_id}")
        
        # Join both users to league
        for user in users:
            join_data = {
                "userId": user["id"],
                "inviteToken": invite_token
            }
            
            result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
            if "error" in result:
                self.log(f"Failed to join user {user['id']} to league", "ERROR")
                return False
        
        # Start auction
        result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in result:
            self.log("Failed to start auction", "ERROR")
            return False
            
        auction_id = result["auctionId"]
        self.test_data["auction_id"] = auction_id
        self.log(f"Started auction: {auction_id}")
        
        # Get auction details
        result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in result:
            self.log("Failed to get auction details", "ERROR")
            return False
            
        current_club = result.get("currentClub")
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
            
        self.test_data["current_club"] = current_club
        self.log(f"Current club: {current_club.get('name')}")
        
        self.log("✅ Test environment setup complete")
        return True
    
    def create_socket_client(self, user_id: str, client_name: str) -> socketio.Client:
        """Create and configure a Socket.IO client"""
        client = socketio.Client(logger=False, engineio_logger=False)
        
        # Track events for this client
        client_events = []
        
        @client.event
        def connect():
            self.log(f"Socket.IO connected: {client_name}")
            client_events.append({"event": "connected", "timestamp": time.time()})
        
        @client.event
        def disconnect():
            self.log(f"Socket.IO disconnected: {client_name}")
            client_events.append({"event": "disconnected", "timestamp": time.time()})
        
        @client.event
        def joined(data):
            self.log(f"{client_name} joined auction room: {data}")
            client_events.append({"event": "joined", "data": data, "timestamp": time.time()})
        
        @client.event
        def sync_state(data):
            self.log(f"{client_name} received sync_state: seq={data.get('seq', 'N/A')}")
            client_events.append({"event": "sync_state", "data": data, "timestamp": time.time()})
            self.sync_states.append({
                "client": client_name,
                "data": data,
                "timestamp": time.time()
            })
        
        @client.event
        def bid_update(data):
            seq = data.get('seq', 'N/A')
            amount = data.get('amount', 'N/A')
            bidder = data.get('bidder', {}).get('displayName', 'Unknown')
            server_time = data.get('serverTime', 'N/A')
            
            self.log(f"{client_name} received bid_update: seq={seq}, amount=£{amount:,}, bidder={bidder}")
            
            event_data = {
                "event": "bid_update",
                "client": client_name,
                "data": data,
                "timestamp": time.time()
            }
            client_events.append(event_data)
            self.received_events.append(event_data)
            
            # Track sequence numbers
            if seq != 'N/A':
                self.bid_sequences.append({
                    "client": client_name,
                    "seq": seq,
                    "amount": amount,
                    "bidder": bidder,
                    "server_time": server_time,
                    "received_at": time.time()
                })
        
        @client.event
        def bid_placed(data):
            self.log(f"{client_name} received bid_placed (legacy)")
            client_events.append({"event": "bid_placed", "data": data, "timestamp": time.time()})
        
        # Store events reference on client
        client.events_received = client_events
        
        return client
    
    def test_monotonic_sequence_numbers(self) -> bool:
        """Test 1: Monotonic Sequence Number Test"""
        self.log("=== Test 1: Monotonic Sequence Number Test ===")
        
        if "auction_id" not in self.test_data or "users" not in self.test_data:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user = self.test_data["users"][0]
        current_club = self.test_data["current_club"]
        
        # Create socket client to receive bid_update events
        client = self.create_socket_client(user["id"], "Monotonic Test User")
        
        try:
            # Connect and join auction
            client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            client.emit('join_auction', {'auctionId': auction_id})
            time.sleep(2)
            
            # Clear sequence tracking
            self.bid_sequences = []
            
            # Place multiple bids in succession
            bid_amounts = [1000000, 1500000, 2000000, 2500000, 3000000]  # £1M to £3M
            
            for i, amount in enumerate(bid_amounts):
                bid_data = {
                    "userId": user["id"],
                    "clubId": current_club["id"],
                    "amount": amount
                }
                
                result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
                if "error" in result:
                    self.log(f"Failed to place bid {i+1}: {result}", "ERROR")
                    return False
                
                self.log(f"Placed bid {i+1}: £{amount:,}")
                time.sleep(0.2)  # Small delay between bids
            
            # Wait for all events to be processed
            time.sleep(3)
            
            # Verify sequence numbers are monotonic
            if len(self.bid_sequences) == 0:
                self.log("No bid sequences recorded", "ERROR")
                return False
            
            sequences = [entry["seq"] for entry in self.bid_sequences]
            self.log(f"Recorded sequences: {sequences}")
            
            # Check if sequences are strictly increasing
            for i in range(1, len(sequences)):
                if sequences[i] <= sequences[i-1]:
                    self.log(f"Sequence not monotonic: {sequences[i-1]} -> {sequences[i]}", "ERROR")
                    return False
            
            self.log("✅ Sequence numbers are strictly monotonic")
            return True
            
        finally:
            if client.connected:
                client.disconnect()
    
    def test_bid_update_event_broadcast(self) -> bool:
        """Test 2: Bid Update Event Broadcast"""
        self.log("=== Test 2: Bid Update Event Broadcast ===")
        
        if "auction_id" not in self.test_data:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        
        # Create two socket clients
        user_a = self.test_data["users"][0]
        user_b = self.test_data["users"][1]
        
        client_a = self.create_socket_client(user_a["id"], "User A")
        client_b = self.create_socket_client(user_b["id"], "User B")
        
        try:
            # Connect both clients
            client_a.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            client_b.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            
            time.sleep(2)  # Wait for connections
            
            # Join auction room
            client_a.emit('join_auction', {'auctionId': auction_id})
            client_b.emit('join_auction', {'auctionId': auction_id})
            
            time.sleep(2)  # Wait for room joins
            
            # Clear events
            self.received_events = []
            
            # User A places a bid
            bid_data = {
                "userId": user_a["id"],
                "clubId": self.test_data["current_club"]["id"],
                "amount": 4000000  # £4M
            }
            
            result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in result:
                self.log(f"Failed to place bid: {result}", "ERROR")
                return False
            
            self.log("User A placed bid: £4,000,000")
            
            # Wait for events
            time.sleep(3)
            
            # Verify both clients received bid_update event
            client_a_events = [e for e in self.received_events if e["client"] == "User A" and e["event"] == "bid_update"]
            client_b_events = [e for e in self.received_events if e["client"] == "User B" and e["event"] == "bid_update"]
            
            if len(client_a_events) == 0:
                self.log("User A did not receive bid_update event", "ERROR")
                return False
            
            if len(client_b_events) == 0:
                self.log("User B did not receive bid_update event", "ERROR")
                return False
            
            # Verify event structure
            event_data = client_a_events[0]["data"]
            required_fields = ["lotId", "amount", "bidder", "seq", "serverTime"]
            
            for field in required_fields:
                if field not in event_data:
                    self.log(f"Missing required field in bid_update: {field}", "ERROR")
                    return False
            
            # Verify bidder structure
            bidder = event_data.get("bidder", {})
            if "userId" not in bidder or "displayName" not in bidder:
                self.log("Invalid bidder structure in bid_update", "ERROR")
                return False
            
            self.log("✅ bid_update events broadcast to all users with correct structure")
            
        finally:
            # Cleanup connections
            if client_a.connected:
                client_a.disconnect()
            if client_b.connected:
                client_b.disconnect()
        
        return True
    
    def test_sync_state_initialization(self) -> bool:
        """Test 3: Sync State Initialization"""
        self.log("=== Test 3: Sync State Initialization ===")
        
        if "auction_id" not in self.test_data:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        
        # Place a bid first to establish state
        user = self.test_data["users"][0]
        bid_data = {
            "userId": user["id"],
            "clubId": self.test_data["current_club"]["id"],
            "amount": 5000000  # £5M
        }
        
        result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            self.log(f"Failed to place initial bid: {result}", "ERROR")
            return False
        
        time.sleep(1)  # Wait for bid to process
        
        # Create new client (simulating user joining mid-bidding)
        client = self.create_socket_client(user["id"], "New User")
        
        try:
            # Clear sync states
            self.sync_states = []
            
            # Connect and join auction
            client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            client.emit('join_auction', {'auctionId': auction_id})
            time.sleep(3)  # Wait for sync_state
            
            # Verify sync_state was received
            if len(self.sync_states) == 0:
                self.log("No sync_state event received", "ERROR")
                return False
            
            sync_data = self.sync_states[0]["data"]
            
            # Verify sync_state structure
            required_fields = ["currentBid", "currentBidder", "seq"]
            for field in required_fields:
                if field not in sync_data:
                    self.log(f"Missing required field in sync_state: {field}", "ERROR")
                    return False
            
            # Verify current bid matches what we placed
            if sync_data["currentBid"] != 5000000:
                self.log(f"sync_state currentBid mismatch: expected 5000000, got {sync_data['currentBid']}", "ERROR")
                return False
            
            # Verify current bidder
            current_bidder = sync_data.get("currentBidder", {})
            if current_bidder.get("userId") != user["id"]:
                self.log("sync_state currentBidder mismatch", "ERROR")
                return False
            
            # Verify sequence number is present
            if not isinstance(sync_data.get("seq"), int) or sync_data["seq"] <= 0:
                self.log(f"Invalid sequence number in sync_state: {sync_data.get('seq')}", "ERROR")
                return False
            
            self.log("✅ sync_state initialization working correctly")
            
        finally:
            if client.connected:
                client.disconnect()
        
        return True
    
    def test_rapid_fire_bidding(self) -> bool:
        """Test 4: Rapid Fire Bid Test (Stress Test)"""
        self.log("=== Test 4: Rapid Fire Bid Test (Stress Test) ===")
        
        if "auction_id" not in self.test_data or len(self.test_data["users"]) < 2:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_a = self.test_data["users"][0]
        user_b = self.test_data["users"][1]
        current_club = self.test_data["current_club"]
        
        # Create socket clients for both users
        client_a = self.create_socket_client(user_a["id"], "Rapid User A")
        client_b = self.create_socket_client(user_b["id"], "Rapid User B")
        
        try:
            # Connect both clients
            client_a.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            client_b.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            # Join auction rooms
            client_a.emit('join_auction', {'auctionId': auction_id})
            client_b.emit('join_auction', {'auctionId': auction_id})
            time.sleep(2)
            
            # Clear tracking
            self.received_events = []
            self.bid_sequences = []
            
            # Rapid fire bidding function
            def place_rapid_bids(user, base_amount, count, delay=0.2):
                for i in range(count):
                    bid_data = {
                        "userId": user["id"],
                        "clubId": current_club["id"],
                        "amount": base_amount + (i * 100000)  # Increment by £100k each time
                    }
                    
                    result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
                    if "error" not in result:
                        self.log(f"{user['name']} placed rapid bid {i+1}: £{bid_data['amount']:,}")
                    
                    time.sleep(delay)
            
            # Start rapid bidding from both users simultaneously
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(place_rapid_bids, user_a, 6000000, 3, 0.3)  # User A: £6M, £6.1M, £6.2M
                future_b = executor.submit(place_rapid_bids, user_b, 6500000, 3, 0.3)  # User B: £6.5M, £6.6M, £6.7M
                
                # Wait for both to complete
                future_a.result()
                future_b.result()
            
            # Wait for all events to be processed
            time.sleep(5)
            
            # Verify all bid_update events were delivered
            total_bid_updates = len([e for e in self.received_events if e["event"] == "bid_update"])
            expected_bids = 6  # 3 from each user
            
            if total_bid_updates < expected_bids:
                self.log(f"Not all bid_update events delivered: got {total_bid_updates}, expected {expected_bids}", "ERROR")
                return False
            
            # Verify sequence numbers are still monotonic (check from one client only)
            client_a_sequences = [entry["seq"] for entry in self.bid_sequences if entry["client"] == "Rapid User A"]
            self.log(f"Rapid fire sequences received by User A: {client_a_sequences}")
            
            # Check if sequences are monotonic in the order they were received
            for i in range(1, len(client_a_sequences)):
                if client_a_sequences[i] <= client_a_sequences[i-1]:
                    self.log(f"Sequence not monotonic after rapid bidding: {client_a_sequences[i-1]} -> {client_a_sequences[i]}", "ERROR")
                    return False
            
            # Verify final state is identical for both users
            client_a_final = [e for e in self.received_events if e["client"] == "Rapid User A" and e["event"] == "bid_update"]
            client_b_final = [e for e in self.received_events if e["client"] == "Rapid User B" and e["event"] == "bid_update"]
            
            if len(client_a_final) != len(client_b_final):
                self.log(f"Different number of events received: A={len(client_a_final)}, B={len(client_b_final)}", "ERROR")
                return False
            
            # Check final bid amounts match
            if len(client_a_final) > 0 and len(client_b_final) > 0:
                final_a = client_a_final[-1]["data"]["amount"]
                final_b = client_b_final[-1]["data"]["amount"]
                
                if final_a != final_b:
                    self.log(f"Final bid amounts don't match: A=£{final_a:,}, B=£{final_b:,}", "ERROR")
                    return False
            
            self.log("✅ Rapid fire bidding test passed - all events delivered, sequences monotonic, final state identical")
            
        finally:
            if client_a.connected:
                client_a.disconnect()
            if client_b.connected:
                client_b.disconnect()
        
        return True
    
    def test_sequence_number_consistency(self) -> bool:
        """Test 5: Sequence Number Consistency"""
        self.log("=== Test 5: Sequence Number Consistency ===")
        
        if "auction_id" not in self.test_data:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user = self.test_data["users"][0]
        current_club = self.test_data["current_club"]
        
        # Create socket client to receive bid_update events
        client = self.create_socket_client(user["id"], "Consistency Test User")
        
        try:
            # Connect and join auction
            client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            client.emit('join_auction', {'auctionId': auction_id})
            time.sleep(2)
            
            # Clear tracking
            self.bid_sequences = []
            
            # Place 10 bids sequentially
            for i in range(10):
                bid_data = {
                    "userId": user["id"],
                    "clubId": current_club["id"],
                    "amount": 10000000 + (i * 100000)  # £10M to £10.9M
                }
                
                result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
                if "error" in result:
                    self.log(f"Failed to place bid {i+1}: {result}", "ERROR")
                    return False
                
                time.sleep(0.2)  # Small delay between bids
            
            # Wait for all events
            time.sleep(3)
            
            # Verify we got 10 sequence numbers
            if len(self.bid_sequences) < 10:
                self.log(f"Expected 10 sequences, got {len(self.bid_sequences)}", "ERROR")
                return False
            
            # Get the last 10 sequences
            recent_sequences = [entry["seq"] for entry in self.bid_sequences[-10:]]
            
            # Verify incremental sequence: should be consecutive
            for i in range(1, len(recent_sequences)):
                expected = recent_sequences[i-1] + 1
                actual = recent_sequences[i]
                if actual != expected:
                    self.log(f"Sequence gap detected: expected {expected}, got {actual}", "ERROR")
                    return False
            
            # Verify no duplicates
            if len(set(recent_sequences)) != len(recent_sequences):
                self.log("Duplicate sequence numbers detected", "ERROR")
                return False
            
            # Get auction to verify bidSequence matches last bid seq
            result = self.test_api_endpoint("GET", f"/auction/{auction_id}")
            if "error" in result:
                self.log("Failed to get auction for sequence verification", "ERROR")
                return False
            
            auction_data = result.get("auction", {})
            auction_bid_sequence = auction_data.get("bidSequence")
            
            if auction_bid_sequence != recent_sequences[-1]:
                self.log(f"Auction bidSequence mismatch: auction={auction_bid_sequence}, last_event={recent_sequences[-1]}", "ERROR")
                return False
            
            self.log("✅ Sequence number consistency verified - incremental, no gaps, no duplicates")
            return True
            
        finally:
            if client.connected:
                client.disconnect()
    
    def test_multi_user_state_synchronization(self) -> bool:
        """Test 6: Multi-User State Synchronization"""
        self.log("=== Test 6: Multi-User State Synchronization ===")
        
        if "auction_id" not in self.test_data or len(self.test_data["users"]) < 2:
            self.log("Test environment not ready", "ERROR")
            return False
        
        auction_id = self.test_data["auction_id"]
        user_a = self.test_data["users"][0]
        user_b = self.test_data["users"][1]
        current_club = self.test_data["current_club"]
        
        # Create socket clients
        client_a = self.create_socket_client(user_a["id"], "Sync User A")
        client_b = self.create_socket_client(user_b["id"], "Sync User B")
        
        try:
            # Connect both clients
            client_a.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            client_b.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            # Join auction rooms
            client_a.emit('join_auction', {'auctionId': auction_id})
            client_b.emit('join_auction', {'auctionId': auction_id})
            time.sleep(2)
            
            # Clear tracking
            self.received_events = []
            
            # Scenario: User A bids £15m (seq=1), User B bids £20m (seq=2), User A bids £25m (seq=3)
            
            # User A bids £15m
            bid_data_a1 = {
                "userId": user_a["id"],
                "clubId": current_club["id"],
                "amount": 15000000
            }
            
            result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data_a1)
            if "error" in result:
                self.log("Failed to place User A first bid", "ERROR")
                return False
            
            time.sleep(1)
            
            # User B bids £20m
            bid_data_b = {
                "userId": user_b["id"],
                "clubId": current_club["id"],
                "amount": 20000000
            }
            
            result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data_b)
            if "error" in result:
                self.log("Failed to place User B bid", "ERROR")
                return False
            
            time.sleep(1)
            
            # User A bids £25m
            bid_data_a2 = {
                "userId": user_a["id"],
                "clubId": current_club["id"],
                "amount": 25000000
            }
            
            result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data_a2)
            if "error" in result:
                self.log("Failed to place User A second bid", "ERROR")
                return False
            
            # Wait for all events
            time.sleep(3)
            
            # Verify both users received all 3 bid_update events
            user_a_events = [e for e in self.received_events if e["client"] == "Sync User A" and e["event"] == "bid_update"]
            user_b_events = [e for e in self.received_events if e["client"] == "Sync User B" and e["event"] == "bid_update"]
            
            if len(user_a_events) < 3:
                self.log(f"User A didn't receive all events: got {len(user_a_events)}, expected 3", "ERROR")
                return False
            
            if len(user_b_events) < 3:
                self.log(f"User B didn't receive all events: got {len(user_b_events)}, expected 3", "ERROR")
                return False
            
            # Verify final state is identical
            final_a = user_a_events[-1]["data"]
            final_b = user_b_events[-1]["data"]
            
            # Check final amount
            if final_a["amount"] != final_b["amount"]:
                self.log(f"Final amounts don't match: A={final_a['amount']}, B={final_b['amount']}", "ERROR")
                return False
            
            # Check final bidder
            if final_a["bidder"]["userId"] != final_b["bidder"]["userId"]:
                self.log("Final bidders don't match", "ERROR")
                return False
            
            # Check final sequence
            if final_a["seq"] != final_b["seq"]:
                self.log(f"Final sequences don't match: A={final_a['seq']}, B={final_b['seq']}", "ERROR")
                return False
            
            # Verify final state matches expected: £25m by User A
            if final_a["amount"] != 25000000:
                self.log(f"Final amount incorrect: expected 25000000, got {final_a['amount']}", "ERROR")
                return False
            
            if final_a["bidder"]["userId"] != user_a["id"]:
                self.log(f"Final bidder incorrect: expected {user_a['id']}, got {final_a['bidder']['userId']}", "ERROR")
                return False
            
            self.log("✅ Multi-user state synchronization verified - both users see identical final state")
            
        finally:
            if client_a.connected:
                client_a.disconnect()
            if client_b.connected:
                client_b.disconnect()
        
        return True
    
    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Disconnect any remaining socket clients
        for client in self.socket_clients:
            if client.connected:
                client.disconnect()
        
        # Delete test league
        if "league_id" in self.test_data and "users" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}?user_id={self.test_data['users'][0]['id']}")
            if "error" not in result:
                self.log("Test league deleted")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all bid broadcasting tests"""
        self.log("🚀 Starting Bid Broadcasting System Tests")
        
        results = {}
        
        # Setup test environment
        if not self.setup_test_environment():
            self.log("❌ Failed to setup test environment", "ERROR")
            return {"setup": False}
        
        results["setup"] = True
        
        # Run all test scenarios
        test_scenarios = [
            ("monotonic_sequence_numbers", self.test_monotonic_sequence_numbers),
            ("bid_update_event_broadcast", self.test_bid_update_event_broadcast),
            ("sync_state_initialization", self.test_sync_state_initialization),
            ("rapid_fire_bidding", self.test_rapid_fire_bidding),
            ("sequence_number_consistency", self.test_sequence_number_consistency),
            ("multi_user_state_synchronization", self.test_multi_user_state_synchronization),
        ]
        
        for test_name, test_func in test_scenarios:
            try:
                self.log(f"\n--- Running {test_name} ---")
                results[test_name] = test_func()
                if results[test_name]:
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = BidBroadcastingTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("BID BROADCASTING SYSTEM TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Acceptance criteria check
    acceptance_criteria = [
        "monotonic_sequence_numbers",
        "bid_update_event_broadcast", 
        "sync_state_initialization",
        "rapid_fire_bidding",
        "sequence_number_consistency",
        "multi_user_state_synchronization"
    ]
    
    all_criteria_met = all(results.get(criteria, False) for criteria in acceptance_criteria)
    
    if all_criteria_met:
        print("\n🎉 All acceptance criteria met!")
        print("✅ Sequence numbers are monotonic (always increasing)")
        print("✅ bid_update events include lotId, amount, bidder, seq, serverTime")
        print("✅ All users in auction room receive bid_update events")
        print("✅ sync_state includes currentBid, currentBidder, seq")
        print("✅ Rapid fire bids result in identical final state for all users")
        print("✅ No stale updates (lower seq) are processed")
        return True
    else:
        print("\n⚠️ Some acceptance criteria not met")
        failed_criteria = [c for c in acceptance_criteria if not results.get(c, False)]
        for criteria in failed_criteria:
            print(f"❌ {criteria}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)