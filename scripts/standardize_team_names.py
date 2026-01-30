#!/usr/bin/env python3
"""
Standardize team names in production database to match Football-Data.org API names.

This ensures:
1. Single source of truth for team names
2. Easier maintenance of logo mappings
3. Consistent fixture imports

Usage: python standardize_team_names.py <MONGO_URL>

Safe to run multiple times (idempotent).
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

# MongoDB connection
MONGO_URL = sys.argv[1] if len(sys.argv) > 1 else None

if not MONGO_URL:
    print("Usage: python standardize_team_names.py <MONGO_URL>")
    print("Example: python standardize_team_names.py 'mongodb+srv://...'")
    sys.exit(1)

DB_NAME = "sport_x_poc"

# Mapping: Current short name -> Official Football-Data.org API name
# Only include teams that need updating
NAME_STANDARDIZATION_MAP = {
    # Spain
    "Real Madrid": "Real Madrid CF",
    "Barcelona": "FC Barcelona",
    "Atlético Madrid": "Club Atlético de Madrid",
    "Athletic Bilbao": "Athletic Club",
    
    # England
    "Manchester City": "Manchester City FC",
    "Arsenal": "Arsenal FC",
    "Liverpool": "Liverpool FC",
    "Aston Villa": "Aston Villa FC",
    "Tottenham": "Tottenham Hotspur FC",
    "Newcastle": "Newcastle United FC",
    "Chelsea": "Chelsea FC",
    "West Ham": "West Ham United FC",
    
    # Germany
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Bayern Munich": "FC Bayern München",
    
    # Italy
    "Inter Milan": "FC Internazionale Milano",
    "Juventus": "Juventus FC",
    "Atalanta": "Atalanta BC",
    "Napoli": "SSC Napoli",
    "Roma": "AS Roma",
    "Lazio": "SS Lazio",
    
    # France
    "Paris Saint-Germain": "Paris Saint-Germain FC",
    "AS Monaco": "AS Monaco FC",
    "Brest": "Stade Brestois 29",
    "Marseille": "Olympique de Marseille",
    "Lyon": "Olympique Lyon",
    "Lille": "LOSC Lille",
    
    # Portugal
    "Benfica": "Sport Lisboa e Benfica",
    "Sporting CP": "Sporting Clube de Portugal",
    
    # Netherlands
    "Feyenoord": "Feyenoord Rotterdam",
    "Ajax": "AFC Ajax",
    
    # Belgium
    "Club Brugge": "Club Brugge KV",
    "Union Saint-Gilloise": "Royale Union Saint-Gilloise",
    
    # Other
    "FC Copenhagen": "FC København",
    "Bodo/Glimt": "FK Bodø/Glimt",
    "Olympiacos": "PAE Olympiakos SFP",
    "Qarabag": "Qarabağ Ağdam FK",
    "Slavia Prague": "SK Slavia Praha",
}

# Teams to add if they don't exist in the database
TEAMS_TO_ADD = [
    # Italy - Serie A
    {"name": "SSC Napoli", "country": "Italy", "league": "Serie A"},
    {"name": "AS Roma", "country": "Italy", "league": "Serie A"},
    {"name": "SS Lazio", "country": "Italy", "league": "Serie A"},
    
    # France - Ligue 1
    {"name": "Olympique de Marseille", "country": "France", "league": "Ligue 1"},
    {"name": "Olympique Lyon", "country": "France", "league": "Ligue 1"},
    {"name": "LOSC Lille", "country": "France", "league": "Ligue 1"},
    
    # Netherlands - Eredivisie
    {"name": "AFC Ajax", "country": "Netherlands", "league": "Eredivisie"},
    
    # CL 2025/26 Teams
    {"name": "FK Bodø/Glimt", "country": "Norway", "league": "Eliteserien"},
    {"name": "PAE Olympiakos SFP", "country": "Greece", "league": "Super League Greece"},
    {"name": "Qarabağ Ağdam FK", "country": "Azerbaijan", "league": "Premier League (Azerbaijan)"},
    {"name": "SK Slavia Praha", "country": "Czech Republic", "league": "Czech First League"},
]


async def standardize_names():
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Get current teams for reference
    print("\n📋 Current football teams in database:")
    teams = await db.assets.find({"sportKey": "football"}).to_list(length=100)
    print(f"   Found {len(teams)} teams")
    
    # Track updates
    updated_count = 0
    skipped_count = 0
    already_standard_count = 0
    
    print("\n🔄 Standardizing team names...\n")
    
    for old_name, new_name in NAME_STANDARDIZATION_MAP.items():
        # Check if team with old name exists
        team = await db.assets.find_one({"name": old_name, "sportKey": "football"})
        
        if team:
            # Update the name
            result = await db.assets.update_one(
                {"_id": team["_id"]},
                {"$set": {"name": new_name}}
            )
            if result.modified_count > 0:
                print(f"   ✅ '{old_name}' → '{new_name}'")
                updated_count += 1
            else:
                print(f"   ⏭️  '{old_name}' - no change needed")
                skipped_count += 1
        else:
            # Check if already has standard name
            standard_team = await db.assets.find_one({"name": new_name, "sportKey": "football"})
            if standard_team:
                already_standard_count += 1
            # Team doesn't exist with either name - skip silently
    
    print(f"\n📊 Standardization Summary:")
    print(f"   Updated: {updated_count}")
    print(f"   Already standard: {already_standard_count}")
    print(f"   Skipped: {skipped_count}")
    
    # Now add missing teams
    print("\n➕ Adding missing teams...\n")
    added_count = 0
    
    for team_data in TEAMS_TO_ADD:
        # Check if team already exists
        existing = await db.assets.find_one({"name": team_data["name"], "sportKey": "football"})
        if existing:
            print(f"   ⏭️  '{team_data['name']}' - already exists")
            continue
        
        # Create new team asset
        import uuid
        new_asset = {
            "id": str(uuid.uuid4()),
            "name": team_data["name"],
            "country": team_data["country"],
            "sportKey": "football",
            "competitionCode": "CL",
            "competitionShort": team_data.get("league", ""),
            "competitions": ["UEFA Champions League", team_data.get("league", "")],
            "type": "team",
        }
        
        await db.assets.insert_one(new_asset)
        print(f"   ✅ Added '{team_data['name']}' ({team_data['country']})")
        added_count += 1
    
    print(f"\n📊 Teams Added: {added_count}")
    
    # Show final state
    print("\n📋 Final team names:")
    teams = await db.assets.find({"sportKey": "football"}).sort("name", 1).to_list(length=100)
    print(f"   Total: {len(teams)} teams")
    for team in teams:
        print(f"   • {team['name']}")
    
    client.close()
    print("\n✅ Done!")


async def dry_run():
    """Preview changes without applying them"""
    print(f"Connecting to MongoDB (DRY RUN)...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print("\n📋 Current team names that would be updated:\n")
    
    would_update = []
    already_standard = []
    not_found = []
    
    for old_name, new_name in NAME_STANDARDIZATION_MAP.items():
        team = await db.assets.find_one({"name": old_name, "sportKey": "football"})
        if team:
            would_update.append((old_name, new_name))
        else:
            standard_team = await db.assets.find_one({"name": new_name, "sportKey": "football"})
            if standard_team:
                already_standard.append(new_name)
            else:
                not_found.append(old_name)
    
    if would_update:
        print("🔄 Would update:")
        for old, new in would_update:
            print(f"   '{old}' → '{new}'")
    
    if already_standard:
        print(f"\n✅ Already standardized ({len(already_standard)} teams)")
    
    if not_found:
        print(f"\n⚠️  Not in database ({len(not_found)} teams):")
        for name in not_found[:10]:  # Show first 10
            print(f"   • {name}")
    
    client.close()
    print("\n💡 Run without --dry-run to apply changes")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        asyncio.run(dry_run())
    else:
        asyncio.run(standardize_names())
