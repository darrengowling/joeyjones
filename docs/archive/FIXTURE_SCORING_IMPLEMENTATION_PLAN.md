# Standard Football Scoring Implementation Plan

## Overview
Create a scoring mechanism that calculates league points from completed fixtures (matches) stored in the database, applying standard football rules.

---

## Scoring Rules (As You Specified)
- **Win**: 3 points
- **Draw**: 1 point  
- **Goal scored**: 1 point per goal

---

## Implementation Approach

### Step 1: Create New Scoring Function

**Location:** `/app/backend/scoring_service.py`

**Function signature:**
```python
async def calculate_points_from_fixtures(db, league_id: str):
    """
    Calculate league points from completed fixtures
    Uses standard football scoring rules
    """
```

**Algorithm:**
```
1. Get the league by league_id
2. Get all participants in this league
3. Get all clubs owned by participants (from clubsWon arrays)
4. Get all COMPLETED fixtures for this league (status="ft", leagueId=league_id)

5. For each owned club:
   a. Find all fixtures where club played (homeTeam==club.name OR awayTeam==club.name)
   b. For each fixture:
      - Determine if club was home or away
      - Get club's goals scored and opponent's goals scored
      - Calculate:
        * If club scored more: wins += 1, points += 3
        * If goals equal: draws += 1, points += 1
        * If club scored less: losses += 1, points += 0
        * Add 1 point per goal: points += goals_scored
   c. Sum up: wins, draws, losses, goals_scored, goals_conceded, total_points
   d. Store/update in league_points collection

6. Return summary of clubs updated
```

### Step 2: Matching Logic

**How to match clubs with fixtures:**

```python
# Get club from assets
club_name = club["name"]  # e.g., "Chelsea"

# Find fixtures where this club played
fixtures = await db.fixtures.find({
    "leagueId": league_id,
    "status": "ft",
    "$or": [
        {"homeTeam": club_name},
        {"awayTeam": club_name}
    ]
}).to_list(100)

# For each fixture, determine if club was home or away
for fixture in fixtures:
    if fixture["homeTeam"] == club_name:
        # Club played at home
        goals_scored = fixture["goalsHome"]
        goals_conceded = fixture["goalsAway"]
    else:
        # Club played away
        goals_scored = fixture["goalsAway"]
        goals_conceded = fixture["goalsHome"]
    
    # Calculate points
    if goals_scored > goals_conceded:
        wins += 1
        points += 3
    elif goals_scored == goals_conceded:
        draws += 1
        points += 1
    else:
        losses += 1
    
    # Add goal points
    points += goals_scored
    total_goals_scored += goals_scored
    total_goals_conceded += goals_conceded
```

### Step 3: Modify Recompute Endpoint

**Location:** `/app/backend/server.py` line 1990

**Current:**
```python
@api_router.post("/leagues/{league_id}/score/recompute")
async def recompute_scores(league_id: str):
    result = await recompute_league_scores(db, league_id)  # ← Always uses Champions League
    return result
```

**Updated:**
```python
@api_router.post("/leagues/{league_id}/score/recompute")
async def recompute_scores(league_id: str):
    """
    Recompute scores for a league.
    Uses fixture-based scoring if fixtures exist, otherwise Champions League.
    """
    # Check if league has linked fixtures
    fixture_count = await db.fixtures.count_documents({
        "leagueId": league_id,
        "status": "ft"
    })
    
    if fixture_count > 0:
        # Use fixture-based scoring
        result = await calculate_points_from_fixtures(db, league_id)
    else:
        # Fall back to Champions League scoring
        result = await recompute_league_scores(db, league_id)
    
    return result
```

---

## Data Flow

