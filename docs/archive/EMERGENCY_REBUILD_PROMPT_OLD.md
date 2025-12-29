# Emergency Project Rebuild Prompt

Use this prompt to recreate the Fantasy Sports Auction Platform from scratch in a new environment (Emergent or other development platform).

---

## 🎯 Project Overview

Build a **multi-sport fantasy auction platform** that enables users to create private competitions, conduct live player auctions, and manage ongoing tournaments with automated scoring for both **Football (Soccer)** and **Cricket**.

---

## 🏗️ Core Architecture

### Tech Stack Requirements
- **Frontend**: React 18 + Tailwind CSS + shadcn/ui components + Socket.IO Client + React Router v6
- **Backend**: FastAPI (Python 3.10+) + python-socketio + JWT authentication + Motor (async MongoDB driver)
- **Database**: MongoDB with collections: users, leagues, auctions, fixtures, assets, sports, participants
- **Real-time**: Socket.IO for bidirectional WebSocket communication

### Project Structure
```
/app/
├── backend/
│   ├── server.py                    # Monolithic FastAPI app (all routes in one file)
│   ├── auth.py                      # JWT token generation/validation
│   ├── socketio_init.py             # Socket.IO server configuration
│   ├── scoring_service.py           # Point calculation logic
│   ├── football_data_client.py      # Football-Data.org API wrapper
│   ├── rapidapi_client.py           # Cricbuzz API wrapper (via RapidAPI)
│   ├── seed_openfootball_clubs.py   # Seed football players
│   ├── seed_ashes_players.py        # Seed cricket players
│   └── .env                         # Backend environment variables
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Login.js
│       │   ├── Register.js
│       │   ├── MyCompetitions.js    # List user's competitions
│       │   ├── CreateLeague.js      # Competition creation + player selection
│       │   ├── LeagueDetail.js      # Pre-auction team management
│       │   ├── CompetitionDashboard.js  # Post-auction: standings, fixtures, scores
│       │   └── AuctionRoom.js       # Live bidding interface
│       └── components/ui/           # shadcn/ui components (button, card, dialog, etc.)
```

---

## 📊 Database Schema (MongoDB)

### Collection: `users`
```javascript
{
  "id": "uuid-string",
  "email": "user@example.com",
  "password": "bcrypt-hashed-password",
  "name": "User Name",
  "createdAt": "2024-01-01T00:00:00Z"  // ISO string
}
```

### Collection: `leagues` (Competitions)
```javascript
{
  "id": "uuid-string",
  "name": "Competition Name",
  "sport": "Football" | "Cricket",
  "commissionerId": "user-id",
  "participants": [
    {
      "userId": "user-id",
      "userName": "Display Name",
      "budget": 100.0,
      "squad": ["asset-id-1", "asset-id-2"],
      "totalSpent": 50.0
    }
  ],
  "settings": {
    "initialBudget": 100.0,
    "maxSquadSize": 11,
    "minBid": 1.0,
    "bidIncrement": 0.5,
    "timerDuration": 30
  },
  "inviteToken": "random-6-char-string",
  "selectedAssets": ["asset-id-1", "asset-id-2"],  // Player pool
  "createdAt": "2024-01-01T00:00:00Z",  // ISO string
  "status": "draft" | "auction_pending" | "active"
}
```

### Collection: `auctions`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "status": "waiting" | "active" | "completed",
  "currentLot": {
    "assetId": "asset-id",
    "currentBid": 5.0,
    "currentBidder": "user-id",
    "timerEnd": "2024-01-01T00:00:30Z"  // ISO string
  },
  "lots": [
    {
      "assetId": "asset-id",
      "winnerId": "user-id" | null,
      "finalPrice": 10.0,
      "allBids": [
        {"userId": "user-id", "amount": 5.0, "timestamp": "ISO-string"}
      ]
    }
  ],
  "lotIndex": 0,
  "createdAt": "2024-01-01T00:00:00Z"  // ISO string
}
```

### Collection: `assets` (Players)
```javascript
{
  "id": "uuid-string",
  "name": "Player Name",
  "sport": "Football" | "Cricket",
  "competition": "Premier League" | "Ashes" | "La Liga",
  "position": "Forward" | "Midfielder" | "Defender" | "Goalkeeper",  // Football
  "role": "Batsman" | "Bowler" | "All-rounder" | "Wicket-keeper",   // Cricket
  "meta": {
    "teamName": "Club/Country Name",
    "nationality": "Country Code",
    "externalId": "api-provider-player-id"
  },
  "createdAt": "2024-01-01T00:00:00Z",  // ⚠️ MUST BE ISO STRING, NOT datetime object
  "updatedAt": "2024-01-01T00:00:00Z"   // ⚠️ MUST BE ISO STRING, NOT datetime object
}
```

### Collection: `fixtures`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "sport": "Football" | "Cricket",
  "homeTeam": "Team Name",
  "awayTeam": "Team Name",
  "date": "2024-01-15T15:00:00Z",  // ISO string
  "status": "scheduled" | "in_progress" | "completed",
  "externalId": "api-provider-fixture-id",
  "scores": {
    "home": 2,
    "away": 1
  },
  "playerScores": [
    {"assetId": "player-id", "points": 10}
  ],
  "createdAt": "2024-01-01T00:00:00Z"  // ISO string
}
```

