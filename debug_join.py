#!/usr/bin/env python3
"""
Test the exact scenario: joining lfc1 league with correct token bcf264bf
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def debug_join_issue():
    """Debug the exact join issue with correct token"""
    
    async with aiohttp.ClientSession() as session:
        print("=== DEBUGGING EXACT JOIN ISSUE ===")
        
        # Get the lfc1 league details
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
            
        print(f"League ID: {lfc1_league['id']}")
        print(f"League Name: '{lfc1_league['name']}'")
        print(f"League Token: '{lfc1_league['inviteToken']}'")
        print(f"Token Type: {type(lfc1_league['inviteToken'])}")
        print(f"Token Length: {len(lfc1_league['inviteToken'])}")
        print(f"Token Repr: {repr(lfc1_league['inviteToken'])}")
        
        # Create test user
        user_data = {"name": "Debug User", "email": f"debug{hash('test')%10000}@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            if response.status != 200:
                print(f"❌ Failed to create user: {await response.text()}")
                return
            user_result = await response.json()
            user_id = user_result["id"]
            print(f"Created user: {user_id}")
        
        # Try to join with exact token
        join_data = {
            "userId": user_id,
            "inviteToken": lfc1_league['inviteToken']  # Using exact token
        }
        
        print(f"\nJOIN REQUEST:")
        print(f"URL: {BASE_URL}/leagues/{lfc1_league['id']}/join")
        print(f"Payload: {json.dumps(join_data, indent=2)}")
        print(f"User ID: '{user_id}'")
        print(f"Token: '{join_data['inviteToken']}'")
        
        async with session.post(f"{BASE_URL}/leagues/{lfc1_league['id']}/join", json=join_data) as response:
            print(f"\nRESPONSE:")
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Body: {response_text}")
            
            if response.status == 403:
                print("❌ INVALID TOKEN ERROR CONFIRMED")
                
                # Let's check what the backend is actually comparing
                print(f"\nDEBUG INFO:")
                print(f"Expected token: '{lfc1_league['inviteToken']}'")
                print(f"Sent token: '{join_data['inviteToken']}'")
                print(f"Are they equal? {lfc1_league['inviteToken'] == join_data['inviteToken']}")
                print(f"Tokens (bytes): {lfc1_league['inviteToken'].encode()} vs {join_data['inviteToken'].encode()}")

if __name__ == "__main__":
    asyncio.run(debug_join_issue())