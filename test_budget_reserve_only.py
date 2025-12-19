#!/usr/bin/env python3
"""
Test Budget Reserve Only
"""

import requests
import json
import time

BASE_URL = "https://fix-roster-sync.preview.emergentagent.com/api"

def test_budget_reserve():
    session = requests.Session()
    
    try:
        # Create commissioner
        user_data = {"name": "Commissioner Alice", "email": "alice.budget@test.com"}
        result = session.post(f"{BASE_URL}/users", json=user_data)
        print(f"Create user: {result.status_code}")
        commissioner_id = result.json()["id"]
        
        # Create league with £150m budget
        league_data = {
            "name": "Budget Reserve Test League",
            "commissionerId": commissioner_id,
            "budget": 150000000.0,  # £150m
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3
        }
        
        result = session.post(f"{BASE_URL}/leagues", json=league_data)
        print(f"Create league: {result.status_code}")
        league_id = result.json()["id"]
        invite_token = result.json()["inviteToken"]
        
        # Join league
        join_data = {"userId": commissioner_id, "inviteToken": invite_token}
        result = session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
        print(f"Join league: {result.status_code}")
        
        # Start and begin auction
        result = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
        print(f"Start auction: {result.status_code}")
        auction_id = result.json()["auctionId"]
        
        result = session.post(f"{BASE_URL}/auction/{auction_id}/begin?commissionerId={commissioner_id}")
        print(f"Begin auction: {result.status_code}")
        
        # Get current club
        result = session.get(f"{BASE_URL}/auction/{auction_id}")
        print(f"Get auction: {result.status_code}")
        current_club = result.json().get("currentClub")
        print(f"Current club: {current_club.get('name') if current_club else 'None'}")
        
        # Bid £100m on first team
        bid_data = {
            "userId": commissioner_id,
            "clubId": current_club["id"],
            "amount": 100000000.0  # £100m
        }
        
        result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
        print(f"First bid: {result.status_code}")
        
        # Complete lot
        print("About to complete lot...")
        result = session.post(f"{BASE_URL}/auction/{auction_id}/complete-lot")
        print(f"Complete lot: {result.status_code}")
        
        if result.status_code != 200:
            print(f"Complete lot error: {result.text}")
            return False
        
        print("Lot completed successfully")
        
        # Wait for next lot
        print("Waiting for next lot...")
        time.sleep(3)
        
        # Get updated auction state
        print("Getting updated auction state...")
        result = session.get(f"{BASE_URL}/auction/{auction_id}")
        print(f"Get auction after first lot: {result.status_code}")
        
        if result.status_code != 200:
            print(f"Get auction error: {result.text}")
            return False
        
        current_club = result.json().get("currentClub")
        print(f"Second club: {current_club.get('name') if current_club else 'None'}")
        
        # Test £50m bid (should be rejected)
        bid_data = {
            "userId": commissioner_id,
            "clubId": current_club["id"],
            "amount": 50000000.0  # £50m - should be rejected
        }
        
        result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
        print(f"£50m bid: {result.status_code}")
        
        if result.status_code == 400:
            print(f"✅ Correctly rejected: {result.json().get('detail')}")
            return True
        else:
            print(f"❌ Should have been rejected: {result.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Test crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_budget_reserve()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")