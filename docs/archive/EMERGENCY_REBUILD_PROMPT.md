# Emergency Project Rebuild Prompt - UPDATED January 2026

**⚠️ CRITICAL: Use this prompt to recreate the Fantasy Sports Auction Platform from scratch**

Last Updated: January 17, 2026  
Current Production Version: Fully functional multi-sport auction platform - preparing for 400-user UK pilot  
Document Version: 3.0

---

## 🎯 Project Overview

Build a **multi-sport fantasy auction platform** enabling users to create private leagues, conduct live player auctions via Socket.IO, and manage tournaments with automated scoring for **Football (Soccer)** and **Cricket**.

---

## 🌐 Production Environment

**Current Production URL:** https://draft-kings-mobile.emergent.host  
**Health Check:** `curl -s "https://draft-kings-mobile.emergent.host/api/health"`

**⚠️ CRITICAL INFRASTRUCTURE UPDATE (January 2026):**
- **Current hosting**: Emergent (US-based) - causes ~700ms latency for UK users
- **Migration planned**: Railway (EU-West/London) for UK pilot
- **Root cause**: 6-7 DB calls per bid × ~100ms transatlantic round-trip = unacceptable latency

**Current Production State (Verified Jan 17, 2026):**
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

**Stress Test Results (Jan 17, 2026 - 10 leagues, 80 users):**
| Metric | Value | Status |
|--------|-------|--------|
| p50 latency | 700ms | ⚠️ High (US hosting) |
| p99 latency | 2808ms | ❌ Too high |
| Bid success | 71% | ⚠️ Contention at scale |
| Leagues completed | 100% | ✅ |

---

## 🚀 Migration Plan (Railway EU-West)

**Why migrating:**
- UK pilot users face ~700ms baseline latency to US servers
- Emergent confirmed US-only hosting, 2-pod limit
- Railway allows EU region selection

**Target architecture:**
```
Railway (EU-West/London)
├── Backend: FastAPI
├── Frontend: React
├── MongoDB Atlas M10 (europe-west2)
└── Redis Cloud (existing account)
```

**Estimated cost:** ~£65/month (Railway £15 + Atlas M10 £45 + Redis £5)

**Dual development workflow (post-migration):**
```
Emergent (sandbox) → Push tested feature → sandbox-repo (GitHub)
                                              ↓ Create PR
Railway (production) ← Auto-deploy ← production-repo (main branch)
```

See `/app/MIGRATION_PLAN.md` for full details.

---

## 🏗️ Core Architecture

### Tech Stack (VERIFIED CURRENT)
- **Frontend**: React 18 + Tailwind CSS + shadcn/ui + Socket.IO Client + React Router v6 + axios + sonner (toasts)
- **Backend**: FastAPI (Python 3.10+) + python-socketio + Motor (async MongoDB) + PyJWT
- **Database**: MongoDB (single database: `test_database`)
- **Real-time**: Socket.IO with Redis adapter for multi-pod production
- **Authentication**: Magic Link (email-based, no passwords) - ⚠️ Needs hardening for pilot
- **External Redis**: Redis Cloud Essentials (256 connections)

### Project Structure (VERIFIED)
```
/app/
├── backend/
│   ├── server.py                    # Monolithic FastAPI (~5,900 lines)
│   ├── auth.py                      # JWT + Magic Link generation
│   ├── socketio_init.py             # Socket.IO server with Redis adapter
│   ├── scoring_service.py           # Point calculation
│   ├── football_data_client.py      # Football-Data.org API wrapper
│   ├── rapidapi_client.py           # Cricbuzz API wrapper
│   ├── models.py                    # Pydantic models
│   ├── metrics.py                   # Bid metrics tracking
│   └── .env                         # Backend env vars
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── MyCompetitions.js    # Home page + auth
│       │   ├── CreateLeague.js      # League creation + club selection
│       │   ├── LeagueDetail.js      # Pre-auction: waiting room
│       │   ├── AuctionRoom.js       # Live bidding (Socket.IO) - ⚠️ DO NOT MODIFY
│       │   ├── CompetitionDashboard.js  # Post-auction: standings
│       │   └── Help.js              # User guide
│       ├── components/ui/           # shadcn/ui components
│       └── utils/
│           ├── socket.js            # Socket.IO client
│           └── debugLogger.js       # Debug report capture
├── tests/
│   └── multi_league_stress_test.py  # Load testing script
├── MASTER_TODO_LIST.md              # Single source of truth for tasks
├── MIGRATION_PLAN.md                # Railway migration details
├── AGENT_START_HERE.md              # Quick reference for agents
└── memory/PRD.md                    # Product requirements
```

