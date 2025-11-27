#!/usr/bin/env python3
"""
Debug Budget Reserve Test
"""

import requests
import json
import time

BASE_URL = "https://leaguepilot.preview.emergentagent.com/api"

def test_budget_reserve():
    session = requests.Session()
    
    # Create commissioner
    user_data = {"name": "Commissioner Alice", "email": "alice.debug@test.com"}
    result = session.post(f"{BASE_URL}/users", json=user_data)
    print(f"Create user: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    commissioner_id = result.json()["id"]
    print(f"Commissioner ID: {commissioner_id}")
    
    # Create league with 3 slots and £300m budget
    league_data = {
        "name": "Debug Budget Test League",
        "commissionerId": commissioner_id,
        "budget": 300000000.0,  # £300m
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3
    }
    
    result = session.post(f"{BASE_URL}/leagues", json=league_data)
    print(f"Create league: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    league_id = result.json()["id"]
    invite_token = result.json()["inviteToken"]
    print(f"League ID: {league_id}")
    
    # Join league
    join_data = {"userId": commissioner_id, "inviteToken": invite_token}
    result = session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
    print(f"Join league: {result.status_code}")
    
    # Start auction
    result = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
    print(f"Start auction: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    auction_id = result.json()["auctionId"]
    print(f"Auction ID: {auction_id}")
    
    # Begin auction
    result = session.post(f"{BASE_URL}/auction/{auction_id}/begin?commissionerId={commissioner_id}")
    print(f"Begin auction: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    # Get current club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    print(f"Get auction: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    current_club = result.json().get("currentClub")
    print(f"Current club: {current_club.get('name') if current_club else 'None'}")
    
    # Bid £100m on first team
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 100000000.0  # £100m
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"First bid (£100m): {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    # Complete lot
    result = session.post(f"{BASE_URL}/auction/{auction_id}/complete-lot")
    print(f"Complete first lot: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    print("First lot completed successfully")
    
    # Wait for next lot
    time.sleep(3)
    
    # Get updated auction state
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    print(f"Get auction after first lot: {result.status_code}")
    if result.status_code != 200:
        print(f"Error: {result.text}")
        return False
    
    current_club = result.json().get("currentClub")
    print(f"Second club: {current_club.get('name') if current_club else 'None'}")
    
    # Test: Try to bid £150m (should be rejected - must reserve £1m for last slot)
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 150000000.0  # £150m - should be rejected
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"Second bid (£150m - should be rejected): {result.status_code}")
    
    if result.status_code == 400:
        error_detail = result.json().get("detail", "")
        print(f"✅ Correctly rejected: {error_detail}")
        if "reserve" in error_detail.lower():
            print("✅ Error message mentions reserve")
        else:
            print("❌ Error message doesn't mention reserve")
    else:
        print(f"❌ Should have been rejected but got: {result.text}")
        return False
    
    # Test: Bid £149m (should be accepted)
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 149000000.0  # £149m - should be accepted
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"Third bid (£149m - should be accepted): {result.status_code}")
    
    if result.status_code == 200:
        print("✅ £149m bid accepted")
    else:
        print(f"❌ Should have been accepted but got: {result.text}")
        return False
    
    print("✅ Budget reserve enforcement working correctly!")
    return True

if __name__ == "__main__":
    success = test_budget_reserve()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")