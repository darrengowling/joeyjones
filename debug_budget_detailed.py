#!/usr/bin/env python3
"""
Debug Budget Reserve Test - Detailed
"""

import requests
import json
import time

BASE_URL = "https://draft-kings-mobile.preview.emergentagent.com/api"

def test_budget_reserve_detailed():
    session = requests.Session()
    
    # Create commissioner
    user_data = {"name": "Commissioner Alice", "email": "alice.debug2@test.com"}
    result = session.post(f"{BASE_URL}/users", json=user_data)
    commissioner_id = result.json()["id"]
    print(f"Commissioner ID: {commissioner_id}")
    
    # Create league with 3 slots and £300m budget
    league_data = {
        "name": "Debug Budget Test League 2",
        "commissionerId": commissioner_id,
        "budget": 300000000.0,  # £300m
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3
    }
    
    result = session.post(f"{BASE_URL}/leagues", json=league_data)
    league_id = result.json()["id"]
    invite_token = result.json()["inviteToken"]
    
    # Join league
    join_data = {"userId": commissioner_id, "inviteToken": invite_token}
    session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
    
    # Check participant budget before auction
    result = session.get(f"{BASE_URL}/leagues/{league_id}/participants")
    participants = result.json()
    commissioner_participant = next(p for p in participants if p["userId"] == commissioner_id)
    print(f"Initial budget: £{commissioner_participant['budgetRemaining']:,.0f}")
    print(f"Initial clubs won: {len(commissioner_participant.get('clubsWon', []))}")
    
    # Start and begin auction
    result = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
    auction_id = result.json()["auctionId"]
    
    session.post(f"{BASE_URL}/auction/{auction_id}/begin?commissionerId={commissioner_id}")
    
    # Get current club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"First club: {current_club.get('name')}")
    
    # Bid £100m on first team
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 100000000.0  # £100m
    }
    
    session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    session.post(f"{BASE_URL}/auction/{auction_id}/complete-lot")
    
    # Check participant budget after first win
    result = session.get(f"{BASE_URL}/leagues/{league_id}/participants")
    participants = result.json()
    commissioner_participant = next(p for p in participants if p["userId"] == commissioner_id)
    print(f"After first win - Budget: £{commissioner_participant['budgetRemaining']:,.0f}")
    print(f"After first win - Clubs won: {len(commissioner_participant.get('clubsWon', []))}")
    
    # Calculate expected values
    clubs_won = len(commissioner_participant.get('clubsWon', []))
    slots_remaining = 3 - clubs_won  # 3 total slots
    print(f"Clubs won: {clubs_won}, Slots remaining: {slots_remaining}")
    
    if slots_remaining > 1:
        reserve_needed = (slots_remaining - 1) * 1_000_000
        max_allowed_bid = commissioner_participant['budgetRemaining'] - reserve_needed
        print(f"Reserve needed: £{reserve_needed:,.0f}")
        print(f"Max allowed bid: £{max_allowed_bid:,.0f}")
    
    # Wait for next lot
    time.sleep(3)
    
    # Get second club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"Second club: {current_club.get('name')}")
    
    # Test: Try to bid £150m
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 150000000.0  # £150m
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"£150m bid result: {result.status_code}")
    
    if result.status_code == 400:
        print(f"✅ Correctly rejected: {result.json().get('detail')}")
    else:
        print(f"❌ Should have been rejected: {result.json()}")
    
    return result.status_code == 400

if __name__ == "__main__":
    success = test_budget_reserve_detailed()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")