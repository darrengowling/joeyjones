# Master TODO List - Sport X Platform

**Last Updated:** February 2, 2026  
**Purpose:** Single source of truth for all work items organized by deployment phase  
**Current Status:** POST-MIGRATION / PRE-PILOT (Railway EU-West Live)

---

## 📍 CURRENT SITUATION SUMMARY

| Aspect | Status |
|--------|--------|
| **Platform** | Railway (EU-West) ✅ MIGRATED mid-January 2026 |
| **Development** | Emergent (for agent-assisted development) |
| **Database** | MongoDB Atlas (EU region) |
| **Cache** | Redis Cloud (256 connections) |
| **Pilot Target** | 400 UK users |
| **Current Phase** | 🟡 PRE-PILOT - Final polish and testing |
| **CORS** | ✅ Configured (explicit origin) |
| **Monitoring** | ⚠️ Recommended (UptimeRobot) |

---

## 🚦 TASK PHASES OVERVIEW

| Phase | Focus | Status |
|-------|-------|--------|
| ~~🔴 PRE-MIGRATION~~ | ~~Prep work before Railway migration~~ | ✅ COMPLETE |
| **🟡 PRE-PILOT** | Work after migration, before 400-user pilot | **CURRENT** |
| 🟢 POST-PILOT | Enhancements after successful pilot | Pending |
| 🔵 FUTURE | Long-term roadmap items | Backlog |

---

## ✅ COMPLETED - RAILWAY MIGRATION (January 2026)

*All pre-migration tasks completed*

| # | Task | Status | Date |
|---|------|--------|------|
| 1 | Railway account setup | ✅ Done | Mid-Jan 2026 |
| 2 | MongoDB Atlas EU cluster | ✅ Done | Mid-Jan 2026 |
| 3 | Redis Cloud configuration | ✅ Done | Mid-Jan 2026 |
| 4 | `/health` endpoint | ✅ Done | Jan 16 |
| 5 | Environment variable audit | ✅ Done | Jan 16 |
| 6 | CORS config for Railway | ✅ Done | Mid-Jan 2026 |
| 7 | Data migration | ✅ Done | Mid-Jan 2026 |

**Latency improvement:** UK users now have optimal latency via EU-West hosting.

---

## ✅ COMPLETED - STITCH UI/UX REDESIGN (January 2026)

*Full visual redesign to premium dark theme*

