#!/usr/bin/env python3
"""
Service Layer and Assets Endpoint Testing
Tests the newly implemented service layer and assets endpoint functionality
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://bidflowfix.preview.emergentagent.com/api"

class ServiceLayerTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> dict:
        """Test API endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                self.log(f"Expected {expected_status}, got {response.status_code}: {response.text}", "ERROR")
                return {"error": f"Status {response.status_code}", "text": response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}
    
    def test_sports_endpoints(self) -> bool:
        """Test sports endpoints - should return Football + Cricket since flag is enabled"""
        self.log("=== Testing Sports Endpoints ===")
        
        # Test GET /api/sports - should return both Football and Cricket
        result = self.test_api_endpoint("GET", "/sports")
        if "error" in result:
            self.log("GET /api/sports failed", "ERROR")
            return False
        
        if not isinstance(result, list):
            self.log("Sports endpoint should return a list", "ERROR")
            return False
        
        # Should have both Football and Cricket since SPORTS_CRICKET_ENABLED=true
        sport_keys = [sport.get("key") for sport in result]
        if "football" not in sport_keys:
            self.log("Football sport not found in sports list", "ERROR")
            return False
        
        if "cricket" not in sport_keys:
            self.log("Cricket sport not found in sports list (should be enabled)", "ERROR")
            return False
        
        self.log(f"✅ GET /api/sports returns {len(result)} sports: {sport_keys}")
        
        # Test individual sport endpoints
        for sport_key in ["football", "cricket"]:
            result = self.test_api_endpoint("GET", f"/sports/{sport_key}")
            if "error" in result:
                self.log(f"GET /api/sports/{sport_key} failed", "ERROR")
                return False
            
            # Verify sport structure
            required_fields = ["key", "name", "assetType", "uiHints", "auctionTemplate", "scoringSchema"]
            for field in required_fields:
                if field not in result:
                    self.log(f"Missing required field '{field}' in {sport_key} sport", "ERROR")
                    return False
            
            # Verify sport-specific configurations
            if sport_key == "football":
                if result.get("assetType") != "CLUB":
                    self.log(f"Football should have assetType='CLUB', got '{result.get('assetType')}'", "ERROR")
                    return False
                ui_hints = result.get("uiHints", {})
                if ui_hints.get("assetLabel") != "Club" or ui_hints.get("assetPlural") != "Clubs":
                    self.log(f"Football UI hints incorrect: {ui_hints}", "ERROR")
                    return False
            
            elif sport_key == "cricket":
                if result.get("assetType") != "PLAYER":
                    self.log(f"Cricket should have assetType='PLAYER', got '{result.get('assetType')}'", "ERROR")
                    return False
                ui_hints = result.get("uiHints", {})
                if ui_hints.get("assetLabel") != "Player" or ui_hints.get("assetPlural") != "Players":
                    self.log(f"Cricket UI hints incorrect: {ui_hints}", "ERROR")
                    return False
            
            self.log(f"✅ GET /api/sports/{sport_key} working correctly")
        
        return True
    
    def test_assets_endpoints(self) -> bool:
        """Test assets endpoints with pagination for both football and cricket"""
        self.log("=== Testing Assets Endpoints ===")
        
        # Test 1: GET /api/assets?sportKey=football - should return paginated clubs
        self.log("Testing football assets...")
        result = self.test_api_endpoint("GET", "/assets?sportKey=football")
        if "error" in result:
            self.log("GET /api/assets?sportKey=football failed", "ERROR")
            return False
        
        # Verify response structure
        if "assets" not in result or "pagination" not in result:
            self.log("Assets response missing required fields (assets, pagination)", "ERROR")
            return False
        
        assets = result.get("assets", [])
        pagination = result.get("pagination", {})
        
        # Should have clubs for football
        if len(assets) == 0:
            self.log("No football clubs returned - should have clubs", "ERROR")
            return False
        
        # Verify pagination structure
        required_pagination_fields = ["page", "pageSize", "total", "totalPages", "hasNext", "hasPrev"]
        for field in required_pagination_fields:
            if field not in pagination:
                self.log(f"Missing pagination field '{field}'", "ERROR")
                return False
        
        # Verify club structure (should be Club objects)
        first_club = assets[0]
        required_club_fields = ["id", "name", "uefaId", "country"]
        for field in required_club_fields:
            if field not in first_club:
                self.log(f"Missing club field '{field}' in football assets", "ERROR")
                return False
        
        self.log(f"✅ Football assets: {len(assets)} clubs, page {pagination['page']}/{pagination['totalPages']}")
        
        # Test 2: GET /api/assets?sportKey=cricket - should return empty array (until seeding)
        self.log("Testing cricket assets...")
        result = self.test_api_endpoint("GET", "/assets?sportKey=cricket")
        if "error" in result:
            self.log("GET /api/assets?sportKey=cricket failed", "ERROR")
            return False
        
        assets = result.get("assets", [])
        pagination = result.get("pagination", {})
        
        # Should be empty for cricket (no players seeded yet)
        if len(assets) != 0:
            self.log(f"Cricket assets should be empty, got {len(assets)} items", "ERROR")
            return False
        
        if pagination.get("total") != 0:
            self.log(f"Cricket pagination total should be 0, got {pagination.get('total')}", "ERROR")
            return False
        
        self.log("✅ Cricket assets correctly returns empty array")
        
        # Test 3: Test pagination parameters
        self.log("Testing pagination parameters...")
        
        # Test with custom page size
        result = self.test_api_endpoint("GET", "/assets?sportKey=football&pageSize=5")
        if "error" in result:
            self.log("Pagination with pageSize failed", "ERROR")
            return False
        
        assets = result.get("assets", [])
        pagination = result.get("pagination", {})
        
        if pagination.get("pageSize") != 5:
            self.log(f"Expected pageSize=5, got {pagination.get('pageSize')}", "ERROR")
            return False
        
        if len(assets) > 5:
            self.log(f"Expected max 5 assets, got {len(assets)}", "ERROR")
            return False
        
        self.log("✅ Pagination pageSize parameter working")
        
        # Test with page parameter
        if pagination.get("totalPages", 0) > 1:
            result = self.test_api_endpoint("GET", "/assets?sportKey=football&page=2")
            if "error" in result:
                self.log("Pagination with page parameter failed", "ERROR")
                return False
            
            pagination = result.get("pagination", {})
            if pagination.get("page") != 2:
                self.log(f"Expected page=2, got {pagination.get('page')}", "ERROR")
                return False
            
            self.log("✅ Pagination page parameter working")
        
        # Test 4: Test search parameter
        self.log("Testing search parameter...")
        result = self.test_api_endpoint("GET", "/assets?sportKey=football&search=Real")
        if "error" in result:
            self.log("Search parameter failed", "ERROR")
            return False
        
        assets = result.get("assets", [])
        if len(assets) > 0:
            # Check if search results contain "Real" in name or country
            found_match = False
            for asset in assets:
                name = asset.get("name", "").lower()
                country = asset.get("country", "").lower()
                if "real" in name or "real" in country:
                    found_match = True
                    break
            
            if not found_match:
                self.log("Search results don't contain search term", "ERROR")
                return False
            
            self.log(f"✅ Search parameter working - found {len(assets)} results for 'Real'")
        else:
            self.log("✅ Search parameter working - no results for 'Real' (acceptable)")
        
        # Test 5: Test missing sportKey parameter
        self.log("Testing missing sportKey parameter...")
        result = self.test_api_endpoint("GET", "/assets", expected_status=422)
        # For 422 status, we get a "detail" field with validation errors
        if "detail" not in result:
            self.log("Missing sportKey should return 422 validation error", "ERROR")
            return False
        
        self.log("✅ Missing sportKey correctly returns 422 validation error")
        
        return True
    
    def test_backward_compatibility(self) -> bool:
        """Test backward compatibility - existing functionality should be preserved"""
        self.log("=== Testing Backward Compatibility ===")
        
        # Test 1: Existing leagues API should still work
        self.log("Testing existing leagues API...")
        result = self.test_api_endpoint("GET", "/leagues")
        if "error" in result:
            self.log("GET /api/leagues failed", "ERROR")
            return False
        
        if not isinstance(result, list):
            self.log("Leagues endpoint should return a list", "ERROR")
            return False
        
        self.log(f"✅ GET /api/leagues working - found {len(result)} leagues")
        
        # Test 2: League creation should default to football when sportKey omitted
        self.log("Testing league creation defaults...")
        
        # First create a test user
        user_data = {
            "name": "Test Commissioner",
            "email": "test.commissioner@example.com"
        }
        
        user_result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in user_result:
            self.log("Failed to create test user for league testing", "ERROR")
            return False
        
        user_id = user_result.get("id")
        self.test_data["test_user_id"] = user_id
        
        # Create league without sportKey (should default to football)
        league_data = {
            "name": "Backward Compatibility Test League",
            "commissionerId": user_id,
            "budget": 100000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3
            # Note: no sportKey specified - should default to football
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("League creation without sportKey failed", "ERROR")
            return False
        
        league_id = result.get("id")
        sport_key = result.get("sportKey")
        
        if sport_key != "football":
            self.log(f"League should default to football, got '{sport_key}'", "ERROR")
            return False
        
        self.test_data["test_league_id"] = league_id
        self.log("✅ League creation defaults to football when sportKey omitted")
        
        # Test 3: League creation with explicit sportKey should work
        league_data_cricket = {
            "name": "Cricket Test League",
            "commissionerId": user_id,
            "budget": 50000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "cricket"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data_cricket)
        if "error" in result:
            self.log("League creation with cricket sportKey failed", "ERROR")
            return False
        
        sport_key = result.get("sportKey")
        if sport_key != "cricket":
            self.log(f"League should have cricket sportKey, got '{sport_key}'", "ERROR")
            return False
        
        cricket_league_id = result.get("id")
        self.test_data["cricket_league_id"] = cricket_league_id
        self.log("✅ League creation with explicit sportKey working")
        
        # Test 4: League filtering by sport should work
        self.log("Testing league filtering by sport...")
        
        # Filter by football
        result = self.test_api_endpoint("GET", "/leagues?sportKey=football")
        if "error" in result:
            self.log("League filtering by football failed", "ERROR")
            return False
        
        football_leagues = result
        football_count = len([l for l in football_leagues if l.get("sportKey") == "football"])
        
        if football_count == 0:
            self.log("No football leagues found in filtered results", "ERROR")
            return False
        
        self.log(f"✅ Found {football_count} football leagues")
        
        # Filter by cricket
        result = self.test_api_endpoint("GET", "/leagues?sportKey=cricket")
        if "error" in result:
            self.log("League filtering by cricket failed", "ERROR")
            return False
        
        cricket_leagues = result
        cricket_count = len([l for l in cricket_leagues if l.get("sportKey") == "cricket"])
        
        if cricket_count == 0:
            self.log("No cricket leagues found in filtered results", "ERROR")
            return False
        
        self.log(f"✅ Found {cricket_count} cricket leagues")
        
        # Test 5: Existing club endpoints should still work
        self.log("Testing existing club endpoints...")
        result = self.test_api_endpoint("GET", "/clubs")
        if "error" in result:
            self.log("GET /api/clubs failed", "ERROR")
            return False
        
        if not isinstance(result, list):
            self.log("Clubs endpoint should return a list", "ERROR")
            return False
        
        self.log(f"✅ GET /api/clubs working - found {len(result)} clubs")
        
        return True
    
    def test_service_layer_integration(self) -> bool:
        """Test that service layer is properly integrated"""
        self.log("=== Testing Service Layer Integration ===")
        
        # The service layer is tested indirectly through the API endpoints
        # We verify that the endpoints are using the service layer correctly
        
        # Test 1: SportService.list_sports() filtering
        self.log("Testing SportService.list_sports() filtering...")
        
        # This is tested through the /api/sports endpoint
        # Since SPORTS_CRICKET_ENABLED=true, both sports should be returned
        result = self.test_api_endpoint("GET", "/sports")
        if "error" in result:
            self.log("SportService.list_sports() test failed", "ERROR")
            return False
        
        sport_keys = [sport.get("key") for sport in result]
        if len(sport_keys) < 2 or "football" not in sport_keys or "cricket" not in sport_keys:
            self.log("SportService.list_sports() not filtering correctly based on flag", "ERROR")
            return False
        
        self.log("✅ SportService.list_sports() filtering working correctly")
        
        # Test 2: SportService.get_sport() retrieval
        self.log("Testing SportService.get_sport() retrieval...")
        
        for sport_key in ["football", "cricket"]:
            result = self.test_api_endpoint("GET", f"/sports/{sport_key}")
            if "error" in result:
                self.log(f"SportService.get_sport('{sport_key}') failed", "ERROR")
                return False
            
            if result.get("key") != sport_key:
                self.log(f"SportService.get_sport() returned wrong sport", "ERROR")
                return False
        
        self.log("✅ SportService.get_sport() working correctly")
        
        # Test 3: AssetService.list_assets() pagination
        self.log("Testing AssetService.list_assets() pagination...")
        
        # Test with different page sizes and pages
        test_cases = [
            {"sportKey": "football", "pageSize": 10},
            {"sportKey": "football", "page": 1, "pageSize": 5},
            {"sportKey": "cricket", "pageSize": 20},
        ]
        
        for test_case in test_cases:
            params = "&".join([f"{k}={v}" for k, v in test_case.items()])
            result = self.test_api_endpoint("GET", f"/assets?{params}")
            if "error" in result:
                self.log(f"AssetService.list_assets() failed with params: {params}", "ERROR")
                return False
            
            pagination = result.get("pagination", {})
            if pagination.get("pageSize") != test_case.get("pageSize"):
                self.log(f"AssetService pagination pageSize incorrect", "ERROR")
                return False
        
        self.log("✅ AssetService.list_assets() pagination working correctly")
        
        return True
    
    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Delete test leagues
        for league_key in ["test_league_id", "cricket_league_id"]:
            if league_key in self.test_data:
                league_id = self.test_data[league_key]
                result = self.test_api_endpoint("DELETE", f"/leagues/{league_id}")
                if "error" not in result:
                    self.log(f"Deleted test league: {league_id}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all service layer and assets endpoint tests"""
        self.log("🚀 Starting Service Layer and Assets Endpoint Tests")
        
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
            ("sports_endpoints", self.test_sports_endpoints),
            ("assets_endpoints", self.test_assets_endpoints),
            ("backward_compatibility", self.test_backward_compatibility),
            ("service_layer_integration", self.test_service_layer_integration),
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
    tester = ServiceLayerTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("SERVICE LAYER AND ASSETS ENDPOINT TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All service layer and assets endpoint tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)