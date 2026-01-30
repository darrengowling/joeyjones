#!/usr/bin/env python3
"""
Pilot Deployment Smoke Test
Automated testing of real-time features after deployment
"""

import asyncio
import aiohttp
import time
from datetime import datetime
import sys

BASE_URL = "https://fantasy-ux-pilot.preview.emergentagent.com/api"

class SmokeTest:
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        self.test_league_id = None
        self.test_auction_id = None
        
    def log_test(self, name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results['tests'].append({
            'name': name,
            'passed': passed,
            'message': message
        })
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        print(f"{status}: {name}")
        if message:
            print(f"  ℹ️  {message}")
    
    async def test_backend_health(self, session):
        """Test 1: Backend responds"""
        try:
            async with session.get(f"{BASE_URL}/sports") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Backend Health", True, f"Found {len(data)} sports")
                    return True
                else:
                    self.log_test("Backend Health", False, f"Status: {resp.status}")
                    return False
        except Exception as e:
            self.log_test("Backend Health", False, str(e))
            return False
    
    async def test_metrics_endpoint(self, session):
        """Test 2: Metrics endpoint accessible"""
        try:
            async with session.get("https://fantasy-ux-pilot.preview.emergentagent.com/api/metrics") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    has_metrics = "python_info" in text
                    self.log_test("Metrics Endpoint", has_metrics, "Prometheus metrics available")
                    return has_metrics
                else:
                    self.log_test("Metrics Endpoint", False, f"Status: {resp.status}")
                    return False
        except Exception as e:
            self.log_test("Metrics Endpoint", False, str(e))
            return False
    
    async def test_cors_headers(self, session):
        """Test 3: CORS headers present"""
        try:
            headers = {
                "Origin": "https://fantasy-ux-pilot.preview.emergentagent.com"
            }
            async with session.options(f"{BASE_URL}/sports", headers=headers) as resp:
                allow_origin = resp.headers.get('Access-Control-Allow-Origin', '')
                has_cors = "bid-socket-system.preview.emergentagent.com" in allow_origin
                self.log_test("CORS Headers", has_cors, f"Allow-Origin: {allow_origin}")
                return has_cors
        except Exception as e:
            self.log_test("CORS Headers", False, str(e))
            return False
    
    async def test_rate_limiting_disabled(self, session):
        """Test 4: Rate limiting disabled (no 429s)"""
        try:
            # Make 5 rapid requests
            responses = []
            for i in range(5):
                async with session.get(f"{BASE_URL}/sports") as resp:
                    responses.append(resp.status)
            
            has_429 = 429 in responses
            self.log_test("Rate Limiting Disabled", not has_429, 
                         f"Responses: {responses}" if has_429 else "No 429 errors")
            return not has_429
        except Exception as e:
            self.log_test("Rate Limiting Disabled", False, str(e))
            return False
    
    async def test_debug_endpoint_secured(self, session):
        """Test 5: Debug endpoint returns 404"""
        try:
            async with session.get(f"{BASE_URL}/debug/rooms/league/test-123") as resp:
                is_404 = resp.status == 404
                self.log_test("Debug Endpoint Secured", is_404, 
                             f"Status: {resp.status} (expected 404)")
                return is_404
        except Exception as e:
            self.log_test("Debug Endpoint Secured", False, str(e))
            return False
    
    async def test_league_creation(self, session):
        """Test 6: Create test league"""
        try:
            async with session.post(
                f"{BASE_URL}/leagues",
                json={
                    "name": f"Smoke Test League {datetime.now().strftime('%H%M%S')}",
                    "sportKey": "football",
                    "commissionerId": f"smoke-test-{int(time.time())}",
                    "budget": 500000000,
                    "minManagers": 2,
                    "maxManagers": 8,
                    "clubSlots": 3,
                    "timerSeconds": 30,
                    "antiSnipeSeconds": 10
                }
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    self.test_league_id = data.get('id')
                    self.log_test("League Creation", True, f"League ID: {self.test_league_id}")
                    return True
                else:
                    self.log_test("League Creation", False, f"Status: {resp.status}")
                    return False
        except Exception as e:
            self.log_test("League Creation", False, str(e))
            return False
    
    async def test_auction_start(self, session):
        """Test 7: Start auction"""
        if not self.test_league_id:
            self.log_test("Auction Start", False, "No league ID (skipped)")
            return False
        
        try:
            async with session.post(
                f"{BASE_URL}/leagues/{self.test_league_id}/auction/start"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.test_auction_id = data.get('auctionId')
                    self.log_test("Auction Start", True, f"Auction ID: {self.test_auction_id}")
                    return True
                else:
                    self.log_test("Auction Start", False, f"Status: {resp.status}")
                    return False
        except Exception as e:
            self.log_test("Auction Start", False, str(e))
            return False
    
    async def test_socketio_endpoint(self, session):
        """Test 8: Socket.IO endpoint responds"""
        try:
            async with session.get(
                "https://fantasy-ux-pilot.preview.emergentagent.com/socket.io/?transport=polling"
            ) as resp:
                is_ok = resp.status in [200, 400]  # 400 is OK if it's a connection error
                self.log_test("Socket.IO Endpoint", is_ok, 
                             f"Status: {resp.status} (endpoint accessible)")
                return is_ok
        except Exception as e:
            self.log_test("Socket.IO Endpoint", False, str(e))
            return False
    
    async def run_all_tests(self):
        """Run all smoke tests"""
        print("="*80)
        print("Pilot Deployment Smoke Test")
        print("="*80)
        print(f"Base URL: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print()
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Run tests in sequence
            await self.test_backend_health(session)
            await self.test_metrics_endpoint(session)
            await self.test_cors_headers(session)
            await self.test_rate_limiting_disabled(session)
            await self.test_debug_endpoint_secured(session)
            await self.test_league_creation(session)
            await self.test_auction_start(session)
            await self.test_socketio_endpoint(session)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print()
        print("="*80)
        print("Test Summary")
        print("="*80)
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()
        
        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED! Deployment ready for manual smoke test.")
            print()
            print("Next Steps:")
            print("1. Open two browsers (normal + incognito)")
            print("2. Test real-time features (lobby, auction button, bids)")
            print("3. Verify metrics at /api/metrics")
            print("4. Check for CORS errors in console")
        else:
            print("⚠️  SOME TESTS FAILED. Review failures before proceeding.")
            print()
            print("Failed Tests:")
            for test in self.results['tests']:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['message']}")
        
        print("="*80)
        
        # Exit code based on results
        sys.exit(0 if self.results['failed'] == 0 else 1)

async def main():
    runner = SmokeTest()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
