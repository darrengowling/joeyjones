# Outstanding Issues & Technical Debt

**Last Updated:** December 13, 2025 (Evening)  
**Updated By:** Agent  
**Purpose:** Living document tracking all known issues, bugs, and technical debt

---

## ⚠️ IMPORTANT: Keep This Document Updated

When fixing an issue, update this document:
1. Move item to "Resolved" section with date and solution
2. Add any new issues discovered during work
3. Update priority if circumstances change

---

## 🔴 P0 - Critical (Blocking Production)

*Currently no P0 issues - production is stable*

---

## 🟠 P1 - High Priority (Active Issues)

### ISSUE-016: Mobile Roster Not Updating After Win
**Status:** ROOT CAUSE IDENTIFIED - Fix ready, awaiting approval  
**Reported:** Dec 13, 2025  
**Latest Evidence:** "Ash friends test 2" - user reported "only got 1 team then full roster displayed"  
**Root Cause:** Race condition - `sold` handler calls `loadAuction()` (line 264) which overwrites fresh `participants` data with stale HTTP response  
**Files Involved:** `/app/frontend/src/pages/AuctionRoom.js` (line 264)  
**Proposed Fix:** Remove `loadAuction()` call from `onSold` handler - trust socket event data (same pattern as Phase 1 bid fix)  
**Risk:** 🟢 Low

### ISSUE-017: Mobile Connection/Lag Issues
**Status:** PARTIALLY ADDRESSED - Phase 1 implemented Dec 13, 2025  
**Reported:** Dec 13, 2025  
**Description:** Some mobile users report "laggy" bids and connection issues.  
**Root Cause Analysis:** Two major latency amplifiers identified:
1. Frontend: Every bid triggered 2 HTTP GETs per client (FIXED in Phase 1)
2. Backend: Hot path has ~10 sequential awaits

**Phase 1 Fix (IMPLEMENTED):**
- ✅ Removed `loadAuction()` and `loadClubs()` from `bid_placed` handler
- ✅ Added resync on socket reconnect only
- ✅ Added seq gap detection for missed events
- ✅ Added performance instrumentation

**Remaining Improvements:**
| Phase | Change | Risk | Status |
|-------|--------|------|--------|
| 2 | Remove diagnostic DB reads from hot path | 🟢 Low | NOT STARTED |
| 3 | Use `findOneAndUpdate` instead of update+read | 🟡 Medium | NOT STARTED |
| 4 | Consolidate to single socket event | 🟡 Medium | NOT STARTED |
| 5 | Socket.IO for bid submission | 🔴 Higher | NOT STARTED |

### ISSUE-018: Team Selection UX Confusion
**Status:** DESIGN DECISION NEEDED  
**Reported:** Dec 13, 2025  
**Description:** Commissioners selecting "PL" in create modal expect PL teams only, but all 74 teams selected by default. "Manage Teams" section below fold.  
**Impact:** Auctions started with wrong team mix  
**Proposed Options:**  
- A. Auto-filter teams based on `competitionCode` on page load (RECOMMENDED)
- B. Move team selection into create modal
- C. Warning before auction start if multiple competitions selected
- D. Start with NO teams selected

---

## 🟡 AWAITING INFO - User Testing Feedback (Dec 13)

### ISSUE-019: "Couldn't Place a Bid"
**Status:** AWAITING CLARIFICATION  
**Reported:** Dec 13, 2025 ("Ash friends test 2" testing)  
**Description:** "One player pressed the bid button but couldn't place a bid"  
**Possible Causes:**
- Budget exhausted (expected behavior)
- Roster full (expected behavior - button shows "Roster Full")
- Self-outbid rejection (expected - shows toast "You are already the highest bidder")
- Network timeout
- Button stuck in disabled state (bug)

**Questions for User:**
1. Did button show "Place Bid" or "Roster Full" or "Loading..."?
2. Was there an error toast message?
3. Did user have budget remaining?
4. What was the user trying to bid on?

