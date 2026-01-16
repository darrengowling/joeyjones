# Sport X Fantasy Auction Platform - PRD

---
## ⚠️ AGENT: READ THIS SECTION FIRST

**Before doing ANYTHING, read these files:**
1. `/app/MASTER_TODO_LIST.md` - Current tasks and priorities
2. `/app/AGENT_START_HERE.md` - Quick reference and gotchas

**Current Status (Jan 2026):** Migrating to Railway (EU). UK users have ~700ms latency on Emergent (US-hosted).

**Critical gotchas:**
- Teams/Players are in `assets` collection (NOT `clubs` or `teams`)
- Points are in `league_points` collection (NOT `league_participants`)
- Auth magic link returns token in response - needs email delivery for production
- Competition names must be exact: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"

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
- **Database**: MongoDB Atlas (Emergent-managed)
- **Real-time**: Socket.IO with Redis adapter (for multi-pod)
- **External APIs**: Football-Data.org, Cricbuzz (via RapidAPI)

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

## P0/P1/P2 Features Remaining

### P0 (Critical)
- [ ] Answer Migration Pre-requisites (awaiting user input):
  - Redis Cloud connection string
  - Football-Data.org API tier
  - Custom domain availability
  - Data migration approach
- [ ] Code refactor: Break `server.py` into routes/services structure

### P1 (High Priority)
- [ ] ISSUE-002: Fix Commissioner Auth Checks
- [ ] ISSUE-003: Configure Sentry Monitoring (awaiting DSN)
- [ ] UI Improvements: Bidder Status, Team Count, Current Bid Label, Sticky Tabs
- [ ] ISSUE-026: Scalable Fixture Template Management
- [ ] Reality TV Market Expansion (technical spec exists)
- [ ] IPL Workplace Version

### P2 (Medium Priority)
- [ ] ISSUE-016: Roster Not Updating (monitoring)
- [ ] ISSUE-019: "Couldn't Place Bid" (monitoring)
- [ ] ISSUE-020: "United Offered 2 Times" (monitoring)
- [ ] ISSUE-021: "Roster Lagged" (monitoring)
- [ ] ISSUE-022: "Unknown" Manager Names (monitoring)

## Key Files Reference
- `/app/backend/server.py` - Main API (monolith, needs refactoring)
- `/app/tests/auction_stress_test.py` - Load testing script (fully functional)
- `/app/API_REFERENCE.md` - Complete API documentation
- `/app/DATABASE_SCHEMA.md` - MongoDB schema documentation
- `/app/MASTER_TODO_LIST.md` - Canonical task tracker
- `/app/docs/` - Structured documentation

## Stress Test Scripts

### Multi-League Stress Test (Primary - Jan 2026)
```bash
# Install dependencies
pip install "python-socketio[asyncio_client]" aiohttp

# Run from local machine against production
python multi_league_stress_test.py --leagues 20 --users 8 --teams 4 --url https://YOUR-PRODUCTION-URL

# Results saved to: stress_test_results_YYYYMMDD_HHMMSS.json/.txt
```

**Location:** `/app/tests/multi_league_stress_test.py`

**Known limitations:**
- £0M spend metric (wrong field reference)
- Excessive "roster full" rejections (polling lag)
- May under-count lots sold (race condition on completion)
- Latency metrics are valid

### Legacy Auction Stress Test
```bash
# Hot lot test (aggressive bidding)
python auction_stress_test.py --mode hot-lot --invite-token TOKEN \
  --commissioner-email EMAIL --use-existing-members --users 6
```

## MongoDB Performance Investigation (Jan 2026)

**Status:** Awaiting Emergent support response

**Problem:** Production latency ~700-1100ms vs Preview ~360ms  
**Root cause:** Emergent's shared MongoDB Atlas cluster (`customer-apps.oxfwhh.mongodb.net`)

**Options:**
1. Contact Emergent for dedicated cluster
2. Bring your own MongoDB Atlas (M10 ~£45/month)
3. Aggressive caching (complex, risky)

**See:** `/app/MASTER_TODO_LIST.md` for full analysis and decision matrix
```

## Important Notes
- **GitHub Sync**: "Save to GitHub" may create conflict branches - check GitHub and merge PRs manually if deployment doesn't reflect changes
- **Defensive API Integration**: Fixture import validates dates before applying scores
- **Socket.IO Events**: Server emits `lot_started`, `bid_update`, `bid_placed`, `sold`, `auction_complete`, `tick`, `auction_snapshot`
- **Test League**: `load10Jan` (token: `237b0451`) is full (8 members), use `--use-existing-members` flag
