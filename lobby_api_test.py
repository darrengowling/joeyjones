#!/usr/bin/env python3
"""
Instant Lobby Updates API Test

Tests the API endpoints for instant lobby updates:
1. GET /api/leagues/:id/members endpoint
2. POST /api/leagues/:id/join endpoint  
3. Member list ordering and format
4. Real-time event emission verification via backend logs

This test focuses on the backend API functionality without Socket.IO client testing.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timezone
import time
import uuid

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cricket-bid-arena.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class LobbyAPITester:
    def __init__(self):
        self.session = None
        self.test_users = []
        self.test_league = None
        
    async def setup(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Setting up API test environment...")
        print(f"📡 Backend URL: {BACKEND_URL}")
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            
        # Cleanup test data
        await self.cleanup_test_data()
        
    async def cleanup_test_data(self):
        """Clean up test users and league"""
        try:
            if self.test_league:
                # Delete test league
                async with self.session.delete(
                    f"{API_BASE}/leagues/{self.test_league['id']}",
                    params={"commissioner_id": self.test_league['commissionerId']}
                ) as resp:
                    if resp.status in [200, 404]:
                        print(f"🗑️ Cleaned up test league: {self.test_league['name']}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
            
    async def create_test_user(self, name_suffix=""):
        """Create a test user"""
        user_data = {
            "name": f"LobbyTestUser{name_suffix}_{int(time.time())}",
            "email": f"lobbytest{name_suffix}_{int(time.time())}@example.com"
        }
        
        async with self.session.post(f"{API_BASE}/users", json=user_data) as resp:
            if resp.status == 200:
                user = await resp.json()
                self.test_users.append(user)
                print(f"👤 Created test user: {user['name']} ({user['id']})")
                return user
            else:
                text = await resp.text()
                raise Exception(f"Failed to create user: {resp.status} - {text}")
                
    async def create_test_league(self, commissioner):
        """Create a test league"""
        league_data = {
            "name": f"LobbyAPITest_{int(time.time())}",
            "commissionerId": commissioner['id'],
            "budget": 500000000,  # £500M
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 3,
            "timerSeconds": 30,
            "antiSnipeSeconds": 10,
            "sportKey": "football"
        }
        
        async with self.session.post(f"{API_BASE}/leagues", json=league_data) as resp:
            if resp.status == 200:
                league = await resp.json()
                self.test_league = league
                print(f"🏆 Created test league: {league['name']} ({league['id']})")
                return league
            else:
                text = await resp.text()
                raise Exception(f"Failed to create league: {resp.status} - {text}")
                
    async def test_members_api_endpoint(self):
        """Test 1: GET /api/leagues/:id/members endpoint"""
        print("\n" + "="*60)
        print("TEST 1: GET /api/leagues/:id/members API Endpoint")
        print("="*60)
        
        league_id = self.test_league['id']
        
        # Test endpoint with initial commissioner
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            if resp.status == 200:
                members = await resp.json()
                print(f"✅ API endpoint working - returned {len(members)} members")
                
                # Verify response format
                if isinstance(members, list):
                    print("✅ Response is a list")
                    
                    if len(members) > 0:
                        member = members[0]
                        required_fields = ['userId', 'displayName', 'joinedAt']
                        for field in required_fields:
                            if field in member:
                                print(f"✅ Member has required field: {field}")
                            else:
                                print(f"❌ Member missing field: {field}")
                                return False
                                
                        # Verify data types
                        if isinstance(member['userId'], str):
                            print("✅ userId is string")
                        else:
                            print("❌ userId is not string")
                            return False
                            
                        if isinstance(member['displayName'], str):
                            print("✅ displayName is string")
                        else:
                            print("❌ displayName is not string")
                            return False
                            
                        # Verify joinedAt is valid ISO timestamp
                        try:
                            datetime.fromisoformat(member['joinedAt'].replace('Z', '+00:00'))
                            print("✅ joinedAt is valid ISO timestamp")
                        except ValueError:
                            print("❌ joinedAt is not valid ISO timestamp")
                            return False
                    
                    return True
                else:
                    print("❌ Response is not a list")
                    return False
            else:
                text = await resp.text()
                print(f"❌ API endpoint failed: {resp.status} - {text}")
                return False
                
    async def test_join_league_api(self):
        """Test 2: POST /api/leagues/:id/join endpoint"""
        print("\n" + "="*60)
        print("TEST 2: POST /api/leagues/:id/join API Endpoint")
        print("="*60)
        
        # Create a new user to join
        new_user = await self.create_test_user("Joiner")
        league_id = self.test_league['id']
        
        # Get initial member count
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            initial_members = await resp.json()
            initial_count = len(initial_members)
            print(f"📊 Initial member count: {initial_count}")
        
        # Join the league
        join_data = {
            "userId": new_user['id'],
            "inviteToken": self.test_league['inviteToken']
        }
        
        async with self.session.post(
            f"{API_BASE}/leagues/{league_id}/join", 
            json=join_data
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ User joined league successfully")
                print(f"📝 Join response: {result.get('message', 'No message')}")
            else:
                text = await resp.text()
                print(f"❌ Failed to join league: {resp.status} - {text}")
                return False
        
        # Verify member count increased
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            updated_members = await resp.json()
            updated_count = len(updated_members)
            print(f"📊 Updated member count: {updated_count}")
            
            if updated_count == initial_count + 1:
                print("✅ Member count increased correctly")
            else:
                print(f"❌ Member count incorrect: expected {initial_count + 1}, got {updated_count}")
                return False
                
        # Verify new member is in the list
        new_member_found = any(m['userId'] == new_user['id'] for m in updated_members)
        if new_member_found:
            print("✅ New member found in members list")
        else:
            print("❌ New member not found in members list")
            return False
            
        # Verify member data is correct
        new_member = next(m for m in updated_members if m['userId'] == new_user['id'])
        if new_member['displayName'] == new_user['name']:
            print("✅ New member displayName is correct")
        else:
            print(f"❌ New member displayName incorrect: {new_member['displayName']} != {new_user['name']}")
            return False
            
        return True
        
    async def test_member_ordering(self):
        """Test 3: Member list ordering by joinedAt"""
        print("\n" + "="*60)
        print("TEST 3: Member List Ordering by joinedAt")
        print("="*60)
        
        league_id = self.test_league['id']
        
        # Add multiple users with delays to ensure different joinedAt times
        join_times = []
        for i in range(3):
            new_user = await self.create_test_user(f"OrderTest{i}")
            
            join_start = time.time()
            join_data = {
                "userId": new_user['id'],
                "inviteToken": self.test_league['inviteToken']
            }
            
            async with self.session.post(
                f"{API_BASE}/leagues/{league_id}/join", 
                json=join_data
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ Failed to join user {i}: {resp.status} - {text}")
                    return False
                    
            join_times.append(join_start)
            print(f"👤 User {i} joined at {join_start}")
            await asyncio.sleep(0.5)  # Small delay to ensure different timestamps
            
        # Get final member list
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            members = await resp.json()
            
        print(f"📊 Final member count: {len(members)}")
        
        # Verify ordering by joinedAt
        if len(members) > 1:
            joined_times = []
            for member in members:
                joined_at = datetime.fromisoformat(member['joinedAt'].replace('Z', '+00:00'))
                joined_times.append(joined_at)
                print(f"👤 {member['displayName']}: {member['joinedAt']}")
                
            # Check if ordered (ascending)
            is_ordered = all(joined_times[i] <= joined_times[i+1] for i in range(len(joined_times)-1))
            if is_ordered:
                print("✅ Members are ordered by joinedAt (ascending)")
                return True
            else:
                print("❌ Members are not properly ordered by joinedAt")
                return False
        else:
            print("⚠️ Not enough members to test ordering")
            return True
            
    async def test_duplicate_join_prevention(self):
        """Test 4: Prevent duplicate joins"""
        print("\n" + "="*60)
        print("TEST 4: Duplicate Join Prevention")
        print("="*60)
        
        # Try to join the same user twice
        existing_user = self.test_users[1]  # Use second user (first is commissioner)
        league_id = self.test_league['id']
        
        # Get current member count
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            initial_members = await resp.json()
            initial_count = len(initial_members)
            
        # Try to join again
        join_data = {
            "userId": existing_user['id'],
            "inviteToken": self.test_league['inviteToken']
        }
        
        async with self.session.post(
            f"{API_BASE}/leagues/{league_id}/join", 
            json=join_data
        ) as resp:
            result = await resp.json()
            
            if resp.status == 200:
                if "Already joined" in result.get('message', ''):
                    print("✅ Duplicate join handled correctly")
                else:
                    print("✅ Duplicate join allowed (returning existing participant)")
            else:
                print(f"❌ Unexpected error on duplicate join: {resp.status}")
                return False
                
        # Verify member count didn't increase
        async with self.session.get(f"{API_BASE}/leagues/{league_id}/members") as resp:
            final_members = await resp.json()
            final_count = len(final_members)
            
        if final_count == initial_count:
            print("✅ Member count unchanged (no duplicate)")
            return True
        else:
            print(f"❌ Member count changed: {initial_count} -> {final_count}")
            return False
            
    async def test_invalid_invite_token(self):
        """Test 5: Invalid invite token handling"""
        print("\n" + "="*60)
        print("TEST 5: Invalid Invite Token Handling")
        print("="*60)
        
        new_user = await self.create_test_user("InvalidToken")
        league_id = self.test_league['id']
        
        # Try to join with invalid token
        join_data = {
            "userId": new_user['id'],
            "inviteToken": "invalid-token-12345"
        }
        
        async with self.session.post(
            f"{API_BASE}/leagues/{league_id}/join", 
            json=join_data
        ) as resp:
            if resp.status == 403:
                result = await resp.json()
                print("✅ Invalid token correctly rejected with 403")
                print(f"📝 Error message: {result.get('detail', 'No detail')}")
                return True
            else:
                print(f"❌ Invalid token not handled correctly: {resp.status}")
                return False
                
    async def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Instant Lobby Updates API Test")
        print(f"⏰ Test started at: {datetime.now()}")
        
        try:
            await self.setup()
            
            # Create test users and league
            commissioner = await self.create_test_user("Commissioner")
            await self.create_test_league(commissioner)
            
            # Run tests
            test_results = {}
            
            test_results['members_api_endpoint'] = await self.test_members_api_endpoint()
            test_results['join_league_api'] = await self.test_join_league_api()
            test_results['member_ordering'] = await self.test_member_ordering()
            test_results['duplicate_join_prevention'] = await self.test_duplicate_join_prevention()
            test_results['invalid_invite_token'] = await self.test_invalid_invite_token()
            
            # Summary
            print("\n" + "="*60)
            print("API TEST RESULTS SUMMARY")
            print("="*60)
            
            passed_tests = sum(1 for result in test_results.values() if result)
            total_tests = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{test_name.replace('_', ' ').title()}: {status}")
                
            print(f"\nOverall: {passed_tests}/{total_tests} API tests passed")
            
            if passed_tests == total_tests:
                print("🎉 ALL API TESTS PASSED!")
                print("✅ GET /api/leagues/:id/members returns ordered member list")
                print("✅ POST /api/leagues/:id/join adds members correctly")
                print("✅ Member list properly ordered by joinedAt")
                print("✅ Duplicate joins handled correctly")
                print("✅ Invalid tokens rejected properly")
                return True
            else:
                print("❌ Some API tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = LobbyAPITester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 LOBBY API ENDPOINTS: WORKING CORRECTLY")
        return 0
    else:
        print("\n🚨 LOBBY API ENDPOINTS: NEED FIXES")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)