### Collection: `sports`
```javascript
{
  "name": "Cricket" | "Football",
  "rules": {
    "run": 1,
    "four": 5,
    "six": 10,
    "wicket": 25,
    // ... full scoring rules
  }
}
```

---

## 🔐 Authentication & Authorization

### JWT Implementation
- Use PyJWT library
- Token contains: `{"user_id": "uuid", "email": "user@example.com", "exp": timestamp}`
- Secret key stored in `JWT_SECRET` environment variable
- Token passed in `Authorization: Bearer <token>` header

### Protected Routes
- All `/api/leagues/*` endpoints require valid JWT (except GET list)
- Commissioner-only actions: start auction, delete league, import fixtures
- Verify `commissionerId` matches `user_id` from JWT token

---

## 🎮 Critical Features & Workflows

### 1. Competition Creation (Commissioner Flow)

**Endpoint**: `POST /api/leagues`

```python
# Request body
{
  "name": "My Competition",
  "sport": "Football",
  "settings": {
    "initialBudget": 100.0,
    "maxSquadSize": 11,
    "minBid": 1.0,
    "bidIncrement": 0.5,
    "timerDuration": 30
  },
  "selectedAssets": ["asset-id-1", "asset-id-2", ...]  # Player pool
}

# Response
{
  "id": "league-id",
  "inviteToken": "ABC123"
}
```

**Important**: 
- Generate 6-character `inviteToken` for participants to join
- Initialize commissioner as first participant with full budget
- Set `status: "draft"`

### 2. Participant Join

**Endpoint**: `POST /api/leagues/{league_id}/join`

```python
# Request body
{
  "inviteToken": "ABC123"
}

# Action
- Verify token matches league.inviteToken
- Add user to league.participants array
- Initialize with full budget and empty squad
```

### 3. Auction System (Real-time Socket.IO)

**Socket Events to Implement**:

**Client → Server**:
- `join_auction`: User joins auction room
  - Add to Socket.IO room: `auction_{auction_id}`
  - Emit current auction state to user

- `place_bid`: User places bid
  ```javascript
  {
    "auctionId": "auction-id",
    "amount": 10.0
  }
  ```
  - Validate: amount > currentBid, user has budget, user hasn't won this lot
  - Update `currentLot.currentBid` and `currentBidder`
  - Reset timer to full duration (anti-snipe)
  - Broadcast `bid_placed` to all clients in room

- `leave_auction`: User disconnects

**Server → Client**:
- `auction_state`: Full auction state (sent on join or state change)
- `bid_placed`: New bid notification
  ```javascript
  {
    "assetId": "player-id",
    "amount": 10.0,
    "bidderName": "User Name",
    "timeRemaining": 30
  }
  ```
- `lot_won`: Current lot completed
- `new_lot`: Next player up for auction
- `auction_complete`: All lots finished

**Timer Logic**:
- Use Python `asyncio.create_task()` for countdown
- Store timer task in memory, cancel on new bid
- On timer expiry:
  - Award player to `currentBidder`
  - Deduct `currentBid` from winner's budget
  - Add asset to winner's squad
  - Emit `lot_won`
  - Move to next lot or complete auction

### 4. Fixture Import

**Football**: `POST /api/leagues/{league_id}/fixtures/import-football`
- Use Football-Data.org API
- Filter fixtures by competition (e.g., Premier League)
- Create fixture documents linked to league
- Map team names to match format

**Cricket**: `POST /api/leagues/{league_id}/fixtures/import-next-cricket`
- Use Cricbuzz API via RapidAPI: `/series/v1/9107` (Ashes series ID)
- Filter for fixtures AFTER league creation date
- Import only the NEXT upcoming match
- **Critical**: Cricbuzz `/matches/v1/upcoming` is unreliable for future dates

### 5. Scoring System

**Endpoint**: `POST /api/leagues/{league_id}/fixtures/{fixture_id}/scores/upload`

```python
# CSV Upload format
player_name,player_id,stat_type,value
"Player Name","asset-id","runs",50
"Player Name","asset-id","wickets",2
```

