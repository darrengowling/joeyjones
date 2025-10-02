#!/usr/bin/env python3
"""
Test script to reproduce the league join token issue
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_league_join_issue():
    """Test league joining with token 'lfc1'"""
    
    async with aiohttp.ClientSession() as session:
        print("=== Testing League Join Issue ===")
        
        # First, let's see if there are any existing leagues
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues_result = await response.json()
            print(f"Existing leagues: {len(leagues_result)}")
            
            for league in leagues_result:
                print(f"  - {league['name']} | Token: {league['inviteToken']} | ID: {league['id']}")
                
                if league['inviteToken'].lower() == 'lfc1':
                    print(f"  ⚠️  Found league with token 'lfc1': {league['name']}")
        
        # Check if there's a league with token 'lfc1' (case insensitive)
        lfc1_league = None
        for league in leagues_result:
            if league['inviteToken'].lower() == 'lfc1':
                lfc1_league = league
                break
        
        if not lfc1_league:
            print("❌ No league found with token 'lfc1'")
            print("Creating a test league with token 'lfc1'...")
            
            # Create a user first
            user_data = {"name": "League Owner", "email": "owner@test.com"}
            async with session.post(f"{BASE_URL}/users", json=user_data) as response:
                user_result = await response.json()
                owner_id = user_result["id"]
                print(f"✅ Created owner user: {owner_id}")
            
            # Create league
            league_data = {
                "name": "LFC Test League",
                "commissionerId": owner_id,
                "budget": 1000.0,
                "minManagers": 2,
                "maxManagers": 8,
                "clubSlots": 3
            }
            async with session.post(f"{BASE_URL}/leagues", json=league_data) as response:
                if response.status != 200:
                    print(f"❌ Failed to create league: {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
                    return
                
                league_result = await response.json()
                print(f"✅ Created league: {league_result['name']}")
                print(f"   Token: {league_result['inviteToken']}")
                print(f"   ID: {league_result['id']}")
                
                # Update the league's invite token to 'lfc1' directly in database if needed
                # For now, let's use the auto-generated token
                lfc1_league = league_result
        
        print(f"\n=== Testing Join with League: {lfc1_league['name']} ===")
        print(f"League ID: {lfc1_league['id']}")
        print(f"Actual Token: {lfc1_league['inviteToken']}")
        
        # Create a second user to test joining
        user2_data = {"name": "Second User", "email": "second@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user2_data) as response:
            user2_result = await response.json()
            user2_id = user2_result["id"]
            print(f"✅ Created second user: {user2_id}")
        
        # Test 1: Join with correct token
        print(f"\n--- Test 1: Join with correct token '{lfc1_league['inviteToken']}' ---")
        join_data = {
            "userId": user2_id,
            "inviteToken": lfc1_league['inviteToken']
        }
        
        async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                result = await response.json()
                print(f"✅ Success: {result['message']}")
            else:
                text = await response.text()
                print(f"❌ Failed: {text}")
        
        # Test 2: Join with 'lfc1' token if different
        if lfc1_league['inviteToken'].lower() != 'lfc1':
            print(f"\n--- Test 2: Join with 'lfc1' token ---")
            join_data_lfc1 = {
                "userId": user2_id,
                "inviteToken": "lfc1"
            }
            
            async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_lfc1) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Success: {result['message']}")
                else:
                    text = await response.text()
                    print(f"❌ Failed: {text}")
        
        # Test 3: Case sensitivity test
        if lfc1_league['inviteToken'] != lfc1_league['inviteToken'].lower():
            print(f"\n--- Test 3: Case sensitivity test ---")
            join_data_lower = {
                "userId": user2_id,
                "inviteToken": lfc1_league['inviteToken'].lower()
            }
            
            async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data_lower) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Success with lowercase: {result['message']}")
                else:
                    text = await response.text()
                    print(f"❌ Failed with lowercase: {text}")

if __name__ == "__main__":
    asyncio.run(test_league_join_issue())