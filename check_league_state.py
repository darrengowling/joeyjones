#!/usr/bin/env python3
"""
Check current state of lfc1 league - participants, capacity, etc.
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def check_league_state():
    """Check current state of lfc1 league"""
    
    async with aiohttp.ClientSession() as session:
        print("=== CHECKING LFC1 LEAGUE STATE ===")
        
        # Find lfc1 league
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues = await response.json()
            lfc1_league = None
            for league in leagues:
                if league['name'].lower() == 'lfc1':
                    lfc1_league = league
                    break
        
        if not lfc1_league:
            print("❌ lfc1 league not found")
            return
            
        print(f"League: {lfc1_league['name']}")
        print(f"ID: {lfc1_league['id']}")  
        print(f"Token: {lfc1_league['inviteToken']}")
        print(f"Budget: ${lfc1_league['budget']}")
        print(f"Min Managers: {lfc1_league['minManagers']}")
        print(f"Max Managers: {lfc1_league['maxManagers']}")
        print(f"Status: {lfc1_league['status']}")
        
        # Get participants
        league_id = lfc1_league['id']
        async with session.get(f"{BASE_URL}/leagues/{league_id}/participants") as response:
            if response.status == 200:
                participants = await response.json()
                print(f"\nCurrent Participants: {len(participants)}/{lfc1_league['maxManagers']}")
                for i, participant in enumerate(participants, 1):
                    print(f"  {i}. {participant['userName']} ({participant['userEmail']})")
                    print(f"     User ID: {participant['userId']}")
                
                if len(participants) >= lfc1_league['maxManagers']:
                    print("🚨 LEAGUE IS FULL - This would cause join failures!")
            else:
                print(f"❌ Could not get participants: {response.status}")
        
        # Test join with a new user to see current behavior
        print(f"\n=== TESTING JOIN WITH NEW USER ===")
        user_data = {"name": "Test Join User", "email": f"testjoin{hash('user')%1000}@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            if response.status != 200:
                print(f"❌ Failed to create test user")
                return
            user_result = await response.json()
            test_user_id = user_result["id"]
            print(f"Created test user: {test_user_id}")
        
        # Try to join
        join_data = {
            "userId": test_user_id,
            "inviteToken": lfc1_league['inviteToken']
        }
        
        async with session.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data) as response:
            print(f"Join attempt status: {response.status}")
            response_text = await response.text()
            print(f"Response: {response_text}")
            
            if response.status == 403:
                print("🚨 CONFIRMED: Invalid token error occurring")
            elif response.status == 400:
                print("🚨 LEAGUE MIGHT BE FULL or other validation error")
            elif response.status == 200:
                print("✅ Join successful - no token issue")

if __name__ == "__main__":
    asyncio.run(check_league_state())