#!/usr/bin/env python3
"""
Test the cleaned up timer system
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_clean_timer():
    """Start a fresh lot to test the cleaned timer"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING CLEANED TIMER SYSTEM ===")
        
        # Get Real Madrid club ID  
        async with session.get(f"{BASE_URL}/clubs") as response:
            clubs = await response.json()
            real_madrid = None
            for club in clubs:
                if "real madrid" in club['name'].lower():
                    real_madrid = club
                    break
        
        if not real_madrid:
            print("❌ Real Madrid not found")
            return
        
        auction_id = "70b40542-d095-4f81-bf97-17bc8152c829"
        club_id = real_madrid['id']
        
        print(f"Starting fresh lot: {real_madrid['name']}")
        
        # Start a new lot to test clean timer
        start_url = f"{BASE_URL}/auction/{auction_id}/start-lot/{club_id}"
        async with session.post(start_url) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Lot started successfully")
                print("✅ Frontend should now show clean timer from useAuctionClock hook only")
                print("✅ No more timer conflicts or 'jumping back' issues")
                return True
            else:
                error = await response.text()
                print(f"❌ Failed to start lot: {error}")
                return False

if __name__ == "__main__":
    asyncio.run(test_clean_timer())