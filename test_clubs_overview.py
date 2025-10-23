#!/usr/bin/env python3
"""
Test the new clubs overview functionality
"""

import asyncio
import aiohttp

BASE_URL = "https://auction-buddy-8.preview.emergentagent.com/api"

async def test_clubs_overview():
    """Test the clubs overview endpoint"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING CLUBS OVERVIEW ===")
        
        # Find an existing auction to test with
        async with session.get(f"{BASE_URL}/leagues") as response:
            leagues = await response.json()
            
            active_league = None
            for league in leagues:
                if league.get("status") == "active":
                    active_league = league
                    break
            
            if not active_league:
                print("❌ No active leagues found")
                return
            
            print(f"✅ Found active league: {active_league['name']}")
        
        # Get auction info
        async with session.get(f"{BASE_URL}/leagues/{active_league['id']}/auction") as response:
            auction_info = await response.json()
            auction_id = auction_info["auctionId"]
            print(f"✅ Auction ID: {auction_id}")
        
        # Test the new clubs endpoint
        async with session.get(f"{BASE_URL}/auction/{auction_id}/clubs") as response:
            if response.status == 200:
                clubs_data = await response.json()
                
                print(f"\n📊 CLUBS OVERVIEW:")
                print(f"   Total Clubs: {clubs_data['totalClubs']}")
                print(f"   Sold: {clubs_data['soldClubs']}")
                print(f"   Unsold: {clubs_data['unsoldClubs']}")
                print(f"   Remaining: {clubs_data['remainingClubs']}")
                
                print(f"\n🏆 CLUB STATUS BREAKDOWN:")
                status_counts = {}
                for club in clubs_data['clubs']:
                    status = club['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    icon = {"current": "🔥", "upcoming": "⏳", "sold": "✅", "unsold": "❌"}.get(status, "❓")
                    print(f"   {icon} {status.title()}: {count}")
                
                # Show first few clubs as example
                print(f"\n📋 SAMPLE CLUBS:")
                for i, club in enumerate(clubs_data['clubs'][:5]):
                    icon = {"current": "🔥", "upcoming": "⏳", "sold": "✅", "unsold": "❌"}.get(club['status'], "❓")
                    lot_info = f"#{club['lotNumber']}" if club['lotNumber'] else "No lot"
                    bid_info = f" - £{club['winningBid']:,} to {club['winner']}" if club.get('winningBid') else ""
                    print(f"   {icon} {club['name']} ({lot_info}){bid_info}")
                
                print(f"✅ Clubs overview API working correctly!")
                
            else:
                error_text = await response.text()
                print(f"❌ Failed to get clubs: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_clubs_overview())