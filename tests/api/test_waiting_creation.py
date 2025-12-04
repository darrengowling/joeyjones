#!/usr/bin/env python3
"""
Prompt F - Test 1: Waiting Room Creation
Verifies auction is created in waiting state with correct initial values
"""

import pytest
import httpx
import asyncio
import uuid

BASE_URL = "https://leaguemaster-6.preview.emergentagent.com/api"

@pytest.mark.asyncio
async def test_waiting_room_creation():
    """
    Test that auction is created in waiting state with correct initial values
    """
    print("\n" + "=" * 60)
    print("Test 1: Waiting Room Creation")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Create test users
        print("\n1️⃣ Creating test users...")
        user1_data = {
            "name": f"WaitingTest_User1_{uuid.uuid4().hex[:6]}",
            "email": f"waiting1_{uuid.uuid4().hex[:6]}@test.com"
        }
        response = await client.post(f"{BASE_URL}/users", json=user1_data)
        assert response.status_code == 200, f"Failed to create user1: {response.text}"
        user1 = response.json()
        print(f"   ✅ User 1: {user1['name']} ({user1['id'][:8]}...)")
        
        user2_data = {
            "name": f"WaitingTest_User2_{uuid.uuid4().hex[:6]}",
            "email": f"waiting2_{uuid.uuid4().hex[:6]}@test.com"
        }
        response = await client.post(f"{BASE_URL}/users", json=user2_data)
        assert response.status_code == 200, f"Failed to create user2: {response.text}"
        user2 = response.json()
        print(f"   ✅ User 2: {user2['name']} ({user2['id'][:8]}...)")
        
        # Step 2: Create league
        print("\n2️⃣ Creating league...")
        league_data = {
            "name": f"Waiting Room Test {uuid.uuid4().hex[:6]}",
            "sportKey": "football",
            "commissionerId": user1["id"],
            "budget": 200000000,
            "minManagers": 2,
            "maxManagers": 2,
            "clubSlots": 3,
            "timerSeconds": 20,
            "antiSnipeSeconds": 5
        }
        response = await client.post(f"{BASE_URL}/leagues", json=league_data)
        assert response.status_code == 200, f"Failed to create league: {response.text}"
        league = response.json()
        league_id = league["id"]
        print(f"   ✅ League: {league['name']} ({league_id[:8]}...)")
        
        # Step 3: User 2 joins league
        print("\n3️⃣ User 2 joining league...")
        invite_token = league["inviteToken"]
        join_data = {
            "userId": user2["id"],
            "displayName": user2["name"],
            "inviteToken": invite_token
        }
        response = await client.post(f"{BASE_URL}/leagues/{league_id}/join", json=join_data)
        assert response.status_code == 200, f"Failed to join league: {response.text}"
        print(f"   ✅ User 2 joined league")
        
        # Step 4: Start auction
        print("\n4️⃣ Starting auction (should create in waiting state)...")
        response = await client.post(f"{BASE_URL}/leagues/{league_id}/auction/start")
        assert response.status_code == 200, f"Failed to start auction: {response.text}"
        start_response = response.json()
        
        print(f"\n   📋 Start Response:")
        print(f"      auctionId: {start_response.get('auctionId', 'N/A')[:8]}...")
        print(f"      status: {start_response.get('status', 'N/A')}")
        
        # ASSERT: Returns status="waiting"
        assert "auctionId" in start_response, "Response missing auctionId"
        assert start_response["status"] == "waiting", f"Expected status='waiting', got '{start_response['status']}'"
        print(f"   ✅ Auction returned status='waiting'")
        
        auction_id = start_response["auctionId"]
        
        # Step 5: Get auction details
        print("\n5️⃣ Fetching auction details...")
        response = await client.get(f"{BASE_URL}/auction/{auction_id}")
        assert response.status_code == 200, f"Failed to get auction: {response.text}"
        auction_data = response.json()
        auction = auction_data.get("auction", {})
        
        print(f"\n   📋 Auction State:")
        print(f"      status: {auction.get('status')}")
        print(f"      currentLot: {auction.get('currentLot')}")
        print(f"      currentClubId: {auction.get('currentClubId')}")
        print(f"      timerEndsAt: {auction.get('timerEndsAt')}")
        print(f"      clubQueue length: {len(auction.get('clubQueue', []))}")
        
        # ASSERT: currentLot == 0
        assert auction.get("currentLot") == 0, f"Expected currentLot=0, got {auction.get('currentLot')}"
        print(f"   ✅ currentLot == 0")
        
        # ASSERT: currentClubId is null
        assert auction.get("currentClubId") is None, f"Expected currentClubId=None, got {auction.get('currentClubId')}"
        print(f"   ✅ currentClubId is null")
        
        # ASSERT: timerEndsAt is null
        assert auction.get("timerEndsAt") is None, f"Expected timerEndsAt=None, got {auction.get('timerEndsAt')}"
        print(f"   ✅ timerEndsAt is null")
        
        # ASSERT: clubQueue is populated
        assert len(auction.get("clubQueue", [])) > 0, "clubQueue should be populated"
        print(f"   ✅ clubQueue populated ({len(auction.get('clubQueue', []))} clubs)")
        
        # Step 6: Get league state
        print("\n6️⃣ Getting league state...")
        response = await client.get(f"{BASE_URL}/leagues/{league_id}/state")
        assert response.status_code == 200, f"Failed to get league state: {response.text}"
        state = response.json()
        
        print(f"\n   📋 League State:")
        print(f"      leagueId: {state.get('leagueId', 'N/A')[:8]}...")
        print(f"      status: {state.get('status')}")
        print(f"      activeAuctionId: {state.get('activeAuctionId', 'N/A')[:8] if state.get('activeAuctionId') else 'None'}...")
        
        # ASSERT: Shows auctionId
        assert state.get("activeAuctionId") == auction_id, "League state should show active auction ID"
        print(f"   ✅ League state shows activeAuctionId")
        
        # ASSERT: Status is active (league status, not auction status)
        assert state.get("status") == "active", f"Expected league status='active', got '{state.get('status')}'"
        print(f"   ✅ League status is 'active' (has auction)")
        
        print("\n" + "=" * 60)
        print("✅ ALL ASSERTIONS PASSED")
        print("=" * 60)
        print("\nTest Summary:")
        print(f"  - Auction created in waiting state ✓")
        print(f"  - currentLot = 0 ✓")
        print(f"  - currentClubId = null ✓")
        print(f"  - timerEndsAt = null ✓")
        print(f"  - clubQueue populated ✓")
        print(f"  - League state shows auction ✓")
        
        return True

if __name__ == "__main__":
    result = asyncio.run(test_waiting_room_creation())
    exit(0 if result else 1)
