# How Fixtures Are Linked to Leagues

## The Linking Mechanism

Fixtures are linked to leagues via the **`leagueId`** field in the fixtures collection.

```javascript
{
  "id": "fixture-uuid",
  "leagueId": "league-uuid",  // ← THIS LINKS THE FIXTURE TO A LEAGUE
  "homeTeam": "Chelsea",
  "awayTeam": "Arsenal",
  ...
}
```

---

## Three Ways Fixtures Get Created & Linked

### Method 1: CSV Import (Production Method) ✅

**How it works:**
1. Commissioner creates a league via UI
2. Commissioner goes to "Fixtures" tab
3. Commissioner uploads CSV file
4. Backend endpoint: `POST /api/leagues/{league_id}/fixtures/import-csv`
5. **Automatically sets `leagueId`** when creating fixtures (line 1635)

**Code Location:** `/app/backend/server.py` line 1570-1750

**CSV Format:**
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-11-29T15:00:00Z,49,42,Stamford Bridge,15,match-123
```

**Key Point:** `leagueId` is **automatically set** from the URL parameter

---

### Method 2: Manual Seed Script (Development) ❌ BROKEN

**Current seed script:** `/app/scripts/seed_epl_fixtures.py`

**Problem:** Line 45-62 creates fixtures but **DOES NOT set leagueId**

```python
fixture_doc = {
    "id": str(uuid.uuid4()),
    "homeTeam": fixture["home"],
    "awayTeam": fixture["away"],
    # ... other fields ...
    "sportKey": "football",
    # ❌ MISSING: "leagueId": "???"
}
```

**Result:** Fixtures created but orphaned (not linked to any league)

**How we fixed it this session:**
Manually updated all fixtures:
```python
await db.fixtures.update_many(
    {"sportKey": "football", "leagueId": None},
    {"$set": {"leagueId": "91168d3f-372f-4a2e-b206-39df10ab3652"}}
)
```

---

### Method 3: API Import Feature (Future Enhancement)

**Proposed:** "Import Fixtures" button we designed earlier

Would call API-Football and create fixtures with `leagueId` automatically set.

**Status:** Not yet implemented (6-7 hours of work)

---

## Current Database State

### Query: How many fixtures per league?

```javascript
// League daz1
db.fixtures.count({leagueId: "91168d3f-372f-4a2e-b206-39df10ab3652"})
// Result: 10 fixtures

// Orphaned fixtures (no league)
db.fixtures.count({leagueId: null})
// Result: 0 (all fixed now)
```

### Query: Get fixtures for a league

```javascript
db.fixtures.find({
  leagueId: "91168d3f-372f-4a2e-b206-39df10ab3652",
  sportKey: "football"
})
```

---

## How The System Uses This Link

### 1. Display Fixtures in UI
```
Frontend: GET /api/leagues/{league_id}/fixtures
Backend: db.fixtures.find({"leagueId": league_id})
Shows: Only fixtures for this specific league
```

### 2. Calculate League Points
```
Backend: calculate_points_from_fixtures(league_id)
Query: db.fixtures.find({"leagueId": league_id, "status": "ft"})
Uses: Only completed fixtures for this league
```

### 3. Update Scores
```
Backend: update_fixtures_from_api()
Query: db.fixtures.find({...}) - gets all fixtures
Matches: By external IDs
Updates: Regardless of leagueId (global update)
```

**⚠️ Note:** Score update updates ALL fixtures globally, then league-specific calculation uses only that league's fixtures.

---

## The Problem We Had

### What Happened:
1. Ran seed script `/app/scripts/seed_epl_fixtures.py`
2. 10 fixtures created with `leagueId: None`
3. Created league "daz1" with ID `91168d3f...`
4. Fixtures tab showed "No fixtures"
5. Updated scores → worked
6. League table showed 0 points
7. Manually linked fixtures to league
8. League table now shows correct points

### Root Cause:
Seed script doesn't know which league to link to (it runs before/separately from league creation)

---

## Recommended Fix for Seed Scripts

### Option A: Require League ID Parameter
```python
async def seed_fixtures(league_id: str):
    # Pass league ID as argument
    fixture_doc = {
        "id": str(uuid.uuid4()),
        "leagueId": league_id,  # ✅ Set from parameter
        ...
    }
```

**Usage:**
```bash
python seed_epl_fixtures.py --league-id="91168d3f-372f-4a2e-b206-39df10ab3652"
```

### Option B: Create Default League
```python
# First create/get a league
league = await db.leagues.find_one({"name": "Default EPL League"})
if not league:
    league = await create_default_league()

league_id = league["id"]

# Then link fixtures
fixture_doc = {
    "leagueId": league_id,  # ✅ Set from created league
    ...
}
```

### Option C: Link After Creation
```python
# Create fixtures without league
# Then manually link them:
league = await db.leagues.find_one({"name": "daz1"})
await db.fixtures.update_many(
    {"sportKey": "football", "leagueId": None},
    {"$set": {"leagueId": league["id"]}}
)
```

**This is what we did in the session** ✅

---

## For New Leagues: Proper Flow

### Commissioner Workflow:
1. **Create League**
   - Go to "Create Competition"
   - Fill in name, sport, budget, slots, etc.
   - Click "Create"
   - Gets league ID: `91168d3f...`

2. **Import Fixtures**
   - Option A: Upload CSV (league ID automatically set)
   - Option B: Use "Import Fixtures" button (not yet built)
   - Option C: Run seed script then manually link (dev only)

3. **Run Auction**
   - Teams get assigned to managers

4. **Update Scores**
   - Click "Update Match Scores"
   - Fixtures update with scores

5. **View League Table**
   - Points automatically calculated
   - Only uses fixtures linked to this league

---

## Validation Needed

### Backend Should Validate:
```python
# When creating fixtures via API
if not league_id:
    raise HTTPException(400, "leagueId is required")

# When calculating points
fixtures = await db.fixtures.find({"leagueId": league_id})
if not fixtures:
    raise HTTPException(400, "No fixtures found for this league")
```

### Frontend Should Check:
```javascript
// Before showing fixtures tab
if (!fixtures || fixtures.length === 0) {
  return <EmptyState message="No fixtures imported yet" />;
}
```

---

## Summary

**How fixtures link to leagues:**
- Single field: `leagueId` in fixtures collection
- Set via: CSV import (automatic), seed script (manual), or API import (future)

**Current State:**
- ✅ League "daz1" has 10 fixtures correctly linked
- ✅ Score updates working
- ✅ League table calculating correctly

**Problem:**
- ❌ Seed script doesn't set leagueId
- ❌ Manual linking required after seeding

**Solution:**
- Use CSV import for production leagues
- Fix seed scripts to require league_id parameter
- Add validation to prevent orphaned fixtures
