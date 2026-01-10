# Sport X Fantasy Auction Platform - PRD

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
- Validates: bid throughput, Socket.IO latency, anti-snipe triggers

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
- `/app/tests/auction_stress_test.py` - Load testing script
- `/app/API_REFERENCE.md` - Complete API documentation
- `/app/DATABASE_SCHEMA.md` - MongoDB schema documentation
- `/app/MASTER_TODO_LIST.md` - Canonical task tracker
- `/app/docs/` - Structured documentation

## Important Notes
- **GitHub Sync**: "Save to GitHub" may create conflict branches - check GitHub and merge PRs manually if deployment doesn't reflect changes
- **Defensive API Integration**: Fixture import now validates dates before applying scores
- **Preview Environment**: Test league `load10Jan` (token: `237b0451`) is full (8 members max)
