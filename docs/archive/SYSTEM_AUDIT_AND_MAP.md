# Complete System Audit & Map

## Purpose
Document every component, connection, and contract to prevent mismatches and enable reliable development.

---

## 1. DATABASE AUDIT

### Connection Details
```
Host: localhost:27017
Database Name: test_database  ← CRITICAL: Not "sport_auction_db"
Environment Variable: DB_NAME in backend/.env
```

### All Collections

#### a. **fixtures** (Match/Game Data)
```javascript
Schema:
{
  "id": "uuid",                          // Our internal ID
  "leagueId": "league-uuid",             // Links to leagues.id
  "homeTeam": "Chelsea",                 // Display name
  "awayTeam": "Arsenal",                 // Display name
  "homeTeamId": "asset-uuid",            // Links to assets.id
  "awayTeamId": "asset-uuid",            // Links to assets.id
  "homeExternalId": "49",                // API-Football team ID (STRING)
  "awayExternalId": "42",                // API-Football team ID (STRING)
  "matchDate": "2025-11-30T15:00:00Z",   // ISO datetime
  "startsAt": "2025-11-30T15:00:00Z",    // Alternate field (INCONSISTENT)
  "status": "ft" | "ns" | "live",        // API-Football status codes
  "goalsHome": 3 | null,                 // Number or null
  "goalsAway": 1 | null,                 // Number or null
  "winner": "Chelsea" | null,            // Team name or null
  "venue": "Stamford Bridge",            // Optional
  "round": "15",                         // Optional
  "externalMatchId": "api-match-id",     // Optional
  "sportKey": "football" | "cricket",    // REQUIRED
  "createdAt": "ISO datetime",
  "updatedAt": "ISO datetime"
}

Status Codes Used:
- "ft" = Finished/Full Time (from API-Football)
- "ns" = Not Started (from API-Football)
- "live" = Currently playing
- "completed" = NOT USED (only in old code expectations)
- "scheduled" = NOT USED (frontend expects this)
- "final" = NOT USED (frontend checks for this)

⚠️ MISMATCH FOUND:
- Database uses: "ft", "ns", "live"
- Frontend expects: "completed", "final", "scheduled"
- Fixed by: Checking for "ft" OR "completed" OR "final"

Current Record Count: 10 fixtures for league daz1
```

#### b. **assets** (Teams/Players)
```javascript
Schema:
{
  "id": "uuid",                      // Our internal ID
  "name": "Chelsea",                 // Display name
  "externalId": "49",                // API-Football team ID (STRING)
  "apiFootballId": 49,               // API-Football team ID (NUMBER) - DUPLICATE
  "sportKey": "football" | "cricket",
  "league": "Premier League",        // League name
  "city": "London",
  "country": "England",
  "founded": 1905,
  "venue": "Stamford Bridge",
  "createdAt": "ISO datetime",
  "updatedAt": "ISO datetime"
}

⚠️ INCONSISTENCY:
- externalId stored as STRING: "49"
- apiFootballId stored as NUMBER: 49
- fixtures.homeExternalId matches externalId (STRING)

Current Record Count: 20 Premier League teams
```

#### c. **leagues** (Competitions)
```javascript
Schema:
{
  "id": "uuid",                           // Our internal ID
  "name": "daz1",                         // User-chosen name
  "sportKey": "football" | "cricket",
  "creatorId": "user-uuid",
  "status": "draft" | "active" | "completed",
  "budget": 100,
  "slots": 2,
  "timerSeconds": 30,
  "antiSnipeSeconds": 10,
  "assetsSelected": ["asset-uuid", ...],  // Optional custom team selection
  "createdAt": "ISO datetime"
}

Key Field: name (user-facing, shown in UI as "daz1")
⚠️ CONFUSION: "daz1" is the NAME, not the ID
Real ID: "91168d3f-372f-4a2e-b206-39df10ab3652"
```

#### d. **league_participants**
```javascript
Schema:
{
  "leagueId": "league-uuid",
  "userId": "user-uuid",
  "userName": "daz1",
  "email": "user@example.com",
  "clubsWon": ["asset-uuid", "asset-uuid"],  // Teams won in auction
  "role": "commissioner" | "participant",
  "joinedAt": "ISO datetime"
}

Links: clubsWon → assets.id
```

