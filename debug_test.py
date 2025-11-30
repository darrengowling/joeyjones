#!/usr/bin/env python3
"""
Debug test to identify specific issues
"""

import requests
import json

BASE_URL = "https://competition-hub-6.preview.emergentagent.com/api"

def test_endpoint(method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> dict:
    """Test API endpoint with detailed debugging"""
    url = f"{BASE_URL}{endpoint}"
    session = requests.Session()
    
    try:
        if method.upper() == "GET":
            response = session.get(url, params=data)
        elif method.upper() == "POST":
            response = session.post(url, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
            
        print(f"{method} {endpoint} -> {response.status_code}")
        
        if response.status_code != expected_status:
            try:
                error_detail = response.json()
                print(f"Error response: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return {"error": f"Status {response.status_code}", "detail": response.text}
            
        try:
            result = response.json()
            return result
        except:
            return {"success": True, "status_code": response.status_code}
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return {"error": str(e)}

def debug_auction_system():
    """Debug auction system issues"""
    print("=== DEBUGGING AUCTION SYSTEM ===")
    
    # Create user
    user_data = {"name": "Debug User", "email": "debug@test.com"}
    result = test_endpoint("POST", "/users", user_data)
    if "error" in result:
        print(f"User creation failed: {result}")
        return
    user_id = result.get("id")
    print(f"Created user: {user_id}")
    
    # Create league
    league_data = {
        "name": "Debug League",
        "commissionerId": user_id,
        "budget": 500000000.0,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 5,
        "sportKey": "football"
    }
    
    result = test_endpoint("POST", "/leagues", league_data)
    if "error" in result:
        print(f"League creation failed: {result}")
        return
    league_id = result.get("id")
    invite_token = result.get("inviteToken")
    print(f"Created league: {league_id}")
    
    # Join league
    join_data = {"userId": user_id, "inviteToken": invite_token}
    result = test_endpoint("POST", f"/leagues/{league_id}/join", join_data)
    if "error" in result:
        print(f"League join failed: {result}")
        return
    print("Joined league successfully")
    
    # Start auction
    result = test_endpoint("POST", f"/leagues/{league_id}/auction/start")
    if "error" in result:
        print(f"Auction start failed: {result}")
        return
    auction_id = result.get("auctionId")
    print(f"Started auction: {auction_id}")
    
    # Get auction details
    result = test_endpoint("GET", f"/auction/{auction_id}")
    if "error" in result:
        print(f"Auction retrieval failed: {result}")
        return
    
    auction = result.get("auction", {})
    current_club = result.get("currentClub")
    print(f"Current club: {current_club.get('name') if current_club else 'None'}")
    
    if not current_club:
        print("No current club - auction may not be active")
        return
    
    # Test minimum budget enforcement
    print("\n--- Testing minimum budget enforcement ---")
    
    # Test low bid (should fail)
    low_bid_data = {
        "userId": user_id,
        "clubId": current_club.get("id"),
        "amount": 500000.0  # £500K - below minimum
    }
    
    result = test_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
    print(f"Low bid result: {result}")
    
    # Test valid bid (should succeed)
    valid_bid_data = {
        "userId": user_id,
        "clubId": current_club.get("id"),
        "amount": 2000000.0  # £2M - above minimum
    }
    
    result = test_endpoint("POST", f"/auction/{auction_id}/bid", valid_bid_data)
    print(f"Valid bid result: {result}")

def debug_error_handling():
    """Debug error handling issues"""
    print("\n=== DEBUGGING ERROR HANDLING ===")
    
    # Test 404 error
    result = test_endpoint("GET", "/users/nonexistent-id", expected_status=404)
    print(f"404 test result: {result}")
    
    # Test invalid endpoint
    result = test_endpoint("GET", "/nonexistent", expected_status=404)
    print(f"Invalid endpoint result: {result}")

if __name__ == "__main__":
    debug_auction_system()
    debug_error_handling()