```
1. User clicks "Update Match Scores"
   ↓
2. Fixtures updated with real scores from API-Football
   fixtures.goalsHome = 3
   fixtures.goalsAway = 1
   fixtures.status = "ft"
   ↓
3. System calls /leagues/{id}/score/recompute
   ↓
4. calculate_points_from_fixtures() runs:
   - Reads completed fixtures
   - Matches with participants' clubs
   - Calculates points
   ↓
5. Updates league_points collection:
   {
     leagueId: "...",
     clubId: "...",
     clubName: "Chelsea",
     wins: 1,
     draws: 0,
     losses: 0,
     goalsScored: 3,
     goalsConceded: 1,
     totalPoints: 6  // 3 for win + 3 for goals
   }
   ↓
6. Frontend fetches /leagues/{id}/standings
   ↓
7. League table displays updated standings
```

---

## Example Calculation

**Fixture:** Chelsea 3 - 1 Arsenal

**For Chelsea (owned by user daz1):**
- Result: Win (3 > 1) → +3 points
- Goals scored: 3 → +3 points  
- **Total: 6 points**
- Record: 1W-0D-0L, GF:3 GA:1

**For Arsenal (owned by user daz2):**
- Result: Loss (1 < 3) → +0 points
- Goals scored: 1 → +1 point
- **Total: 1 point**
- Record: 0W-0D-1L, GF:1 GA:3

---

## Edge Cases to Handle

### 1. Club Not In Any Fixtures
```python
if not fixtures:
    # Club didn't play any matches
    # Store with 0 points, 0 wins, 0 draws, 0 losses
```

### 2. Fixture Missing Scores
```python
if fixture["goalsHome"] is None or fixture["goalsAway"] is None:
    # Skip this fixture - not completed yet
    continue
```

### 3. Name Mismatch
```python
# Ensure exact string match between:
# - assets.name (e.g., "Tottenham Hotspur")
# - fixtures.homeTeam / fixtures.awayTeam (must match exactly)
```

### 4. Multiple Fixtures Same Club
```python
# Sum across all fixtures where club played
# E.g., if Chelsea played 3 matches, calculate points from all 3
```

---

## Testing Plan

### Test Case 1: Single Match
```
Fixture: Chelsea 3 - 1 Arsenal
Expected:
  Chelsea: 6 points (3 win + 3 goals)
  Arsenal: 1 point (0 loss + 1 goal)
```

### Test Case 2: Draw
```
Fixture: Brentford 2 - 2 Fulham  
Expected:
  Brentford: 3 points (1 draw + 2 goals)
  Fulham: 3 points (1 draw + 2 goals)
```

### Test Case 3: Multiple Matches
```
Chelsea fixtures:
  - Chelsea 3-1 Arsenal (Win: 3+3=6 pts)
  - Chelsea 1-2 Fulham (Loss: 0+1=1 pt)
Expected: 7 points total, 1W-0D-1L, GF:4 GA:3
```

---

## Files To Modify

1. **`/app/backend/scoring_service.py`**
   - Add `calculate_points_from_fixtures()` function

2. **`/app/backend/server.py`** (line ~1990)
   - Modify `/leagues/{id}/score/recompute` endpoint
   - Add logic to choose between fixture-based or Champions League scoring

---

## Implementation Steps

1. ✅ Understand current system (DONE)
2. ⏳ Write `calculate_points_from_fixtures()` function
3. ⏳ Update recompute endpoint  
4. ⏳ Test with league daz1
5. ⏳ Verify league table shows correct standings
6. ⏳ Test edge cases

---

## Risk Assessment

**Low Risk:**
- New function, doesn't modify existing Champions League scoring
- Uses existing database structures (fixtures, league_points)
- Clear, simple logic (standard football rules)
- Easily testable

**What Could Go Wrong:**
- Name mismatches between assets and fixtures
- Fixtures not linked to league
- Missing scores in fixtures

**Mitigation:**
- Defensive checks for None values
- Exact string matching
- Clear error messages

---

## Summary

**What:** Calculate league points from completed fixtures using standard football scoring  
**Where:** New function in scoring_service.py  
**How:** Match club names with fixture results, apply scoring rules  
**When:** Called by existing recompute endpoint  
**Why:** Current system only scores from external Champions League data

**Ready to implement?**
