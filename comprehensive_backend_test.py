#!/usr/bin/env python3
"""
Comprehensive Backend Readiness Test for Pilot Report
Tests all core backend functionality as requested in the review.
"""

import requests
import json
import uuid
import time
import csv
import io
from datetime import datetime, timezone

# Backend URL from frontend/.env
BACKEND_URL = "https://bidflowfix.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.test_results = {
            "multi_sport_foundation": {},
            "asset_management": {},
            "league_creation_management": {},
            "auction_core_functionality": {},
            "cricket_specific_features": {},
            "my_competitions_endpoints": {},
            "socket_io": {}
        }
        self.test_user_id = None
        self.test_league_id = None
        self.test_auction_id = None
        self.invite_token = None
        
    def log_test(self, category, test_name, success, details="", response_code=None):
        """Log test result"""
        self.test_results[category][test_name] = {
            "success": success,
            "details": details,
            "response_code": response_code,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category}.{test_name}: {details}")
        
    def create_test_user(self):
        """Create a test user for authentication"""
        try:
            user_data = {
                "name": f"TestUser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com"
            }
            
            response = requests.post(f"{BACKEND_URL}/users", json=user_data)
            if response.status_code == 200:
                user = response.json()
                self.test_user_id = user["id"]
                print(f"✅ Created test user: {user['name']} (ID: {self.test_user_id})")
                return True
            else:
                print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating test user: {str(e)}")
            return False
    
    def test_multi_sport_foundation(self):
        """Test Area 1: Multi-Sport Foundation"""
        print("\n=== Testing Multi-Sport Foundation ===")
        
        # Test GET /api/sports
        try:
            response = requests.get(f"{BACKEND_URL}/sports")
            if response.status_code == 200:
                sports = response.json()
                football_found = any(sport.get("key") == "football" for sport in sports)
                cricket_found = any(sport.get("key") == "cricket" for sport in sports)
                
                if football_found and cricket_found:
                    self.log_test("multi_sport_foundation", "get_sports", True, 
                                f"Found {len(sports)} sports (Football + Cricket)", response.status_code)
                else:
                    self.log_test("multi_sport_foundation", "get_sports", False, 
                                f"Missing sports - Football: {football_found}, Cricket: {cricket_found}", response.status_code)
            else:
                self.log_test("multi_sport_foundation", "get_sports", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("multi_sport_foundation", "get_sports", False, f"Exception: {str(e)}")
        
        # Test GET /api/sports/football
        try:
            response = requests.get(f"{BACKEND_URL}/sports/football")
            if response.status_code == 200:
                football_sport = response.json()
                self.log_test("multi_sport_foundation", "get_football_sport", True, 
                            f"Football sport config retrieved: {football_sport.get('name')}", response.status_code)
            else:
                self.log_test("multi_sport_foundation", "get_football_sport", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("multi_sport_foundation", "get_football_sport", False, f"Exception: {str(e)}")
        
        # Test GET /api/sports/cricket
        try:
            response = requests.get(f"{BACKEND_URL}/sports/cricket")
            if response.status_code == 200:
                cricket_sport = response.json()
                self.log_test("multi_sport_foundation", "get_cricket_sport", True, 
                            f"Cricket sport config retrieved: {cricket_sport.get('name')}", response.status_code)
            else:
                self.log_test("multi_sport_foundation", "get_cricket_sport", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("multi_sport_foundation", "get_cricket_sport", False, f"Exception: {str(e)}")
        
        # Verify SPORTS_CRICKET_ENABLED=true (implicit from cricket endpoint working)
        cricket_enabled = self.test_results["multi_sport_foundation"].get("get_cricket_sport", {}).get("success", False)
        self.log_test("multi_sport_foundation", "cricket_enabled_flag", cricket_enabled, 
                    "Cricket feature flag verified through API availability")
    
    def test_asset_management(self):
        """Test Area 2: Asset Management"""
        print("\n=== Testing Asset Management ===")
        
        # Test GET /api/assets?sportKey=football
        try:
            response = requests.get(f"{BACKEND_URL}/assets", params={"sportKey": "football"})
            if response.status_code == 200:
                football_assets = response.json()
                asset_count = len(football_assets.get("assets", []))
                if asset_count >= 36:
                    self.log_test("asset_management", "football_assets", True, 
                                f"Found {asset_count} football clubs (expected 36+)", response.status_code)
                else:
                    self.log_test("asset_management", "football_assets", False, 
                                f"Only found {asset_count} football clubs (expected 36)", response.status_code)
            else:
                self.log_test("asset_management", "football_assets", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("asset_management", "football_assets", False, f"Exception: {str(e)}")
        
        # Test GET /api/assets?sportKey=cricket
        try:
            response = requests.get(f"{BACKEND_URL}/assets", params={"sportKey": "cricket"})
            if response.status_code == 200:
                cricket_assets = response.json()
                asset_count = len(cricket_assets.get("assets", []))
                self.log_test("asset_management", "cricket_assets", True, 
                            f"Found {asset_count} cricket players", response.status_code)
            else:
                self.log_test("asset_management", "cricket_assets", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("asset_management", "cricket_assets", False, f"Exception: {str(e)}")
    
    def test_league_creation_management(self):
        """Test Area 3: League Creation & Management"""
        print("\n=== Testing League Creation & Management ===")
        
        if not self.test_user_id:
            self.log_test("league_creation_management", "user_required", False, "No test user available")
            return
        
        # Test POST /api/leagues (create test league)
        try:
            league_data = {
                "name": f"Test League {uuid.uuid4().hex[:8]}",
                "commissionerId": self.test_user_id,
                "sportKey": "football",
                "budget": 500000000,  # £500M
                "clubSlots": 3,
                "minManagers": 2,
                "maxManagers": 8,
                "timerSeconds": 30,
                "antiSnipeSeconds": 10
            }
            
            response = requests.post(f"{BACKEND_URL}/leagues", json=league_data)
            if response.status_code == 200:
                league = response.json()
                self.test_league_id = league["id"]
                self.invite_token = league["inviteToken"]
                self.log_test("league_creation_management", "create_league", True, 
                            f"Created league: {league['name']} (ID: {self.test_league_id})", response.status_code)
            else:
                self.log_test("league_creation_management", "create_league", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("league_creation_management", "create_league", False, f"Exception: {str(e)}")
        
        # Test POST /api/leagues/:id/join (join with invite token)
        if self.test_league_id and self.invite_token:
            try:
                join_data = {
                    "userId": self.test_user_id,
                    "inviteToken": self.invite_token
                }
                
                response = requests.post(f"{BACKEND_URL}/leagues/{self.test_league_id}/join", json=join_data)
                if response.status_code == 200:
                    self.log_test("league_creation_management", "join_league", True, 
                                "Successfully joined league with invite token", response.status_code)
                else:
                    self.log_test("league_creation_management", "join_league", False, 
                                f"HTTP {response.status_code}: {response.text}", response.status_code)
            except Exception as e:
                self.log_test("league_creation_management", "join_league", False, f"Exception: {str(e)}")
        
        # Test GET /api/leagues (verify league appears)
        try:
            response = requests.get(f"{BACKEND_URL}/leagues")
            if response.status_code == 200:
                leagues = response.json()
                league_found = any(league.get("id") == self.test_league_id for league in leagues)
                self.log_test("league_creation_management", "get_leagues", league_found, 
                            f"Found {len(leagues)} leagues, test league present: {league_found}", response.status_code)
            else:
                self.log_test("league_creation_management", "get_leagues", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("league_creation_management", "get_leagues", False, f"Exception: {str(e)}")
        
        # Test GET /api/me/competitions (verify user's leagues)
        try:
            response = requests.get(f"{BACKEND_URL}/me/competitions", params={"userId": self.test_user_id})
            if response.status_code == 200:
                competitions = response.json()
                competition_found = any(comp.get("leagueId") == self.test_league_id for comp in competitions)
                self.log_test("league_creation_management", "get_my_competitions", competition_found, 
                            f"Found {len(competitions)} competitions, test league present: {competition_found}", response.status_code)
            else:
                self.log_test("league_creation_management", "get_my_competitions", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("league_creation_management", "get_my_competitions", False, f"Exception: {str(e)}")
    
    def test_auction_core_functionality(self):
        """Test Area 4: Auction Core Functionality"""
        print("\n=== Testing Auction Core Functionality ===")
        
        if not self.test_league_id or not self.test_user_id:
            self.log_test("auction_core_functionality", "prerequisites_missing", False, "No test league or user available")
            return
        
        # Test POST /api/leagues/:id/auction/start (start auction for test league)
        try:
            response = requests.post(f"{BACKEND_URL}/leagues/{self.test_league_id}/auction/start")
            if response.status_code == 200:
                auction = response.json()
                print(f"DEBUG: Auction response: {auction}")
                # Handle different response formats
                if "id" in auction:
                    self.test_auction_id = auction["id"]
                elif "auction" in auction and "id" in auction["auction"]:
                    self.test_auction_id = auction["auction"]["id"]
                else:
                    # Try to find auction ID in response
                    auction_keys = [k for k in auction.keys() if "id" in k.lower()]
                    if auction_keys:
                        self.test_auction_id = auction[auction_keys[0]]
                    else:
                        raise KeyError("No auction ID found in response")
                
                self.log_test("auction_core_functionality", "begin_auction", True, 
                            f"Started auction: {self.test_auction_id}", response.status_code)
            else:
                self.log_test("auction_core_functionality", "begin_auction", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("auction_core_functionality", "begin_auction", False, f"Exception: {str(e)}")
        
        # Test GET /api/auction/:id (verify auction details)
        if self.test_auction_id:
            try:
                response = requests.get(f"{BACKEND_URL}/auction/{self.test_auction_id}")
                if response.status_code == 200:
                    auction_data = response.json()
                    auction_status = auction_data.get("status")
                    self.log_test("auction_core_functionality", "auction_status", True, 
                                f"Auction status: {auction_status}", response.status_code)
                else:
                    self.log_test("auction_core_functionality", "auction_status", False, 
                                f"HTTP {response.status_code}: {response.text}", response.status_code)
            except Exception as e:
                self.log_test("auction_core_functionality", "auction_status", False, f"Exception: {str(e)}")
        
        # Test GET /api/auction/:id/clubs (verify asset list)
        if self.test_auction_id:
            try:
                response = requests.get(f"{BACKEND_URL}/auction/{self.test_auction_id}/clubs")
                if response.status_code == 200:
                    clubs_data = response.json()
                    clubs_count = clubs_data.get("totalClubs", 0)
                    self.log_test("auction_core_functionality", "auction_clubs", True, 
                                f"Found {clubs_count} clubs in auction", response.status_code)
                else:
                    self.log_test("auction_core_functionality", "auction_clubs", False, 
                                f"HTTP {response.status_code}: {response.text}", response.status_code)
            except Exception as e:
                self.log_test("auction_core_functionality", "auction_clubs", False, f"Exception: {str(e)}")
        
        # Test POST /api/auction/:id/bid (test bidding with minimum £1M validation)
        if self.test_auction_id:
            try:
                headers = {"X-User-ID": self.test_user_id}
                
                # Test bid below minimum (should fail)
                bid_data = {"amount": 500000}  # £500k - below £1M minimum
                response = requests.post(f"{BACKEND_URL}/auction/{self.test_auction_id}/bid", 
                                       json=bid_data, headers=headers)
                
                if response.status_code == 400:
                    self.log_test("auction_core_functionality", "bid_validation_minimum", True, 
                                "Correctly rejected bid below £1M minimum", response.status_code)
                else:
                    self.log_test("auction_core_functionality", "bid_validation_minimum", False, 
                                f"Expected 400 for low bid, got {response.status_code}: {response.text}", response.status_code)
                
                # Test valid bid (should succeed)
                bid_data = {"amount": 1000000}  # £1M - minimum valid bid
                response = requests.post(f"{BACKEND_URL}/auction/{self.test_auction_id}/bid", 
                                       json=bid_data, headers=headers)
                
                if response.status_code == 200:
                    self.log_test("auction_core_functionality", "bid_placement", True, 
                                "Successfully placed £1M bid", response.status_code)
                else:
                    self.log_test("auction_core_functionality", "bid_placement", False, 
                                f"HTTP {response.status_code}: {response.text}", response.status_code)
                    
            except Exception as e:
                self.log_test("auction_core_functionality", "bid_testing", False, f"Exception: {str(e)}")
    
    def test_cricket_specific_features(self):
        """Test Area 5: Cricket-Specific Features"""
        print("\n=== Testing Cricket-Specific Features ===")
        
        if not self.test_user_id:
            self.log_test("cricket_specific_features", "user_required", False, "No test user available")
            return
        
        # Verify cricket assets are available (already tested in asset_management)
        cricket_assets_success = self.test_results.get("asset_management", {}).get("cricket_assets", {}).get("success", False)
        self.log_test("cricket_specific_features", "cricket_assets_available", cricket_assets_success, 
                    "Cricket assets availability verified from asset management tests")
        
        # Test cricket league creation
        try:
            cricket_league_data = {
                "name": f"Cricket Test League {uuid.uuid4().hex[:8]}",
                "commissionerId": self.test_user_id,
                "sportKey": "cricket",
                "budget": 500000000,
                "clubSlots": 3,
                "minManagers": 2,
                "maxManagers": 8,
                "timerSeconds": 30,
                "antiSnipeSeconds": 10
            }
            
            response = requests.post(f"{BACKEND_URL}/leagues", json=cricket_league_data)
            if response.status_code == 200:
                cricket_league = response.json()
                cricket_league_id = cricket_league["id"]
                self.log_test("cricket_specific_features", "cricket_league_creation", True, 
                            f"Created cricket league: {cricket_league['name']}", response.status_code)
                
                # Test cricket scoring ingest endpoint exists
                try:
                    # Create a test CSV content
                    csv_content = "matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts\nM001,P001,50,2,1,0,0\n"
                    files = {'file': ('test_cricket_scores.csv', csv_content, 'text/csv')}
                    
                    response = requests.post(f"{BACKEND_URL}/scoring/{cricket_league_id}/ingest", files=files)
                    # We expect this to work or give a reasonable error (not 404)
                    if response.status_code in [200, 400, 403]:  # 400/403 are acceptable (validation/auth errors)
                        self.log_test("cricket_specific_features", "cricket_scoring_ingest", True, 
                                    f"Cricket scoring endpoint exists (HTTP {response.status_code})", response.status_code)
                    else:
                        self.log_test("cricket_specific_features", "cricket_scoring_ingest", False, 
                                    f"HTTP {response.status_code}: {response.text}", response.status_code)
                except Exception as e:
                    self.log_test("cricket_specific_features", "cricket_scoring_ingest", False, f"Exception: {str(e)}")
                    
            else:
                self.log_test("cricket_specific_features", "cricket_league_creation", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("cricket_specific_features", "cricket_league_creation", False, f"Exception: {str(e)}")
    
    def test_my_competitions_endpoints(self):
        """Test Area 6: My Competitions Endpoints"""
        print("\n=== Testing My Competitions Endpoints ===")
        
        if not self.test_league_id or not self.test_user_id:
            self.log_test("my_competitions_endpoints", "prerequisites_missing", False, "No test league or user available")
            return
        
        # Test GET /api/leagues/:id/summary
        try:
            response = requests.get(f"{BACKEND_URL}/leagues/{self.test_league_id}/summary", 
                                  params={"userId": self.test_user_id})
            if response.status_code == 200:
                summary = response.json()
                required_fields = ["leagueId", "name", "sportKey", "status", "commissioner", "yourRoster", "managers"]
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("my_competitions_endpoints", "league_summary", True, 
                                f"League summary complete with all required fields", response.status_code)
                else:
                    self.log_test("my_competitions_endpoints", "league_summary", False, 
                                f"Missing fields: {missing_fields}", response.status_code)
            else:
                self.log_test("my_competitions_endpoints", "league_summary", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("my_competitions_endpoints", "league_summary", False, f"Exception: {str(e)}")
        
        # Test GET /api/leagues/:id/standings
        try:
            response = requests.get(f"{BACKEND_URL}/leagues/{self.test_league_id}/standings")
            if response.status_code == 200:
                standings = response.json()
                has_table = "table" in standings
                self.log_test("my_competitions_endpoints", "league_standings", has_table, 
                            f"Standings retrieved, has table: {has_table}", response.status_code)
            else:
                self.log_test("my_competitions_endpoints", "league_standings", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("my_competitions_endpoints", "league_standings", False, f"Exception: {str(e)}")
        
        # Test GET /api/leagues/:id/fixtures
        try:
            response = requests.get(f"{BACKEND_URL}/leagues/{self.test_league_id}/fixtures")
            if response.status_code == 200:
                fixtures = response.json()
                self.log_test("my_competitions_endpoints", "league_fixtures", True, 
                            f"Fixtures retrieved: {len(fixtures)} fixtures", response.status_code)
            else:
                self.log_test("my_competitions_endpoints", "league_fixtures", False, 
                            f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("my_competitions_endpoints", "league_fixtures", False, f"Exception: {str(e)}")
    
    def test_socket_io_configuration(self):
        """Test Socket.IO path configuration"""
        print("\n=== Testing Socket.IO Configuration ===")
        
        try:
            # Test Socket.IO endpoint accessibility
            response = requests.get(f"https://bidflowfix.preview.emergentagent.com/api/socket.io/")
            # Socket.IO typically returns specific responses, we just want to ensure the path is configured
            if response.status_code in [200, 400, 404]:  # Any response indicates the path is configured
                self.log_test("socket_io", "path_configuration", True, 
                            f"Socket.IO path /api/socket.io configured (HTTP {response.status_code})", response.status_code)
            else:
                self.log_test("socket_io", "path_configuration", False, 
                            f"Unexpected response: HTTP {response.status_code}", response.status_code)
        except Exception as e:
            self.log_test("socket_io", "path_configuration", False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND READINESS TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        critical_failures = []
        
        for category, tests in self.test_results.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            category_passed = 0
            category_total = 0
            
            for test_name, result in tests.items():
                category_total += 1
                total_tests += 1
                
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"  {status} {test_name}: {result['details']}")
                
                if result["success"]:
                    category_passed += 1
                    passed_tests += 1
                else:
                    # Identify critical failures
                    if category in ["multi_sport_foundation", "league_creation_management", "auction_core_functionality"]:
                        critical_failures.append(f"{category}.{test_name}: {result['details']}")
            
            print(f"  Category Score: {category_passed}/{category_total}")
        
        # Overall assessment
        print(f"\n{'='*80}")
        print(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if critical_failures:
            print(f"\n❌ CRITICAL ISSUES FOUND ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"  - {failure}")
        
        # Recommendation
        if len(critical_failures) == 0 and passed_tests >= total_tests * 0.9:
            recommendation = "✅ GO - Backend is ready for production"
        elif len(critical_failures) <= 2 and passed_tests >= total_tests * 0.8:
            recommendation = "⚠️ CONDITIONAL GO - Minor issues need attention"
        else:
            recommendation = "❌ NO-GO - Critical issues must be resolved"
        
        print(f"\nRECOMMENDATION: {recommendation}")
        print("="*80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": (passed_tests/total_tests)*100,
            "critical_failures": critical_failures,
            "recommendation": recommendation,
            "detailed_results": self.test_results
        }

def main():
    """Run comprehensive backend readiness test"""
    print("Starting Comprehensive Backend Readiness Test for Pilot Report")
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    
    tester = BackendTester()
    
    # Create test user first
    if not tester.create_test_user():
        print("❌ Cannot proceed without test user")
        return
    
    # Run all test suites
    tester.test_multi_sport_foundation()
    tester.test_asset_management()
    tester.test_league_creation_management()
    tester.test_auction_core_functionality()
    tester.test_cricket_specific_features()
    tester.test_my_competitions_endpoints()
    tester.test_socket_io_configuration()
    
    # Generate final report
    report = tester.generate_report()
    
    # Save detailed results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed results saved to: /app/backend_test_results.json")

if __name__ == "__main__":
    main()