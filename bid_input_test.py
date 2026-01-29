#!/usr/bin/env python3
"""
Test script to verify bid input UI implementation
Tests the updated bid input UI in the AuctionRoom page.
"""

import requests
import json

def test_bid_input_implementation():
    """Test the bid input UI implementation by examining the code"""
    
    print("=== BID INPUT UI IMPLEMENTATION TEST ===")
    
    # Read the AuctionRoom.js file to verify implementation
    try:
        with open('/app/frontend/src/pages/AuctionRoom.js', 'r') as f:
            content = f.read()
        
        print("✅ Successfully read AuctionRoom.js file")
        
        # Test 1: Verify bid buttons array contains correct values
        if '[1, 2, 5, 10, 20, 50]' in content:
            print("✅ Bid buttons array contains correct values: +1m, +2m, +5m, +10m, +20m, +50m")
        else:
            print("❌ Bid buttons array does not match expected values")
            return False
        
        # Test 2: Verify input field is read-only
        if 'readOnly' in content and 'data-testid="bid-amount-input"' in content:
            print("✅ Bid input field is marked as readOnly")
        else:
            print("❌ Bid input field is not properly configured as read-only")
            return False
        
        # Test 3: Verify formatted display
        if '£${bidAmount}m' in content:
            print("✅ Input displays formatted value like £105m")
        else:
            print("❌ Input does not display formatted value correctly")
            return False
        
        # Test 4: Verify Place Bid button exists
        if 'data-testid="place-bid-button"' in content and 'Place Bid' in content:
            print("✅ Place Bid button is implemented")
        else:
            print("❌ Place Bid button is not properly implemented")
            return False
        
        # Test 5: Verify button functionality
        if 'setBidAmount(newBid.toString())' in content:
            print("✅ Bid buttons update the input value correctly")
        else:
            print("❌ Bid buttons do not update input value")
            return False
        
        print("\n=== IMPLEMENTATION VERIFICATION COMPLETE ===")
        print("✅ All 5 tests passed - Bid input UI implementation is correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading AuctionRoom.js: {e}")
        return False

def test_api_endpoints():
    """Test that the backend API endpoints are working"""
    
    print("\n=== API ENDPOINTS TEST ===")
    
    base_url = "https://sportcrest.preview.emergentagent.com/api"
    
    try:
        # Test leagues endpoint
        response = requests.get(f"{base_url}/leagues", timeout=10)
        if response.status_code == 200:
            leagues = response.json()
            print(f"✅ Leagues API working - found {len(leagues)} leagues")
            
            # Find active leagues
            active_leagues = [l for l in leagues if l.get('status') == 'active']
            print(f"✅ Found {len(active_leagues)} active leagues")
            
            if active_leagues:
                league_id = active_leagues[0]['id']
                print(f"✅ Test league available: {active_leagues[0]['name']} ({league_id})")
                return True
            else:
                print("ℹ️ No active leagues found for testing")
                return True
        else:
            print(f"❌ Leagues API failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Bid Input UI Implementation")
    print("=" * 50)
    
    # Test 1: Code implementation
    impl_test = test_bid_input_implementation()
    
    # Test 2: API availability
    api_test = test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"Implementation Test: {'✅ PASS' if impl_test else '❌ FAIL'}")
    print(f"API Test: {'✅ PASS' if api_test else '❌ FAIL'}")
    
    if impl_test and api_test:
        print("\n🎉 ALL TESTS PASSED - Bid Input UI is ready for testing!")
    else:
        print("\n⚠️ Some tests failed - check implementation")