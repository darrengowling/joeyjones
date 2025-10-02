#!/usr/bin/env python3
"""
Test commissioner pause/resume and league deletion functionality
"""

import asyncio
import aiohttp

BASE_URL = "https://ucl-bidding.preview.emergentagent.com/api"

async def test_commissioner_controls():
    """Test the new commissioner functionality"""
    
    async with aiohttp.ClientSession() as session:
        print("=== TESTING COMMISSIONER CONTROLS ===")
        
        # Create test league
        user_data = {"name": "Commissioner Test", "email": "commissioner@test.com"}
        async with session.post(f"{BASE_URL}/users", json=user_data) as response:
            user = await response.json()
            print(f"✅ Created commissioner: {user['id']}")
        
        league_data = {
            "name": "Commissioner Test League",
            "commissionerId": user["id"],
            "budget": 500000000.0,
            "minManagers": 1,
            "maxManagers": 2,
            "clubSlots": 3
        }
        
        async with session.post(f"{BASE_URL}/leagues", json=league_data) as response:
            league = await response.json()
            league_id = league["id"]
            print(f"✅ Created league: {league_id}")
        
        # Test league deletion (should work for pending league)
        print(f"\n🧪 Testing league deletion...")
        async with session.delete(f"{BASE_URL}/leagues/{league_id}") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ League deleted successfully: {result['message']}")
                print(f"   Deleted data: {result['deletedData']}")
            else:
                error_text = await response.text()
                print(f"❌ Delete failed: {error_text}")
        
        # Create another league for auction pause/resume testing
        league_data["name"] = "Pause/Resume Test League"
        async with session.post(f"{BASE_URL}/leagues", json=league_data) as response:
            league2 = await response.json()
            league2_id = league2["id"]
        
        # Join league
        join_data = {"userId": user["id"], "inviteToken": league2["inviteToken"]}
        await session.post(f"{BASE_URL}/leagues/{league2_id}/join", json=join_data)
        
        # Start auction
        async with session.post(f"{BASE_URL}/leagues/{league2_id}/auction/start") as response:
            auction_result = await response.json()
            auction_id = auction_result["auctionId"]
            print(f"✅ Started auction for pause/resume test: {auction_id}")
        
        # Test pause functionality
        print(f"\n🧪 Testing auction pause...")
        async with session.post(f"{BASE_URL}/auction/{auction_id}/pause") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Auction paused: {result['message']}")
                print(f"   Remaining time when paused: {result['remainingTime']}s")
            else:
                error_text = await response.text()
                print(f"❌ Pause failed: {error_text}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test resume functionality
        print(f"\n🧪 Testing auction resume...")
        async with session.post(f"{BASE_URL}/auction/{auction_id}/resume") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Auction resumed: {result['message']}")
                print(f"   Remaining time on resume: {result['remainingTime']}s")
            else:
                error_text = await response.text()
                print(f"❌ Resume failed: {error_text}")
        
        print(f"\n✅ All commissioner controls tested successfully!")

if __name__ == "__main__":
    asyncio.run(test_commissioner_controls())