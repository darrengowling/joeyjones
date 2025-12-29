# Database Schema Reference

**Created:** December 28, 2025  
**Purpose:** Complete MongoDB collection schema documentation  
**Database:** MongoDB (via Motor async driver)  
**Status:** ACTIVE

---

## Overview

| Collection | Purpose | Record Count (Dec 2025) |
|------------|---------|------------------------|
| `users` | User accounts | ~477 |
| `leagues` | League/competition definitions | ~427 |
| `league_participants` | User membership in leagues | ~83 |
| `assets` | Teams, players, contestants | ~127 |
| `fixtures` | Matches, episodes | ~193 |
| `auctions` | Auction state | ~33 |
| `bids` | Bid history | ~225 |
| `league_points` | Scoring data (football) | ~31 |
| `standings` | Computed standings | ~137 |
| `sports` | Sport configurations | 2 |
| `league_stats` | Cricket match stats | ~209 |
| `cricket_leaderboard` | Cricket player totals | ~127 |
| `debug_reports` | Debug submissions | Variable |
| `magic_links` | Auth tokens | Transient |

---

## Core Collections

### users

**Purpose:** User account data

```javascript
{
  "id": "uuid-string",           // Primary key (NOT _id)
  "email": "user@example.com",   // Unique
  "name": "Display Name",
  "passwordHash": "bcrypt...",   // Optional (magic link users may not have)
  "createdAt": ISODate(),
  "lastLogin": ISODate()
}
```

**Indexes:**
- `id` (unique)
- `email` (unique)

**Notes:**
- Always query with `{"_id": 0}` projection
- `id` is a UUID string, not MongoDB ObjectId

---

### leagues

**Purpose:** League/competition definitions

```javascript
{
  "id": "uuid-string",           // Primary key
  "name": "My League",
  "commissionerId": "user-uuid", // Creator/owner
  "sportKey": "football",        // Links to sports collection
  "competitionCode": "PL",       // PL, CL, AFCON, etc.
  
  // Auction settings
  "budget": 500000000,           // Per-user budget (in base units)
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,                // Assets per user
  "timerSeconds": 30,            // Bid timer
  "antiSnipeSeconds": 10,        // Anti-snipe extension
  
  // Team selection
  "assetsSelected": ["uuid", ...], // Selected asset IDs for auction
  
  // Scoring
  "scoringOverrides": {          // Optional custom rules
    "win": 5,
    "draw": 2
  },
  
  // State
  "status": "draft",             // draft, waiting, active, completed
  "inviteToken": "abc123",       // 8-char join code
  "createdAt": ISODate()
}
```

**Status Values:**
- `draft` - Created, not started
- `waiting` - Auction created, waiting for participants
- `active` - Auction in progress
- `completed` - Auction finished

**Indexes:**
- `id` (unique)
- `inviteToken` (unique)
- `commissionerId`
- `status`

---

### league_participants

**Purpose:** User membership in leagues with auction results

```javascript
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "userId": "user-uuid",
  "userName": "Display Name",
  "userEmail": "user@example.com",
  
  // Auction results
  "budgetRemaining": 350000000,
  "totalSpent": 150000000,
  "clubsWon": ["asset-uuid-1", "asset-uuid-2"], // Won asset IDs
  
  "joinedAt": ISODate()
}
```

**Indexes:**
- `{leagueId, userId}` (compound, unique)
- `leagueId`
- `userId`

**Notes:**
- `clubsWon` contains asset IDs (despite the name, applies to all asset types)
- Points are NOT stored here - see `league_points` collection

---

### assets

**Purpose:** All auctionable items (teams, players, contestants)

