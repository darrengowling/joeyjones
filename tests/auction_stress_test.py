#!/usr/bin/env python3
"""
Sport X - Auction Stress Test Suite (Preview Environment)
==========================================================

Tests the auction system under realistic load conditions against the preview environment.

WHAT THIS TESTS:
----------------
1. HOT-LOT MODE: Simulates frantic bidding on a popular team
   - 7 users bidding aggressively every 0.5-2 seconds
   - Tests bid throughput, Socket.IO broadcast speed, timer accuracy
   - Duration: ~5 minutes or until lot completes

2. FULL-AUCTION MODE: Simulates complete 32-team auction
   - Variable bidding strategies based on team popularity
   - Tests sustained load, memory/connection stability
   - Duration: 45-60 minutes

3. RACE-CONDITION MODE: All users bid simultaneously
   - Tests bid ordering, conflict resolution
   - Only one bid should succeed per moment
   - Duration: ~30 seconds

OUTPUTS:
--------
- Bid success rate (target: >90%)
- Socket.IO latency percentiles (p50, p95, p99)
- Disconnection count (target: 0)
- Per-user statistics
- Error log
- Anti-snipe trigger count
- Recommendations based on results

Usage:
    python auction_stress_test.py --mode hot-lot --invite-token YOUR_TOKEN
    python auction_stress_test.py --mode full-auction --invite-token YOUR_TOKEN
    python auction_stress_test.py --mode race-condition --invite-token YOUR_TOKEN

Requirements:
    pip install "python-socketio[asyncio_client]" aiohttp
"""

import asyncio
import aiohttp
import socketio
import json
import time
import argparse
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field

# ============================================================================
# CONFIGURATION - Preview Environment
# ============================================================================
BASE_URL = "http://localhost:8001/api"
SOCKET_URL = "http://localhost:8001"
SOCKET_PATH = "/api/socket.io"

# Team popularity tiers (for realistic bidding behavior)
HOT_TEAMS = [
    "Manchester City", "Real Madrid", "Bayern Munich", "Liverpool",
    "Paris Saint-Germain", "Arsenal", "Barcelona", "Inter Milan"
]

MEDIUM_TEAMS = [
    "Juventus", "Borussia Dortmund", "AC Milan", "Manchester United",
    "Tottenham", "RB Leipzig", "Atalanta", "Porto", "Chelsea"
]

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TestUser:
    """Represents a test user"""
    email: str
    user_id: Optional[str] = None
    jwt_token: Optional[str] = None
    budget_remaining: int = 500_000_000  # £500M
    clubs_won: List[str] = field(default_factory=list)
    bids_placed: int = 0
    bids_won: int = 0
    bids_failed: int = 0
    bids_outbid: int = 0
    last_bid_sent_at: Optional[float] = None
    socket_client: Optional[socketio.AsyncClient] = None
    connected: bool = False


@dataclass
class BidEvent:
    """Records a bid for analysis"""
    timestamp: float
    user_email: str
    amount: int
    success: bool
    latency_ms: float
    error: Optional[str] = None


@dataclass 
class LotResult:
    """Records outcome of a lot"""
    club_name: str
    winner_email: Optional[str]
    winning_amount: Optional[int]
    total_bids: int
    duration_seconds: float
    anti_snipe_triggered: bool = False


