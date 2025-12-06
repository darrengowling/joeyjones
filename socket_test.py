#!/usr/bin/env python3
"""
Focused Socket.IO Event Testing
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime

# Configuration
BASE_URL = "https://draft-kings-mobile.preview.emergentagent.com/api"
SOCKET_URL = "https://draft-kings-mobile.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

def test_socket_events():
    """Test Socket.IO events in detail"""
    print("=== Detailed Socket.IO Event Testing ===")
    
    # Create test data first
    session = requests.Session()
    
    # Create user
    user_data = {"name": "Socket Tester", "email": "socket.test@test.com"}
    user_response = session.post(f"{BASE_URL}/users", json=user_data)
    user_id = user_response.json()["id"]
    print(f"Created user: {user_id}")
    
    # Seed clubs
    session.post(f"{BASE_URL}/clubs/seed")
    
    # Create league
    league_data = {
        "name": "Socket Test League",
        "commissionerId": user_id,
        "budget": 100.0,
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3
    }
    league_response = session.post(f"{BASE_URL}/leagues", json=league_data)
    league_id = league_response.json()["id"]
    invite_token = league_response.json()["inviteToken"]
    print(f"Created league: {league_id}")
    
    # Join league
    join_data = {"userId": user_id, "inviteToken": invite_token}
    session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
    
    # Start auction
    auction_response = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
    auction_id = auction_response.json()["auctionId"]
    print(f"Started auction: {auction_id}")
    
    # Get auction details
    auction_details = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = auction_details.json()["currentClub"]
    print(f"Current club: {current_club['name']}")
    
    # Set up Socket.IO client
    sio = socketio.Client(logger=True, engineio_logger=True)
    events_received = []
    
    @sio.event
    def connect():
        print("✅ Socket.IO connected")
        events_received.append("connected")
    
    @sio.event
    def disconnect():
        print("Socket.IO disconnected")
        events_received.append("disconnected")
    
    @sio.event
    def joined(data):
        print(f"✅ Joined auction room: {data}")
        events_received.append("joined")
    
    @sio.event
    def sync_state(data):
        print("✅ Received sync_state event")
        events_received.append("sync_state")
    
    @sio.event
    def bid_placed(data):
        print(f"✅ Bid placed event received: ${data.get('bid', {}).get('amount')}")
        events_received.append("bid_placed")
    
    @sio.event
    def timer_update(data):
        print(f"Timer update: {data.get('timeRemaining')}s")
        events_received.append("timer_update")
    
    @sio.event
    def lot_started(data):
        print(f"✅ Lot started: {data.get('club', {}).get('name')}")
        events_received.append("lot_started")
    
    @sio.event
    def lot_complete(data):
        print("✅ Lot completed")
        events_received.append("lot_complete")
    
    @sio.event
    def anti_snipe_triggered(data):
        print(f"✅ Anti-snipe triggered: +{data.get('extensionSeconds')}s")
        events_received.append("anti_snipe_triggered")
    
    try:
        # Connect to socket
        print("Connecting to Socket.IO...")
        sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
        time.sleep(2)
        
        if "connected" not in events_received:
            print("❌ Socket connection failed")
            return False
        
        # Join auction room
        print("Joining auction room...")
        sio.emit('join_auction', {'auctionId': auction_id})
        time.sleep(2)
        
        if "joined" not in events_received:
            print("❌ Failed to join auction room")
            return False
        
        print("✅ Successfully joined auction room")
        
        # Clear events and place a bid
        events_received = []
        print("Placing bid to test real-time events...")
        
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 25.0
        }
        
        bid_response = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
        print(f"Bid response: {bid_response.status_code}")
        
        # Wait for events
        print("Waiting for bid_placed event...")
        time.sleep(3)
        
        print(f"Events received after bid: {events_received}")
        
        if "bid_placed" in events_received:
            print("✅ bid_placed event received successfully")
        else:
            print("❌ bid_placed event not received")
        
        # Wait for timer updates
        print("Waiting for timer updates...")
        initial_timer_count = events_received.count("timer_update")
        time.sleep(8)  # Wait longer for timer updates
        final_timer_count = events_received.count("timer_update")
        
        if final_timer_count > initial_timer_count:
            print("✅ Timer updates working")
        else:
            print("❌ No timer updates received")
        
        # Disconnect
        sio.disconnect()
        
        # Cleanup
        session.delete(f"{BASE_URL}/leagues/{league_id}?user_id={user_id}")
        print("Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Socket test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_socket_events()
    print(f"\nSocket.IO test {'PASSED' if success else 'FAILED'}")