#!/usr/bin/env python3
"""
Simple production test to verify core functionality
"""

import requests
import json
import time

BASE_URL = "https://sporty-ui.preview.emergentagent.com/api"

def test_endpoint(method: str, endpoint: str, data: dict = None) -> dict:
    """Test API endpoint"""
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
        
        try:
            return response.json()
        except:
            return {"success": True, "status_code": response.status_code}
            
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🚀 SIMPLE PRODUCTION READINESS TEST")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Multi-sport architecture
    print("\n1. Testing Multi-Sport Architecture...")
    result = test_endpoint("GET", "/sports")
    if isinstance(result, list) and len(result) >= 2:
        sport_keys = [sport.get("key") for sport in result]
        if "football" in sport_keys and "cricket" in sport_keys:
            print("✅ Multi-sport architecture working")
            results["multi_sport"] = True
        else:
            print(f"❌ Missing sports. Found: {sport_keys}")
            results["multi_sport"] = False
    else:
        print(f"❌ Sports endpoint failed: {result}")
        results["multi_sport"] = False
    
    # Test 2: Asset management
    print("\n2. Testing Asset Management...")
    football_result = test_endpoint("GET", "/assets", {"sportKey": "football"})
    cricket_result = test_endpoint("GET", "/assets", {"sportKey": "cricket"})
    
    if (football_result.get("assets") and len(football_result["assets"]) == 36 and
        cricket_result.get("assets") and len(cricket_result["assets"]) == 20):
        print("✅ Asset management working (36 football, 20 cricket)")
        results["assets"] = True
    else:
        football_count = len(football_result.get("assets", []))
        cricket_count = len(cricket_result.get("assets", []))
        print(f"❌ Asset counts wrong. Football: {football_count}, Cricket: {cricket_count}")
        results["assets"] = False
    
    # Test 3: User management
    print("\n3. Testing User Management...")
    user_data = {"name": "Test User", "email": "test@production.com"}
    result = test_endpoint("POST", "/users", user_data)
    if result.get("id"):
        print("✅ User management working")
        results["users"] = True
        user_id = result["id"]
    else:
        print(f"❌ User creation failed: {result}")
        results["users"] = False
        return results
    
    # Test 4: League management
    print("\n4. Testing League Management...")
    league_data = {
        "name": "Production Test League",
        "commissionerId": user_id,
        "budget": 500000000.0,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 5,
        "sportKey": "football"
    }
    result = test_endpoint("POST", "/leagues", league_data)
    if result.get("id"):
        print("✅ League management working")
        results["leagues"] = True
        league_id = result["id"]
        invite_token = result["inviteToken"]
    else:
        print(f"❌ League creation failed: {result}")
        results["leagues"] = False
        return results
    
    # Test 5: Auction system
    print("\n5. Testing Auction System...")
    result = test_endpoint("POST", f"/leagues/{league_id}/auction/start")
    if result.get("auctionId"):
        print("✅ Auction system working")
        results["auctions"] = True
        auction_id = result["auctionId"]
        
        # Test bidding
        result = test_endpoint("GET", f"/auction/{auction_id}")
        current_club = result.get("currentClub")
        if current_club:
            # Join league first
            join_data = {"userId": user_id, "inviteToken": invite_token}
            test_endpoint("POST", f"/leagues/{league_id}/join", join_data)
            
            # Test valid bid
            bid_data = {
                "userId": user_id,
                "clubId": current_club["id"],
                "amount": 2000000.0
            }
            bid_result = test_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if bid_result.get("message"):
                print("✅ Bidding system working")
                results["bidding"] = True
            else:
                print(f"❌ Bidding failed: {bid_result}")
                results["bidding"] = False
        else:
            print("❌ No current club in auction")
            results["bidding"] = False
    else:
        print(f"❌ Auction start failed: {result}")
        results["auctions"] = False
        results["bidding"] = False
    
    # Test 6: Cricket scoring
    print("\n6. Testing Cricket Scoring...")
    cricket_league_data = {
        "name": "Cricket Test League",
        "commissionerId": user_id,
        "budget": 300000000.0,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 11,
        "sportKey": "cricket"
    }
    result = test_endpoint("POST", "/leagues", cricket_league_data)
    if result.get("id"):
        cricket_league_id = result["id"]
        
        # Test CSV upload
        csv_data = "matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts\nmatch1,player1,75,2,1,0,1"
        files = {"file": ("test.csv", csv_data, "text/csv")}
        
        # Use requests directly for file upload
        url = f"{BASE_URL}/scoring/{cricket_league_id}/ingest"
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("✅ Cricket scoring working")
            results["cricket_scoring"] = True
        else:
            print(f"❌ Cricket scoring failed: {response.status_code}")
            results["cricket_scoring"] = False
    else:
        print(f"❌ Cricket league creation failed: {result}")
        results["cricket_scoring"] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PRODUCTION READINESS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    print(f"\nOverall Score: {percentage:.1f}% ({passed}/{total})")
    
    if percentage >= 85:
        print("🟢 PRODUCTION READY")
    elif percentage >= 70:
        print("🟡 MOSTLY READY")
    else:
        print("🔴 NEEDS WORK")
    
    return results

if __name__ == "__main__":
    main()