| # | Component | Status | Date |
|---|-----------|--------|------|
| 1 | Design System CSS (`design-system.css`) | ✅ Done | Jan 27 |
| 2 | BottomNav component | ✅ Done | Jan 27 |
| 3 | HomePage redesign | ✅ Done | Jan 27 |
| 4 | CreateCompetition page | ✅ Done | Jan 27 |
| 5 | LeagueDetail/CompetitionDashboard | ✅ Done | Jan 27 |
| 6 | AuctionRoom (waiting room + live auction) | ✅ Done | Jan 27-29 |
| 7 | Profile page (NEW) | ✅ Done | Jan 29 |
| 8 | Waiting room redesign (commissioner + user views) | ✅ Done | Jan 29 |
| 9 | Background color standardization (#0F172A) | ✅ Done | Jan 29 |
| 10 | TeamCrest soft white backdrop | ✅ Done | Jan 29 |

**Design tokens:** Inter font, #0F172A navy background, #06B6D4 cyan accent, 12px radius

---

## ✅ COMPLETED - TEAM LOGO INTEGRATION (January 2026)

### IPL Cricket (10 teams) - Jan 29
All logos at 256x256px in `/app/frontend/public/assets/clubs/cricket/`

### UEFA Champions League 2025/26 - Jan 30 ✅ COMPLETE
| Priority | Teams Added | Status |
|----------|-------------|--------|
| P1 (Playoffs) | Galatasaray SK, PAE Olympiakos SFP, Qarabağ Ağdam FK | ✅ Done |
| P2 (League Phase) | FC København, Paphos FC, SK Slavia Praha, Royale Union Saint-Gilloise | ✅ Done |
| Scottish | Celtic FC, Rangers FC | ✅ Done |
| Eastern European | Dinamo Zagreb, Shakhtar, Red Star Belgrade, Jagiellonia | ✅ Done |
| Central European | Sturm Graz, Sparta Prague, Young Boys | ✅ Done |
| Quick wins | Girona FC, Stade Brestois 29, Bologna FC 1909, Club Atlético de Madrid, FK Bodø/Glimt, Club Brugge KV | ✅ Done |

### FIFA World Cup 2026 - Jan 30 ✅ COMPLETE
| Confederation | Teams | Status |
|---------------|-------|--------|
| CAF (Africa) | Algeria, Cabo Verde, Côte d'Ivoire, Egypt, Ghana, Morocco, Senegal, South Africa, Tunisia | ✅ Done |
| AFC (Asia) | Australia, Iran, Japan, Jordan, Qatar, Saudi Arabia, South Korea, Uzbekistan | ✅ Done |
| UEFA (Europe) | Austria, Belgium, Croatia, England, France, Germany, Netherlands, Norway, Portugal, Scotland, Spain, Switzerland | ✅ Done |
| CONCACAF | Canada, Curaçao, Haiti, Mexico, Panama, United States | ✅ Done |
| OFC (Oceania) | New Zealand | ✅ Done |
| CONMEBOL | Argentina, Brazil, Colombia, Ecuador, Paraguay, Uruguay | ✅ Done |

**Total: 42 national teams with badges and Football-Data.org IDs**

**Assets folder:** `/app/frontend/public/assets/clubs/national_teams/`
**Mapping:** `nationalTeamLogoMapping` in `teamLogoMapping.js`

### Football-Data.org Integration - Jan 30 ✅ COMPLETE
- All 105 teams have `footballDataId` for fixture imports and score updates
- Script created: `/app/scripts/populate_football_data_ids.py`

**Mapping file:** `/app/frontend/src/utils/teamLogoMapping.js`  
**Football assets folder:** `/app/frontend/public/assets/clubs/football/`

---

## 🟡 PRE-PILOT TASKS (CURRENT PHASE)

*Tasks to complete before ~200 user charity foundation pilot*

---

### 🟢 QUICK WINS (< 2 hours, Low Risk)

| # | Task | Effort | Risk | Owner | Notes |
|---|------|--------|------|-------|-------|
| 1 | ~~**Hide "FE" dev indicator**~~ | 15 min | Low | Agent | ✅ DONE - Hidden in production builds |
| 2 | ~~**Hide cricket for pilot**~~ | 30 min | Low | Agent | ✅ DONE - Football only |
| 3 | ~~**"How to Install" Help section**~~ | 30 min | Low | Agent | ✅ DONE - Added iOS/Android instructions |
| 4 | ~~**Auction button layout optimization**~~ | 1 hr | Low | Agent | ✅ DONE - 2 rows of 3 equal buttons, Pass integrated |
| 5 | **UptimeRobot on /api/health** | 15 min | Low | User | External uptime monitoring |
| 6 | **Install guide PDF** | 1 hr | Low | User | Charity partner distributes to users |

---

### 🟡 MEDIUM EFFORT (2-6 hours, Low-Medium Risk)

| # | Task | Effort | Risk | Owner | Notes |
|---|------|--------|------|-------|-------|
| 7 | ~~**"About" section on homepage**~~ | 2-3 hrs | Low | Agent | ✅ DONE - Full content added with cards |
| 8 | **Google Analytics 4 integration** | 2-3 hrs | Low | Agent | Basic user journey visibility |
| 9 | **Auction behavior tracking** | 2-4 hrs | Low | Agent | Log bid patterns, timing, amounts to DB |
| 10 | **Auction results archive** | 3-4 hrs | Low | Agent | Which team, how much paid, winner - persistent record |
| 11 | **Display other users' budgets in auction** | 2-3 hrs | Low | Agent | Show remaining budget for all participants |
| 12 | **"View All" modal enhancements** | 2-3 hrs | Low | Agent | Show who owns each team + amount paid |
| 13 | **Bidding multiples (multi-tap)** | 3-4 hrs | Med | Agent | Allow stacking +£50m taps for £100m/£150m bids |
| 14 | **MongoDB Atlas → Flex upgrade** | 30 min | Low | User | Critical for backups - Free tier has none |

---

### 🟠 HIGHER EFFORT (1-2 days, Medium Risk)

| # | Task | Effort | Risk | Owner | Notes |
|---|------|--------|------|-------|-------|
| 15 | ~~**Screen size optimization (Samsung A56)**~~ | 1 day | Med | Agent | ✅ DONE - Compact layout, 100dvh, reduced padding |
| 16 | **Google OAuth implementation** | 4-6 hrs | Med | Agent | Simpler auth for users, no email delivery needed |
| 17 | **Magic link email hardening** | 1 day | Med | Agent | SendGrid integration, rate limiting, single-use tokens |
| 18 | **Time-limited pilot access** | 4-6 hrs | Med | Agent | 2-week access window for controlled pilot |

---

### 🔴 SIGNIFICANT EFFORT (2+ days, Higher Risk/Complexity)

| # | Task | Effort | Risk | Owner | Notes |
|---|------|--------|------|-------|-------|
| 19 | **OneSignal push notifications** | 1-2 days | Med | Agent | Score updates, upcoming fixtures - requires integration |
| 20 | **Auto score updates (cron job)** | 1-2 days | Med | Agent | Background task to fetch/update scores automatically |

---

### 📋 TASK DEPENDENCIES & GROUPINGS

**Authentication (choose path):**
- Option A: Google OAuth only (simpler, 4-6 hrs)
- Option B: Magic link hardening (needs SendGrid, 1 day)
- Option C: Both (1.5-2 days)

**Auction Room Enhancements (can bundle):**
- Button layout optimization (#4)
- Display other users' budgets (#11)
- "View All" modal enhancements (#12)
- Bidding multiples (#13)
- *Total if bundled: ~1 day*

**Analytics & Tracking (can bundle):**
- GA4 integration (#8)
- Auction behavior tracking (#9)
- Auction results archive (#10)
- *Total if bundled: ~1 day*

**Pilot Controls:**
- Hide cricket (#2)
- Time-limited access (#18)
- *Related: keep pilot scope tight*

---

### ❓ QUESTIONS / DECISIONS NEEDED

| # | Question | Options | Impact |
|---|----------|---------|--------|
| 1 | **Auth approach?** | OAuth only / Magic link only / Both | Determines 4-6 hrs vs 1-2 days |
| 2 | **Push notifications priority?** | Must-have / Nice-to-have / Post-pilot | OneSignal is 1-2 days effort |
| 3 | **Auto score updates priority?** | Must-have / Nice-to-have / Post-pilot | Backend cron job, 1-2 days |
| 4 | **Time-limited access mechanism?** | Invite codes expire / Account expiry / Manual cutoff | Complexity varies |
| 5 | **"About" content ready?** | User to provide | Blocks task #7 |

---

### 🔐 Authentication Options Detail

**Current State:** Magic-link returns token in response (dev mode - insecure)

**Option A: Google OAuth Only**
- Effort: 4-6 hours
- Pros: No email delivery needed, familiar UX, secure
- Cons: Requires Google account

**Option B: Magic Link Hardening**
- Effort: 1 day
- Requires: SendGrid/Resend account setup
- Includes: Real email delivery, rate limiting (3/hr), single-use tokens

**Option C: Both**
- Effort: 1.5-2 days
- Pros: Maximum flexibility for users
- Cons: More to maintain

---

### 📱 Screen Size Issue Detail

**Problem:** Samsung A56 (and potentially other devices) has main bidding interface obscured when placing bids.

**Potential causes:**
- Virtual keyboard pushing content
- Fixed positioning conflicts
- Viewport height calculation issues

**Investigation needed:**
- Get exact screen dimensions for A56
- Screenshot of the issue
- Test on similar viewport sizes

---

### 🏷️ STATUS KEY

| Symbol | Meaning |
|--------|---------|
| ❓ | Pending - not started |
| 🔄 | In progress |
| ⏸️ | Paused/blocked |
| ✅ | Complete |

---

### UI/UX Bugs (Existing)

| Issue ID | Page | Summary | Status | Notes |
|----------|------|---------|--------|-------|
| UI-001 | CompetitionDashboard | Tab height/centering on mobile | 🔴 BLOCKED | Multiple fix attempts failed |
| UI-002 | TeamCrest | Shield logos overflow circular container | 🟡 PARTIAL | Paused per user request |
| UI-003 | AuctionRoom | Bidding interface obscured on Samsung A56 | ❓ NEW | Needs investigation |

---

### Deferred Features (Pre-Pilot Risk)

| Feature | Current State | Why Deferred | Revisit When |
|---------|---------------|--------------|--------------|
| **"Pass This Round" Button** | UI shows "Coming soon!" toast | Touches core auction logic | Post-pilot, if users report frustration |
| **Dynamic team colors** | Not implemented | Complexity before pilot | Post-pilot |

---

### Infrastructure Issues

| Issue ID | Summary | Status | Notes |
|----------|---------|--------|-------|
| INFRA-001 | CORS PATCH method | ✅ Fixed Jan 29 | Added PATCH to allow_methods |

---

### Monitoring Items (Watch During Pilot)

| Issue ID | Summary | Watch For |
|----------|---------|-----------|
| ISSUE-016 | Roster not updating | Race conditions at 7+ users |
| ISSUE-019 | "Couldn't place bid" | False reports (roster full) |
| ISSUE-020 | Team offered twice | Socket duplication |
| ISSUE-022 | "Unknown" manager names | Missing userName data |

---

## 🟢 POST-PILOT TASKS

*Enhancements after successful pilot*

### New Features

| # | Feature | Effort | Priority | Notes |
|---|---------|--------|----------|-------|
| 1 | "Pass This Round" functionality | 2-3 hrs | P1 | If users request |
| 2 | Manual score entry UI | 4 hrs | P2 | Commissioners fix scores |
| 3 | Auction history tab | 4 hrs | P2 | Review all bids |
| 4 | Custom scoring rules | 1 week | P3 | Flexibility per tournament |
| 5 | Email notifications | 1 week | P2 | Invites, reminders |
| 6 | Payment integration (Stripe) | 2 weeks | P3 | Entry fees |

### 🔧 Developer Experience Enhancements

| # | Feature | Effort | Priority | Notes |
|---|---------|--------|----------|-------|
| 1 | **Sport toggle via env variable** | 20 min | P2 | `REACT_APP_PILOT_MODE=football|cricket|all` - avoids code changes when switching between football/cricket pilots for different partners |

### 🏆 FIFA World Cup 2026 Setup (P1 - Needed for Pilot)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Research qualified teams | 🔜 Next | ~35 confirmed, 48 total |
| 2 | Seed national team assets | ⏳ Pending | After team list finalized |
| 3 | Source national team logos/flags | ⏳ Pending | 48 logos needed |
| 4 | Set up WC2026 competition code | ⏳ Pending | New competition in DB |
| 5 | Test fixture import | ⏳ Pending | Football-Data.org supports WC |

### 🏏 IPL 2026 Setup (P1 - Ready, Waiting for Data)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | IPL 2026 player assets | ✅ Done | 125 players seeded |
| 2 | IPL team logos | ✅ Done | All 10 franchises |
| 3 | Cricbuzz API integration | ✅ Ready | Client working, tested |
| 4 | IPL 2026 Series ID | ⏳ Waiting | Schedule releases ~Feb/Mar 2026 |
| 5 | Fixture import test | ⏳ Waiting | After series ID available |
| 6 | Automated score updates | 🔜 Enhancement | Background job for live scores |

### 📱 Device/Screen Optimization (P0 - Pending User Feedback)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Gather user testing feedback | ⏸️ Waiting | User to collect device-specific issues |
| 2 | Audit responsive breakpoints | ⏳ Pending | After feedback received |
| 3 | Fix identified issues | ⏳ Pending | Priority based on user reports |

### Technical Debt

| # | Task | Effort | Priority | Notes |
|---|------|--------|----------|-------|
| 1 | Refactor server.py (5,900+ lines) | 1-2 weeks | P2 | Maintainability |
| 2 | Fixture import - use externalId | 4 hrs | P3 | Reliability |
| 3 | Consolidate socket events | 4 hrs | P3 | Simpler client |
| 4 | Socket.IO bidding (replace HTTP) | 1 week | P3 | Faster mobile |
| 5 | E2E test suite expansion | 4-5 days | P2 | Regression coverage |

### Mobile App Strategy 📱

| Phase | Approach | Trigger |
|-------|----------|---------|
| Current | Mobile-responsive web | ✅ Done |
| Post-Pilot | Capacitor wrapper | Users want "real" app |
| Scale | React Native | If Capacitor insufficient |

---

## 🔵 FUTURE / BACKLOG

### Multi-Region Expansion

| Region | Trigger | Action |
|--------|---------|--------|
| US | 100+ active US users | US Railway deployment |
| India | 100+ active India users | Asia deployment |
| Europe | Current | ✅ EU-West serves all |

### Advanced Features

- Native mobile apps (React Native)
- Real-time leaderboards
- Social features (chat, forums)
- Tournament brackets
- Third-party API

---

## ✅ RECENTLY RESOLVED

| # | Issue | Summary | Solution | Date |
|---|-------|---------|----------|------|
| 1 | Railway migration | EU-West hosting | Full migration complete | Mid-Jan 2026 |
| 2 | Stitch redesign | Dark theme UI/UX | Complete visual overhaul | Jan 27-29, 2026 |
| 3 | IPL logos | All 10 team crests | Local assets + mapping | Jan 29, 2026 |
| 4 | CL 2025/26 logos | P1 + P2 teams | Local assets + mapping | Jan 30, 2026 |
| 5 | CORS PATCH | Method not allowed | Added to allow_methods | Jan 29, 2026 |
| 6 | Profile page | User can't change name | New page + PATCH endpoint | Jan 29, 2026 |
| 7 | Waiting room | Needed redesign | Commissioner/user views | Jan 29, 2026 |
| 8 | Sentry monitoring | Backend error tracking | Configured DSN | Jan 17, 2026 |
| 9 | Redis limits | Connection exhaustion | Upgraded to Essentials | Jan 2026 |
| 10 | Fixture import bug | Completed matches imported | Added status filter to skip FT matches | Feb 1, 2026 |
| 11 | Auction carousel order | Revealed auction sequence | Seeded shuffle for display | Feb 1, 2026 |
| 12 | Dark logo watermarks | Invisible on dark bg | Invert filter for dark logos | Feb 1, 2026 |
| 13 | Help page styling | Emojis/colorful text | Standardized to Stitch design | Feb 1, 2026 |
| 14 | CORS wildcard fix | `*` doesn't work with credentials | Explicit origin in Railway env | Feb 2, 2026 |
| 15 | My Competitions loading | Showed "no competitions" while loading | Added spinner loading state | Feb 2, 2026 |
| 16 | My Competitions perf | 6s load time (N+1 queries) | Batched to 7 queries, <1s | Feb 2, 2026 |
| 17 | Score update toast | Showed confusing fixture count | Simplified to "Scores updated" | Feb 2, 2026 |
| 18 | Auto-reconnection logic | DB disconnect required manual restart | DatabaseManager with retry | Feb 2, 2026 |
| 19 | Ford Overoad league fix | 4 teams showing as "Team" | Direct DB update of asset IDs | Feb 2, 2026 |

---

## ⚠️ KNOWN LIMITATIONS

| Area | Limitation | Workaround |
|------|------------|------------|
| Bulk delete | 30+ leagues times out | Delete in batches of 5-10 |
| Shield logos | Overflow circular container | Documented in UI-002 |

---

## 📁 KEY FILES REFERENCE

| File | Purpose |
|------|---------|
| `/app/frontend/src/utils/teamLogoMapping.js` | Team name → logo file mapping |
| `/app/frontend/public/assets/clubs/` | Logo PNG files (football/, cricket/) |
| `/app/frontend/src/components/TeamCrest.jsx` | Logo display component |
| `/app/backend/server.py` | Main API (monolithic) |
| `/app/backend/db_manager.py` | Database connection manager with auto-reconnect |
| `/app/SESSION_CHANGES.md` | Detailed session work log |
| `/app/AGENT_START_HERE.md` | Quick reference for agents |
| `/app/OPTIMIZATION_AUDIT.md` | Performance optimization findings |

### Database Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `assets` | Teams (football) / Players (cricket) | `name`, `sportKey`, `competitionShort` |
| `leagues` | Competition settings | `id`, `name`, `sport` |
| `league_participants` | User budgets, rosters | `clubsWon` array |
| `league_points` | Team/player scores | NOT in league_participants |
| `auctions` | Active auction state | `status`, `currentLot` |
| `users` | User accounts | `email`, `displayName` |

---

## 🎯 IMMEDIATE NEXT ACTIONS

**Phase 1 Complete (Feb 6, 2026)**

### ✅ Completed Quick Wins
1. ✅ **Hide "FE" dev indicator** - Hidden in production builds
2. ✅ **Hide cricket for pilot** - Football only
3. ✅ **Auction button layout** - 2 rows of 3 equal buttons, Pass integrated
4. ✅ **"How to Install" Help section** - iOS/Android instructions added

### 🟡 User Actions Needed
5. 🔴 **MongoDB Atlas → Flex** - Critical for backups
6. ❓ **UptimeRobot setup** - External monitoring
7. ✅ **Provide "About" content** - Content received!
8. ✅ **Samsung A56 screenshot** - Screenshot received!
9. ✅ **Auth decision** - Both OAuth + Magic Link

### 🟠 Next Phase (Phase 2)
10. ❓ **"About" section on homepage** - Content ready to implement
11. ❓ **GA4 integration** - User visibility
12. ❓ **Auction room enhancements bundle** - Budgets, view all, etc.
13. ❓ **Screen size fix** - Samsung A56 issue identified

### 🔴 Larger Items (Phase 3+)
14. ❓ **Auth implementation** - Both OAuth + Magic Link
15. ❓ **Time-limited pilot access** - 4-6 hrs
16. ❓ **OneSignal push notifications** - 1-2 days (must have)
17. ❓ **Auto score updates** - 1-2 days (must have)

### ✅ Completed
- ✅ Phase 1 Quick Wins (Feb 6, 2026)
- ✅ Football scoring rules UI
- ✅ CL 2025/26 logo integration
- ✅ Fixture import skip completed matches
- ✅ Auction carousel order randomization
- ✅ Dark logo watermark visibility
- ✅ Help page Stitch standardization
- ✅ CORS explicit origin configuration
- ✅ My Competitions performance optimization (6s → <1s)
- ✅ Auto-reconnection logic (deployed)
- ✅ Ford Overoad league fix

---

## 🚀 PERFORMANCE & RELIABILITY IMPROVEMENTS

| Area | Before | After | Improvement |
|------|--------|-------|-------------|
| My Competitions load | ~6 seconds | <1 second | **6x faster** |
| DB queries (20 comps) | 30+ queries | 7 queries | **4x fewer** |
| DB connection loss | Manual restart required | Auto-reconnect | **Self-healing** |

---

**Document Version:** 4.6  
**Last Updated:** February 6, 2026

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 4.6 | Feb 6, 2026 | Phase 1 Quick Wins complete: Hide FE indicator, hide cricket, auction button layout, install help section |
| 4.5 | Feb 6, 2026 | Major update post team meeting: Added 20 pre-pilot tasks organized by effort/risk; New items include OneSignal, auto-scores, auction enhancements, time-limited access, hide cricket; Added dependencies and decision points |
| 4.4 | Feb 5, 2026 | Added pre-pilot readiness items: GA4, PWA install guide, hide dev indicators, Google OAuth |
| 4.3 | Feb 2, 2026 | Added auto-reconnection logic, Ford Overoad league fix, updated optimization audit |
| 4.2 | Feb 2, 2026 | Added CORS fix, My Competitions optimization (6s→<1s), loading state, toast fix |
| 4.1 | Feb 1, 2026 | Added Session 7 fixes: fixture import filter, carousel shuffle, dark watermarks, Help page standardization |
| 4.0 | Jan 30, 2026 | Major update: Marked Railway migration complete; Added Stitch redesign completion; Added logo integration; Updated phase to PRE-PILOT; Reorganized priorities |
| 3.0 | Jan 16, 2026 | Complete reorganization by phase; Added mobile strategy |
| 2.1 | Dec 21, 2025 | Added stress test findings |
| 2.0 | Dec 2025 | Initial comprehensive list |
