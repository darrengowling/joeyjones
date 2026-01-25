#!/usr/bin/env python3
"""
Integration test for assetsSelected API endpoints
Tests real API calls to verify Prompt 1 implementation
"""
import requests
import json
import sys

BACKEND_URL = "https://fantasy-sports-uk.preview.emergentagent.com/api"

def test_league_creation_with_assets():
    """Test creating a league with assetsSelected via API"""
    print("\n" + "="*70)
    print("TEST 1: Create League with Selected Assets")
    print("="*70)
    
    # First, create a test user
    user_data = {
        "name": "Test Commissioner",
        "email": f"test-prompt1-{hash('test')}.{id(None)}@example.com"
    }
    
    print(f"\n📝 Creating test user: {user_data['email']}")
    user_response = requests.post(f"{BACKEND_URL}/users", json=user_data)
    
    if user_response.status_code != 200:
        print(f"❌ Failed to create user: {user_response.text}")
        return False
    
    user = user_response.json()
    print(f"✅ User created: {user['id']}")
    
    # Get some club IDs to select
    print("\n📝 Fetching available clubs...")
    clubs_response = requests.get(f"{BACKEND_URL}/clubs")
    
    if clubs_response.status_code != 200:
        print(f"❌ Failed to fetch clubs: {clubs_response.text}")
        return False
    
    clubs = clubs_response.json()
    selected_club_ids = [club['id'] for club in clubs[:9]]  # Select 9 clubs
    print(f"✅ Selected {len(selected_club_ids)} clubs for testing")
    
    # Create league with selected assets
    league_data = {
        "name": "Prompt1 Test League with Assets",
        "commissionerId": user['id'],
        "budget": 500000000,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 3,
        "sportKey": "football",
        "assetsSelected": selected_club_ids  # THE KEY FIELD
    }
    
    print(f"\n📝 Creating league with {len(selected_club_ids)} selected assets...")
    league_response = requests.post(f"{BACKEND_URL}/leagues", json=league_data)
    
    if league_response.status_code != 200:
        print(f"❌ Failed to create league: {league_response.text}")
        return False
    
    league = league_response.json()
    print(f"✅ League created: {league['id']}")
    
    # Verify assetsSelected was stored
    if 'assetsSelected' not in league:
        print(f"❌ assetsSelected field missing from response")
        return False
    
    if league['assetsSelected'] != selected_club_ids:
        print(f"❌ assetsSelected mismatch!")
        print(f"   Expected: {selected_club_ids}")
        print(f"   Got: {league['assetsSelected']}")
        return False
    
    print(f"✅ assetsSelected correctly stored: {len(league['assetsSelected'])} assets")
    
    # Retrieve league and verify persistence
    print(f"\n📝 Retrieving league to verify persistence...")
    get_response = requests.get(f"{BACKEND_URL}/leagues/{league['id']}")
    
    if get_response.status_code != 200:
        print(f"❌ Failed to retrieve league: {get_response.text}")
        return False
    
    retrieved_league = get_response.json()
    
    if retrieved_league['assetsSelected'] != selected_club_ids:
        print(f"❌ assetsSelected not persisted correctly!")
        return False
    
    print(f"✅ League retrieved with correct assetsSelected")
    
    return True

def test_league_creation_without_assets():
    """Test creating a league without assetsSelected (backward compatibility)"""
    print("\n" + "="*70)
    print("TEST 2: Create League WITHOUT Selected Assets (All Teams)")
    print("="*70)
    
    # Create a test user
    user_data = {
        "name": "Test Commissioner 2",
        "email": f"test-prompt1-no-assets-{hash('test2')}.{id(list)}@example.com"
    }
    
    print(f"\n📝 Creating test user: {user_data['email']}")
    user_response = requests.post(f"{BACKEND_URL}/users", json=user_data)
    
    if user_response.status_code != 200:
        print(f"❌ Failed to create user: {user_response.text}")
        return False
    
    user = user_response.json()
    print(f"✅ User created: {user['id']}")
    
    # Create league WITHOUT assetsSelected
    league_data = {
        "name": "Prompt1 Test League All Teams",
        "commissionerId": user['id'],
        "budget": 500000000,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 3,
        "sportKey": "football"
        # NOTE: assetsSelected NOT included
    }
    
    print(f"\n📝 Creating league without assetsSelected...")
    league_response = requests.post(f"{BACKEND_URL}/leagues", json=league_data)
    
    if league_response.status_code != 200:
        print(f"❌ Failed to create league: {league_response.text}")
        return False
    
    league = league_response.json()
    print(f"✅ League created: {league['id']}")
    
    # Verify assetsSelected is None or not present (both acceptable)
    assets_selected = league.get('assetsSelected')
    if assets_selected is not None:
        print(f"❌ Expected assetsSelected to be None, got: {assets_selected}")
        return False
    
    print(f"✅ assetsSelected correctly set to None (include all teams)")
    
    return True

