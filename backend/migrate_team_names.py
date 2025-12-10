#!/usr/bin/env python3
"""
Database Migration: Update Team Names to Match Football-Data.org API
Run this to ensure all team names match the API exactly for scoring to work
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_team_names():
    """Update all 40 team names to match API exactly"""
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL not set")
        return False
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    try:
        print("=" * 80)
        print("DATABASE MIGRATION: Updating Team Names")
        print("=" * 80)
        
        # Champions League updates (22 teams)
        cl_updates = [
            ('Ajax', 'AFC Ajax', '678', 'UEFA Champions League'),
            ('Monaco', 'AS Monaco FC', '548', 'UEFA Champions League'),
            ('Arsenal', 'Arsenal FC', '57', 'UEFA Champions League'),
            ('Leverkusen', 'Bayer 04 Leverkusen', '3', 'UEFA Champions League'),
            ('Club Brugge', 'Club Brugge KV', '851', 'UEFA Champions League'),
            ('Frankfurt', 'Eintracht Frankfurt', '19', 'UEFA Champions League'),
            ('Barcelona', 'FC Barcelona', '81', 'UEFA Champions League'),
            ('Bayern München', 'FC Bayern München', '5', 'UEFA Champions League'),
            ('Inter', 'FC Internazionale Milano', '108', 'UEFA Champions League'),
            ('Bodø/Glimt', 'FK Bodø/Glimt', '5721', 'UEFA Champions League'),
            ('Galatasaray', 'Galatasaray SK', '610', 'UEFA Champions League'),
            ('Juventus', 'Juventus FC', '109', 'UEFA Champions League'),
            ('Liverpool', 'Liverpool FC', '64', 'UEFA Champions League'),
            ('Newcastle', 'Newcastle United FC', '67', 'UEFA Champions League'),
            ('Marseille', 'Olympique de Marseille', '516', 'UEFA Champions League'),
            ('Paris', 'Paris Saint-Germain FC', '524', 'UEFA Champions League'),
            ('Qarabağ', 'Qarabağ Ağdam FK', '611', 'UEFA Champions League'),
            ('Real Madrid', 'Real Madrid CF', '86', 'UEFA Champions League'),
            ('Slavia Praha', 'SK Slavia Praha', '930', 'UEFA Champions League'),
            ('Napoli', 'SSC Napoli', '113', 'UEFA Champions League'),
            ('Tottenham', 'Tottenham Hotspur FC', '73', 'UEFA Champions League'),
            ('Villarreal', 'Villarreal CF', '94', 'UEFA Champions League'),
        ]
        
        # Premier League updates (16 teams)
        pl_updates = [
            ('Bournemouth', 'AFC Bournemouth', '1044', 'English Premier League'),
            ('Arsenal', 'Arsenal FC', '57', 'English Premier League'),
            ('Aston Villa', 'Aston Villa FC', '58', 'English Premier League'),
            ('Brentford', 'Brentford FC', '402', 'English Premier League'),
            ('Brighton & Hove Albion', 'Brighton & Hove Albion FC', '397', 'English Premier League'),
            ('Burnley', 'Burnley FC', '328', 'English Premier League'),
            ('Crystal Palace', 'Crystal Palace FC', '354', 'English Premier League'),
            ('Everton', 'Everton FC', '62', 'English Premier League'),
            ('Fulham', 'Fulham FC', '63', 'English Premier League'),
            ('Leeds United', 'Leeds United FC', '341', 'English Premier League'),
            ('Liverpool', 'Liverpool FC', '64', 'English Premier League'),
            ('Manchester United', 'Manchester United FC', '66', 'English Premier League'),
            ('Newcastle', 'Newcastle United FC', '67', 'English Premier League'),
            ('Nottingham Forest', 'Nottingham Forest FC', '351', 'English Premier League'),
            ('Tottenham', 'Tottenham Hotspur FC', '73', 'English Premier League'),
            ('West Ham United', 'West Ham United FC', '563', 'English Premier League'),
        ]
        
        # Fix teams with wrong externalId
        fixes = [
            ('Sunderland', 'Sunderland AFC', '71', 'English Premier League'),
            ('Wolverhampton Wanderers', 'Wolverhampton Wanderers FC', '76', 'English Premier League'),
        ]
        
        total_updated = 0
        total_skipped = 0
        
        # Process CL updates
        print("\n📊 Champions League Teams:")
        for old_name, new_name, ext_id, comp in cl_updates:
            result = await db.assets.update_one(
                {
                    'name': old_name,
                    'competitions': comp,
                    'externalId': ext_id
                },
                {
                    '$set': {'name': new_name}
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✅ {old_name} → {new_name}")
                total_updated += 1
            else:
                # Check if already updated
                existing = await db.assets.find_one({
                    'name': new_name,
                    'competitions': comp,
                    'externalId': ext_id
                })
                if existing:
                    print(f"  ⏭️  {new_name} (already updated)")
                    total_skipped += 1
                else:
                    print(f"  ⚠️  {old_name} not found")
        
        # Process PL updates
        print("\n📊 Premier League Teams:")
        for old_name, new_name, ext_id, comp in pl_updates:
            result = await db.assets.update_one(
                {
                    'name': old_name,
                    'competitions': comp,
                    'externalId': ext_id
                },
                {
                    '$set': {'name': new_name}
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✅ {old_name} → {new_name}")
                total_updated += 1
            else:
                existing = await db.assets.find_one({
                    'name': new_name,
                    'competitions': comp,
                    'externalId': ext_id
                })
                if existing:
                    print(f"  ⏭️  {new_name} (already updated)")
                    total_skipped += 1
                else:
                    print(f"  ⚠️  {old_name} not found")
        
        # Process fixes (name + externalId)
        print("\n📊 ExternalId Fixes:")
        for old_name, new_name, ext_id, comp in fixes:
            result = await db.assets.update_one(
                {
                    'name': old_name,
                    'competitions': comp
                },
                {
                    '$set': {
                        'name': new_name,
                        'externalId': ext_id
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✅ {old_name} → {new_name} (externalId: {ext_id})")
                total_updated += 1
            else:
                existing = await db.assets.find_one({
                    'name': new_name,
                    'externalId': ext_id,
                    'competitions': comp
                })
                if existing:
                    print(f"  ⏭️  {new_name} (already updated)")
                    total_skipped += 1
                else:
                    print(f"  ⚠️  {old_name} not found")
        
        print("\n" + "=" * 80)
        print(f"✅ Migration complete!")
        print(f"   Updated: {total_updated}")
        print(f"   Skipped (already correct): {total_skipped}")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        client.close()


if __name__ == "__main__":
    success = asyncio.run(migrate_team_names())
    exit(0 if success else 1)
