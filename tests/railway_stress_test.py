#!/usr/bin/env python3
"""
Emergent - Railway Migration Stress Test
=========================================

Tests the Railway deployment with UK server + M0 MongoDB Atlas to measure:
- Latency improvements vs previous infrastructure
- Error rates at scale
- Socket.IO real-time performance
- Concurrent auction handling

REQUIREMENTS:
-------------
pip install "python-socketio[asyncio_client]" aiohttp

USAGE:
------
python railway_stress_test.py --leagues 1 --url https://joeyjones-production.up.railway.app
"""

import asyncio
import aiohttp
import socketio
import json
import time
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# CONFIGURATION
DEFAULT_BASE_URL = "http://localhost:8001/api"
DEFAULT_SOCKET_URL = "http://localhost:8001"
SOCKET_PATH = "/api/socket.io"

BASE_URL = DEFAULT_BASE_URL
SOCKET_URL = DEFAULT_SOCKET_URL

USERS_PER_LEAGUE = 8
TEAMS_PER_ROSTER = 4
BID_INCREMENT = 5_000_000
STARTING_BUDGET = 500_000_000
DEFAULT_COMPETITION = "CL"

@dataclass
class TestUser:
    email: str
    user_id: Optional[str] = None
    jwt_token: Optional[str] = None
    budget_remaining: int = STARTING_BUDGET
    teams_won: int = 0
    bids_placed: int = 0
    socket_client: Optional[socketio.AsyncClient] = None
    connected: bool = False
    is_commissioner: bool = False

@dataclass
class TestLeague:
    league_id: Optional[str] = None
    league_name: str = ""
    invite_token: Optional[str] = None
    commissioner: Optional[TestUser] = None
    members: List[TestUser] = field(default_factory=list)
    auction_id: Optional[str] = None

@dataclass
class LeagueMetrics:
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
    errors: List[str] = field(default_factory=list)
    bid_latencies_ms: List[float] = field(default_factory=list)
    bid_rejection_reasons: Dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    total_spend: int = 0

@dataclass
class GlobalMetrics:
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

