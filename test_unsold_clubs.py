#!/usr/bin/env python3
"""
Test the new unsold club queue functionality
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_unsold_club_system():
    """Test the unsold club queue and minimum budget system"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING UNSOLD CLUB QUEUE SYSTEM ===")
        
        # Clean and setup fresh environment
        await session.post(f"{BASE_URL}/clubs/seed")
        
        # Create test league with high budget
        user_data = {"name": "Unsold Test Commissioner", "email": "unsold@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user = await response.json()
        
        league_data = {
            "name": "Unsold Test League",
            "commissionerId": user["id"],
            "budget": 500000000.0,  # £500m budget (new default)
            "minManagers": 1,
            "maxManagers": 2,
            "clubSlots": 3
        }
        
        async with session.post(f"{BASE_URL}/leagues", json=league_data) as response:
            league = await response.json()
            print(f"✅ Created league with £{league['budget']:,} budget")
        
        # Join league
        join_data = {"userId": user["id"], "inviteToken": league["inviteToken"]}
        await session.post(f"{BASE_URL}/leagues/{league['id']}/join", json=join_data)
        
        # Start auction
        async with session.post(f"{BASE_URL}/leagues/{league['id']}/auction/start") as response:
            auction_result = await response.json()
            auction_id = auction_result["auctionId"]
            print(f"✅ Started auction: {auction_id}")
        
        # Get auction details to verify new fields
        async with session.get(f"{BASE_URL}/auction/{auction_id}") as response:
            auction_details = await response.json()
            auction = auction_details["auction"]
            
            print(f"✅ Auction fields:")
            print(f"   Club Queue Length: {len(auction.get('clubQueue', []))}")
            print(f"   Unsold Clubs: {len(auction.get('unsoldClubs', []))}")
            print(f"   Minimum Budget: £{auction.get('minimumBudget', 0):,}")
            print(f"   Current Club: {auction_details['currentClub']['name'] if auction_details.get('currentClub') else 'None'}")
        
        # Test completion of lot without bids (should mark as unsold)
        print(f"\n🧪 Testing unsold club functionality...")
        print(f"   Current club will go unsold (no bids placed)")
        print(f"   Should be moved to unsold queue and next club offered")
        
        return auction_id

if __name__ == "__main__":
    asyncio.run(test_unsold_club_system())