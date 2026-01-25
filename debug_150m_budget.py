#!/usr/bin/env python3
"""
Debug with £150m budget
"""

import requests
import json
import time

BASE_URL = "https://fantasy-sports-uk.preview.emergentagent.com/api"

def test_150m_budget():
    session = requests.Session()
    
    # Create commissioner
    user_data = {"name": "Commissioner Alice", "email": "alice.debug4@test.com"}
    result = session.post(f"{BASE_URL}/users", json=user_data)
    commissioner_id = result.json()["id"]
    
    # Create league with £150m budget (not £300m)
    league_data = {
        "name": "Debug 150m Budget League",
        "commissionerId": commissioner_id,
        "budget": 150000000.0,  # £150m
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
    
    # Start and begin auction
    result = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
    auction_id = result.json()["auctionId"]
    
    session.post(f"{BASE_URL}/auction/{auction_id}/begin?commissionerId={commissioner_id}")
    
    # Get first club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"First club: {current_club.get('name')}")
    
    # Bid £100m on first team (this would leave £50m)
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 100000000.0  # £100m
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"First bid (£100m): {result.status_code}")
    
    session.post(f"{BASE_URL}/auction/{auction_id}/complete-lot")
    
    # Check state after first win
    result = session.get(f"{BASE_URL}/leagues/{league_id}/participants")
    participants = result.json()
    participant = next(p for p in participants if p["userId"] == commissioner_id)
    
    print(f"After first win - Budget: £{participant['budgetRemaining']:,.0f}")
    print(f"After first win - Clubs won: {len(participant.get('clubsWon', []))}")
    
    # Calculate reserve
    clubs_won_count = len(participant.get("clubsWon", []))
    slots_remaining = 3 - clubs_won_count  # 2 remaining
    reserve_needed = (slots_remaining - 1) * 1_000_000  # £1m
    max_allowed_bid = participant['budgetRemaining'] - reserve_needed
    
    print(f"Reserve needed: £{reserve_needed:,.0f}")
    print(f"Max allowed bid: £{max_allowed_bid:,.0f}")
    
    # With £50m remaining and £1m reserve, max bid would be £49m
    # So a £50m bid should be rejected
    
    # Wait for next lot
    time.sleep(3)
    
    # Get second club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"Second club: {current_club.get('name')}")
    
    # Test £50m bid (should be rejected)
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 50000000.0  # £50m
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"£50m bid result: {result.status_code}")
    
    if result.status_code == 400:
        print(f"✅ Correctly rejected: {result.json().get('detail')}")
        return True
    else:
        print(f"❌ Should have been rejected: {result.json()}")
        return False

if __name__ == "__main__":
    success = test_150m_budget()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")