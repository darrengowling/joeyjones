# Sport X Platform - Product Requirements Document

**Last Updated:** February 6, 2026  
**Status:** PRE-PILOT (Phase 1 Quick Wins Complete)

---

## Original Problem Statement

Build a fantasy sports auction platform for UK-based users with:
1. Real-time auction functionality for multiple users
2. Support for football (club teams + national teams) and cricket (IPL)
3. Low latency (<500ms p99) for UK users
4. Premium dark-theme UI ("Stitch" design)

---

## Current Architecture

### Infrastructure
- **Hosting:** Railway (EU-West) - migrated from Emergent (US)
- **Database:** MongoDB Atlas (EU region)
- **Cache:** Redis Cloud
- **Target:** ~200 users charity foundation pilot

### Tech Stack
- **Frontend:** React with Stitch dark theme
- **Backend:** FastAPI (Python)
- **Real-time:** Socket.IO
- **APIs:** Football-Data.org, Cricbuzz (RapidAPI)

---

## What's Been Implemented

### Core Features ✅
- [x] Real-time auction room with Socket.IO
- [x] Commissioner and participant roles
- [x] Budget management and bidding
- [x] Multiple competition support (CL, PL, WC2026, IPL)
- [x] Fixture imports and score updates
- [x] Profile page with username editing
- [x] Magic link authentication (dev mode)
- [x] Auto-reconnection database manager (self-healing)
- [x] **Auction Reports system** - Auto-generated, admin-only, CSV download

### UI/UX (Stitch Redesign) ✅
- [x] Dark theme (#0F172A background)
- [x] Redesigned waiting room (commissioner/user views)
- [x] Transparent logo backgrounds with conditional backdrop
- [x] Team type filter (Clubs vs National Teams)
- [x] Mobile-first responsive design
- [x] "How to Install" PWA instructions in Help page
- [x] Optimized auction button layout (2x3 grid)
- [x] Hidden cricket for football-only pilot
- [x] Hidden dev indicator in production
- [x] **About page** - Separate page with header nav link
- [x] **Screen size optimization** - Compact auction room for smaller phones

### Team Assets ✅
- [x] 63 football club teams with logos
- [x] 42 FIFA World Cup 2026 national teams with badges
- [x] 10 IPL cricket teams with logos
- [x] 125 IPL players with roles
- [x] All teams have Football-Data.org IDs (100% coverage)

### Performance & Reliability ✅
- [x] My Competitions: 6s → <1s load time
- [x] DB queries optimized: 30+ → 7 queries
- [x] Auto-reconnection for DB failures

---

## Backlog (Prioritized)

### P0 - Must Have for Pilot
- [ ] Authentication: Google OAuth + Magic Link hardening
- [ ] OneSignal push notifications
- [ ] Auto score updates (cron job)

### P1 - Should Have for Pilot
- [ ] Display other users' budgets in auction room
- [ ] "View All" modal: show owner + amount paid
- [ ] Auction behavior tracking
- [ ] Auction results archive
- [ ] Display other users' budgets in auction
- [ ] Screen size fix (Samsung A56 issue)
- [ ] MongoDB Atlas → Flex upgrade (backups)

### P2 - Nice to Have
- [ ] "View All" modal enhancements
- [ ] Bidding multiples (multi-tap)
- [ ] Time-limited pilot access

### P3 - Post-Pilot
- [ ] "Pass This Round" implementation
- [ ] Manual score entry UI
- [ ] Email notifications
- [ ] server.py refactoring
- [ ] Mobile app (Capacitor wrapper)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `/app/MASTER_TODO_LIST.md` | All tasks, priorities, phases |
| `/app/SESSION_CHANGES.md` | Detailed session work log |
| `/app/AGENT_START_HERE.md` | Quick reference for agents |
| `/app/frontend/src/utils/teamLogoMapping.js` | Team → logo mapping |
| `/app/frontend/src/components/DebugFooter.js` | Dev indicator (hidden in prod) |
| `/app/frontend/src/pages/AuctionRoom.js` | Auction room with optimized buttons |
| `/app/frontend/src/pages/Help.js` | Help page with install instructions |

---

## Database Schema

```
assets           → Teams (football) + Players (cricket)
                   - footballDataId: API ID
                   - type: 'national_team' | null
                   - competitionCode: 'WC2026', 'CL', etc.
leagues          → Competition settings
league_participants → User budgets, rosters
league_points    → Team/player scores
auctions         → Active auction state
fixtures         → Match data
users            → User accounts
```

---

## Credentials (Test)

- **Test User:** darren.gowling@gmail.com
- **MongoDB:** MongoDB Atlas (sport_x_poc database)
- **Football-Data.org:** API token in .env
- **Cricbuzz:** RapidAPI key in .env

---

**Document Version:** 3.0  
**Maintained By:** Development Team
