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
DEFAULT_COMPETITION = "ucl"  # UEFA Champions League

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
    total_bids: int = 0
    successful_bids: int = 0
    errors: List[str] = field(default_factory=list)
    bid_latencies_ms: List[float] = field(default_factory=list)
    status: str = "pending"

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
    
    def __init__(self, league_index: int, competition: str = DEFAULT_COMPETITION):
        self.league_index = league_index
        self.competition = competition
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
            
            # Step 3: Create members and join
            for i in range(USERS_PER_LEAGUE - 1):  # -1 because commissioner is already a member
                member_email = f"member-{self.league_index}-{i+1}-{timestamp}@stresstest.local"
                member = await self._create_user(member_email)
                await self._join_league(member)
                self.league.members.append(member)
            
            print(f"   [League {self.league_index}] ✓ {len(self.league.members)} members joined")
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
            "competition": self.competition,
            "maxManagers": USERS_PER_LEAGUE,
            "budget": STARTING_BUDGET,
            "teamsPerManager": TEAMS_PER_ROSTER,
            "commissionerId": commissioner.user_id
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
                    self.lot_active = False
                    self.current_bid = 0
                
                @sio.on('unsold')
                async def on_unsold(data):
                    club_id = data.get('clubId')
                    if club_id and club_id not in self._processed_sold_lots:
                        self._processed_sold_lots.add(club_id)
                        self.lots_sold += 1
                    self.lot_active = False
                    self.current_bid = 0
                
                @sio.on('auction_complete')
                async def on_complete(data):
                    self.auction_complete = True
                
                await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
                user.connected = True
                
                # Join auction room
                if self.league.auction_id:
                    await sio.emit('join_auction', {
                        'auctionId': self.league.auction_id,
                        'odIuser': user.user_id
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
            
            # Join all sockets to auction room
            all_users = [self.league.commissioner] + self.league.members
            for user in all_users:
                if user.socket_client and user.connected:
                    await user.socket_client.emit('join_auction', {
                        'auctionId': self.league.auction_id,
                        'userId': user.user_id
                    })
            
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
        """Run bidding until auction completes"""
        timeout = 3600  # 1 hour max
        start = time.time()
        
        async def user_bidder(user: TestUser):
            """Individual user bidding coroutine"""
            while not self.auction_complete and (time.time() - start) < timeout:
                if not self.lot_active:
                    await asyncio.sleep(0.3)
                    continue
                
                # Skip if already winning
                if self.current_bidder_id == user.user_id:
                    await asyncio.sleep(0.5)
                    continue
                
                # Skip if roster full
                if user.teams_won >= TEAMS_PER_ROSTER:
                    await asyncio.sleep(1)
                    continue
                
                # Random delay (realistic bidding behavior)
                await asyncio.sleep(random.uniform(0.3, 2.0))
                
                # Place bid if still active and not winning
                if self.lot_active and self.current_bidder_id != user.user_id:
                    bid_amount = (self.current_bid or 0) + BID_INCREMENT
                    if bid_amount <= user.budget_remaining:
                        success = await self._place_bid(user, bid_amount)
                        if success:
                            user.teams_won += 1
                            user.budget_remaining -= bid_amount
        
        # Run all bidders concurrently
        tasks = [asyncio.create_task(user_bidder(user)) for user in users]
        
        # Wait for auction to complete or timeout
        while not self.auction_complete and (time.time() - start) < timeout:
            await asyncio.sleep(1)
        
        # Cancel remaining tasks
        for task in tasks:
            task.cancel()
    
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
                return False
        except Exception as e:
            self.metrics.errors.append(f"Bid error: {e}")
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
    
    def __init__(self, num_leagues: int, stagger_seconds: int = 5, competition: str = DEFAULT_COMPETITION):
        self.num_leagues = num_leagues
        self.stagger_seconds = stagger_seconds
        self.competition = competition
        self.global_metrics = GlobalMetrics()
        self.league_metrics: List[LeagueMetrics] = []
        self.runners: List[LeagueRunner] = []
    
    async def run(self):
        """Run the full test"""
        print("\n" + "=" * 60)
        print("MULTI-LEAGUE STRESS TEST (Fully Automated)")
        print("=" * 60)
        print(f"Leagues to create:    {self.num_leagues}")
        print(f"Users per league:     {USERS_PER_LEAGUE}")
        print(f"Total users:          {self.num_leagues * USERS_PER_LEAGUE}")
        print(f"Stagger between starts: {self.stagger_seconds}s")
        print(f"Competition:          {self.competition}")
        print("=" * 60)
        
        self.global_metrics.start_time = time.time()
        
        # Phase 1: Create all leagues
        print(f"\n📋 PHASE 1: Creating {self.num_leagues} leagues...")
        
        for i in range(self.num_leagues):
            print(f"\n   Creating League {i + 1}/{self.num_leagues}...")
            runner = LeagueRunner(league_index=i + 1, competition=self.competition)
            success = await runner.setup()
            
            if success:
                self.runners.append(runner)
                self.global_metrics.leagues_created += 1
                self.global_metrics.total_users_created += USERS_PER_LEAGUE
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
        
        print("\n" + "=" * 60)
        print("STRESS TEST REPORT")
        print("=" * 60)
        
        print(f"\n--- SUMMARY ---")
        print(f"Duration:              {duration:.1f}s ({duration/60:.1f} minutes)")
        print(f"Leagues created:       {self.global_metrics.leagues_created}")
        print(f"Leagues completed:     {self.global_metrics.leagues_completed}")
        print(f"Leagues failed:        {self.global_metrics.leagues_failed}")
        print(f"Total users created:   {self.global_metrics.total_users_created}")
        print(f"Total bids placed:     {self.global_metrics.total_bids}")
        print(f"Total lots auctioned:  {self.global_metrics.total_lots}")
        
        if self.global_metrics.all_latencies_ms:
            latencies = sorted(self.global_metrics.all_latencies_ms)
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 100 else latencies[-1]
            
            print(f"\n--- BID LATENCY ---")
            print(f"p50:  {p50:.0f}ms")
            print(f"p95:  {p95:.0f}ms")
            print(f"p99:  {p99:.0f}ms")
            print(f"max:  {max(latencies):.0f}ms")
        
        print(f"\n--- PER-LEAGUE RESULTS ---")
        for metrics in self.league_metrics:
            success_rate = (metrics.successful_bids / metrics.total_bids * 100) if metrics.total_bids > 0 else 0
            duration = metrics.end_time - metrics.start_time if metrics.end_time else 0
            status_icon = "✅" if metrics.status == "completed" else "❌"
            print(f"{status_icon} {metrics.league_name}: {metrics.lots_completed} lots, {metrics.total_bids} bids ({success_rate:.0f}% success), {duration:.0f}s")
        
        if self.global_metrics.errors:
            print(f"\n--- ERRORS ({len(self.global_metrics.errors)}) ---")
            for err in self.global_metrics.errors[:10]:
                print(f"   • {err[:100]}")
        
        # Pilot readiness assessment
        print(f"\n--- PILOT READINESS ---")
        
        if self.global_metrics.leagues_failed == 0:
            print("✅ All leagues completed successfully")
        else:
            fail_rate = self.global_metrics.leagues_failed / self.num_leagues * 100
            print(f"⚠️  {fail_rate:.0f}% of leagues failed - investigate before pilot")
        
        if self.global_metrics.all_latencies_ms:
            p99 = sorted(self.global_metrics.all_latencies_ms)[int(len(self.global_metrics.all_latencies_ms) * 0.99)]
            if p99 < 100:
                print("✅ Bid latency excellent (<100ms p99)")
            elif p99 < 500:
                print("⚠️  Bid latency acceptable - monitor during pilot")
            else:
                print("❌ Bid latency too high - may affect user experience")
        
        avg_lots = self.global_metrics.total_lots / max(self.global_metrics.leagues_completed, 1)
        if avg_lots >= 30:
            print(f"✅ Auctions completing properly ({avg_lots:.0f} avg lots per league)")
        else:
            print(f"⚠️  Auctions may be incomplete ({avg_lots:.0f} avg lots per league)")
        
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
        competition=args.competition
    )
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
