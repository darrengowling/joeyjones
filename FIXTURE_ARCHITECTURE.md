# Fixture Architecture Documentation

## Overview
Fixtures in this system serve two distinct purposes:
1. **Shared Real-World Fixtures**: Public fixtures (e.g., EPL matchdays) accessible by all competitions
2. **Competition-Specific Fixtures**: Private fixtures created via CSV import for individual competitions

## Data Model

### Shared Fixtures (No leagueId)
Real-world fixtures from external APIs or seed scripts:
- **leagueId**: NOT SET (null/doesn't exist)
- **sportKey**: "football", "cricket", etc.
- **source**: "api", "seed", etc.
- **Purpose**: Shared resource for multiple competitions to calculate scores

Example:
```json
{
  "id": "924ef28e-7e92-487d-816a-646e0dba03e5",
  "homeTeam": "Brentford",
  "awayTeam": "Burnley",
  "sportKey": "football",
  "status": "ft",
  "goalsHome": 3,
  "goalsAway": 1
  // NO leagueId field
}
```

### Competition-Specific Fixtures (With leagueId)
Custom fixtures created via CSV import:
- **leagueId**: SET to specific competition ID
- **source**: "csv"
- **Purpose**: Private fixtures for a single competition only

Example:
```json
{
  "id": "a67eb6e0-cfe2-4d8c-9a41-cbada74f8dc9",
  "leagueId": "d17dbe69-9316-4f95-8b1c-bfe4517b3829",
  "sportKey": "cricket",
  "source": "csv",
  "status": "scheduled"
}
```

## Query Logic

### How Competitions Access Fixtures

**Endpoint**: `GET /api/leagues/{league_id}/fixtures`
**Location**: `server.py` lines 345-402

```python
# Get teams in the competition
teams = await db.assets.find({"id": {"$in": league["assetsSelected"]}})
team_names = [team["name"] for team in teams]

# Query fixtures by team names (NOT by leagueId)
fixtures = await db.fixtures.find({
    "sportKey": sport_key,
    "$or": [
        {"homeTeam": {"$in": team_names}},
        {"awayTeam": {"$in": team_names}}
    ]
})
```

**Key Point**: The query does NOT filter by `leagueId`. This allows multiple competitions to share the same fixtures.

## Fixture Creation Mechanisms

### 1. Seed Scripts (Shared Fixtures)
**File**: `/app/scripts/seed_epl_fixtures.py`
- Creates fixtures WITHOUT `leagueId`
- Used for populating real-world fixtures
- ✅ CORRECT: Does not set leagueId

### 2. API-Football Updates (Shared Fixtures)
**File**: `/app/backend/sports_data_client.py`
**Function**: `update_fixtures_from_api()`
- Updates scores for existing fixtures
- Only updates: `goalsHome`, `goalsAway`, `status`, `winner`, `updatedAt`
- ✅ CORRECT: Does not set or modify leagueId

### 3. CSV Import (Competition-Specific Fixtures)
**File**: `/app/backend/server.py`
**Endpoint**: `POST /leagues/{league_id}/fixtures/import-csv`
- Creates fixtures WITH `leagueId` set
- Used for custom/private fixtures
- ✅ CORRECT: This is the ONLY mechanism that should set leagueId

## Scoring Logic

**File**: `/app/backend/scoring_service.py`
**Function**: `calculate_points_from_fixtures()`

The scoring system also queries by team names, not by leagueId:

```python
# Get all clubs owned by participants
clubs = await db.assets.find({"id": {"$in": unique_club_ids}})
team_names = [club["name"] for club in clubs]

# Get completed fixtures for these teams
fixtures = await db.fixtures.find({
    "status": "ft",
    "sportKey": "football",
    "$or": [
        {"homeTeam": {"$in": team_names}},
        {"awayTeam": {"$in": team_names}}
    ]
})
```

This allows multiple competitions to independently calculate scores from the same underlying fixtures.

## Example Scenario

### Real-World State
- EPL Matchday has 10 fixtures
- All stored in DB with NO leagueId

### User Creates Two Competitions
1. **Competition A** (daz1):
   - Teams: Arsenal, Brentford, Chelsea, Fulham
   - Sees 3 fixtures from the shared pool
   - Calculates own league table

2. **Competition B** (prem26):
   - Teams: Bournemouth, Burnley, Crystal Palace, Everton
   - Sees 4 fixtures from the shared pool
   - Calculates own league table

Both competitions access the same 10 fixtures but see different subsets based on their selected teams.

## Issue Fixed (Nov 2025)

**Problem**: All football fixtures had `leagueId: "daz1"` hardcoded
**Impact**: Misleading data - fixtures appeared league-specific but were being treated as shared
**Solution**: Removed `leagueId` from all shared football fixtures
**Result**: Data model now matches query logic - shared fixtures have no leagueId

## Critical Rules

1. ✅ Shared fixtures (seed scripts, API updates) must NOT have `leagueId`
2. ✅ CSV-imported fixtures SHOULD have `leagueId`
3. ✅ Query logic ignores `leagueId` to enable sharing
4. ✅ Scoring logic queries by team names, not `leagueId`
5. ⚠️ Never add `leagueId` filtering to fixture queries unless intentionally breaking the shared model

---

**Last Updated**: November 2025
**Status**: ✅ Working correctly
