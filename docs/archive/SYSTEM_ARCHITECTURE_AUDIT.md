# SYSTEM ARCHITECTURE AUDIT - Fantasy Sports Auction Platform

**Generated:** December 2025  
**Purpose:** Complete understanding of system architecture for agent onboarding

---

## DATABASE ARCHITECTURE

### Database: `test_database` (MongoDB)

#### Core Collections & Their Purpose:

1. **`assets`** (127 documents)
   - **Purpose:** Stores teams/players that can be auctioned
   - **Key Fields:** `id`, `name`, `sportKey`, `externalId`, `competitionShort`, `competitions`, `country`, `uefaId` (optional)
   - **Sports:** football (PL, CL, AFCON), cricket
   - **Note:** AFCON teams use `competitionShort: "AFCON"` and `competitions: ["Africa Cup of Nations"]`

2. **`leagues`** (411 documents)
   - **Purpose:** Competition instances created by commissioners
   - **Key Fields:** `id`, `name`, `commissionerId`, `sportKey`, `competitionCode`, `status`, `inviteToken`, `budget`, `clubSlots`, `assetsSelected`
   - **Status values:** `draft`, `active`, `completed`
   - **Note:** `assetsSelected` is array of asset IDs chosen for this league

3. **`league_participants`** (66 documents)
   - **Purpose:** Users who have joined a league
   - **Key Fields:** `leagueId`, `userId`, `userName`, `clubsWon` (array of asset IDs), `budgetRemaining`, `totalSpent`
   - **Note:** `clubsWon` is populated during/after auction, NOT before

4. **`league_points`** (27 documents) ⭐ CRITICAL
   - **Purpose:** STORES INDIVIDUAL CLUB/TEAM POINTS FOR SCORING
   - **Key Fields:** `leagueId`, `clubId`, `clubName`, `wins`, `draws`, `losses`, `goalsScored`, `goalsConceded`, `totalPoints`
   - **Note:** This is THE source of truth for points, NOT `league_participants.points`
   - **Populated by:** `/leagues/{league_id}/score/recompute` endpoint