#### e. **league_points** (Club-Level Scoring)
```javascript
Schema:
{
  "leagueId": "league-uuid",
  "clubId": "asset-uuid",              // Links to assets.id
  "clubName": "Chelsea",
  "wins": 1,
  "draws": 0,
  "losses": 0,
  "goalsScored": 3,
  "goalsConceded": 1,
  "totalPoints": 6,                    // Calculated: (wins*3) + (draws*1) + goals
  "lastUpdated": "ISO datetime"
}

Populated by: calculate_points_from_fixtures()
```

#### f. **standings** (User-Level Aggregated)
```javascript
Schema:
{
  "id": "uuid",
  "leagueId": "league-uuid",
  "sportKey": "football" | "cricket",
  "table": [
    {
      "userId": "user-uuid",
      "displayName": "daz1",
      "points": 11.0,                    // Sum of all owned clubs' points
      "assetsOwned": ["club-uuid", ...],
      "tiebreakers": {
        "goals": 5.0,
        "wins": 2.0,
        "runs": 0.0,                     // Cricket only
        "wickets": 0.0                   // Cricket only
      }
    }
  ],
  "lastComputedAt": "ISO datetime"
}

Populated by: update_standings_from_club_points()
```

---

## 2. API ENDPOINTS AUDIT

### Backend Base URL
```
Internal: http://0.0.0.0:8001
External: Uses REACT_APP_BACKEND_URL (via Kubernetes ingress)
All routes prefixed with: /api
```

### Scoring Flow Endpoints

#### POST /api/fixtures/update-scores
```
Purpose: Fetch scores from API-Football and update fixtures
Request Body: None (or optional fixture_ids)
Response:
{
  "status": "completed",
  "updated": 10,
  "errors": [],
  "api_requests_remaining": 98,
  "timestamp": "ISO datetime"
}

What it does:
1. Calls API-Football: GET /fixtures?date=YYYY-MM-DD
2. Filters for league_id=39 (Premier League) in Python
3. Matches by homeExternalId/awayExternalId
4. Updates fixtures: goalsHome, goalsAway, status="ft", winner
5. Does NOT trigger score calculation

Backend File: /app/backend/server.py line 278
Calls: sports_data_client.update_fixtures_from_api()
```

#### POST /api/leagues/{league_id}/score/recompute
```
Purpose: Calculate league points from fixtures
Request Body: None
Response:
{
  "message": "Scores calculated from fixtures successfully",
  "clubs_updated": 4,
  "fixtures_processed": 5
}

What it does:
1. Checks if fixtures exist for league
2. If YES: Calls calculate_points_from_fixtures()
3. If NO: Calls recompute_league_scores() (Champions League fallback)
4. Updates league_points collection
5. Updates standings collection

Backend File: /app/backend/server.py line 1990
Calls: scoring_service.calculate_points_from_fixtures()
```

#### GET /api/leagues/{league_id}/fixtures
```
Purpose: Get fixtures for a league
Response:
{
  "fixtures": [
    {
      "id": "uuid",
      "homeTeam": "Chelsea",
      "awayTeam": "Arsenal",
      "status": "ft",
      "goalsHome": 3,
      "goalsAway": 1,
      ...
    }
  ]
}

Backend File: /app/backend/server.py
Query: db.fixtures.find({"leagueId": league_id})
```

#### GET /api/leagues/{league_id}/standings
```
Purpose: Get league table
Response:
{
  "id": "standing-uuid",
  "leagueId": "league-uuid",
  "table": [
    {
      "userId": "uuid",
      "displayName": "daz1",
      "points": 11.0,
      "assetsOwned": ["club-uuid"],
      "tiebreakers": {...}
    }
  ]
}

Backend File: /app/backend/server.py line 1382 and 2020
⚠️ TWO ENDPOINTS WITH SAME ROUTE (duplicate definition)
```

---

## 3. EXTERNAL API CONTRACTS

### API-Football

#### Connection
```
URL: https://v3.football.api-sports.io
API Key: Stored in backend/.env as API_FOOTBALL_KEY
Plan: Free Tier (100 requests/day, 3-day rolling window)
```

#### Team ID Format
```
API Returns: NUMBER (49)
We Store: STRING ("49") in assets.externalId
Match By: String comparison str(api_id) == db_external_id
```