---

## 📊 Database Schema (MongoDB) - VERIFIED CURRENT STATE

### Database Name
- **ONLY ONE DATABASE**: `test_database`
- Collections: `users`, `leagues`, `league_participants`, `auctions`, `bids`, `assets`, `fixtures`, `league_points`, `standings`, `sports`, `magic_links`, `debug_reports`

### Collection: `users`
```javascript
{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "User Name",
  "createdAt": "2025-01-01T00:00:00+00:00"
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
  "budget": 500000000,
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,
  "timerSeconds": 30,
  "antiSnipeSeconds": 10,
  "inviteToken": "6-char-string",
  "assetsSelected": ["asset-id-1", "asset-id-2"],
  "createdAt": "2025-01-01T00:00:00+00:00"
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
  "clubsWon": ["asset-id-1", "asset-id-2"],
  "totalSpent": 150000000,
  "joinedAt": "2025-01-01T00:00:00+00:00"
}
```
⚠️ **CRITICAL**: Points are NOT in this collection - see `league_points`

### Collection: `auctions`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",
  "status": "waiting" | "active" | "paused" | "auction_complete",
  "currentClubId": "asset-id",
  "currentLotId": "lot-id",
  "currentLot": 1,
  "bidTimer": 30,
  "antiSnipeSeconds": 10,
  "timerEndsAt": "2025-01-01T00:00:30+00:00",
  "clubQueue": ["asset-id-1", "asset-id-2"],
  "unsoldClubs": ["asset-id-3"],
  "minimumBudget": 1000000,
  "currentBid": 5000000,
  "currentBidder": {"userId": "user-id", "displayName": "Name"},
  "bidSequence": 42,
  "usersInWaitingRoom": ["user-id-1", "user-id-2"],
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
  "externalId": "61",
  "apiFootballId": "49",
  "competitions": ["UEFA Champions League", "English Premier League"],
  "competitionShort": "EPL",
  "country": "England",
  "logo": null,
  "createdAt": "2025-01-01T00:00:00+00:00"
}
```
⚠️ **CRITICAL**: 
- NO separate `clubs` or `teams` collection
- Filter by `sportKey: "football"` for clubs
- Competition names MUST be exact: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"

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
  "totalPoints": 32,
  "lastUpdated": "2025-01-01T00:00:00+00:00"
}
```

### Collection: `fixtures`
```javascript
{
  "id": "uuid-string",
  "leagueId": "league-id",  // ⚠️ CRITICAL: MUST have leagueId
  "sportKey": "football",
  "homeTeam": "Chelsea FC",
  "awayTeam": "Arsenal FC",
  "homeTeamId": "asset-id",
  "awayTeamId": "asset-id",
  "startsAt": "2025-01-15T15:00:00+00:00",
  "status": "ns" | "live" | "ft",  // ⚠️ "ft" for finished
  "goalsHome": 2,
  "goalsAway": 1,
  "winner": "home" | "away" | "draw",
  "footballDataId": 551918,
  "source": "api" | "csv"
}
```

---

## 🔐 Authentication - Magic Link

### Current State (PRE-PILOT - NEEDS HARDENING)
1. User enters email
2. Backend generates token, stores in `magic_links` collection
3. ⚠️ **DEV MODE**: Token returned in API response (NOT emailed)
4. User enters token
5. Backend validates, returns JWT tokens

### Pre-Pilot Hardening Required
| Item | Current | Required |
|------|---------|----------|
| Email delivery | Token in response | Send via SendGrid/Resend |
| Rate limiting | None | 3 requests/hour/email |
| Single-use tokens | Needs verification | Ensure deleted after use |

See `/app/MASTER_TODO_LIST.md` for full auth hardening plan.

---

## 🎮 Critical Features

### 1. Auction System (Socket.IO) - ⚠️ DO NOT MODIFY WITHOUT STAGING