```javascript
// Football Club
{
  "id": "uuid-string",
  "name": "Manchester City",
  "sportKey": "football",
  "externalId": "MCI",           // API identifier
  "country": "England",
  "competitions": ["English Premier League"],
  "competitionShort": "PL",
  "logo": "url-or-null",
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}

// Cricket Player
{
  "id": "uuid-string",
  "name": "Virat Kohli",
  "sportKey": "cricket",
  "externalId": "virat_kohli",
  "meta": {
    "team": "India",
    "role": "Batsman"
  },
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}

// Reality TV Contestant (Pick TV)
{
  "id": "uuid-string",
  "name": "Jane Doe",
  "sportKey": "reality_tv",
  "externalId": "SURVIVOR47_01",
  "competitionShort": "SURVIVOR47",
  "meta": {
    "age": 28,
    "occupation": "Teacher",
    "hometown": "Austin, TX",
    "tribe": "Gata",
    "photo_url": "https://..."
  },
  "currentStatus": "active",     // active, eliminated, winner
  "eliminationEpisode": null,
  "finalPlacement": null,
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}
```

**Indexes:**
- `id` (unique)
- `sportKey`
- `externalId`
- `competitionShort`
- `{sportKey, competitionShort}`

**⚠️ Critical Notes:**
- ALL assets are in this single collection (no separate `clubs` collection)
- Filter by `sportKey`: `football`, `cricket`, `reality_tv`
- Competition names must be exact: "English Premier League" not "Premier League"

---

### fixtures

**Purpose:** Matches (football), fixtures (cricket), episodes (reality TV)

```javascript
// Football Match
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "externalMatchId": "PL-2025-123",
  "sportKey": "football",
  
  // Teams
  "homeTeam": "Manchester City",
  "awayTeam": "Liverpool",
  "homeAssetId": "asset-uuid",
  "awayAssetId": "asset-uuid",
  "homeAssetExternalId": "MCI",
  "awayAssetExternalId": "LIV",
  
  // Schedule
  "startsAt": ISODate(),
  "venue": "Etihad Stadium",
  "round": "Matchweek 15",
  
  // Results
  "status": "scheduled",        // scheduled, live, ft
  "goalsHome": null,
  "goalsAway": null,
  "winner": null,               // "home", "away", "draw"
  
  // Metadata
  "source": "api",              // api, csv, manual
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}

// Cricket Match
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "sportKey": "cricket",
  "externalMatchId": "nz-eng-odi-1",
  
  "homeAssetId": "player-uuid",
  "awayAssetId": "player-uuid",
  
  "startsAt": ISODate(),
  "venue": "Bay Oval",
  "round": "Match 1",
  "status": "scheduled",
  
  "autoScoringEnabled": true,
  "cricapiMatchId": "api-id",
  
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}

// Reality TV Episode (Pick TV)
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "sportKey": "reality_tv",
  "externalMatchId": "SURVIVOR47_EP01",
  
  "episodeNumber": 1,
  "episodeTitle": "The Marooning",
  "airDate": ISODate(),
  "eventType": "episode",       // episode, finale, reunion
  
  // Episode results
  "results": [
    {
      "contestantId": "uuid",
      "survived": true,
      "eliminated": false,
      "wonChallenge": false,
      "wonImmunity": false
    }
  ],
  "eliminatedContestants": ["uuid"],
  "challengeWinners": ["uuid"],
  
  "status": "ft",               // scheduled, ft (completed)
  "createdAt": ISODate(),
  "updatedAt": ISODate()
}
```

**Status Values:**
- `scheduled` - Not yet played/aired
- `live` - In progress
- `ft` - Full time / completed (required for scoring)

**⚠️ Critical:** Status must be `ft` for scoring to calculate.

**Indexes:**
- `id` (unique)
- `leagueId`
- `{leagueId, status}`
- `externalMatchId`

---

### auctions

**Purpose:** Real-time auction state