class LeagueRunner:
    def __init__(self, league_index: int, competition: str = DEFAULT_COMPETITION,
                 users_per_league: int = USERS_PER_LEAGUE,
                 teams_per_roster: int = TEAMS_PER_ROSTER):
        self.league_index = league_index
        self.competition = competition
        self.users_per_league = users_per_league
        self.teams_per_roster = teams_per_roster
        self.league = TestLeague()
        self.metrics = LeagueMetrics()
        self.current_bid = 0
        self.current_bidder_id = None
        self.lot_active = False
        self.auction_complete = False
        self.lots_sold = 0
        self._processed_sold_lots = set()

    async def setup(self) -> bool:
        try:
            timestamp = int(time.time() * 1000)
            commissioner_email = "commissioner-" + str(self.league_index) + "-" + str(timestamp) + "@test.local"
            self.league.commissioner = await self._create_user(commissioner_email, True)
            print("   [League " + str(self.league_index) + "] Commissioner created")

            await self._create_league()
            print("   [League " + str(self.league_index) + "] League created")

            await self._join_league(self.league.commissioner)

            for i in range(self.users_per_league - 1):
                member_email = "member-" + str(self.league_index) + "-" + str(i+1) + "-" + str(timestamp) + "@test.local"
                member = await self._create_user(member_email)
                await self._join_league(member)
                self.league.members.append(member)

            print("   [League " + str(self.league_index) + "] " + str(len(self.league.members) + 1) + " users joined")
            return True

        except Exception as e:
            self.metrics.status = "setup_failed: " + str(e)
            self.metrics.errors.append("Setup failed: " + str(e))
            print("   [League " + str(self.league_index) + "] Setup failed: " + str(e))
            return False

    async def run_auction(self) -> LeagueMetrics:
        self.metrics.league_name = self.league.league_name
        self.metrics.start_time = time.time()
        self.metrics.status = "running"

        try:
            all_users = [self.league.commissioner] + self.league.members
            print("   [League " + str(self.league_index) + "] Connecting " + str(len(all_users)) + " users...")
            await self._connect_all_sockets(all_users)

            await self._start_auction()
            print("   [League " + str(self.league_index) + "] Auction started")

            await self._run_bidding_loop(all_users)

            headers = {"Authorization": "Bearer " + self.league.commissioner.jwt_token}
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    BASE_URL + "/leagues/" + self.league.league_id + "/participants",
                    headers=headers
                )
                if resp.status == 200:
                    data = await resp.json()
                    participants = data.get('participants', [])
                    total_clubs = sum(len(p.get('clubsWon', [])) for p in participants)
                    total_spend = sum(p.get('totalSpent', 0) for p in participants)

                    self.lots_sold = total_clubs
                    self.metrics.lots_sold = total_clubs
                    self.metrics.total_spend = total_spend

                    print("   [League " + str(self.league_index) + "] Final: " + str(total_clubs) + " clubs, £" + str(total_spend/1_000_000) + "M")

            self.metrics.status = "completed"
            self.metrics.lots_completed = self.lots_sold

        except Exception as e:
            self.metrics.status = "failed: " + str(e)
            self.metrics.errors.append(str(e))
            print("   [League " + str(self.league_index) + "] Failed: " + str(e))

        finally:
            await self._cleanup()
            self.metrics.end_time = time.time()

        return self.metrics

    async def _create_user(self, email: str, is_commissioner: bool = False) -> TestUser:
        user = TestUser(email=email, is_commissioner=is_commissioner)

        async with aiohttp.ClientSession() as session:
            # Request magic link
            url = BASE_URL + "/auth/magic-link"
            print("      DEBUG: POST " + url)

            resp = await session.post(url, json={"email": email})

            print("      DEBUG: Response status: " + str(resp.status))
            print("      DEBUG: Content-Type: " + str(resp.headers.get('Content-Type', 'unknown')))

            if resp.status != 200:
                text = await resp.text()
                raise Exception("Magic link failed: " + str(resp.status) + " - " + text[:200])

            # Check if we got JSON or HTML
            content_type = resp.headers.get('Content-Type', '')
            if 'html' in content_type.lower():
                text = await resp.text()
                print("      DEBUG: Got HTML instead of JSON!")
                print("      DEBUG: First 500 chars: " + text[:500])
                raise Exception("API returned HTML instead of JSON. Check if backend is running.")

            data = await resp.json()
            token = data.get('token')

            if not token:
                raise Exception("No token in response: " + str(data))

            # Verify magic link
            resp = await session.post(
                BASE_URL + "/auth/verify-magic-link",
                json={"email": email, "token": token}
            )
            if resp.status != 200:
                text = await resp.text()
                raise Exception("Verify failed: " + str(resp.status) + " - " + text[:200])

            data = await resp.json()
            user.jwt_token = data.get('accessToken') or data.get('token')
            user.user_id = data['user']['id']

        return user

    async def _create_league(self):
        commissioner = self.league.commissioner
        league_name = "RailwayTest-" + str(self.league_index) + "-" + str(int(time.time()))

        headers = {
            "Authorization": "Bearer " + commissioner.jwt_token,
            "X-User-ID": commissioner.user_id
        }

        payload = {
            "name": league_name,
            "competitionCode": self.competition,
            "maxManagers": self.users_per_league,
            "budget": STARTING_BUDGET,
            "clubSlots": self.teams_per_roster,
            "commissionerId": commissioner.user_id,
            "timerSeconds": 10,
            "antiSnipeSeconds": 10
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(BASE_URL + "/leagues", json=payload, headers=headers)
            if resp.status not in [200, 201]:
                raise Exception("League creation failed")

            data = await resp.json()
            self.league.league_id = data.get('id') or data.get('leagueId')
            self.league.league_name = league_name
            self.league.invite_token = data.get('inviteToken')

    async def _join_league(self, user: TestUser):
        headers = {"Authorization": "Bearer " + user.jwt_token}
        payload = {
            "inviteToken": self.league.invite_token,
            "userId": user.user_id
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                BASE_URL + "/leagues/" + self.league.league_id + "/join",
                json=payload,
                headers=headers
            )
            if resp.status not in [200, 409]:
                raise Exception("Join failed")

    async def _connect_all_sockets(self, users: List[TestUser]):
        for user in users:
            try:
                sio = socketio.AsyncClient(reconnection=False)
                user.socket_client = sio

                @sio.on('bid_update')
                async def on_bid_update(data):
                    self.current_bid = data.get('amount', 0)
                    self.metrics.socket_events_received += 1

                @sio.on('lot_started')
                async def on_lot_started(data):
                    self.lot_active = True
                    self.metrics.socket_events_received += 1

                @sio.on('sold')
                async def on_sold(data):
                    club_id = data.get('clubId')
                    if club_id and club_id not in self._processed_sold_lots:
                        self._processed_sold_lots.add(club_id)
                        self.lots_sold += 1
                        self.metrics.lots_sold += 1
                    self.lot_active = False
                    self.metrics.socket_events_received += 1

                @sio.on('unsold')
                async def on_unsold(data):
                    self.metrics.lots_unsold += 1
                    self.lot_active = False
                    self.metrics.socket_events_received += 1

                @sio.on('auction_complete')
                async def on_complete(data):
                    self.auction_complete = True
                    self.metrics.socket_events_received += 1

                await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
                user.connected = True

            except Exception as e:
                self.metrics.errors.append("Socket failed: " + str(e))

    async def _start_auction(self):
        commissioner = self.league.commissioner
        headers = {
            "Authorization": "Bearer " + commissioner.jwt_token,
            "X-User-ID": commissioner.user_id
        }

        async with aiohttp.ClientSession() as session:
            # Step 1: Create auction
            resp = await session.post(
                BASE_URL + "/leagues/" + self.league.league_id + "/auction/start",
                headers=headers
            )
            if resp.status != 200:
                text = await resp.text()
                raise Exception("Auction creation failed: " + str(resp.status) + " - " + text[:200])

            data = await resp.json()
            self.league.auction_id = data.get('auctionId')

            if not self.league.auction_id:
                raise Exception("No auction ID in response: " + str(data))

            print("      DEBUG: Auction created, ID: " + self.league.auction_id)

            # Join sockets to auction room
            all_users = [self.league.commissioner] + self.league.members
            for user in all_users:
                if user.socket_client and user.connected:
                    try:
                        await user.socket_client.emit('join_auction', {
                            'auctionId': self.league.auction_id,
                            'userId': user.user_id
                        })
                    except Exception as e:
                        self.metrics.errors.append("join_auction failed: " + str(e))

            await asyncio.sleep(0.5)

            # Step 2: Activate with /begin endpoint
            activation_url = BASE_URL + "/auction/" + self.league.auction_id + "/begin"

            print("      DEBUG: Activating with: " + activation_url)
            resp = await session.post(activation_url, headers=headers)
            print("      DEBUG: Activation response: " + str(resp.status))

            if resp.status == 200:
                print("      DEBUG: Activation successful!")
            elif resp.status == 409:
                print("      DEBUG: Already active (409)")
            else:
                # Show detailed error
                try:
                    error_data = await resp.json()
                    print("      ERROR: Activation failed: " + str(error_data))
                except:
                    error_text = await resp.text()
                    print("      ERROR: Activation failed: " + error_text[:300])

            await asyncio.sleep(1)

            # Verify auction state
            resp = await session.get(
                BASE_URL + "/auction/" + self.league.auction_id,
                headers=headers
            )
            if resp.status == 200:
                data = await resp.json()
                auction = data.get('auction', {})
                status = auction.get('status')

                print("      DEBUG: Auction status: " + str(status))

                if status == 'active':
                    self.lot_active = True
                    self.current_bid = auction.get('currentBid') or 0
                elif status == 'waiting':
                    print("      WARN: Auction still in 'waiting' state - may need manual activation")
                else:
                    print("      WARN: Unexpected status: " + str(status))

    async def _run_bidding_loop(self, users: List[TestUser]):
        timeout = 60  # Shorter timeout for testing
        start = time.time()
        poll_interval = 2

        last_lot_id = None
        bid_placed_this_lot = False
        lots_we_bid_on = set()
        last_lot_num = -1

        # Check initial state
        state = await self._get_auction_state()
        if state:
            print("      DEBUG: Initial auction status: " + str(state.get('status')))
            if state.get('status') == 'waiting':
                print("      ERROR: Auction stuck in 'waiting' state!")
                print("      ERROR: Your backend needs an activation endpoint")
                print("      ERROR: Or the auction should auto-start after creation")
                return

        while not self.auction_complete and (time.time() - start) < timeout:
            state = await self._get_auction_state()
            if not state:
                await asyncio.sleep(poll_interval)
                continue

            if state.get('status') == 'completed':
                self.auction_complete = True
                print("   [League " + str(self.league_index) + "] Completed!")
                break

            if state.get('status') == 'waiting':
                elapsed = time.time() - start
                if int(elapsed) % 10 == 0:
                    print("      WARN: Still waiting after " + str(int(elapsed)) + "s...")
                await asyncio.sleep(poll_interval)
                continue

            current_lot_id = state.get('lotId')
            current_bid = state.get('currentBid') or 0
            current_bidder = state.get('currentBidderId')
            lot_num = state.get('currentLot', 0)

            if current_lot_id != last_lot_id or lot_num != last_lot_num:
                if last_lot_id is not None:
                    print("      [League " + str(self.league_index) + "] Lot " + str(lot_num))
                last_lot_id = current_lot_id
                last_lot_num = lot_num
                bid_placed_this_lot = current_lot_id in lots_we_bid_on

                completed = state.get('completedLots', [])
                sold_count = len([c for c in completed if c.get('sold')])
                if sold_count > self.lots_sold:
                    self.lots_sold = sold_count
                    self.metrics.lots_sold = sold_count

                all_filled = all(
                    state.get('rosters', {}).get(u.user_id, 0) >= self.teams_per_roster
                    for u in users
                )
                if all_filled:
                    print("   [League " + str(self.league_index) + "] All rosters filled!")
                    self.auction_complete = True
                    break

            if bid_placed_this_lot:
                await asyncio.sleep(poll_interval)
                continue

            eligible_users = []
            for user in users:
                if current_bidder == user.user_id:
                    continue

                user_roster_count = state.get('rosters', {}).get(user.user_id, 0)
                if user_roster_count >= self.teams_per_roster:
                    continue

                bid_amount = current_bid + BID_INCREMENT
                if bid_amount > user.budget_remaining:
                    continue

                eligible_users.append(user)

            if eligible_users:
                eligible_users.sort(key=lambda u: (
                    state.get('rosters', {}).get(u.user_id, 0),
                    u.email
                ))

                if len(eligible_users) > 1 and lot_num > 0:
                    idx = lot_num % len(eligible_users)
                    bidder_selected = eligible_users[idx]
                else:
                    bidder_selected = eligible_users[0]

                bid_amount = current_bid + BID_INCREMENT
                success = await self._place_bid(bidder_selected, bid_amount)

                if success:
                    bid_placed_this_lot = True
                    lots_we_bid_on.add(current_lot_id)
                    print("      [League " + str(self.league_index) + "] Bid: £" + str(bid_amount/1_000_000) + "M")

            await asyncio.sleep(poll_interval)

            elapsed = time.time() - start
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                print("   [League " + str(self.league_index) + "] " + str(self.lots_sold) + " lots, " + str(self.metrics.total_bids) + " bids")

        if (time.time() - start) >= timeout:
            print("   [League " + str(self.league_index) + "] TIMEOUT after " + str(timeout) + "s")

    async def _get_auction_state(self) -> Optional[Dict]:
        try:
            headers = {"Authorization": "Bearer " + self.league.commissioner.jwt_token}
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    BASE_URL + "/auction/" + self.league.auction_id,
                    headers=headers
                )
                if resp.status == 200:
                    data = await resp.json()
                    auction = data.get('auction', {})

                    completed_lots = auction.get('completedLots') or []
                    self.lots_sold = len([c for c in completed_lots if c.get('sold')])

                    rosters = {}
                    for lot in completed_lots:
                        if lot.get('sold') and lot.get('winnerId'):
                            rosters[lot['winnerId']] = rosters.get(lot['winnerId'], 0) + 1

                    return {
                        'status': auction.get('status'),
                        'currentBid': auction.get('currentBid') or 0,
                        'currentBidderId': auction.get('currentBidder', {}).get('userId') if auction.get('currentBidder') else None,
                        'lotId': auction.get('currentLotId'),
                        'currentLot': auction.get('currentLot', 0),
                        'rosters': rosters,
                        'completedLots': completed_lots
                    }
        except Exception as e:
            self.metrics.errors.append("Poll error: " + str(e))
        return None

    async def _place_bid(self, user: TestUser, amount: int) -> bool:
        headers = {
            "Authorization": "Bearer " + user.jwt_token,
            "X-User-ID": user.user_id,
            "Content-Type": "application/json"
        }

        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    BASE_URL + "/auction/" + self.league.auction_id + "/bid",
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
                    try:
                        error_data = await resp.json()
                        reason = error_data.get('detail', str(resp.status))
                        if isinstance(reason, list):
                            reason = reason[0].get('msg', str(resp.status)) if reason else str(resp.status)
                    except:
                        reason = str(resp.status)

                    reason_key = reason[:50]
                    self.metrics.bid_rejection_reasons[reason_key] = self.metrics.bid_rejection_reasons.get(reason_key, 0) + 1
                    return False
        except Exception as e:
            self.metrics.errors.append("Bid error: " + str(e))
            self.metrics.failed_bids += 1
            return False

    async def _cleanup(self):
        all_users = [self.league.commissioner] + self.league.members
        for user in all_users:
            if user.socket_client:
                try:
                    await user.socket_client.disconnect()
                except:
                    pass

