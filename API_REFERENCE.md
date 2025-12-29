# API Reference

**Created:** December 28, 2025  
**Purpose:** Complete API endpoint documentation for Sport X / Pick TV  
**Base URL:** `https://your-domain.com/api`  
**Status:** ACTIVE

---

## Overview

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Health & Metrics | 2 | System health and Prometheus metrics |
| Authentication | 4 | Login, registration, magic links |
| Users | 2 | User management |
| Sports | 2 | Sport configurations |
| Assets | 4 | Teams/players/contestants |
| Leagues | 15 | League CRUD and management |
| Fixtures | 8 | Match/episode management |
| Scoring | 4 | Points and standings |
| Auctions | 12 | Real-time auction operations |
| Admin | 2 | Administrative operations |
| Debug | 6 | Development/debugging tools |
| **Total** | **61** | |

---

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

Tokens are obtained from `/api/auth/verify-magic-link` or login endpoints.

---

## Health & Metrics

### GET /api/health

**Purpose:** System health check for load balancers and monitoring

**Authentication:** None

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "socketio": {
    "mode": "redis",
    "redis_configured": true,
    "multi_pod_ready": true
  }
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Unhealthy (database disconnected)

---

### GET /api/metrics

**Purpose:** Prometheus metrics endpoint

**Authentication:** None

**Response:** Prometheus text format

---

## Authentication

### POST /api/auth/magic-link

**Purpose:** Request a magic link for passwordless login

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Magic link sent to email",
  "token": "abc123..."  // Only in development
}
```

---

### POST /api/auth/verify-magic-link

**Purpose:** Verify magic link and get JWT token

**Authentication:** None

**Request Body:**
```json
{
  "token": "abc123..."
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

---

### POST /api/auth/refresh

**Purpose:** Refresh JWT token before expiry

**Authentication:** Required (current token)

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { ... }
}
```

---

### GET /api/auth/me

**Purpose:** Get current authenticated user

**Authentication:** Required

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

---

## Users

### POST /api/users

**Purpose:** Create a new user (registration)

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "password": "securepassword"
}
```

---

### GET /api/users/{user_id}

**Purpose:** Get user by ID

**Authentication:** Required

**Response:**
```json
{
  "id": "uuid",
  "name": "User Name",
  "email": "user@example.com"
}
```

---

## Sports

### GET /api/sports

**Purpose:** List all available sports/competition types

**Authentication:** None

**Response:**
```json
[
  {
    "key": "football",
    "name": "Football",
    "description": "Fantasy football competitions",
    "active": true,
    "assetType": "CLUB",
    "scoringSchema": {
      "type": "matchResults",
      "rules": { "win": 3, "draw": 1, "goal": 1 }
    },
    "uiHints": {
      "assetLabel": "Club",
      "assetPlural": "Clubs"
    }
  },
  {
    "key": "cricket",
    "name": "Cricket",
    "active": true,
    "assetType": "PLAYER"
  }
]
```

---

### GET /api/sports/{sport_key}

**Purpose:** Get specific sport configuration

**Authentication:** None

**Path Parameters:**
- `sport_key`: `football`, `cricket`, `reality_tv`

---

## Assets (Teams/Players/Contestants)

### GET /api/assets

**Purpose:** List all assets (teams, players, contestants)

**Authentication:** None

