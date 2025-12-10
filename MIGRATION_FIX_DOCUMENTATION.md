# Team Name Migration Fix - Documentation

## Problem Summary

**Issue:** Production scoring is broken because team names in the database don't match the Football-Data.org API exactly.

**Examples:**
- Database: `"Chelsea"` → API expects: `"Chelsea FC"`
- Database: `"Atalanta"` → API expects: `"Atalanta BC"`
- Database: `"Atlético de Madrid"` → API expects: `"Club Atlético de Madrid"`

**Impact:** The scoring service uses fuzzy matching (`if club_name in team_name`) which fails when database names are LONGER than API names.

---

## Root Cause

The migration script exists and is integrated into startup (server.py lines 187-225), BUT it appears to be failing silently in production. Possible reasons:

1. **Import Error:** Python module path issues in production environment
2. **Environment Variables:** MONGO_URL not available at startup time
3. **Silent Failure:** Exception being caught but not logged prominently
4. **Timing Issue:** Migration running before database is fully ready

---

## Solutions Implemented

### 1. Enhanced Migration Script (`migrate_team_names_v2.py`)

**Improvements:**
- ✅ Better connection testing (ping database before migration)
- ✅ Detailed logging at every step
- ✅ Enhanced error messages with full tracebacks
- ✅ Verification after migration (sample team check)
- ✅ Additional production-specific fixes (Chelsea, Atalanta, Man City, etc.)
- ✅ Connection status logging (LOCAL vs ATLAS vs Unknown)

**New teams covered:**
- Chelsea → Chelsea FC (externalId: 61)
- Atalanta → Atalanta BC (externalId: 102)
- Atlético de Madrid → Club Atlético de Madrid (externalId: 78)
- Manchester City → Manchester City FC (externalId: 65)

### 2. Enhanced Startup Logging (`server.py`)

**Changes:**
- ✅ Log environment variables before migration
- ✅ Separate ImportError from general exceptions
- ✅ Log sys.path to debug import issues
- ✅ More visible error messages (80-char separator lines)

### 3. Manual Migration Runner (`run_migration_manually.py`)

**Purpose:** Run the migration directly from command line if startup migration fails

**Usage:**
```bash
cd /app
python3 run_migration_manually.py
# Type 'yes' when prompted
```

**Safety:**
- Shows which database it will connect to before running
- Requires explicit 'yes' confirmation
- Idempotent (safe to run multiple times)

---

## Deployment Plan

### Option A: Automatic (Recommended)

**Step 1:** Deploy the updated code
```bash
# Code already includes the new migration script
# Just redeploy through your normal deployment process
```

**Step 2:** Check backend startup logs
```bash
# Look for these log messages:
# "🔄 STARTUP: Initializing team name migration..."
# "✅ Team name migration completed successfully"
```

**Step 3:** Verify in production
```bash
curl https://draft-kings-mobile.emergent.host/api/clubs?sportKey=football | jq '.[] | select(.externalId=="61") | .name'
# Should return: "Chelsea FC"
```

**Step 4:** Test scoring
- Go to any production league (e.g., MYCL 8)
- Click "Update All Scores"
- Check if league points are now being calculated

---

### Option B: Manual (If Startup Migration Fails)

**Step 1:** SSH into production server

**Step 2:** Run manual migration
```bash
cd /app
python3 run_migration_manually.py
# Type 'yes' when prompted
```

**Step 3:** Verify changes
```bash
# Check that Chelsea is now "Chelsea FC"
python3 -c "
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ.get('DB_NAME', 'test_database')]
chelsea = db.assets.find_one({'externalId': '61', 'competitions': 'UEFA Champions League'}, {'_id': 0, 'name': 1})
print(f'Chelsea: {chelsea}')
"
```

**Step 4:** Test scoring in UI

---

## Testing Checklist

### After Migration Runs:

- [ ] **Check team names in production database**
  ```bash
  curl https://draft-kings-mobile.emergent.host/api/clubs?sportKey=football | grep -E "Chelsea|Atalanta|Atlético"
  ```
  
  Expected:
  - "Chelsea FC" (not "Chelsea")
  - "Atalanta BC" (not "Atalanta")
  - "Club Atlético de Madrid" (not "Atlético de Madrid")

- [ ] **Test fixture import**
  - Import fixtures for a league (should work as before)

- [ ] **Test score update**
  - Update scores for fixtures
  - Check that `goalsHome` and `goalsAway` are populated
  - Check that `status` is set to "ft"

- [ ] **Test scoring calculation**
  - Click "Update All Scores" in a production league
  - Verify that `league_points` collection is populated
  - Check that standings show correct points

- [ ] **Verify specific league (MYCL 8)**
  - Get league summary: `GET /api/leagues/{MYCL_8_id}/summary`
  - Should show participant points correctly calculated

---

## Rollback Plan

If migration causes issues:

**Option 1: Revert team names**
```python
# Run this script to revert (DO NOT use unless necessary)
# This will break the fixed scoring, so only use if migration caused other issues

from pymongo import MongoClient
import os
updates = [
    ('Chelsea FC', 'Chelsea', '61'),
    ('Atalanta BC', 'Atalanta', '102'),
    # etc...
]
# Apply reverse updates
```

**Option 2: Restore from backup**
- If you have a MongoDB backup before migration
- Restore the `assets` collection only

---

## Long-Term Fix (Future Improvement)

The current system has a fundamental flaw:

**Current:** Scoring uses fuzzy matching (`if club_name in team_name`)
**Problem:** This breaks when database names are longer than API names

**Recommended Fix:**
1. Update `scoring_service.py` to use `externalId` for matching instead of names
2. Ensure all fixtures store `homeAssetId` and `awayAssetId` (not just names)
3. Change matching logic from:
   ```python
   if club_name in team1:  # Fuzzy
   ```
   To:
   ```python
   if club_id == fixture['homeAssetId']:  # Exact
   ```

This would make the system resilient to team name changes and API variations.

---

## Files Modified

1. `/app/backend/migrate_team_names_v2.py` - Enhanced migration script
2. `/app/backend/server.py` - Enhanced startup logging (lines 187-225)
3. `/app/run_migration_manually.py` - Manual migration runner
4. `/app/MIGRATION_FIX_DOCUMENTATION.md` - This file

---

## Questions & Troubleshooting

### Q: How do I know if migration ran in production?

**A:** Check backend startup logs for these messages:
```
🔄 STARTUP: Initializing team name migration...
✅ Team name migration completed successfully
```

If you see `❌ Team name migration failed`, check the error details that follow.

---

### Q: Migration says "already correct" but scoring still doesn't work?

**A:** This means the database IS correct but something else is wrong. Check:
1. Are fixtures actually in the database? (`GET /api/leagues/{id}/fixtures`)
2. Do fixtures have `status: "ft"`? (Scoring ignores non-ft fixtures)
3. Do fixtures have `goalsHome` and `goalsAway` populated?
4. Are participants actually in the league? (`GET /api/leagues/{id}/participants`)
5. Do participants have `clubsWon` array populated? (Scoring only calculates for owned clubs)

---

### Q: Can I run the migration multiple times?

**A:** Yes! The migration is **idempotent** - it checks before updating and skips teams that are already correct.

---

### Q: What if new teams are added in the future?

**A:** Add them to the migration script and redeploy. The script will only update the new teams.

---

**Document Version:** 1.0  
**Created:** December 10, 2024  
**Last Updated:** December 10, 2024