class MultiLeagueStressTest:
    def __init__(self, num_leagues: int, stagger_seconds: int = 5,
                 competition: str = DEFAULT_COMPETITION,
                 users_per_league: int = USERS_PER_LEAGUE,
                 teams_per_roster: int = TEAMS_PER_ROSTER):
        self.num_leagues = num_leagues
        self.stagger_seconds = stagger_seconds
        self.competition = competition
        self.users_per_league = users_per_league
        self.teams_per_roster = teams_per_roster
        self.global_metrics = GlobalMetrics()
        self.league_metrics: List[LeagueMetrics] = []
        self.runners: List[LeagueRunner] = []

    async def run(self):
        print("\n" + "=" * 70)
        print("RAILWAY MIGRATION POC TEST")
        print("=" * 70)
        print("Target: " + BASE_URL)
        print("Leagues: " + str(self.num_leagues))
        print("Users per league: " + str(self.users_per_league))
        print("=" * 70)

        self.global_metrics.start_time = time.time()

        print("\nPHASE 1: Creating leagues...")

        for i in range(self.num_leagues):
            print("\n   Creating League " + str(i + 1) + "...")
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

        print("\nCreated " + str(self.global_metrics.leagues_created) + " leagues")

        if not self.runners:
            print("\nNo leagues created. Aborting.")
            return

        print("\nPHASE 2: Starting auctions...")

        async def run_with_stagger(runner: LeagueRunner, delay: float):
            if delay > 0:
                await asyncio.sleep(delay)
            return await runner.run_auction()

        tasks = []
        for i, runner in enumerate(self.runners):
            delay = i * self.stagger_seconds
            task = asyncio.create_task(run_with_stagger(runner, delay))
            tasks.append(task)

        print("\nWaiting for completion...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

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

        self.global_metrics.end_time = time.time()
        self._generate_report()

    def _generate_report(self):
        duration = self.global_metrics.end_time - self.global_metrics.start_time

        print("\n" + "=" * 70)
        print("RAILWAY POC REPORT")
        print("=" * 70)

        print("\nSUMMARY:")
        print("Duration: " + str(int(duration)) + "s")
        print("Leagues completed: " + str(self.global_metrics.leagues_completed))
        print("Total bids: " + str(self.global_metrics.total_bids))

        print("\nLATENCY:")
        if self.global_metrics.all_latencies_ms:
            latencies = sorted(self.global_metrics.all_latencies_ms)
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            avg = sum(latencies) / len(latencies)

            print("Average: " + str(int(avg)) + "ms")
            print("p50: " + str(int(p50)) + "ms")
            print("p95: " + str(int(p95)) + "ms")
            print("Max: " + str(int(max(latencies))) + "ms")

            # Verdict
            print("\n" + "=" * 70)
            if p50 < 100 and self.global_metrics.leagues_completed > 0:
                print("VERDICT: [PASS] Migration looks good!")
            elif self.global_metrics.leagues_completed == 0:
                print("VERDICT: [FAIL] No auctions completed")
            else:
                print("VERDICT: [WARN] Review metrics above")
        else:
            print("No latency data collected")
            print("\n" + "=" * 70)
            if self.global_metrics.leagues_completed == 0:
                print("VERDICT: [FAIL] No auctions completed")
            else:
                print("VERDICT: [WARN] No bids placed")

        print("\nBIDS:")
        total_success = sum(m.successful_bids for m in self.league_metrics)
        total_failed = sum(m.failed_bids for m in self.league_metrics)
        total = total_success + total_failed
        if total > 0:
            print("Success rate: " + str(int(total_success / total * 100)) + "%")

        print("\nSOCKET.IO:")
        total_events = sum(m.socket_events_received for m in self.league_metrics)
        print("Events received: " + str(total_events))

        print("=" * 70)

async def main():
    global BASE_URL, SOCKET_URL

    parser = argparse.ArgumentParser(description="Railway Migration Test")
    parser.add_argument("--leagues", type=int, default=1)
    parser.add_argument("--url", help="Railway URL")
    parser.add_argument("--stagger", type=int, default=10)

    args = parser.parse_args()

    if args.url:
        base = args.url.rstrip('/')
        BASE_URL = base + "/api"
        SOCKET_URL = base

    test = MultiLeagueStressTest(
        num_leagues=args.leagues,
        stagger_seconds=args.stagger
    )
    await test.run()

if __name__ == "__main__":
    asyncio.run(main())