```javascript
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "status": "active",           // waiting, active, paused, completed
  
  // Current lot
  "currentLot": 3,              // Index in queue
  "currentClubId": "asset-uuid",
  "currentLotId": "auction-id-lot-3",
  
  // Timer
  "bidTimer": 30,
  "antiSnipeSeconds": 10,
  "timerEndsAt": ISODate(),
  
  // Queue
  "clubQueue": ["uuid1", "uuid2", ...],  // Asset IDs in order
  "unsoldClubs": [],            // Assets with no bids
  
  // Current bid
  "currentBid": 50000000,
  "currentBidder": {
    "userId": "user-uuid",
    "displayName": "User Name"
  },
  "bidSequence": 5,             // Bid counter for sync
  
  // Budget
  "minimumBudget": 1000000,     // Minimum bid
  
  // Pause state
  "pausedAt": null,
  "pausedRemainingTime": null,
  
  "createdAt": ISODate(),
  "completedAt": "iso-string"   // When finished
}
```

**Status Values:**
- `waiting` - Created, not started
- `active` - Bidding in progress
- `paused` - Temporarily stopped
- `completed` - All lots sold

**Indexes:**
- `id` (unique)
- `leagueId` (unique for active auctions)
- `status`

---

### bids

**Purpose:** Historical bid records

```javascript
{
  "id": "uuid-string",
  "auctionId": "auction-uuid",
  "clubId": "asset-uuid",       // Asset being bid on
  "userId": "user-uuid",
  "userName": "Display Name",
  "userEmail": "user@example.com",
  "amount": 50000000,
  "timestamp": ISODate()
}
```

**Indexes:**
- `id` (unique)
- `auctionId`
- `{auctionId, clubId}`
- `userId`

---

## Scoring Collections

### league_points

**Purpose:** Points per asset per league (football scoring)

```javascript
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "clubId": "asset-uuid",
  "clubName": "Manchester City",
  
  // Stats
  "wins": 5,
  "draws": 2,
  "losses": 1,
  "goalsScored": 15,
  "goalsConceded": 5,
  
  // Calculated
  "totalPoints": 17,            // Based on scoring rules
  
  "lastUpdated": ISODate()
}
```

**⚠️ Critical:** This is where points live, NOT in `league_participants`.

**Indexes:**
- `{leagueId, clubId}` (compound, unique)
- `leagueId`

---

### standings

**Purpose:** Computed league standings (cached)

```javascript
{
  "id": "uuid-string",
  "leagueId": "league-uuid",
  "sportKey": "football",
  
  "table": [
    {
      "userId": "user-uuid",
      "displayName": "User Name",
      "points": 25,
      "assetsOwned": ["asset-uuid-1", "asset-uuid-2"],
      "tiebreakers": {
        "goals": 10,
        "wins": 3,
        "draws": 1,
        "runs": 0,
        "wickets": 0
      }
    }
  ],
  
  "lastComputedAt": ISODate()
}
```

**Indexes:**
- `leagueId` (unique)

---

### league_stats

**Purpose:** Per-match player stats (cricket)

```javascript
{
  "matchId": "match-external-id",
  "playerExternalId": "virat_kohli",
  "leagueId": "league-uuid",
  
  // Stats
  "runs": 75,
  "wickets": 0,
  "catches": 1,
  "stumpings": 0,
  "runOuts": 0,
  
  // Calculated
  "totalPoints": 85,
  
  "updatedAt": ISODate()
}
```

**Indexes:**
- `{leagueId, matchId, playerExternalId}` (compound, unique)

---

### cricket_leaderboard

**Purpose:** Aggregated cricket player totals per league

```javascript
{
  "leagueId": "league-uuid",
  "playerExternalId": "virat_kohli",
  "totalPoints": 249,
  "updatedAt": ISODate()
}
```

**Indexes:**
- `{leagueId, playerExternalId}` (compound, unique)

---

## Configuration Collections

### sports

**Purpose:** Sport/competition type configuration

