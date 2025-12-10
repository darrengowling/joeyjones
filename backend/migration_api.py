"""
Migration API endpoints - callable from browser/curl to fix production
"""
from fastapi import APIRouter, HTTPException
from migrate_team_names_v2 import migrate_team_names
import logging
import os

migration_api = APIRouter()
logger = logging.getLogger("server")

@migration_api.get("/admin/migration/status")
async def check_migration_status():
    """
    Check if team names need migration (read-only, safe to call)
    Returns sample team names to verify if migration is needed
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    try:
        # Check critical teams that should have specific names
        checks = [
            {'name': 'Expected: Chelsea FC', 'externalId': '61', 'competition': 'UEFA Champions League'},
            {'name': 'Expected: Atalanta BC', 'externalId': '102', 'competition': 'UEFA Champions League'},
            {'name': 'Expected: Club Atlético de Madrid', 'externalId': '78', 'competition': 'UEFA Champions League'},
            {'name': 'Expected: Manchester City FC', 'externalId': '65', 'competition': 'English Premier League'},
            {'name': 'Expected: Arsenal FC', 'externalId': '57', 'competition': 'English Premier League'},
        ]
        
        results = []
        needs_migration = False
        
        for check in checks:
            team = await db.assets.find_one({
                'externalId': check['externalId'],
                'competitions': check['competition']
            }, {'_id': 0, 'name': 1, 'externalId': 1})
            
            expected_name = check['name'].replace('Expected: ', '')
            if team:
                is_correct = team['name'] == expected_name
                if not is_correct:
                    needs_migration = True
                results.append({
                    'externalId': check['externalId'],
                    'expected': expected_name,
                    'actual': team['name'],
                    'status': '✅ Correct' if is_correct else '❌ Needs update'
                })
            else:
                results.append({
                    'externalId': check['externalId'],
                    'expected': expected_name,
                    'actual': 'NOT FOUND',
                    'status': '⚠️ Missing'
                })
                needs_migration = True
        
        # Get database info
        db_info = 'LOCAL' if 'localhost' in mongo_url else 'PRODUCTION (Atlas)'
        
        return {
            'database': db_info,
            'database_name': os.environ.get('DB_NAME', 'test_database'),
            'migration_needed': needs_migration,
            'summary': f'{"❌ Migration needed" if needs_migration else "✅ All correct"}',
            'teams_checked': len(checks),
            'details': results,
            'next_step': 'Call POST /api/admin/migration/run to fix' if needs_migration else 'No action needed'
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
    finally:
        client.close()


@migration_api.post("/admin/migration/run")
async def run_migration():
    """
    Run the team name migration (makes database changes)
    Safe to call multiple times (idempotent)
    """
    logger.info("="*80)
    logger.info("🔄 MANUAL MIGRATION: Triggered via API endpoint")
    logger.info("="*80)
    
    try:
        # Run migration with full logging
        success = await migrate_team_names(logger=logger)
        
        if success:
            logger.info("✅ Manual migration completed successfully via API")
            return {
                'success': True,
                'message': '✅ Migration completed successfully',
                'details': 'Team names have been updated to match the Football-Data.org API',
                'next_steps': [
                    '1. Call GET /api/admin/migration/status to verify changes',
                    '2. Test "Update All Scores" in your leagues',
                    '3. Verify league points are now being calculated'
                ]
            }
        else:
            logger.error("❌ Manual migration via API returned False")
            return {
                'success': False,
                'message': '⚠️ Migration completed but some teams were not found',
                'details': 'Check backend logs for details. Some teams may already be correct.',
                'next_step': 'Call GET /api/admin/migration/status to see current state'
            }
    except Exception as e:
        logger.error(f"❌ Migration API error: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                'error': str(e),
                'message': 'Migration failed with exception',
                'hint': 'Check backend logs for full error details'
            }
        )


@migration_api.get("/admin/migration/help")
async def migration_help():
    """
    Show instructions for using the migration endpoints
    """
    return {
        'title': 'Team Name Migration API',
        'description': 'Use these endpoints to fix production scoring issues caused by team name mismatches',
        'endpoints': {
            'GET /api/admin/migration/status': {
                'description': 'Check if migration is needed (safe, read-only)',
                'example': 'curl https://your-app.com/api/admin/migration/status'
            },
            'POST /api/admin/migration/run': {
                'description': 'Run the migration to fix team names (safe, idempotent)',
                'example': 'curl -X POST https://your-app.com/api/admin/migration/run'
            },
            'GET /api/admin/migration/help': {
                'description': 'Show this help message',
                'example': 'curl https://your-app.com/api/admin/migration/help'
            }
        },
        'workflow': [
            '1. Call GET /admin/migration/status to see if migration is needed',
            '2. If needed, call POST /admin/migration/run to fix the database',
            '3. Call GET /admin/migration/status again to verify it worked',
            '4. Test scoring in your leagues'
        ],
        'safety': 'All endpoints are safe to call multiple times. The migration is idempotent (won\'t duplicate changes).'
    }