5. **`standings`** (114 documents)
   - **Purpose:** Aggregated league table (combines participant + their clubs' points)
   - **Key Fields:** `leagueId`, `table` (array of manager standings), `lastComputedAt`
   - **Note:** Computed from `league_points` + `league_participants`

6. **`fixtures`** (183 documents)
   - **Purpose:** Match schedules and results
   - **Key Fields:** `leagueId`, `homeTeam`, `awayTeam`, `homeAssetId`, `awayAssetId`, `startsAt`, `status`, `goalsHome`, `goalsAway`, `winner`, `source`
   - **Status values:** `scheduled`, `live`, `ft` (full-time/completed), `final`
   - **⭐ CRITICAL:** Scoring service looks for `status: "ft"`, NOT "completed"
   - **Source values:** `api`, `csv`, `manual`

7. **`auctions`** (38 documents)
   - **Purpose:** Active/completed auction state
   - **Key Fields:** `leagueId`, `status`, `currentClubId`, `clubQueue`, `bidTimer`, `timerEndsAt`
   - **Status values:** `active`, `paused`, `completed`

8. **`bids`** (225 documents)
   - **Purpose:** Individual bid records during auction
   - **Key Fields:** `auctionId`, `userId`, `clubId`, `amount`, `timestamp`

9. **`users`** (472 documents)
   - **Purpose:** User accounts
   - **Key Fields:** `id`, `name`, `email`, `createdAt`
   - **Auth:** Magic link based (no passwords)

---

## SCORING SYSTEM ARCHITECTURE

### How Points Flow Through The System:

```
1. Fixtures are imported/created
   ↓
2. Commissioner uploads scores (CSV) or API auto-updates
   ↓
3. Fixtures get `status: "ft"` + goalsHome/goalsAway/winner populated
   ↓
4. POST /leagues/{league_id}/score/recompute is called
   ↓
5. scoring_service.py → calculate_points_from_fixtures()
   ↓
6. Queries fixtures with `status: "ft"` for teams in league
   ↓
7. Calculates: Win=3pts, Draw=1pt, Goal Scored=1pt per goal
   ↓
8. Updates/creates records in `league_points` collection
   ↓
9. Aggregates by participant → updates `standings` collection
   ↓
10. UI fetches from GET /leagues/{league_id}/summary
```

### KEY SCORING RULES:

**Football:**
- Win: 3 points
- Draw: 1 point  
- Loss: 0 points
- Goals scored: 1 point per goal
- **Example:** Team wins 3-1 → 3 (win) + 3 (goals) = 6 points

**Cricket:**
- Complex player-based scoring (runs, wickets, catches, etc.)
- Stored in `cricket_leaderboard` and `league_stats` collections

---

## API ENDPOINTS - CRITICAL ONES

### Authentication
- `POST /auth/magic-link` - Request magic link
- `POST /auth/verify-magic-link` - Verify and get JWT
- `POST /auth/refresh` - Refresh access token

### League Management
- `POST /leagues` - Create new league
- `GET /leagues/{league_id}` - Get league details
- `POST /leagues/{league_id}/join` - Join with invite token
- `PUT /leagues/{league_id}/assets` - Save selected teams
- `GET /leagues/{league_id}/summary` - Get standings + participant rosters
- `DELETE /leagues/{league_id}` - Delete league (cascade)

### Fixtures
- `POST /leagues/{league_id}/fixtures/import-from-api` - Import from Football-Data.org (PL/CL)
- `POST /leagues/{league_id}/fixtures/import-csv` - Import via CSV (AFCON)
- `GET /leagues/{league_id}/fixtures` - Get all fixtures for league
- `DELETE /leagues/{league_id}/fixtures/clear` - Clear all fixtures
- `PATCH /fixtures/{fixture_id}/score` - Manually update single fixture score

### Scoring ⭐ CRITICAL
- `POST /leagues/{league_id}/score/recompute` - **Recalculate all points from fixtures**
- `POST /fixtures/update-scores` - Fetch latest scores from API (PL/CL)
- `GET /leagues/{league_id}/standings` - Get current standings

### Auction
- `POST /leagues/{league_id}/auction/start` - Start auction
- `GET /auction/{auction_id}` - Get auction state
- `POST /auction/{auction_id}/bid` - Place bid
- WebSocket events for real-time updates

### Assets/Teams
- `GET /clubs` - Get teams filtered by sport/competition
- `GET /leagues/{league_id}/available-assets` - Get teams for selection
- `GET /assets/{asset_id}/next-fixture` - Get team's next match

---

## FRONTEND ARCHITECTURE

### Key Pages:

1. **`/` (App.js)** - Home + league creation
2. **`/league/:id` (LeagueDetail.js)** - Pre-auction: team selection, fixture import, participant list
3. **`/auction/:id` (AuctionRoom.js)** - Live auction bidding interface
4. **`/competitions/:leagueId` (CompetitionDashboard.js)** - Post-auction: standings, fixtures, score upload

### Data Flow Example - AFCON CSV Upload:

```
1. User clicks "Choose File" on CompetitionDashboard (Fixtures tab)
   ↓
2. handleCSVUpload() in CompetitionDashboard.js
   ↓
3. POST /api/leagues/{leagueId}/fixtures/import-csv (multipart/form-data)
   ↓
4. Backend: server.py line 2503 - import_csv()
   ↓
5. Parses CSV, creates/updates fixtures with scores
   ↓
6. Sets status="ft" if goalsHome/goalsAway present
   ↓
7. Frontend: Automatically calls POST /api/leagues/{leagueId}/score/recompute
   ↓
8. Backend: scoring_service.py calculates points → league_points collection
   ↓
9. Frontend: Refreshes fixtures and summary to show updated standings
```

---

## COMPETITION-SPECIFIC LOGIC

### Premier League (PL)
- **Competition Code:** `PL`
- **Fixture Source:** API (Football-Data.org)
- **Import Method:** League Detail page → "Import Fixtures from API" button
- **Teams:** 20 clubs with `competitionShort: "EPL"` or `competitions: ["English Premier League"]`
- **External IDs:** Numeric (e.g., "65" for Man City)

### Champions League (CL)
- **Competition Code:** `CL` or `UCL`
- **Fixture Source:** API (Football-Data.org)
- **Import Method:** League Detail page → "Import Fixtures from API" button
- **Teams:** 36 clubs with `competitions: ["UEFA Champions League"]`
- **External IDs:** Numeric
- **Key:** Fixtures are league-specific, no cross-contamination with PL

### AFCON
- **Competition Code:** `AFCON`
- **Fixture Source:** CSV upload (API doesn't support AFCON)
- **Import Method:** Competition Dashboard → Fixtures tab → "Import Fixtures (CSV)"
- **Teams:** 24 national teams with `competitionShort: "AFCON"` and `competitions: ["Africa Cup of Nations"]`
- **External IDs:** String format `AFCON_001` through `AFCON_024`
- **CSV Template:** Available at `/api/templates/afcon_2025_fixtures_with_names.csv`
- **Template Features:** Includes `homeTeam` and `awayTeam` columns for readability (ignored by backend)

### Cricket
- **Competition Code:** Various
- **Fixture Source:** RapidAPI (Cricbuzz)
- **Scoring:** Player-based, not team-based
- **Collections:** Uses `cricket_leaderboard` and `league_stats`

---

## COMMON PITFALLS & MISTAKES TO AVOID

### 1. Wrong Collection for Points
❌ **WRONG:** Looking in `league_participants.points`  
✅ **CORRECT:** Look in `league_points` collection for individual club points

### 2. Status Value Mismatch
❌ **WRONG:** Setting fixture status to "completed"  
✅ **CORRECT:** Use status "ft" (full-time) for scoring service compatibility

### 3. Fixture Import Doesn't Auto-Calculate Points
❌ **WRONG:** Assuming CSV upload calculates points automatically  
✅ **CORRECT:** Must call `POST /leagues/{league_id}/score/recompute` after upload (now automatic in frontend)

### 4. AFCON Team Structure
❌ **WRONG:** Using `competition: "AFCON"` field only  
✅ **CORRECT:** Must have `competitionShort: "AFCON"` AND `competitions: ["Africa Cup of Nations"]` to match PL/CL structure

### 5. uefaId Field
❌ **WRONG:** Requiring uefaId for all teams  
✅ **CORRECT:** uefaId is optional (AFCON teams don't have UEFA IDs)

### 6. Assuming Data Exists
❌ **WRONG:** Checking one collection and declaring system broken  
✅ **CORRECT:** Verify data location first, understand data flow, confirm with user before declaring issues

### 7. Making Changes Without Approval
❌ **WRONG:** "Fixing" issues without confirming they exist  
✅ **CORRECT:** Investigate thoroughly, confirm with user, get approval before implementing

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI app (5600+ lines)
│   ├── models.py              # Pydantic models
│   ├── scoring_service.py     # Points calculation logic
│   ├── auction/               # Auction logic
│   │   ├── completion.py
│   │   └── ...
│   ├── services/
│   │   └── sport_service.py
│   └── .env                   # Environment variables (MONGO_URL, etc.)
│
├── frontend/
│   └── src/
│       ├── App.js             # Main app + routing + league creation
│       ├── pages/
│       │   ├── LeagueDetail.js         # Team selection, fixture import
│       │   ├── AuctionRoom.js          # Live auction
│       │   └── CompetitionDashboard.js # Post-auction management
│       └── .env               # REACT_APP_BACKEND_URL
│
├── public/
│   └── templates/
│       └── afcon_2025_fixtures_with_names.csv  # AFCON template
│
├── scripts/
│   └── add_afcon_teams.py     # Populate AFCON teams
│
└── docs/ (various .md files)
```

---

## ENVIRONMENT VARIABLES

### Backend (.env)
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name (test_database)
- `JWT_SECRET` - For token signing
- `FOOTBALL_DATA_TOKEN` - Football-Data.org API key
- `RAPIDAPI_KEY` - For cricket API

### Frontend (.env)
- `REACT_APP_BACKEND_URL` - Backend API URL (production URL, not localhost)

⭐ **CRITICAL:** Never hardcode URLs or ports. Always use environment variables.

---

## TESTING CHECKLIST

Before declaring any feature "broken":

1. ✅ Verify you're looking in the correct database collection
2. ✅ Check the correct fields (e.g., `league_points.totalPoints` not `league_participants.points`)
3. ✅ Confirm the user's observation (ask for screenshots/details)
4. ✅ Test the actual API endpoint response, not just database
5. ✅ Check frontend console for errors
6. ✅ Review recent code changes that might affect the feature
7. ✅ Get user approval before implementing any "fix"

---

## SUMMARY - KEY TAKEAWAYS

1. **Points are stored in `league_points` collection**, aggregated in `standings`
2. **Fixture status must be "ft"** for scoring service to process
3. **CSV upload doesn't auto-calculate points** - must call recompute endpoint
4. **AFCON teams need specific structure** matching PL/CL (competitionShort + competitions fields)
5. **Always verify data location** before declaring issues
6. **Get user confirmation** before implementing changes
7. **The system works** - verify assumptions before "fixing"

---

**Last Updated:** December 6, 2025  
**Version:** 1.0