@dataclass
class TestMetrics:
    """Tracks all test metrics"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Bid tracking
    bids: List[BidEvent] = field(default_factory=list)
    
    # Latency tracking
    bid_latencies_ms: List[float] = field(default_factory=list)
    socket_broadcast_latencies_ms: List[float] = field(default_factory=list)
    
    # Lot tracking
    lots_completed: List[LotResult] = field(default_factory=list)
    
    # Issues
    errors: List[str] = field(default_factory=list)
    disconnects: int = 0
    reconnects: int = 0
    
    # Anti-snipe
    anti_snipe_triggers: int = 0
    
    def duration_seconds(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time
    
    def bid_success_rate(self) -> float:
        if not self.bids:
            return 0.0
        successful = sum(1 for b in self.bids if b.success)
        return (successful / len(self.bids)) * 100
    
    def percentile(self, values: List[float], p: int) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * (p / 100))
        return sorted_vals[min(idx, len(sorted_vals) - 1)]


# ============================================================================
# MAIN TEST CLASS
# ============================================================================

class AuctionStressTest:
    """Main test orchestrator"""
    
    def __init__(self, invite_token: str, mode: str, num_users: int = 7, commissioner_email: str = None, use_existing_members: bool = False):
        self.invite_token = invite_token
        self.mode = mode
        self.num_users = num_users
        self.commissioner_email = commissioner_email
        self.use_existing_members = use_existing_members
        self.users: List[TestUser] = []
        self.metrics = TestMetrics()
        self.commissioner: Optional[TestUser] = None
        
        # League/auction state
        self.league_id: Optional[str] = None
        self.league_name: Optional[str] = None
        self.auction_id: Optional[str] = None
        
        # Current lot state (updated via Socket.IO)
        self.current_lot_club_id: Optional[str] = None
        self.current_lot_club_name: Optional[str] = None
        self.current_bid: int = 0
        self.current_bidder_id: Optional[str] = None
        self.timer_ends_at: Optional[float] = None
        self.lot_start_time: Optional[float] = None
        self.lot_bid_count: int = 0
        
        # State flags
        self.lot_active = False
        self.auction_complete = False
        self.last_timer_remaining: Optional[float] = None
        
    # ========================================================================
    # SETUP METHODS
    # ========================================================================
    
    async def setup(self):
        """Initialize test environment"""
        self._print_header("AUCTION STRESS TEST - SETUP")
        
        # Step 1: Get league info
        print(f"\n1. Fetching league info (token: {self.invite_token})...")
        await self._get_league_by_token()
        print(f"   ✓ League: {self.league_name}")
        print(f"   ✓ League ID: {self.league_id}")
        
        # Step 1.5: Authenticate commissioner if provided
        if self.commissioner_email:
            print(f"\n1.5. Authenticating commissioner ({self.commissioner_email})...")
            try:
                self.commissioner = await self._create_test_user(self.commissioner_email)
                print(f"   ✓ Commissioner authenticated (ID: {self.commissioner.user_id[:8]}...)")
                # Add commissioner to users list so they can participate in bidding
                self.users.append(self.commissioner)
            except Exception as e:
                print(f"   ⚠ Failed to authenticate commissioner: {e}")
                print("   → Will try to proceed without commissioner privileges")
        
        # Step 2: Create or authenticate test users
        if self.use_existing_members:
            print(f"\n2. Using existing league members as test users...")
            await self._authenticate_existing_members()
        else:
            print(f"\n2. Creating {self.num_users} test users...")
            for i in range(self.num_users):
                email = f"stress-test-{i+1}-{int(time.time())}@test.local"
                try:
                    user = await self._create_test_user(email)
                    self.users.append(user)
                    print(f"   ✓ {email[:30]}... (ID: {user.user_id[:8]}...)")
                except Exception as e:
                    print(f"   ✗ Failed to create {email}: {e}")
                    self.metrics.errors.append(f"User creation failed: {e}")
        
        if len(self.users) < 2:
            raise Exception("Need at least 2 users to run test")
        
        # Step 3: Join league
        print(f"\n3. Joining users to league...")
        for user in self.users:
            try:
                await self._join_league(user)
                print(f"   ✓ {user.email[:30]}... joined")
            except Exception as e:
                if "already" not in str(e).lower():
                    print(f"   ⚠ {user.email[:30]}...: {e}")
        
        # Step 4: Check for existing auction or create new
        print(f"\n4. Checking auction status...")
        auction = await self._get_auction()
        
        if auction:
            self.auction_id = auction.get('auctionId') or auction.get('id')
            status = auction.get('status')
            print(f"   ✓ Existing auction found: {self.auction_id[:8]}... (status: {status})")
            
            if status == 'completed':
                print("   ⚠ Auction already completed. Resetting...")
                await self._reset_auction()
                auction = None
        
        if not auction:
            print("   → Starting new auction...")
            await self._start_auction()
            print(f"   ✓ Auction created: {self.auction_id[:8]}...")
        
        print("\n✓ Setup complete!")
    
    async def _get_league_by_token(self):
        """Fetch league info by invite token"""
        url = f"{BASE_URL}/leagues/by-token/{self.invite_token}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get league: {await resp.text()}")
                data = await resp.json()
                
                # API returns {"found": true, "league": {...}} structure
                if not data.get('found'):
                    raise Exception(f"League not found for token: {self.invite_token}")
                
                league = data.get('league', {})
                self.league_id = league.get('id')
                self.league_name = league.get('name', 'Unknown')
                
                if not self.league_id:
                    raise Exception(f"League ID not found in response: {data}")
    
    async def _authenticate_existing_members(self):
        """Authenticate existing league members as test users"""
        url = f"{BASE_URL}/leagues/{self.league_id}/members"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get members: {await resp.text()}")
                members = await resp.json()
        
        # Filter to stress-test users (not the commissioner)
        test_members = [m for m in members if 'stress-test' in m.get('displayName', '').lower()]
        
        # Limit to num_users
        test_members = test_members[:self.num_users]
        
        for member in test_members:
            # Construct email from displayName (stress-test users use displayName@test.local)
            display_name = member.get('displayName', '')
            email = f"{display_name}@test.local"
            
            try:
                user = await self._create_test_user(email)
                # Verify the user ID matches
                if user.user_id == member.get('userId'):
                    self.users.append(user)
                    print(f"   ✓ {email[:30]}... authenticated (ID: {user.user_id[:8]}...)")
                else:
                    print(f"   ⚠ {email}: User ID mismatch")
            except Exception as e:
                print(f"   ⚠ {email}: {e}")
        
        if len(self.users) == 0:
            print("   ⚠ No existing stress-test members found. Will create new users.")

    async def _create_test_user(self, email: str) -> TestUser:
        """Create a test user via magic link (works in preview/dev mode)"""
        user = TestUser(email=email)
        
        async with aiohttp.ClientSession() as session:
            # Request magic link
            url = f"{BASE_URL}/auth/magic-link"
            async with session.post(url, json={"email": email}) as resp:
                if resp.status != 200:
                    raise Exception(f"Magic link request failed: {await resp.text()}")
                data = await resp.json()
                magic_token = data.get('token')
                
                if not magic_token:
                    raise Exception("No token returned - are you in production mode?")
            
            # Verify magic link - API requires both email and token
            url = f"{BASE_URL}/auth/verify-magic-link"
            async with session.post(url, json={"email": email, "token": magic_token}) as resp:
                if resp.status != 200:
                    raise Exception(f"Magic link verify failed: {await resp.text()}")
                data = await resp.json()
                # API returns accessToken, not token
                user.jwt_token = data.get('accessToken') or data.get('token')
                user.user_id = data['user']['id']
        
        return user
    
    async def _join_league(self, user: TestUser):
        """Join user to league"""
        url = f"{BASE_URL}/leagues/{self.league_id}/join"
        headers = {"Authorization": f"Bearer {user.jwt_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json={"inviteToken": self.invite_token, "userId": user.user_id}, 
                headers=headers
            ) as resp:
                if resp.status not in [200, 409]:  # 409 = already joined
                    raise Exception(f"Join failed: {await resp.text()}")
    
    def _get_auth_user(self) -> TestUser:
        """Get the user to use for authenticated requests (commissioner if available)"""
        return self.commissioner if self.commissioner else self.users[0]
    
    async def _fetch_auction_state(self):
        """Fetch current auction state via HTTP to initialize local state"""
        auth_user = self._get_auth_user()
        url = f"{BASE_URL}/auction/{self.auction_id}"
        headers = {
            "Authorization": f"Bearer {auth_user.jwt_token}",
            "X-User-ID": auth_user.user_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        auction = data.get('auction', {})
                        current_club = data.get('currentClub', {})
                        
                        status = auction.get('status')
                        if status == 'active':
                            self.lot_active = True
                            self.current_lot_club_id = auction.get('currentClubId')
                            self.current_lot_club_name = current_club.get('name', 'Unknown')
                            self.current_bid = auction.get('currentBid') or 0
                            
                            bidder = auction.get('currentBidder')
                            self.current_bidder_id = bidder.get('userId') if bidder else None
                            
                            self.lot_start_time = time.time()
                            
                            print(f"   ✓ Auction active: {self.current_lot_club_name}")
                            print(f"   ✓ Current bid: £{self.current_bid/1_000_000:.1f}M" if self.current_bid else "   ✓ No bids yet")
                        elif status == 'completed':
                            self.auction_complete = True
                            print("   ⚠ Auction already completed")
                        else:
                            print(f"   ⚠ Auction status: {status}")
                    else:
                        print(f"   ⚠ Could not fetch auction state: {resp.status}")
        except Exception as e:
            print(f"   ⚠ Error fetching auction state: {e}")
    
    async def _get_auction(self) -> Optional[Dict]:
        """Get current auction for league"""
        auth_user = self._get_auth_user()
        url = f"{BASE_URL}/leagues/{self.league_id}/auction"
        headers = {
            "Authorization": f"Bearer {auth_user.jwt_token}",
            "X-User-ID": auth_user.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    return None
                return await resp.json()
    
    async def _start_auction(self):
        """Start auction (uses commissioner if available)"""
        auth_user = self._get_auth_user()
        url = f"{BASE_URL}/leagues/{self.league_id}/auction/start"
        headers = {
            "Authorization": f"Bearer {auth_user.jwt_token}",
            "X-User-ID": auth_user.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to start auction: {await resp.text()}")
                data = await resp.json()
                self.auction_id = data['auctionId']
    
    async def _reset_auction(self):
        """Reset auction to allow restart"""
        auth_user = self._get_auth_user()
        url = f"{BASE_URL}/leagues/{self.league_id}/auction/reset"
        headers = {
            "Authorization": f"Bearer {auth_user.jwt_token}",
            "X-User-ID": auth_user.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"   ⚠ Reset failed: {await resp.text()}")
    
    async def _begin_auction(self):
        """Begin auction (start first lot)"""
        auth_user = self._get_auth_user()
        url = f"{BASE_URL}/auction/{self.auction_id}/begin"
        headers = {
            "Authorization": f"Bearer {auth_user.jwt_token}",
            "X-User-ID": auth_user.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    return  # Successfully started
                
                text = await resp.text()
                
                # These are acceptable states - auction already in progress
                if any(x in text.lower() for x in ["already", "not in waiting", "active"]):
                    print("   ✓ Auction already in progress")
                    return
                
                if "commissioner" in text.lower():
                    print("   ⚠ Only commissioner can begin auction.")
                    print("   → Please provide --commissioner-email flag or start the auction manually in the UI.")
                    return
                
                raise Exception(f"Failed to begin auction: {text}")
    
    # ========================================================================
    # SOCKET.IO CONNECTION
    # ========================================================================
    
    async def _connect_all_sockets(self):
        """Connect all users to Socket.IO"""
        print("\nConnecting users via Socket.IO...")
        
        for user in self.users:
            try:
                await self._connect_socket(user)
                print(f"   ✓ {user.email[:30]}... connected")
            except Exception as e:
                print(f"   ✗ {user.email[:30]}... failed: {e}")
                self.metrics.errors.append(f"Socket connect failed for {user.email}: {e}")
        
        # Brief pause to let connections stabilize
        await asyncio.sleep(1)
    
    async def _connect_socket(self, user: TestUser):
        """Connect single user to Socket.IO"""
        sio = socketio.AsyncClient(reconnection=True, reconnection_attempts=3)
        user.socket_client = sio
        
        # Event handlers
        @sio.on('connect')
        async def on_connect():
            user.connected = True
        
        @sio.on('disconnect')
        async def on_disconnect():
            user.connected = False
            self.metrics.disconnects += 1
        
        @sio.on('auction_state')
        async def on_auction_state(data):
            self._update_auction_state(data)
        
        @sio.on('new_lot')
        async def on_new_lot(data):
            self._handle_new_lot(data)
        
        @sio.on('bid_update')
        async def on_bid_update(data):
            self._handle_bid_update(data, user)
        
        @sio.on('timer_sync')
        async def on_timer_sync(data):
            self._handle_timer_sync(data)
        
        @sio.on('sold')
        async def on_sold(data):
            self._handle_sold(data)
        
        @sio.on('unsold')
        async def on_unsold(data):
            self._handle_unsold(data)
        
        @sio.on('auction_completed')
        async def on_auction_complete(data):
            self.auction_complete = True
            print("\n🏁 AUCTION COMPLETED")
        
        @sio.on('error')
        async def on_error(data):
            self.metrics.errors.append(f"Socket error: {data}")
        
        # Connect
        await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
        
        # Join auction room
        await sio.emit('join_auction', {
            'auctionId': self.auction_id,
            'userId': user.user_id
        })
        
        await asyncio.sleep(0.3)
    
    def _update_auction_state(self, data: Dict):
        """Update local state from auction_state event"""
        self.current_bid = data.get('currentBid', 0)
        self.current_bidder_id = data.get('currentBidder', {}).get('userId')
        self.current_lot_club_id = data.get('currentClubId')
        
        status = data.get('status')
        if status == 'active':
            self.lot_active = True
        elif status == 'completed':
            self.auction_complete = True
    
    def _handle_new_lot(self, data: Dict):
        """Handle new lot starting"""
        self.current_lot_club_id = data.get('clubId')
        self.current_lot_club_name = data.get('clubName', 'Unknown')
        self.current_bid = 0
        self.current_bidder_id = None
        self.lot_active = True
        self.lot_start_time = time.time()
        self.lot_bid_count = 0
        
        print(f"\n📢 NEW LOT: {self.current_lot_club_name}")
    
    def _handle_bid_update(self, data: Dict, receiving_user: TestUser):
        """Handle bid update - track latency if this user placed the bid"""
        new_bid = data.get('currentBid', 0)
        old_bid = self.current_bid
        
        self.current_bid = new_bid
        self.current_bidder_id = data.get('bidderId')
        self.lot_bid_count += 1
        
        # Check for anti-snipe (bid increased timer)
        new_timer = data.get('timerEndsAt')
        if new_timer and self.timer_ends_at:
            # If timer extended, anti-snipe triggered
            if new_timer > self.timer_ends_at:
                self.metrics.anti_snipe_triggers += 1
        
        self.timer_ends_at = new_timer
        
        # Calculate broadcast latency if this user just bid
        if receiving_user.last_bid_sent_at and self.current_bidder_id == receiving_user.user_id:
            latency_ms = (time.time() - receiving_user.last_bid_sent_at) * 1000
            self.metrics.socket_broadcast_latencies_ms.append(latency_ms)
            receiving_user.last_bid_sent_at = None  # Reset
    
    def _handle_timer_sync(self, data: Dict):
        """Handle timer synchronization"""
        self.timer_ends_at = data.get('timerEndsAt')
        remaining = data.get('remainingMs', 0) / 1000
        self.last_timer_remaining = remaining
    
    def _handle_sold(self, data: Dict):
        """Handle lot sold"""
        winner_id = data.get('winnerId')
        winner_name = data.get('winnerName', 'Unknown')
        amount = data.get('amount', 0)
        
        # Find winning user
        winner_email = None
        for user in self.users:
            if user.user_id == winner_id:
                user.bids_won += 1
                user.clubs_won.append(self.current_lot_club_name or 'Unknown')
                user.budget_remaining -= amount
                winner_email = user.email
                break
        
        # Record lot result
        duration = time.time() - (self.lot_start_time or time.time())
        self.metrics.lots_completed.append(LotResult(
            club_name=self.current_lot_club_name or 'Unknown',
            winner_email=winner_email,
            winning_amount=amount,
            total_bids=self.lot_bid_count,
            duration_seconds=duration,
            anti_snipe_triggered=self.metrics.anti_snipe_triggers > 0
        ))
        
        self.lot_active = False
        print(f"   ✓ SOLD: {self.current_lot_club_name} → {winner_name} for £{amount/1_000_000:.1f}M")
    
    def _handle_unsold(self, data: Dict):
        """Handle lot unsold"""
        duration = time.time() - (self.lot_start_time or time.time())
        self.metrics.lots_completed.append(LotResult(
            club_name=self.current_lot_club_name or 'Unknown',
            winner_email=None,
            winning_amount=None,
            total_bids=self.lot_bid_count,
            duration_seconds=duration
        ))
        
        self.lot_active = False
        print(f"   ✗ UNSOLD: {self.current_lot_club_name}")
    
    # ========================================================================
    # BIDDING
    # ========================================================================
    
    async def _place_bid(self, user: TestUser, amount: int) -> bool:
        """Place a bid via HTTP POST"""
        url = f"{BASE_URL}/auction/{self.auction_id}/bid"
        headers = {
            "Authorization": f"Bearer {user.jwt_token}",
            "X-User-ID": user.user_id,
            "Content-Type": "application/json"
        }
        
        user.last_bid_sent_at = time.time()
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json={"amount": amount, "userId": user.user_id}, 
                    headers=headers
                ) as resp:
                    latency_ms = (time.time() - start_time) * 1000
                    success = resp.status == 200
                    
                    error_text = None
                    if not success:
                        error_text = await resp.text()
                        user.bids_failed += 1
                        
                        # Track specific failure reasons
                        if "outbid" in error_text.lower() or "higher" in error_text.lower():
                            user.bids_outbid += 1
                    
                    user.bids_placed += 1
                    
                    self.metrics.bids.append(BidEvent(
                        timestamp=time.time(),
                        user_email=user.email,
                        amount=amount,
                        success=success,
                        latency_ms=latency_ms,
                        error=error_text
                    ))
                    
                    self.metrics.bid_latencies_ms.append(latency_ms)
                    
                    return success
                    
        except Exception as e:
            self.metrics.bids.append(BidEvent(
                timestamp=time.time(),
                user_email=user.email,
                amount=amount,
                success=False,
                latency_ms=0,
                error=str(e)
            ))
            user.bids_failed += 1
            self.metrics.errors.append(f"Bid exception: {e}")
            return False
    
    def _get_next_bid_amount(self, increment: int = 5_000_000) -> int:
        """Calculate next bid amount based on current bid"""
        if self.current_bid == 0:
            return 1_000_000  # Start at £1M
        return self.current_bid + increment
    
    # ========================================================================
    # TEST MODES
    # ========================================================================
    
    async def run_test(self):
        """Execute the selected test mode"""
        self._print_header(f"RUNNING TEST: {self.mode.upper()}")
        
        # Connect all sockets
        await self._connect_all_sockets()
        
        # Begin auction
        print("\n🚀 Beginning auction...")
        await self._begin_auction()
        
        # Fetch initial auction state via HTTP (since Socket.IO may not send initial state)
        print("   Fetching auction state...")
        await self._fetch_auction_state()
        
        # Wait for first lot
        print("   Waiting for first lot...")
        timeout = 10
        while not self.lot_active and timeout > 0:
            await asyncio.sleep(0.5)
            timeout -= 0.5
        
        if not self.lot_active:
            print("   ⚠ No lot started - auction may need manual start")
        
        # Run selected test
        if self.mode == "hot-lot":
            await self._test_hot_lot()
        elif self.mode == "full-auction":
            await self._test_full_auction()
        elif self.mode == "race-condition":
            await self._test_race_condition()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        self.metrics.end_time = time.time()
        
        # Cleanup
        await self._disconnect_all()
    
    async def _test_hot_lot(self):
        """
        HOT LOT TEST
        ------------
        All users bid aggressively on first lot.
        Tests: bid throughput, socket broadcasting, timer accuracy
        """
        print("\n" + "-" * 40)
        print("HOT LOT TEST: All users bidding aggressively")
        print("-" * 40 + "\n")
        
        async def aggressive_bidder(user: TestUser):
            """Bid aggressively with short delays"""
            while self.lot_active and not self.auction_complete:
                # Don't bid if we're already winning
                if self.current_bidder_id == user.user_id:
                    await asyncio.sleep(0.5)
                    continue
                
                # Random delay 0.5-2 seconds
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                if self.lot_active:
                    amount = self._get_next_bid_amount()
                    success = await self._place_bid(user, amount)
                    status = "✓" if success else "✗"
                    print(f"   {status} {user.email[:15]}...: £{amount/1_000_000:.1f}M")
        
        # Run all bidders concurrently
        tasks = [aggressive_bidder(user) for user in self.users]
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300  # 5 minute max
            )
        except asyncio.TimeoutError:
            print("\n⏰ Test timeout (5 minutes)")
    
    async def _test_full_auction(self):
        """
        FULL AUCTION TEST
        -----------------
        Complete auction with variable bidding based on team popularity.
        Tests: sustained load, connection stability, memory usage
        """
        print("\n" + "-" * 40)
        print("FULL AUCTION TEST: Variable bidding strategies")
        print("-" * 40 + "\n")
        
        async def smart_bidder(user: TestUser):
            """Bid based on team popularity"""
            while not self.auction_complete:
                if not self.lot_active:
                    await asyncio.sleep(1)
                    continue
                
                # Don't bid if winning
                if self.current_bidder_id == user.user_id:
                    await asyncio.sleep(1)
                    continue
                
                # Determine strategy based on team
                team = self.current_lot_club_name or ""
                
                if any(hot in team for hot in HOT_TEAMS):
                    delay = random.uniform(0.5, 2.0)
                    bid_chance = 0.9
                elif any(med in team for med in MEDIUM_TEAMS):
                    delay = random.uniform(2.0, 5.0)
                    bid_chance = 0.6
                else:
                    delay = random.uniform(5.0, 10.0)
                    bid_chance = 0.3
                
                await asyncio.sleep(delay)
                
                if self.lot_active and random.random() < bid_chance:
                    amount = self._get_next_bid_amount()
                    success = await self._place_bid(user, amount)
                    if success:
                        print(f"   💰 {user.email[:15]}...: £{amount/1_000_000:.1f}M")
        
        tasks = [smart_bidder(user) for user in self.users]
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=3600  # 1 hour max
            )
        except asyncio.TimeoutError:
            print("\n⏰ Test timeout (1 hour)")
    
    async def _test_race_condition(self):
        """
        RACE CONDITION TEST
        -------------------
        All users bid at exact same moment.
        Tests: bid ordering, conflict resolution, data consistency
        """
        print("\n" + "-" * 40)
        print("RACE CONDITION TEST: Simultaneous bids")
        print("-" * 40 + "\n")
        
        if not self.lot_active:
            print("Waiting for lot to start...")
            while not self.lot_active and not self.auction_complete:
                await asyncio.sleep(0.5)
        
        # Wait for timer to be low (if we can detect it)
        print("Waiting 20 seconds into the lot...")
        await asyncio.sleep(20)
        
        print("\n💥 ALL USERS BIDDING SIMULTANEOUSLY!\n")
        
        # All users bid same amount at same time
        bid_amount = self._get_next_bid_amount()
        
        tasks = [self._place_bid(user, bid_amount) for user in self.users]
        results = await asyncio.gather(*tasks)
        
        # Analyze
        successful = sum(results)
        print(f"\nRace condition results:")
        print(f"   Total bids: {len(results)}")
        print(f"   Accepted: {successful}")
        print(f"   Rejected: {len(results) - successful}")
        
        # Expected: only 1 should succeed (first to arrive)
        if successful > 1:
            print("   ⚠ Multiple bids accepted - potential race condition!")
        elif successful == 1:
            print("   ✓ Only one bid accepted - correct behavior")
        else:
            print("   ⚠ No bids accepted - check bid validation")
        
        # Wait for lot to complete
        await asyncio.sleep(15)
    
    # ========================================================================
    # CLEANUP & REPORTING
    # ========================================================================
    
    async def _disconnect_all(self):
        """Disconnect all Socket.IO clients"""
        for user in self.users:
            if user.socket_client:
                try:
                    await user.socket_client.disconnect()
                except:
                    pass
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self._print_header("STRESS TEST REPORT")
        
        # Overview
        print(f"Test Mode:      {self.mode.upper()}")
        print(f"Duration:       {self.metrics.duration_seconds():.1f} seconds")
        print(f"Users:          {len(self.users)}")
        print(f"League:         {self.league_name}")
        
        # Results summary
        print("\n" + "-" * 40)
        print("RESULTS SUMMARY")
        print("-" * 40)
        
        total_bids = len(self.metrics.bids)
        success_rate = self.metrics.bid_success_rate()
        
        print(f"Lots completed:     {len(self.metrics.lots_completed)}")
        print(f"Total bids:         {total_bids}")
        print(f"Bid success rate:   {success_rate:.1f}%")
        print(f"Anti-snipe triggers:{self.metrics.anti_snipe_triggers}")
        print(f"Socket disconnects: {self.metrics.disconnects}")
        print(f"Errors:             {len(self.metrics.errors)}")
        
        # Latency stats
        if self.metrics.bid_latencies_ms:
            print("\n" + "-" * 40)
            print("BID LATENCY (HTTP POST)")
            print("-" * 40)
            print(f"p50:  {self.metrics.percentile(self.metrics.bid_latencies_ms, 50):.0f}ms")
            print(f"p95:  {self.metrics.percentile(self.metrics.bid_latencies_ms, 95):.0f}ms")
            print(f"p99:  {self.metrics.percentile(self.metrics.bid_latencies_ms, 99):.0f}ms")
            print(f"max:  {max(self.metrics.bid_latencies_ms):.0f}ms")
        
        if self.metrics.socket_broadcast_latencies_ms:
            print("\n" + "-" * 40)
            print("SOCKET BROADCAST LATENCY")
            print("-" * 40)
            print(f"p50:  {self.metrics.percentile(self.metrics.socket_broadcast_latencies_ms, 50):.0f}ms")
            print(f"p95:  {self.metrics.percentile(self.metrics.socket_broadcast_latencies_ms, 95):.0f}ms")
            print(f"p99:  {self.metrics.percentile(self.metrics.socket_broadcast_latencies_ms, 99):.0f}ms")
        
        # Per-user stats
        print("\n" + "-" * 40)
        print("PER-USER STATISTICS")
        print("-" * 40)
        
        for user in self.users:
            total = user.bids_placed
            if total == 0:
                continue
            success_rate = ((total - user.bids_failed) / total) * 100
            print(f"\n{user.email[:35]}...")
            print(f"   Bids: {total} (won: {user.bids_won}, failed: {user.bids_failed})")
            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Clubs won: {len(user.clubs_won)}")
            print(f"   Budget remaining: £{user.budget_remaining/1_000_000:.0f}M")
        
        # Lot results
        if self.metrics.lots_completed:
            print("\n" + "-" * 40)
            print("LOT RESULTS")
            print("-" * 40)
            
            for lot in self.metrics.lots_completed:
                winner = lot.winner_email[:20] + "..." if lot.winner_email else "UNSOLD"
                amount = f"£{lot.winning_amount/1_000_000:.1f}M" if lot.winning_amount else "-"
                print(f"   {lot.club_name[:25]}: {winner} ({amount}, {lot.total_bids} bids)")
        
        # Errors
        if self.metrics.errors:
            print("\n" + "-" * 40)
            print(f"ERRORS ({len(self.metrics.errors)})")
            print("-" * 40)
            for error in self.metrics.errors[:10]:
                print(f"   • {error[:80]}")
            if len(self.metrics.errors) > 10:
                print(f"   ... and {len(self.metrics.errors) - 10} more")
        
        # Recommendations
        print("\n" + "-" * 40)
        print("RECOMMENDATIONS")
        print("-" * 40)
        
        issues = []
        
        if success_rate < 90:
            issues.append("⚠️  Bid success rate below 90% - investigate rejection reasons")
        else:
            print("✅ Bid success rate acceptable (≥90%)")
        
        if self.metrics.disconnects > 0:
            issues.append(f"⚠️  {self.metrics.disconnects} disconnects - check Socket.IO stability")
        else:
            print("✅ No disconnects - Socket.IO stable")
        
        if self.metrics.bid_latencies_ms:
            p99 = self.metrics.percentile(self.metrics.bid_latencies_ms, 99)
            if p99 > 1000:
                issues.append(f"⚠️  p99 latency {p99:.0f}ms - may affect UX")
            else:
                print("✅ Bid latency acceptable (<1s p99)")
        
        if len(self.metrics.errors) > 5:
            issues.append(f"⚠️  {len(self.metrics.errors)} errors - review error logs")
        else:
            print("✅ Error count acceptable")
        
        for issue in issues:
            print(issue)
        
        self._print_header("TEST COMPLETE")
    
    def _print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Auction Stress Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick chaos test on first lot
    python auction_stress_test.py --mode hot-lot --invite-token abc123
    
    # Full auction simulation
    python auction_stress_test.py --mode full-auction --invite-token abc123
    
    # Race condition test
    python auction_stress_test.py --mode race-condition --invite-token abc123
        """
    )
    
    parser.add_argument(
        "--mode", 
        required=True,
        choices=["hot-lot", "full-auction", "race-condition"],
        help="Test mode to run"
    )
    parser.add_argument(
        "--invite-token",
        required=True,
        help="League invite token"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=7,
        help="Number of test users (default: 7)"
    )
    parser.add_argument(
        "--commissioner-email",
        help="Email of the league commissioner (required to start auction)"
    )
    parser.add_argument(
        "--use-existing-members",
        action="store_true",
        help="Use existing league members as test users (for full leagues)"
    )
    
    args = parser.parse_args()
    
    test = AuctionStressTest(
        invite_token=args.invite_token,
        mode=args.mode,
        num_users=args.users,
        commissioner_email=args.commissioner_email,
        use_existing_members=args.use_existing_members
    )
    
    try:
        await test.setup()
        await test.run_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
