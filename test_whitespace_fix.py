#!/usr/bin/env python3
"""
Test the whitespace fix
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_whitespace_fix():
    """Test that whitespace is now handled correctly"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING WHITESPACE FIX ===")
        
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
        user_data = {"name": "Whitespace Test User", "email": f"whitespace{hash('fix')%1000}@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user_result = await response.json()
            user_id = user_result["id"]
            print(f"Created user: {user_id}")
        
        # Test various whitespace scenarios
        test_cases = [
            f" {lfc1_league['inviteToken']}",      # Leading space
            f"{lfc1_league['inviteToken']} ",      # Trailing space  
            f" {lfc1_league['inviteToken']} ",     # Both spaces
            f"  {lfc1_league['inviteToken']}  ",   # Multiple spaces
            f"\t{lfc1_league['inviteToken']}\n",   # Tab and newline
            lfc1_league['inviteToken'],            # Exact (should work)
        ]
        
        for i, token_with_whitespace in enumerate(test_cases, 1):
            print(f"\n--- Test {i}: Token='{repr(token_with_whitespace)}' ---")
            
            # Create new user for each test  
            user_data = {"name": f"Test User {i}", "email": f"test{i}{hash(token_with_whitespace)%100}@test.com"}
            async with session.post(f"{BASE_URL}/users", json=user_data) as response:
                test_user = await response.json()
                test_user_id = test_user["id"]
            
            join_data = {
                "userId": test_user_id,
                "inviteToken": token_with_whitespace
            }
            
            async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ SUCCESS: {result['message']}")
                else:
                    error = await response.text()
                    print(f"❌ FAILED: {error}")

if __name__ == "__main__":
    asyncio.run(test_whitespace_fix())