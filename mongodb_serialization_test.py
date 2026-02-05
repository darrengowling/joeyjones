#!/usr/bin/env python3
"""
MongoDB _id Serialization Test for Prem8 League
Tests specific endpoints to verify all MongoDB _id serialization issues are fixed.
"""

import requests
import json
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://sportauction.preview.emergentagent.com/api"

class MongoSerializationTester:
    def __init__(self):
        self.test_results = {}
        self.prem8_league_id = "e479329d-3111-4000-b69c-880a667fe43d"
        
    def log_test(self, test_name, success, details="", response_code=None, response_data=None):
        """Log test result"""
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "response_code": response_code,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_code:
            print(f"    Response Code: {response_code}")
        if not success and response_data:
            print(f"    Response Data: {json.dumps(response_data, indent=2)}")
    
    def make_request(self, method, endpoint, data=None):
        """Make HTTP request and return response"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code < 400
            }
        except Exception as e:
            return {
                "status_code": None,
                "data": {"error": str(e)},
                "success": False
            }
    
    def check_for_id_fields(self, data, path=""):
        """Recursively check for _id fields in response data"""
        id_fields_found = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if key == "_id":
                    id_fields_found.append(current_path)
                else:
                    id_fields_found.extend(self.check_for_id_fields(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                id_fields_found.extend(self.check_for_id_fields(item, current_path))
        
        return id_fields_found
    
    def test_league_details(self):
        """Test GET /api/leagues/{league_id}"""
        print(f"\n=== Testing League Details Endpoint ===")
        
        result = self.make_request("GET", f"/leagues/{self.prem8_league_id}")
        
        if not result["success"]:
            self.log_test(
                "league_details",
                False,
                f"Request failed with status {result['status_code']}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Check for _id fields
        id_fields = self.check_for_id_fields(result["data"])
        
        if id_fields:
            self.log_test(
                "league_details",
                False,
                f"Found _id fields in response: {', '.join(id_fields)}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Verify response structure
        data = result["data"]
        required_fields = ["id", "name", "sportKey"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test(
                "league_details",
                False,
                f"Missing required fields: {', '.join(missing_fields)}",
                result["status_code"],
                data
            )
            return False
        
        self.log_test(
            "league_details",
            True,
            f"League '{data.get('name')}' returned without _id fields",
            result["status_code"]
        )
        return True
    
    def test_league_fixtures(self):
        """Test GET /api/leagues/{league_id}/fixtures"""
        print(f"\n=== Testing League Fixtures Endpoint ===")
        
        result = self.make_request("GET", f"/leagues/{self.prem8_league_id}/fixtures")
        
        if not result["success"]:
            self.log_test(
                "league_fixtures",
                False,
                f"Request failed with status {result['status_code']}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Check for _id fields
        id_fields = self.check_for_id_fields(result["data"])
        
        if id_fields:
            self.log_test(
                "league_fixtures",
                False,
                f"Found _id fields in response: {', '.join(id_fields)}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Verify response structure
        data = result["data"]
        fixtures = data.get("fixtures", [])
        
        if not isinstance(fixtures, list):
            self.log_test(
                "league_fixtures",
                False,
                "Fixtures should be a list",
                result["status_code"],
                data
            )
            return False
        
        # Check expected fixture count (should be 6 according to review request)
        expected_count = 6
        if len(fixtures) != expected_count:
            self.log_test(
                "league_fixtures",
                False,
                f"Expected {expected_count} fixtures, got {len(fixtures)}",
                result["status_code"],
                data
            )
            return False
        
        self.log_test(
            "league_fixtures",
            True,
            f"Retrieved {len(fixtures)} fixtures without _id fields",
            result["status_code"]
        )
        return True
    
    def test_league_participants(self):
        """Test GET /api/leagues/{league_id}/participants"""
        print(f"\n=== Testing League Participants Endpoint ===")
        
        result = self.make_request("GET", f"/leagues/{self.prem8_league_id}/participants")
        
        if not result["success"]:
            self.log_test(
                "league_participants",
                False,
                f"Request failed with status {result['status_code']}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Check for _id fields
        id_fields = self.check_for_id_fields(result["data"])
        
        if id_fields:
            self.log_test(
                "league_participants",
                False,
                f"Found _id fields in response: {', '.join(id_fields)}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Verify response structure
        data = result["data"]
        
        # Check if it's the new format with count and participants
        if isinstance(data, dict) and "participants" in data:
            participants = data["participants"]
            count = data.get("count", 0)
        elif isinstance(data, list):
            # Old format - direct list
            participants = data
            count = len(participants)
        else:
            self.log_test(
                "league_participants",
                False,
                "Invalid response format",
                result["status_code"],
                data
            )
            return False
        
        if not isinstance(participants, list):
            self.log_test(
                "league_participants",
                False,
                "Participants should be a list",
                result["status_code"],
                data
            )
            return False
        
        self.log_test(
            "league_participants",
            True,
            f"Retrieved {len(participants)} participants without _id fields",
            result["status_code"]
        )
        return True
    
    def test_clubs_endpoint(self):
        """Test GET /api/clubs"""
        print(f"\n=== Testing Clubs Endpoint ===")
        
        result = self.make_request("GET", "/clubs")
        
        if not result["success"]:
            self.log_test(
                "clubs_endpoint",
                False,
                f"Request failed with status {result['status_code']}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Check for _id fields
        id_fields = self.check_for_id_fields(result["data"])
        
        if id_fields:
            self.log_test(
                "clubs_endpoint",
                False,
                f"Found _id fields in response: {', '.join(id_fields)}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Verify response structure
        data = result["data"]
        
        if not isinstance(data, list):
            self.log_test(
                "clubs_endpoint",
                False,
                "Clubs should be a list",
                result["status_code"],
                data
            )
            return False
        
        # Check that we have clubs
        if len(data) == 0:
            self.log_test(
                "clubs_endpoint",
                False,
                "No clubs returned",
                result["status_code"],
                data
            )
            return False
        
        # Verify club structure
        for i, club in enumerate(data[:3]):  # Check first 3 clubs
            required_fields = ["id", "name"]
            missing_fields = [field for field in required_fields if field not in club]
            if missing_fields:
                self.log_test(
                    "clubs_endpoint",
                    False,
                    f"Club {i} missing required fields: {', '.join(missing_fields)}",
                    result["status_code"],
                    data
                )
                return False
        
        self.log_test(
            "clubs_endpoint",
            True,
            f"Retrieved {len(data)} clubs without _id fields",
            result["status_code"]
        )
        return True
    
    def test_leagues_endpoint(self):
        """Test GET /api/leagues"""
        print(f"\n=== Testing Leagues Endpoint ===")
        
        result = self.make_request("GET", "/leagues")
        
        if not result["success"]:
            self.log_test(
                "leagues_endpoint",
                False,
                f"Request failed with status {result['status_code']}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Check for _id fields
        id_fields = self.check_for_id_fields(result["data"])
        
        if id_fields:
            self.log_test(
                "leagues_endpoint",
                False,
                f"Found _id fields in response: {', '.join(id_fields)}",
                result["status_code"],
                result["data"]
            )
            return False
        
        # Verify response structure
        data = result["data"]
        
        if not isinstance(data, list):
            self.log_test(
                "leagues_endpoint",
                False,
                "Leagues should be a list",
                result["status_code"],
                data
            )
            return False
        
        # Check that we have leagues
        if len(data) == 0:
            self.log_test(
                "leagues_endpoint",
                False,
                "No leagues returned",
                result["status_code"],
                data
            )
            return False
        
        # Verify league structure
        for i, league in enumerate(data[:3]):  # Check first 3 leagues
            required_fields = ["id", "name"]
            missing_fields = [field for field in required_fields if field not in required_fields]
            if missing_fields:
                self.log_test(
                    "leagues_endpoint",
                    False,
                    f"League {i} missing required fields: {', '.join(missing_fields)}",
                    result["status_code"],
                    data
                )
                return False
        
        # Check if prem8 league is in the list
        prem8_found = any(league.get("id") == self.prem8_league_id for league in data)
        if not prem8_found:
            self.log_test(
                "leagues_endpoint",
                False,
                f"Prem8 league {self.prem8_league_id} not found in leagues list",
                result["status_code"],
                data
            )
            return False
        
        self.log_test(
            "leagues_endpoint",
            True,
            f"Retrieved {len(data)} leagues without _id fields (including prem8 league)",
            result["status_code"]
        )
        return True
    
    def run_all_tests(self):
        """Run all MongoDB serialization tests"""
        print("🚀 Starting MongoDB _id Serialization Tests for Prem8 League")
        print(f"Testing league ID: {self.prem8_league_id}")
        
        test_functions = [
            ("league_details", self.test_league_details),
            ("league_fixtures", self.test_league_fixtures),
            ("league_participants", self.test_league_participants),
            ("clubs_endpoint", self.test_clubs_endpoint),
            ("leagues_endpoint", self.test_leagues_endpoint),
        ]
        
        results = {}
        
        for test_name, test_func in test_functions:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} crashed: {str(e)}")
                self.log_test(test_name, False, f"Test crashed: {str(e)}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results):
        """Print test summary"""
        print("\n" + "="*60)
        print("MONGODB _ID SERIALIZATION TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All MongoDB serialization tests passed!")
            print("✅ No 500 Internal Server Errors")
            print("✅ No ObjectId serialization errors")
            print("✅ All responses are valid JSON")
            print("✅ Response data structure is correct")
            return True
        else:
            print("⚠️  Some MongoDB serialization tests failed")
            print("\nFailed tests details:")
            for test_name, result in results.items():
                if not result and test_name in self.test_results:
                    test_data = self.test_results[test_name]
                    print(f"\n❌ {test_name}:")
                    print(f"   Details: {test_data['details']}")
                    if test_data['response_code']:
                        print(f"   Response Code: {test_data['response_code']}")
            return False

def main():
    """Main test execution"""
    tester = MongoSerializationTester()
    results = tester.run_all_tests()
    success = tester.print_summary(results)
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)