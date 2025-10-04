#!/usr/bin/env python3
"""
Multi-Sport Backend API Testing for Friends of Pifa
Tests the newly implemented multi-sport functionality including:
- Sports API endpoints
- Sport-aware league functionality  
- Data migration verification
- Cricket functionality enablement
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://fantasy-cricket-6.preview.emergentagent.com/api"

class MultiSportTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200, params: dict = None) -> dict:
        """Test API endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                self.log(f"Expected {expected_status}, got {response.status_code}: {response.text}", "ERROR")
                return {"error": f"Status {response.status_code}", "text": response.text, "detail": response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}

    def test_sports_api_endpoints(self) -> bool:
        """Test Sports API endpoints"""
        self.log("=== Testing Sports API Endpoints ===")
        
        # Test 1: GET /api/sports - Should return both Football and Cricket sports
        self.log("Testing GET /api/sports...")
        result = self.test_api_endpoint("GET", "/sports")
        if "error" in result:
            self.log("GET /api/sports failed", "ERROR")
            return False
        
        if not isinstance(result, list):
            self.log("Sports endpoint should return a list", "ERROR")
            return False
        
        # Verify we have both football and cricket
        sport_keys = [sport.get("key") for sport in result]
        if "football" not in sport_keys:
            self.log("Football sport not found in sports list", "ERROR")
            return False
        
        if "cricket" not in sport_keys:
            self.log("Cricket sport not found in sports list", "ERROR")
            return False
        
        self.log(f"✅ GET /api/sports returned {len(result)} sports: {sport_keys}")
        
        # Store sports data for later verification
        self.test_data["sports"] = result
        
        # Test 2: GET /api/sports/football - Should return Football sport details
        self.log("Testing GET /api/sports/football...")
        result = self.test_api_endpoint("GET", "/sports/football")
        if "error" in result:
            self.log("GET /api/sports/football failed", "ERROR")
            return False
        
        # Verify football sport configuration
        if result.get("key") != "football":
            self.log("Football sport key incorrect", "ERROR")
            return False
        
        if result.get("name") != "Football":
            self.log("Football sport name incorrect", "ERROR")
            return False
        
        if result.get("assetType") != "CLUB":
            self.log("Football assetType should be CLUB", "ERROR")
            return False
        
        # Verify uiHints
        ui_hints = result.get("uiHints", {})
        if ui_hints.get("assetLabel") != "Club" or ui_hints.get("assetPlural") != "Clubs":
            self.log("Football uiHints incorrect", "ERROR")
            return False
        
        # Verify auctionTemplate and scoringSchema exist
        if not result.get("auctionTemplate") or not result.get("scoringSchema"):
            self.log("Football missing auctionTemplate or scoringSchema", "ERROR")
            return False
        
        self.log("✅ GET /api/sports/football returned correct Football configuration")
        
        # Test 3: GET /api/sports/cricket - Should return Cricket sport details
        self.log("Testing GET /api/sports/cricket...")
        result = self.test_api_endpoint("GET", "/sports/cricket")
        if "error" in result:
            self.log("GET /api/sports/cricket failed", "ERROR")
            return False
        
        # Verify cricket sport configuration
        if result.get("key") != "cricket":
            self.log("Cricket sport key incorrect", "ERROR")
            return False
        
        if result.get("name") != "Cricket":
            self.log("Cricket sport name incorrect", "ERROR")
            return False
        
        if result.get("assetType") != "PLAYER":
            self.log("Cricket assetType should be PLAYER", "ERROR")
            return False
        
        # Verify uiHints
        ui_hints = result.get("uiHints", {})
        if ui_hints.get("assetLabel") != "Player" or ui_hints.get("assetPlural") != "Players":
            self.log("Cricket uiHints incorrect", "ERROR")
            return False
        
        # Verify auctionTemplate and scoringSchema exist
        if not result.get("auctionTemplate") or not result.get("scoringSchema"):
            self.log("Cricket missing auctionTemplate or scoringSchema", "ERROR")
            return False
        
        # Verify cricket-specific scoring schema
        scoring_schema = result.get("scoringSchema", {})
        if scoring_schema.get("type") != "perPlayerMatch":
            self.log("Cricket scoringSchema type should be perPlayerMatch", "ERROR")
            return False
        
        # Check for cricket-specific scoring rules
        rules = scoring_schema.get("rules", {})
        expected_rules = ["run", "wicket", "catch", "stumping", "runOut"]
        for rule in expected_rules:
            if rule not in rules:
                self.log(f"Cricket scoring rule '{rule}' missing", "ERROR")
                return False
        
        # Check for milestones
        milestones = scoring_schema.get("milestones", {})
        expected_milestones = ["halfCentury", "century", "fiveWicketHaul"]
        for milestone in expected_milestones:
            if milestone not in milestones:
                self.log(f"Cricket milestone '{milestone}' missing", "ERROR")
                return False
        
        self.log("✅ GET /api/sports/cricket returned correct Cricket configuration")
        
        self.log("✅ All Sports API endpoints working correctly")
        return True

    def test_sport_aware_league_functionality(self) -> bool:
        """Test Sport-Aware League Functionality"""
        self.log("=== Testing Sport-Aware League Functionality ===")
        
        # First create a test user for league operations
        user_data = {
            "name": "Multi Sport Manager",
            "email": "multisport.manager@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in result:
            self.log("Failed to create test user for league testing", "ERROR")
            return False
        
        user_id = result.get("id")
        self.test_data["user_id"] = user_id
        self.log(f"Created test user: {user_id}")
        
        # Test 4: GET /api/leagues - Should show existing leagues with sportKey:"football" (migration backfill working)
        self.log("Testing GET /api/leagues (checking migration backfill)...")
        result = self.test_api_endpoint("GET", "/leagues")
        if "error" in result:
            self.log("GET /api/leagues failed", "ERROR")
            return False
        
        if not isinstance(result, list):
            self.log("Leagues endpoint should return a list", "ERROR")
            return False
        
        # Check if existing leagues have been backfilled with sportKey (should have some sport key)
        existing_leagues_count = len(result)
        football_leagues_existing = 0
        other_sport_leagues_existing = 0
        
        if existing_leagues_count > 0:
            for league in result:
                sport_key = league.get("sportKey")
                if not sport_key:
                    self.log("Found league without sportKey - migration backfill failed", "ERROR")
                    return False
                if sport_key == "football":
                    football_leagues_existing += 1
                else:
                    other_sport_leagues_existing += 1
            self.log(f"✅ Migration backfill working: {existing_leagues_count} existing leagues have sportKey ({football_leagues_existing} football, {other_sport_leagues_existing} other sports)")
        else:
            self.log("No existing leagues found - will test with new leagues")
        
        # Test 5: GET /api/leagues?sportKey=football - Should filter leagues by football sport
        self.log("Testing GET /api/leagues?sportKey=football...")
        result = self.test_api_endpoint("GET", "/leagues", params={"sportKey": "football"})
        if "error" in result:
            self.log("GET /api/leagues?sportKey=football failed", "ERROR")
            return False
        
        football_leagues_count = len(result)
        if existing_leagues_count > 0 and football_leagues_count != football_leagues_existing:
            self.log(f"Football filter returned {football_leagues_count} leagues, expected {football_leagues_existing}", "ERROR")
            return False
        
        self.log(f"✅ GET /api/leagues?sportKey=football returned {football_leagues_count} football leagues")
        
        # Test 6: GET /api/leagues?sportKey=cricket - Should work (even if empty, no errors)
        self.log("Testing GET /api/leagues?sportKey=cricket...")
        result = self.test_api_endpoint("GET", "/leagues", params={"sportKey": "cricket"})
        if "error" in result:
            self.log("GET /api/leagues?sportKey=cricket failed", "ERROR")
            return False
        
        cricket_leagues_count = len(result)
        self.log(f"✅ GET /api/leagues?sportKey=cricket returned {cricket_leagues_count} cricket leagues (no errors)")
        
        # Test 7: POST /api/leagues with sportKey field - Should create new leagues with specified sport
        self.log("Testing POST /api/leagues with sportKey field...")
        
        # Create a football league
        football_league_data = {
            "name": "Test Football League",
            "commissionerId": user_id,
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "football"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", football_league_data)
        if "error" in result:
            self.log("Failed to create football league with sportKey", "ERROR")
            return False
        
        football_league_id = result.get("id")
        if not football_league_id:
            self.log("No league ID returned for football league", "ERROR")
            return False
        
        if result.get("sportKey") != "football":
            self.log("Created football league doesn't have correct sportKey", "ERROR")
            return False
        
        self.test_data["football_league_id"] = football_league_id
        self.log(f"✅ Created football league with sportKey: {football_league_id}")
        
        # Create a cricket league
        cricket_league_data = {
            "name": "Test Cricket League",
            "commissionerId": user_id,
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "cricket"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", cricket_league_data)
        if "error" in result:
            self.log("Failed to create cricket league with sportKey", "ERROR")
            return False
        
        cricket_league_id = result.get("id")
        if not cricket_league_id:
            self.log("No league ID returned for cricket league", "ERROR")
            return False
        
        if result.get("sportKey") != "cricket":
            self.log("Created cricket league doesn't have correct sportKey", "ERROR")
            return False
        
        self.test_data["cricket_league_id"] = cricket_league_id
        self.log(f"✅ Created cricket league with sportKey: {cricket_league_id}")
        
        # Verify filtering works with new leagues
        self.log("Verifying sport filtering with newly created leagues...")
        
        # Check football filter includes new football league
        result = self.test_api_endpoint("GET", "/leagues", params={"sportKey": "football"})
        if "error" in result:
            self.log("Failed to get football leagues after creation", "ERROR")
            return False
        
        football_league_ids = [league.get("id") for league in result]
        if football_league_id not in football_league_ids:
            self.log("New football league not found in football filter results", "ERROR")
            return False
        
        # Check cricket filter includes new cricket league
        result = self.test_api_endpoint("GET", "/leagues", params={"sportKey": "cricket"})
        if "error" in result:
            self.log("Failed to get cricket leagues after creation", "ERROR")
            return False
        
        cricket_league_ids = [league.get("id") for league in result]
        if cricket_league_id not in cricket_league_ids:
            self.log("New cricket league not found in cricket filter results", "ERROR")
            return False
        
        self.log("✅ Sport filtering working correctly with newly created leagues")
        
        self.log("✅ All Sport-Aware League Functionality working correctly")
        return True

    def test_data_verification(self) -> bool:
        """Test Data Verification"""
        self.log("=== Testing Data Verification ===")
        
        # Test 8: Verify existing leagues have been backfilled with sportKey:"football"
        self.log("Verifying existing leagues backfill...")
        result = self.test_api_endpoint("GET", "/leagues")
        if "error" in result:
            self.log("Failed to get leagues for backfill verification", "ERROR")
            return False
        
        leagues_without_sport_key = 0
        leagues_with_football = 0
        leagues_with_other_sports = 0
        
        for league in result:
            sport_key = league.get("sportKey")
            if not sport_key:
                leagues_without_sport_key += 1
            elif sport_key == "football":
                leagues_with_football += 1
            else:
                leagues_with_other_sports += 1
        
        if leagues_without_sport_key > 0:
            self.log(f"Found {leagues_without_sport_key} leagues without sportKey - migration incomplete", "ERROR")
            return False
        
        self.log(f"✅ All leagues have sportKey field: {leagues_with_football} football, {leagues_with_other_sports} other sports")
        
        # Test 9: Confirm sports collection has both Football and Cricket with proper schema
        self.log("Verifying sports collection schema...")
        if "sports" not in self.test_data:
            self.log("Sports data not available from previous test", "ERROR")
            return False
        
        sports = self.test_data["sports"]
        
        # Find football and cricket sports
        football_sport = next((s for s in sports if s.get("key") == "football"), None)
        cricket_sport = next((s for s in sports if s.get("key") == "cricket"), None)
        
        if not football_sport:
            self.log("Football sport not found in sports collection", "ERROR")
            return False
        
        if not cricket_sport:
            self.log("Cricket sport not found in sports collection", "ERROR")
            return False
        
        # Verify football schema
        required_fields = ["key", "name", "assetType", "uiHints", "auctionTemplate", "scoringSchema"]
        for field in required_fields:
            if field not in football_sport:
                self.log(f"Football sport missing required field: {field}", "ERROR")
                return False
        
        # Verify cricket schema
        for field in required_fields:
            if field not in cricket_sport:
                self.log(f"Cricket sport missing required field: {field}", "ERROR")
                return False
        
        self.log("✅ Sports collection has both Football and Cricket with proper schema")
        
        self.log("✅ All Data Verification tests passed")
        return True

    def test_cricket_functionality_enabled(self) -> bool:
        """Test that cricket functionality is enabled (SPORTS_CRICKET_ENABLED=true)"""
        self.log("=== Testing Cricket Functionality Enabled ===")
        
        # Test 10: Test that cricket functionality is enabled (SPORTS_CRICKET_ENABLED=true)
        # We can verify this by checking if cricket sport is available and functional
        
        # Check if cricket sport endpoint works
        result = self.test_api_endpoint("GET", "/sports/cricket")
        if "error" in result:
            self.log("Cricket sport endpoint not working - cricket functionality may be disabled", "ERROR")
            return False
        
        # Check if we can create cricket leagues
        if "cricket_league_id" not in self.test_data:
            self.log("Cricket league creation was not tested - cannot verify cricket functionality", "ERROR")
            return False
        
        cricket_league_id = self.test_data["cricket_league_id"]
        
        # Verify cricket league exists and is accessible
        result = self.test_api_endpoint("GET", f"/leagues/{cricket_league_id}")
        if "error" in result:
            self.log("Cannot access created cricket league - cricket functionality may be disabled", "ERROR")
            return False
        
        if result.get("sportKey") != "cricket":
            self.log("Cricket league doesn't have correct sportKey", "ERROR")
            return False
        
        # Check if cricket leagues are returned in sport-filtered queries
        result = self.test_api_endpoint("GET", "/leagues", params={"sportKey": "cricket"})
        if "error" in result:
            self.log("Cricket league filtering not working", "ERROR")
            return False
        
        cricket_league_ids = [league.get("id") for league in result]
        if cricket_league_id not in cricket_league_ids:
            self.log("Created cricket league not found in cricket filter", "ERROR")
            return False
        
        self.log("✅ Cricket functionality is enabled and working correctly")
        
        self.log("✅ All Cricket Functionality tests passed")
        return True

    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Delete test leagues if created
        if "football_league_id" in self.test_data and "user_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['football_league_id']}")
            if "error" not in result:
                self.log("Test football league deleted")
        
        if "cricket_league_id" in self.test_data and "user_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['cricket_league_id']}")
            if "error" not in result:
                self.log("Test cricket league deleted")

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all multi-sport tests"""
        self.log("🚀 Starting Multi-Sport Backend API Tests")
        
        results = {}
        
        # Test basic API connectivity
        root_result = self.test_api_endpoint("GET", "/")
        if "error" in root_result:
            self.log("❌ API not accessible", "ERROR")
            return {"api_connectivity": False}
        
        self.log("✅ API connectivity working")
        results["api_connectivity"] = True
        
        # Run all test suites
        test_suites = [
            ("sports_api_endpoints", self.test_sports_api_endpoints),
            ("sport_aware_league_functionality", self.test_sport_aware_league_functionality),
            ("data_verification", self.test_data_verification),
            ("cricket_functionality_enabled", self.test_cricket_functionality_enabled),
        ]
        
        for test_name, test_func in test_suites:
            try:
                results[test_name] = test_func()
                if not results[test_name]:
                    self.log(f"❌ {test_name} failed", "ERROR")
                else:
                    self.log(f"✅ {test_name} passed")
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = MultiSportTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("MULTI-SPORT BACKEND TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All multi-sport backend tests passed!")
        return True
    else:
        print("⚠️  Some multi-sport backend tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)