#!/usr/bin/env python3
"""
Force restart the Real Madrid lot with proper timer
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def force_restart_lot():
    """Force restart the current lot with timer"""
    
    async with aiohttp.ClientSession() as session:
        print("=== FORCE RESTARTING REAL MADRID LOT ===")
        
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
        
        print(f"Restarting lot: {real_madrid['name']} ({club_id})")
        
        # Force start this lot
        start_url = f"{BASE_URL}/auction/{auction_id}/start-lot/{club_id}"
        async with session.post(start_url) as response:
            print(f"Restart status: {response.status}")
            result = await response.text()
            print(f"Result: {result}")
            
            if response.status == 200:
                print("✅ Lot restarted successfully!")
                print("Timer should now be working!")
            else:
                print("❌ Failed to restart lot")

if __name__ == "__main__":
    asyncio.run(force_restart_lot())