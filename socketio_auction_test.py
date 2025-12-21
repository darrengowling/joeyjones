#!/usr/bin/env python3
"""
Socket.IO Auction Flow Test - CRITICAL PRODUCTION ISSUE
Tests the complete auction flow with focus on Socket.IO real-time updates.

Issue: Bids are successfully placed via REST API, but Socket.IO broadcast events 
(`bid_update`, `bid_placed`) are NOT reaching clients in production.
"""

import requests
import json
import uuid
import time
import socketio
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://fixture-correction.preview.emergentagent.com/api"
SOCKET_URL = "https://fixture-correction.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class SocketIOAuctionTester:
    def __init__(self):
        self.test_data = {}
        self.socket_events = []
        self.socket_client = None
        self.socket_client_2 = None
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, headers: dict = None, expected_status: int = 200) -> dict:
        """Test API endpoint with proper error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        
        # Add X-User-ID header if we have a test user
        if headers is None:
            headers = {}
        if "user_id" in self.test_data and "X-User-ID" not in headers:
            headers["X-User-ID"] = self.test_data["user_id"]
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code == expected_status:
                try:
                    return response.json()
                except:
                    return {"success": True, "text": response.text}
            else:
                try:
                    error_data = response.json()
                    return {"error": f"HTTP {response.status_code}", "details": error_data, "text": response.text}
                except:
                    return {"error": f"HTTP {response.status_code}", "text": response.text}
                    
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}
    
    def create_test_users(self) -> bool:
        """Create 2 test users for the auction"""
        self.log("=== Creating Test Users ===")
        
        try:
            # Create User 1
            user1_data = {
                "name": f"AuctionUser1_{uuid.uuid4().hex[:8]}",
                "email": f"user1_{uuid.uuid4().hex[:8]}@test.com"
            }
            
            response = requests.post(f"{BACKEND_URL}/users", json=user1_data)
            if response.status_code == 200:
                user1 = response.json()
                self.test_data["user1_id"] = user1["id"]
                self.test_data["user1_email"] = user1["email"]
                self.log(f"✅ Created User 1: {user1['name']} (ID: {user1['id']})")
            else:
                self.log(f"❌ Failed to create User 1: {response.status_code} - {response.text}")
                return False
            
            # Create User 2
            user2_data = {
                "name": f"AuctionUser2_{uuid.uuid4().hex[:8]}",
                "email": f"user2_{uuid.uuid4().hex[:8]}@test.com"
            }
            
            response = requests.post(f"{BACKEND_URL}/users", json=user2_data)
            if response.status_code == 200:
                user2 = response.json()
                self.test_data["user2_id"] = user2["id"]
                self.test_data["user2_email"] = user2["email"]
                self.log(f"✅ Created User 2: {user2['name']} (ID: {user2['id']})")
            else:
                self.log(f"❌ Failed to create User 2: {response.status_code} - {response.text}")
                return False
                
            # Set primary user for headers
            self.test_data["user_id"] = self.test_data["user1_id"]
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test users: {str(e)}")
            return False
    
    def create_test_league(self) -> bool:
        """Create a test league with both users"""
        self.log("=== Creating Test League ===")
        
        if "user1_id" not in self.test_data:
            self.log("❌ No users available for league creation")
            return False
        
        try:
            # Create league with User 1 as commissioner
            league_data = {
                "name": f"SocketIO Test League {uuid.uuid4().hex[:8]}",
                "commissionerId": self.test_data["user1_id"],
                "budget": 100000000.0,  # £100m budget
                "minManagers": 2,
                "maxManagers": 4,
                "clubSlots": 5
            }
            
            result = self.test_api_endpoint("POST", "/leagues", league_data)
            if "error" in result:
                self.log(f"❌ League creation failed: {result}")
                return False
            
            self.test_data["league_id"] = result["id"]
            self.test_data["invite_token"] = result["inviteToken"]
            self.log(f"✅ Created league: {result['id']}")
            
            # User 1 joins league (commissioner auto-join)
            join_data = {
                "userId": self.test_data["user1_id"],
                "inviteToken": self.test_data["invite_token"]
            }
            
            result = self.test_api_endpoint("POST", f"/leagues/{self.test_data['league_id']}/join", join_data)
            if "error" in result:
                self.log(f"❌ User 1 join failed: {result}")
                return False
            
            self.log("✅ User 1 joined league")
            
            # User 2 joins league
            join_data["userId"] = self.test_data["user2_id"]
            
            result = self.test_api_endpoint("POST", f"/leagues/{self.test_data['league_id']}/join", join_data)
            if "error" in result:
                self.log(f"❌ User 2 join failed: {result}")
                return False
            
            self.log("✅ User 2 joined league")
            
            # Verify participants
            result = self.test_api_endpoint("GET", f"/leagues/{self.test_data['league_id']}/participants")
            if "error" in result:
                self.log(f"❌ Failed to get participants: {result}")
                return False
            
            participants = result if isinstance(result, list) else result.get("participants", [])
            if len(participants) < 2:
                self.log(f"❌ Expected 2 participants, found {len(participants)}")
                return False
            
            self.log(f"✅ League has {len(participants)} participants")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test league: {str(e)}")
            return False
    
    def start_auction(self) -> bool:
        """Start the auction (creates in waiting state)"""
        self.log("=== Starting Auction ===")
        
        if "league_id" not in self.test_data:
            self.log("❌ No league available for auction")
            return False
        
        try:
            result = self.test_api_endpoint("POST", f"/leagues/{self.test_data['league_id']}/auction/start")
            if "error" in result:
                self.log(f"❌ Auction start failed: {result}")
                return False
            
            self.test_data["auction_id"] = result["auctionId"]
            auction_status = result.get("status", "unknown")
            self.log(f"✅ Created auction: {result['auctionId']} (status: {auction_status})")
            
            # Get auction details
            result = self.test_api_endpoint("GET", f"/auction/{self.test_data['auction_id']}")
            if "error" in result:
                self.log(f"❌ Failed to get auction details: {result}")
                return False
            
            auction_data = result.get("auction", {})
            current_status = auction_data.get("status", "unknown")
            self.log(f"✅ Auction status: {current_status}")
            
            # If auction is in waiting state, we'll begin it later after Socket.IO setup
            if current_status == "waiting":
                self.log("✅ Auction created in waiting state (will begin after Socket.IO setup)")
                return True
            
            # If auction is already active, get current club
            current_club = result.get("currentClub")
            if current_club:
                self.test_data["current_club"] = current_club
                self.log(f"✅ Current club: {current_club.get('name')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error starting auction: {str(e)}")
            return False
    
    def begin_auction(self) -> bool:
        """Begin the auction from waiting state"""
        self.log("=== Beginning Auction ===")
        
        if "auction_id" not in self.test_data:
            self.log("❌ No auction available to begin")
            return False
        
        try:
            # Begin the auction (moves from waiting to active)
            result = self.test_api_endpoint("POST", f"/auction/{self.test_data['auction_id']}/begin")
            if "error" in result:
                self.log(f"❌ Begin auction failed: {result}")
                return False
            
            self.log("✅ Auction begun successfully")
            
            # Get updated auction details
            result = self.test_api_endpoint("GET", f"/auction/{self.test_data['auction_id']}")
            if "error" in result:
                self.log(f"❌ Failed to get auction details after begin: {result}")
                return False
            
            current_club = result.get("currentClub")
            if not current_club:
                self.log("❌ No current club in auction after begin")
                return False
            
            self.test_data["current_club"] = current_club
            self.log(f"✅ Current club: {current_club.get('name')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error beginning auction: {str(e)}")
            return False
    
    def setup_socket_clients(self) -> bool:
        """Setup Socket.IO clients for both users"""
        self.log("=== Setting Up Socket.IO Clients ===")
        
        try:
            # Setup User 1 Socket Client
            self.socket_client = socketio.Client(logger=False, engineio_logger=False)
            self.socket_events = []
            
            @self.socket_client.event
            def connect():
                self.log("🔌 User 1 Socket.IO connected")
                self.socket_events.append({"event": "connect", "user": "user1", "timestamp": time.time()})
            
            @self.socket_client.event
            def disconnect():
                self.log("🔌 User 1 Socket.IO disconnected")
                self.socket_events.append({"event": "disconnect", "user": "user1", "timestamp": time.time()})
            
            @self.socket_client.event
            def joined(data):
                self.log(f"🔌 User 1 joined auction room: {data}")
                self.socket_events.append({"event": "joined", "user": "user1", "data": data, "timestamp": time.time()})
            
            @self.socket_client.event
            def bid_update(data):
                self.log(f"📢 User 1 received bid_update: {data}")
                self.socket_events.append({"event": "bid_update", "user": "user1", "data": data, "timestamp": time.time()})
            
            @self.socket_client.event
            def bid_placed(data):
                self.log(f"📢 User 1 received bid_placed: {data}")
                self.socket_events.append({"event": "bid_placed", "user": "user1", "data": data, "timestamp": time.time()})
            
            @self.socket_client.event
            def sync_state(data):
                self.log(f"🔄 User 1 received sync_state")
                self.socket_events.append({"event": "sync_state", "user": "user1", "data": data, "timestamp": time.time()})
            
            @self.socket_client.event
            def auction_snapshot(data):
                self.log(f"📸 User 1 received auction_snapshot: status={data.get('status')}")
                self.socket_events.append({"event": "auction_snapshot", "user": "user1", "data": data, "timestamp": time.time()})
            
            @self.socket_client.event
            def lot_started(data):
                self.log(f"🎬 User 1 received lot_started: {data.get('club', {}).get('name')}")
                self.socket_events.append({"event": "lot_started", "user": "user1", "data": data, "timestamp": time.time()})
            
            # Setup User 2 Socket Client
            self.socket_client_2 = socketio.Client(logger=False, engineio_logger=False)
            
            @self.socket_client_2.event
            def connect():
                self.log("🔌 User 2 Socket.IO connected")
                self.socket_events.append({"event": "connect", "user": "user2", "timestamp": time.time()})
            
            @self.socket_client_2.event
            def disconnect():
                self.log("🔌 User 2 Socket.IO disconnected")
                self.socket_events.append({"event": "disconnect", "user": "user2", "timestamp": time.time()})
            
            @self.socket_client_2.event
            def joined(data):
                self.log(f"🔌 User 2 joined auction room: {data}")
                self.socket_events.append({"event": "joined", "user": "user2", "data": data, "timestamp": time.time()})
            
            @self.socket_client_2.event
            def bid_update(data):
                self.log(f"📢 User 2 received bid_update: {data}")
                self.socket_events.append({"event": "bid_update", "user": "user2", "data": data, "timestamp": time.time()})
            
            @self.socket_client_2.event
            def bid_placed(data):
                self.log(f"📢 User 2 received bid_placed: {data}")
                self.socket_events.append({"event": "bid_placed", "user": "user2", "data": data, "timestamp": time.time()})
            
            @self.socket_client_2.event
            def sync_state(data):
                self.log(f"🔄 User 2 received sync_state")
                self.socket_events.append({"event": "sync_state", "user": "user2", "data": data, "timestamp": time.time()})
            
            @self.socket_client_2.event
            def auction_snapshot(data):
                self.log(f"📸 User 2 received auction_snapshot: status={data.get('status')}")
                self.socket_events.append({"event": "auction_snapshot", "user": "user2", "data": data, "timestamp": time.time()})
            
            @self.socket_client_2.event
            def lot_started(data):
                self.log(f"🎬 User 2 received lot_started: {data.get('club', {}).get('name')}")
                self.socket_events.append({"event": "lot_started", "user": "user2", "data": data, "timestamp": time.time()})
            
            # Connect both clients
            self.log("Connecting User 1 Socket.IO client...")
            self.socket_client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            
            self.log("Connecting User 2 Socket.IO client...")
            self.socket_client_2.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            
            # Wait for connections
            time.sleep(3)
            
            # Check connections
            user1_connected = any(e["event"] == "connect" and e["user"] == "user1" for e in self.socket_events)
            user2_connected = any(e["event"] == "connect" and e["user"] == "user2" for e in self.socket_events)
            
            if not user1_connected:
                self.log("❌ User 1 Socket.IO connection failed")
                return False
            
            if not user2_connected:
                self.log("❌ User 2 Socket.IO connection failed")
                return False
            
            self.log("✅ Both Socket.IO clients connected successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Error setting up Socket.IO clients: {str(e)}")
            return False
    
    def join_auction_rooms(self) -> bool:
        """Have both users join the auction room"""
        self.log("=== Joining Auction Rooms ===")
        
        if not self.socket_client or not self.socket_client_2 or "auction_id" not in self.test_data:
            self.log("❌ Socket clients not ready or no auction ID")
            return False
        
        try:
            auction_id = self.test_data["auction_id"]
            
            # User 1 joins auction room
            self.log(f"User 1 joining auction room: {auction_id}")
            self.socket_client.emit('join_auction', {
                'auctionId': auction_id,
                'userId': self.test_data["user1_id"]
            })
            
            # User 2 joins auction room
            self.log(f"User 2 joining auction room: {auction_id}")
            self.socket_client_2.emit('join_auction', {
                'auctionId': auction_id,
                'userId': self.test_data["user2_id"]
            })
            
            # Wait for join confirmations
            time.sleep(3)
            
            # Check if both users joined
            user1_joined = any(e["event"] == "joined" and e["user"] == "user1" for e in self.socket_events)
            user2_joined = any(e["event"] == "joined" and e["user"] == "user2" for e in self.socket_events)
            
            if not user1_joined:
                self.log("❌ User 1 failed to join auction room")
                return False
            
            if not user2_joined:
                self.log("❌ User 2 failed to join auction room")
                return False
            
            self.log("✅ Both users joined auction room successfully")
            
            # Check for sync_state events
            user1_synced = any(e["event"] == "sync_state" and e["user"] == "user1" for e in self.socket_events)
            user2_synced = any(e["event"] == "sync_state" and e["user"] == "user2" for e in self.socket_events)
            
            if user1_synced and user2_synced:
                self.log("✅ Both users received sync_state events")
            else:
                self.log("⚠️  Some users did not receive sync_state events")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error joining auction rooms: {str(e)}")
            return False
    
    def check_backend_logs_before_bid(self):
        """Check backend logs before placing bid"""
        self.log("=== Checking Backend Logs (Pre-Bid) ===")
        
        try:
            # Check backend logs for Socket.IO room information
            import subprocess
            
            # Check for recent Socket.IO logs
            result = subprocess.run([
                "tail", "-n", "50", "/var/log/supervisor/backend.out.log"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                self.log("📋 Recent backend logs (last 50 lines):")
                for line in logs.split('\n')[-10:]:  # Show last 10 lines
                    if line.strip():
                        self.log(f"  {line}")
                
                # Look for Socket.IO related logs
                if "join_auction_room" in logs:
                    self.log("✅ Found join_auction_room events in logs")
                else:
                    self.log("⚠️  No join_auction_room events found in logs")
                
                if "roomSize" in logs:
                    self.log("✅ Found roomSize information in logs")
                else:
                    self.log("⚠️  No roomSize information found in logs")
            
        except Exception as e:
            self.log(f"⚠️  Could not check backend logs: {str(e)}")
    
    def place_bid_and_monitor_events(self) -> bool:
        """Place a bid and monitor Socket.IO events"""
        self.log("=== Placing Bid and Monitoring Events ===")
        
        if "auction_id" not in self.test_data or "current_club" not in self.test_data:
            self.log("❌ No auction or current club available")
            return False
        
        try:
            # Clear previous events for this test
            initial_event_count = len(self.socket_events)
            
            # Place bid with User 1
            bid_data = {
                "userId": self.test_data["user1_id"],
                "clubId": self.test_data["current_club"]["id"],
                "amount": 2500000.0  # £2.5m
            }
            
            self.log(f"User 1 placing bid: £{bid_data['amount']:,.0f} for {self.test_data['current_club']['name']}")
            
            # Record time before bid
            bid_start_time = time.time()
            
            # Place the bid via REST API
            result = self.test_api_endpoint("POST", f"/auction/{self.test_data['auction_id']}/bid", bid_data)
            
            # Record time after bid
            bid_end_time = time.time()
            
            if "error" in result:
                self.log(f"❌ Bid placement failed: {result}")
                return False
            
            bid_response = result.get("bid", {})
            self.log(f"✅ Bid REST API returned 200 success: Bid ID {bid_response.get('id')}")
            
            # Wait for Socket.IO events
            self.log("⏳ Waiting for Socket.IO broadcast events...")
            time.sleep(5)
            
            # Check backend logs after bid
            self.check_backend_logs_after_bid()
            
            # Analyze Socket.IO events received after the bid
            new_events = self.socket_events[initial_event_count:]
            
            self.log(f"📊 Received {len(new_events)} Socket.IO events after bid:")
            for event in new_events:
                event_time = event.get("timestamp", 0)
                if event_time >= bid_start_time:
                    self.log(f"  - {event['event']} ({event['user']}) at {datetime.fromtimestamp(event_time).strftime('%H:%M:%S.%f')[:-3]}")
            
            # Check for critical events
            bid_update_events = [e for e in new_events if e["event"] == "bid_update" and e.get("timestamp", 0) >= bid_start_time]
            bid_placed_events = [e for e in new_events if e["event"] == "bid_placed" and e.get("timestamp", 0) >= bid_start_time]
            
            success = True
            
            if not bid_update_events:
                self.log("❌ CRITICAL: No bid_update events received by any client")
                success = False
            else:
                self.log(f"✅ Received {len(bid_update_events)} bid_update events")
                
                # Check if User 2 received the event (should see User 1's bid)
                user2_bid_updates = [e for e in bid_update_events if e["user"] == "user2"]
                if user2_bid_updates:
                    self.log("✅ User 2 received bid_update from User 1's bid")
                else:
                    self.log("❌ CRITICAL: User 2 did not receive bid_update from User 1's bid")
                    success = False
            
            if not bid_placed_events:
                self.log("❌ CRITICAL: No bid_placed events received by any client")
                success = False
            else:
                self.log(f"✅ Received {len(bid_placed_events)} bid_placed events")
            
            return success
            
        except Exception as e:
            self.log(f"❌ Error during bid and event monitoring: {str(e)}")
            return False
    
    def check_backend_logs_after_bid(self):
        """Check backend logs after placing bid"""
        self.log("=== Checking Backend Logs (Post-Bid) ===")
        
        try:
            import subprocess
            
            # Check backend output logs
            result = subprocess.run([
                "tail", "-n", "100", "/var/log/supervisor/backend.out.log"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for Socket.IO emission logs
                emission_logs = []
                room_size_logs = []
                
                for line in logs.split('\n'):
                    if "bid_update" in line and "emit" in line.lower():
                        emission_logs.append(line.strip())
                    if "bid_placed" in line and "emit" in line.lower():
                        emission_logs.append(line.strip())
                    if "roomSize" in line:
                        room_size_logs.append(line.strip())
                
                if emission_logs:
                    self.log("✅ Found Socket.IO emission logs:")
                    for log in emission_logs[-5:]:  # Show last 5
                        self.log(f"  {log}")
                else:
                    self.log("❌ CRITICAL: No Socket.IO emission logs found")
                
                if room_size_logs:
                    self.log("✅ Found room size logs:")
                    for log in room_size_logs[-3:]:  # Show last 3
                        self.log(f"  {log}")
                        
                        # Extract room size if possible
                        if "roomSize" in log:
                            try:
                                import re
                                match = re.search(r'"roomSize":(\d+)', log)
                                if match:
                                    room_size = int(match.group(1))
                                    if room_size > 0:
                                        self.log(f"✅ Room has {room_size} clients")
                                    else:
                                        self.log(f"❌ CRITICAL: Room has {room_size} clients (no one to receive events)")
                            except:
                                pass
                else:
                    self.log("❌ CRITICAL: No room size information found")
            
            # Check error logs
            result = subprocess.run([
                "tail", "-n", "50", "/var/log/supervisor/backend.err.log"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                error_logs = result.stdout.strip()
                if error_logs:
                    self.log("⚠️  Recent error logs:")
                    for line in error_logs.split('\n')[-5:]:  # Show last 5 errors
                        if line.strip():
                            self.log(f"  ERROR: {line}")
                else:
                    self.log("✅ No recent errors in backend logs")
            
        except Exception as e:
            self.log(f"⚠️  Could not check backend logs: {str(e)}")
    
    def test_connection_stability(self) -> bool:
        """Test for connection/disconnection patterns"""
        self.log("=== Testing Connection Stability ===")
        
        try:
            # Monitor events for disconnections
            disconnect_events = [e for e in self.socket_events if e["event"] == "disconnect"]
            connect_events = [e for e in self.socket_events if e["event"] == "connect"]
            
            self.log(f"📊 Connection Events Summary:")
            self.log(f"  - Total connects: {len(connect_events)}")
            self.log(f"  - Total disconnects: {len(disconnect_events)}")
            
            if len(disconnect_events) > 0:
                self.log("⚠️  Detected disconnection events:")
                for event in disconnect_events:
                    timestamp = datetime.fromtimestamp(event.get("timestamp", 0)).strftime('%H:%M:%S')
                    self.log(f"  - {event['user']} disconnected at {timestamp}")
                
                # Check if there are reconnections
                reconnects = len(connect_events) - 2  # Subtract initial connections
                if reconnects > 0:
                    self.log(f"⚠️  Detected {reconnects} reconnection(s) - indicates connection instability")
                    return False
            
            # Check current connection status
            user1_connected = self.socket_client and self.socket_client.connected
            user2_connected = self.socket_client_2 and self.socket_client_2.connected
            
            if user1_connected and user2_connected:
                self.log("✅ Both clients remain connected")
                return True
            else:
                self.log(f"❌ Connection status: User1={user1_connected}, User2={user2_connected}")
                return False
            
        except Exception as e:
            self.log(f"❌ Error testing connection stability: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up test data and connections"""
        self.log("=== Cleaning Up ===")
        
        try:
            # Disconnect socket clients
            if self.socket_client and self.socket_client.connected:
                self.socket_client.disconnect()
                self.log("🔌 User 1 Socket.IO disconnected")
            
            if self.socket_client_2 and self.socket_client_2.connected:
                self.socket_client_2.disconnect()
                self.log("🔌 User 2 Socket.IO disconnected")
            
            # Delete test league if created
            if "league_id" in self.test_data and "user1_id" in self.test_data:
                result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}?user_id={self.test_data['user1_id']}")
                if "error" not in result:
                    self.log("🗑️  Test league deleted")
            
        except Exception as e:
            self.log(f"⚠️  Cleanup error: {str(e)}")
    
    def run_socket_auction_test(self) -> Dict[str, bool]:
        """Run the complete Socket.IO auction flow test"""
        self.log("🚀 Starting Socket.IO Auction Flow Test")
        self.log("=" * 60)
        
        results = {}
        
        # Test sequence
        test_steps = [
            ("create_users", self.create_test_users),
            ("create_league", self.create_test_league),
            ("start_auction", self.start_auction),
            ("setup_socket_clients", self.setup_socket_clients),
            ("join_auction_rooms", self.join_auction_rooms),
            ("begin_auction", self.begin_auction),
            ("place_bid_and_monitor", self.place_bid_and_monitor_events),
            ("test_connection_stability", self.test_connection_stability),
        ]
        
        for step_name, step_func in test_steps:
            try:
                self.log(f"\n🔄 Running: {step_name}")
                results[step_name] = step_func()
                
                if results[step_name]:
                    self.log(f"✅ {step_name}: PASSED")
                else:
                    self.log(f"❌ {step_name}: FAILED")
                    # Continue with remaining tests even if one fails
                    
            except Exception as e:
                self.log(f"❌ {step_name}: CRASHED - {str(e)}")
                results[step_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = SocketIOAuctionTester()
    results = tester.run_socket_auction_test()
    
    # Print summary
    print("\n" + "="*60)
    print("SOCKET.IO AUCTION FLOW TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Critical analysis
    critical_tests = ["place_bid_and_monitor", "setup_socket_clients", "join_auction_rooms", "begin_auction"]
    critical_passed = sum(1 for test in critical_tests if results.get(test, False))
    
    print(f"\nCritical Socket.IO Tests: {critical_passed}/{len(critical_tests)} passed")
    
    if results.get("place_bid_and_monitor", False):
        print("🎉 Socket.IO broadcast events are working correctly!")
    else:
        print("🚨 CRITICAL ISSUE: Socket.IO broadcast events are NOT working!")
        print("   - Bids succeed via REST API but events don't reach clients")
        print("   - Check backend logs for room size and emission details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)