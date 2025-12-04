"""
Setup Test Auction for Load Testing
Creates a league, starts an auction, and returns the auction ID
"""
import requests
import sys
import time

BACKEND_URL = "https://leaguemaster-6.preview.emergentagent.com"
API = f"{BACKEND_URL}/api"

def create_test_user():
    """Create a test commissioner user"""
    email = f"loadtest_commissioner_{int(time.time())}@test.com"
    
    # Request magic link
    print(f"Creating commissioner user: {email}")
    response = requests.post(f"{API}/auth/magic-link", json={"email": email})
    
    if response.status_code != 200:
        print(f"❌ Failed to generate magic link: {response.text}")
        sys.exit(1)
    
    token = response.json()["token"]
    
    # Verify magic link
    response = requests.post(f"{API}/auth/verify-magic-link", json={
        "email": email,
        "token": token
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to verify magic link: {response.text}")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ Commissioner user created: {data['user']['id']}")
    return data["accessToken"], data["user"]["id"]

def create_test_league(access_token, user_id):
    """Create a test league for load testing"""
    print("\nCreating test league...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    league_data = {
        "name": f"Socket.IO Load Test {int(time.time())}",
        "sportKey": "football",
        "budget": 500000000,
        "minManagers": 2,
        "maxManagers": 50,  # Support up to 50 concurrent bidders
        "clubSlots": 3,
        "timerSeconds": 30,
        "antiSnipeSeconds": 10,
        "commissionerId": user_id
    }
    
    response = requests.post(f"{API}/leagues", json=league_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to create league: {response.text}")
        sys.exit(1)
    
    league = response.json()
    print(f"✅ League created: {league['id']}")
    print(f"   Invite Token: {league['inviteToken']}")
    return league["id"]

def start_auction(access_token, league_id):
    """Start an auction in the test league"""
    print("\nStarting auction...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{API}/leagues/{league_id}/auction/start", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to start auction: {response.text}")
        sys.exit(1)
    
    auction = response.json()
    print(f"Response: {auction}")
    auction_id = auction.get("auctionId")
    print(f"✅ Auction started: {auction_id}")
    print(f"   First Asset: {auction.get('firstAsset')}")
    return auction_id

def main():
    print("=" * 60)
    print("Socket.IO Load Test - Auction Setup")
    print("=" * 60)
    
    # Create commissioner
    access_token, user_id = create_test_user()
    
    # Create league
    league_id = create_test_league(access_token, user_id)
    
    # Start auction
    auction_id = start_auction(access_token, league_id)
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"\nTest Auction ID: {auction_id}")
    print(f"League ID: {league_id}")
    print("\nTo run the load test, execute:")
    print(f"export TEST_AUCTION_ID={auction_id}")
    print(f"export TEST_LEAGUE_ID={league_id}")
    print("./run_auction_test.sh")
    print("\n" + "=" * 60)
    
    # Write to file for easy sourcing
    with open("/app/tests/load/test_env.sh", "w") as f:
        f.write(f"export TEST_AUCTION_ID={auction_id}\n")
        f.write(f"export TEST_LEAGUE_ID={league_id}\n")
    
    print("\n✅ Environment variables written to: /app/tests/load/test_env.sh")
    print("   You can source it with: source /app/tests/load/test_env.sh")

if __name__ == "__main__":
    main()
