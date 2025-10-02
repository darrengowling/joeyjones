#!/usr/bin/env python3
"""
Real-time debug of current lfc1 auction state
"""

import asyncio
import aiohttp
from datetime import datetime

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def realtime_debug():
    """Check exactly what's happening right now"""
    
    async with aiohttp.ClientSession() as session:
        print("=== REAL-TIME LFC1 AUCTION DEBUG ===")
        
        # Get lfc1 league
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues = await response.json()
            lfc1_league = None
            for league in leagues:
                if league['name'].lower() == 'lfc1':
                    lfc1_league = league
                    break
        
        if not lfc1_league:
            print("❌ No lfc1 league found")
            return
        
        # Get auction details
        async with session.get(f"{BASE_URL}/leagues/{lfc1_league['id']}/auction") as response:
            auction_info = await response.json()
            auction_id = auction_info['auctionId']
        
        # Get full auction state
        async with session.get(f"{BASE_URL}/auction/{auction_id}") as response:
            auction = await response.json()
            
            print(f"Auction ID: {auction_id}")
            print(f"Status: {auction.get('status', 'unknown')}")
            print(f"Current Lot: {auction.get('currentLot', 'unknown')}")
            print(f"Timer Ends At: {auction.get('timerEndsAt', 'None')}")
            
            if auction.get('timerEndsAt'):
                # Check if timer has expired
                from datetime import datetime
                import dateutil.parser
                try:
                    end_time = dateutil.parser.parse(auction['timerEndsAt'])
                    now = datetime.now(end_time.tzinfo)
                    seconds_remaining = (end_time - now).total_seconds()
                    print(f"Seconds remaining: {seconds_remaining}")
                    
                    if seconds_remaining <= 0:
                        print("🚨 TIMER HAS EXPIRED - LOT SHOULD HAVE COMPLETED!")
                    else:
                        print(f"✅ Timer still running: {int(seconds_remaining)}s left")
                except Exception as e:
                    print(f"Error parsing timer: {e}")
            
            current_club = auction.get('currentClub')
            if current_club:
                print(f"Current Club: {current_club['name']}")
            else:
                print("Current Club: None")
            
            # Check bids for current lot
            if auction.get('currentClubId'):
                print(f"Checking bids for club {auction['currentClubId']}...")
                # This endpoint might not exist, but let's try
                try:
                    bids_url = f"{BASE_URL}/auction/{auction_id}/bids"
                    async with session.get(bids_url) as bids_response:
                        if bids_response.status == 200:
                            bids = await bids_response.json()
                            print(f"Current bids: {len(bids)}")
                        else:
                            print("Could not get bids")
                except:
                    print("Bids endpoint not available")

if __name__ == "__main__":
    asyncio.run(realtime_debug())