def test_update_league_assets():
    """Test updating league assets via PUT endpoint"""
    print("\n" + "="*70)
    print("TEST 3: Update League Assets via PUT Endpoint")
    print("="*70)
    
    # Create a test user
    user_data = {
        "name": "Test Commissioner 3",
        "email": f"test-prompt1-update-{hash('test3')}.{id(dict)}@example.com"
    }
    
    print(f"\n📝 Creating test user: {user_data['email']}")
    user_response = requests.post(f"{BACKEND_URL}/users", json=user_data)
    
    if user_response.status_code != 200:
        print(f"❌ Failed to create user: {user_response.text}")
        return False
    
    user = user_response.json()
    print(f"✅ User created: {user['id']}")
    
    # Create league without selected assets initially
    league_data = {
        "name": "Prompt1 Test League for Update",
        "commissionerId": user['id'],
        "budget": 500000000,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 3,
        "sportKey": "football"
    }
    
    print(f"\n📝 Creating initial league...")
    league_response = requests.post(f"{BACKEND_URL}/leagues", json=league_data)
    
    if league_response.status_code != 200:
        print(f"❌ Failed to create league: {league_response.text}")
        return False
    
    league = league_response.json()
    print(f"✅ League created: {league['id']}")
    
    # Get some club IDs
    clubs_response = requests.get(f"{BACKEND_URL}/clubs")
    clubs = clubs_response.json()
    selected_club_ids = [club['id'] for club in clubs[10:15]]  # Select different 5 clubs
    
    # Update league assets
    print(f"\n📝 Updating league with {len(selected_club_ids)} selected assets...")
    update_response = requests.put(
        f"{BACKEND_URL}/leagues/{league['id']}/assets",
        json=selected_club_ids
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update assets: {update_response.text}")
        return False
    
    update_result = update_response.json()
    print(f"✅ Assets updated: {update_result['message']}")
    
    # Verify update persisted
    print(f"\n📝 Retrieving league to verify update...")
    get_response = requests.get(f"{BACKEND_URL}/leagues/{league['id']}")
    
    if get_response.status_code != 200:
        print(f"❌ Failed to retrieve league: {get_response.text}")
        return False
    
    updated_league = get_response.json()
    
    if updated_league['assetsSelected'] != selected_club_ids:
        print(f"❌ Update not persisted correctly!")
        print(f"   Expected: {selected_club_ids}")
        print(f"   Got: {updated_league['assetsSelected']}")
        return False
    
    print(f"✅ Update persisted correctly: {len(updated_league['assetsSelected'])} assets")
    
    return True

def test_validation():
    """Test validation features"""
    print("\n" + "="*70)
    print("TEST 4: Validation (Deduplication, Trimming)")
    print("="*70)
    
    # Create a test user
    user_data = {
        "name": "Test Commissioner 4",
        "email": f"test-prompt1-validation-{hash('test4')}.{id(set)}@example.com"
    }
    
    print(f"\n📝 Creating test user...")
    user_response = requests.post(f"{BACKEND_URL}/users", json=user_data)
    
    if user_response.status_code != 200:
        print(f"❌ Failed to create user: {user_response.text}")
        return False
    
    user = user_response.json()
    
    # Get club IDs
    clubs_response = requests.get(f"{BACKEND_URL}/clubs")
    clubs = clubs_response.json()
    club_id = clubs[0]['id']
    
    # Create league with duplicates and whitespace
    league_data = {
        "name": "Prompt1 Test Validation",
        "commissionerId": user['id'],
        "budget": 500000000,
        "minManagers": 2,
        "maxManagers": 8,
        "clubSlots": 3,
        "sportKey": "football",
        "assetsSelected": [f" {club_id} ", club_id, clubs[1]['id'], club_id]  # Duplicates & whitespace
    }
    
    print(f"\n📝 Creating league with duplicates and whitespace...")
    print(f"   Input: {league_data['assetsSelected']}")
    
    league_response = requests.post(f"{BACKEND_URL}/leagues", json=league_data)
    
    if league_response.status_code != 200:
        print(f"❌ Failed to create league: {league_response.text}")
        return False
    
    league = league_response.json()
    print(f"✅ League created")
    
    # Verify deduplication and trimming
    expected = [club_id, clubs[1]['id']]  # Deduplicated, trimmed
    
    if league['assetsSelected'] != expected:
        print(f"❌ Validation failed!")
        print(f"   Expected: {expected}")
        print(f"   Got: {league['assetsSelected']}")
        return False
    
    print(f"✅ Validation working: {league['assetsSelected']}")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PROMPT 1 - API INTEGRATION TESTS")
    print("="*70)
    
    all_passed = True
    
    try:
        # Run all tests
        tests = [
            ("Create with Assets", test_league_creation_with_assets),
            ("Create without Assets", test_league_creation_without_assets),
            ("Update Assets", test_update_league_assets),
            ("Validation", test_validation)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                passed = test_func()
                results.append((test_name, passed))
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"\n❌ Test '{test_name}' raised exception: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
                all_passed = False
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        if all_passed:
            print("\n" + "="*70)
            print("🎉 ALL API INTEGRATION TESTS PASSED!")
            print("="*70)
            print("\nPrompt 1 Implementation Verified:")
            print("✅ API accepts and stores assetsSelected in league creation")
            print("✅ API returns assetsSelected in league retrieval")
            print("✅ PUT endpoint updates assetsSelected correctly")
            print("✅ Backward compatibility maintained (missing field = None)")
            print("✅ Validation working (deduplication, trimming)")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
