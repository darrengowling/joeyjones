#!/usr/bin/env python3
"""
Cricket Player Seeding and Assets Endpoint Testing
Tests all requirements from the review request:
1. Cricket player seeding verification
2. Assets endpoint functionality for cricket
3. Pagination and search functionality
4. Data integrity checks
5. No regression on football assets
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).parent / "backend"
load_dotenv(backend_dir / '.env')

# Configuration
BACKEND_URL = "https://sportbid-platform.preview.emergentagent.com/api"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

class CricketAssetsTestSuite:
    def __init__(self):
        self.session = None
        self.db = None
        self.client = None
        self.test_results = {
            "cricket_seeding_verification": False,
            "cricket_assets_endpoint": False,
            "pagination_functionality": False,
            "search_functionality": False,
            "data_integrity": False,
            "football_regression": False
        }
        self.detailed_results = []
    
    async def setup(self):
        """Setup HTTP session and database connection"""
        self.session = aiohttp.ClientSession()
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        print("🔧 Test setup completed")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.client:
            self.client.close()
        print("🧹 Test cleanup completed")
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.detailed_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_cricket_seeding_verification(self):
        """Test 1: Verify cricket players were successfully seeded into assets collection"""
        print("\n🏏 Testing Cricket Player Seeding Verification...")
        
        try:
            # Check assets collection directly
            cricket_players = await self.db.assets.find({"sportKey": "cricket"}).to_list(100)
            
            if len(cricket_players) == 0:
                self.log_result("Cricket Seeding", False, "No cricket players found in assets collection")
                return False
            
            # Verify we have expected number of players (20 from CSV)
            expected_count = 20
            actual_count = len(cricket_players)
            
            if actual_count != expected_count:
                self.log_result("Cricket Seeding", False, f"Expected {expected_count} players, found {actual_count}")
                return False
            
            # Verify structure of first player
            sample_player = cricket_players[0]
            required_fields = ["id", "sportKey", "externalId", "name", "meta"]
            
            for field in required_fields:
                if field not in sample_player:
                    self.log_result("Cricket Seeding", False, f"Missing required field: {field}")
                    return False
            
            # Verify sportKey is "cricket"
            if sample_player["sportKey"] != "cricket":
                self.log_result("Cricket Seeding", False, f"Expected sportKey 'cricket', got '{sample_player['sportKey']}'")
                return False
            
            # Verify meta structure contains franchise and role
            meta = sample_player.get("meta", {})
            if "franchise" not in meta or "role" not in meta:
                self.log_result("Cricket Seeding", False, "Meta object missing franchise or role")
                return False
            
            self.log_result("Cricket Seeding", True, f"Successfully verified {actual_count} cricket players with correct structure")
            self.test_results["cricket_seeding_verification"] = True
            return True
            
        except Exception as e:
            self.log_result("Cricket Seeding", False, f"Database error: {str(e)}")
            return False
    
    async def test_upsert_functionality(self):
        """Test 2: Verify upsert functionality works (no duplicates on re-running)"""
        print("\n🔄 Testing Upsert Functionality...")
        
        try:
            # Get initial count
            initial_count = await self.db.assets.count_documents({"sportKey": "cricket"})
            
            # Re-run seeding script
            import subprocess
            result = subprocess.run([
                sys.executable, "scripts/seed_cricket_players.py"
            ], cwd="/app", capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_result("Upsert Functionality", False, f"Seeding script failed: {result.stderr}")
                return False
            
            # Check count after re-running
            final_count = await self.db.assets.count_documents({"sportKey": "cricket"})
            
            if final_count != initial_count:
                self.log_result("Upsert Functionality", False, f"Count changed from {initial_count} to {final_count} - duplicates created")
                return False
            
            # Verify no duplicate externalIds
            pipeline = [
                {"$match": {"sportKey": "cricket"}},
                {"$group": {"_id": "$externalId", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.assets.aggregate(pipeline).to_list(100)
            
            if duplicates:
                self.log_result("Upsert Functionality", False, f"Found {len(duplicates)} duplicate externalIds")
                return False
            
            self.log_result("Upsert Functionality", True, f"No duplicates created, count remained {final_count}")
            return True
            
        except Exception as e:
            self.log_result("Upsert Functionality", False, f"Error: {str(e)}")
            return False
    
    async def test_cricket_assets_endpoint(self):
        """Test 3: GET /api/assets?sportKey=cricket - Should return seeded players"""
        print("\n🏏 Testing Cricket Assets Endpoint...")
        
        try:
            url = f"{BACKEND_URL}/assets?sportKey=cricket"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Cricket Assets Endpoint", False, f"HTTP {response.status}: {await response.text()}")
                    return False
                
                data = await response.json()
                
                # Verify response structure
                if "assets" not in data or "pagination" not in data:
                    self.log_result("Cricket Assets Endpoint", False, "Missing 'assets' or 'pagination' in response")
                    return False
                
                assets = data["assets"]
                pagination = data["pagination"]
                
                # Verify we get 20 players
                if len(assets) != 20:
                    self.log_result("Cricket Assets Endpoint", False, f"Expected 20 players, got {len(assets)}")
                    return False
                
                # Verify pagination info
                expected_pagination = {
                    "page": 1,
                    "pageSize": 50,
                    "total": 20,
                    "totalPages": 1,
                    "hasNext": False,
                    "hasPrev": False
                }
                
                for key, expected_value in expected_pagination.items():
                    if pagination.get(key) != expected_value:
                        self.log_result("Cricket Assets Endpoint", False, f"Pagination {key}: expected {expected_value}, got {pagination.get(key)}")
                        return False
                
                # Verify player structure
                sample_player = assets[0]
                required_fields = ["id", "sportKey", "externalId", "name", "meta"]
                
                for field in required_fields:
                    if field not in sample_player:
                        self.log_result("Cricket Assets Endpoint", False, f"Player missing field: {field}")
                        return False
                
                # Verify meta structure
                meta = sample_player["meta"]
                if "franchise" not in meta or "role" not in meta:
                    self.log_result("Cricket Assets Endpoint", False, "Player meta missing franchise or role")
                    return False
                
                self.log_result("Cricket Assets Endpoint", True, f"Successfully returned {len(assets)} cricket players with correct structure")
                self.test_results["cricket_assets_endpoint"] = True
                return True
                
        except Exception as e:
            self.log_result("Cricket Assets Endpoint", False, f"Error: {str(e)}")
            return False
    
    async def test_pagination_functionality(self):
        """Test 4: Test pagination parameters (page, pageSize)"""
        print("\n📄 Testing Pagination Functionality...")
        
        try:
            # Test page 1 with pageSize 10
            url = f"{BACKEND_URL}/assets?sportKey=cricket&page=1&pageSize=10"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Pagination - Page 1", False, f"HTTP {response.status}")
                    return False
                
                data = await response.json()
                assets = data["assets"]
                pagination = data["pagination"]
                
                if len(assets) != 10:
                    self.log_result("Pagination - Page 1", False, f"Expected 10 assets, got {len(assets)}")
                    return False
                
                if pagination["page"] != 1 or pagination["pageSize"] != 10:
                    self.log_result("Pagination - Page 1", False, f"Wrong pagination info: page={pagination['page']}, pageSize={pagination['pageSize']}")
                    return False
                
                if not pagination["hasNext"] or pagination["hasPrev"]:
                    self.log_result("Pagination - Page 1", False, f"Wrong hasNext/hasPrev: hasNext={pagination['hasNext']}, hasPrev={pagination['hasPrev']}")
                    return False
            
            # Test page 2 with pageSize 10
            url = f"{BACKEND_URL}/assets?sportKey=cricket&page=2&pageSize=10"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Pagination - Page 2", False, f"HTTP {response.status}")
                    return False
                
                data = await response.json()
                assets = data["assets"]
                pagination = data["pagination"]
                
                if len(assets) != 10:
                    self.log_result("Pagination - Page 2", False, f"Expected 10 assets, got {len(assets)}")
                    return False
                
                if pagination["page"] != 2 or pagination["pageSize"] != 10:
                    self.log_result("Pagination - Page 2", False, f"Wrong pagination info: page={pagination['page']}, pageSize={pagination['pageSize']}")
                    return False
                
                if pagination["hasNext"] or not pagination["hasPrev"]:
                    self.log_result("Pagination - Page 2", False, f"Wrong hasNext/hasPrev: hasNext={pagination['hasNext']}, hasPrev={pagination['hasPrev']}")
                    return False
            
            self.log_result("Pagination Functionality", True, "Page 1 and Page 2 with pageSize=10 working correctly")
            self.test_results["pagination_functionality"] = True
            return True
            
        except Exception as e:
            self.log_result("Pagination Functionality", False, f"Error: {str(e)}")
            return False
    
    async def test_search_functionality(self):
        """Test 5: Test search functionality by name, franchise, role"""
        print("\n🔍 Testing Search Functionality...")
        
        try:
            # Test search by name
            url = f"{BACKEND_URL}/assets?sportKey=cricket&search=Virat"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Search by Name", False, f"HTTP {response.status}")
                    return False
                
                data = await response.json()
                assets = data["assets"]
                
                if len(assets) != 1:
                    self.log_result("Search by Name", False, f"Expected 1 result for 'Virat', got {len(assets)}")
                    return False
                
                if "Virat" not in assets[0]["name"]:
                    self.log_result("Search by Name", False, f"Result doesn't contain 'Virat': {assets[0]['name']}")
                    return False
            
            # Test search by franchise
            url = f"{BACKEND_URL}/assets?sportKey=cricket&search=Mumbai"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Search by Franchise", False, f"HTTP {response.status}")
                    return False
                
                data = await response.json()
                assets = data["assets"]
                
                # Should find multiple Mumbai Indians players
                if len(assets) < 2:
                    self.log_result("Search by Franchise", False, f"Expected multiple results for 'Mumbai', got {len(assets)}")
                    return False
                
                # Verify all results contain Mumbai in franchise
                for asset in assets:
                    if "Mumbai" not in asset["meta"]["franchise"]:
                        self.log_result("Search by Franchise", False, f"Result doesn't contain 'Mumbai' in franchise: {asset['meta']['franchise']}")
                        return False
            
            # Test search by role
            url = f"{BACKEND_URL}/assets?sportKey=cricket&search=Bowler"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Search by Role", False, f"HTTP {response.status}")
                    return False
                
                data = await response.json()
                assets = data["assets"]
                
                # Should find multiple bowlers
                if len(assets) < 3:
                    self.log_result("Search by Role", False, f"Expected multiple results for 'Bowler', got {len(assets)}")
                    return False
                
                # Verify all results have Bowler role
                for asset in assets:
                    if asset["meta"]["role"] != "Bowler":
                        self.log_result("Search by Role", False, f"Result doesn't have 'Bowler' role: {asset['meta']['role']}")
                        return False
            
            self.log_result("Search Functionality", True, "Search by name, franchise, and role all working correctly")
            self.test_results["search_functionality"] = True
            return True
            
        except Exception as e:
            self.log_result("Search Functionality", False, f"Error: {str(e)}")
            return False
    
    async def test_data_integrity(self):
        """Test 6: Verify cricket players have all required fields and proper meta structure"""
        print("\n🔍 Testing Data Integrity...")
        
        try:
            # Get all cricket players from database
            cricket_players = await self.db.assets.find({"sportKey": "cricket"}).to_list(100)
            
            required_fields = ["id", "sportKey", "externalId", "name", "meta", "createdAt", "updatedAt"]
            required_meta_fields = ["franchise", "role"]
            
            for i, player in enumerate(cricket_players):
                # Check required fields
                for field in required_fields:
                    if field not in player:
                        self.log_result("Data Integrity", False, f"Player {i+1} missing field: {field}")
                        return False
                
                # Check sportKey is cricket
                if player["sportKey"] != "cricket":
                    self.log_result("Data Integrity", False, f"Player {i+1} has wrong sportKey: {player['sportKey']}")
                    return False
                
                # Check meta structure
                meta = player.get("meta", {})
                for meta_field in required_meta_fields:
                    if meta_field not in meta:
                        self.log_result("Data Integrity", False, f"Player {i+1} meta missing field: {meta_field}")
                        return False
                
                # Check externalId is not empty
                if not player.get("externalId", "").strip():
                    self.log_result("Data Integrity", False, f"Player {i+1} has empty externalId")
                    return False
                
                # Check name is not empty
                if not player.get("name", "").strip():
                    self.log_result("Data Integrity", False, f"Player {i+1} has empty name")
                    return False
                
                # Check franchise and role are not empty
                if not meta.get("franchise", "").strip():
                    self.log_result("Data Integrity", False, f"Player {i+1} has empty franchise")
                    return False
                
                if not meta.get("role", "").strip():
                    self.log_result("Data Integrity", False, f"Player {i+1} has empty role")
                    return False
            
            self.log_result("Data Integrity", True, f"All {len(cricket_players)} cricket players have correct structure and required fields")
            self.test_results["data_integrity"] = True
            return True
            
        except Exception as e:
            self.log_result("Data Integrity", False, f"Error: {str(e)}")
            return False
    
    async def test_football_regression(self):
        """Test 7: Check that football assets still work (no regression)"""
        print("\n⚽ Testing Football Assets Regression...")
        
        try:
            # Test football assets endpoint
            url = f"{BACKEND_URL}/assets?sportKey=football"
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.log_result("Football Regression", False, f"HTTP {response.status}: {await response.text()}")
                    return False
                
                data = await response.json()
                
                # Verify response structure
                if "assets" not in data or "pagination" not in data:
                    self.log_result("Football Regression", False, "Missing 'assets' or 'pagination' in response")
                    return False
                
                assets = data["assets"]
                
                # Should have 36 football clubs
                if len(assets) != 36:
                    self.log_result("Football Regression", False, f"Expected 36 football clubs, got {len(assets)}")
                    return False
                
                # Verify club structure (should have different structure than cricket players)
                sample_club = assets[0]
                expected_club_fields = ["id", "name", "country", "uefaId"]
                
                for field in expected_club_fields:
                    if field not in sample_club:
                        self.log_result("Football Regression", False, f"Football club missing field: {field}")
                        return False
                
                # Verify it's not cricket data
                if "sportKey" in sample_club and sample_club["sportKey"] == "cricket":
                    self.log_result("Football Regression", False, "Football endpoint returning cricket data")
                    return False
                
                # Test football search
                url = f"{BACKEND_URL}/assets?sportKey=football&search=Real"
                async with self.session.get(url) as response:
                    if response.status != 200:
                        self.log_result("Football Search Regression", False, f"HTTP {response.status}")
                        return False
                    
                    data = await response.json()
                    assets = data["assets"]
                    
                    # Should find Real Madrid
                    if len(assets) == 0:
                        self.log_result("Football Search Regression", False, "No results for 'Real' search")
                        return False
                    
                    found_real_madrid = any("Real" in club["name"] for club in assets)
                    if not found_real_madrid:
                        self.log_result("Football Search Regression", False, "Real Madrid not found in search results")
                        return False
            
            self.log_result("Football Regression", True, "Football assets endpoint working correctly, no regression detected")
            self.test_results["football_regression"] = True
            return True
            
        except Exception as e:
            self.log_result("Football Regression", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("🏏 Starting Cricket Assets Testing Suite...")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run all tests
            await self.test_cricket_seeding_verification()
            await self.test_upsert_functionality()
            await self.test_cricket_assets_endpoint()
            await self.test_pagination_functionality()
            await self.test_search_functionality()
            await self.test_data_integrity()
            await self.test_football_regression()
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏏 CRICKET ASSETS TESTING SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Cricket assets functionality is working correctly!")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - See details above")
            return False

async def main():
    """Main test runner"""
    test_suite = CricketAssetsTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ Cricket assets testing completed successfully!")
        return 0
    else:
        print("\n❌ Cricket assets testing failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)