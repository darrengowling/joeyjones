"""
Socket.IO Auction Load Test
Production Hardening - Load Testing

Simulates concurrent users bidding in real-time auctions via Socket.IO
Tests the most critical and vulnerable path in the system

Scenarios:
1. Users connect via Socket.IO
2. Join auction rooms
3. Place concurrent bids
4. Receive real-time updates
5. Monitor broadcast performance
"""

import time
import random
import uuid
import json
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import socketio
from socketio.exceptions import ConnectionError, TimeoutError

# Configuration
BACKEND_URL = "https://fantasy-ux-pilot.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
SOCKET_PATH = "/api/socket.io"

# Test auction configuration (you'll need to set this)
TEST_AUCTION_ID = None  # Set before running: export TEST_AUCTION_ID=your-auction-id
TEST_LEAGUE_ID = None   # Set before running: export TEST_LEAGUE_ID=your-league-id


class AuctionBidder(HttpUser):
    """
    Simulates a user in an active auction
    Focuses on Socket.IO bidding performance
    """
    wait_time = between(1, 3)  # Wait between bids
    
    def on_start(self):
        """Initialize auction bidder"""
        self.user_id = None
        self.access_token = None
        self.email = f"bidder_{uuid.uuid4().hex[:8]}@loadtest.com"
        self.socket = None
        self.connected = False
        self.current_lot = None
        self.current_price = 0
        self.bid_count = 0
        
        # Get test auction/league from environment
        import os
        self.auction_id = os.environ.get('TEST_AUCTION_ID', TEST_AUCTION_ID)
        self.league_id = os.environ.get('TEST_LEAGUE_ID', TEST_LEAGUE_ID)
        
        if not self.auction_id:
            print("❌ TEST_AUCTION_ID not set. Please set environment variable.")
            raise StopUser()
        
        # Authenticate
        self.authenticate()
        
        # Connect to Socket.IO
        self.connect_socket()
    
    def authenticate(self):
        """Quick authentication"""
        try:
            # Request magic link
            response = self.client.post(
                "/api/auth/magic-link",
                json={"email": self.email},
                name="Auth: Magic Link"
            )
            
            if response.status_code == 200:
                magic_token = response.json().get("token")
                
                # Verify and get JWT
                auth_response = self.client.post(
                    "/api/auth/verify-magic-link",
                    json={"email": self.email, "token": magic_token},
                    name="Auth: Verify Token"
                )
                
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    self.access_token = auth_data.get("accessToken")
                    self.user_id = auth_data.get("user", {}).get("id")
                else:
                    raise StopUser()
            else:
                raise StopUser()
                
        except Exception as e:
            print(f"❌ Auth failed: {e}")
            raise StopUser()
    
    def connect_socket(self):
        """Connect to Socket.IO"""
        start_time = time.time()
        
        try:
            # Create Socket.IO client
            self.socket = socketio.Client(
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1,
            )
            
            # Event handlers
            @self.socket.on('connect')
            def on_connect():
                self.connected = True
                print(f"✅ Socket connected: {self.socket.sid}")
            
            @self.socket.on('disconnect')
            def on_disconnect():
                self.connected = False
                print(f"❌ Socket disconnected")
            
            @self.socket.on('auction_snapshot')
            def on_snapshot(data):
                # Track current lot and price
                if data.get('currentLot'):
                    self.current_lot = data['currentLot']
                    if data['currentLot'].get('highestBid'):
                        self.current_price = data['currentLot']['highestBid']['amount']
            
            @self.socket.on('bid_placed')
            def on_bid(data):
                # Update current price when bid received
                if data.get('amount'):
                    self.current_price = data['amount']
                
                # Record event reception time
                elapsed = (time.time() - start_time) * 1000
                events.request.fire(
                    request_type="SocketIO",
                    name="Event: bid_placed",
                    response_time=elapsed,
                    response_length=len(json.dumps(data)),
                    exception=None,
                    context={}
                )
            
            @self.socket.on('timer_update')
            def on_timer(data):
                pass  # Just receive, don't log (too frequent)
            
            @self.socket.on('error')
            def on_error(data):
                print(f"❌ Socket error: {data}")
            
            # Connect to Socket.IO
            self.socket.connect(
                BACKEND_URL,
                socketio_path=SOCKET_PATH,
                transports=['websocket', 'polling']
            )
            
            # Wait for connection
            timeout = 10
            waited = 0
            while not self.connected and waited < timeout:
                time.sleep(0.1)
                waited += 0.1
            
            if not self.connected:
                raise ConnectionError("Socket.IO connection timeout")
            
            # Join auction room
            self.socket.emit('join_auction', {'auctionId': self.auction_id})
            
            # Wait for snapshot
            time.sleep(1)
            
            elapsed = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="SocketIO",
                name="Connect & Join Room",
                response_time=elapsed,
                response_length=0,
                exception=None,
                context={}
            )
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="SocketIO",
                name="Connect & Join Room",
                response_time=elapsed,
                response_length=0,
                exception=e,
                context={}
            )
            print(f"❌ Socket.IO connection failed: {e}")
            raise StopUser()
    
    @task(10)
    def place_bid(self):
        """Place a bid via Socket.IO"""
        if not self.connected or not self.current_lot:
            return
        
        start_time = time.time()
        
        try:
            # Calculate bid amount (increment by 1-5 million)
            increment = random.randint(1000000, 5000000)
            bid_amount = self.current_price + increment
            
            # Place bid via API (Socket.IO doesn't handle bid placement)
            response = self.client.post(
                f"/api/auction/{self.auction_id}/bid",
                json={
                    "userId": self.user_id,
                    "lotId": self.current_lot['id'],
                    "amount": bid_amount
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "X-User-ID": self.user_id
                },
                name="Auction: Place Bid"
            )
            
            if response.status_code == 200:
                self.bid_count += 1
                
                # Wait to receive bid update via Socket.IO
                # This tests broadcast latency
                time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Bid failed: {e}")
    
    @task(2)
    def check_auction_status(self):
        """Check auction status via API"""
        if not self.auction_id:
            return
        
        try:
            self.client.get(
                f"/api/auction/{self.auction_id}",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "X-User-ID": self.user_id
                },
                name="Auction: Get Status"
            )
        except Exception as e:
            print(f"❌ Status check failed: {e}")
    
    def on_stop(self):
        """Cleanup on user stop"""
        if self.socket and self.connected:
            try:
                self.socket.disconnect()
            except:
                pass
        
        print(f"👋 Bidder stopped. Total bids placed: {self.bid_count}")


