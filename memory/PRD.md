# Sport X Platform - Product Requirements Document

**Last Updated:** January 30, 2026  
**Status:** PRE-PILOT (Railway EU Deployed)

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
- **Target:** 400 UK users pilot

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

### UI/UX (Stitch Redesign) ✅
- [x] Dark theme (#0F172A background)
- [x] Redesigned waiting room (commissioner/user views)
- [x] Transparent logo backgrounds with conditional backdrop
- [x] Team type filter (Clubs vs National Teams)
- [x] Mobile-first responsive design

### Team Assets ✅
- [x] 63 football club teams with logos
- [x] 42 FIFA World Cup 2026 national teams with badges
- [x] 10 IPL cricket teams with logos
- [x] 125 IPL players with roles
- [x] All teams have Football-Data.org IDs (100% coverage)

### Database ✅
- [x] Standardized team names (official API format)
- [x] Merged duplicate entries
- [x] Preview environment connected to production DB

---

## Backlog (Prioritized)

### P0 - Pending User Feedback
- [ ] Device/Screen responsive audit (waiting for specific feedback)

### P1 - Needed for Pilot
- [ ] Authentication hardening (SendGrid for emails)
- [ ] Remaining WC2026 qualifiers (6 playoff spots)
- [ ] IPL 2026 fixture import (when schedule released)

### P2 - Post-Pilot Enhancements
- [ ] "Pass This Round" auction feature
- [ ] Dynamic team colors in auction room
- [ ] Manual score entry UI
- [ ] Auction history tab
- [ ] Email notifications

### P3 - Future
- [ ] Payment integration (Stripe)
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
| `/app/scripts/populate_football_data_ids.py` | Football-Data.org ID script |

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

**Document Version:** 2.0  
**Maintained By:** Development Team
