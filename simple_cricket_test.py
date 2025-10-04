#!/usr/bin/env python3
"""
Simple cricket scoring test to debug the issue
"""

import requests
import json

BASE_URL = "https://uefa-auction-hub.preview.emergentagent.com/api"

def simple_test():
    # Create test user and cricket league
    user_data = {"name": "Simple User", "email": "simple@test.com"}
    user_result = requests.post(f"{BASE_URL}/users", json=user_data)
    user_id = user_result.json()["id"]
    
    league_data = {
        "name": "Simple Cricket League",
        "commissionerId": user_id,
        "budget": 50000000.0,
        "minManagers": 2,
        "maxManagers": 4,
        "clubSlots": 3,
        "sportKey": "cricket"
    }
    
    league_result = requests.post(f"{BASE_URL}/leagues", json=league_data)
    league_id = league_result.json()["id"]
    
    # Join league
    join_data = {
        "userId": user_id,
        "inviteToken": league_result.json()["inviteToken"]
    }
    requests.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
    
    print(f"Created league: {league_id}")
    
    # Set custom overrides (exactly like the failing test)
    custom_overrides = {
        "scoringOverrides": {
            "rules": {
                "run": 2,      # 2 points per run (default is 1)
                "wicket": 30,  # 30 points per wicket (default is 25)
                "catch": 15,   # 15 points per catch (default is 10)
                "stumping": 20,
                "runOut": 25
            },
            "milestones": {
                "halfCentury": {
                    "enabled": True,
                    "threshold": 50,
                    "points": 15   # 15 points for half-century (custom)
                },
                "century": {
                    "enabled": False,  # Disabled
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
    if response.status_code != 200:
        print(f"Override Error: {response.text}")
        return
    
    # Upload CSV (exactly like the failing test)
    csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match1,player1,25,1,1,0,0
match1,player2,75,0,2,1,0
match1,player3,100,2,0,0,1"""
    
    files = {'file': ('test_cricket_data.csv', csv_data, 'text/csv')}
    response = requests.post(f"{BASE_URL}/scoring/{league_id}/ingest", files=files)
    print(f"Ingest Status: {response.status_code}")
    print(f"Ingest Response: {response.text}")
    
    if response.status_code != 200:
        print("Ingest failed!")
        return
    
    # Get leaderboard
    response = requests.get(f"{BASE_URL}/scoring/{league_id}/leaderboard")
    print(f"Leaderboard Status: {response.status_code}")
    print(f"Leaderboard Response: {response.text}")
    
    leaderboard_data = response.json()
    leaderboard = leaderboard_data.get("leaderboard", [])
    
    print(f"Leaderboard entries: {len(leaderboard)}")
    for entry in leaderboard:
        print(f"  {entry['playerExternalId']}: {entry['totalPoints']} points")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/leagues/{league_id}")

if __name__ == "__main__":
    simple_test()