**Processing**:
1. Parse CSV
2. Lookup scoring rules from `sports` collection
3. Calculate points: `points = sum(rule[stat_type] * value for each stat)`
4. Update fixture.playerScores
5. Recalculate league standings:
   ```python
   for participant in league.participants:
       total_points = sum(
           fixture.playerScores[asset_id].points 
           for asset_id in participant.squad
       )
   ```
6. Sort participants by total_points descending

---

## 🔌 Third-Party Integrations

### Football-Data.org API
```python
# Required header
headers = {"X-Auth-Token": os.getenv("FOOTBALL_DATA_TOKEN")}

# Endpoints
GET https://api.football-data.org/v4/competitions/PL/matches
GET https://api.football-data.org/v4/matches/{match_id}
```

### Cricbuzz API (via RapidAPI)
```python
# Required headers
headers = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}

# Endpoints
GET https://cricbuzz-cricket.p.rapidapi.com/series/v1/9107  # Ashes series
```

**Ashes Series ID**: 9107

---

## ⚠️ Critical Gotchas & Lessons Learned

### 1. MongoDB DateTime Serialization
**Problem**: Python `datetime` objects cause `TypeError: Object of type datetime is not JSON serializable` during auctions.

**Solution**: 
- Always store dates as ISO-formatted strings: `datetime.now(timezone.utc).isoformat()`
- Never insert Python `datetime` objects directly into MongoDB
- When seeding players, use:
  ```python
  "createdAt": datetime.now(timezone.utc).isoformat(),
  "updatedAt": datetime.now(timezone.utc).isoformat()
  ```

### 2. MongoDB `_id` Field
**Problem**: MongoDB auto-generates ObjectId `_id` field, which can't be JSON serialized.

**Solution**: 
- Always exclude `_id` in queries: `db.collection.find({}, {"_id": 0})`
- Use custom `id` field (UUID string) as primary key

### 3. CORS Configuration
**Problem**: Frontend can't connect to backend due to CORS errors.

**Solution**:
```python
# In FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 4. Socket.IO CORS
**Problem**: Socket.IO connections fail even with FastAPI CORS configured.

**Solution**:
```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=os.getenv("CORS_ORIGINS").split(",")
)
```

### 5. Frontend API Base URL
**Problem**: Hardcoded URLs break across environments.

**Solution**:
- Always use `process.env.REACT_APP_BACKEND_URL` in frontend
- Never hardcode `http://localhost:8001` or production URLs

### 6. Cricket API Endpoint Selection
**Problem**: Cricbuzz `/matches/v1/upcoming` doesn't return future Test matches.

**Solution**: 
- Use series endpoint: `/series/v1/{seriesId}` 
- Parse full series schedule
- Filter for upcoming matches after league creation date

---

## 🎨 Frontend Key Components

### Player Card Component Pattern
```javascript
// Reusable card for displaying players
<div className="border rounded-lg p-4">
  <h3 className="font-bold">{player.name}</h3>
  <p className="text-sm text-gray-600">{player.meta.teamName}</p>
  <p className="text-sm">{player.position || player.role}</p>
  {player.meta.nationality && (
    <p className="text-xs text-gray-500">
      Nationality: {player.meta.nationality}
    </p>
  )}
</div>
```

### Socket.IO Integration Pattern
```javascript
import io from 'socket.io-client';

const socket = io(process.env.REACT_APP_BACKEND_URL);

// Join auction
socket.emit('join_auction', { auctionId });

// Listen for updates
socket.on('auction_state', (data) => {
  // Update UI with full auction state
});

socket.on('bid_placed', (data) => {
  // Show toast notification
});

// Place bid
const placeBid = (amount) => {
  socket.emit('place_bid', { auctionId, amount });
};
```

### Protected Route Pattern
```javascript
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};
```

---

## 🚀 Environment Variables

### Backend `.env`
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="fantasy_sports_db"
CORS_ORIGINS="http://localhost:3000"
FRONTEND_ORIGIN="http://localhost:3000"
JWT_SECRET="change-in-production"
JWT_SECRET_KEY="change-in-production"
SPORTS_CRICKET_ENABLED=true
FEATURE_MY_COMPETITIONS=true
FEATURE_ASSET_SELECTION=true
FEATURE_WAITING_ROOM=true
API_FOOTBALL_KEY="your-key-here"
FOOTBALL_DATA_TOKEN="your-key-here"
RAPIDAPI_KEY="your-key-here"
CRICAPI_KEY="multisport-auction"
REDIS_URL=""
ENABLE_RATE_LIMITING=false
ENABLE_METRICS=true
SENTRY_DSN=""
ENV="development"
```

### Frontend `.env`
```bash
REACT_APP_BACKEND_URL="http://localhost:8001"
WDS_SOCKET_PORT=3000
REACT_APP_FEATURE_MY_COMPETITIONS=true
REACT_APP_FEATURE_ASSET_SELECTION=true
REACT_APP_SENTRY_DSN=""
```

---

## 📦 Key Dependencies

### Backend `requirements.txt`
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.1
pymongo==4.5.0
python-socketio==5.10.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.4.2
python-dotenv==1.0.0
httpx==0.25.0
```

