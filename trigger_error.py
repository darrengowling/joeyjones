#!/usr/bin/env python3
"""
Try to trigger the token error to capture detailed logs
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def trigger_token_error():
    """Try different scenarios to trigger the token error"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TRIGGERING TOKEN ERROR FOR DEBUGGING ===")
        
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
        
        # Create a new user
        user_data = {"name": "Token Test User", "email": f"tokentest{hash('debug')%1000}@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user_result = await response.json()
            user_id = user_result["id"]
            print(f"Created user: {user_id}")
        
        # Test 1: Wrong token to see detailed error logs
        print("\n--- Test 1: Wrong token (should see detailed logs) ---")
        join_data_wrong = {
            "userId": user_id,
            "inviteToken": "wrongtoken"
        }
        
        async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_wrong) as response:
            print(f"Status: {response.status}")
            if response.status == 403:
                error = await response.json()
                print(f"Error: {error['detail']}")
            else:
                print(f"Unexpected: {await response.text()}")
        
        # Test 2: Correct token with extra whitespace
        print(f"\n--- Test 2: Token with whitespace ---")
        join_data_space = {
            "userId": user_id,
            "inviteToken": f" {lfc1_league['inviteToken']} "  # Extra spaces
        }
        
        async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_space) as response:
            print(f"Status: {response.status}")
            if response.status == 403:
                error = await response.json()
                print(f"Error: {error['detail']}")
                print("🔍 Found whitespace issue!")
            else:
                print(f"Response: {await response.text()}")
        
        # Test 3: Correct token exactly
        print(f"\n--- Test 3: Correct token exactly ---")
        join_data_correct = {
            "userId": user_id,
            "inviteToken": lfc1_league['inviteToken']
        }
        
        async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_correct) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Response: {response_text}")

if __name__ == "__main__":
    asyncio.run(trigger_token_error())