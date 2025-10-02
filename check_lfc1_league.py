#!/usr/bin/env python3
"""
Check the specific 'lfc1' league details
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def check_lfc1_league():
    """Check details of the lfc1 league"""
    
    async with aiohttp.ClientSession() as session:
        print("=== Checking LFC1 League Details ===")
        
        # Get all leagues
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues_result = await response.json()
            
            # Find the lfc1 league
            lfc1_league = None
            for league in leagues_result:
                if league['name'].lower() == 'lfc1':
                    lfc1_league = league
                    break
            
            if not lfc1_league:
                print("❌ No league found with name 'lfc1'")
                return
            
            print(f"✅ Found LFC1 League:")
            print(f"   Name: {lfc1_league['name']}")
            print(f"   Invite Token: {lfc1_league['inviteToken']}")
            print(f"   League ID: {lfc1_league['id']}")
            print(f"   Budget: ${lfc1_league['budget']}")
            print(f"   Managers: {lfc1_league['minManagers']}-{lfc1_league['maxManagers']}")
            
            # Check current participants
            league_id = lfc1_league['id']
            async with session.get(f"{BASE_URL}/leagues/{league_id}/participants") as response:
                if response.status == 200:
                    participants = await response.json()
                    print(f"   Current Participants: {len(participants)}")
                    for i, participant in enumerate(participants, 1):
                        print(f"     {i}. {participant['userName']} ({participant['userEmail']})")
                else:
                    print("   Could not fetch participants")
            
            print(f"\n🎯 **CORRECT INVITE TOKEN FOR 'lfc1' LEAGUE: {lfc1_league['inviteToken']}**")
            print(f"   Users should use '{lfc1_league['inviteToken']}' not 'lfc1' to join!")

if __name__ == "__main__":
    asyncio.run(check_lfc1_league())