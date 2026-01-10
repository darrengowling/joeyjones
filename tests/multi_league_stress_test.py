#!/usr/bin/env python3
"""
Sport X - Multi-League Concurrent Stress Test
==============================================

Simulates multiple leagues running auctions simultaneously to test
infrastructure under realistic pilot conditions.

PILOT SCENARIO:
---------------
- 10-20 leagues running concurrently
- 8 users per league
- 32 teams per auction (4 per user roster)
- Full auction completion

WHAT THIS TESTS:
----------------
1. MongoDB write capacity across multiple leagues
2. Socket.IO room isolation and broadcast efficiency
3. Timer management across concurrent auctions
4. Overall system stability under realistic load

REQUIREMENTS:
-------------
- Pre-created test leagues with invite tokens
- Commissioner access for each league
- pip install "python-socketio[asyncio_client]" aiohttp

Usage:
    # Test with a config file listing leagues
    python multi_league_stress_test.py --config leagues.json --url https://your-app.emergent.sh

    # Quick test with single league (validates setup)
    python multi_league_stress_test.py --quick-test --invite-token TOKEN --commissioner-email EMAIL --url URL

Config file format (leagues.json):
    {
        "leagues": [
            {"invite_token": "abc123", "commissioner_email": "user1@example.com"},
            {"invite_token": "def456", "commissioner_email": "user2@example.com"},
            ...
        ]
    }
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
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_BASE_URL = "http://localhost:8001/api"
DEFAULT_SOCKET_URL = "http://localhost:8001"
SOCKET_PATH = "/api/socket.io"

# Will be set from CLI
BASE_URL = DEFAULT_BASE_URL
SOCKET_URL = DEFAULT_SOCKET_URL

# Auction settings
USERS_PER_LEAGUE = 8
TEAMS_PER_AUCTION = 32
TEAMS_PER_ROSTER = 4
BID_INCREMENT = 5_000_000  # £5M

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TestUser:
    """Represents a test user in a league"""
    email: str
    user_id: Optional[str] = None
    jwt_token: Optional[str] = None
    budget_remaining: int = 500_000_000
    teams_won: int = 0
    bids_placed: int = 0
    bids_won: int = 0
    socket_client: Optional[socketio.AsyncClient] = None
    connected: bool = False

@dataclass
class LeagueMetrics:
    """Metrics for a single league's auction"""
    league_id: str
    league_name: str
    start_time: float = 0
    end_time: float = 0
    lots_completed: int = 0
    total_bids: int = 0
    successful_bids: int = 0
    errors: List[str] = field(default_factory=list)
    bid_latencies_ms: List[float] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed

@dataclass
class GlobalMetrics:
    """Aggregate metrics across all leagues"""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    leagues_completed: int = 0
    leagues_failed: int = 0
    total_bids: int = 0
    total_lots: int = 0
    all_latencies_ms: List[float] = field(default_factory=list)
    peak_concurrent_bids: int = 0
    errors: List[str] = field(default_factory=list)

# ============================================================================
# SINGLE LEAGUE AUCTION RUNNER
# ============================================================================

