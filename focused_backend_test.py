#!/usr/bin/env python3
"""
Focused Backend Test for Production Readiness Re-Verification
Tests critical backend functionality after UI improvements
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://fantasy-cricket-6.preview.emergentagent.com/api"

class FocusedBackendTester:
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

    def test_multi_sport_core_functions(self) -> bool:
        """Test Multi-Sport Core Functions"""
        self.log("=== Testing Multi-Sport Core Functions ===")
        
        # Test sports endpoint
        sports_result = self.test_api_endpoint("GET", "/sports")
        if "error" in sports_result:
            return False
        
        if not isinstance(sports_result, list) or len(sports_result) < 2:
            self.log(f"Expected at least 2 sports, got {len(sports_result) if isinstance(sports_result, list) else 0}", "ERROR")
            return False
        
        sport_keys = [sport.get("key") for sport in sports_result]
        if "football" not in sport_keys or "cricket" not in sport_keys:
            self.log(f"Missing required sports. Found: {sport_keys}", "ERROR")
            return False
        
        self.log("✅ Both football and cricket sports available")
        return True

    def test_asset_management(self) -> bool:
        """Test Asset Management"""
        self.log("=== Testing Asset Management ===")
        
        # Test football assets (should be 36 clubs)
        football_result = self.test_api_endpoint("GET", "/assets?sportKey=football")
        if "error" in football_result:
            return False
        
        football_assets = football_result.get("assets", [])
        if len(football_assets) != 36:
            self.log(f"Expected 36 football clubs, got {len(football_assets)}", "ERROR")
            return False
        
        # Test cricket assets (should be 20 players)
        cricket_result = self.test_api_endpoint("GET", "/assets?sportKey=cricket")
        if "error" in cricket_result:
            return False
        
        cricket_assets = cricket_result.get("assets", [])
        if len(cricket_assets) != 20:
            self.log(f"Expected 20 cricket players, got {len(cricket_assets)}", "ERROR")
            return False
        
        self.log("✅ Asset management working - 36 football clubs, 20 cricket players")
        return True

    def test_league_management(self) -> bool:
        """Test League Management"""
        self.log("=== Testing League Management ===")
        
        # Create test user
        user_data = {
            "name": "Focused Test Manager",
            "email": "focused.test@example.com"
        }
        
        user_result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in user_result:
            return False
        
        user_id = user_result.get("id")
        self.test_data["user_id"] = user_id
        
        # Create football league
        football_league_data = {
            "name": "Focused Test Football League",
            "commissionerId": user_id,
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 5,
            "sportKey": "football"
        }
        
        football_league_result = self.test_api_endpoint("POST", "/leagues", football_league_data)
        if "error" in football_league_result:
            return False
        
        football_league_id = football_league_result.get("id")
        self.test_data["football_league_id"] = football_league_id
        
        # Create cricket league
        cricket_league_data = {
            "name": "Focused Test Cricket League",
            "commissionerId": user_id,
            "budget": 300000000.0,
            "minManagers": 2,
            "maxManagers": 10,
            "clubSlots": 11,
            "sportKey": "cricket"
        }
        
        cricket_league_result = self.test_api_endpoint("POST", "/leagues", cricket_league_data)
        if "error" in cricket_league_result:
            return False
        
        cricket_league_id = cricket_league_result.get("id")
        self.test_data["cricket_league_id"] = cricket_league_id
        
        # Test league filtering
        football_leagues = self.test_api_endpoint("GET", "/leagues?sportKey=football")
        if "error" in football_leagues:
            return False
        
        cricket_leagues = self.test_api_endpoint("GET", "/leagues?sportKey=cricket")
        if "error" in cricket_leagues:
            return False
        
        # Verify our leagues are in the filtered results
        football_ids = [league.get("id") for league in football_leagues]
        cricket_ids = [league.get("id") for league in cricket_leagues]
        
        if football_league_id not in football_ids:
            self.log("Football league not found in filtered results", "ERROR")
            return False
        
        if cricket_league_id not in cricket_ids:
            self.log("Cricket league not found in filtered results", "ERROR")
            return False
        
        self.log("✅ League management working - created and filtered both sports")
        return True

    def test_auction_system(self) -> bool:
        """Test Auction System"""
        self.log("=== Testing Auction System ===")
        
        if "football_league_id" not in self.test_data or "user_id" not in self.test_data:
            self.log("Missing test data for auction test", "ERROR")
            return False
        
        league_id = self.test_data["football_league_id"]
        user_id = self.test_data["user_id"]
        
        # Join the league first
        league_result = self.test_api_endpoint("GET", f"/leagues/{league_id}")
        if "error" in league_result:
            return False
        
        invite_token = league_result.get("inviteToken")
        
        join_data = {
            "userId": user_id,
            "inviteToken": invite_token
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in join_result:
            return False
        
        # Start auction
        auction_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in auction_result:
            return False
        
        auction_id = auction_result.get("auctionId")
        if not auction_id:
            self.log("No auction ID returned", "ERROR")
            return False
        
        self.test_data["auction_id"] = auction_id
        
        # Get auction details
        auction_details = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_details:
            return False
        
        current_club = auction_details.get("currentClub")
        if not current_club:
            self.log("No current club in auction", "ERROR")
            return False
        
        # Test bidding
        bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 2000000.0  # £2M
        }
        
        bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
        if "error" in bid_result:
            return False
        
        # Test minimum budget enforcement
        low_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 500000.0  # Below £1M minimum
        }
        
        low_bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
        if "detail" not in low_bid_result or "£1,000,000" not in low_bid_result["detail"]:
            self.log("Minimum budget enforcement not working", "ERROR")
            return False
        
        # Test clubs list endpoint
        clubs_result = self.test_api_endpoint("GET", f"/auction/{auction_id}/clubs")
        if "error" in clubs_result:
            return False
        
        clubs = clubs_result.get("clubs", [])
        if len(clubs) != 36:
            self.log(f"Expected 36 clubs, got {len(clubs)}", "ERROR")
            return False
        
        self.log("✅ Auction system working - bidding, minimum budget, clubs list")
        return True

    def test_api_endpoints(self) -> bool:
        """Test Core API Endpoints"""
        self.log("=== Testing Core API Endpoints ===")
        
        endpoints = [
            ("GET", "/"),
            ("GET", "/sports"),
            ("GET", "/sports/football"),
            ("GET", "/sports/cricket"),
            ("GET", "/assets?sportKey=football"),
            ("GET", "/assets?sportKey=cricket"),
            ("GET", "/leagues"),
            ("GET", "/clubs"),
        ]
        
        for method, endpoint in endpoints:
            result = self.test_api_endpoint(method, endpoint)
            if "error" in result:
                self.log(f"Endpoint {method} {endpoint} failed", "ERROR")
                return False
        
        self.log("✅ All core API endpoints working")
        return True

    def test_database_integrity(self) -> bool:
        """Test Database Integrity"""
        self.log("=== Testing Database Integrity ===")
        
        # Check leagues exist and have proper sport keys
        leagues_result = self.test_api_endpoint("GET", "/leagues")
        if "error" in leagues_result:
            return False
        
        leagues = leagues_result if isinstance(leagues_result, list) else []
        
        football_count = len([l for l in leagues if l.get("sportKey") == "football"])
        cricket_count = len([l for l in leagues if l.get("sportKey") == "cricket"])
        
        if football_count == 0:
            self.log("No football leagues found", "ERROR")
            return False
        
        if cricket_count == 0:
            self.log("No cricket leagues found", "ERROR")
            return False
        
        # Check sports configuration
        for sport_key in ["football", "cricket"]:
            sport_result = self.test_api_endpoint("GET", f"/sports/{sport_key}")
            if "error" in sport_result:
                return False
            
            required_fields = ["key", "name", "assetType", "uiHints"]
            for field in required_fields:
                if field not in sport_result:
                    self.log(f"Missing {field} in {sport_key} configuration", "ERROR")
                    return False
        
        self.log(f"✅ Database integrity verified - {football_count} football, {cricket_count} cricket leagues")
        return True

    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Delete test leagues
        for league_key in ["football_league_id", "cricket_league_id"]:
            if league_key in self.test_data:
                league_id = self.test_data[league_key]
                result = self.test_api_endpoint("DELETE", f"/leagues/{league_id}")
                if "error" not in result:
                    self.log(f"Deleted test league {league_id}")

    def run_focused_tests(self) -> dict:
        """Run focused backend tests"""
        self.log("🚀 Starting Focused Backend Production Readiness Test")
        
        results = {}
        
        test_suites = [
            ("multi_sport_core_functions", self.test_multi_sport_core_functions),
            ("asset_management", self.test_asset_management),
            ("league_management", self.test_league_management),
            ("auction_system", self.test_auction_system),
            ("api_endpoints", self.test_api_endpoints),
            ("database_integrity", self.test_database_integrity),
        ]
        
        for test_name, test_func in test_suites:
            try:
                self.log(f"\n--- Running {test_name.replace('_', ' ').title()} ---")
                results[test_name] = test_func()
                
                if results[test_name]:
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED")
                    
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = FocusedBackendTester()
    results = tester.run_focused_tests()
    
    # Calculate results
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    # Print summary
    print("\n" + "="*60)
    print("FOCUSED BACKEND PRODUCTION READINESS TEST RESULTS")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display:35} {status}")
    
    print(f"\nSuccess Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
    
    if success_rate >= 80.0:
        print("🎉 BACKEND CORE FUNCTIONALITY WORKING")
        return True
    else:
        print("⚠️  BACKEND ISSUES DETECTED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)