**Query Parameters:**
- `sportKey` (optional): Filter by sport (`football`, `cricket`)
- `competition` (optional): Filter by competition name

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Manchester City",
    "sportKey": "football",
    "externalId": "MCI",
    "country": "England",
    "competitions": ["English Premier League"],
    "competitionShort": "PL"
  }
]
```

---

### GET /api/clubs

**Purpose:** List football clubs (filtered by competition)

**Authentication:** None

**Query Parameters:**
- `competition` (optional): `PL`, `EPL`, `CL`, `UCL`, `AFCON`

**Response:** Array of club objects

---

### GET /api/leagues/{league_id}/assets

**Purpose:** Get assets for a specific league (filtered by competition)

**Authentication:** Required

**Response:** Array of assets relevant to the league's sport/competition

---

### GET /api/leagues/{league_id}/available-assets

**Purpose:** Get assets available for auction (not yet selected)

**Authentication:** Required

---

## Leagues

### POST /api/leagues

**Purpose:** Create a new league/competition

**Authentication:** Required

**Request Body:**
```json
{
  "name": "My League",
  "sportKey": "football",
  "competitionCode": "PL",
  "budget": 500000000,
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,
  "timerSeconds": 30,
  "antiSnipeSeconds": 10
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My League",
  "inviteToken": "abc123",
  "status": "draft",
  "commissionerId": "user-uuid"
}
```

---

### GET /api/leagues

**Purpose:** List all leagues (optionally filtered)

**Authentication:** Required

**Query Parameters:**
- `status` (optional): `draft`, `active`, `completed`

---

### GET /api/leagues/search

**Purpose:** Search leagues by name or invite token

**Authentication:** Required

**Query Parameters:**
- `q`: Search query

---

### GET /api/leagues/by-token/{invite_token}

**Purpose:** Get league details by invite token (for joining)

**Authentication:** None

**Response:**
```json
{
  "id": "uuid",
  "name": "League Name",
  "sportKey": "football",
  "currentParticipants": 3,
  "maxManagers": 8
}
```

---

### GET /api/leagues/{league_id}

**Purpose:** Get full league details

**Authentication:** Required

---

### POST /api/leagues/{league_id}/join

**Purpose:** Join a league using invite token

**Authentication:** Required

**Request Body:**
```json
{
  "inviteToken": "abc123"
}
```

---

### GET /api/leagues/{league_id}/participants

**Purpose:** List all participants in a league

**Authentication:** Required

**Response:**
```json
[
  {
    "userId": "uuid",
    "userName": "User Name",
    "budgetRemaining": 350000000,
    "clubsWon": ["club-uuid-1", "club-uuid-2"]
  }
]
```

---

### GET /api/leagues/{league_id}/members

**Purpose:** Alias for participants (same as above)

---

### GET /api/me/competitions

**Purpose:** Get all leagues the current user is part of

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "League Name",
    "status": "active",
    "isCommissioner": true,
    "myPosition": 2,
    "myPoints": 15
  }
]
```

---

### GET /api/leagues/{league_id}/summary

**Purpose:** Get league summary with standings and rosters

**Authentication:** Required

**Response:**
```json
{
  "league": { ... },
  "standings": [
    {
      "userId": "uuid",
      "displayName": "User",
      "points": 25,
      "roster": [{ "name": "Man City", "points": 15 }]
    }
  ]
}
```

---

### PUT /api/leagues/{league_id}/assets

**Purpose:** Set selected assets for auction (commissioner only)

**Authentication:** Required (Commissioner)

**Request Body:**
```json
{
  "assetIds": ["uuid-1", "uuid-2", "uuid-3"]
}
```

---

### DELETE /api/leagues/{league_id}

**Purpose:** Delete a league (commissioner only, before auction starts)

**Authentication:** Required (Commissioner)

---

### POST /api/leagues/bulk-delete

**Purpose:** Delete multiple leagues

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "leagueIds": ["uuid-1", "uuid-2"]
}
```

---

### PUT /api/leagues/{league_id}/scoring-overrides

**Purpose:** Set custom scoring rules for a league

**Authentication:** Required (Commissioner)

**Request Body:**
```json
{
  "win": 5,
  "draw": 2,
  "goal": 1
}
```

---

## Fixtures (Matches/Episodes)

### GET /api/fixtures

**Purpose:** List all fixtures

**Authentication:** Required

---

### GET /api/fixtures/{fixture_id}

**Purpose:** Get specific fixture details

**Authentication:** Required

---

### GET /api/leagues/{league_id}/fixtures

**Purpose:** Get all fixtures for a league

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "homeTeam": "Man City",
    "awayTeam": "Liverpool",
    "startsAt": "2025-01-15T15:00:00Z",
    "status": "scheduled",
    "goalsHome": null,
    "goalsAway": null
  }
]
```

