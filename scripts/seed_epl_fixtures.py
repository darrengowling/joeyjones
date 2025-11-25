import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone

# November 29-30, 2025 EPL Fixtures
FIXTURES = [
    {"home": "Brentford", "away": "Burnley", "date": "2025-11-29T15:00:00Z"},
    {"home": "Manchester City", "away": "Leeds United", "date": "2025-11-29T15:00:00Z"},
    {"home": "Sunderland", "away": "AFC Bournemouth", "date": "2025-11-29T15:00:00Z"},
    {"home": "Everton", "away": "Newcastle United", "date": "2025-11-29T15:00:00Z"},
    {"home": "Tottenham Hotspur", "away": "Fulham", "date": "2025-11-29T17:30:00Z"},
    {"home": "Crystal Palace", "away": "Manchester United", "date": "2025-11-30T14:00:00Z"},
    {"home": "Aston Villa", "away": "Wolverhampton Wanderers", "date": "2025-11-30T14:00:00Z"},
    {"home": "Nottingham Forest", "away": "Brighton & Hove Albion", "date": "2025-11-30T14:00:00Z"},
    {"home": "West Ham United", "away": "Liverpool", "date": "2025-11-30T16:30:00Z"},
    {"home": "Chelsea", "away": "Arsenal", "date": "2025-11-30T16:30:00Z"},
]

async def seed_fixtures():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/auction_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client.auction_db
    
    print("=" * 70)
    print("SEEDING EPL FIXTURES - NOVEMBER 29-30, 2025")
    print("=" * 70)
    print()
    
    # Get all teams for lookup
    teams = await db.assets.find({"sportKey": "football"}).to_list(length=None)
    team_lookup = {team["name"]: team for team in teams}
    
    added_count = 0
    
    for fixture in FIXTURES:
        home_team = team_lookup.get(fixture["home"])
        away_team = team_lookup.get(fixture["away"])
        
        if not home_team or not away_team:
            print(f"⚠️  Skipped: {fixture['home']} vs {fixture['away']} (team not found)")
            continue
        
        fixture_doc = {
            "id": str(uuid.uuid4()),
            "homeTeam": fixture["home"],
            "awayTeam": fixture["away"],
            "homeTeamId": home_team["id"],
            "awayTeamId": away_team["id"],
            "homeExternalId": home_team.get("externalId"),
            "awayExternalId": away_team.get("externalId"),
            "matchDate": fixture["date"],
            "status": "scheduled",
            "goalsHome": None,
            "goalsAway": None,
            "winner": None,
            "sportKey": "football",
            "competition": "EPL Nov 29-30 2025",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.fixtures.insert_one(fixture_doc)
        print(f"✓ Added: {fixture['home']} vs {fixture['away']} ({fixture['date']})")
        added_count += 1
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {added_count} fixtures added for Nov 29-30, 2025")
    print("=" * 70)
    print()
    print("Fixtures are ready for API-FOOTBALL score updates!")

asyncio.run(seed_fixtures())
