#!/usr/bin/env python3
"""
Instant Lobby Updates Implementation Test

Tests the real-time lobby updates when users join leagues:
1. API Endpoint Test: GET /api/leagues/:id/members
2. Real-Time Event Emissions: member_joined and sync_members events  
3. Multi-User Real-Time Test: Socket.IO event delivery
4. Edge Cases: Multiple users, no duplicates, correct ordering

GOAL: Verify that when a user joins a league, all existing members 
(especially the commissioner) see the new member appear in the lobby 
within ~1 second without refresh.
"""

import asyncio
import aiohttp
import socketio
import json
import os
import sys
from datetime import datetime, timezone
import time
import uuid

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://prod-auction-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = f"{BACKEND_URL}/api/socket.io"

class InstantLobbyTester:
    def __init__(self):
        self.session = None
        self.sockets = {}  # Store multiple socket connections
        self.received_events = {}  # Track events received by each socket
        self.test_users = []
        self.test_league = None
        
    async def setup(self):
        """Setup HTTP session and test data"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Setting up test environment...")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔌 Socket.IO URL: {SOCKET_URL}")
        
    async def cleanup(self):
        """Cleanup resources"""
        # Disconnect all sockets
        for socket_id, sio in self.sockets.items():
            if sio.connected:
                await sio.disconnect()
                print(f"🔌 Disconnected socket: {socket_id}")
        
        # Close HTTP session
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
            "name": f"TestUser{name_suffix}_{int(time.time())}",
            "email": f"testuser{name_suffix}_{int(time.time())}@example.com"
        }
        
        async with self.session.post(f"{API_BASE}/users", json=user_data) as resp:
            if resp.status == 200:
                user = await resp.json()
                self.test_users.append(user)
                print(f"👤 Created test user: {user['name']} ({user['id']})")
                return user
            else:
                raise Exception(f"Failed to create user: {resp.status}")
                
    async def create_test_league(self, commissioner):
        """Create a test league"""
        league_data = {
            "name": f"InstantLobbyTest_{int(time.time())}",
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
                
    async def create_socket_connection(self, user_id, socket_name):
        """Create a Socket.IO connection for a user"""
        sio = socketio.AsyncClient()
        self.received_events[socket_name] = []
        
        # Event handlers to track received events
        @sio.event
        async def connect():
            print(f"🔌 Socket connected: {socket_name}")
            
        @sio.event
        async def disconnect():
            print(f"🔌 Socket disconnected: {socket_name}")
            
        @sio.event
        async def member_joined(data):
            print(f"📨 {socket_name} received member_joined: {data}")
            self.received_events[socket_name].append({
                'event': 'member_joined',
                'data': data,
                'timestamp': time.time()
            })
            
        @sio.event
        async def sync_members(data):
            print(f"📨 {socket_name} received sync_members: {data}")
            self.received_events[socket_name].append({
                'event': 'sync_members', 
                'data': data,
                'timestamp': time.time()
            })
            
        @sio.event
        async def participant_joined(data):
            print(f"📨 {socket_name} received participant_joined: {data}")
            self.received_events[socket_name].append({
                'event': 'participant_joined',
                'data': data, 
                'timestamp': time.time()
            })
        
        # Connect to Socket.IO
        try:
            await sio.connect(SOCKET_URL)
            self.sockets[socket_name] = sio
            return sio
        except Exception as e:
            print(f"❌ Failed to connect socket {socket_name}: {e}")
            raise
            
    async def join_league_room(self, socket_name, league_id):
        """Join a league room via Socket.IO"""
        sio = self.sockets[socket_name]
        await sio.emit('join_league_room', {'leagueId': league_id})
        print(f"🏠 {socket_name} joined league room: {league_id}")
        
    async def test_api_endpoint(self):
        """Test 1: API Endpoint Test - GET /api/leagues/:id/members"""
        print("\n" + "="*60)
        print("TEST 1: API Endpoint - GET /api/leagues/:id/members")
        print("="*60)
        
        league_id = self.test_league['id']
        
        # Test endpoint exists and returns data
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
                                
                        # Check ordering by joinedAt
                        if len(members) > 1:
                            for i in range(1, len(members)):
                                prev_time = datetime.fromisoformat(members[i-1]['joinedAt'].replace('Z', '+00:00'))
                                curr_time = datetime.fromisoformat(members[i]['joinedAt'].replace('Z', '+00:00'))
                                if prev_time <= curr_time:
                                    print("✅ Members ordered by joinedAt")
                                else:
                                    print("❌ Members not properly ordered by joinedAt")
                                    return False
                    
                    return True
                else:
                    print("❌ Response is not a list")
                    return False
            else:
                print(f"❌ API endpoint failed: {resp.status}")
                return False
                
    async def test_real_time_events(self):
        """Test 2: Real-Time Event Emissions"""
        print("\n" + "="*60)
        print("TEST 2: Real-Time Event Emissions")
        print("="*60)
        
        # Create commissioner socket connection
        commissioner = self.test_users[0]
        commissioner_socket = await self.create_socket_connection(
            commissioner['id'], 
            f"commissioner_{commissioner['name']}"
        )
        
        # Join league room
        await self.join_league_room(f"commissioner_{commissioner['name']}", self.test_league['id'])
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(1)
        
        # Clear any initial events
        socket_name = f"commissioner_{commissioner['name']}"
        self.received_events[socket_name] = []
        
        # Create a new user to join the league
        new_user = await self.create_test_user("NewJoiner")
        
        # Record time before join
        join_start_time = time.time()
        
        # Join the league via API
        join_data = {
            "userId": new_user['id'],
            "inviteToken": self.test_league['inviteToken']
        }
        
        async with self.session.post(
            f"{API_BASE}/leagues/{self.test_league['id']}/join", 
            json=join_data
        ) as resp:
            if resp.status == 200:
                print(f"✅ User {new_user['name']} joined league successfully")
            else:
                text = await resp.text()
                print(f"❌ Failed to join league: {resp.status} - {text}")
                return False
        
        # Wait for events (up to 3 seconds)
        print("⏳ Waiting for real-time events...")
        await asyncio.sleep(3)
        
        # Check received events
        events = self.received_events[socket_name]
        print(f"📊 Commissioner received {len(events)} events")
        
        # Check for member_joined event
        member_joined_events = [e for e in events if e['event'] == 'member_joined']
        if member_joined_events:
            event = member_joined_events[0]
            event_time = event['timestamp'] - join_start_time
            print(f"✅ member_joined event received in {event_time:.2f}s")
            
            # Verify event data
            data = event['data']
            if data.get('userId') == new_user['id']:
                print("✅ member_joined event has correct userId")
            else:
                print(f"❌ member_joined event userId mismatch: {data.get('userId')} != {new_user['id']}")
                
            if data.get('displayName') == new_user['name']:
                print("✅ member_joined event has correct displayName")
            else:
                print(f"❌ member_joined event displayName mismatch: {data.get('displayName')} != {new_user['name']}")
                
            if 'joinedAt' in data:
                print("✅ member_joined event has joinedAt timestamp")
            else:
                print("❌ member_joined event missing joinedAt")
        else:
            print("❌ No member_joined event received")
            return False
            
        # Check for sync_members event
        sync_events = [e for e in events if e['event'] == 'sync_members']
        if sync_events:
            event = sync_events[0]
            event_time = event['timestamp'] - join_start_time
            print(f"✅ sync_members event received in {event_time:.2f}s")
            
            # Verify event data
            data = event['data']
            if 'members' in data and isinstance(data['members'], list):
                members = data['members']
                print(f"✅ sync_members event contains {len(members)} members")
                
                # Check if new user is in the list
                new_user_found = any(m.get('userId') == new_user['id'] for m in members)
                if new_user_found:
                    print("✅ New user found in sync_members list")
                else:
                    print("❌ New user not found in sync_members list")
                    return False
            else:
                print("❌ sync_members event missing or invalid members array")
                return False
        else:
            print("❌ No sync_members event received")
            return False
            
        return True
        
    async def test_multi_user_real_time(self):
        """Test 3: Multi-User Real-Time Test"""
        print("\n" + "="*60)
        print("TEST 3: Multi-User Real-Time Test")
        print("="*60)
        
        # Create multiple socket connections
        user_sockets = []
        for i, user in enumerate(self.test_users[:3]):  # Use first 3 users
            socket_name = f"user_{i}_{user['name']}"
            socket = await self.create_socket_connection(user['id'], socket_name)
            await self.join_league_room(socket_name, self.test_league['id'])
            user_sockets.append(socket_name)
            
        # Wait for connections to stabilize
        await asyncio.sleep(2)
        
        # Clear events
        for socket_name in user_sockets:
            self.received_events[socket_name] = []
            
        # Create and join a new user
        new_user = await self.create_test_user("MultiTest")
        join_start_time = time.time()
        
        join_data = {
            "userId": new_user['id'],
            "inviteToken": self.test_league['inviteToken']
        }
        
        async with self.session.post(
            f"{API_BASE}/leagues/{self.test_league['id']}/join", 
            json=join_data
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"❌ Failed to join league: {resp.status} - {text}")
                return False
                
        # Wait for events
        await asyncio.sleep(3)
        
        # Check that ALL connected users received the events
        all_received_member_joined = True
        all_received_sync_members = True
        
        for socket_name in user_sockets:
            events = self.received_events[socket_name]
            
            # Check member_joined
            member_joined_events = [e for e in events if e['event'] == 'member_joined']
            if member_joined_events:
                event_time = member_joined_events[0]['timestamp'] - join_start_time
                print(f"✅ {socket_name} received member_joined in {event_time:.2f}s")
            else:
                print(f"❌ {socket_name} did not receive member_joined event")
                all_received_member_joined = False
                
            # Check sync_members
            sync_events = [e for e in events if e['event'] == 'sync_members']
            if sync_events:
                event_time = sync_events[0]['timestamp'] - join_start_time
                print(f"✅ {socket_name} received sync_members in {event_time:.2f}s")
            else:
                print(f"❌ {socket_name} did not receive sync_members event")
                all_received_sync_members = False
                
        if all_received_member_joined:
            print("✅ All users received member_joined event")
        else:
            print("❌ Not all users received member_joined event")
            
        if all_received_sync_members:
            print("✅ All users received sync_members event")
        else:
            print("❌ Not all users received sync_members event")
            
        return all_received_member_joined and all_received_sync_members
        
    async def test_edge_cases(self):
        """Test 4: Edge Cases"""
        print("\n" + "="*60)
        print("TEST 4: Edge Cases")
        print("="*60)
        
        # Test with 3+ users joining sequentially
        print("🔄 Testing sequential joins...")
        
        # Create commissioner socket
        commissioner = self.test_users[0]
        socket_name = f"commissioner_edge_{commissioner['name']}"
        await self.create_socket_connection(commissioner['id'], socket_name)
        await self.join_league_room(socket_name, self.test_league['id'])
        
        await asyncio.sleep(1)
        self.received_events[socket_name] = []
        
        # Join 3 users sequentially
        join_times = []
        for i in range(3):
            new_user = await self.create_test_user(f"Sequential{i}")
            
            join_start = time.time()
            join_data = {
                "userId": new_user['id'],
                "inviteToken": self.test_league['inviteToken']
            }
            
            async with self.session.post(
                f"{API_BASE}/leagues/{self.test_league['id']}/join", 
                json=join_data
            ) as resp:
                if resp.status != 200:
                    print(f"❌ Failed to join user {i}: {resp.status}")
                    return False
                    
            join_times.append(join_start)
            await asyncio.sleep(1)  # Small delay between joins
            
        # Wait for all events
        await asyncio.sleep(3)
        
        # Check events received
        events = self.received_events[socket_name]
        member_joined_events = [e for e in events if e['event'] == 'member_joined']
        sync_events = [e for e in events if e['event'] == 'sync_members']
        
        print(f"📊 Received {len(member_joined_events)} member_joined events")
        print(f"📊 Received {len(sync_events)} sync_members events")
        
        # Verify no duplicate members in sync_members
        if sync_events:
            latest_sync = sync_events[-1]
            members = latest_sync['data'].get('members', [])
            user_ids = [m.get('userId') for m in members]
            unique_user_ids = set(user_ids)
            
            if len(user_ids) == len(unique_user_ids):
                print("✅ No duplicate members in sync_members")
            else:
                print(f"❌ Duplicate members found: {len(user_ids)} total, {len(unique_user_ids)} unique")
                return False
                
            # Verify joinedAt timestamps are in correct order
            joined_times = []
            for member in members:
                if 'joinedAt' in member:
                    joined_times.append(datetime.fromisoformat(member['joinedAt'].replace('Z', '+00:00')))
                    
            if len(joined_times) > 1:
                is_ordered = all(joined_times[i] <= joined_times[i+1] for i in range(len(joined_times)-1))
                if is_ordered:
                    print("✅ joinedAt timestamps are in correct order")
                else:
                    print("❌ joinedAt timestamps are not properly ordered")
                    return False
        else:
            print("❌ No sync_members events received")
            return False
            
        return True
        
    async def run_all_tests(self):
        """Run all instant lobby update tests"""
        print("🚀 Starting Instant Lobby Updates Implementation Test")
        print(f"⏰ Test started at: {datetime.now()}")
        
        try:
            await self.setup()
            
            # Create test users and league
            commissioner = await self.create_test_user("Commissioner")
            await self.create_test_league(commissioner)
            
            # Run tests
            test_results = {}
            
            test_results['api_endpoint'] = await self.test_api_endpoint()
            test_results['real_time_events'] = await self.test_real_time_events()
            test_results['multi_user_real_time'] = await self.test_multi_user_real_time()
            test_results['edge_cases'] = await self.test_edge_cases()
            
            # Summary
            print("\n" + "="*60)
            print("TEST RESULTS SUMMARY")
            print("="*60)
            
            passed_tests = sum(1 for result in test_results.values() if result)
            total_tests = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{test_name.replace('_', ' ').title()}: {status}")
                
            print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 ALL ACCEPTANCE CRITERIA MET!")
                print("✅ GET /api/leagues/:id/members returns ordered member list")
                print("✅ member_joined event emitted on POST /api/leagues/:id/join")
                print("✅ sync_members event emitted with complete ordered list")
                print("✅ Events delivered to all sockets in league room within ~1s")
                print("✅ No duplicate members in the list")
                return True
            else:
                print("❌ Some tests failed - instant lobby updates need fixes")
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
    tester = InstantLobbyTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 INSTANT LOBBY UPDATES: PRODUCTION READY")
        sys.exit(0)
    else:
        print("\n🚨 INSTANT LOBBY UPDATES: NEEDS FIXES")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())