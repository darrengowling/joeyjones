#!/usr/bin/env python3
"""
Debug script to check specific cricket scoring configuration issues
"""

import requests
import json

BASE_URL = "https://sporty-ui.preview.emergentagent.com/api"

def test_validation_errors():
    # Create test user and cricket league
    user_data = {"name": "Debug User", "email": "debug@test.com"}
    user_result = requests.post(f"{BASE_URL}/users", json=user_data)
    user_id = user_result.json()["id"]
    
    league_data = {
        "name": "Debug Cricket League",
        "commissionerId": user_id,
        "budget": 50000000.0,
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3,
        "sportKey": "cricket"
    }
    
    league_result = requests.post(f"{BASE_URL}/leagues", json=league_data)
    league_id = league_result.json()["id"]
    
    print(f"Created league: {league_id}")
    
    # Test 1: Missing rules validation
    print("\n=== Testing Missing Rules Validation ===")
    invalid_overrides = {
        "scoringOverrides": {
            "rules": {
                "run": 2,
                "wicket": 30
                # Missing catch, stumping, runOut
            }
        }
    }
    
    response = requests.put(f"{BASE_URL}/leagues/{league_id}/scoring-overrides", json=invalid_overrides)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 2: Non-cricket league
    print("\n=== Testing Non-Cricket League ===")
    football_league_data = {
        "name": "Debug Football League",
        "commissionerId": user_id,
        "budget": 50000000.0,
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3,
        "sportKey": "football"
    }
    
    football_result = requests.post(f"{BASE_URL}/leagues", json=football_league_data)
    football_league_id = football_result.json()["id"]
    
    scoring_overrides = {
        "scoringOverrides": {
            "rules": {
                "run": 2,
                "wicket": 30,
                "catch": 15,
                "stumping": 20,
                "runOut": 25
            }
        }
    }
    
    response = requests.put(f"{BASE_URL}/leagues/{football_league_id}/scoring-overrides", json=scoring_overrides)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 3: Custom scoring application
    print("\n=== Testing Custom Scoring Application ===")
    
    # Set custom overrides
    custom_overrides = {
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
                    "threshold": 50,
                    "points": 15
                },
                "century": {
                    "enabled": False,
                    "threshold": 100,
                    "points": 50
                },
                "fiveWicketHaul": {
                    "enabled": True,
                    "threshold": 5,
                    "points": 40
                }
            }
        }
    }
    
    response = requests.put(f"{BASE_URL}/leagues/{league_id}/scoring-overrides", json=custom_overrides)
    print(f"Override Status: {response.status_code}")
    
    # Upload CSV
    csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match1,player1,25,1,1,0,0"""
    
    files = {'file': ('test.csv', csv_data, 'text/csv')}
    response = requests.post(f"{BASE_URL}/scoring/{league_id}/ingest", files=files)
    print(f"Ingest Status: {response.status_code}")
    print(f"Ingest Response: {response.text}")
    
    # Get leaderboard
    response = requests.get(f"{BASE_URL}/scoring/{league_id}/leaderboard")
    print(f"Leaderboard Status: {response.status_code}")
    print(f"Leaderboard Response: {response.text}")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/leagues/{league_id}")
    requests.delete(f"{BASE_URL}/leagues/{football_league_id}")

if __name__ == "__main__":
    test_validation_errors()