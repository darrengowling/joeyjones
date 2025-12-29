# CRITICAL ISSUES: Cricket & Hardcoding

## New Rule Established
**DO NOT IGNORE ERRORS OR POTENTIAL ERRORS** even if not directly related to current analysis.
Pass this to next agent as core instruction.

---

## Issue 1: Football Competition Filters (Hardcoded)

### Location
`/app/backend/server.py` lines 843-865

### Problem
```python
@api_router.get("/clubs")
async def get_clubs(competition: str = None):
    query = {"sportKey": "football"}  # ❌ Hardcoded to football only
    
    if competition:
        if competition.upper() == "EPL":  # ❌ Hardcoded
            query["$or"] = [
                {"competitionShort": "EPL"},
                {"competitions": "English Premier League"}
            ]
        elif competition.upper() == "UCL":  # ❌ Hardcoded
            query["$or"] = [
                {"competitionShort": "UCL"},
                {"competitions": "UEFA Champions League"}
            ]
```

### Impact
- **Cannot add new football competitions** (La Liga, Serie A, Bundesliga) without code changes
- **Scalability blocked** for expansion
- **Inconsistent with generic scoring** we just fixed

### Fix Needed
Make it generic:
```python
@api_router.get("/clubs")
async def get_clubs(competition: str = None):
    query = {"sportKey": "football"}
    
    if competition:
        # Generic - works for ANY competition
        query["$or"] = [
            {"competitionShort": competition.upper()},
            {"competitions": competition}
        ]
```

**Risk:** LOW - Data already has these fields
**Effort:** 5 minutes
**Priority:** MEDIUM (for expansion, not blocking pilot)

---

## Issue 2: Cricket Completely Broken

### 2A: Cricket Assets Use Different Structure

**Football:**
```javascript
{
  "sportKey": "football",
  "name": "Chelsea",          // Team name
  "competitionShort": "EPL"
}
```

**Cricket:**
```javascript
{
  "sportKey": "cricket",
  "name": "Harry Brook",      // Player name (not team!)
  "externalId": "harry-brook",
  "meta": {
    "team": "England",
    "role": "Batsman"
  }
}
```

**Impact:** Cricket uses PLAYERS, not TEAMS

---

### 2B: Cricket Fixtures Use Different Structure

**Football fixtures:**
```javascript
{
  "homeTeam": "Chelsea",      // Team name string
  "awayTeam": "Arsenal",      // Team name string
  "homeExternalId": "49",
  "awayExternalId": "42"
}
```

**Cricket fixtures:**
```javascript
{
  "homeAssetId": "uuid",      // Player ID (not name!)
  "awayAssetId": "uuid",      // Player ID (not name!)
  "cricapiMatchId": "test-match-123",
  "startsAt": "2025-10-26 02:00:00",
  "status": "scheduled"
}
```

**Differences:**
- Uses `homeAssetId`/`awayAssetId` (player IDs)
- No `homeTeam`/`awayTeam` strings
- Has `cricapiMatchId` instead of API-Football fields
- Uses `startsAt` instead of `matchDate`

---

### 2C: Cricket Scoring Uses Wrong Logic

**Location:** `/app/backend/server.py` lines 2007-2014

```python
if sport_key == "football":
    result = await calculate_points_from_fixtures(db, league_id)
else:
    # ❌ WRONG: Uses Champions League scoring for cricket!
    result = await recompute_league_scores(db, league_id)
```

**What happens:**
1. Cricket competition tries to calculate scores
2. Falls back to `recompute_league_scores()`
3. That function fetches FOOTBALL Champions League data
4. Tries to match cricket player names with football team names
5. **FAILS COMPLETELY**

---

### 2D: No Cricket Competition Filters

The `/clubs` endpoint only returns football:
```python
query = {"sportKey": "football"}  # ❌ Cricket can't use this
```

**Impact:** Cannot filter cricket players by competition (IPL, The Hundred, etc.)

---

## Issue 3: Fixture-Based Scoring Assumes Football Structure

### Location
`/app/backend/scoring_service.py` line 323-331

```python
# Get team names for this league
team_names = [club["name"] for club in clubs]  # Works for football teams

# Find fixtures where these teams played
fixtures = await db.fixtures.find({
    "status": "ft",
    "sportKey": "football",  # ❌ Hardcoded
    "$or": [
        {"homeTeam": {"$in": team_names}},  # ❌ Cricket doesn't have homeTeam
        {"awayTeam": {"$in": team_names}}   # ❌ Cricket doesn't have awayTeam
    ]
})
```

**Impact:** This logic ONLY works for football, not cricket

---

## Issue 4: Cricket Match Scoring Not Implemented

Cricket has 203 leagues but no working scoring mechanism.

**What's needed:**
1. Cricket-specific scoring rules (runs, wickets, strike rate, economy)
2. Match cricket player IDs (`homeAssetId`) with player assets
3. Calculate points based on cricket stats (not football goals/wins)
4. Transform cricket fixture format to scoring format

**Current state:** COMPLETELY UNIMPLEMENTED

---

## Summary of Broken Cricket Functionality

| Feature | Football | Cricket |
|---------|----------|---------|
| Asset type | Teams | Players ✅ |
| Competition filters | EPL, UCL (hardcoded) | None ❌ |
| Fixture structure | homeTeam, awayTeam | homeAssetId, awayAssetId ✅ |
| Scoring logic | calculate_points_from_fixtures ✅ | Champions League (wrong!) ❌ |
| Score updates | API-Football ✅ | Not implemented ❌ |
| League table | Working ✅ | Broken ❌ |

**Cricket Status:** 🔴 COMPLETELY BROKEN for any scoring functionality

---

## Recommendations

### Immediate (Before Pilot)
1. ✅ **Document that cricket scoring is not implemented**
2. ✅ **Disable cricket league creation OR add warning**
3. ❌ **Do NOT promise cricket functionality**

### Short Term (Post-Pilot)
1. 🔄 **Make football competition filters generic** (5 mins)
2. 🔄 **Implement cricket scoring logic** (1-2 days)
3. 🔄 **Add cricket competition filters** (30 mins)

### Long Term
1. 🔮 **Abstract sport-specific logic** (scoring, fixtures, assets)
2. 🔮 **Create sport plugins/modules**
3. 🔮 **Support multiple cricket formats** (T20, ODI, Test)

---

## What User Asked

> "ok, so only the hardcoded competitions are supported in football, that's ok for now but what about cricket. did you even check?"

**Answer:** 
- ✅ Checked now
- ❌ Cricket scoring is completely broken
- ❌ Cricket uses different data structures
- ❌ No cricket scoring implementation exists
- 🔴 Cricket leagues CANNOT calculate points with current code

**The scoring fix we just made ONLY works for football.**

---

## Action Required

1. **Immediate:** Tell user cricket is not working for scoring
2. **Decision needed:** Should we fix cricket or just support football for pilot?
3. **Documentation:** Add to system map that cricket scoring is unimplemented

---

## Lesson Learned

**New Rule:** Do not dismiss issues as "not directly related" - they often ARE critical.

This applies to:
- ✅ Hardcoded values
- ✅ Assumptions about data structures
- ✅ "TODO" or "fallback" logic
- ✅ Different code paths for different sports
- ✅ Anything that looks inconsistent

**Be diligent. Check everything.**