#### Status Codes
```
API Returns:
- "FT" = Full Time (finished)
- "NS" = Not Started
- "LIVE" = Currently playing
- "PST" = Postponed
- "CANC" = Cancelled

We Store (lowercase):
- "ft"
- "ns"
- "live"
```

#### Fixture Response Format
```json
{
  "fixture": {
    "id": 1379090,
    "date": "2025-11-30T15:00:00+00:00",
    "status": {
      "short": "FT",
      "long": "Match Finished"
    }
  },
  "teams": {
    "home": {
      "id": 49,              // NUMBER
      "name": "Chelsea"
    },
    "away": {
      "id": 42,              // NUMBER
      "name": "Arsenal"
    }
  },
  "goals": {
    "home": 3,
    "away": 1
  },
  "league": {
    "id": 39,                // Premier League
    "name": "Premier League",
    "season": 2025
  }
}
```

---

## 4. FRONTEND-BACKEND CONTRACT MISMATCHES

### Issue 1: Status Code Mismatch
```
Backend stores: "ft", "ns", "live"
Frontend expects: "completed", "final", "scheduled"
Fix: Frontend now checks for both
Location: CompetitionDashboard.js line 890
```

### Issue 2: Fixture Date Fields
```
Database has TWO fields:
- matchDate: "2025-11-30T15:00:00Z"
- startsAt: "2025-11-30T15:00:00Z"

Frontend reads: fixture.startsAt || fixture.matchDate
⚠️ INCONSISTENCY: Should standardize on ONE field
```

### Issue 3: Score Display
```
Frontend didn't display scores even when they existed
Fix: Added score display logic
Location: CompetitionDashboard.js line 861-868
```

---

## 5. DATA FLOW MAPS

### Flow 1: Update Scores & Calculate Points

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: CompetitionDashboard.js                           │
│ User clicks "Update Match Scores"                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ API: POST /api/fixtures/update-scores                       │
│ Handler: server.py line 278                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FUNCTION: update_fixtures_from_api()                        │
│ File: sports_data_client.py                                 │
│                                                              │
│ 1. Call API-Football: GET /fixtures?date=2025-11-30        │
│ 2. Filter: league_id=39 (Premier League)                   │
│ 3. Match: api.teams.home.id == db.homeExternalId           │
│ 4. Update: db.fixtures {goalsHome, goalsAway, status}      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ DATABASE: fixtures collection updated                       │
│ - status: "scheduled" → "ft"                                │
│ - goalsHome: null → 3                                       │
│ - goalsAway: null → 1                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Auto-trigger recompute                           │
│ POST /api/leagues/{id}/score/recompute                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FUNCTION: calculate_points_from_fixtures()                  │
│ File: scoring_service.py                                    │
│                                                              │
│ 1. Get fixtures: status="ft", leagueId=X                   │
│ 2. Transform format: {team1, team2, score}                 │
│ 3. For each club: calculate_club_points()                  │
│ 4. Update: db.league_points                                │
│ 5. Aggregate: update_standings_from_club_points()          │
│ 6. Update: db.standings                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Reload fixtures & standings                       │
│ GET /api/leagues/{id}/fixtures                              │
│ GET /api/leagues/{id}/standings                             │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: External ID Matching

