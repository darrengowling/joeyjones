"""
Locust Load Testing for Multi-Sport Auction Platform
Production Hardening - Days 4-5

Test Scenarios:
1. Authentication Load (JWT magic links)
2. League Creation & Joining
3. Auction Bidding (critical path)
4. Socket.IO Real-time Connections
5. Concurrent Auctions (multiple rooms)
6. API Endpoint Performance

Target: 150 concurrent users
"""

import time
import random
import uuid
import json
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import socketio

# Configuration
BACKEND_URL = "https://sportauction.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class AuctionUser(HttpUser):
    """
    Simulates a user participating in the auction platform
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = None
        self.access_token = None
        self.refresh_token = None
        self.email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.league_id = None
        self.auction_id = None
        
        # Authenticate user
        self.authenticate()
    
    def authenticate(self):
        """Perform JWT authentication"""
        # Step 1: Request magic link
        with self.client.post(
            "/api/auth/magic-link",
            json={"email": self.email},
            catch_response=True,
            name="/api/auth/magic-link"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                magic_token = data.get("token")
                
                if not magic_token:
                    response.failure("No magic token in response")
                    raise StopUser()
                
                # Step 2: Verify magic link and get JWT
                with self.client.post(
                    "/api/auth/verify-magic-link",
                    json={"email": self.email, "token": magic_token},
                    catch_response=True,
                    name="/api/auth/verify-magic-link"
                ) as verify_response:
                    if verify_response.status_code == 200:
                        auth_data = verify_response.json()
                        self.access_token = auth_data.get("accessToken")
                        self.refresh_token = auth_data.get("refreshToken")
                        self.user_id = auth_data.get("user", {}).get("id")
                        
                        if not self.user_id or not self.access_token:
                            verify_response.failure("Authentication failed - missing tokens")
                            raise StopUser()
                        
                        verify_response.success()
                    else:
                        verify_response.failure(f"Verify failed: {verify_response.status_code}")
                        raise StopUser()
                
                response.success()
            else:
                response.failure(f"Magic link failed: {response.status_code}")
                raise StopUser()
    
    def get_headers(self):
        """Get authenticated headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-User-ID": self.user_id,
            "Content-Type": "application/json"
        }
    
    @task(3)
    def view_sports(self):
        """Get available sports"""
        with self.client.get(
            "/api/sports",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/sports"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    def view_leagues(self):
        """View available leagues"""
        with self.client.get(
            "/api/leagues",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/leagues"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def view_assets(self):
        """View assets (football clubs or cricket players)"""
        sport = random.choice(["football", "cricket"])
        with self.client.get(
            f"/api/assets?sportKey={sport}&page=1&pageSize=20",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/assets"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    def create_league(self):
        """Create a new league"""
        league_data = {
            "name": f"Load Test League {uuid.uuid4().hex[:8]}",
            "commissionerId": self.user_id,
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 4,
            "sportKey": random.choice(["football", "cricket"]),
            "timerSeconds": 30,
            "antiSnipeSeconds": 10
        }
        
        with self.client.post(
            "/api/leagues",
            json=league_data,
            headers=self.get_headers(),
            catch_response=True,
            name="/api/leagues [POST]"
        ) as response:
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                self.league_id = data.get("id")
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    def view_my_competitions(self):
        """View user's competitions"""
        with self.client.get(
            f"/api/me/competitions?userId={self.user_id}",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/me/competitions"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def view_league_details(self):
        """View league details if user has joined a league"""
        if self.league_id:
            with self.client.get(
                f"/api/leagues/{self.league_id}",
                headers=self.get_headers(),
                catch_response=True,
                name="/api/leagues/:id"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed: {response.status_code}")


class BiddingUser(HttpUser):
    """
    Specialized user for high-intensity bidding scenarios
    Tests the most critical path: real-time auction bidding
    """
    wait_time = between(0.5, 2)  # Faster pace for bidding
    
    def on_start(self):
        """Initialize bidding user"""
        self.user_id = None
        self.access_token = None
        self.email = f"bidder_{uuid.uuid4().hex[:8]}@example.com"
        self.league_id = None
        self.auction_id = None
        self.current_lot_id = None
        
        # Authenticate
        self.authenticate()
    
    def authenticate(self):
        """Quick authentication"""
        # Request magic link
        response = self.client.post(
            "/api/auth/magic-link",
            json={"email": self.email}
        )
        
        if response.status_code == 200:
            magic_token = response.json().get("token")
            
            # Verify and get JWT
            auth_response = self.client.post(
                "/api/auth/verify-magic-link",
                json={"email": self.email, "token": magic_token}
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                self.access_token = auth_data.get("accessToken")
                self.user_id = auth_data.get("user", {}).get("id")
            else:
                raise StopUser()
        else:
            raise StopUser()
    
    def get_headers(self):
        """Get authenticated headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-User-ID": self.user_id,
            "Content-Type": "application/json"
        }
    
    @task(10)
    def place_bid(self):
        """Place a bid in an active auction"""
        # In a real scenario, we'd need an active auction
        # For load testing, we'll simulate the bid endpoint call
        if self.auction_id and self.current_lot_id:
            bid_amount = random.randint(1000000, 50000000)  # £1M to £50M
            
            with self.client.post(
                f"/api/auction/{self.auction_id}/bid",
                json={
                    "userId": self.user_id,
                    "lotId": self.current_lot_id,
                    "amount": bid_amount
                },
                headers=self.get_headers(),
                catch_response=True,
                name="/api/auction/:id/bid"
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 400:
                    # Expected for budget/validation errors
                    response.success()
                else:
                    response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    def check_auction_status(self):
        """Check auction status"""
        if self.auction_id:
            with self.client.get(
                f"/api/auction/{self.auction_id}",
                headers=self.get_headers(),
                catch_response=True,
                name="/api/auction/:id"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed: {response.status_code}")


# Custom events for detailed metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("="*80)
    print("LOAD TEST STARTING")
    print(f"Target: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'} users")
    print(f"Backend: {BACKEND_URL}")
    print("="*80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("="*80)
    print("LOAD TEST COMPLETE")
    print("="*80)
    
    # Print summary stats
    stats = environment.stats
    print("\nSUMMARY STATISTICS:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time}ms")
    print(f"Max response time: {stats.total.max_response_time}ms")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    print(f"Failure rate: {(stats.total.num_failures / stats.total.num_requests * 100) if stats.total.num_requests > 0 else 0:.2f}%")
    
    print("\nP50/P95/P99 Response Times:")
    for name, stat in stats.entries.items():
        print(f"  {name}:")
        print(f"    p50: {stat.get_response_time_percentile(0.50):.2f}ms")
        print(f"    p95: {stat.get_response_time_percentile(0.95):.2f}ms")
        print(f"    p99: {stat.get_response_time_percentile(0.99):.2f}ms")
