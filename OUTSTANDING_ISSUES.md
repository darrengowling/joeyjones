# Outstanding Issues & Technical Debt

**Last Updated:** December 13, 2025  
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

## 🟠 P1 - High Priority (Under Investigation)

### ISSUE-016: Mobile Roster Not Updating After Win
**Status:** MONITORING - Awaiting test results  
**Reported:** Dec 13, 2025  
**Description:** Some mobile users report roster not always updating after successfully winning a bid.  
**Hypothesis:** Race condition between `sold` socket event and `loadAuction()` API call overwriting fresh data with stale data.  
**Files Involved:** `/app/frontend/src/pages/AuctionRoom.js` (lines 234-237)  
**Data Needed:** Device/browser, does refresh fix it, console errors  
**Proposed Fix:** Remove `loadAuction()` call from `onSold` handler - trust socket event data

### ISSUE-017: Mobile Connection/Lag Issues
**Status:** PARTIALLY ADDRESSED - Phase 1 implemented Dec 13, 2025  
**Reported:** Dec 13, 2025  
**Description:** Some (not all) mobile users report losing connection repeatedly and bids being "laggy".  
**Root Cause Analysis:** Identified two major latency amplifiers:
1. Frontend: Every bid triggered 2 HTTP GETs (`loadAuction()` + `loadClubs()`) for every client
2. Backend: Hot path has ~10 sequential awaits (7 DB reads, 2-3 writes, 2 emits)

**Phase 1 Fix (IMPLEMENTED):**
- Removed `loadAuction()` and `loadClubs()` from `bid_placed` handler
- Added resync on socket reconnect only
- Added seq gap detection for missed events
- Added performance instrumentation (tap→ack, receive→render timing)

**Remaining Improvements (Phase 2-5):**
| Phase | Change | Risk | Status |
|-------|--------|------|--------|
| 2 | Remove diagnostic DB reads from hot path | 🟢 Low | NOT STARTED |
| 3 | Use `findOneAndUpdate` instead of update+read | 🟡 Medium | NOT STARTED |
| 4 | Consolidate to single socket event | 🟡 Medium | NOT STARTED |
| 5 | Socket.IO for bid submission (optional) | 🔴 Higher | NOT STARTED |

**Instrumentation Added:** Console logs now show:
- `tapToAckMs`: Time from bid tap to server response
- `serverLatencyMs`: Server-to-client latency
- `bid_update rendered: totalMs`: Receive-to-render time

**Files Modified:** 
- `/app/frontend/src/pages/AuctionRoom.js` (bid handlers)
- `/app/backend/server.py` (serverTime in emit)

### ISSUE-018: Team Selection UX Confusion
**Status:** MONITORING - Design decision needed  
**Reported:** Dec 13, 2025  
**Description:** Commissioners selecting "PL" in create modal expect PL teams only, but all 74 teams are selected by default. "Manage Teams" section is below the fold and easy to miss.  
**Impact:** Auctions started with wrong team mix (PL + CL + AFCON combined)  
**Proposed Options:**  
- A. Auto-filter teams based on `competitionCode` on page load (recommended)  
- B. Move team selection into create modal  
- C. Warning before auction start if multiple competitions selected  
- D. Start with NO teams selected  
**Proposed Fix:** TBD - awaiting user preference

---

## 🟠 P1 - High Priority (Should Address Soon)

### 1. Manual Score Entry UI
**ID:** ISSUE-001  
**Status:** NOT STARTED  
**Estimated Effort:** 3-4 hours  
**Description:** Backend endpoint `PATCH /api/fixtures/{id}/score` exists but there's no frontend UI for commissioners to manually enter/update scores.  
**Impact:** Commissioners must use CSV upload or API calls to update scores.  
**Files Involved:**
- Backend: `/app/backend/server.py` (endpoint exists)
- Frontend: `/app/frontend/src/pages/CompetitionDashboard.js` (needs UI)

**Acceptance Criteria:**
- [ ] UI on Fixtures tab to edit individual fixture scores
- [ ] Validation for score inputs
- [ ] Automatic recompute trigger after save
- [ ] Success/error feedback to user

---

### 2. Commissioner Authorization Checks
**ID:** ISSUE-002  
**Status:** NOT STARTED  
**Estimated Effort:** 2 hours  
**Description:** Two TODO comments in server.py indicate missing authorization checks.  
**Impact:** Currently any authenticated user might access commissioner-only functions.  
**Files Involved:**
- `/app/backend/server.py` (lines 3436, 3555)

**Code References:**
```python
# Line 3436: # TODO: Add commissioner authorization check when auth is implemented
# Line 3555: # TODO: Add commissioner authorization check here when auth is implemented
```

**Acceptance Criteria:**
- [ ] Verify user is league commissioner before allowing action
- [ ] Return 403 Forbidden if not authorized
- [ ] Add tests for authorization

---

### 3. Sentry Error Monitoring Not Configured
**ID:** ISSUE-003  
**Status:** CODE READY - NEEDS CONFIG  
**Estimated Effort:** 30 minutes  
**Description:** Sentry SDK is integrated in the code but `SENTRY_DSN` is not set.  
**Impact:** No automated error tracking or alerting in production.  
**Files Involved:**
- `/app/backend/server.py` (lines 31-34, 84-106)
- `/app/backend/.env` (SENTRY_DSN empty)

**To Enable:**
1. Create Sentry account at https://sentry.io
2. Create new project (Python/FastAPI)
3. Get DSN from project settings
4. Set `SENTRY_DSN` in production environment variables
5. Redeploy

---

## 🟡 P2 - Medium Priority (Nice to Have)

### 4. ESLint Configuration Warning
**ID:** ISSUE-004  
**Status:** NOT STARTED  
**Estimated Effort:** 30 minutes  
**Description:** Non-blocking webpack warning about `react-hooks/exhaustive-deps` rule not being defined.  
**Impact:** Cosmetic - clutters build output but doesn't affect functionality.  
**Files Involved:**
- `/app/frontend/package.json` or `.eslintrc.json`

---

### 5. Mobile League Detail Page Long Scrolling
**ID:** ISSUE-005  
**Status:** MONITORING  
**Estimated Effort:** 2-3 hours  
**Description:** The redesigned League Detail page requires significant scrolling on mobile.  
**Impact:** UX friction for commissioners on mobile devices.  
**Files Involved:**
- `/app/frontend/src/pages/LeagueDetail.js`

**Potential Solutions:**
- Collapsible sections
- Sticky action buttons
- Tab-based layout for mobile

---

### 6. "Complete Lot" Button Redundancy
**ID:** ISSUE-006  
**Status:** MONITORING  
**Estimated Effort:** 1 hour  
**Description:** This button was added as a manual override for a now-fixed bug. May no longer be needed.  
**Impact:** UI clutter if not used.  
**Action:** Monitor during testing - remove if unused.

---

### 7. Improve Cricket Error Messaging
**ID:** ISSUE-007  
**Status:** NOT STARTED  
**Estimated Effort:** 2 hours  
**Description:** Error messages for cricket operations (especially future matches) are too generic.  
**Impact:** Users don't understand what went wrong.  
**Files Involved:**
- `/app/backend/server.py` (cricket endpoints)
- `/app/backend/services/scoring/cricket.py`

---

## 🔵 P3 - Future (Technical Debt / Enhancements)

### 8. Refactor server.py Monolith
**ID:** ISSUE-008  
**Status:** NOT STARTED  
**Estimated Effort:** 8 hours  
**Description:** `server.py` is 5,917 lines - should be split into modular routers.  
**Impact:** Maintainability, testing, code reviews all harder.  
**Proposed Structure:**
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
