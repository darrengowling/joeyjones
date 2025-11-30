# Football - Current Status

## What Works ✅

### 1. Score Update from API-Football
- Endpoint: `POST /api/fixtures/update-scores` ✅
- Fetches from API-Football (workaround for free tier) ✅
- Matches by external IDs ✅
- Updates fixtures with scores ✅
- **Status: WORKING**

### 2. Fixture Display
- Frontend shows fixtures for each competition ✅
- Status badge shows "Finished" for completed matches ✅
- Scores display as "Team 3 - 1 Team" ✅
- **Status: WORKING**

### 3. Scoring Calculation (For Some Competitions)
- Function: `calculate_points_from_fixtures()` ✅
- Queries fixtures by team names (shared across competitions) ✅
- Calculates points (3-1-1 rules) ✅
- Updates league_points ✅
- Updates standings ✅
- **Verified working for:**
  - "daz1": daz2 (6pts), daz1 (5pts) ✅
  - "Premier League": Ash (14pts), daz1 (14pts), nathan (8pts) ✅

---

## What's Broken ❌

### 1. Most Competitions Show 0.0 Points

**Affected competitions:**
- prem2: 0.0 total points ❌
- prem3: 0.0 total points ❌
- prem5: 0.0 total points ❌
- prem8, prem12, prem13, prem15, prem16: Unknown ❌

**Why:**
These competitions likely haven't had `POST /leagues/{id}/score/recompute` called since we fixed the scoring logic.

**Test:** Need to trigger recompute for each competition

---

## Database State

### Fixtures
```
Total football fixtures: 10
Completed (status="ft"): 5 (Nov 29)
Not started (status="ns"): 5 (Nov 30)
```

**The 5 completed fixtures are shared by ALL competitions.**

### Competitions
```
Total football competitions: 10
- 2 tested and working (daz1, Premier League)
- 8 untested after our fixes
```

---

## What Needs Testing

### Test 1: Does "Update Match Scores" button work?
**Steps:**
1. Go to any competition
2. Click "Update Match Scores"
3. Check: Do fixtures show scores?
4. Check: Does league table update automatically?

**Current Status:** Unknown - needs manual test

---

### Test 2: Do all 10 competitions calculate correctly?
**Steps:**
For each competition (prem2, prem3, etc):
1. Trigger: `POST /api/leagues/{id}/score/recompute`
2. Check: Does league table show non-zero points?
3. Verify: Points calculated from correct teams

**Current Status:** Only 2/10 tested

---

### Test 3: Does frontend automatically refresh?
**Steps:**
1. Click "Update Match Scores"
2. Check: Does Fixtures tab refresh to show scores?
3. Check: Does League Table tab refresh to show points?

**Current Status:** Code says yes, needs verification

---

## Known Issues

### Issue 1: Hardcoded Competition Filters
**Location:** `/app/backend/server.py` lines 851-862
**Problem:** Only "EPL" and "UCL" supported when selecting teams
**Impact:** Cannot add La Liga, Serie A, etc. without code changes
**Priority:** MEDIUM (doesn't block pilot)

### Issue 2: Nov 30 Fixtures Not Updated
**Status:** "ns" (not started)
**Reason:** Either matches haven't finished OR "Update Match Scores" hasn't been run since they finished
**Action:** Need to click "Update Match Scores" again

---

## Summary

### ✅ WORKING (Verified)
1. Score fetching from API-Football
2. Fixture display with scores
3. Scoring calculation logic
4. Multiple competitions sharing fixtures
5. League table display

### ❌ NEEDS VERIFICATION
1. All 10 competitions calculate correctly
2. Automatic frontend refresh after score update
3. "Update Match Scores" button workflow end-to-end

### 🔄 NEEDS ACTION
1. Trigger recompute for all competitions
2. Update Nov 30 fixture scores
3. Manual test of full user workflow

---

## Next Steps

1. **Test one competition end-to-end:**
   - Pick a competition (e.g., prem2)
   - Click "Update Match Scores"
   - Verify fixtures show scores
   - Verify league table shows points

2. **If it works:**
   - Declare football scoring COMPLETE
   - Document any remaining issues

3. **If it doesn't work:**
   - Debug specific failure
   - Fix
   - Re-test

**Recommendation:** Test prem2 or prem3 right now as proof it works.
