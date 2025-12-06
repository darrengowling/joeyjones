#!/usr/bin/env python3
"""
Quick test script to create fresh auction and test timer
"""

import asyncio
import aiohttp
import socketio
import time
import json

BASE_URL = "https://restart-auction.preview.emergentagent.com/api"
SOCKET_URL = "https://restart-auction.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

async def test_timer_fix():
    """Test timer functionality with fresh auction"""
    
    async with aiohttp.ClientSession() as session:
        print("=== Creating fresh auction for timer test ===")
        
        # Create user
        user_data = {"name": "Timer Test User", "email": "timer.test@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user_result = await response.json()
            user_id = user_result["id"]
            print(f"✅ Created user: {user_id}")
        
        # Seed clubs
        async with session.post(f"{BASE_URL}/clubs/seed") as response:
            print(f"✅ Seeded clubs: {response.status}")
        
        # Create league
        league_data = {
            "name": "Timer Test League",
            "commissionerId": user_id,
            "budget": 1000.0,
            "minManagers": 1,  # Single manager for testing
            "maxManagers": 2,
            "clubSlots": 3
        }
        async with session.post(f"{BASE_URL}/leagues", json=league_data) as response:
            league_result = await response.json()
            league_id = league_result["id"]
            invite_token = league_result["inviteToken"]
            print(f"✅ Created league: {league_id}")
        
        # Join league
        join_data = {"userId": user_id, "inviteToken": invite_token}
        async with session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data) as response:
            print(f"✅ Joined league: {response.status}")
        
        # Start auction
        async with session.post(f"{BASE_URL}/leagues/{league_id}/auction/start") as response:
            auction_result = await response.json()
            auction_id = auction_result["auctionId"]
            print(f"✅ Started auction: {auction_id}")
        
        # Get auction details
        async with session.get(f"{BASE_URL}/auction/{auction_id}") as response:
            auction_details = await response.json()
            current_club = auction_details["currentClub"]
            print(f"✅ Current club: {current_club['name']}")
        
        print("\n=== Testing Socket.IO timer events ===")
        
        # Set up Socket.IO client
        sio = socketio.AsyncClient()
        events_received = []
        
        @sio.event
        async def connect():
            print("🔌 Socket.IO connected")
            events_received.append("connected")
        
        @sio.event 
        async def joined(data):
            print(f"🎯 Joined auction room: {data}")
            events_received.append("joined")
        
        @sio.event
        async def sync_state(data):
            time_remaining = data.get('timeRemaining', 0)
            print(f"📊 Received sync_state: timeRemaining={time_remaining}")
            events_received.append(f"sync_state:{time_remaining}")
        
        @sio.event
        async def timer_update(data):
            time_remaining = data.get('timeRemaining', 0)
            auction_id_in_event = data.get('auctionId', 'none')
            print(f"🕒 Timer update received: {time_remaining}s for auction {auction_id_in_event}")
            if auction_id_in_event == auction_id:
                events_received.append(f"timer_update:{time_remaining}")
            else:
                events_received.append(f"timer_update_other:{time_remaining}")
        
        @sio.event
        async def test_room_message(data):
            print(f"🧪 Test room message: {data}")
            events_received.append("test_room_message")
        
        @sio.event
        async def timer_update_broadcast(data):
            time_remaining = data.get('timeRemaining', 0)
            auction_id = data.get('auctionId', 'unknown')
            print(f"📡 Broadcast timer update: {time_remaining}s for auction {auction_id}")
            events_received.append(f"timer_broadcast:{time_remaining}")
        
        try:
            # Connect to socket
            await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            await asyncio.sleep(2)
            
            # Join auction room
            await sio.emit('join_auction', {'auctionId': auction_id})
            await asyncio.sleep(2)
            
            # Monitor timer events for 15 seconds
            print("\n🕐 Monitoring timer events for 15 seconds...")
            initial_events = len(events_received)
            
            for i in range(15):
                await asyncio.sleep(1)
                timer_updates = [e for e in events_received if e.startswith("timer_update")]
                print(f"  {i+1:2d}s: {len(timer_updates)} timer updates received")
            
            final_events = len(events_received)
            timer_events = [e for e in events_received if e.startswith("timer_update")]
            
            print(f"\n📈 Results:")
            print(f"   Total events: {final_events}")
            print(f"   Timer updates: {len(timer_events)}")
            print(f"   Events received: {events_received}")
            
            if len(timer_events) >= 10:  # Should get at least 10 timer updates in 15 seconds
                print("✅ Timer events working correctly!")
                return True
            else:
                print("❌ Timer events not working - no or insufficient timer_update events received")
                return False
            
        except Exception as e:
            print(f"❌ Socket.IO test failed: {str(e)}")
            return False
        
        finally:
            await sio.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_timer_fix())
    print(f"\n{'🎉 TIMER FIX SUCCESSFUL' if success else '🚨 TIMER STILL BROKEN'}")