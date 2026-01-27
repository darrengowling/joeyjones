#!/usr/bin/env python3
"""
Debug Participant State
"""

import requests
import json
import time

BASE_URL = "https://uxoverhaul-1.preview.emergentagent.com/api"

def check_participant_state(session, league_id, user_id, step_name):
    result = session.get(f"{BASE_URL}/leagues/{league_id}/participants")
    participants = result.json()
    participant = next(p for p in participants if p["userId"] == user_id)
    
    print(f"\n=== {step_name} ===")
    print(f"Budget remaining: £{participant['budgetRemaining']:,.0f}")
    print(f"Clubs won: {participant.get('clubsWon', [])}")
    print(f"Clubs won count: {len(participant.get('clubsWon', []))}")
    print(f"Total spent: £{participant.get('totalSpent', 0):,.0f}")
    
    return participant

def test_participant_state():
    session = requests.Session()
    
    # Create commissioner
    user_data = {"name": "Commissioner Alice", "email": "alice.debug3@test.com"}
    result = session.post(f"{BASE_URL}/users", json=user_data)
    commissioner_id = result.json()["id"]
    
    # Create league
    league_data = {
        "name": "Debug Participant State League",
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
    
    # Check initial state
    participant = check_participant_state(session, league_id, commissioner_id, "Initial State")
    
    # Start and begin auction
    result = session.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
    auction_id = result.json()["auctionId"]
    
    session.post(f"{BASE_URL}/auction/{auction_id}/begin?commissionerId={commissioner_id}")
    
    # Get first club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"\nFirst club: {current_club.get('name')}")
    
    # Bid £100m on first team
    bid_data = {
        "userId": commissioner_id,
        "clubId": current_club["id"],
        "amount": 100000000.0  # £100m
    }
    
    result = session.post(f"{BASE_URL}/auction/{auction_id}/bid", json=bid_data)
    print(f"First bid result: {result.status_code}")
    
    # Check state after bid but before completion
    participant = check_participant_state(session, league_id, commissioner_id, "After First Bid")
    
    # Complete lot
    result = session.post(f"{BASE_URL}/auction/{auction_id}/complete-lot")
    print(f"Complete lot result: {result.status_code}")
    
    # Check state after completion
    participant = check_participant_state(session, league_id, commissioner_id, "After First Win")
    
    # Calculate expected reserve
    clubs_won_count = len(participant.get("clubsWon", []))
    max_slots = 3
    slots_remaining = max_slots - clubs_won_count
    
    print(f"\n=== Reserve Calculation ===")
    print(f"Clubs won count: {clubs_won_count}")
    print(f"Max slots: {max_slots}")
    print(f"Slots remaining: {slots_remaining}")
    
    if slots_remaining > 1:
        reserve_needed = (slots_remaining - 1) * 1_000_000
        max_allowed_bid = participant['budgetRemaining'] - reserve_needed
        print(f"Reserve needed: £{reserve_needed:,.0f}")
        print(f"Max allowed bid: £{max_allowed_bid:,.0f}")
        
        # Test the reserve enforcement
        print(f"\n=== Testing Reserve Enforcement ===")
        print(f"Testing bid of £150m (should be {'REJECTED' if 150000000 > max_allowed_bid else 'ACCEPTED'})")
    
    # Wait for next lot
    time.sleep(3)
    
    # Get second club
    result = session.get(f"{BASE_URL}/auction/{auction_id}")
    current_club = result.json().get("currentClub")
    print(f"\nSecond club: {current_club.get('name')}")
    
    # Test £150m bid
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
        print(f"❌ Should have been rejected but was accepted")
        print(f"Response: {result.json()}")

if __name__ == "__main__":
    test_participant_state()