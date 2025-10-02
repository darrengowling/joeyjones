#!/usr/bin/env python3
"""
Test the new standardized timer events
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_new_timer_events():
    """Test the new timer event format"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING NEW TIMER EVENT FORMAT ===")
        
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
        
        print(f"Starting lot: {real_madrid['name']} ({club_id})")
        
        # Start a new lot manually
        start_url = f"{BASE_URL}/auction/{auction_id}/start-lot/{club_id}"
        async with session.post(start_url) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Lot started: {result}")
                
                print("\nMonitoring backend logs for new timer events...")
                print("Expected events: lot_started, tick (every 500ms)")
                print("Expected format: lotId, seq, endsAt (epoch ms), serverNow (epoch ms)")
                
                return True
            else:
                error = await response.text()
                print(f"❌ Failed to start lot: {error}")
                return False

if __name__ == "__main__":
    asyncio.run(test_new_timer_events())