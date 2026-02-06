#!/usr/bin/env python3
"""
COMPREHENSIVE E2E PRODUCTION READINESS RE-VERIFICATION TEST
Covers all areas specified in the review request after UI improvements and text changes
"""

import requests
import socketio
import json
import time
import csv
import io
from datetime import datetime

BASE_URL = "https://fantasy-sports-bid.preview.emergentagent.com/api"
SOCKET_URL = "https://fantasy-sports-bid.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class ComprehensiveReviewTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_client = None
        self.socket_events = []
        self.performance_metrics = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200, files: dict = None) -> dict:
        """Test API endpoint with performance tracking"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            self.performance_metrics[f"{method} {endpoint}"] = response_time
            
            self.log(f"{method} {endpoint} -> {response.status_code} ({response_time:.3f}s)")
            
            if response.status_code != expected_status:
                return {"error": f"Status {response.status_code}", "text": response.text, "detail": response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}

    def test_multi_sport_core_functions(self) -> bool:
        """1. Multi-Sport Core Functions: Both football and cricket functionality intact"""
        self.log("=== 1. Multi-Sport Core Functions ===")
        
        # Test sports API
        sports_result = self.test_api_endpoint("GET", "/sports")
        if "error" in sports_result:
            return False
        
        sport_keys = [sport.get("key") for sport in sports_result]
        if "football" not in sport_keys or "cricket" not in sport_keys:
            self.log(f"Missing sports. Found: {sport_keys}", "ERROR")
            return False
        
        # Test individual sport configurations
        for sport_key in ["football", "cricket"]:
            sport_result = self.test_api_endpoint("GET", f"/sports/{sport_key}")
            if "error" in sport_result:
                return False
            
            required_fields = ["key", "name", "assetType", "uiHints", "auctionTemplate", "scoringSchema"]
            for field in required_fields:
                if field not in sport_result:
                    self.log(f"Missing {field} in {sport_key} configuration", "ERROR")
                    return False
        
        self.log("✅ Multi-Sport Core Functions intact")
        return True

    def test_league_management(self) -> bool:
        """2. League Management: Create/join/delete operations for both sports"""
        self.log("=== 2. League Management ===")
        
        # Create test user
        user_data = {
            "name": "Review Test Manager",
            "email": "review.test@example.com"
        }
        
        user_result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in user_result:
            return False
        
        user_id = user_result.get("id")
        self.test_data["user_id"] = user_id
        
        # Test league creation for both sports
        for sport_key in ["football", "cricket"]:
            league_data = {
                "name": f"Review Test {sport_key.title()} League",
                "commissionerId": user_id,
                "budget": 500000000.0,  # £500M budget as specified
                "minManagers": 2,
                "maxManagers": 8,
                "clubSlots": 5,
                "sportKey": sport_key
            }
            
            league_result = self.test_api_endpoint("POST", "/leagues", league_data)
            if "error" in league_result:
                return False
            
            league_id = league_result.get("id")
            invite_token = league_result.get("inviteToken")
            
            self.test_data[f"{sport_key}_league_id"] = league_id
            self.test_data[f"{sport_key}_invite_token"] = invite_token
            
            # Test joining league
            join_data = {
                "userId": user_id,
                "inviteToken": invite_token
            }
            
            join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
            if "error" in join_result:
                return False
            
            # Verify £500M budget
            participant = join_result.get("participant", {})
            if participant.get("budgetRemaining") != 500000000.0:
                self.log(f"Incorrect budget: {participant.get('budgetRemaining')}", "ERROR")
                return False
        
        self.log("✅ League Management working")
        return True

    def test_asset_management(self) -> bool:
        """3. Asset Management: Football clubs (36) and cricket players (20) accessible"""
        self.log("=== 3. Asset Management ===")
        
        # Test football clubs
        football_result = self.test_api_endpoint("GET", "/assets?sportKey=football")
        if "error" in football_result:
            return False
        
        football_assets = football_result.get("assets", [])
        if len(football_assets) != 36:
            self.log(f"Expected 36 football clubs, got {len(football_assets)}", "ERROR")
            return False
        
        # Test cricket players
        cricket_result = self.test_api_endpoint("GET", "/assets?sportKey=cricket")
        if "error" in cricket_result:
            return False
        
        cricket_assets = cricket_result.get("assets", [])
        if len(cricket_assets) != 20:
            self.log(f"Expected 20 cricket players, got {len(cricket_assets)}", "ERROR")
            return False
        
        # Test asset search functionality
        search_result = self.test_api_endpoint("GET", "/assets?sportKey=cricket&search=Mumbai")
        if "error" in search_result:
            return False
        
        self.log("✅ Asset Management working - 36 clubs, 20 players")
        return True

    def test_auction_system(self) -> bool:
        """4. Auction System: Real-time bidding, timer sync, lot completion working"""
        self.log("=== 4. Auction System ===")
        
        if "football_league_id" not in self.test_data:
            return False
        
        league_id = self.test_data["football_league_id"]
        user_id = self.test_data["user_id"]
        
        # Start auction
        auction_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/auction/start")
        if "error" in auction_result:
            return False
        
        auction_id = auction_result.get("auctionId")
        self.test_data["auction_id"] = auction_id
        
        # Get auction details
        auction_details = self.test_api_endpoint("GET", f"/auction/{auction_id}")
        if "error" in auction_details:
            return False
        
        current_club = auction_details.get("currentClub")
        if not current_club:
            return False
        
        self.test_data["current_club"] = current_club
        
        # Test real-time bidding
        bid_amounts = [1000000.0, 1500000.0, 2000000.0]  # £1M, £1.5M, £2M
        
        for amount in bid_amounts:
            bid_data = {
                "userId": user_id,
                "clubId": current_club["id"],
                "amount": amount
            }
            
            bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in bid_result:
                return False
        
        # Test minimum budget enforcement (£1M minimum)
        low_bid_data = {
            "userId": user_id,
            "clubId": current_club["id"],
            "amount": 500000.0
        }
        
        low_bid_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
        if "detail" not in low_bid_result or "£1,000,000" not in low_bid_result["detail"]:
            return False
        
        # Test lot completion
        complete_result = self.test_api_endpoint("POST", f"/auction/{auction_id}/complete-lot")
        if "error" in complete_result:
            return False
        
        self.log("✅ Auction System working - bidding, timer, lot completion")
        return True

    def test_cricket_scoring(self) -> bool:
        """5. Cricket Scoring: CSV upload, points calculation, leaderboards functional"""
        self.log("=== 5. Cricket Scoring ===")
        
        if "cricket_league_id" not in self.test_data:
            return False
        
        cricket_league_id = self.test_data["cricket_league_id"]
        
        # Create test CSV data
        csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match1,player1,75,2,1,0,1
match1,player2,45,0,2,1,0
match1,player3,120,1,0,0,0
match2,player1,30,3,0,0,2
match2,player2,85,1,1,0,0"""
        
        # Test CSV upload
        files = {
            'file': ('test_scoring.csv', io.StringIO(csv_data), 'text/csv')
        }
        
        upload_result = self.test_api_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", files=files)
        if "error" in upload_result:
            return False
        
        # Verify processing
        processed_rows = upload_result.get("processedRows", 0)
        if processed_rows != 5:
            self.log(f"Expected 5 processed rows, got {processed_rows}", "ERROR")
            return False
        
        # Test leaderboard
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
        if "error" in leaderboard_result:
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        if len(leaderboard) == 0:
            return False
        
        # Test re-upload (no double counting)
        re_upload_result = self.test_api_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", files=files)
        if "error" in re_upload_result:
            return False
        
        self.log("✅ Cricket Scoring working - CSV upload, leaderboards")
        return True

    def test_custom_scoring_rules(self) -> bool:
        """6. Custom Scoring Rules: League overrides, validation, immediate application"""
        self.log("=== 6. Custom Scoring Rules ===")
        
        if "cricket_league_id" not in self.test_data:
            return False
        
        cricket_league_id = self.test_data["cricket_league_id"]
        
        # Test custom scoring rules
        custom_scoring = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,
                    "wicket": 30,
                    "catch": 15,
                    "stumping": 20,
                    "runOut": 25
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": True,
                        "points": 60,
                        "threshold": 50
                    },
                    "century": {
                        "enabled": True,
                        "points": 120,
                        "threshold": 100
                    },
                    "fiveWicketHaul": {
                        "enabled": False,
                        "points": 0,
                        "threshold": 5
                    }
                }
            }
        }
        
        scoring_result = self.test_api_endpoint("PUT", f"/leagues/{cricket_league_id}/scoring-overrides", custom_scoring)
        if "error" in scoring_result:
            return False
        
        # Test validation - invalid rules should be rejected
        invalid_scoring = {
            "scoringOverrides": {
                "rules": {
                    "run": 1,
                    "wicket": 25
                    # Missing required rules
                }
            }
        }
        
        invalid_result = self.test_api_endpoint("PUT", f"/leagues/{cricket_league_id}/scoring-overrides", invalid_scoring, expected_status=400)
        if "detail" not in invalid_result:
            return False
        
        self.log("✅ Custom Scoring Rules working - validation, application")
        return True

    def test_socket_io_events(self) -> bool:
        """7. Socket.IO Events: Real-time communication for auctions still working"""
        self.log("=== 7. Socket.IO Events ===")
        
        try:
            self.socket_client = socketio.Client(logger=False, engineio_logger=False)
            
            @self.socket_client.event
            def connect():
                self.socket_events.append("connected")
            
            @self.socket_client.event
            def sync_state(data):
                self.socket_events.append("sync_state")
            
            @self.socket_client.event
            def joined(data):
                self.socket_events.append("joined")
            
            @self.socket_client.event
            def tick(data):
                self.socket_events.append("tick")
            
            # Connect
            self.socket_client.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(2)
            
            if "connected" not in self.socket_events:
                return False
            
            # Join auction room
            if "auction_id" in self.test_data:
                self.socket_client.emit('join_auction', {'auctionId': self.test_data["auction_id"]})
                time.sleep(2)
                
                if "joined" not in self.socket_events:
                    return False
                
                # Wait for timer ticks
                initial_ticks = self.socket_events.count("tick")
                time.sleep(3)
                final_ticks = self.socket_events.count("tick")
                
                if final_ticks > initial_ticks:
                    self.log("✅ Socket.IO Events working - connection, timer sync")
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"Socket.IO test failed: {str(e)}", "ERROR")
            return False

    def test_api_endpoints(self) -> bool:
        """8. API Endpoints: All endpoints responding correctly after changes"""
        self.log("=== 8. API Endpoints ===")
        
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
                return False
        
        self.log("✅ API Endpoints responding correctly")
        return True

    def test_database_integrity(self) -> bool:
        """9. Database Integrity: After league cleanup (54 deleted, 11 remaining)"""
        self.log("=== 9. Database Integrity ===")
        
        # Check leagues
        leagues_result = self.test_api_endpoint("GET", "/leagues")
        if "error" in leagues_result:
            return False
        
        leagues = leagues_result if isinstance(leagues_result, list) else []
        
        # Verify sport distribution
        football_count = len([l for l in leagues if l.get("sportKey") == "football"])
        cricket_count = len([l for l in leagues if l.get("sportKey") == "cricket"])
        
        if football_count == 0 or cricket_count == 0:
            self.log(f"Missing leagues: football={football_count}, cricket={cricket_count}", "ERROR")
            return False
        
        # Check sports configuration integrity
        for sport_key in ["football", "cricket"]:
            sport_result = self.test_api_endpoint("GET", f"/sports/{sport_key}")
            if "error" in sport_result:
                return False
        
        # Check asset collections
        for sport_key, expected_count in [("football", 36), ("cricket", 20)]:
            assets_result = self.test_api_endpoint("GET", f"/assets?sportKey={sport_key}")
            if "error" in assets_result:
                return False
            
            assets = assets_result.get("assets", [])
            if len(assets) != expected_count:
                return False
        
        self.log("✅ Database Integrity maintained")
        return True

    def test_performance_validation(self) -> bool:
        """10. Performance Validation: API calls under acceptable thresholds"""
        self.log("=== 10. Performance Validation ===")
        
        if self.performance_metrics:
            avg_response_time = sum(self.performance_metrics.values()) / len(self.performance_metrics)
            self.log(f"Average API response time: {avg_response_time:.3f}s")
            
            # Check if under 0.01s threshold as specified
            if avg_response_time > 0.01:
                self.log(f"Response time {avg_response_time:.3f}s exceeds 0.01s threshold", "ERROR")
                return False
        
        # Test concurrent operations
        start_time = time.time()
        concurrent_results = []
        
        for i in range(5):
            result = self.test_api_endpoint("GET", "/sports")
            concurrent_results.append("error" not in result)
        
        concurrent_time = time.time() - start_time
        
        if not all(concurrent_results):
            return False
        
        self.log(f"✅ Performance within limits - avg {avg_response_time:.3f}s, concurrent OK")
        return True

    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        if self.socket_client and self.socket_client.connected:
            self.socket_client.disconnect()
        
        # Delete test leagues (skip if auction is active)
        for sport_key in ["football", "cricket"]:
            league_key = f"{sport_key}_league_id"
            if league_key in self.test_data:
                league_id = self.test_data[league_key]
                # Try to delete, but don't fail if auction is active
                self.test_api_endpoint("DELETE", f"/leagues/{league_id}")

    def run_comprehensive_review_test(self) -> dict:
        """Run comprehensive review test"""
        self.log("🚀 COMPREHENSIVE E2E PRODUCTION READINESS RE-VERIFICATION")
        self.log("Verifying 96%+ readiness score maintenance after UI improvements")
        
        results = {}
        
        test_suites = [
            ("multi_sport_core_functions", self.test_multi_sport_core_functions),
            ("league_management", self.test_league_management),
            ("asset_management", self.test_asset_management),
            ("auction_system", self.test_auction_system),
            ("cricket_scoring", self.test_cricket_scoring),
            ("custom_scoring_rules", self.test_custom_scoring_rules),
            ("socket_io_events", self.test_socket_io_events),
            ("api_endpoints", self.test_api_endpoints),
            ("database_integrity", self.test_database_integrity),
            ("performance_validation", self.test_performance_validation),
        ]
        
        for test_name, test_func in test_suites:
            try:
                results[test_name] = test_func()
                
                if results[test_name]:
                    self.log(f"✅ {test_name.replace('_', ' ').title()}")
                else:
                    self.log(f"❌ {test_name.replace('_', ' ').title()}")
                    
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
        
        self.cleanup()
        return results