The auction system is complex and interconnected. Changes have caused production issues.

**Socket Events (Server → Client)**:
- `waiting_room_updated`: Participant list changed
- `auction_snapshot`: Full state on join
- `bid_update`: New bid placed
- `lot_started`: New lot begins
- `sold`: Lot completed (sold or unsold)
- `next_team_countdown`: 3-2-1 between lots
- `auction_complete`: All lots finished

**Key Logic**:
- Anti-snipe: Timer extends on late bids
- Unsold teams: Re-queued at end
- Budget reserve: Must keep £1m per remaining slot
- Self-outbid prevention: Can't outbid yourself

**DB Calls Per Bid (Current - 6-7 calls)**:
1. `auctions.find_one` - Get auction state
2. `users.find_one` - Get bidder info
3. `leagues.find_one` - Get league settings (clubSlots)
4. `league_participants.find_one` - Get budget/roster
5. `bids.insert_one` - Record bid
6. `auctions.update_one` - Update current bid
7. `auctions.find_one` - Get new bid sequence

⚠️ **Caching attempt (Jan 16, 2026) FAILED** - reverted due to bug affecting auction completion.

### 2. Fixture Import & Scoring

**Import**: `POST /api/leagues/{league_id}/fixtures/import-from-api`
- Uses FUZZY matching for team names

**Scoring**: `POST /api/leagues/{league_id}/score/recompute`
- Uses EXACT matching for team names
- MUST filter by `leagueId`
- Only counts fixtures with `status: "ft"`

### 3. Debug Report System

**Frontend captures**:
- Auction state, participants, socket events, user actions, errors
- Auto-uploads to `debug_reports` collection

**Endpoints**:
```
POST /api/debug/reports - Submit report
GET /api/debug/reports - List reports
GET /api/debug/reports/{referenceId} - Get specific report
```

---

## 🧪 Stress Testing

**Script**: `/app/tests/multi_league_stress_test.py`

**Run from local machine**:
```bash
# Prerequisites
pip install "python-socketio[asyncio_client]" aiohttp

# Commands
python multi_league_stress_test.py --leagues 2 --users 6 --teams 4 --url https://your-url.com
python multi_league_stress_test.py --leagues 10 --users 8 --teams 4 --url https://your-url.com
python multi_league_stress_test.py --leagues 20 --users 8 --teams 4 --url https://your-url.com
```

**Output**: Creates timestamped JSON and TXT result files.

**Target metrics (post-Railway migration)**:
| Scale | Target Success | Target p50 | Target p99 |
|-------|---------------|------------|------------|
| 20 leagues | ≥95% | ≤200ms | ≤1000ms |
| 50 leagues | ≥90% | ≤300ms | ≤1500ms |

---

## 📱 Mobile Strategy (Post-Pilot)

**Decision**: Capacitor (wrap existing React app)

| Phase | Approach | When |
|-------|----------|------|
| Current | Mobile-responsive web | Now |
| Post-Pilot | Capacitor | After successful pilot |
| Scale | React Native | If Capacitor hits limits |

**Capacitor benefits**:
- Reuse 90%+ of existing code
- Real App Store/Play Store presence
- Push notifications
- ~1-2 weeks implementation

**Costs**: Apple Dev ~£79/year + Google Play ~£20 one-time

---

## ⚠️ CRITICAL Gotchas

### 1. Team Names MUST Match API Exactly
- Scoring uses exact MongoDB `$in` matching
- "Chelsea FC" (not "Chelsea")
- See team name verification in assets collection

### 2. Fixture Import vs Scoring - Different Matching
- **Import**: FUZZY (forgiving)
- **Scoring**: EXACT (strict)

### 3. leagueId MUST Be in Fixtures
- Without filter, same fixture counted multiple times

### 4. MongoDB DateTime Serialization
```python
"createdAt": datetime.now(timezone.utc).isoformat()
```

### 5. MongoDB _id Field
```python
db.collection.find({}, {"_id": 0})  # Always exclude
```

### 6. Auction Code is Fragile
- ⚠️ Changes have broken production
- Test in staging environment (Railway) before production
- Even "low risk" changes can have hidden dependencies

---