---

### POST /api/leagues/{league_id}/fixtures/import-csv

**Purpose:** Import fixtures from CSV file

**Authentication:** Required (Commissioner)

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file`: CSV file with columns: `homeTeam`, `awayTeam`, `startsAt`, `venue`, `round`

---

### POST /api/leagues/{league_id}/fixtures/import-from-api

**Purpose:** Import fixtures from Football-Data.org API

**Authentication:** Required (Commissioner)

**Query Parameters:**
- `competition`: `PL` or `CL`

---

### POST /api/leagues/{league_id}/fixtures/import-from-cricket-api

**Purpose:** Import cricket fixtures from API

**Authentication:** Required (Commissioner)

---

### DELETE /api/leagues/{league_id}/fixtures/clear

**Purpose:** Delete all fixtures for a league

**Authentication:** Required (Commissioner)

---

### PATCH /api/fixtures/{fixture_id}/score

**Purpose:** Manually update fixture score

**Authentication:** Required (Commissioner)

**Request Body:**
```json
{
  "goalsHome": 2,
  "goalsAway": 1,
  "status": "ft"
}
```

**Note:** Status must be `ft` (full-time) for scoring to calculate.

---

## Scoring

### POST /api/leagues/{league_id}/score/recompute

**Purpose:** Recalculate all scores from fixtures

**Authentication:** Required (Commissioner)

**Response:**
```json
{
  "message": "Scores recomputed",
  "fixturesProcessed": 10,
  "pointsUpdated": true
}
```

---

### GET /api/leagues/{league_id}/standings

**Purpose:** Get league standings/leaderboard

**Authentication:** Required

**Response:**
```json
{
  "table": [
    {
      "userId": "uuid",
      "displayName": "User",
      "points": 25,
      "tiebreakers": {
        "goals": 10,
        "wins": 3,
        "draws": 1
      }
    }
  ]
}
```

---

### POST /api/scoring/{league_id}/ingest

**Purpose:** Ingest cricket match scores

**Authentication:** Required

**Request Body:**
```json
{
  "matchId": "match-123",
  "playerStats": [
    {
      "playerExternalId": "virat_kohli",
      "runs": 75,
      "wickets": 0,
      "catches": 1
    }
  ]
}
```

---

### GET /api/scoring/{league_id}/leaderboard

**Purpose:** Get cricket player leaderboard

**Authentication:** Required

---

## Auctions

### POST /api/leagues/{league_id}/auction/start

**Purpose:** Start the auction for a league

**Authentication:** Required (Commissioner)

**Response:**
```json
{
  "auctionId": "uuid",
  "status": "waiting",
  "message": "Auction created, waiting for participants"
}
```

---

### GET /api/leagues/{league_id}/auction

**Purpose:** Get auction for a league

**Authentication:** Required

---

### GET /api/auction/{auction_id}

**Purpose:** Get auction state by ID

**Authentication:** Required

**Response:**
```json
{
  "id": "uuid",
  "leagueId": "uuid",
  "status": "active",
  "currentLot": 3,
  "currentClubId": "club-uuid",
  "currentBid": 50000000,
  "currentBidder": {
    "userId": "uuid",
    "displayName": "User"
  },
  "timerEndsAt": "2025-01-15T15:00:30Z",
  "bidSequence": 5
}
```

---

### POST /api/auction/{auction_id}/begin

**Purpose:** Begin auction (start first lot)

**Authentication:** Required (Commissioner)

---

### GET /api/auction/{auction_id}/clubs

**Purpose:** Get clubs/assets in auction queue

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Arsenal",
    "country": "England",
    "status": "pending"  // pending, current, sold, unsold
  }
]
```

---

### POST /api/auction/{auction_id}/bid

**Purpose:** Place a bid on current lot

**Authentication:** Required

**Request Body:**
```json
{
  "amount": 55000000
}
```

**Response:**
```json
{
  "success": true,
  "newBid": 55000000,
  "timerEndsAt": "2025-01-15T15:00:40Z"
}
```

