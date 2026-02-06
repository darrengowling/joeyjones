#!/usr/bin/env python3
"""
Comprehensive Team Verification Script
Verifies ALL CL and PL teams match the Football-Data.org API
"""
import asyncio
import aiohttp
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
FOOTBALL_DATA_TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN')

async def verify_teams():
    """Verify all teams against Football-Data.org API"""
    
    print("="*80)
    print("COMPREHENSIVE TEAM VERIFICATION")
    print("="*80)
    print()
    
    # Connect to database
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get our teams
        our_cl_teams = await db.assets.find({
            'sportKey': 'football',
            'competitions': 'UEFA Champions League'
        }, {'_id': 0, 'name': 1, 'externalId': 1}).to_list(100)
        
        our_pl_teams = await db.assets.find({
            'sportKey': 'football',
            'competitions': 'English Premier League'
        }, {'_id': 0, 'name': 1, 'externalId': 1}).to_list(100)
        
        print(f"📊 Database: {len(our_cl_teams)} CL teams, {len(our_pl_teams)} PL teams")
        print()
        
        # Get API teams
        async with aiohttp.ClientSession() as session:
            # Champions League
            print("🔍 Verifying Champions League teams...")
            async with session.get(
                'https://api.football-data.org/v4/competitions/CL/teams',
                headers={'X-Auth-Token': FOOTBALL_DATA_TOKEN}
            ) as resp:
                if resp.status == 200:
                    cl_data = await resp.json()
                    api_cl_teams = {str(t['id']): t['name'] for t in cl_data.get('teams', [])}
                    print(f"✅ API returned {len(api_cl_teams)} CL teams")
                else:
                    print(f"❌ API error: {resp.status}")
                    api_cl_teams = {}
            
            # Premier League
            print("🔍 Verifying Premier League teams...")
            async with session.get(
                'https://api.football-data.org/v4/competitions/PL/teams',
                headers={'X-Auth-Token': FOOTBALL_DATA_TOKEN}
            ) as resp:
                if resp.status == 200:
                    pl_data = await resp.json()
                    api_pl_teams = {str(t['id']): t['name'] for t in pl_data.get('teams', [])}
                    print(f"✅ API returned {len(api_pl_teams)} PL teams")
                else:
                    print(f"❌ API error: {resp.status}")
                    api_pl_teams = {}
        
        print()
        print("="*80)
        print("CHAMPIONS LEAGUE VERIFICATION")
        print("="*80)
        print()
        
        cl_mismatches = []
        cl_missing = []
        cl_correct = 0
        
        for team in sorted(our_cl_teams, key=lambda x: x['name']):
            ext_id = str(team['externalId'])
            our_name = team['name']
            
            if ext_id in api_cl_teams:
                api_name = api_cl_teams[ext_id]
                if our_name == api_name:
                    print(f"✅ {our_name[:50]:50} | ID: {ext_id}")
                    cl_correct += 1
                else:
                    print(f"⚠️  {our_name[:50]:50} | ID: {ext_id}")
                    print(f"    API expects: {api_name}")
                    cl_mismatches.append({
                        'id': ext_id,
                        'our_name': our_name,
                        'api_name': api_name
                    })
            else:
                print(f"❌ {our_name[:50]:50} | ID: {ext_id} NOT IN API")
                cl_missing.append({'id': ext_id, 'name': our_name})
        
        print()
        print("="*80)
        print("PREMIER LEAGUE VERIFICATION")
        print("="*80)
        print()
        
        pl_mismatches = []
        pl_missing = []
        pl_correct = 0
        
        for team in sorted(our_pl_teams, key=lambda x: x['name']):
            ext_id = str(team['externalId'])
            our_name = team['name']
            
            if ext_id in api_pl_teams:
                api_name = api_pl_teams[ext_id]
                if our_name == api_name:
                    print(f"✅ {our_name[:50]:50} | ID: {ext_id}")
                    pl_correct += 1
                else:
                    print(f"⚠️  {our_name[:50]:50} | ID: {ext_id}")
                    print(f"    API expects: {api_name}")
                    pl_mismatches.append({
                        'id': ext_id,
                        'our_name': our_name,
                        'api_name': api_name
                    })
            else:
                print(f"❌ {our_name[:50]:50} | ID: {ext_id} NOT IN API")
                pl_missing.append({'id': ext_id, 'name': our_name})
        
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print()
        print("Champions League:")
        print(f"  ✅ Correct: {cl_correct}/{len(our_cl_teams)}")
        print(f"  ⚠️  Name mismatches: {len(cl_mismatches)}")
        print(f"  ❌ Missing from API: {len(cl_missing)}")
        print()
        print("Premier League:")
        print(f"  ✅ Correct: {pl_correct}/{len(our_pl_teams)}")
        print(f"  ⚠️  Name mismatches: {len(pl_mismatches)}")
        print(f"  ❌ Missing from API: {len(pl_missing)}")
        print()
        
        if cl_mismatches or pl_mismatches:
            print("="*80)
            print("⚠️  NAME MISMATCHES FOUND")
            print("="*80)
            print()
            print("These teams will NOT match during scoring!")
            print()
            for m in cl_mismatches + pl_mismatches:
                print(f"  ID {m['id']}:")
                print(f"    Database: {m['our_name']}")
                print(f"    API:      {m['api_name']}")
                print()
        
        if cl_missing or pl_missing:
            print("="*80)
            print("❌ TEAMS NOT IN API")
            print("="*80)
            print()
            print("These teams have IDs not recognized by Football-Data.org:")
            print()
            for m in cl_missing + pl_missing:
                print(f"  {m['name']} (ID: {m['id']})")
            print()
        
        if not cl_mismatches and not pl_mismatches and not cl_missing and not pl_missing:
            print("="*80)
            print("🎉 ALL TEAMS VERIFIED SUCCESSFULLY!")
            print("="*80)
            print()
            print("✅ All team names match the API exactly")
            print("✅ All external IDs are valid")
            print("✅ Fixture import, score updates, and points calculation will work correctly")
            print()
            return True
        else:
            print("="*80)
            print("⚠️  VERIFICATION FAILED")
            print("="*80)
            print()
            print("Action required: Update team names/IDs to match API")
            return False
            
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(verify_teams())
    sys.exit(0 if success else 1)