### ISSUE-020: "United Offered 2 Times"
**Status:** AWAITING CLARIFICATION  
**Reported:** Dec 13, 2025 ("Ash friends test 2" testing)  
**Description:** "Roster lagged in 2 places and United was offered 2 times"  
**Possible Causes:**
- Unsold retry mechanism (EXPECTED - if no bids, team re-offered later with toast "Re-offering unsold team")
- Data bug causing duplicate entry
- UI showing stale data

**Questions for User:**
1. Which United? (Manchester United FC?)
2. Did the team go unsold the first time (no one bid)?
3. Was there a toast message like "Re-offering unsold team: Manchester United FC"?

### ISSUE-021: "Roster Lagged in 2 Places"
**Status:** AWAITING CLARIFICATION - Likely same as ISSUE-016  
**Reported:** Dec 13, 2025 ("Ash friends test 2" testing)  
**Description:** Roster display lagged/showed incorrect data  
**Likely Cause:** Same race condition as ISSUE-016 (loadAuction overwriting socket data)

---

## 🟠 P1 - High Priority (Should Address Soon)

### ISSUE-001: Manual Score Entry UI
**Status:** NOT STARTED  
**Estimated Effort:** 3-4 hours  
**Description:** Backend endpoint exists but no frontend UI for manual score entry.  
**Files:** `/app/frontend/src/pages/CompetitionDashboard.js`

### ISSUE-002: Commissioner Authorization Checks
**Status:** NOT STARTED  
**Estimated Effort:** 2 hours  
**Description:** TODO comments indicate missing auth checks in `server.py` (lines 3436, 3555)

### ISSUE-003: Sentry Error Monitoring
**Status:** CODE READY - NEEDS CONFIG  
**Estimated Effort:** 30 minutes  
**Description:** Sentry SDK integrated but `SENTRY_DSN` not set.  
**Action:** User to create Sentry account and provide DSN

---

## 🟡 P2 - Medium Priority

### ISSUE-004: ESLint Configuration Warning
**Status:** NOT STARTED  
**Effort:** 30 minutes  
**Description:** Non-blocking webpack warning about `react-hooks/exhaustive-deps`

### ISSUE-005: Mobile League Detail Long Scrolling
**Status:** MONITORING  
**Effort:** 2-3 hours  
**Description:** League Detail page requires excessive scrolling on mobile  
**Potential Fix:** Collapsible sections or tabs

### ISSUE-006: "Complete Lot" Button Redundancy
**Status:** MONITORING  
**Effort:** 1 hour  
**Description:** May no longer be needed - monitor usage

### ISSUE-007: Improve Cricket Error Messaging
**Status:** NOT STARTED  
**Effort:** 2 hours  
**Description:** Generic error messages for cricket operations

### ISSUE-022: "Unknown" Manager Names in Auction
**Status:** VERIFY IF STILL OCCURRING  
**Reported:** Dec 13, 2025 (UI Audit)  
**Description:** Screenshots showed "Unknown" for some manager names in AuctionRoom  
**Files:** `/app/frontend/src/pages/AuctionRoom.js`, `/app/backend/server.py`

---

## 🔵 P3 - Future / Post-Pilot

### ISSUE-008: Refactor server.py Monolith
**Effort:** 8 hours  
**Description:** Split 5,917 line file into modular routers

### ISSUE-009: Refactor Fixture Import Logic
**Effort:** 4 hours  
**Description:** Use `externalId` instead of fuzzy name matching

### ISSUE-010: User-Configurable Scoring Rules
**Effort:** 4 hours

### ISSUE-011: Auction History Tab
**Effort:** 4 hours

### ISSUE-012: Email Notifications
**Effort:** 6 hours

### ISSUE-013: Analytics Integration
**Effort:** 3 hours

### ISSUE-014: Database Automated Backups
**Effort:** 3 hours

### ISSUE-015: Performance/Load Testing
**Effort:** 4 hours**
```
/app/backend/
├── routers/
│   ├── auth.py
│   ├── leagues.py
│   ├── auctions.py
│   ├── fixtures.py
│   ├── scoring.py
│   └── assets.py
├── server.py (slim - just mounts routers)
```

