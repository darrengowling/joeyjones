#!/usr/bin/env python3
"""
ISSUE-018 Team Selection Test - Backend Testing
Tests the fix for team selection in auctions where Premier League should show exactly 20 teams, not 74.

Test Scenario:
1. Create a new Premier League competition via backend API
2. Verify the league shows exactly 20 PL clubs (not 74)
3. Verify team selection APIs work correctly
4. Start the auction and verify queue contains exactly 20 Premier League teams
"""

import requests
import json
import uuid
import time
from datetime import datetime, timezone

# Backend URL from frontend/.env
BACKEND_URL = "https://bidding-tester.preview.emergentagent.com/api"

class Issue018Tester:
    def __init__(self):
        self.test_user_id = None
        self.test_league_id = None
        self.test_auction_id = None
        self.invite_token = None
        
    def log(self, message, level="INFO"):
        """Log test message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Test an API endpoint and return response"""
        url = f"{BACKEND_URL}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
        
        # Add user ID header if we have one
        if self.test_user_id:
            headers["X-User-ID"] = self.test_user_id
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
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
    
    def create_test_user(self):
        """Create a test user for authentication"""
        try:
            user_data = {
                "name": f"PL_TestUser_{uuid.uuid4().hex[:8]}",
                "email": f"pl_test_{uuid.uuid4().hex[:8]}@example.com"
            }
            
            response = requests.post(f"{BACKEND_URL}/users", json=user_data)
            if response.status_code == 200:
                user = response.json()
                self.test_user_id = user["id"]
                self.log(f"✅ Created test user: {user['name']} (ID: {self.test_user_id})")
                return True
            else:
                self.log(f"❌ Failed to create test user: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error creating test user: {str(e)}", "ERROR")
            return False
    
    def test_premier_league_creation(self):
        """Test creating a Premier League competition"""
        self.log("=== Testing Premier League Creation ===")
        
        if not self.test_user_id:
            self.log("❌ No test user available", "ERROR")
            return False
        
        # Create Premier League competition
        league_data = {
            "name": f"Premier League Test {uuid.uuid4().hex[:6]}",
            "commissionerId": self.test_user_id,
            "budget": 500000000.0,  # £500m budget
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 20,  # Premier League has 20 teams
            "sportKey": "football",
            "competitionCode": "EPL"  # Premier League code
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log(f"❌ League creation failed: {result}", "ERROR")
            return False
        
        self.test_league_id = result.get("id")
        self.invite_token = result.get("inviteToken")
        
        if not self.test_league_id:
            self.log("❌ No league ID returned", "ERROR")
            return False
        
        self.log(f"✅ Created Premier League: {self.test_league_id}")
        return True
    
    def test_premier_league_club_count(self):
        """Test that Premier League shows exactly 20 clubs"""
        self.log("=== Testing Premier League Club Count ===")
        
        if not self.test_league_id:
            self.log("❌ No league available", "ERROR")
            return False
        
        # Get league details
        result = self.test_api_endpoint("GET", f"/leagues/{self.test_league_id}")
        if "error" in result:
            self.log(f"❌ Failed to get league details: {result}", "ERROR")
            return False
        
        # Check assetsSelected count (may be null initially)
        assets_selected = result.get("assetsSelected")
        if assets_selected is None:
            assets_selected = []
        
        self.log(f"League has {len(assets_selected)} assets selected")
        
        # Get clubs for Premier League using the filtered endpoint
        clubs_result = self.test_api_endpoint("GET", "/clubs?competition=EPL")
        if "error" in clubs_result:
            self.log(f"❌ Failed to get EPL clubs: {clubs_result}", "ERROR")
            return False
        
        if isinstance(clubs_result, list):
            epl_clubs = clubs_result
        else:
            epl_clubs = clubs_result.get("clubs", [])
        
        epl_club_count = len(epl_clubs)
        self.log(f"Found {epl_club_count} EPL clubs via filtered endpoint")
        
        # Verify exactly 20 Premier League clubs
        if epl_club_count != 20:
            self.log(f"❌ Expected 20 EPL clubs, found {epl_club_count}", "ERROR")
            return False
        
        self.log("✅ Premier League has exactly 20 clubs")
        
        # Get all clubs to verify total count (should be more than 20)
        all_clubs_result = self.test_api_endpoint("GET", "/clubs")
        if "error" not in all_clubs_result:
            if isinstance(all_clubs_result, list):
                all_clubs = all_clubs_result
            else:
                all_clubs = all_clubs_result.get("clubs", [])
            
            total_clubs = len(all_clubs)
            self.log(f"Total clubs in database: {total_clubs}")
            
            # Verify we have more than 20 clubs total (should be around 74)
            if total_clubs < 50:
                self.log(f"❌ Expected at least 50 total clubs, found {total_clubs}", "ERROR")
                return False
            
            # This confirms the fix: EPL endpoint returns 20, but total is much higher
            if total_clubs > epl_club_count:
                self.log(f"✅ Confirmed: EPL filter returns {epl_club_count} clubs, total is {total_clubs}")
            else:
                self.log(f"❌ Issue: Total clubs ({total_clubs}) not greater than EPL clubs ({epl_club_count})", "ERROR")
                return False
        
        return True
    
    def test_team_selection_api(self):
        """Test team selection APIs"""
        self.log("=== Testing Team Selection APIs ===")
        
        if not self.test_league_id:
            self.log("❌ No league available", "ERROR")
            return False
        
        # Test getting all available teams (should show all 74+ teams)
        all_clubs_result = self.test_api_endpoint("GET", "/clubs")
        if "error" in all_clubs_result:
            self.log(f"❌ Failed to get all clubs: {all_clubs_result}", "ERROR")
            return False
        
        if isinstance(all_clubs_result, list):
            all_clubs = all_clubs_result
        else:
            all_clubs = all_clubs_result.get("clubs", [])
        
        total_clubs = len(all_clubs)
        self.log(f"Total clubs available: {total_clubs}")
        
        if total_clubs < 70:  # Should have at least 70+ clubs (EPL + UCL)
            self.log(f"❌ Expected at least 70 clubs, found {total_clubs}", "ERROR")
            return False
        
        # Test getting EPL clubs specifically
        epl_clubs_result = self.test_api_endpoint("GET", "/clubs?competition=EPL")
        if "error" in epl_clubs_result:
            self.log(f"❌ Failed to get EPL clubs: {epl_clubs_result}", "ERROR")
            return False
        
        if isinstance(epl_clubs_result, list):
            epl_clubs = epl_clubs_result
        else:
            epl_clubs = epl_clubs_result.get("clubs", [])
        
        epl_count = len(epl_clubs)
        self.log(f"EPL clubs available: {epl_count}")
        
        if epl_count != 20:
            self.log(f"❌ Expected exactly 20 EPL clubs, found {epl_count}", "ERROR")
            return False
        
        self.log("✅ Team selection APIs working correctly")
        return True
    
    def test_auction_creation_with_correct_teams(self):
        """Test auction creation uses exactly 20 Premier League teams"""
        self.log("=== Testing Auction Creation with Correct Teams ===")
        
        if not self.test_league_id:
            self.log("❌ No league available", "ERROR")
            return False
        
        # Join the league first (commissioner needs to be a participant)
        join_data = {
            "userId": self.test_user_id,
            "inviteToken": self.invite_token
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{self.test_league_id}/join", join_data)
        if "error" in join_result:
            self.log(f"❌ Failed to join league: {join_result}", "ERROR")
            return False
        
        self.log("✅ Joined league as commissioner")
        
        # Start auction
        auction_result = self.test_api_endpoint("POST", f"/leagues/{self.test_league_id}/auction/start")
        if "error" in auction_result:
            self.log(f"❌ Failed to start auction: {auction_result}", "ERROR")
            return False
        
        self.test_auction_id = auction_result.get("auctionId")
        if not self.test_auction_id:
            self.log("❌ No auction ID returned", "ERROR")
            return False
        
        self.log(f"✅ Started auction: {self.test_auction_id}")
        
        # Get auction details to verify club queue (auction starts in "waiting" status)
        auction_details = self.test_api_endpoint("GET", f"/auction/{self.test_auction_id}")
        if "error" in auction_details:
            self.log(f"❌ Failed to get auction details: {auction_details}", "ERROR")
            return False
        
        auction_data = auction_details.get("auction", {})
        clubs_queue = auction_data.get("clubQueue", [])
        
        self.log(f"Auction queue has {len(clubs_queue)} clubs")
        
        # Verify exactly 20 clubs in queue
        if len(clubs_queue) != 20:
            self.log(f"❌ Expected 20 clubs in auction queue, found {len(clubs_queue)}", "ERROR")
            return False
        
        # Begin the auction to move from "waiting" to "active" status
        begin_result = self.test_api_endpoint("POST", f"/auction/{self.test_auction_id}/begin")
        if "error" in begin_result:
            self.log(f"❌ Failed to begin auction: {begin_result}", "ERROR")
            return False
        
        self.log("✅ Auction begun successfully")
        
        # Get clubs list from auction endpoint
        clubs_list_result = self.test_api_endpoint("GET", f"/auction/{self.test_auction_id}/clubs")
        if "error" in clubs_list_result:
            self.log(f"❌ Failed to get auction clubs list: {clubs_list_result}", "ERROR")
            return False
        
        clubs_data = clubs_list_result.get("clubs", [])
        total_clubs_in_auction = clubs_list_result.get("totalClubs", len(clubs_data))
        
        self.log(f"Auction clubs endpoint shows {total_clubs_in_auction} total clubs")
        
        if total_clubs_in_auction != 20:
            self.log(f"❌ Expected 20 clubs in auction, found {total_clubs_in_auction}", "ERROR")
            return False
        
        # Verify all clubs are Premier League clubs by checking names
        epl_clubs_in_auction = 0
        non_epl_found = []
        
        for club in clubs_data:
            club_name = club.get("name", "")
            # Check if this is a known EPL club (basic validation)
            if any(epl_team in club_name for epl_team in [
                "Arsenal", "Chelsea", "Liverpool", "Manchester", "Tottenham", 
                "Brighton", "Newcastle", "West Ham", "Aston Villa", "Crystal Palace",
                "Everton", "Brentford", "Fulham", "Wolves", "Bournemouth",
                "Sheffield", "Burnley", "Luton", "Nottingham", "Leicester"
            ]):
                epl_clubs_in_auction += 1
            else:
                # Check if it's a non-EPL club that shouldn't be there
                if any(non_epl in club_name for non_epl in [
                    "Real Madrid", "Barcelona", "Bayern", "PSG", "Juventus",
                    "AC Milan", "Inter Milan", "Atletico", "Dortmund", "Ajax"
                ]):
                    non_epl_found.append(club_name)
        
        self.log(f"Found {epl_clubs_in_auction} recognizable EPL clubs in auction")
        
        if non_epl_found:
            self.log(f"❌ Found non-EPL clubs in Premier League auction: {non_epl_found}", "ERROR")
            return False
        
        # Should have most clubs as EPL clubs (allowing for some name variations)
        if epl_clubs_in_auction < 15:  # At least 15 should be recognizable EPL clubs
            self.log(f"❌ Expected at least 15 EPL clubs, found {epl_clubs_in_auction}", "ERROR")
            return False
        
        self.log("✅ Auction created with correct number of Premier League teams")
        return True
    
    def test_no_non_pl_teams_in_auction(self):
        """Test that no non-Premier League teams appear in the auction"""
        self.log("=== Testing No Non-PL Teams in Auction ===")
        
        if not self.test_auction_id:
            self.log("❌ No auction available", "ERROR")
            return False
        
        # Get clubs list from auction
        clubs_list_result = self.test_api_endpoint("GET", f"/auction/{self.test_auction_id}/clubs")
        if "error" in clubs_list_result:
            self.log(f"❌ Failed to get auction clubs: {clubs_list_result}", "ERROR")
            return False
        
        clubs_data = clubs_list_result.get("clubs", [])
        
        # Check for non-PL teams that should NOT be in a Premier League auction
        non_pl_teams = [
            "Real Madrid", "Barcelona", "Bayern Munich", "PSG", "Juventus",
            "AC Milan", "Inter Milan", "Atletico Madrid", "Borussia Dortmund",
            "Ajax", "Porto", "Benfica", "Celtic", "Rangers"
        ]
        
        found_non_pl = []
        for club in clubs_data:
            club_name = club.get("name", "")
            for non_pl_team in non_pl_teams:
                if non_pl_team.lower() in club_name.lower():
                    found_non_pl.append(club_name)
        
        if found_non_pl:
            self.log(f"❌ Found non-Premier League teams in auction: {found_non_pl}", "ERROR")
            return False
        
        self.log("✅ No non-Premier League teams found in auction")
        return True
    
    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        # Delete test league if created
        if self.test_league_id and self.test_user_id:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_league_id}?user_id={self.test_user_id}")
            if "error" not in result:
                self.log("✅ Test league deleted")
            else:
                self.log(f"⚠️ Failed to delete test league: {result}")
    
    def run_issue_018_test(self):
        """Run the complete ISSUE-018 test"""
        self.log("🚀 Starting ISSUE-018 Team Selection Test")
        self.log("Testing fix for Premier League showing 20 teams (not 74)")
        
        results = {}
        
        # Test steps
        test_steps = [
            ("create_test_user", self.create_test_user),
            ("premier_league_creation", self.test_premier_league_creation),
            ("premier_league_club_count", self.test_premier_league_club_count),
            ("team_selection_api", self.test_team_selection_api),
            ("auction_creation_with_correct_teams", self.test_auction_creation_with_correct_teams),
            ("no_non_pl_teams_in_auction", self.test_no_non_pl_teams_in_auction),
        ]
        
        for test_name, test_func in test_steps:
            try:
                self.log(f"\n--- Running {test_name} ---")
                results[test_name] = test_func()
                if results[test_name]:
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED")
                    break  # Stop on first failure for this specific issue test
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
                break
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = Issue018Tester()
    results = tester.run_issue_018_test()
    
    # Print summary
    print("\n" + "="*60)
    print("ISSUE-018 TEAM SELECTION TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ISSUE-018 fix verified - Premier League team selection working correctly!")
        print("✅ Premier League competitions now show exactly 20 teams (not 74)")
        print("✅ Auction queues contain exactly 20 Premier League teams")
        print("✅ No non-Premier League teams appear in Premier League auctions")
        return True
    else:
        print("⚠️ ISSUE-018 fix verification failed")
        print("❌ Premier League team selection still has issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)