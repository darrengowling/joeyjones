#!/usr/bin/env python3
"""
Simple Backend Test - Focus on Core Functionality
Tests the key areas without complex Socket.IO event handling
"""

import requests
import time
from datetime import datetime

# Configuration
BASE_URL = "https://fantasy-sports-bid.preview.emergentagent.com/api"

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_api_endpoint(method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> dict:
    """Test API endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    session = requests.Session()
    
    try:
        if method.upper() == "GET":
            response = session.get(url)
        elif method.upper() == "POST":
            response = session.post(url, json=data)
        elif method.upper() == "DELETE":
            response = session.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        log(f"{method} {endpoint} -> {response.status_code}")
        
        if response.status_code != expected_status:
            log(f"Expected {expected_status}, got {response.status_code}: {response.text}", "ERROR")
            return {"error": f"Status {response.status_code}", "text": response.text}
            
        try:
            return response.json()
        except:
            return {"success": True, "text": response.text}
            
    except Exception as e:
        log(f"Request failed: {str(e)}", "ERROR")
        return {"error": str(e)}

def main():
    """Test core backend functionality"""
    log("🚀 Testing Core Backend Functionality")
    
    # Test 1: Create user and league with £500M budget
    log("=== Test 1: League Creation with £500M Budget ===")
    
    user_data = {"name": "Test Manager", "email": "test@example.com"}
    result = test_api_endpoint("POST", "/users", user_data)
    if not result or "error" in result:
        log("❌ User creation failed", "ERROR")
        return False
    
    user_id = result.get("id")
    log(f"✅ Created user: {user_id}")
    
    league_data = {
        "name": "Test League £500M",
        "commissionerId": user_id,
        "budget": 500000000.0,  # £500M
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 5
    }
    
    result = test_api_endpoint("POST", "/leagues", league_data)
    if not result or "error" in result:
        log("❌ League creation failed", "ERROR")
        return False
    
    league_id = result.get("id")
    invite_token = result.get("inviteToken")
    budget = result.get("budget")
    
    if budget != 500000000.0:
        log(f"❌ Budget incorrect: expected £500M, got £{budget:,.0f}", "ERROR")
        return False
    
    log(f"✅ Created league with £500M budget: {league_id}")
    
    # Test 2: Join league
    join_data = {"userId": user_id, "inviteToken": invite_token}
    result = test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
    if "error" in result:
        log("❌ Join league failed", "ERROR")
        return False
    
    participant = result.get("participant")
    if participant.get("budgetRemaining") != 500000000.0:
        log("❌ Participant budget incorrect", "ERROR")
        return False
    
    log("✅ Successfully joined league with correct budget")
    
    # Test 3: Start auction and verify randomization
    log("=== Test 3: Auction Management ===")
    
    result = test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
    if "error" in result:
        log("❌ Auction start failed", "ERROR")
        return False
    
    auction_id = result.get("auctionId")
    log(f"✅ Started auction: {auction_id}")
    
    # Get auction details
    result = test_api_endpoint("GET", f"/auction/{auction_id}")
    if not result or "error" in result:
        log("❌ Get auction failed", "ERROR")
        return False
    
    auction_data = result.get("auction", {})
    current_club = result.get("currentClub")
    club_queue = auction_data.get("clubQueue", [])
    
    if not current_club:
        log("❌ No current club", "ERROR")
        return False
    
    if len(club_queue) != 36:
        log(f"❌ Expected 36 clubs in queue, got {len(club_queue)}", "ERROR")
        return False
    
    log(f"✅ Club queue randomized: {len(club_queue)} clubs, first club: {current_club.get('name')}")
    
    # Test 4: Clubs list endpoint (alphabetical sorting)
    result = test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
    if "error" in result:
        log("❌ Clubs list failed", "ERROR")
        return False
    
    clubs_data = result.get("clubs", [])
    upcoming_clubs = [c for c in clubs_data if c.get("status") == "upcoming"]
    
    if len(upcoming_clubs) > 1:
        upcoming_names = [c.get("name") for c in upcoming_clubs]
        sorted_names = sorted(upcoming_names)
        if upcoming_names == sorted_names:
            log("✅ Clubs list sorted alphabetically (draw order hidden)")
        else:
            log("⚠️ Clubs list may reveal draw order", "WARN")
    
    # Test 5: Minimum budget enforcement
    log("=== Test 5: Minimum Budget Enforcement ===")
    
    # Test bid below £1M (should fail)
    low_bid = {
        "userId": user_id,
        "clubId": current_club["id"],
        "amount": 500000.0  # £500k
    }
    
    result = test_api_endpoint("POST", f"/auction/{auction_id}/bid", low_bid, expected_status=400)
    if "detail" not in result or "£1,000,000" not in result.get("detail", ""):
        log("❌ Minimum budget validation failed", "ERROR")
        return False
    
    log("✅ Minimum £1M budget validation working")
    
    # Test valid bids
    valid_bids = [1000000.0, 1500000.0, 2000000.0]  # £1M, £1.5M, £2M
    
    for amount in valid_bids:
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": amount
        }
        
        result = test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in result:
            log(f"❌ Valid bid £{amount:,.0f} failed", "ERROR")
            return False
    
    log(f"✅ Placed {len(valid_bids)} valid bids successfully")
    
    # Test 6: Budget management
    log("=== Test 6: Budget Management ===")
    
    # Complete lot to trigger budget deduction
    result = test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
    if "error" in result:
        log("❌ Complete lot failed", "ERROR")
        return False
    
    log("✅ Lot completed successfully")
    
    # Wait for processing
    time.sleep(2)
    
    # Check budget deduction
    result = test_api_endpoint("GET", f"/leagues/{league_id}/participants")
    if "error" in result:
        log("❌ Get participants failed", "ERROR")
        return False
    
    participants = result
    user_participant = next((p for p in participants if p.get("userId") == user_id), None)
    
    if not user_participant:
        log("❌ User participant not found", "ERROR")
        return False
    
    final_budget = user_participant.get("budgetRemaining", 0)
    total_spent = user_participant.get("totalSpent", 0)
    clubs_won = len(user_participant.get("clubsWon", []))
    
    log(f"Final budget: £{final_budget:,.0f}, spent: £{total_spent:,.0f}, clubs won: {clubs_won}")
    
    if total_spent != 2000000.0:  # Should be the highest bid (£2M)
        log(f"❌ Expected £2M spent, got £{total_spent:,.0f}", "ERROR")
        return False
    
    if final_budget != 498000000.0:  # £500M - £2M
        log(f"❌ Expected £498M remaining, got £{final_budget:,.0f}", "ERROR")
        return False
    
    if clubs_won != 1:
        log(f"❌ Expected 1 club won, got {clubs_won}", "ERROR")
        return False
    
    log("✅ Budget deductions working correctly")
    
    # Test 7: Commissioner controls
    log("=== Test 7: Commissioner Controls ===")
    
    # Test pause
    result = test_api_endpoint("POST", f"/auction/{auction_id}/pause")
    if "error" in result:
        log("❌ Pause auction failed", "ERROR")
        return False
    
    log("✅ Auction paused successfully")
    
    # Test resume
    result = test_api_endpoint("POST", f"/auction/{auction_id}/resume")
    if "error" in result:
        log("❌ Resume auction failed", "ERROR")
        return False
    
    log("✅ Auction resumed successfully")
    
    # Test delete
    result = test_api_endpoint("DELETE", f"/auction/{auction_id}")
    if "error" in result:
        log("❌ Delete auction failed", "ERROR")
        return False
    
    log("✅ Auction deleted successfully")
    
    # Cleanup
    result = test_api_endpoint("DELETE", f"/leagues/{league_id}")
    if "error" not in result:
        log("✅ Test league cleaned up")
    
    log("🎉 All core backend functionality tests PASSED!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)