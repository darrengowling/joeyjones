# Emergency Project Rebuild Prompt - UPDATED December 2025

**⚠️ CRITICAL: Use this prompt to recreate the Fantasy Sports Auction Platform from scratch**

Last Updated: December 9, 2025  
Current Production Version: Fully functional multi-sport auction platform

---

## 🎯 Project Overview

Build a **multi-sport fantasy auction platform** enabling users to create private leagues, conduct live player auctions via Socket.IO, and manage tournaments with automated scoring for **Football (Soccer)** and **Cricket**.

---

## 🏗️ Core Architecture

### Tech Stack (VERIFIED CURRENT)
- **Frontend**: React 18 + Tailwind CSS + shadcn/ui + Socket.IO Client + React Router v6 + axios + react-hot-toast
- **Backend**: FastAPI (Python 3.10+) + python-socketio + Motor (async MongoDB) + PyJWT
- **Database**: MongoDB (single database: `test_database`)
- **Real-time**: Socket.IO with Redis adapter for multi-pod production (optional for single-pod)
- **Authentication**: Magic Link (email-based, no passwords)

### Project Structure (VERIFIED)
```
/app/
├── backend/
│   ├── server.py                    # Monolithic FastAPI (ALL routes in one file)
│   ├── auth.py                      # JWT + Magic Link generation
│   ├── socketio_init.py             # Socket.IO server with conditional Redis
│   ├── scoring_service.py           # Point calculation (CRITICAL: uses exact name matching)
│   ├── football_data_client.py      # Football-Data.org API wrapper
│   ├── rapidapi_client.py           # Cricbuzz API wrapper
│   ├── models.py                    # Pydantic models (MUST include usersInWaitingRoom)
│   ├── seed_openfootball_clubs.py   # Seed football clubs
│   ├── seed_ashes_players.py        # Seed cricket players
│   └── .env                         # Backend env vars
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── MyCompetitions.js    # Home page + auth (NO separate Login.js)
│       │   ├── CreateLeague.js      # League creation + club selection
│       │   ├── LeagueDetail.js      # Pre-auction: waiting room, participants
│       │   ├── AuctionRoom.js       # Live bidding (Socket.IO)
│       │   ├── CompetitionDashboard.js  # Post-auction: standings, fixtures
│       │   ├── ClubsList.js         # Browse all clubs
│       │   └── Help.js              # User guide
│       ├── components/
│       │   ├── ui/                  # shadcn/ui components
│       │   └── DebugFooter.js       # Shows build hash + backend URL
│       └── utils/
│           ├── socket.js            # Socket.IO client setup
│           └── sentry.js            # Error tracking (optional)
```

---

## 📊 Database Schema (MongoDB) - VERIFIED CURRENT STATE

### Database Name
- **ONLY ONE DATABASE**: `test_database`
- Collections: `users`, `leagues`, `league_participants`, `auctions`, `bids`, `assets`, `fixtures`, `league_points`, `standings`, `sports`, `cricket_leaderboard`, `league_stats`, `magic_links`

### Collection: `users`
```javascript
{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "User Name",
  "createdAt": "2025-01-01T00:00:00+00:00"  // ISO string with timezone
}
```
⚠️ **NO PASSWORD FIELD** - uses magic link authentication

### Collection: `leagues`
```javascript
{
  "id": "uuid-string",
  "name": "My League",
  "commissionerId": "user-id",
  "sportKey": "football" | "cricket",
  "competitionCode": "CL" | "PL" | "AFCON",
  "status": "draft" | "auction_pending" | "auction_live" | "active" | "completed",
  "budget": 500000000,  // Budget in smallest unit (pence for £)
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,
  "timerSeconds": 30,
  "antiSnipeSeconds": 10,
  "inviteToken": "6-char-string",
  "assetsSelected": ["asset-id-1", "asset-id-2"],  // Selected clubs/players
  "createdAt": "2025-01-01T00:00:00+00:00",
  "scoringOverrides": {}  // Optional custom scoring rules
}
```