```
┌─────────────────────────────────────────────────────────────┐
│ SEED SCRIPT: seed_epl_teams.py                              │
│ Creates assets with:                                        │
│ - externalId: "49" (STRING)                                 │
│ - apiFootballId: 49 (NUMBER) ← Redundant                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ DATABASE: assets collection                                 │
│ {name: "Chelsea", externalId: "49"}                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ SEED SCRIPT: seed_epl_fixtures.py                           │
│ Creates fixtures by copying:                                │
│ - homeExternalId ← assets.externalId                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ DATABASE: fixtures collection                               │
│ {homeTeam: "Chelsea", homeExternalId: "49"}                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ API-FOOTBALL: Returns fixture                               │
│ {teams: {home: {id: 49}}}  ← NUMBER                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCHING LOGIC: update_fixtures_from_api()                  │
│ str(api_fixture["teams"]["home"]["id"]) == db["homeExtId"] │
│ str(49) == "49" ✅ MATCH                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. IDENTIFIED ISSUES & FIXES

### ✅ FIXED
1. Database name confusion (using test_database correctly now)
2. Sunderland external ID mismatch (71 → 746)
3. Status code mismatch (frontend now checks "ft")
4. Fixtures not linked to leagues (now linked on creation)
5. Score display missing (now shows "Team 3 - 1 Team")
6. Manual recompute required (now automatic after score update)

### ⚠️ REMAINING INCONSISTENCIES

#### 1. Duplicate Date Fields
```
Problem: fixtures has both matchDate and startsAt
Impact: Code must check both fields
Fix Needed: Standardize on ONE field (prefer matchDate)
Effort: Database migration + code update
```

#### 2. Duplicate External ID Fields
```
Problem: assets has both externalId (string) and apiFootballId (number)
Impact: Confusion about which to use
Fix Needed: Remove apiFootballId, keep only externalId
Effort: Database cleanup + seed script update
```

#### 3. Duplicate Standings Endpoints
```
Problem: Two @api_router.get("/leagues/{id}/standings") definitions
Impact: Only second one is used, first is dead code
Fix Needed: Remove duplicate at line 1382
Effort: 5 mins
```

#### 4. Status Code Enum
```
Problem: No centralized definition of valid status codes
Impact: Hard to know what values are valid
Fix Needed: Create enum/constant file
Effort: 30 mins
```

---

## 7. CRITICAL PATHS TO AUDIT

### Path 1: Fixture Creation
```
Manual: seed_epl_fixtures.py
        ↓
    fixtures collection
        ↓
    Must have: leagueId, homeExternalId, awayExternalId, sportKey

⚠️ Risk: Forgetting leagueId means fixtures won't appear in league
```

### Path 2: Team Creation
```
Manual: seed_epl_teams.py
        ↓
    assets collection
        ↓
    Must have: externalId matching API-Football team ID

⚠️ Risk: Wrong externalId means scores won't update
```

### Path 3: Score Update
```
API-Football returns team.id as NUMBER
        ↓
    Convert to STRING: str(49)
        ↓
    Match with fixtures.homeExternalId (STRING)
        ↓
    Update if match found

⚠️ Risk: Type mismatch breaks matching
```

---

## 8. STANDARDIZATION RECOMMENDATIONS

### Immediate (Do Now)
1. ✅ Document all status codes in one place
2. ✅ Remove duplicate standings endpoint
3. ✅ Add validation: fixtures must have leagueId
4. ✅ Add validation: assets must have externalId

### Short Term (Next Sprint)
1. Standardize on matchDate (remove startsAt)
2. Remove apiFootballId (keep only externalId)
3. Create shared constants file for status codes
4. Add database schema validation

### Long Term (Post-Pilot)
1. TypeScript for type safety
2. API contract testing
3. Database migration framework
4. Automated integration tests

---

## 9. ENVIRONMENT VARIABLES

### Backend (.env)
```bash
# Database
MONGO_URL="mongodb://localhost:27017"      # ⚠️ PROTECTED - DO NOT CHANGE
DB_NAME="test_database"                     # ⚠️ CRITICAL

# API Keys
API_FOOTBALL_KEY="ce31120a..."             # External API
EMERGENT_LLM_KEY="..."                     # If using

# Monitoring
SENTRY_DSN=""                               # ⏳ PENDING
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL="..."                 # ⚠️ PROTECTED - Points to external URL
```

---

## 10. TESTING CHECKLIST

Before declaring anything "working":

1. [ ] Check database directly (not just API response)
2. [ ] Check what frontend receives (not just what backend sends)
3. [ ] Check what frontend displays (not just what it receives)
4. [ ] Verify with actual user flow (not just curl tests)
5. [ ] Check for null/undefined values
6. [ ] Check for type mismatches (string vs number)
7. [ ] Check for status code variations
8. [ ] Check logs for errors (not just success messages)

---

## SUMMARY

### Root Causes of Issues
1. **No Single Source of Truth**: Status codes, field names, types scattered across codebase
2. **Inconsistent Naming**: matchDate vs startsAt, externalId vs apiFootballId
3. **Type Confusion**: String vs Number for IDs
4. **Missing Validation**: No checks that fixtures have leagueId
5. **Assumptions in Code**: Frontend expects "completed", backend stores "ft"

### Path Forward
1. Use this document as reference for all development
2. Update document when making changes
3. Add validation at every layer
4. Standardize naming and types
5. Create automated tests for critical paths

This audit should serve as the map to prevent future issues.
