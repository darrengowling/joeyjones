#!/usr/bin/env python3
"""
Sport X - Multi-League Concurrent Stress Test (Fully Automated)
================================================================

Automatically creates leagues and users, then runs concurrent auctions.
No manual setup required.

WHAT IT DOES:
-------------
1. Creates N commissioner users (via magic link)
2. Each commissioner creates a league
3. Creates 7 additional users per league
4. All users join their respective leagues
5. Auctions start and run concurrently
6. Reports aggregate results

PILOT SCENARIO:
---------------
- 10-20 leagues running concurrently
- 8 users per league (1 commissioner + 7 members)
- 32 teams per auction (4 per user roster)
- Full auction completion

REQUIREMENTS:
-------------
pip install "python-socketio[asyncio_client]" aiohttp

USAGE:
------
# Test against production with 10 concurrent leagues
python multi_league_stress_test.py --leagues 10 --url https://your-app.emergent.sh

# Quick single-league validation
python multi_league_stress_test.py --leagues 1 --url https://your-app.emergent.sh

# Local/preview test
python multi_league_stress_test.py --leagues 5
"""

import asyncio
import aiohttp
import socketio
import json
import time
import argparse
import random
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_BASE_URL = "http://localhost:8001/api"
DEFAULT_SOCKET_URL = "http://localhost:8001"
SOCKET_PATH = "/api/socket.io"

# Will be set from CLI
BASE_URL = DEFAULT_BASE_URL
SOCKET_URL = DEFAULT_SOCKET_URL

# League/Auction settings
USERS_PER_LEAGUE = 8
TEAMS_PER_ROSTER = 4
BID_INCREMENT = 5_000_000  # £5M
STARTING_BUDGET = 500_000_000  # £500M
DEFAULT_COMPETITION = "CL"  # UEFA Champions League (CL or UCL accepted)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TestUser:
    """Represents a test user"""
    email: str
    user_id: Optional[str] = None
    jwt_token: Optional[str] = None
    budget_remaining: int = STARTING_BUDGET
    teams_won: int = 0
    bids_placed: int = 0
    bids_won: int = 0
    socket_client: Optional[socketio.AsyncClient] = None
    connected: bool = False
    is_commissioner: bool = False

@dataclass 
class TestLeague:
    """Represents a test league"""
    league_id: Optional[str] = None
    league_name: str = ""
    invite_token: Optional[str] = None
    commissioner: Optional[TestUser] = None
    members: List[TestUser] = field(default_factory=list)
    auction_id: Optional[str] = None

@dataclass
class LeagueMetrics:
    """Metrics for a single league's auction"""
    league_name: str = ""
    start_time: float = 0
    end_time: float = 0
    lots_completed: int = 0
    lots_sold: int = 0
    lots_unsold: int = 0
    total_bids: int = 0
    successful_bids: int = 0
    failed_bids: int = 0
    socket_events_received: int = 0
    socket_connected_users: int = 0
    errors: List[str] = field(default_factory=list)
    bid_latencies_ms: List[float] = field(default_factory=list)
    bid_rejection_reasons: Dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    rosters_filled: int = 0
    total_spend: int = 0

@dataclass
class GlobalMetrics:
    """Aggregate metrics across all leagues"""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    leagues_created: int = 0
    leagues_completed: int = 0
    leagues_failed: int = 0
    total_users_created: int = 0
    total_bids: int = 0
    total_lots: int = 0
    all_latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

# ============================================================================
# SINGLE LEAGUE RUNNER
# ============================================================================

