#!/usr/bin/env python3
"""
Test Roster Visibility Only
"""

import requests
import json
import time

BASE_URL = "https://leaguepilot.preview.emergentagent.com/api"

def test_roster_visibility():
    session = requests.Session()
    
    try:
        # Create users
        user1_data = {"name": "Commissioner Alice", "email": "alice.roster@test.com"}
        result = session.post(f"{BASE_URL}/users", json=user1_data)
        print(f"Create user 1: {result.status_code}")
        user1_id = result.json()["id"]
        
        user2_data = {"name": "Manager Bob", "email": "bob.roster@test.com"}
        result = session.post(f"{BASE_URL}/users", json=user2_data)
        print(f"Create user 2: {result.status_code}")
        user2_id = result.json()["id"]
        
        # Create league
        league_data = {
            "name": "Roster Visibility Test League",
            "commissionerId": user1_id,
            "budget": 500000000.0,  # £500m
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 2
        }
        
        result = session.post(f"{BASE_URL}/leagues", json=league_data)
        print(f"Create league: {result.status_code}")
        league_id = result.json()["id"]
        invite_token = result.json()["inviteToken"]
        
        # Both users join league
        for user_id in [user1_id, user2_id]:
            join_data = {"userId": user_id, "inviteToken": invite_token}
            result = session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
            print(f"User {user_id[:8]} join: {result.status_code}")
        
        # Test the summary endpoint before auction
        print("\n=== Testing Summary Endpoint (Pre-Auction) ===")
        result = session.get(f"{BASE_URL}/leagues/{league_id}/summary?userId={user1_id}")
        print(f"Get summary: {result.status_code}")
        
        if result.status_code == 200:
            summary = result.json()
            print(f"League name: {summary.get('name')}")
            print(f"Your roster: {summary.get('yourRoster', [])}")
            print(f"Managers count: {len(summary.get('managers', []))}")
            
            managers = summary.get('managers', [])
            for manager in managers:
                print(f"Manager: {manager.get('name')} - Roster: {len(manager.get('roster', []))} teams")
            
            print("✅ Roster visibility endpoint working (pre-auction)")
            return True
        else:
            print(f"❌ Summary endpoint failed: {result.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_roster_visibility()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")