### Frontend `package.json` (key dependencies)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.18.0",
    "socket.io-client": "^4.5.4",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.5"
  }
}
```

---

## 🧪 Testing Checklist

### 1. Authentication Flow
- [ ] Register new user
- [ ] Login and receive JWT token
- [ ] Access protected route with token
- [ ] Reject request with invalid/missing token

### 2. Competition Creation
- [ ] Create football competition
- [ ] Create cricket competition
- [ ] Verify invite token generated
- [ ] Non-commissioner can't delete league

### 3. Participant Flow
- [ ] Join with valid invite token
- [ ] Reject invalid token
- [ ] Verify participant added with full budget

### 4. Auction Flow
- [ ] Start auction (commissioners only)
- [ ] All participants receive `auction_state` via Socket.IO
- [ ] Place valid bid (amount > current, user has budget)
- [ ] Reject invalid bid (insufficient funds)
- [ ] Timer resets on new bid (anti-snipe)
- [ ] Lot completes on timer expiry
- [ ] Winner's budget deducted
- [ ] Asset added to winner's squad
- [ ] Progress to next lot
- [ ] Auction completes after all lots

### 5. Fixture Import
- [ ] Import football fixtures (Football-Data.org)
- [ ] Import next cricket fixture (Cricbuzz)
- [ ] Fixtures display on dashboard
- [ ] Fixtures linked to correct league

### 6. Scoring
- [ ] Upload CSV with player stats
- [ ] Points calculated correctly
- [ ] Standings updated
- [ ] Dashboard shows updated league table

---

## 🎯 Build Priority Order

1. **Phase 1: Core Infrastructure** (Day 1-2)
   - Set up MongoDB connection
   - Implement JWT authentication
   - Create user registration/login endpoints and pages

2. **Phase 2: Competition Management** (Day 3-4)
   - League creation endpoint and UI
   - Participant join flow
   - Competition dashboard (basic)

3. **Phase 3: Player Management** (Day 5)
   - Seed football players
   - Seed cricket players
   - Player selection UI

4. **Phase 4: Auction System** (Day 6-8)
   - Implement Socket.IO server
   - Build auction backend logic (bidding, timer, lot progression)
   - Create auction room UI
   - Test real-time bidding with multiple users

5. **Phase 5: Fixtures & Scoring** (Day 9-10)
   - Football API integration
   - Cricket API integration
   - CSV upload and scoring logic
   - Dashboard leaderboard

6. **Phase 6: Polish & Testing** (Day 11-12)
   - End-to-end testing
   - Bug fixes
   - UI improvements

---

## 📞 Emergency Contact Points

If rebuilding fails or you encounter blockers:

### Known Complex Areas
1. **Socket.IO auction timer**: Most complex part. Use `asyncio.create_task()` and store task reference to cancel on new bids.
2. **MongoDB serialization**: Test with single record first before bulk operations.
3. **Cricbuzz API**: Series endpoint `/series/v1/{seriesId}` is reliable. Other endpoints may have missing data.

### Alternative Approaches
- **Auction Timer**: Could use Redis for distributed timer if scaling to multiple servers
- **Scoring**: Could use background jobs (Celery) instead of synchronous CSV processing
- **Player Data**: Could scrape from Wikipedia/ESPN if APIs fail

---

## ✅ Success Criteria

You've successfully rebuilt the platform when:

1. ✅ Users can register, login, and create competitions
2. ✅ Commissioner can select players and invite participants
3. ✅ Multiple users can join an auction room simultaneously
4. ✅ Real-time bidding works with timer anti-snipe protection
5. ✅ Budget enforcement prevents overbidding
6. ✅ Fixtures can be imported for both football and cricket
7. ✅ CSV score upload calculates points and updates standings
8. ✅ Dashboard shows league table, fixtures, and player stats

---

## 💾 Backup Recommendation

Before attempting rebuild, ensure you have:
- Complete MongoDB dump: `mongodump --db fantasy_sports_db --out /backup`
- Full Git repository with all commits
- Copy of this document and `/app/README.md`

---

**This document is your lifeline. Treat it as the source of truth for recreating the entire application from zero.**
