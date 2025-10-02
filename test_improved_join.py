#!/usr/bin/env python3
"""
Test the improved join league functionality
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_improved_join():
    """Test improved join with better error messages"""
    
    async with aiohttp.ClientSession() as session:
        print("=== Testing Improved League Join ===")
        
        # Test new search endpoint
        print("\n--- Test 1: Search for 'lfc1' league ---")
        async with session.get(f"{BASE_URL}/leagues/search?name=lfc1") as response:
            if response.status == 200:
                results = await response.json()
                print(f"✅ Found {len(results)} leagues:")
                for league in results:
                    print(f"  - {league['name']}: token={league['inviteToken']}")
            else:
                print(f"❌ Search failed: {response.status}")
        
        # Test case-insensitive search
        print("\n--- Test 2: Case-insensitive search for 'LFC1' ---")
        async with session.get(f"{BASE_URL}/leagues/search?name=LFC1") as response:
            if response.status == 200:
                results = await response.json()
                print(f"✅ Found {len(results)} leagues (case-insensitive):")
                for league in results:
                    print(f"  - {league['name']}: token={league['inviteToken']}")
            else:
                print(f"❌ Case-insensitive search failed: {response.status}")
        
        # Create test user
        user_data = {"name": "Test User", "email": "test@example.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user_result = await response.json()
            user_id = user_result["id"]
            print(f"\n✅ Created test user: {user_id}")
        
        # Test improved error message
        print("\n--- Test 3: Improved error message when using wrong token ---")
        join_data = {
            "userId": user_id,
            "inviteToken": "lfc1"  # Wrong token (should be league name)
        }
        
        # Get the actual lfc1 league ID
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues = await response.json()
            lfc1_league = None
            for league in leagues:
                if league['name'].lower() == 'lfc1':
                    lfc1_league = league
                    break
        
        if lfc1_league:
            async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data) as response:
                print(f"Status: {response.status}")
                if response.status == 403:
                    error_response = await response.json()
                    print(f"✅ Improved error message: {error_response['detail']}")
                else:
                    text = await response.text()
                    print(f"Unexpected response: {text}")
        
        # Test correct token
        print("\n--- Test 4: Join with correct token ---")
        if lfc1_league:
            join_data_correct = {
                "userId": user_id,
                "inviteToken": lfc1_league['inviteToken']
            }
            
            async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_correct) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Successfully joined: {result['message']}")
                else:
                    text = await response.text()
                    print(f"❌ Failed: {text}")

if __name__ == "__main__":
    asyncio.run(test_improved_join())