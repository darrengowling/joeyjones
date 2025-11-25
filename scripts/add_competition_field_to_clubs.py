import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def add_competition_field():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("ADDING COMPETITION FIELD TO CLUBS")
    print("=" * 70)
    print()
    
    # Update EPL clubs
    epl_result = await db.clubs.update_many(
        {"uefaId": {"$regex": "^EPL_"}},
        {"$set": {"competition": "English Premier League", "competitionShort": "EPL"}}
    )
    print(f"✓ Updated {epl_result.modified_count} EPL clubs")
    
    # Update CL clubs (those without EPL_ prefix)
    cl_result = await db.clubs.update_many(
        {"uefaId": {"$not": {"$regex": "^EPL_"}}, "competition": {"$exists": False}},
        {"$set": {"competition": "UEFA Champions League", "competitionShort": "UCL"}}
    )
    print(f"✓ Updated {cl_result.modified_count} Champions League clubs")
    
    # Update overlapping clubs (Arsenal, Aston Villa, Liverpool, Man City)
    overlap_clubs = ["Arsenal", "Aston Villa", "Liverpool", "Manchester City"]
    for club_name in overlap_clubs:
        await db.clubs.update_one(
            {"name": club_name},
            {"$set": {"competitions": ["UEFA Champions League", "English Premier League"]}}
        )
    print(f"✓ Updated {len(overlap_clubs)} overlapping clubs with multiple competitions")
    
    print()
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Verify
    epl_count = await db.clubs.count_documents({"competitionShort": "EPL"})
    cl_count = await db.clubs.count_documents({"competitionShort": "UCL"})
    multi_count = await db.clubs.count_documents({"competitions": {"$exists": True}})
    
    print(f"EPL clubs: {epl_count}")
    print(f"Champions League clubs: {cl_count}")
    print(f"Multi-competition clubs: {multi_count}")

asyncio.run(add_competition_field())