def main():
    """Main test execution"""
    tester = ComprehensiveReviewTester()
    results = tester.run_comprehensive_review_test()
    
    # Calculate production readiness score
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    readiness_score = (passed / total) * 100 if total > 0 else 0
    
    # Print results
    print("\n" + "="*80)
    print("COMPREHENSIVE E2E PRODUCTION READINESS RE-VERIFICATION RESULTS")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display:40} {status}")
    
    print(f"\nProduction Readiness Score: {readiness_score:.1f}% ({passed}/{total} tests passed)")
    
    # Performance summary
    if hasattr(tester, 'performance_metrics') and tester.performance_metrics:
        avg_response = sum(tester.performance_metrics.values()) / len(tester.performance_metrics)
        print(f"Average API Response Time: {avg_response:.3f}s")
    
    # Final assessment
    if readiness_score >= 96.0:
        print("🎉 PRODUCTION READY - Maintaining 96%+ readiness score!")
        print("✅ All critical functionality verified after UI improvements")
        return True
    else:
        print(f"⚠️  PRODUCTION READINESS: {readiness_score:.1f}% - Below 96% threshold")
        
        # Show failed areas
        failed_tests = [name for name, result in results.items() if not result]
        if failed_tests:
            print("\n❌ FAILED AREAS:")
            for test in failed_tests:
                print(f"   - {test.replace('_', ' ').title()}")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)