class LeagueAuctionRunner:
    """Runs a complete auction for a single league"""
    
    def __init__(self, invite_token: str, commissioner_email: Optional[str], league_index: int):
        self.invite_token = invite_token
        self.commissioner_email = commissioner_email  # Can be None - will auto-detect
        self.league_index = league_index
        self.users: List[TestUser] = []
        self.metrics = LeagueMetrics(league_id="", league_name="")
        
        # Auction state
        self.league_id: Optional[str] = None
        self.auction_id: Optional[str] = None
        self.current_bid: int = 0
        self.current_bidder_id: Optional[str] = None
        self.current_club_name: Optional[str] = None
        self.lot_active: bool = False
        self.auction_complete: bool = False
        self.lots_sold: int = 0
        
        # Deduplication
        self._processed_sold_lots: set = set()
    
    async def run(self) -> LeagueMetrics:
        """Run complete auction and return metrics"""
        self.metrics.start_time = time.time()
        self.metrics.status = "running"
        
        try:
            # Setup
            await self._setup_league()
            await self._setup_users()
            await self._connect_sockets()
            await self._start_auction()
            
            # Run bidding until auction completes or timeout
            await self._run_bidding_loop()
            
            self.metrics.status = "completed"
            self.metrics.leagues_completed = 1
            
        except Exception as e:
            self.metrics.status = f"failed: {e}"
            self.metrics.errors.append(str(e))
            print(f"   [League {self.league_index}] ❌ Failed: {e}")
        
        finally:
            await self._cleanup()
            self.metrics.end_time = time.time()
        
        return self.metrics
    
    async def _setup_league(self):
        """Get league info and auto-detect commissioner if needed"""
        # Step 1: Get league ID from invite token
        url = f"{BASE_URL}/leagues/by-token/{self.invite_token}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"League lookup failed: {await resp.text()}")
                data = await resp.json()
                if not data.get('found'):
                    raise Exception(f"League not found: {self.invite_token}")
                league = data['league']
                self.league_id = league['id']
                self.metrics.league_id = league['id']
                self.metrics.league_name = league.get('name', 'Unknown')
            
            # Step 2: Get full league details (includes commissionerId)
            if not self.commissioner_email:
                league_url = f"{BASE_URL}/leagues/{self.league_id}"
                async with session.get(league_url) as league_resp:
                    if league_resp.status == 200:
                        full_league = await league_resp.json()
                        commissioner_id = full_league.get('commissionerId')
                        
                        if commissioner_id:
                            # Step 3: Fetch commissioner's email
                            user_url = f"{BASE_URL}/users/{commissioner_id}"
                            async with session.get(user_url) as user_resp:
                                if user_resp.status == 200:
                                    user_data = await user_resp.json()
                                    self.commissioner_email = user_data.get('email')
                                    print(f"   [League {self.league_index}] ✓ Auto-detected commissioner: {self.commissioner_email}")
                
                if not self.commissioner_email:
                    raise Exception("Could not determine commissioner email - please provide manually")
        
        print(f"   [League {self.league_index}] ✓ {self.metrics.league_name}")
    
    async def _setup_users(self):
        """Authenticate commissioner and create/auth test users"""
        # Commissioner first
        commissioner = await self._auth_user(self.commissioner_email)
        self.users.append(commissioner)
        
        # Get existing members
        url = f"{BASE_URL}/leagues/{self.league_id}/members"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    members = await resp.json()
                    # Auth existing stress-test members
                    for member in members:
                        if 'stress-test' in member.get('displayName', '').lower():
                            email = f"{member['displayName']}@test.local"
                            try:
                                user = await self._auth_user(email)
                                if user.user_id == member['userId']:
                                    self.users.append(user)
                            except:
                                pass
        
        # Create more users if needed
        while len(self.users) < USERS_PER_LEAGUE:
            email = f"stress-{self.league_index}-{len(self.users)}-{int(time.time())}@test.local"
            try:
                user = await self._auth_user(email)
                await self._join_league(user)
                self.users.append(user)
            except Exception as e:
                if "full" in str(e).lower():
                    break  # League full, use what we have
                raise
        
        print(f"   [League {self.league_index}] ✓ {len(self.users)} users ready")
    
    async def _auth_user(self, email: str) -> TestUser:
        """Authenticate user via magic link"""
        user = TestUser(email=email)
        
        async with aiohttp.ClientSession() as session:
            # Request magic link
            resp = await session.post(f"{BASE_URL}/auth/magic-link", json={"email": email})
            if resp.status != 200:
                raise Exception(f"Magic link failed: {await resp.text()}")
            data = await resp.json()
            token = data.get('token')
            
            # Verify
            resp = await session.post(f"{BASE_URL}/auth/verify-magic-link", 
                                      json={"email": email, "token": token})
            if resp.status != 200:
                raise Exception(f"Verify failed: {await resp.text()}")
            data = await resp.json()
            user.jwt_token = data.get('accessToken')
            user.user_id = data['user']['id']
        
        return user
    
    async def _join_league(self, user: TestUser):
        """Join user to league"""
        url = f"{BASE_URL}/leagues/{self.league_id}/join"
        headers = {"Authorization": f"Bearer {user.jwt_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"inviteToken": self.invite_token, "userId": user.user_id}, headers=headers) as resp:
                if resp.status not in [200, 409]:
                    raise Exception(f"Join failed: {await resp.text()}")
    
    async def _connect_sockets(self):
        """Connect all users to Socket.IO"""
        for user in self.users:
            try:
                sio = socketio.AsyncClient(reconnection=True, reconnection_attempts=3)
                user.socket_client = sio
                
                @sio.on('bid_update')
                async def on_bid_update(data):
                    self.current_bid = data.get('amount', 0)
                    bidder = data.get('bidder', {})
                    self.current_bidder_id = bidder.get('userId') if isinstance(bidder, dict) else None
                
                @sio.on('bid_placed')
                async def on_bid_placed(data):
                    bid = data.get('bid', {})
                    self.current_bid = bid.get('amount', 0)
                    self.current_bidder_id = bid.get('userId')
                
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
                    if club_id not in self._processed_sold_lots:
                        self._processed_sold_lots.add(club_id)
                        self.lots_sold += 1
                        self.metrics.lots_completed += 1
                    self.lot_active = False
                    self.current_bid = 0
                
                @sio.on('auction_complete')
                async def on_complete(data):
                    self.auction_complete = True
                
                await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
                await sio.emit('join_auction', {'auctionId': self.auction_id, 'userId': user.user_id})
                user.connected = True
                
            except Exception as e:
                self.metrics.errors.append(f"Socket connect failed: {e}")
    
    async def _start_auction(self):
        """Get or start auction"""
        commissioner = self.users[0]
        headers = {"Authorization": f"Bearer {commissioner.jwt_token}", "X-User-ID": commissioner.user_id}
        
        async with aiohttp.ClientSession() as session:
            # Check existing auction
            resp = await session.get(f"{BASE_URL}/leagues/{self.league_id}/auction", headers=headers)
            if resp.status == 200:
                data = await resp.json()
                self.auction_id = data.get('auctionId')
                status = data.get('status')
                
                if status == 'completed':
                    # Reset auction
                    await session.post(f"{BASE_URL}/leagues/{self.league_id}/auction/reset?commissioner_id={commissioner.user_id}", headers=headers)
                    self.auction_id = None
            
            # Start new auction if needed
            if not self.auction_id:
                resp = await session.post(f"{BASE_URL}/leagues/{self.league_id}/auction/start", headers=headers)
                if resp.status == 200:
                    data = await resp.json()
                    self.auction_id = data['auctionId']
            
            # Begin auction
            resp = await session.post(f"{BASE_URL}/auction/{self.auction_id}/begin", headers=headers)
            # Ignore "already active" errors
            
            # Fetch initial state
            resp = await session.get(f"{BASE_URL}/auction/{self.auction_id}", headers=headers)
            if resp.status == 200:
                data = await resp.json()
                auction = data.get('auction', {})
                if auction.get('status') == 'active':
                    self.lot_active = True
                    self.current_bid = auction.get('currentBid') or 0
                    club = data.get('currentClub', {})
                    self.current_club_name = club.get('name')
        
        print(f"   [League {self.league_index}] ✓ Auction started")
    
    async def _run_bidding_loop(self):
        """Run bidding until auction completes"""
        timeout = 3600  # 1 hour max
        start = time.time()
        
        async def user_bidder(user: TestUser):
            """Individual user bidding behavior"""
            while not self.auction_complete and (time.time() - start) < timeout:
                if not self.lot_active:
                    await asyncio.sleep(0.5)
                    continue
                
                # Skip if already winning
                if self.current_bidder_id == user.user_id:
                    await asyncio.sleep(0.5)
                    continue
                
                # Skip if roster full
                if user.teams_won >= TEAMS_PER_ROSTER:
                    await asyncio.sleep(1)
                    continue
                
                # Random delay (realistic bidding)
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
                if self.lot_active and self.current_bidder_id != user.user_id:
                    bid_amount = (self.current_bid or 0) + BID_INCREMENT
                    if bid_amount <= user.budget_remaining:
                        success = await self._place_bid(user, bid_amount)
                        if success:
                            user.bids_won += 1
        
        # Run all bidders concurrently
        tasks = [user_bidder(user) for user in self.users]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _place_bid(self, user: TestUser, amount: int) -> bool:
        """Place a bid"""
        url = f"{BASE_URL}/auction/{self.auction_id}/bid"
        headers = {"Authorization": f"Bearer {user.jwt_token}", "X-User-ID": user.user_id}
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"amount": amount, "userId": user.user_id}, headers=headers) as resp:
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
        for user in self.users:
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
    
    def __init__(self, leagues_config: List[Dict], stagger_seconds: int = 5):
        self.leagues_config = leagues_config
        self.stagger_seconds = stagger_seconds
        self.global_metrics = GlobalMetrics()
        self.league_metrics: List[LeagueMetrics] = []
    
    async def run(self):
        """Run all leagues with staggered start"""
        print("\n" + "=" * 60)
        print(f"MULTI-LEAGUE STRESS TEST")
        print(f"Leagues: {len(self.leagues_config)}")
        print(f"Stagger: {self.stagger_seconds}s between starts")
        print("=" * 60)
        
        self.global_metrics.start_time = time.time()
        
        # Create runners
        runners = []
        for i, config in enumerate(self.leagues_config):
            runner = LeagueAuctionRunner(
                invite_token=config['invite_token'],
                commissioner_email=config['commissioner_email'],
                league_index=i + 1
            )
            runners.append(runner)
        
        # Start leagues with stagger
        print(f"\n📢 Starting {len(runners)} leagues...")
        
        tasks = []
        for i, runner in enumerate(runners):
            if i > 0:
                await asyncio.sleep(self.stagger_seconds)
            print(f"\n🚀 Starting League {i + 1}/{len(runners)}...")
            task = asyncio.create_task(runner.run())
            tasks.append(task)
        
        # Wait for all to complete
        print(f"\n⏳ Waiting for all auctions to complete...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect metrics
        for i, result in enumerate(results):
            if isinstance(result, LeagueMetrics):
                self.league_metrics.append(result)
                self.global_metrics.total_bids += result.total_bids
                self.global_metrics.total_lots += result.lots_completed
                self.global_metrics.all_latencies_ms.extend(result.bid_latencies_ms)
                if result.status == "completed":
                    self.global_metrics.leagues_completed += 1
                else:
                    self.global_metrics.leagues_failed += 1
            else:
                self.global_metrics.leagues_failed += 1
                self.global_metrics.errors.append(f"League {i+1}: {result}")
        
        self.global_metrics.end_time = time.time()
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive report"""
        duration = self.global_metrics.end_time - self.global_metrics.start_time
        
        print("\n" + "=" * 60)
        print("MULTI-LEAGUE STRESS TEST REPORT")
        print("=" * 60)
        
        print(f"\nDuration:           {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"Leagues attempted:  {len(self.leagues_config)}")
        print(f"Leagues completed:  {self.global_metrics.leagues_completed}")
        print(f"Leagues failed:     {self.global_metrics.leagues_failed}")
        print(f"Total bids:         {self.global_metrics.total_bids}")
        print(f"Total lots sold:    {self.global_metrics.total_lots}")
        
        if self.global_metrics.all_latencies_ms:
            latencies = sorted(self.global_metrics.all_latencies_ms)
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
            
            print(f"\n--- BID LATENCY (across all leagues) ---")
            print(f"p50:  {p50:.0f}ms")
            print(f"p95:  {p95:.0f}ms")
            print(f"p99:  {p99:.0f}ms")
            print(f"max:  {max(latencies):.0f}ms")
        
        print(f"\n--- PER-LEAGUE SUMMARY ---")
        for metrics in self.league_metrics:
            success_rate = (metrics.successful_bids / metrics.total_bids * 100) if metrics.total_bids > 0 else 0
            duration = metrics.end_time - metrics.start_time
            print(f"\n{metrics.league_name}:")
            print(f"   Status: {metrics.status}")
            print(f"   Duration: {duration:.0f}s")
            print(f"   Lots: {metrics.lots_completed}/{TEAMS_PER_AUCTION}")
            print(f"   Bids: {metrics.total_bids} ({success_rate:.1f}% success)")
            if metrics.errors:
                print(f"   Errors: {len(metrics.errors)}")
        
        if self.global_metrics.errors:
            print(f"\n--- ERRORS ({len(self.global_metrics.errors)}) ---")
            for err in self.global_metrics.errors[:10]:
                print(f"   • {err[:80]}")
        
        # Recommendations
        print(f"\n--- PILOT READINESS ---")
        if self.global_metrics.leagues_failed == 0:
            print("✅ All leagues completed successfully")
        else:
            print(f"⚠️  {self.global_metrics.leagues_failed} leagues failed - investigate before pilot")
        
        if self.global_metrics.all_latencies_ms:
            p99 = sorted(self.global_metrics.all_latencies_ms)[int(len(self.global_metrics.all_latencies_ms) * 0.99)]
            if p99 < 100:
                print("✅ Bid latency excellent (<100ms p99)")
            elif p99 < 500:
                print("⚠️  Bid latency acceptable but monitor during pilot")
            else:
                print("❌ Bid latency too high - may affect user experience")
        
        print("\n" + "=" * 60)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    global BASE_URL, SOCKET_URL
    
    parser = argparse.ArgumentParser(
        description="Multi-League Concurrent Stress Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test with config file (recommended for multiple leagues)
    python multi_league_stress_test.py --config leagues.json --url https://your-app.emergent.sh

    # Quick single-league validation
    python multi_league_stress_test.py --quick-test --invite-token TOKEN \\
        --commissioner-email EMAIL --url https://your-app.emergent.sh

Config file format (leagues.json):
{
    "leagues": [
        {"invite_token": "abc123", "commissioner_email": "user1@example.com"},
        {"invite_token": "def456", "commissioner_email": "user2@example.com"}
    ],
    "stagger_seconds": 10
}
        """
    )
    
    parser.add_argument("--config", help="Path to leagues config JSON file")
    parser.add_argument("--quick-test", action="store_true", help="Run single-league validation")
    parser.add_argument("--invite-token", help="League invite token (for quick-test)")
    parser.add_argument("--commissioner-email", help="Commissioner email (for quick-test)")
    parser.add_argument("--url", help="Production URL (e.g., https://your-app.emergent.sh)")
    parser.add_argument("--stagger", type=int, default=10, help="Seconds between league starts (default: 10)")
    
    args = parser.parse_args()
    
    # Set URLs
    if args.url:
        base = args.url.rstrip('/')
        BASE_URL = f"{base}/api"
        SOCKET_URL = base
        print(f"🌐 Target: {base}")
    else:
        print("🏠 Target: localhost:8001 (use --url for production)")
    
    # Load config
    if args.quick_test:
        if not args.invite_token:
            print("❌ --quick-test requires --invite-token")
            return
        leagues_config = [{"invite_token": args.invite_token, "commissioner_email": args.commissioner_email}]
        stagger = 0
    elif args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {args.config}")
            return
        with open(config_path) as f:
            config = json.load(f)
        leagues_config = config.get('leagues', [])
        stagger = config.get('stagger_seconds', args.stagger)
    else:
        print("❌ Provide either --config or --quick-test")
        return
    
    if not leagues_config:
        print("❌ No leagues configured")
        return
    
    # Ensure each league has at least invite_token
    for league in leagues_config:
        if 'invite_token' not in league:
            print("❌ Each league must have 'invite_token'")
            return
        # commissioner_email is now optional - will be auto-detected
        if 'commissioner_email' not in league:
            league['commissioner_email'] = None
    
    print(f"\n📋 Loaded {len(leagues_config)} league(s)")
    
    # Run test
    test = MultiLeagueStressTest(leagues_config, stagger_seconds=stagger)
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