class LeagueRunner:
    """Creates and runs a single league auction"""
    
    def __init__(self, league_index: int, competition: str = DEFAULT_COMPETITION, users_per_league: int = USERS_PER_LEAGUE, teams_per_roster: int = TEAMS_PER_ROSTER):
        self.league_index = league_index
        self.competition = competition
        self.users_per_league = users_per_league
        self.teams_per_roster = teams_per_roster
        self.league = TestLeague()
        self.metrics = LeagueMetrics()
        
        # Auction state
        self.current_bid: int = 0
        self.current_bidder_id: Optional[str] = None
        self.current_club_name: Optional[str] = None
        self.lot_active: bool = False
        self.auction_complete: bool = False
        self.lots_sold: int = 0
        self._processed_sold_lots: set = set()
    
    async def setup(self) -> bool:
        """Create commissioner, league, and members. Returns True if successful."""
        try:
            # Step 1: Create commissioner
            timestamp = int(time.time() * 1000)
            commissioner_email = f"commissioner-{self.league_index}-{timestamp}@stresstest.local"
            self.league.commissioner = await self._create_user(commissioner_email, is_commissioner=True)
            print(f"   [League {self.league_index}] ✓ Commissioner created")
            
            # Step 2: Create league
            await self._create_league()
            print(f"   [League {self.league_index}] ✓ League created: {self.league.league_name}")
            
            # Step 3: Commissioner must join their own league (not automatic)
            await self._join_league(self.league.commissioner)
            
            # Step 4: Create additional members and join
            for i in range(self.users_per_league - 1):
                member_email = f"member-{self.league_index}-{i+1}-{timestamp}@stresstest.local"
                member = await self._create_user(member_email)
                await self._join_league(member)
                self.league.members.append(member)
            
            print(f"   [League {self.league_index}] ✓ {len(self.league.members) + 1} users joined")
            return True
            
        except Exception as e:
            self.metrics.status = f"setup_failed: {e}"
            self.metrics.errors.append(f"Setup failed: {e}")
            print(f"   [League {self.league_index}] ❌ Setup failed: {e}")
            return False
    
    async def run_auction(self) -> LeagueMetrics:
        """Run the auction and return metrics"""
        self.metrics.league_name = self.league.league_name
        self.metrics.start_time = time.time()
        self.metrics.status = "running"
        
        try:
            # Connect all users to Socket.IO
            all_users = [self.league.commissioner] + self.league.members
            print(f"   [League {self.league_index}] Users in auction: {len(all_users)} - {[u.email[:20] for u in all_users]}")
            await self._connect_all_sockets(all_users)
            
            # Start auction
            await self._start_auction()
            print(f"   [League {self.league_index}] ✓ Auction started")
            
            # Run bidding loop
            await self._run_bidding_loop(all_users)
            
            self.metrics.status = "completed"
            self.metrics.lots_completed = self.lots_sold
            
        except Exception as e:
            self.metrics.status = f"failed: {e}"
            self.metrics.errors.append(str(e))
            print(f"   [League {self.league_index}] ❌ Auction failed: {e}")
        
        finally:
            await self._cleanup()
            self.metrics.end_time = time.time()
        
        return self.metrics
    
    async def _create_user(self, email: str, is_commissioner: bool = False) -> TestUser:
        """Create and authenticate a user via magic link"""
        user = TestUser(email=email, is_commissioner=is_commissioner)
        
        async with aiohttp.ClientSession() as session:
            # Request magic link
            resp = await session.post(f"{BASE_URL}/auth/magic-link", json={"email": email})
            if resp.status != 200:
                raise Exception(f"Magic link request failed: {await resp.text()}")
            data = await resp.json()
            token = data.get('token')
            
            if not token:
                raise Exception("No token in magic link response - is this production mode?")
            
            # Verify magic link
            resp = await session.post(
                f"{BASE_URL}/auth/verify-magic-link",
                json={"email": email, "token": token}
            )
            if resp.status != 200:
                raise Exception(f"Magic link verify failed: {await resp.text()}")
            
            data = await resp.json()
            user.jwt_token = data.get('accessToken') or data.get('token')
            user.user_id = data['user']['id']
        
        return user
    
    async def _create_league(self):
        """Create a new league"""
        commissioner = self.league.commissioner
        league_name = f"StressTest-{self.league_index}-{int(time.time())}"
        
        headers = {
            "Authorization": f"Bearer {commissioner.jwt_token}",
            "X-User-ID": commissioner.user_id
        }
        
        payload = {
            "name": league_name,
            "competitionCode": self.competition,
            "maxManagers": self.users_per_league,
            "budget": STARTING_BUDGET,
            "clubSlots": self.teams_per_roster,
            "commissionerId": commissioner.user_id,
            "timerSeconds": 10  # Short timer for testing
        }
        
        async with aiohttp.ClientSession() as session:
            resp = await session.post(f"{BASE_URL}/leagues", json=payload, headers=headers)
            if resp.status not in [200, 201]:
                raise Exception(f"League creation failed: {await resp.text()}")
            
            data = await resp.json()
            self.league.league_id = data.get('id') or data.get('leagueId')
            self.league.league_name = league_name
            self.league.invite_token = data.get('inviteToken')
    
    async def _join_league(self, user: TestUser):
        """Join a user to the league"""
        headers = {"Authorization": f"Bearer {user.jwt_token}"}
        payload = {
            "inviteToken": self.league.invite_token,
            "userId": user.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{BASE_URL}/leagues/{self.league.league_id}/join",
                json=payload,
                headers=headers
            )
            if resp.status not in [200, 409]:  # 409 = already joined
                raise Exception(f"Join failed: {await resp.text()}")
    
    async def _connect_all_sockets(self, users: List[TestUser]):
        """Connect all users to Socket.IO"""
        for user in users:
            try:
                sio = socketio.AsyncClient(reconnection=False)
                user.socket_client = sio
                
                # Event handlers (closure captures self)
                @sio.on('bid_update')
                async def on_bid_update(data):
                    self.current_bid = data.get('amount', 0)
                    bidder = data.get('bidder', {})
                    self.current_bidder_id = bidder.get('userId') if isinstance(bidder, dict) else None
                
                @sio.on('lot_started')
                async def on_lot_started(data):
                    club = data.get('club', {})
                    self.current_club_name = club.get('name', 'Unknown')
                    self.current_bid = 0
                    self.current_bidder_id = None
                    self.lot_active = True
                
                @sio.on('sold')
                async def on_sold(data):
                    club_id = data.get('clubId')
                    if club_id and club_id not in self._processed_sold_lots:
                        self._processed_sold_lots.add(club_id)
                        self.lots_sold += 1
                        self.metrics.lots_sold += 1
                        self.metrics.socket_events_received += 1
                        # Track winning bid amount
                        winning_bid = data.get('winningBid', {})
                        if winning_bid:
                            self.metrics.total_spend += winning_bid.get('amount', 0)
                    self.lot_active = False
                    self.current_bid = 0
                
                @sio.on('unsold')
                async def on_unsold(data):
                    self.metrics.lots_unsold += 1
                    self.metrics.socket_events_received += 1
                    self.lot_active = False
                    self.current_bid = 0
                
                @sio.on('auction_complete')
                async def on_complete(data):
                    self.auction_complete = True
                
                await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
                user.connected = True
                
                # Join auction room if we have an auction ID
                if self.league.auction_id:
                    await sio.emit('join_auction', {
                        'auctionId': self.league.auction_id,
                        'userId': user.user_id
                    })
                
            except Exception as e:
                self.metrics.errors.append(f"Socket connect failed for {user.email}: {e}")
    
    async def _start_auction(self):
        """Start the auction"""
        commissioner = self.league.commissioner
        headers = {
            "Authorization": f"Bearer {commissioner.jwt_token}",
            "X-User-ID": commissioner.user_id
        }
        
        async with aiohttp.ClientSession() as session:
            # Start auction
            resp = await session.post(
                f"{BASE_URL}/leagues/{self.league.league_id}/auction/start",
                headers=headers
            )
            if resp.status != 200:
                raise Exception(f"Auction start failed: {await resp.text()}")
            
            data = await resp.json()
            self.league.auction_id = data.get('auctionId')
            
            # NOW join all sockets to auction room (after we have the auction ID)
            all_users = [self.league.commissioner] + self.league.members
            for user in all_users:
                if user.socket_client and user.connected:
                    try:
                        await user.socket_client.emit('join_auction', {
                            'auctionId': self.league.auction_id,
                            'userId': user.user_id
                        })
                    except Exception as e:
                        self.metrics.errors.append(f"join_auction emit failed: {e}")
            
            await asyncio.sleep(0.5)  # Wait for room joins to process
            
            # Begin auction (start first lot)
            resp = await session.post(
                f"{BASE_URL}/auction/{self.league.auction_id}/begin",
                headers=headers
            )
            # Ignore "already active" errors
            
            # Fetch initial state
            resp = await session.get(
                f"{BASE_URL}/auction/{self.league.auction_id}",
                headers=headers
            )
            if resp.status == 200:
                data = await resp.json()
                auction = data.get('auction', {})
                if auction.get('status') == 'active':
                    self.lot_active = True
                    self.current_bid = auction.get('currentBid') or 0
    
    async def _run_bidding_loop(self, users: List[TestUser]):
        """
        Run bidding until auction completes.
        
        CRITICAL FIX: The anti-snipe timer extends every time a bid is placed.
        If we bid continuously, the timer never expires and no lots sell.
        
        Strategy:
        1. Only bid if we are NOT the current high bidder
        2. After bidding, WAIT for the timer to expire (let the other side respond or timer run out)
        3. Use a longer poll interval than the anti-snipe window
        """
        timeout = 600  # 10 min max
        start = time.time()
        
        # Get league's timer settings (default 10s timer + 10s anti-snipe)
        timer_seconds = 15  # Wait time after bidding (should be > anti-snipe)
        
        # Track which lot we're on to detect lot transitions
        last_lot_id = None
        bid_placed_this_lot = {}  # Track which users bid on current lot
        
        while not self.auction_complete and (time.time() - start) < timeout:
            # Poll current auction state
            state = await self._get_auction_state()
            if not state:
                await asyncio.sleep(2)
                continue
            
            if state.get('status') == 'completed':
                self.auction_complete = True
                print(f"   [League {self.league_index}] ✓ Auction completed!")
                break
            
            current_lot_id = state.get('lotId')
            current_bid = state.get('currentBid') or 0
            current_bidder = state.get('currentBidderId')
            
            # Detect lot transition (new lot started)
            if current_lot_id != last_lot_id:
                last_lot_id = current_lot_id
                bid_placed_this_lot = {}  # Reset tracking for new lot
                
                # Update lots_sold from completedLots
                completed = state.get('completedLots', [])
                sold_count = len([c for c in completed if c.get('sold')])
                if sold_count > self.lots_sold:
                    self.lots_sold = sold_count
                    self.metrics.lots_sold = sold_count
            
            # ---- BIDDING LOGIC ----
            # Key insight: We want ONE user to bid, then WAIT.
            # If no one bids, the timer expires and lot sells (or goes unsold).
            # IMPORTANT: Alternate between users to ensure fair distribution
            
            # Select a bidder: rotate through users who are eligible
            # Use lot number to help distribute lots among users
            lot_num = state.get('currentLot', 0)
            
            bidder_selected = None
            eligible_users = []
            
            for user in users:
                # Skip if already the highest bidder on this lot
                if current_bidder == user.user_id:
                    continue
                
                # Skip if user's roster is full
                user_roster_count = state.get('rosters', {}).get(user.user_id, 0)
                if user_roster_count >= self.teams_per_roster:
                    user.teams_won = user_roster_count  # Track locally
                    continue
                
                # Check budget
                bid_amount = current_bid + BID_INCREMENT
                if bid_amount > user.budget_remaining:
                    continue
                
                # This user is eligible
                eligible_users.append(user)
            
            # Pick one eligible user - prefer users with fewer teams
            if eligible_users:
                # Sort by roster count (ascending) - users with fewer teams bid first
                eligible_users.sort(key=lambda u: state.get('rosters', {}).get(u.user_id, 0))
                bidder_selected = eligible_users[0]
            
            if bidder_selected:
                bid_amount = current_bid + BID_INCREMENT
                success = await self._place_bid(bidder_selected, bid_amount)
                
                if success:
                    print(f"      [League {self.league_index}] Bid OK: {bidder_selected.email[:20]}... bid £{bid_amount/1_000_000:.0f}M")
                    # After successful bid, WAIT for timer to potentially expire
                    # This is critical - don't bid again immediately!
                    await asyncio.sleep(timer_seconds)
                else:
                    # Bid failed - get the reason from metrics
                    last_reason = list(self.metrics.bid_rejection_reasons.keys())[-1] if self.metrics.bid_rejection_reasons else "unknown"
                    print(f"      [League {self.league_index}] Bid FAIL: {last_reason[:40]}")
                    await asyncio.sleep(2)
            else:
                # No one can/should bid - wait for timer to expire
                # This happens when:
                # - Current bidder's roster is full (they win by default)
                # - Or everyone's roster is full (auction ending)
                print(f"      [League {self.league_index}] No bidder selected (current={current_bidder[:8] if current_bidder else 'none'})")
                await asyncio.sleep(timer_seconds)
            
            # Progress update every 30 seconds
            elapsed = time.time() - start
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                all_filled = all(
                    state.get('rosters', {}).get(u.user_id, 0) >= self.teams_per_roster 
                    for u in users
                )
                status = "ALL FILLED" if all_filled else f"bidder={current_bidder[:8] if current_bidder else 'none'}"
                print(f"   [League {self.league_index}] {self.lots_sold} lots sold, {self.metrics.total_bids} bids, {elapsed:.0f}s [{status}]")
    
    async def _get_auction_state(self) -> Optional[Dict]:
        """Get current auction state via HTTP"""
        try:
            headers = {"Authorization": f"Bearer {self.league.commissioner.jwt_token}"}
            async with aiohttp.ClientSession() as session:
                resp = await session.get(f"{BASE_URL}/auction/{self.league.auction_id}", headers=headers)
                if resp.status == 200:
                    data = await resp.json()
                    auction = data.get('auction', {})
                    
                    # Get completed lots
                    completed_lots = auction.get('completedLots') or []
                    
                    # Update local tracking
                    self.lots_sold = len([c for c in completed_lots if c.get('sold')])
                    
                    # Build roster counts from completedLots
                    rosters = {}
                    for lot in completed_lots:
                        if lot.get('sold') and lot.get('winnerId'):
                            rosters[lot['winnerId']] = rosters.get(lot['winnerId'], 0) + 1
                    
                    return {
                        'status': auction.get('status'),
                        'currentBid': auction.get('currentBid') or 0,
                        'currentBidderId': auction.get('currentBidder', {}).get('userId') if auction.get('currentBidder') else None,
                        'lotId': auction.get('currentLotId') or auction.get('currentClubId'),
                        'currentLot': auction.get('currentLot', 0),
                        'rosters': rosters,
                        'completedLots': completed_lots
                    }
        except Exception as e:
            self.metrics.errors.append(f"Poll error: {e}")
        return None
    
    async def _place_bid(self, user: TestUser, amount: int) -> bool:
        """Place a bid"""
        headers = {
            "Authorization": f"Bearer {user.jwt_token}",
            "X-User-ID": user.user_id,
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{BASE_URL}/auction/{self.league.auction_id}/bid",
                    json={"amount": amount, "userId": user.user_id},
                    headers=headers
                )
                latency = (time.time() - start_time) * 1000
                self.metrics.bid_latencies_ms.append(latency)
                self.metrics.total_bids += 1
                user.bids_placed += 1
                
                if resp.status == 200:
                    self.metrics.successful_bids += 1
                    return True
                else:
                    self.metrics.failed_bids += 1
                    # Track rejection reason
                    try:
                        error_data = await resp.json()
                        reason = error_data.get('detail', str(resp.status))
                        if isinstance(reason, list):
                            reason = reason[0].get('msg', str(resp.status)) if reason else str(resp.status)
                    except:
                        reason = str(resp.status)
                    
                    # Categorize the reason
                    reason_key = reason[:50]  # Truncate for grouping
                    self.metrics.bid_rejection_reasons[reason_key] = self.metrics.bid_rejection_reasons.get(reason_key, 0) + 1
                    return False
        except Exception as e:
            self.metrics.errors.append(f"Bid error: {e}")
            self.metrics.failed_bids += 1
            return False
    
    async def _cleanup(self):
        """Disconnect all sockets"""
        all_users = [self.league.commissioner] + self.league.members
        for user in all_users:
            if user.socket_client:
                try:
                    await user.socket_client.disconnect()
                except:
                    pass


