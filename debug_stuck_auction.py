#!/usr/bin/env python3
"""
Debug the stuck lfc1 auction
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def debug_stuck_auction():
    """Debug the current state of lfc1 auction"""
    
    async with aiohttp.ClientSession() as session:
        print("=== DEBUGGING STUCK LFC1 AUCTION ===")
        
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
        
        league_id = lfc1_league['id']
        print(f"League ID: {league_id}")
        print(f"League Status: {lfc1_league['status']}")
        
        # Check if there's an auction
        async with session.get(f"{BASE_URL}/leagues/{league_id}/auction") as response:
            if response.status == 200:
                auction_info = await response.json()
                auction_id = auction_info.get('auctionId')
                print(f"Auction ID: {auction_id}")
                
                if auction_id:
                    # Get auction details
                    async with session.get(f"{BASE_URL}/auction/{auction_id}") as response:
                        if response.status == 200:
                            auction = await response.json()
                            print(f"\nAUCTION STATE:")
                            print(f"  Status: {auction.get('status', 'Unknown')}")
                            print(f"  Current Lot: {auction.get('currentLot', 'Unknown')}")
                            print(f"  Current Club ID: {auction.get('currentClubId', 'None')}")
                            print(f"  Timer Ends At: {auction.get('timerEndsAt', 'None')}")
                            
                            current_club = auction.get('currentClub')
                            if current_club:
                                print(f"  Current Club: {current_club['name']}")
                            else:
                                print(f"  Current Club: None - THIS IS THE PROBLEM!")
                            
                            print(f"  Bid Timer: {auction.get('bidTimer', 'Unknown')}s")
                            print(f"  Anti-Snipe: {auction.get('antiSnipeSeconds', 'Unknown')}s")
                        else:
                            print(f"❌ Could not get auction details: {response.status}")
                else:
                    print("❌ No auction ID found")
            else:
                print(f"❌ Could not get auction info: {response.status}")
        
        # Check available clubs
        async with session.get(f"{BASE_URL}/clubs") as response:
            if response.status == 200:
                clubs = await response.json()
                print(f"\nAVAILABLE CLUBS: {len(clubs)}")
                if len(clubs) == 0:
                    print("🚨 NO CLUBS IN DATABASE - THIS IS THE PROBLEM!")
                    print("Need to seed clubs first!")
            else:
                print(f"❌ Could not get clubs: {response.status}")

if __name__ == "__main__":
    asyncio.run(debug_stuck_auction())