### Collection: `league_participants` (CRITICAL)
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "userId": "user-id",
  "userName": "Display Name",
  "userEmail": "user@example.com",
  "budgetRemaining": 500000000,
  "clubsWon": ["asset-id-1", "asset-id-2"],  // Clubs won in auction
  "totalSpent": 150000000,
  "joinedAt": "2025-01-01T00:00:00+00:00"
}
```
⚠️ **CRITICAL**: Points are NOT in this collection

### Collection: `auctions`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "status": "waiting" | "active" | "paused" | "completed",
  "currentClubId": "asset-id",  // Current lot
  "currentLotId": "lot-id",
  "bidTimer": 30,
  "antiSnipeSeconds": 10,
  "timerEndsAt": "2025-01-01T00:00:30+00:00",
  "clubQueue": ["asset-id-1", "asset-id-2"],  // Upcoming lots
  "unsoldClubs": ["asset-id-3"],  // Clubs with no bids
  "minimumBudget": 1000000,
  "currentBid": 5000000,
  "currentBidder": {"userId": "user-id", "displayName": "Name"},
  "bidSequence": 42,  // Monotonic counter for bid updates
  "usersInWaitingRoom": ["user-id-1", "user-id-2"],  // CRITICAL: Track who entered
  "pausedAt": "2025-01-01T00:00:00+00:00",  // If paused
  "pausedRemainingTime": 15,  // Seconds remaining when paused
  "createdAt": "2025-01-01T00:00:00+00:00",
  "completedAt": "2025-01-01T00:00:00+00:00"
}
```

### Collection: `assets` (CRITICAL - ALL clubs AND players)
```javascript
// Football club
{
  "id": "uuid-string",
  "sportKey": "football",
  "name": "Chelsea FC",  // ⚠️ MUST match API exactly for scoring
  "externalId": "61",  // Football-Data.org team ID
  "competitions": ["UEFA Champions League", "English Premier League"],  // Array of strings
  "competitionShort": "PL",
  "city": "London",
  "country": "England",
  "logo": "https://...",
  "createdAt": "2025-01-01T00:00:00+00:00",
  "updatedAt": "2025-01-01T00:00:00+00:00"
}

// Cricket player
{
  "id": "uuid-string",
  "sportKey": "cricket",
  "name": "Player Name",
  "externalId": "cricapi-player-id",
  "meta": {
    "role": "Batsman" | "Bowler" | "All-rounder" | "Wicket-keeper",
    "team": "Country Name"
  },
  "createdAt": "2025-01-01T00:00:00+00:00",
  "updatedAt": "2025-01-01T00:00:00+00:00"
}
```
⚠️ **CRITICAL**: 
- NO separate `clubs` or `teams` collection
- Filter by `sportKey: "football"` for clubs
- Filter by `sportKey: "cricket"` for players
- Competition names MUST be exact: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"

### Collection: `fixtures`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",  // ⚠️ CRITICAL: MUST have leagueId for scoring
  "sportKey": "football" | "cricket",
  "homeTeam": "Chelsea FC",  // Exact team name from API
  "awayTeam": "Arsenal FC",
  "homeTeamId": "asset-id",  // Link to assets collection
  "awayTeamId": "asset-id",
  "homeAssetId": "asset-id",  // Duplicate field (legacy)
  "awayAssetId": "asset-id",
  "startsAt": "2025-01-15T15:00:00+00:00",
  "status": "ns" | "live" | "ft" | "scheduled" | "completed",  // ⚠️ "ft" for finished
  "goalsHome": 2,
  "goalsAway": 1,
  "winner": "home" | "away" | "draw",
  "externalMatchId": "football-data-fixture-id",
  "footballDataId": 551918,  // Football-Data.org ID
  "source": "api" | "csv",
  "round": "Matchday 1",
  "venue": "Stadium Name",
  "autoScoringEnabled": true,
  "createdAt": "2025-01-01T00:00:00+00:00",
  "updatedAt": "2025-01-01T00:00:00+00:00"
}
```

### Collection: `league_points` (⭐ SOURCE OF TRUTH FOR SCORING)
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "clubId": "asset-id",
  "clubName": "Chelsea FC",
  "wins": 5,
  "draws": 2,
  "losses": 3,
  "goalsScored": 15,
  "goalsConceded": 10,
  "totalPoints": 32,  // (wins * 3) + (draws * 1) + goalsScored
  "lastUpdated": "2025-01-01T00:00:00+00:00"
}
```
⚠️ **CRITICAL**: This is WHERE points are calculated and stored

