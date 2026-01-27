# Sport X Fantasy Auction Platform - PRD

---
## ⚠️ AGENT: READ THIS SECTION FIRST

**Before doing ANYTHING, read these files:**
1. `/app/MASTER_TODO_LIST.md` - Current tasks and priorities
2. `/app/AGENT_START_HERE.md` - Quick reference and gotchas
3. `/app/POC_RAILWAY_DEPLOYMENT.md` - Railway migration POC results

**Current Status (Jan 27, 2026):** 🎨 UI/UX REDESIGN IN PROGRESS - Stitch design implementation

**Critical gotchas:**
- Teams/Players are in `assets` collection (NOT `clubs` or `teams`)
- Points are in `league_points` collection (NOT `league_participants`)
- Auth magic link returns token in response - needs email delivery for production
- Competition names must be exact: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"
- `competitions` field must be array: `["UEFA Champions League"]` not `"UEFA Champions League"`

**Ask user for approval before implementing anything.**

---

## Original Problem Statement
Build a fantasy sports auction platform where users create leagues, bid on teams/clubs in real-time auctions, and compete based on team performance scores.

## User Personas
1. **Commissioners** - Create and manage leagues, configure auction settings, start/stop auctions
2. **Managers** - Join leagues, participate in auctions, build team rosters via bidding
3. **Spectators** - Watch live auctions (view-only)

## Core Requirements
- Real-time auction bidding via Socket.IO
- Multi-sport support (Football, Cricket, Reality TV planned)
- League management with invite tokens
- Anti-snipe timer extension for last-second bids
- Score updates from external APIs (Football-Data.org, Cricbuzz)
- Magic link authentication (passwordless)

## Technology Stack
- **Frontend**: React (port 3000)
- **Backend**: FastAPI/Python (port 8001)
- **Database**: MongoDB Atlas (M0 free for POC, M2 recommended for production)
- **Real-time**: Socket.IO with WebSocket-only transport
- **External APIs**: Football-Data.org, Cricbuzz (via RapidAPI)
- **Hosting**: Railway (EU-West) - validated via POC

## What's Been Implemented

### Phase 1: Core Platform (Complete)
- User authentication (magic links)
- League CRUD operations
- Real-time auction engine with bidding
- Anti-snipe timer mechanism
- Socket.IO real-time updates
- Football competition support (UCL, Premier League, etc.)
- Cricket competition support (IPL)

### Phase 2: Documentation Overhaul (Complete - Jan 2026)
- Restructured docs into `/app/docs/` directory
- Created API_REFERENCE.md, DATABASE_SCHEMA.md, ENV_VARIABLES.md
- Archived 196 obsolete markdown files
- Created Pick TV onboarding documents

### Phase 3: Bug Fixes (Complete - Jan 2026)
- ISSUE-027: Fixed fixture score import bug (historical scores applied to future matches)
- Added admin reset endpoints for fixture data correction
- Fixed AFCON 2025 fixtures with qualified knockout teams

### Phase 4: Testing Infrastructure (Complete - Jan 2026)
- Created Python stress test script: `/app/tests/auction_stress_test.py`
- Supports hot-lot, full-auction, and race-condition test modes
- Fixed Socket.IO event handling to match server events
- Validates: bid throughput, Socket.IO latency, anti-snipe triggers, race conditions
- Test results: 56.7% bid success rate (expected for competitive bidding), p99 latency 13ms

### Phase 5: Railway POC (Complete - Jan 24, 2026)
- ✅ Backend deploys successfully on Railway (EU-West Amsterdam)
- ✅ Frontend deploys successfully (static build)
- ✅ WebSocket-only transport works (no sticky sessions needed)
- ✅ MongoDB Atlas (M0, Ireland) connects
- ✅ Full auction flow completes end-to-end
- ✅ 100% bid success rate (32/32 bids)
- ✅ ~480ms average latency (vs ~700ms on Emergent)
- ✅ Socket.IO events working (112 events received)

**POC Fixes Applied:**
- Sentry v10 API change (`startTransaction` removed)
- ESLint 9 configuration for react-hooks
- yarn frozen-lockfile override
- `competitions` field as array in seed data

## P0/P1/P2 Features Remaining

### P0 (Critical)
- [x] ~~Railway POC~~ ✅ COMPLETED
- [ ] Upgrade MongoDB Atlas to M2 (London region)
- [ ] Upgrade Railway to paid tier (London region)
- [ ] Run full 400-user stress test on Railway
- [ ] Code refactor: Break `server.py` into routes/services structure

### P1 (High Priority)
- [ ] Authentication hardening (SendGrid email delivery)
- [ ] ISSUE-002: Fix Commissioner Auth Checks
- [ ] UI Improvements: Bidder Status, Team Count, Current Bid Label, Sticky Tabs
- [ ] ISSUE-026: Scalable Fixture Template Management
- [ ] Reality TV Market Expansion (technical spec exists)

### P2 (Medium Priority)
- [ ] ISSUE-016: Roster Not Updating (monitoring)
- [ ] ISSUE-019: "Couldn't Place Bid" (monitoring)
- [ ] ISSUE-020: "United Offered 2 Times" (monitoring)
- [ ] ISSUE-022: "Unknown" Manager Names (monitoring)

## Key Files Reference
- `/app/backend/server.py` - Main API (monolith, needs refactoring)
- `/app/tests/railway_stress_test.py` - Railway POC stress test (working)
- `/app/tests/multi_league_stress_test.py` - Multi-league stress test
- `/app/scripts/seed_railway_poc.py` - Seed script for Railway POC
- `/app/POC_RAILWAY_DEPLOYMENT.md` - Railway POC results and learnings
- `/app/MASTER_TODO_LIST.md` - Canonical task tracker
- `/app/docs/` - Structured documentation

## Stress Test Scripts

### Railway POC Stress Test (Jan 24, 2026)
```bash
# Install dependencies
pip install "python-socketio[asyncio_client]" aiohttp

# Run against Railway
python /app/tests/railway_stress_test.py --leagues 1 --url https://joeyjones-production.up.railway.app

# Results: 100% success, 483ms avg latency, 112 socket events
```

### Multi-League Stress Test
```bash
python multi_league_stress_test.py --leagues 20 --users 8 --teams 4 --url https://YOUR-PRODUCTION-URL
```

## Important Notes
- **Railway requires WebSocket-only**: `transports: ['websocket'], upgrade: false` in Socket.IO client
- **GitHub Sync**: "Save to GitHub" may not commit all files - verify in browser
- **CI=true**: Railway treats ESLint warnings as errors - fix warnings or add disable comments
- **Auction activation**: After creating auction, call `/api/auction/{id}/begin` to start
- **MongoDB data**: `competitions` field must be array, not string