# ============================================================================
# MULTI-LEAGUE ORCHESTRATOR
# ============================================================================

class MultiLeagueStressTest:
    """Orchestrates multiple concurrent league auctions"""
    
    def __init__(self, num_leagues: int, stagger_seconds: int = 5, competition: str = DEFAULT_COMPETITION, users_per_league: int = USERS_PER_LEAGUE, teams_per_roster: int = TEAMS_PER_ROSTER):
        self.num_leagues = num_leagues
        self.stagger_seconds = stagger_seconds
        self.competition = competition
        self.users_per_league = users_per_league
        self.teams_per_roster = teams_per_roster
        self.global_metrics = GlobalMetrics()
        self.league_metrics: List[LeagueMetrics] = []
        self.runners: List[LeagueRunner] = []
    
    async def run(self):
        """Run the full test"""
        print("\n" + "=" * 60)
        print("MULTI-LEAGUE STRESS TEST (Fully Automated)")
        print("=" * 60)
        print(f"Leagues to create:    {self.num_leagues}")
        print(f"Users per league:     {self.users_per_league}")
        print(f"Teams per roster:     {self.teams_per_roster}")
        print(f"Total users:          {self.num_leagues * self.users_per_league}")
        print(f"Stagger between starts: {self.stagger_seconds}s")
        print(f"Competition:          {self.competition}")
        print("=" * 60)
        
        self.global_metrics.start_time = time.time()
        
        # Phase 1: Create all leagues
        print(f"\n📋 PHASE 1: Creating {self.num_leagues} leagues...")
        
        for i in range(self.num_leagues):
            print(f"\n   Creating League {i + 1}/{self.num_leagues}...")
            runner = LeagueRunner(
                league_index=i + 1, 
                competition=self.competition,
                users_per_league=self.users_per_league,
                teams_per_roster=self.teams_per_roster
            )
            success = await runner.setup()
            
            if success:
                self.runners.append(runner)
                self.global_metrics.leagues_created += 1
                self.global_metrics.total_users_created += self.users_per_league
            else:
                self.global_metrics.leagues_failed += 1
        
        print(f"\n✓ Created {self.global_metrics.leagues_created} leagues with {self.global_metrics.total_users_created} users")
        
        if not self.runners:
            print("\n❌ No leagues created successfully. Aborting.")
            return
        
        # Phase 2: Run auctions concurrently with stagger
        print(f"\n🚀 PHASE 2: Starting {len(self.runners)} auctions...")
        
        async def run_with_stagger(runner: LeagueRunner, delay: float):
            if delay > 0:
                await asyncio.sleep(delay)
            print(f"   [League {runner.league_index}] Starting auction...")
            return await runner.run_auction()
        
        tasks = []
        for i, runner in enumerate(self.runners):
            delay = i * self.stagger_seconds
            task = asyncio.create_task(run_with_stagger(runner, delay))
            tasks.append(task)
        
        # Wait for all auctions
        print(f"\n⏳ Waiting for all auctions to complete...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect metrics
        for result in results:
            if isinstance(result, LeagueMetrics):
                self.league_metrics.append(result)
                self.global_metrics.total_bids += result.total_bids
                self.global_metrics.total_lots += result.lots_completed
                self.global_metrics.all_latencies_ms.extend(result.bid_latencies_ms)
                if result.status == "completed":
                    self.global_metrics.leagues_completed += 1
                else:
                    self.global_metrics.leagues_failed += 1
                    self.global_metrics.errors.append(f"{result.league_name}: {result.status}")
        
        self.global_metrics.end_time = time.time()
        self._generate_report()
    
    def _generate_report(self):
        """Generate comprehensive report"""
        duration = self.global_metrics.end_time - self.global_metrics.start_time
        
        print("\n" + "=" * 70)
        print("STRESS TEST REPORT")
        print("=" * 70)
        
        # === EXECUTIVE SUMMARY ===
        print(f"\n{'='*70}")
        print("EXECUTIVE SUMMARY")
        print(f"{'='*70}")
        print(f"Test Duration:         {duration:.1f}s ({duration/60:.1f} minutes)")
        print(f"Leagues Created:       {self.global_metrics.leagues_created}")
        print(f"Leagues Completed:     {self.global_metrics.leagues_completed}")
        print(f"Leagues Failed:        {self.global_metrics.leagues_failed}")
        print(f"Total Users:           {self.global_metrics.total_users_created}")
        print(f"Total Bids:            {self.global_metrics.total_bids}")
        print(f"Total Lots Auctioned:  {self.global_metrics.total_lots}")
        
        # === BID LATENCY ANALYSIS ===
        print(f"\n{'='*70}")
        print("BID LATENCY ANALYSIS")
        print(f"{'='*70}")
        if self.global_metrics.all_latencies_ms:
            latencies = sorted(self.global_metrics.all_latencies_ms)
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 100 else latencies[-1]
            avg = sum(latencies) / len(latencies)
            
            print(f"Samples:    {len(latencies)}")
            print(f"Average:    {avg:.1f}ms")
            print(f"p50:        {p50:.0f}ms")
            print(f"p95:        {p95:.0f}ms")
            print(f"p99:        {p99:.0f}ms")
            print(f"Max:        {max(latencies):.0f}ms")
            print(f"Min:        {min(latencies):.0f}ms")
            
            # Latency distribution
            under_50 = len([l for l in latencies if l < 50])
            under_100 = len([l for l in latencies if l < 100])
            under_500 = len([l for l in latencies if l < 500])
            print(f"\nDistribution:")
            print(f"  <50ms:    {under_50} ({under_50/len(latencies)*100:.1f}%)")
            print(f"  <100ms:   {under_100} ({under_100/len(latencies)*100:.1f}%)")
            print(f"  <500ms:   {under_500} ({under_500/len(latencies)*100:.1f}%)")
        else:
            print("No latency data collected")
        
        # === BID SUCCESS ANALYSIS ===
        print(f"\n{'='*70}")
        print("BID SUCCESS ANALYSIS")
        print(f"{'='*70}")
        total_success = sum(m.successful_bids for m in self.league_metrics)
        total_failed = sum(m.failed_bids for m in self.league_metrics)
        total_bids = total_success + total_failed
        success_rate = (total_success / total_bids * 100) if total_bids > 0 else 0
        
        print(f"Total Bids:      {total_bids}")
        print(f"Successful:      {total_success} ({success_rate:.1f}%)")
        print(f"Failed:          {total_failed} ({100-success_rate:.1f}%)")
        
        # Aggregate rejection reasons
        all_reasons = {}
        for m in self.league_metrics:
            for reason, count in m.bid_rejection_reasons.items():
                all_reasons[reason] = all_reasons.get(reason, 0) + count
        
        if all_reasons:
            print(f"\nBid Rejection Reasons:")
            for reason, count in sorted(all_reasons.items(), key=lambda x: -x[1])[:10]:
                print(f"  {count:5d}x  {reason[:60]}")
        
        # === AUCTION COMPLETION ANALYSIS ===
        print(f"\n{'='*70}")
        print("AUCTION COMPLETION ANALYSIS")
        print(f"{'='*70}")
        total_sold = sum(m.lots_sold for m in self.league_metrics)
        total_unsold = sum(m.lots_unsold for m in self.league_metrics)
        total_spend = sum(m.total_spend for m in self.league_metrics)
        
        print(f"Lots Sold:       {total_sold}")
        print(f"Lots Unsold:     {total_unsold} (re-offered)")
        print(f"Total Spend:     £{total_spend/1_000_000:.1f}M")
        if total_sold > 0:
            print(f"Avg Price:       £{total_spend/total_sold/1_000_000:.1f}M per team")
        
        # === PER-LEAGUE DETAILS ===
        print(f"\n{'='*70}")
        print("PER-LEAGUE DETAILS")
        print(f"{'='*70}")
        for metrics in self.league_metrics:
            success_rate = (metrics.successful_bids / metrics.total_bids * 100) if metrics.total_bids > 0 else 0
            duration = metrics.end_time - metrics.start_time if metrics.end_time else 0
            status_icon = "✅" if metrics.status == "completed" else "❌"
            
            print(f"\n{status_icon} {metrics.league_name}")
            print(f"   Status:       {metrics.status}")
            print(f"   Duration:     {duration:.0f}s")
            print(f"   Lots Sold:    {metrics.lots_sold}")
            print(f"   Lots Unsold:  {metrics.lots_unsold}")
            print(f"   Total Bids:   {metrics.total_bids}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Total Spend:  £{metrics.total_spend/1_000_000:.1f}M")
            print(f"   Socket Events: {metrics.socket_events_received}")
            if metrics.errors:
                print(f"   Errors:       {len(metrics.errors)}")
                for err in metrics.errors[:3]:
                    print(f"      - {err[:70]}")
        
        # === SOCKET.IO HEALTH ===
        print(f"\n{'='*70}")
        print("SOCKET.IO HEALTH")
        print(f"{'='*70}")
        total_socket_events = sum(m.socket_events_received for m in self.league_metrics)
        print(f"Total Events Received: {total_socket_events}")
        if total_socket_events == 0:
            print("⚠️  WARNING: No Socket.IO events received - users may not be in auction rooms!")
        
        # === ERRORS ===
        if self.global_metrics.errors:
            print(f"\n{'='*70}")
            print(f"ERRORS ({len(self.global_metrics.errors)})")
            print(f"{'='*70}")
            for err in self.global_metrics.errors[:15]:
                print(f"   • {err[:100]}")
        
        # === PILOT READINESS ASSESSMENT ===
        print(f"\n{'='*70}")
        print("PILOT READINESS ASSESSMENT")
        print(f"{'='*70}")
        
        issues = []
        warnings = []
        passes = []
        
        # Check 1: League completion
        if self.global_metrics.leagues_failed == 0:
            passes.append("All leagues completed successfully")
        else:
            fail_rate = self.global_metrics.leagues_failed / self.num_leagues * 100
            issues.append(f"{fail_rate:.0f}% of leagues failed")
        
        # Check 2: Latency
        if self.global_metrics.all_latencies_ms:
            p99 = sorted(self.global_metrics.all_latencies_ms)[int(len(self.global_metrics.all_latencies_ms) * 0.99)]
            if p99 < 100:
                passes.append(f"Bid latency excellent (p99={p99:.0f}ms)")
            elif p99 < 500:
                warnings.append(f"Bid latency acceptable but monitor (p99={p99:.0f}ms)")
            else:
                issues.append(f"Bid latency too high (p99={p99:.0f}ms)")
        
        # Check 3: Socket events
        if total_socket_events > 0:
            passes.append(f"Socket.IO events flowing ({total_socket_events} received)")
        else:
            issues.append("No Socket.IO events received - room join may be broken")
        
        # Check 4: Bid success rate
        if success_rate >= 30:
            passes.append(f"Bid success rate healthy ({success_rate:.1f}%)")
        else:
            warnings.append(f"Bid success rate low ({success_rate:.1f}%) - check bidding logic")
        
        # Check 5: Lots sold
        expected_lots = self.global_metrics.leagues_completed * 32  # 32 teams per UCL auction
        if total_sold >= expected_lots * 0.8:
            passes.append(f"Auction lots selling ({total_sold} sold)")
        else:
            warnings.append(f"Low lot completion ({total_sold}/{expected_lots} expected)")
        
        print("\n🟢 PASSED:")
        for p in passes:
            print(f"   ✅ {p}")
        
        if warnings:
            print("\n🟡 WARNINGS:")
            for w in warnings:
                print(f"   ⚠️  {w}")
        
        if issues:
            print("\n🔴 ISSUES:")
            for i in issues:
                print(f"   ❌ {i}")
        
        # Final verdict
        print(f"\n{'='*70}")
        if not issues and not warnings:
            print("🎉 VERDICT: READY FOR PILOT")
        elif not issues:
            print("⚠️  VERDICT: PROCEED WITH CAUTION - Review warnings")
        else:
            print("❌ VERDICT: NOT READY - Fix issues before pilot")
        print(f"{'='*70}")
        
        print("\n" + "=" * 60)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    global BASE_URL, SOCKET_URL
    
    parser = argparse.ArgumentParser(
        description="Multi-League Stress Test - Fully Automated",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick test with 1 league (validation)
    python multi_league_stress_test.py --leagues 1

    # Test against production with 10 concurrent leagues
    python multi_league_stress_test.py --leagues 10 --url https://your-app.emergent.sh

    # Full pilot simulation (20 leagues, staggered start)
    python multi_league_stress_test.py --leagues 20 --stagger 30 --url https://your-app.emergent.sh
        """
    )
    
    parser.add_argument(
        "--leagues",
        type=int,
        default=5,
        help="Number of leagues to create and test (default: 5)"
    )
    parser.add_argument(
        "--url",
        help="Production URL (e.g., https://your-app.emergent.sh)"
    )
    parser.add_argument(
        "--stagger",
        type=int,
        default=10,
        help="Seconds between league auction starts (default: 10)"
    )
    parser.add_argument(
        "--competition",
        default=DEFAULT_COMPETITION,
        help=f"Competition type for leagues (default: {DEFAULT_COMPETITION})"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=USERS_PER_LEAGUE,
        help=f"Users per league (default: {USERS_PER_LEAGUE})"
    )
    parser.add_argument(
        "--teams",
        type=int,
        default=TEAMS_PER_ROSTER,
        help=f"Teams per user roster (default: {TEAMS_PER_ROSTER})"
    )
    
    args = parser.parse_args()
    
    # Set URLs
    if args.url:
        base = args.url.rstrip('/')
        BASE_URL = f"{base}/api"
        SOCKET_URL = base
        print(f"🌐 Target: {base}")
    else:
        print("🏠 Target: localhost:8001 (use --url for production)")
    
    # Run test
    test = MultiLeagueStressTest(
        num_leagues=args.leagues,
        stagger_seconds=args.stagger,
        competition=args.competition,
        users_per_league=args.users,
        teams_per_roster=args.teams
    )
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