---

### 9. Refactor Fixture Import Logic
**ID:** ISSUE-009  
**Status:** NOT STARTED  
**Estimated Effort:** 4 hours  
**Description:** Current import uses fuzzy name matching; should use `externalId` for reliability.  
**Impact:** Potential mismatches when team names differ slightly from API.  
**Files Involved:**
- `/app/backend/server.py` (fixture import endpoints)
- `/app/backend/sports_data_client.py`

---

### 10. User-Configurable Scoring Rules
**ID:** ISSUE-010  
**Status:** NOT STARTED  
**Estimated Effort:** 4 hours  
**Description:** Allow commissioners to customize scoring rules per league.  
**Impact:** Different tournaments may want different scoring systems.  
**Files Involved:**
- Backend: League model, scoring service
- Frontend: League creation/edit UI

---

### 11. Auction History Tab
**ID:** ISSUE-011  
**Status:** NOT STARTED  
**Estimated Effort:** 4 hours  
**Description:** Show complete bid history, final prices, who won what after auction.  
**Impact:** Users can't review auction results easily.  
**Files Involved:**
- New frontend component
- Backend: Query bids collection

---

### 12. Email Notifications
**ID:** ISSUE-012  
**Status:** NOT STARTED  
**Estimated Effort:** 6 hours  
**Description:** Send emails for competition invites, auction reminders, results.  
**Impact:** Users must manually check app for updates.  
**Integration:** SendGrid or similar service needed.

---

### 13. Analytics Integration
**ID:** ISSUE-013  
**Status:** NOT STARTED  
**Estimated Effort:** 3 hours  
**Description:** Add Google Analytics or similar to track user engagement.  
**Impact:** No visibility into user behavior.

---

### 14. Database Automated Backups
**ID:** ISSUE-014  
**Status:** NOT STARTED  
**Estimated Effort:** 3 hours  
**Description:** Set up automated daily backups with retention policy.  
**Impact:** Risk of data loss without backups.

---

### 15. Performance/Load Testing
**ID:** ISSUE-015  
**Status:** NOT STARTED  
**Estimated Effort:** 4 hours  
**Description:** Load test for 150 concurrent users before scaling pilot.  
**Impact:** Unknown capacity limits.

---

## ✅ Resolved Issues

| ID | Issue | Resolved Date | Solution |
|----|-------|---------------|----------|
| - | Debug report missing server state | Dec 19, 2025 | Enhanced debugLogger to capture all 15 socket events + fetch server-side auction state via `/api/debug/auction-state/{id}` |
| - | Users can outbid themselves | Dec 13, 2025 | Added backend validation to reject bids from current highest bidder |
| - | 500 error on first bid | Dec 12, 2025 | Fixed Pydantic serialization and None value handling |
| - | Screen freeze on auction deletion | Dec 12, 2025 | Added `auction_deleted` Socket.IO event |
| - | Mobile horizontal scrolling | Dec 12, 2025 | Fixed AuctionRoom.js responsive layout |
| - | Bid validation (accept equal bids) | Dec 12, 2025 | Fixed to require bids > current highest |
| - | Socket.IO multi-pod not working | Dec 8, 2025 | Configured Redis Cloud for pub/sub |
| - | Football scoring not working | Nov 30, 2025 | Rewrote scoring logic for shared fixtures |
| - | Cricket competition creation blocked | Nov 25, 2025 | Fixed /api/clubs endpoint for multi-sport |

---

## 📝 Update Instructions

**When finding a new issue:**
1. Add to appropriate priority section
2. Assign ID (ISSUE-XXX)
3. Include: Status, Effort estimate, Description, Impact, Files involved

**When fixing an issue:**
1. Move to "Resolved Issues" table
2. Add resolution date and solution summary
3. Update any related issues

---

**Document Version:** 1.0  
**Next Review:** Weekly during active development
