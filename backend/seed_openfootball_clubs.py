#!/usr/bin/env python3
"""
Seed UEFA Champions League clubs from OpenFootball data
Run this script to populate the clubs collection with real CL teams
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import uuid

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Champions League 2024/25 qualified clubs
# Based on OpenFootball data and UEFA official lists
OPENFOOTBALL_CL_CLUBS = [
    # Spain - La Liga
    {"name": "Real Madrid", "country": "Spain", "uefaId": "RMA"},
    {"name": "Barcelona", "country": "Spain", "uefaId": "FCB"},
    {"name": "Atlético Madrid", "country": "Spain", "uefaId": "ATM"},
    {"name": "Girona", "country": "Spain", "uefaId": "GIR"},
    
    # England - Premier League
    {"name": "Manchester City", "country": "England", "uefaId": "MCI"},
    {"name": "Arsenal", "country": "England", "uefaId": "ARS"},
    {"name": "Liverpool", "country": "England", "uefaId": "LIV"},
    {"name": "Aston Villa", "country": "England", "uefaId": "AVL"},
    
    # Germany - Bundesliga
    {"name": "Bayer Leverkusen", "country": "Germany", "uefaId": "B04"},
    {"name": "Bayern Munich", "country": "Germany", "uefaId": "FCB"},
    {"name": "VfB Stuttgart", "country": "Germany", "uefaId": "VFB"},
    {"name": "RB Leipzig", "country": "Germany", "uefaId": "RBL"},
    {"name": "Borussia Dortmund", "country": "Germany", "uefaId": "BVB"},
    
    # Italy - Serie A
    {"name": "Inter Milan", "country": "Italy", "uefaId": "INT"},
    {"name": "AC Milan", "country": "Italy", "uefaId": "ACM"},
    {"name": "Juventus", "country": "Italy", "uefaId": "JUV"},
    {"name": "Atalanta", "country": "Italy", "uefaId": "ATA"},
    {"name": "Bologna", "country": "Italy", "uefaId": "BOL"},
    
    # France - Ligue 1
    {"name": "Paris Saint-Germain", "country": "France", "uefaId": "PSG"},
    {"name": "Monaco", "country": "France", "uefaId": "ASM"},
    {"name": "Brest", "country": "France", "uefaId": "SB29"},
    {"name": "Lille", "country": "France", "uefaId": "LIL"},
    
    # Portugal - Primeira Liga
    {"name": "Sporting CP", "country": "Portugal", "uefaId": "SCP"},
    {"name": "Benfica", "country": "Portugal", "uefaId": "SLB"},
    {"name": "FC Porto", "country": "Portugal", "uefaId": "FCP"},
    
    # Netherlands - Eredivisie
    {"name": "PSV Eindhoven", "country": "Netherlands", "uefaId": "PSV"},
    {"name": "Feyenoord", "country": "Netherlands", "uefaId": "FEY"},
    
    # Belgium - Pro League
    {"name": "Club Brugge", "country": "Belgium", "uefaId": "CLB"},
    
    # Scotland - Premiership
    {"name": "Celtic", "country": "Scotland", "uefaId": "CEL"},
    
    # Austria - Bundesliga
    {"name": "Sturm Graz", "country": "Austria", "uefaId": "STU"},
    
    # Czech Republic
    {"name": "Sparta Prague", "country": "Czech Republic", "uefaId": "SPP"},
    
    # Croatia
    {"name": "Dinamo Zagreb", "country": "Croatia", "uefaId": "DZG"},
    
    # Switzerland
    {"name": "Young Boys", "country": "Switzerland", "uefaId": "YB"},
    
    # Serbia
    {"name": "Red Star Belgrade", "country": "Serbia", "uefaId": "RSB"},
    
    # Ukraine
    {"name": "Shakhtar Donetsk", "country": "Ukraine", "uefaId": "SHA"},
    
    # Slovakia
    {"name": "Slovan Bratislava", "country": "Slovakia", "uefaId": "SLO"},
]


async def seed_clubs():
    """Seed clubs to database"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        print(f"🌱 Seeding {len(OPENFOOTBALL_CL_CLUBS)} Champions League clubs...")
        
        # Clear existing clubs
        deleted = await db.clubs.delete_many({})
        print(f"   Deleted {deleted.deleted_count} existing clubs")
        
        # Insert new clubs
        clubs_to_insert = []
        for club_data in OPENFOOTBALL_CL_CLUBS:
            club = {
                "id": str(uuid.uuid4()),
                "name": club_data["name"],
                "uefaId": club_data["uefaId"],
                "country": club_data["country"],
                "logo": None
            }
            clubs_to_insert.append(club)
        
        if clubs_to_insert:
            result = await db.clubs.insert_many(clubs_to_insert)
            print(f"   ✅ Inserted {len(result.inserted_ids)} clubs")
        
        # Print summary
        print("\n📊 Clubs by country:")
        countries = {}
        for club in OPENFOOTBALL_CL_CLUBS:
            country = club["country"]
            countries[country] = countries.get(country, 0) + 1
        
        for country, count in sorted(countries.items(), key=lambda x: -x[1]):
            print(f"   {country}: {count} clubs")
        
        print(f"\n✅ Seeding complete! Total: {len(clubs_to_insert)} clubs")
        
    except Exception as e:
        print(f"❌ Error seeding clubs: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_clubs())
