#!/usr/bin/env python3
"""Seed Railway POC database with CL teams for stress testing"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import sys

# Railway MongoDB connection - update with your connection string
MONGO_URL = sys.argv[1] if len(sys.argv) > 1 else None

if not MONGO_URL:
    print("Usage: python seed_railway_poc.py <MONGO_URL>")
    sys.exit(1)

DB_NAME = "sport_x_poc"

UEFA_CL_CLUBS = [
    {"name": "Real Madrid", "country": "Spain", "uefaId": "RM"},
    {"name": "Barcelona", "country": "Spain", "uefaId": "FCB"},
    {"name": "Atlético Madrid", "country": "Spain", "uefaId": "ATM"},
    {"name": "Athletic Bilbao", "country": "Spain", "uefaId": "ATH"},
    {"name": "Manchester City", "country": "England", "uefaId": "MCI"},
    {"name": "Arsenal", "country": "England", "uefaId": "ARS"},
    {"name": "Liverpool", "country": "England", "uefaId": "LIV"},
    {"name": "Aston Villa", "country": "England", "uefaId": "AVL"},
    {"name": "Bayer Leverkusen", "country": "Germany", "uefaId": "B04"},
    {"name": "Bayern Munich", "country": "Germany", "uefaId": "FCB2"},
    {"name": "VfB Stuttgart", "country": "Germany", "uefaId": "VFB"},
    {"name": "RB Leipzig", "country": "Germany", "uefaId": "RBL"},
    {"name": "Inter Milan", "country": "Italy", "uefaId": "INT"},
    {"name": "AC Milan", "country": "Italy", "uefaId": "ACM"},
    {"name": "Juventus", "country": "Italy", "uefaId": "JUV"},
    {"name": "Atalanta", "country": "Italy", "uefaId": "ATA"},
    {"name": "Paris Saint-Germain", "country": "France", "uefaId": "PSG"},
    {"name": "AS Monaco", "country": "France", "uefaId": "ASM"},
    {"name": "Brest", "country": "France", "uefaId": "SB29"},
    {"name": "Sporting CP", "country": "Portugal", "uefaId": "SCP"},
    {"name": "Benfica", "country": "Portugal", "uefaId": "SLB"},
    {"name": "FC Porto", "country": "Portugal", "uefaId": "FCP"},
    {"name": "PSV Eindhoven", "country": "Netherlands", "uefaId": "PSV"},
    {"name": "Feyenoord", "country": "Netherlands", "uefaId": "FEY"},
    {"name": "Club Brugge", "country": "Belgium", "uefaId": "CLB"},
    {"name": "Union Saint-Gilloise", "country": "Belgium", "uefaId": "USG"},
    {"name": "Celtic", "country": "Scotland", "uefaId": "CEL"},
    {"name": "Rangers", "country": "Scotland", "uefaId": "RAN"},
    {"name": "Sturm Graz", "country": "Austria", "uefaId": "STU"},
    {"name": "Sparta Prague", "country": "Czech Republic", "uefaId": "SPP"},
    {"name": "Dinamo Zagreb", "country": "Croatia", "uefaId": "DZG"},
    {"name": "Young Boys", "country": "Switzerland", "uefaId": "YB"},
    {"name": "Red Star Belgrade", "country": "Serbia", "uefaId": "RSB"},
    {"name": "Shakhtar Donetsk", "country": "Ukraine", "uefaId": "SHA"},
    {"name": "FC Copenhagen", "country": "Denmark", "uefaId": "FCK"},
    {"name": "Jagiellonia Białystok", "country": "Poland", "uefaId": "JAG"},
]

async def seed_database():
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
    
    # Clear existing assets
    result = await db.assets.delete_many({"sportKey": {"$in": ["CL", "football"]}})
    print(f"Cleared {result.deleted_count} existing assets")
    
    # Insert CL teams
    assets = []
    for club in UEFA_CL_CLUBS:
        asset = {
            "id": str(uuid.uuid4()),
            "name": club["name"],
            "country": club["country"],
            "uefaId": club["uefaId"],
            "sportKey": "football",
            "competitionCode": "CL",
            "competitionShort": "UCL",
            "competitions": "UEFA Champions League",
            "type": "team",
            "flag": f"https://flagcdn.com/w40/{club['country'].lower()[:2]}.png"
        }
        assets.append(asset)
    
    result = await db.assets.insert_many(assets)
    print(f"✅ Inserted {len(result.inserted_ids)} CL teams")
    
    # Create indexes
    await db.assets.create_index("sportKey")
    await db.assets.create_index("id")
    await db.assets.create_index([("sportKey", 1), ("name", 1)])
    print("✅ Created indexes")
    
    # Verify
    count = await db.assets.count_documents({"sportKey": "football"})
    print(f"✅ Verified: {count} football teams in database")
    
    client.close()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(seed_database())
