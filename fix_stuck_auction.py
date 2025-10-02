#!/usr/bin/env python3
"""
Fix the stuck lfc1 auction by manually starting the first lot
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def fix_stuck_auction():
    """Fix the stuck auction by manually triggering the first lot"""
    
    async with aiohttp.ClientSession() as session:
        print("=== FIXING STUCK LFC1 AUCTION ===")
        
        # Get lfc1 league auction info
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
        
        league_id = lfc1_league['id']
        
        # Get auction ID
        async with session.get(f"{BASE_URL}/leagues/{league_id}/auction") as response:
            if response.status != 200:
                print(f"❌ Could not get auction: {response.status}")
                return
                
            auction_info = await response.json()
            auction_id = auction_info.get('auctionId')
            
            if not auction_id:
                print("❌ No auction ID found")
                return
        
        print(f"Auction ID: {auction_id}")
        
        # Get first available club
        async with session.get(f"{BASE_URL}/clubs") as response:
            if response.status != 200:
                print(f"❌ Could not get clubs: {response.status}")
                return
                
            clubs = await response.json()
            if not clubs:
                print("❌ No clubs available")
                return
            
            # Use first club
            first_club = clubs[0]
            club_id = first_club['id']
            print(f"Starting first lot with: {first_club['name']}")
        
        # Try to start the first lot manually
        start_lot_url = f"{BASE_URL}/auction/{auction_id}/start-lot/{club_id}"
        print(f"Calling: {start_lot_url}")
        
        async with session.post(start_lot_url) as response:
            print(f"Start lot status: {response.status}")
            response_text = await response.text()
            print(f"Response: {response_text}")
            
            if response.status == 200:
                print("✅ Successfully started first lot!")
                print("The auction should now be working with timer countdown!")
            else:
                print("❌ Failed to start first lot")
                print(f"Error: {response_text}")

if __name__ == "__main__":
    asyncio.run(fix_stuck_auction())