### Collection: `standings` (Aggregated view)
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "userId": "user-id",
  "userName": "Display Name",
  "totalPoints": 95,
  "clubs": [
    {
      "clubId": "asset-id",
      "clubName": "Chelsea FC",
      "points": 32
    }
  ],
  "lastUpdated": "2025-01-01T00:00:00+00:00"
}
```

### Collection: `sports`
```javascript
{
  "key": "football" | "cricket",
  "name": "Football" | "Cricket",
  "enabled": true,
  "scoringRules": {
    "win": 3,
    "draw": 1,
    "goalScored": 1,
    "goalConceded": 0
    // ... more rules
  }
}
```

---

## 🔐 Authentication - Magic Link (NO PASSWORDS)

### Implementation
1. User enters email
2. Backend generates 6-digit code, stores in `magic_links` collection
3. Backend sends email (or shows code in dev mode)
4. User enters code
5. Backend validates, returns JWT tokens (access + refresh)

### JWT Tokens
```python
# Access token (short-lived)
{
  "user_id": "uuid",
  "email": "user@example.com",
  "exp": timestamp  # 15 minutes
}

# Refresh token (long-lived)
{
  "user_id": "uuid",
  "type": "refresh",
  "exp": timestamp  # 7 days
}
```

### Protected Routes
- All `/api/leagues/*` require valid JWT
- Commissioner-only: start auction, delete league, import fixtures
- Verify `commissionerId` matches `user_id` from token

---

## 🎮 Critical Features & Implementation

### 1. Auction System (Socket.IO Real-time)

**Socket Events (Client → Server)**:
- `join_auction`: User enters auction room
  ```javascript
  { auctionId: "id", userId: "user-id" }
  ```
  - Add to room: `auction:{auction_id}`
  - Add to `usersInWaitingRoom` array in auctions collection
  - Broadcast `waiting_room_updated` to all in room
  - Send `auction_snapshot` to joining user

- `place_bid`: User places bid
  ```javascript
  { auctionId: "id", amount: 10000000, userId: "user-id" }
  ```
  - Validate: amount > currentBid, user has budget
  - Update auction document
  - Increment `bidSequence` (monotonic counter)
  - Broadcast `bid_update` to all in room
  - Reset timer (anti-snipe)

**Socket Events (Server → Client)**:
- `waiting_room_updated`: Participant list changed
  ```javascript
  { usersInWaitingRoom: ["user-id-1", "user-id-2"] }
  ```
- `auction_snapshot`: Full state (on join)
- `bid_update`: New bid placed
- `tick`: Timer countdown
- `auction_lot_won`: Lot completed
- `auction_complete`: All lots finished

**Timer Logic (CRITICAL)**:
- Use `asyncio.create_task()` for countdown
- Store task reference, cancel on new bid
- On timer expiry:
  - Award club to currentBidder
  - Deduct amount from winner's budget
  - Add to clubsWon array
  - Move to next lot or complete

**Redis for Production (Multi-pod)**:
```python
# socketio_init.py
if os.getenv('REDIS_URL'):
    mgr = socketio.AsyncRedisManager(os.getenv('REDIS_URL'))
    sio = socketio.AsyncServer(async_mode='asgi', client_manager=mgr)
else:
    sio = socketio.AsyncServer(async_mode='asgi')
```

### 2. Fixture Import

**Football (API)**: `POST /api/leagues/{league_id}/fixtures/import-from-api`
```python
# Use Football-Data.org API
GET https://api.football-data.org/v4/competitions/{code}/matches
# code: "CL" or "PL"

# For each match:
# 1. Match team names using FUZZY logic (substring matching)
# 2. Create fixture with homeTeamId, awayTeamId
# 3. Store footballDataId for score updates
# 4. MUST include leagueId field
```

**Cricket (Manual CSV)**: `POST /api/leagues/{league_id}/fixtures/import-csv`

### 3. Score Updates

**Endpoint**: `GET /api/leagues/{league_id}/fixtures/update-scores`

**Process**:
1. Fetch latest scores from Football-Data.org API
2. Find fixtures by `footballDataId`
3. Update `goalsHome`, `goalsAway`, `status: "ft"`, `winner`
4. ⚠️ ONLY updates fixtures, does NOT calculate points

### 4. Score Calculation (CRITICAL)

**Endpoint**: `POST /api/leagues/{league_id}/score/recompute`

**Process (`scoring_service.py`)**:
```python
# 1. Get league's selected assets
assets = await db.assets.find({"id": {"$in": league.assetsSelected}})
team_names = [asset["name"] for asset in assets]

# 2. Find completed fixtures FOR THIS LEAGUE
fixtures = await db.fixtures.find({
    "leagueId": league_id,  # ⚠️ CRITICAL: Filter by leagueId
    "status": "ft",
    "sportKey": "football",
    "$or": [
        {"homeTeam": {"$in": team_names}},  # ⚠️ EXACT match required
        {"awayTeam": {"$in": team_names}}
    ]
})

# 3. Calculate points for each team
# Win: 3 pts, Draw: 1 pt, Goal: 1 pt

# 4. Store in league_points collection
```

⚠️ **CRITICAL REQUIREMENTS**:
- Fixture `status` MUST be "ft" (not "completed")
- Team names in `assets` MUST match `fixtures` exactly
- MUST filter by `leagueId` to avoid counting duplicates
- Scoring uses EXACT name matching, fixture import uses FUZZY

---

## 🔌 Third-Party Integrations

### Football-Data.org API
```python
headers = {"X-Auth-Token": os.getenv("FOOTBALL_DATA_TOKEN")}
GET https://api.football-data.org/v4/competitions/CL/matches
GET https://api.football-data.org/v4/competitions/PL/matches
```

**Team Names MUST Match Exactly**:
- Store in database: "Chelsea FC" (not "Chelsea")
- Store in database: "Atalanta BC" (not "Atalanta")
- See `/app/TEAM_UPDATES_COMPLETED.md` for full list

### Cricbuzz API (via RapidAPI)
```python
headers = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}
GET https://cricbuzz-cricket.p.rapidapi.com/series/v1/{seriesId}
```

---

## ⚠️ CRITICAL Gotchas (MUST READ)

### 1. Team Names MUST Match API Exactly
**Problem**: Scoring uses exact MongoDB `$in` matching. If DB has "Chelsea" but fixtures have "Chelsea FC", scoring fails.

**Solution**: All team names in `assets` collection MUST match Football-Data.org API exactly:
- "Chelsea FC" (not "Chelsea")
- "Arsenal FC" (not "Arsenal")
- "Club Atlético de Madrid" (not "Atlético de Madrid")

See `/app/TEAM_UPDATES_COMPLETED.md` for complete list of 56 verified teams.

### 2. Fixture Import vs Scoring - Different Matching
- **Fixture Import**: Uses FUZZY substring matching (forgiving)
- **Scoring**: Uses EXACT matching (strict)

This is why fixtures import successfully but scoring fails if names don't match exactly.

### 3. leagueId MUST Be in Fixtures
**Problem**: Without `leagueId` filter in scoring query, same fixture counted multiple times if multiple leagues imported it.

**Solution**: ALWAYS include `leagueId: league_id` in fixture find query.

### 4. MongoDB DateTime Serialization
**Problem**: Python `datetime` objects cause JSON serialization errors.

**Solution**: ALWAYS use `.isoformat()`:
```python
"createdAt": datetime.now(timezone.utc).isoformat()
```

### 5. MongoDB _id Field
**Problem**: Auto-generated ObjectId can't be JSON serialized.

**Solution**: ALWAYS exclude `_id`:
```python
db.collection.find({}, {"_id": 0})
```

### 6. CORS Configuration
```python
# FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Socket.IO
sio = socketio.AsyncServer(
    cors_allowed_origins=os.getenv("CORS_ORIGINS").split(",")
)
```

### 7. Frontend Environment Variables
- NEVER hardcode URLs
- ALWAYS use `process.env.REACT_APP_BACKEND_URL`

### 8. Pydantic Models MUST Include usersInWaitingRoom
```python
# models.py - Auction model
class Auction(BaseModel):
    # ... other fields
    usersInWaitingRoom: Optional[List[str]] = []  # CRITICAL for waiting room
```

### 9. Socket.IO userId from Event Data
```python
# Backend receives userId in event data, NOT from session
@sio.on('join_auction')
async def join_auction(sid, data):
    user_id = data.get('userId')  # From client
```

---

## 🚀 Environment Variables

### Backend `.env` (VERIFIED)
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET="your-secret-key-here"
FOOTBALL_DATA_TOKEN="your-token-here"
RAPIDAPI_KEY="your-key-here"
REDIS_URL=""  # Optional: for multi-pod production
```

### Frontend `.env` (VERIFIED)
```bash
REACT_APP_BACKEND_URL="http://localhost:8001"
```

---

## 📦 Key Dependencies (CURRENT)

### Backend
```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
motor>=3.3.1
pymongo>=4.5.0
python-socketio>=5.10.0
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
python-multipart
pydantic>=2.4.2
python-dotenv
httpx
```

### Frontend
```json
{
  "react": "^18.2.0",
  "react-router-dom": "^6.x",
  "socket.io-client": "^4.x",
  "axios": "^1.x",
  "tailwindcss": "^3.x",
  "react-hot-toast": "^2.x"
}
```

---

## 🧪 Testing Checklist

### 1. Authentication
- [ ] User enters email, receives magic link code
- [ ] User enters code, receives JWT tokens
- [ ] Protected routes reject invalid tokens
- [ ] Token refresh works on 401

### 2. League Creation
- [ ] Create league with selected clubs
- [ ] Invite token generated
- [ ] Commissioner joins automatically

### 3. Participant Flow
- [ ] Join with valid token
- [ ] Reject invalid token
- [ ] Budget initialized correctly

### 4. Auction Flow (Socket.IO)
- [ ] Multiple users join waiting room
- [ ] Participant count updates in real-time
- [ ] Start auction (commissioner only)
- [ ] Place bids with validation
- [ ] Timer resets on new bid (anti-snipe)
- [ ] Lot completes, winner assigned
- [ ] Budget deducted
- [ ] Progress to next lot
- [ ] Auction completes

### 5. Fixtures & Scoring
- [ ] Import CL fixtures (Chelsea FC, Arsenal FC match exactly)
- [ ] Import PL fixtures
- [ ] Update scores from API
- [ ] Recompute points (check league_points collection)
- [ ] Standings update correctly
- [ ] Verify no duplicate counting (leagueId filter working)

---

## 🎯 Build Priority

1. **Infrastructure** (Day 1-2)
   - MongoDB connection
   - Magic link auth
   - JWT middleware

2. **League Management** (Day 3-4)
   - Create/join leagues
   - Club selection
   - Participant management

3. **Auction System** (Day 5-7)
   - Socket.IO setup with Redis option
   - Bidding logic with anti-snipe
   - Waiting room tracking
   - Timer system

4. **Fixtures & Scoring** (Day 8-9)
   - Football-Data.org integration
   - Fixture import with leagueId
   - Score updates
   - Points calculation (exact name matching)

5. **Testing & Polish** (Day 10)
   - End-to-end flows
   - Bug fixes
   - Verify all 56 team names match API

---

## 📞 Critical Files Reference

- `/app/SYSTEM_ARCHITECTURE_AUDIT.md` - Complete system documentation
- `/app/TEAM_UPDATES_COMPLETED.md` - All 56 verified team names
- `/app/AGENT_ONBOARDING_PROMPT.md` - Common mistakes to avoid
- `/app/WAITING_ROOM_FIX_COMPLETE.md` - Socket.IO implementation details

---

## ✅ Success Criteria

Platform rebuilt successfully when:
1. ✅ Magic link auth works
2. ✅ Multiple users can create/join leagues
3. ✅ Real-time auction with anti-snipe timer
4. ✅ Waiting room shows live participant count
5. ✅ CL/PL fixtures import successfully
6. ✅ Score updates work from API
7. ✅ Points calculate correctly (all 56 teams)
8. ✅ Standings display correctly
9. ✅ No duplicate point counting

---

**This document contains VERIFIED CURRENT STATE as of December 9, 2025. Treat as source of truth for rebuild.**