**Error Responses:**
- `400` - Bid too low, insufficient budget, roster full
- `409` - Self-outbid (already highest bidder)

---

### POST /api/auction/{auction_id}/start-lot/{club_id}

**Purpose:** Manually start a specific lot (commissioner override)

**Authentication:** Required (Commissioner)

---

### POST /api/auction/{auction_id}/complete-lot

**Purpose:** Manually complete current lot (force timer expiry)

**Authentication:** Required (Commissioner)

---

### POST /api/auction/{auction_id}/pause

**Purpose:** Pause the auction

**Authentication:** Required (Commissioner)

---

### POST /api/auction/{auction_id}/resume

**Purpose:** Resume a paused auction

**Authentication:** Required (Commissioner)

---

### POST /api/leagues/{league_id}/auction/reset

**Purpose:** Reset auction (delete and allow restart)

**Authentication:** Required (Commissioner)

---

### DELETE /api/auction/{auction_id}

**Purpose:** Delete an auction

**Authentication:** Required (Commissioner)

---

## Admin Endpoints

### PATCH /api/admin/assets/{asset_id}

**Purpose:** Update asset details (admin only)

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "name": "Updated Name",
  "country": "Updated Country"
}
```

---

### POST /api/admin/fixtures/replace-team

**Purpose:** Replace team in all fixtures (data correction)

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "oldTeamName": "Kenya",
  "newTeamName": "Cameroon",
  "leagueId": "uuid"
}
```

---

## Debug Endpoints

⚠️ **Development/debugging only. May not be available in production.**

### GET /api/debug/rooms/{scope}/{room_id}

**Purpose:** View Socket.IO room state

---

### GET /api/debug/bid-logs/{auction_id}

**Purpose:** View bid logs for auction

---

### GET /api/debug/auction-state/{auction_id}

**Purpose:** View detailed auction state

---

### GET /api/debug/league-lookup

**Purpose:** Lookup league by various identifiers

---

### POST /api/debug/reports

**Purpose:** Submit debug report from frontend

---

### GET /api/debug/reports

**Purpose:** List debug reports

---

### GET /api/debug/reports/{reference_id}

**Purpose:** Get specific debug report

---

## Socket.IO Events

Socket.IO connection: `wss://your-domain.com/api/socket.io`

### Server → Client Events

| Event | Purpose | Payload |
|-------|---------|--------|
| `auction_state` | Full auction sync | Auction object |
| `bid_update` | New bid placed | `{currentBid, bidderId, bidderName, bidSequence, timerEndsAt}` |
| `bid_placed` | Bid confirmation to bidder | Same as bid_update |
| `timer_sync` | Timer synchronization | `{timerEndsAt, serverTime, remainingMs}` |
| `sold` | Lot completed with winner | `{clubId, winnerId, winnerName, amount}` |
| `unsold` | Lot completed, no bids | `{clubId}` |
| `new_lot` | Next lot starting | `{clubId, clubName, index, timerEndsAt}` |
| `auction_completed` | Auction finished | `{auctionId}` |
| `auction_paused` | Auction paused | `{auctionId}` |
| `auction_resumed` | Auction resumed | `{auctionId, timerEndsAt}` |
| `participant_joined` | User joined | `{userId, userName}` |
| `roster_update` | Roster changed | `{userId, clubsWon, budgetRemaining}` |
| `auction_deleted` | Auction was deleted | `{auctionId}` |
| `error` | Error message | `{message, code}` |

### Client → Server Events

| Event | Purpose | Payload |
|-------|---------|--------|
| `join_auction` | Join auction room | `{auctionId, userId}` |
| `leave_auction` | Leave auction room | `{auctionId}` |

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Invalid/missing token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `409` | Conflict - Business rule violation |
| `500` | Internal Server Error |

---

## Rate Limiting

Rate limiting is configurable via `ENABLE_RATE_LIMITING` environment variable.

When enabled:
- Default: 100 requests per minute per IP
- Auction endpoints: 30 requests per minute per user

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