# Custom events for Socket.IO metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("="*80)
    print("SOCKET.IO AUCTION LOAD TEST STARTING")
    print("="*80)
    print(f"Target: {BACKEND_URL}")
    print(f"Socket Path: {SOCKET_PATH}")
    
    import os
    auction_id = os.environ.get('TEST_AUCTION_ID')
    if auction_id:
        print(f"Test Auction: {auction_id}")
    else:
        print("⚠️  WARNING: TEST_AUCTION_ID not set!")
    
    print("="*80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("="*80)
    print("SOCKET.IO AUCTION LOAD TEST COMPLETE")
    print("="*80)
    
    # Print summary
    stats = environment.stats
    print("\n📊 SUMMARY STATISTICS:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time}ms")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    
    print("\n📡 SOCKET.IO METRICS:")
    for name, stat in stats.entries.items():
        if 'SocketIO' in name or 'Event:' in name:
            print(f"  {name}:")
            print(f"    Requests: {stat.num_requests}")
            print(f"    Failures: {stat.num_failures}")
            print(f"    Avg: {stat.avg_response_time:.2f}ms")
            print(f"    P95: {stat.get_response_time_percentile(0.95):.2f}ms")
    
    print("\n🎯 AUCTION PERFORMANCE:")
    bid_stats = stats.entries.get(('POST', 'Auction: Place Bid'))
    if bid_stats:
        print(f"  Total bids: {bid_stats.num_requests}")
        print(f"  Failed bids: {bid_stats.num_failures}")
        print(f"  Success rate: {((bid_stats.num_requests - bid_stats.num_failures) / bid_stats.num_requests * 100):.1f}%")
        print(f"  Avg bid time: {bid_stats.avg_response_time:.2f}ms")
    
    print("="*80)
