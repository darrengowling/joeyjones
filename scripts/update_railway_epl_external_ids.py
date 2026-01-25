#!/usr/bin/env python3
"""
Update Railway EPL teams with football-data.org externalIds
Required for fixture imports to work.

Usage: python update_railway_epl_external_ids.py <RAILWAY_MONGO_URL>
Example: python update_railway_epl_external_ids.py "mongodb+srv://user:pass@cluster.mongodb.net/sport_x_poc"
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

# Railway MongoDB connection
MONGO_URL = sys.argv[1] if len(sys.argv) > 1 else None

if not MONGO_URL:
    print("Usage: python update_railway_epl_external_ids.py <RAILWAY_MONGO_URL>")
    print('Example: python update_railway_epl_external_ids.py "mongodb+srv://..."')
    sys.exit(1)

DB_NAME = "sport_x_poc"

# EPL teams with football-data.org externalIds
# These IDs are required for fixture imports to work
EPL_EXTERNAL_IDS = {
    "AFC Bournemouth": 1044,
    "Arsenal": 57,
    "Arsenal FC": 57,
    "Aston Villa": 58,
    "Aston Villa FC": 58,
    "Brentford": 402,
    "Brentford FC": 402,
    "Brighton": 397,
    "Brighton & Hove Albion": 397,
    "Brighton & Hove Albion FC": 397,
    "Chelsea": 61,
    "Chelsea FC": 61,
    "Crystal Palace": 354,
    "Crystal Palace FC": 354,
    "Everton": 62,
    "Everton FC": 62,
    "Fulham": 63,
    "Fulham FC": 63,
    "Ipswich Town": 349,
    "Ipswich Town FC": 349,
    "Leicester City": 338,
    "Leicester City FC": 338,
    "Liverpool": 64,
    "Liverpool FC": 64,
    "Manchester City": 65,
    "Manchester City FC": 65,
    "Manchester United": 66,
    "Manchester United FC": 66,
    "Newcastle United": 67,
    "Newcastle United FC": 67,
    "Nottingham Forest": 351,
    "Nottingham Forest FC": 351,
    "Southampton": 340,
    "Southampton FC": 340,
    "Tottenham Hotspur": 73,
    "Tottenham Hotspur FC": 73,
    "West Ham United": 563,
    "West Ham United FC": 563,
    "Wolverhampton Wanderers": 76,
    "Wolverhampton Wanderers FC": 76,
    "Wolves": 76,
}

async def update_external_ids():
    print(f"Connecting to Railway MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Get all football teams
    teams = await db.assets.find({"sportKey": "football"}).to_list(200)
    print(f"Found {len(teams)} football teams in Railway DB")
    
    # Update each team with externalId
    updated = 0
    not_found = []
    
    for team in teams:
        name = team.get("name")
        current_ext_id = team.get("externalId")
        
        # Skip if already has externalId
        if current_ext_id:
            print(f"  ✓ {name}: already has externalId={current_ext_id}")
            continue
        
        # Look up externalId
        ext_id = EPL_EXTERNAL_IDS.get(name)
        
        if ext_id:
            result = await db.assets.update_one(
                {"id": team["id"]},
                {"$set": {"externalId": ext_id}}
            )
            if result.modified_count > 0:
                print(f"  ✅ {name}: set externalId={ext_id}")
                updated += 1
        else:
            not_found.append(name)
    
    print(f"\n{'='*50}")
    print(f"✅ Updated {updated} teams with externalId")
    
    if not_found:
        print(f"\n⚠️ No externalId found for {len(not_found)} teams:")
        for name in not_found:
            print(f"   - {name}")
        print("\nThese teams may be CL/AFCON only or have different names.")
    
    # Verify EPL teams now have externalIds
    epl_teams = await db.assets.find({
        "sportKey": "football",
        "$or": [
            {"competitionShort": "EPL"},
            {"competitions": "English Premier League"}
        ]
    }).to_list(50)
    
    epl_with_ext = [t for t in epl_teams if t.get("externalId")]
    print(f"\n📊 EPL teams with externalId: {len(epl_with_ext)} / {len(epl_teams)}")
    
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(update_external_ids())
