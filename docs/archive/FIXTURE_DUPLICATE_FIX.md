# Fixture Duplicate Issue - Fixed

## Problem Discovered

Two identical Chelsea vs Arsenal fixtures existed in the database:

**Fixture 1** (Old - from seed script):
- Created: Nov 25, 2025
- Source: Unknown (seed script)
- API Football ID: None
- External IDs: 49 (Chelsea), 42 (Arsenal)

**Fixture 2** (New - from automatic import):
- Created: Nov 30, 2025
- Source: api-football
- API Football ID: 1379091
- External IDs: 49 (Chelsea), 42 (Arsenal)

## Root Cause

The duplicate detection logic in `/api/leagues/{id}/fixtures/import-from-api` only checked for existing fixtures by `apiFootballId`:

```python
existing = await db.fixtures.find_one({
    "apiFootballId": fixture_id,
    "leagueId": {"$exists": False}
})
```

**Problem**: Old fixtures from seed scripts don't have `apiFootballId`, so they weren't detected as duplicates when importing from API.

## Solution Implemented

### 1. Enhanced Duplicate Detection

Updated the import logic to check BOTH:
- By API Football ID (for fixtures already imported from API)
- By teams + date (for fixtures from seed scripts or CSV)

**New Logic**:
```python
existing = await db.fixtures.find_one({
    "$and": [
        {"leagueId": {"$exists": False}},  # Only shared fixtures
        {
            "$or": [
                {"apiFootballId": fixture_id},  # Match by API ID
                {
                    "$and": [  # Or match by teams + date
                        {"homeExternalId": str(home_team_api_id)},
                        {"awayExternalId": str(away_team_api_id)},
                        {"matchDate": {"$regex": f"^{match_date[:10]}"}}
                    ]
                }
            ]
        }
    ]
})
```

### 2. Update Behavior

When a match is found:
- If it has no API Football ID → adds the API ID
- Updates all fixture data with latest from API
- Logs when adding API ID to existing fixture

### 3. Database Cleanup

Removed the duplicate Chelsea vs Arsenal fixture:
- Deleted: Old fixture without API ID
- Kept: New fixture with API ID 1379091

**Result**: 
- Before: 4 fixtures (2 duplicates)
- After: 3 fixtures (no duplicates)

## Why This Matters

### Before Fix
1. User imports fixtures from API → creates duplicates
2. Two identical matches show in fixtures list
3. Score updates might update wrong fixture
4. Confusing for users and commissioners

### After Fix
1. User imports fixtures from API → detects existing fixtures
2. Updates existing fixtures with API data
3. Adds API Football ID to seed script fixtures
4. Single source of truth per match

## Edge Cases Handled

### Case 1: Seed Script Fixtures
- Seed scripts create fixtures without API ID
- First API import will add API ID to these fixtures
- Future imports will update by API ID

### Case 2: CSV Import Fixtures
- CSV imports create competition-specific fixtures (with leagueId)
- These are excluded from duplicate detection (leagueId exists)
- No conflicts with shared fixtures

### Case 3: Multiple Imports
- First import: Creates fixture with API ID
- Second import: Finds by API ID, updates scores
- No duplicates created

### Case 4: Same Teams, Different Dates
- Liverpool vs Arsenal on Dec 1
- Liverpool vs Arsenal on Dec 15
- Date regex ensures these are treated as different fixtures

## Testing

### Manual Test
```bash
# Before fix - 4 fixtures
GET /api/leagues/{daz1}/fixtures
Returns: 4 fixtures (including 2 Chelsea vs Arsenal)

# After cleanup - 3 fixtures
GET /api/leagues/{daz1}/fixtures
Returns: 3 fixtures (single Chelsea vs Arsenal)
```

### Future Test
When API-Football account is reactivated:
1. Import fixtures for daz1
2. Should update existing Chelsea vs Arsenal (not create duplicate)
3. Should add API ID to Brentford vs Burnley and Fulham fixtures

## Files Modified

- `/app/backend/server.py` - Enhanced duplicate detection in `import_fixtures_from_api` endpoint

## Related Issues

### API-Football Account Suspended
The score update failure was caused by API-Football account suspension, not the duplicate fixtures. The duplicate was discovered during investigation.

**Suspension Error**:
```json
{
  "errors": {
    "access": "Your account is suspended, check on https://dashboard.api-football.com."
  }
}
```

This needs to be resolved separately on the API-Football dashboard.

---

**Status**: ✅ FIXED
**Database Cleaned**: ✅ YES
**Prevention Implemented**: ✅ YES
**Testing Required**: Once API account reactivated
