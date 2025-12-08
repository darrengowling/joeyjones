#!/usr/bin/env python3
"""
Rate Limiting Load Test
Tests rate limits on critical endpoints to ensure abuse prevention without hurting normal users
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from collections import defaultdict
import sys

# Configuration
BASE_URL = "https://bid-fixer.preview.emergentagent.com/api"
CONCURRENT_USERS = 10
TEST_DURATION_SECONDS = 120  # 2 minutes
REQUEST_DELAY = 0.5  # 500ms between requests per user

class LoadTestRunner:
    def __init__(self):
        self.results = {
            'total_requests': 0,
            'successful': 0,
            'rate_limited': 0,
            'errors': 0,
            'status_codes': defaultdict(int),
            'response_times': [],
            'rate_limited_times': [],
            'start_time': None,
            'end_time': None
        }
        self.test_auction_id = None
        self.test_league_id = None
        self.test_user_token = None
        
    async def create_test_league(self, session):
        """Create a test league for auction bid testing"""
        try:
            # First create a test user to be commissioner
            test_commissioner_id = f"load-test-commissioner-{int(time.time())}"
            
            async with session.post(
                f"{BASE_URL}/leagues",
                json={
                    "name": f"Load Test League {datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "sportKey": "football",
                    "commissionerId": test_commissioner_id,
                    "budget": 500000000,
                    "minManagers": 2,
                    "maxManagers": 8,
                    "clubSlots": 3,
                    "timerSeconds": 30,
                    "antiSnipeSeconds": 10
                },
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status == 200 or resp.status == 201:
                    data = await resp.json()
                    self.test_league_id = data.get('id')
                    print(f"✅ Test league created: {self.test_league_id}")
                    return True
                else:
                    print(f"❌ Failed to create test league: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Error creating test league: {e}")
            return False
    
    async def start_test_auction(self, session):
        """Start auction for testing bid rate limits"""
        if not self.test_league_id:
            return False
            
        try:
            async with session.post(
                f"{BASE_URL}/leagues/{self.test_league_id}/auction/start",
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.test_auction_id = data.get('auctionId')
                    print(f"✅ Test auction started: {self.test_auction_id}")
                    return True
                else:
                    print(f"❌ Failed to start auction: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Error starting auction: {e}")
            return False
    
    async def test_bid_endpoint(self, session, user_id):
        """Test the auction bid endpoint with rate limiting"""
        if not self.test_auction_id:
            return
            
        end_time = time.time() + TEST_DURATION_SECONDS
        request_count = 0
        
        while time.time() < end_time:
            try:
                start = time.time()
                
                async with session.post(
                    f"{BASE_URL}/auction/{self.test_auction_id}/bid",
                    json={"amount": 5000000 + (request_count * 1000000)},  # Increment bid
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    elapsed = time.time() - start
                    
                    self.results['total_requests'] += 1
                    self.results['status_codes'][resp.status] += 1
                    self.results['response_times'].append(elapsed)
                    
                    if resp.status == 200:
                        self.results['successful'] += 1
                    elif resp.status == 429:
                        self.results['rate_limited'] += 1
                        self.results['rate_limited_times'].append(time.time())
                        # print(f"⚠️  User {user_id}: Rate limited (429)")
                    else:
                        self.results['errors'] += 1
                        
                request_count += 1
                await asyncio.sleep(REQUEST_DELAY)
                
            except Exception as e:
                self.results['errors'] += 1
                print(f"❌ User {user_id} error: {e}")
                await asyncio.sleep(REQUEST_DELAY)
    
    async def test_league_creation_endpoint(self, session, user_id):
        """Test the league creation endpoint with rate limiting"""
        end_time = time.time() + TEST_DURATION_SECONDS
        request_count = 0
        
        while time.time() < end_time:
            try:
                start = time.time()
                
                async with session.post(
                    f"{BASE_URL}/leagues",
                    json={
                        "name": f"Rate Test League {user_id}-{request_count}",
                        "sportKey": "football",
                        "commissionerId": f"load-test-user-{user_id}",
                        "budget": 500000000,
                        "minManagers": 2,
                        "maxManagers": 8,
                        "clubSlots": 3,
                        "timerSeconds": 30,
                        "antiSnipeSeconds": 10
                    },
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    elapsed = time.time() - start
                    
                    self.results['total_requests'] += 1
                    self.results['status_codes'][resp.status] += 1
                    self.results['response_times'].append(elapsed)
                    
                    if resp.status in [200, 201]:
                        self.results['successful'] += 1
                    elif resp.status == 429:
                        self.results['rate_limited'] += 1
                        self.results['rate_limited_times'].append(time.time())
                    else:
                        self.results['errors'] += 1
                        
                request_count += 1
                await asyncio.sleep(REQUEST_DELAY * 2)  # Slower for league creation
                
            except Exception as e:
                self.results['errors'] += 1
                await asyncio.sleep(REQUEST_DELAY * 2)
    
    async def run_test(self, test_type='bid'):
        """Run the load test with multiple concurrent users"""
        print(f"\n{'='*80}")
        print(f"Rate Limiting Load Test - {test_type.upper()} endpoint")
        print(f"{'='*80}")
        print(f"Configuration:")
        print(f"  - Concurrent users: {CONCURRENT_USERS}")
        print(f"  - Test duration: {TEST_DURATION_SECONDS}s")
        print(f"  - Request delay: {REQUEST_DELAY}s")
        print(f"  - Base URL: {BASE_URL}")
        print(f"{'='*80}\n")
        
        self.results['start_time'] = datetime.now()
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Setup: Create test league and auction if testing bid endpoint
            if test_type == 'bid':
                print("Setting up test environment...")
                if not await self.create_test_league(session):
                    print("❌ Failed to create test league. Exiting.")
                    return
                
                if not await self.start_test_auction(session):
                    print("❌ Failed to start test auction. Exiting.")
                    return
                
                print(f"\n🚀 Starting load test with {CONCURRENT_USERS} users...\n")
                
                # Run concurrent bid tests
                tasks = [
                    self.test_bid_endpoint(session, i)
                    for i in range(CONCURRENT_USERS)
                ]
            else:
                print(f"\n🚀 Starting load test with {CONCURRENT_USERS} users...\n")
                
                # Run concurrent league creation tests
                tasks = [
                    self.test_league_creation_endpoint(session, i)
                    for i in range(CONCURRENT_USERS)
                ]
            
            await asyncio.gather(*tasks)
        
        self.results['end_time'] = datetime.now()
        self.print_results(test_type=test_type)
    
    def print_results(self, test_type='bid'):
        """Print test results summary"""
        print(f"\n{'='*80}")
        print(f"Test Results")
        print(f"{'='*80}")
        
        duration = (self.results['end_time'] - self.results['start_time']).total_seconds()
        
        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"\n📊 Request Summary:")
        print(f"  - Total requests: {self.results['total_requests']}")
        print(f"  - Successful (200/201): {self.results['successful']} ({self.results['successful']/self.results['total_requests']*100:.1f}%)")
        print(f"  - Rate limited (429): {self.results['rate_limited']} ({self.results['rate_limited']/self.results['total_requests']*100:.1f}%)")
        print(f"  - Errors (other): {self.results['errors']} ({self.results['errors']/self.results['total_requests']*100:.1f}%)")
        
        print(f"\n📈 Status Code Distribution:")
        for status, count in sorted(self.results['status_codes'].items()):
            print(f"  - {status}: {count} ({count/self.results['total_requests']*100:.1f}%)")
        
        if self.results['response_times']:
            avg_response = sum(self.results['response_times']) / len(self.results['response_times'])
            p95_response = sorted(self.results['response_times'])[int(len(self.results['response_times']) * 0.95)]
            p99_response = sorted(self.results['response_times'])[int(len(self.results['response_times']) * 0.99)]
            
            print(f"\n⚡ Response Times:")
            print(f"  - Average: {avg_response*1000:.0f}ms")
            print(f"  - p95: {p95_response*1000:.0f}ms")
            print(f"  - p99: {p99_response*1000:.0f}ms")
            print(f"  - Min: {min(self.results['response_times'])*1000:.0f}ms")
            print(f"  - Max: {max(self.results['response_times'])*1000:.0f}ms")
        
        requests_per_second = self.results['total_requests'] / duration
        print(f"\n🔥 Throughput: {requests_per_second:.2f} requests/second")
        
        print(f"\n{'='*80}")
        
        # Analysis
        print(f"\n🔍 Analysis:")
        
        rate_limit_percentage = (self.results['rate_limited'] / self.results['total_requests'] * 100) if self.results['total_requests'] > 0 else 0
        
        if rate_limit_percentage > 50:
            print(f"  ⚠️  HIGH: {rate_limit_percentage:.1f}% of requests were rate limited")
            print(f"  ➡️  Recommendation: Consider INCREASING rate limits")
        elif rate_limit_percentage > 20:
            print(f"  ⚠️  MODERATE: {rate_limit_percentage:.1f}% of requests were rate limited")
            print(f"  ➡️  Recommendation: Monitor in production, may need adjustment")
        elif rate_limit_percentage > 0:
            print(f"  ✅ GOOD: {rate_limit_percentage:.1f}% of requests were rate limited")
            print(f"  ➡️  Rate limiting is working as expected")
        else:
            print(f"  ⚠️  WARNING: No requests were rate limited")
            print(f"  ➡️  Rate limits may be too high or not enabled")
        
        if self.results['errors'] > self.results['successful'] * 0.1:
            print(f"  ⚠️  ERROR RATE: {self.results['errors']/self.results['total_requests']*100:.1f}% errors detected")
            print(f"  ➡️  Investigate error causes")
        
        print(f"\n{'='*80}\n")
        
        # Save results to file
        results_file = f"/app/load_tests/results_{test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                **self.results,
                'start_time': self.results['start_time'].isoformat(),
                'end_time': self.results['end_time'].isoformat(),
                'duration_seconds': duration,
                'requests_per_second': requests_per_second
            }, f, indent=2, default=str)
        
        print(f"📝 Results saved to: {results_file}\n")

async def main():
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'bid'
    
    if test_type not in ['bid', 'league']:
        print(f"❌ Invalid test type: {test_type}. Use 'bid' or 'league'")
        sys.exit(1)
    
    runner = LoadTestRunner()
    await runner.run_test(test_type=test_type)

if __name__ == "__main__":
    asyncio.run(main())
