#!/usr/bin/env python3
"""
Database Migration V2: Update Team Names to Match Football-Data.org API
Enhanced with better logging and error handling
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from datetime import datetime, timezone

class MigrationLogger:
    """Simple logger that works both standalone and when called from server"""
    def __init__(self, external_logger=None):
        self.external_logger = external_logger
    
    def info(self, msg):
        if self.external_logger:
            self.external_logger.info(msg)
        print(msg)
    
    def warning(self, msg):
        if self.external_logger:
            self.external_logger.warning(msg)
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        if self.external_logger:
            self.external_logger.error(msg)
        print(f"ERROR: {msg}")

async def migrate_team_names(logger=None):
    """Update all 40 team names to match API exactly"""
    log = MigrationLogger(logger)
    
    log.info("="*80)
    log.info("DATABASE MIGRATION V2: Updating Team Names")
    log.info("="*80)
    
    # Get environment variables
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    if not mongo_url:
        log.error("❌ MONGO_URL environment variable not set")
        return False
    
    # Log connection details (mask sensitive parts)
    if 'localhost' in mongo_url:
        log.info("🔍 Connecting to: LOCAL MongoDB (localhost)")
    elif 'mongodb.net' in mongo_url or 'atlas' in mongo_url.lower():
        log.info("🔍 Connecting to: MongoDB ATLAS (production)")
    else:
        masked_url = mongo_url[:30] + "..." if len(mongo_url) > 30 else mongo_url
        log.info(f"🔍 Connecting to: {masked_url}")
    log.info(f"🔍 Database: {db_name}")
    log.info(f"🔍 Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    client = None
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # Test connection
        await db.command('ping')
        log.info("✅ Database connection successful")
        
        # Count existing assets before migration
        total_assets = await db.assets.count_documents({'sportKey': 'football'})
        log.info(f"📊 Total football assets in database: {total_assets}")
        
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
        
        # Additional fixes found in production
        additional_fixes = [
            # Teams with wrong names AND externalId
            ('Sunderland', 'Sunderland AFC', '71', 'English Premier League'),
            ('Wolverhampton Wanderers', 'Wolverhampton Wanderers FC', '76', 'English Premier League'),
            # CL teams missing from original list
            ('Chelsea', 'Chelsea FC', '61', 'UEFA Champions League'),
            ('Atalanta', 'Atalanta BC', '102', 'UEFA Champions League'),
            ('Atlético de Madrid', 'Club Atlético de Madrid', '78', 'UEFA Champions League'),
            ('Manchester City', 'Manchester City FC', '65', 'English Premier League'),
        ]
        
        total_updated = 0
        total_skipped = 0
        total_not_found = 0
        
        # Process CL updates
        log.info("\n📊 Champions League Teams:")
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
                log.info(f"  ✅ {old_name} → {new_name}")
                total_updated += 1
            else:
                # Check if already updated
                existing = await db.assets.find_one({
                    'name': new_name,
                    'competitions': comp,
                    'externalId': ext_id
                })
                if existing:
                    log.info(f"  ⏭️  {new_name} (already correct)")
                    total_skipped += 1
                else:
                    log.warning(f"  ⚠️  {old_name} not found (externalId: {ext_id})")
                    total_not_found += 1
        
        # Process PL updates
        log.info("\n📊 Premier League Teams:")
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
                log.info(f"  ✅ {old_name} → {new_name}")
                total_updated += 1
            else:
                existing = await db.assets.find_one({
                    'name': new_name,
                    'competitions': comp,
                    'externalId': ext_id
                })
                if existing:
                    log.info(f"  ⏭️  {new_name} (already correct)")
                    total_skipped += 1
                else:
                    log.warning(f"  ⚠️  {old_name} not found (externalId: {ext_id})")
                    total_not_found += 1
        
        # Process additional fixes
        log.info("\n📊 Additional Fixes (Production-Specific):")
        for old_name, new_name, ext_id, comp in additional_fixes:
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
                log.info(f"  ✅ {old_name} → {new_name} (externalId: {ext_id})")
                total_updated += 1
            else:
                existing = await db.assets.find_one({
                    'name': new_name,
                    'externalId': ext_id,
                    'competitions': comp
                })
                if existing:
                    log.info(f"  ⏭️  {new_name} (already correct)")
                    total_skipped += 1
                else:
                    log.warning(f"  ⚠️  {old_name} not found")
                    total_not_found += 1
        
        log.info("\n" + "="*80)
        log.info("✅ Migration complete!")
        log.info(f"   Updated: {total_updated}")
        log.info(f"   Skipped (already correct): {total_skipped}")
        log.info(f"   Not found: {total_not_found}")
        log.info("="*80)
        
        # If we updated teams, log a sample to verify
        if total_updated > 0:
            sample_team = await db.assets.find_one({
                'name': 'Chelsea FC',
                'competitions': 'UEFA Champions League'
            }, {'_id': 0, 'name': 1, 'externalId': 1})
            log.info(f"\n🔍 Verification sample - Chelsea FC: {sample_team}")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Migration failed with exception: {e}")
        import traceback
        log.error(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        if client:
            client.close()
            log.info("🔌 Database connection closed")


if __name__ == "__main__":
    # Only load .env when running as standalone script
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🚀 Running standalone migration script...\n")
    success = asyncio.run(migrate_team_names())
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