## 🚀 Environment Variables

### Backend `.env`
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET="your-secret-key"
FOOTBALL_DATA_TOKEN="your-token"
RAPIDAPI_KEY="your-key"
REDIS_URL="redis://..."  # Redis Cloud connection
FRONTEND_ORIGIN="https://your-frontend-url"
```

### Frontend `.env`
```bash
REACT_APP_BACKEND_URL="http://localhost:8001"
```

---

## 📋 Outstanding Issues (January 2026)

### 🔴 P0 - Blockers
| Issue | Summary | Status |
|-------|---------|--------|
| Infrastructure | UK users have ~700ms latency | Migration to Railway planned |
| Auth hardening | Magic link returns token in response | Needs SendGrid integration |

### 🟡 P1 - Pre-Pilot
| Issue | Summary | Status |
|-------|---------|--------|
| Sentry monitoring | Error tracking not configured | Needs DSN |
| DB backups | Need to verify Atlas M10 backups | Config check |
| Commissioner auth | Missing auth checks on some endpoints | Not started |

### 🟢 P2 - Post-Pilot
| Issue | Summary |
|-------|---------|
| Mobile apps | Capacitor implementation |
| Server.py refactor | 5,900+ lines - needs splitting |
| DB call optimization | Reduce 6-7 calls per bid |
| Email notifications | Invite, reminder, results emails |

See `/app/MASTER_TODO_LIST.md` for complete list.

---

## ❌ Failed Approaches (LESSONS LEARNED)

### DB Call Caching (Jan 16, 2026) - FAILED
**Attempted**: Cache league settings and user info to reduce DB calls  
**Result**: Bug in implementation (missed variable reference) broke bidding  
**Lesson**: Real-time auction code needs dedicated staging environment

### MongoDB Pool Size Increase - NO EFFECT
**Attempted**: Increase connection pool size  
**Result**: No latency improvement  
**Lesson**: Pool size wasn't the bottleneck

### Hybrid DB Approach - RULED OUT
**Attempted**: UK-based MongoDB with US-hosted app  
**Result**: Wouldn't help - app server latency is the issue  
**Lesson**: App and users must be in same region

---

## 📞 Critical Files Reference

| File | Purpose |
|------|---------|
| `/app/MASTER_TODO_LIST.md` | **PRIMARY** - All tasks organized by phase |
| `/app/MIGRATION_PLAN.md` | Railway migration details |
| `/app/AGENT_START_HERE.md` | Quick reference for agents |
| `/app/memory/PRD.md` | Product requirements |
| `/app/docs/ARCHITECTURE.md` | System architecture |
| `/app/docs/OPERATIONS_PLAYBOOK.md` | Operational procedures |
| `/app/tests/multi_league_stress_test.py` | Load testing script |

---

## ✅ Success Criteria

Platform rebuilt successfully when:
1. ✅ Magic link auth works
2. ✅ Multiple users can create/join leagues
3. ✅ Real-time auction with anti-snipe timer
4. ✅ Waiting room shows live participant count
5. ✅ CL/PL/AFCON fixtures import successfully
6. ✅ Score updates work from API
7. ✅ Points calculate correctly
8. ✅ Socket.IO works in multi-pod (Redis)
9. ✅ Debug reports capture and upload
10. ⏳ Auth hardening (pre-pilot)
11. ⏳ UK latency ≤200ms (post-Railway migration)

---

## 🔄 Pilot Readiness Checklist

Before 400-user UK pilot:
- [ ] Complete Railway migration (EU-West)
- [ ] Run stress test - verify p50 ≤200ms
- [ ] Auth hardening (SendGrid email delivery)
- [ ] Enable Sentry error monitoring
- [ ] Verify MongoDB Atlas backups
- [ ] Update CORS for new domain

---

**This document contains VERIFIED CURRENT STATE as of January 17, 2026. Treat as source of truth for rebuild.**

---

## 📝 Document History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Jan 17, 2026 | Major update: Infrastructure findings, Railway migration plan, stress testing, mobile strategy, auth hardening, failed approaches |
| 2.0 | Dec 20, 2025 | Added Debug Report System, Failed Fix Attempts |
| 1.0 | Dec 13, 2025 | Initial comprehensive rebuild prompt |
