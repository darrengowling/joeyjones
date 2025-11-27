#!/usr/bin/env python3
"""
Debug Socket.IO Connection and Room Joining
"""

import asyncio
import json
import requests
import socketio
import time
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://leaguepilot.preview.emergentagent.com/api"
SOCKET_URL = "https://leaguepilot.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {message}")

def test_api_endpoint(method: str, endpoint: str, data: dict = None) -> dict:
    """Test API endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        log(f"{method} {endpoint} -> {response.status_code}")
        
        try:
            return response.json()
        except:
            return {"success": True, "text": response.text}
            
    except Exception as e:
        log(f"Request failed: {str(e)}", "ERROR")
        return {"error": str(e)}

def main():
    log("🚀 Starting Socket.IO Debug Test")
    
    # Create test user and league
    user_data = {"name": "Debug User", "email": "debug@test.com"}
    user_result = test_api_endpoint("POST", "/users", user_data)
    if "error" in user_result:
        log("User creation failed", "ERROR")
        return False
    
    user_id = user_result.get("id")
    log(f"Created user: {user_id}")
    
    # Seed clubs
    test_api_endpoint("POST", "/clubs/seed")
    
    # Create league
    league_data = {
        "name": "Debug League",
        "commissionerId": user_id,
        "budget": 500000000.0,
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3
    }
    
    league_result = test_api_endpoint("POST", "/leagues", league_data)
    if "error" in league_result:
        log("League creation failed", "ERROR")
        return False
    
    league_id = league_result.get("id")
    invite_token = league_result.get("inviteToken")
    log(f"Created league: {league_id}")
    
    # Join league
    join_data = {"userId": user_id, "inviteToken": invite_token}
    test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
    
    # Setup Socket.IO client
    events_received = []
    
    client = socketio.Client(logger=True, engineio_logger=True)
    
    @client.event
    def connect():
        log("✅ Socket.IO connected successfully")
        events_received.append("connected")
    
    @client.event
    def disconnect():
        log("Socket.IO disconnected")
        events_received.append("disconnected")
    
    @client.event
    def room_joined(data):
        log(f"✅ Room joined confirmation: {data}")
        events_received.append("room_joined")
    
    @client.event
    def sync_members(data):
        log(f"✅ Sync members received: {len(data.get('members', []))} members")
        events_received.append("sync_members")
    
    @client.event
    def league_status_changed(data):
        log(f"🎯 LEAGUE STATUS CHANGED: {data}")
        events_received.append("league_status_changed")
    
    @client.event
    def connect_error(data):
        log(f"❌ Connection error: {data}", "ERROR")
    
    # Connect to Socket.IO
    try:
        log("Connecting to Socket.IO...")
        client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
        
        # Wait for connection
        time.sleep(3)
        
        if "connected" not in events_received:
            log("❌ Socket.IO connection failed", "ERROR")
            return False
        
        # Join league room
        log(f"Joining league room: {league_id}")
        client.emit('join_league', {
            'leagueId': league_id,
            'userId': user_id
        })
        
        # Wait for room join confirmation
        time.sleep(3)
        
        if "room_joined" not in events_received:
            log("❌ Room join confirmation not received", "ERROR")
            return False
        
        log("✅ Successfully joined league room")
        
        # Clear events and start auction
        events_received = []
        
        log("Starting auction to test event delivery...")
        auction_result = test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        
        if "error" in auction_result:
            log("❌ Auction start failed", "ERROR")
            return False
        
        auction_id = auction_result.get("auctionId")
        log(f"✅ Auction started: {auction_id}")
        
        # Wait for league_status_changed event
        log("Waiting for league_status_changed event...")
        time.sleep(5)
        
        if "league_status_changed" in events_received:
            log("🎉 SUCCESS: league_status_changed event received!")
            return True
        else:
            log("❌ FAILED: league_status_changed event NOT received", "ERROR")
            log(f"Events received: {events_received}")
            return False
        
    except Exception as e:
        log(f"❌ Socket.IO test failed: {str(e)}", "ERROR")
        return False
    
    finally:
        if client.connected:
            client.disconnect()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)