```javascript
{
  "key": "football",            // Primary key
  "name": "Football",
  "description": "Fantasy football competitions",
  "active": true,
  "assetType": "CLUB",          // CLUB, PLAYER, CONTESTANT
  
  "scoringSchema": {
    "type": "matchResults",     // matchResults, perPlayerMatch, elimination
    "rules": {
      "win": 3,
      "draw": 1,
      "goal": 1
    },
    "milestones": {}
  },
  
  "auctionTemplate": {
    "bidTimerSeconds": 30,
    "antiSnipeSeconds": 10,
    "minIncrement": 1
  },
  
  "uiHints": {
    "assetLabel": "Club",
    "assetPlural": "Clubs",
    "currencySymbol": "£",
    "currencySuffix": "m"
  },
  
  "createdAt": ISODate()
}
```

**Current Sports:**
- `football` - Football clubs
- `cricket` - Cricket players
- `reality_tv` - Reality TV contestants (Pick TV)

---

## Utility Collections

### magic_links

**Purpose:** Temporary authentication tokens

```javascript
{
  "token": "random-string",
  "userId": "user-uuid",
  "email": "user@example.com",
  "expiresAt": ISODate(),
  "used": false
}
```

**TTL Index:** Documents auto-delete after expiry

---

### debug_reports

**Purpose:** Debug report submissions from frontend

```javascript
{
  "referenceId": "DBG-20251219-001",
  "auctionId": "auction-uuid",
  "leagueId": "league-uuid",
  "submittedAt": ISODate(),
  
  "metadata": {
    "userAgent": "...",
    "screenSize": "1920x1080"
  },
  
  "statistics": { ... },
  "errorSummary": { ... },
  "socketEvents": [ ... ],
  "bidEvents": [ ... ],
  "serverState": { ... }
}
```

---

## Query Patterns

### Always Exclude _id

```python
# Correct
await db.users.find({}, {"_id": 0}).to_list(100)
await db.leagues.find_one({"id": league_id}, {"_id": 0})

# Wrong - will cause serialization errors
await db.users.find({}).to_list(100)
```

### Find Assets by Sport

```python
# Football clubs
await db.assets.find({"sportKey": "football"}, {"_id": 0}).to_list(100)

# Cricket players
await db.assets.find({"sportKey": "cricket"}, {"_id": 0}).to_list(100)

# Specific competition
await db.assets.find({
    "sportKey": "football",
    "competitionShort": "PL"
}, {"_id": 0}).to_list(100)
```

### Find User's Leagues

```python
participations = await db.league_participants.find(
    {"userId": user_id},
    {"_id": 0}
).to_list(100)

league_ids = [p["leagueId"] for p in participations]

leagues = await db.leagues.find(
    {"id": {"$in": league_ids}},
    {"_id": 0}
).to_list(100)
```

### Get League Standings

```python
# Get points for all assets in league
points = await db.league_points.find(
    {"leagueId": league_id},
    {"_id": 0}
).to_list(100)

# Get participants with their assets
participants = await db.league_participants.find(
    {"leagueId": league_id},
    {"_id": 0}
).to_list(100)

# Calculate user totals from asset points
for p in participants:
    user_points = sum(
        pt["totalPoints"] 
        for pt in points 
        if pt["clubId"] in p["clubsWon"]
    )
```

---

## Common Mistakes

| Mistake | Correct Approach |
|---------|------------------|
| Looking for `clubs` collection | Use `assets` with `sportKey: "football"` |
| Looking for points in `league_participants` | Points are in `league_points` |
| Using status `"completed"` for fixtures | Use `"ft"` (full-time) |
| Not excluding `_id` in projections | Always add `{"_id": 0}` |
| Using wrong competition name | Use exact names from database |

---

## Backup & Migration

### Export Collection

```bash
mongodump --uri="$MONGO_URL" --collection=leagues --out=./backup
```

### Import Collection

```bash
mongorestore --uri="$MONGO_URL" --collection=leagues ./backup/dbname/leagues.bson
```

### Data Migration Checklist

For migration to new environment:
1. `users` - User accounts
2. `leagues` - League definitions
3. `league_participants` - Memberships
4. `assets` - All assets
5. `fixtures` - Match data
6. `sports` - Configuration
7. `league_points` - Scoring data
8. `standings` - Can be regenerated

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
