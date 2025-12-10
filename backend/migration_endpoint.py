"""
API endpoint to check and run team name migration
Call this in production to verify/fix team names
"""
from fastapi import APIRouter, HTTPException
from migrate_team_names import migrate_team_names
import logging

migration_router = APIRouter()
logger = logging.getLogger("server")

@migration_router.get("/migration/check-teams")
async def check_team_names():
    """Check if team names match API (no changes made)"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    try:
        # Check sample teams
        checks = [
            ('Chelsea FC', '61', 'UEFA Champions League'),
            ('Atalanta BC', '102', 'UEFA Champions League'),
            ('Club Atlético de Madrid', '78', 'UEFA Champions League'),
            ('Arsenal FC', '57', 'English Premier League'),
        ]
        
        results = []
        issues = []
        
        for expected_name, ext_id, comp in checks:
            team = await db.assets.find_one({
                'externalId': ext_id,
                'competitions': comp
            }, {'_id': 0, 'name': 1})
            
            if team:
                is_correct = team['name'] == expected_name
                results.append({
                    'externalId': ext_id,
                    'expected': expected_name,
                    'actual': team['name'],
                    'correct': is_correct
                })
                if not is_correct:
                    issues.append(f"{team['name']} should be {expected_name}")
            else:
                results.append({
                    'externalId': ext_id,
                    'expected': expected_name,
                    'actual': 'NOT FOUND',
                    'correct': False
                })
                issues.append(f"Team {ext_id} not found")
        
        return {
            'database_connection': 'Atlas' if 'mongodb.net' in mongo_url else 'Local',
            'database_name': os.environ.get('DB_NAME', 'test_database'),
            'teams_checked': len(checks),
            'issues_found': len(issues),
            'all_correct': len(issues) == 0,
            'details': results,
            'issues': issues
        }
    finally:
        client.close()


@migration_router.post("/migration/run")
async def run_migration():
    """Run the team name migration (makes database changes)"""
    try:
        logger.info("🔄 Manual migration triggered via API")
        success = await migrate_team_names(logger=logger)
        
        if success:
            logger.info("✅ Manual migration completed successfully")
            return {
                'success': True,
                'message': 'Migration completed successfully. Team names updated.',
                'next_step': 'Call /migration/check-teams to verify'
            }
        else:
            logger.error("❌ Manual migration failed")
            return {
                'success': False,
                'message': 'Migration failed. Check logs for details.'
            }
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
