# Master TODO List - Sport X Platform

**Last Updated:** December 21, 2025  
**Purpose:** Single source of truth for all work items - issues, bugs, features, and technical debt

---

## Quick Stats

| Category | Count |
|----------|-------|
| 🔍 Monitoring | 5 |
| 🟠 Medium Priority - Technical | 2 |
| 🟠 Medium Priority - UI/UX | 4 |
| 🟠 Medium Priority - Config | 1 |
| 🔵 Post-Pilot | 18 |
| ✅ Recently Resolved | 17 |

---

## 🔍 MONITORING - Needs More Data

| # | Issue ID | Summary | Cause | Evidence | Status |
|---|----------|---------|-------|----------|--------|
| 1 | **ISSUE-016** | **Roster Not Updating** - User wins team but roster shows wrong count or "Full" prematurely | Suspected race condition under higher concurrency (7+ users) | Single report from "Ash friends test 2" (7-user auction). Not reproduced in 100s of 4-6 user tests. | 🔍 MONITORING |
| 2 | **ISSUE-019** | **"Couldn't Place Bid"** - User pressed bid button but bid didn't go through | Likely expected behavior (roster full) | Investigation suggests roster was full when bid attempted | 🔍 MONITORING |
| 3 | **ISSUE-020** | **"United Offered 2 Times"** - Same team appeared twice mid-auction | Frontend display bug or socket duplication | No recurrence reported | 🔍 MONITORING |
| 4 | **ISSUE-021** | **"Roster Lagged"** - Roster display showed incorrect/delayed data | Same root cause as ISSUE-016 | Linked to ISSUE-016 | 🔍 MONITORING |
| 5 | **ISSUE-022** | **"Unknown" Manager Names** - Some managers show as "Unknown" | Missing userName in participant data | Not recurring in recent tests (Dec 21) | 🔍 MONITORING |

**Decision (Dec 21, 2025):** All above issues moved to monitoring. Will revisit if they recur in larger group testing.

**Files:** `/app/frontend/src/pages/AuctionRoom.js`  
**Next Action:** Wait for reproduction with debug report capture.

---

## 🟠 MEDIUM PRIORITY - Technical/Bugs

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 1 | **ISSUE-017 Phase 2** | **Backend Diagnostic Reads** - Unnecessary DB reads in bid hot path add latency | Diagnostic logging reads league + participants on every bid | Move diagnostic reads to async background task | 🟢 Low | ~20-50ms faster bid processing |
| 2 | **ISSUE-002** | **Commissioner Auth Checks** - Missing authorization checks on some endpoints | TODO comments never implemented (server.py lines 3436, 3555) | Add `require_commissioner` check to flagged endpoints | 🟡 Medium | Security improvement |

**Files:**
- ISSUE-017: `/app/backend/server.py` (bid hot path)
- ISSUE-002: `/app/backend/server.py` (lines 3436, 3555)

---

## 🟠 MEDIUM PRIORITY - UI/UX

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 6 | - | **Demote "Explore" Button** - "Explore Teams" has equal visual weight to Create/Join | Button hierarchy not optimized | Consider removing altogether - serves no critical purpose | 🟢 Low | Reclaims mobile space, clearer primary actions |
| 7 | - | **Bidder Status Indicator** - Users don't know if they're winning or outbid at a glance | No visual differentiation for current bidder | Add "YOU'RE WINNING" (green) / "OUTBID" (red) indicator | 🟢 Low | Major clarity improvement for auctions |
| 8 | - | **Team Count Preview** - Users don't know how many teams they'll get when creating competition | No preview shown after competition selection | Add "20 PL teams will be included" text after dropdown | 🟢 Low | Sets correct expectations |
| 9 | - | **Current Bid Label** - Bid input field lacks context for current bid amount | Only placeholder text, no label | Add "Current bid: £Xm" label above input | 🟢 Low | Clearer bidding context |
| 10 | - | **Sticky Tabs (Mobile)** - Dashboard tabs scroll away on mobile | Standard scroll behavior | Make tab bar sticky/fixed | 🟢 Low | Better mobile navigation |

**Files:**
- Explore button: `/app/frontend/src/pages/MyCompetitions.js`
- Bidder status: `/app/frontend/src/pages/AuctionRoom.js`
- Team count: `/app/frontend/src/components/CreateLeagueModal.js`
- Bid label: `/app/frontend/src/pages/AuctionRoom.js`
- Sticky tabs: `/app/frontend/src/pages/CompetitionDashboard.js`

---

## 🟠 MEDIUM PRIORITY - Configuration

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 11 | **ISSUE-003** | **Sentry Monitoring** - No automated error tracking in production | `SENTRY_DSN` not configured (code is ready) | User creates Sentry account, adds DSN to env vars | 🟢 Low | Visibility into production errors |

---

## 🔵 POST-PILOT - Technical Debt

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 1 | **ISSUE-008** | **Refactor server.py** - 5,917 line monolithic file | Rapid development, no time to split | Split into modular routers (auth, leagues, auctions, fixtures, scoring, assets) | 🟡 Medium | Maintainability, easier debugging |
| 2 | **ISSUE-009** | **Fixture Import Logic** - Fuzzy name matching for fixture imports | Legacy implementation | Use `externalId` instead of name matching | 🟡 Medium | More reliable fixture imports |
| 3 | **ISSUE-017 Phase 4** | **Consolidate Socket Events** - Two events per bid (`bid_update` + `bid_placed`) | Historical design | Merge into single `bid_committed` event | 🟡 Medium | Simpler client code, less state churn |
| 4 | **ISSUE-017 Phase 5** | **Socket.IO Bidding** - HTTP POST for bids adds latency on mobile | Current architecture uses REST for bids | Use Socket.IO emit with ack for bidding | 🔴 Higher | Faster mobile bidding, fewer failure modes |

---

## 🔵 POST-PILOT - New Features

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 5 | **ISSUE-001** | **Manual Score Entry UI** - No UI for manual score updates | Backend exists, frontend not built | Build score entry UI in CompetitionDashboard | 🟢 Low | Commissioners can fix scores without CSV |
| 6 | **ISSUE-011** | **Auction History Tab** - Can't review bid history after auction | Feature not implemented | Add history tab showing all bids, prices, winners | 🟢 Low | Post-auction review capability |
| 7 | **ISSUE-010** | **Custom Scoring Rules** - All leagues use same scoring rules | Hardcoded scoring | Add commissioner UI to customize points | 🟡 Medium | Flexibility for different tournaments |
| 8 | **ISSUE-012** | **Email Notifications** - Users must manually check app | No email integration | Integrate SendGrid for invites, reminders, results | 🟡 Medium | Better user engagement |
| 9 | - | **Payment Integration** - No entry fees or charity donations | Feature not built | Stripe Connect integration (see PAYMENT_INTEGRATION_PLAN.md) | 🟡 Medium | Revenue capability, charity support |
| 10 | **ISSUE-024** | **Auto-Import Fixtures** - Users forget to import fixtures, scoring fails | Manual step easily missed | Auto-import fixtures when commissioner saves teams (Option A: trigger on `update_league_assets`) | 🟢 Low | Removes friction, prevents "no scores" confusion |

---

## 🔵 POST-PILOT - Infrastructure & Nice to Have

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 11 | **ISSUE-013** | **Analytics** - No visibility into user behavior | Not implemented | Add Google Analytics | 🟢 Low | Usage insights |
| 12 | **ISSUE-014** | **Database Backups** - Risk of data loss | No automated backups | Configure MongoDB Atlas daily backups | 🟢 Low | Data protection |
| 13 | **ISSUE-004** | **ESLint Warnings** - Build output cluttered with warnings | Missing ESLint rule config | Add rule to eslintrc | 🟢 Low | Cleaner builds |
| 14 | **ISSUE-007** | **Cricket Error Messages** - Generic error messages for cricket | Insufficient error handling | Add specific error messages | 🟢 Low | Better user feedback |
| 15 | **ISSUE-005** | **LeagueDetail Scrolling** - Excessive scrolling on mobile | Long page design | Add collapsible sections or tabs | 🟢 Low | Better mobile UX |
| 16 | **ISSUE-006** | **"Complete Lot" Button** - Button may be redundant | Added for now-fixed bug | Monitor usage, remove if unused | 🟢 Low | Cleaner UI |
| 17 | - | **Rate Limiting** - Rate limiting function exists but not applied to endpoints | Deferred during development | Apply `get_rate_limiter()` to key endpoints | 🟢 Low | Protection against API abuse |
| 18 | **ISSUE-025** | **Rename Help to User Testing Guide** - "Help" button name not clear | Generic naming | Rename "Help" to "User Testing Guide" in UI | 🟢 Low | Clearer purpose for testers |

---

## ✅ RECENTLY RESOLVED (Dec 2025)

| # | Issue | Summary | Solution | Date |
|---|-------|---------|----------|------|
| 1 | **AFCON Data Fix** | Kenya shown instead of Cameroon in AFCON competition, incorrect fixtures | Admin endpoints to update assets in production, corrected fixtures CSV uploaded (36 group matches) | Dec 21 |
| 2 | **ISSUE-023** | Bid input race condition - rapid bidding caused typed amounts to append/inflate | Made bid input read-only, added +1m/+2m buttons (now: +1m, +2m, +5m, +10m, +20m, +50m) | Dec 21 |
| 3 | **ISSUE-018 Enhancement** | "Manage Clubs" modal showed all 74 teams even when PL selected | Auto-populate `assetsSelected` on league creation + default filter dropdown to competition | Dec 21 |
| 4 | **ISSUE-018** | Team Selection UX - LeagueDetail showed all 74 clubs instead of competition-specific clubs | Backend `get_league_assets()` now filters by `competitionCode` when `assetsSelected` is empty. PL shows exactly 20 clubs. | Dec 20 |
| 5 | **Debug report** | Debug report only captured client-side data, couldn't diagnose server issues | Enhanced to capture 15 socket events + server state. Auto-uploads to MongoDB with reference ID. Query via `/api/debug/reports` | Dec 19 |
| 6 | **Self-outbid** | Users could increase their own winning bid | Backend validation + input reset on rejection | Dec 13 |
| 7 | **Bid lag Phase 1** | 2 HTTP GETs per bid per client causing lag | Removed loadAuction/loadClubs from bid_placed handler | Dec 13 |
| 8 | **500 on first bid** | Server error on initial bid | Fixed Pydantic serialization, None handling | Dec 12 |
| 9 | **Frozen on delete** | Screen froze when auction deleted | Added auction_deleted socket event | Dec 12 |
| 10 | **Horizontal scroll** | Mobile auction room had horizontal scroll | Fixed responsive layout | Dec 12 |
| 11 | **Equal bid accepted** | Bids equal to current were accepted | Changed to require bid > current | Dec 12 |
| 12 | **Multi-pod Socket.IO** | Socket.IO didn't work across pods | Configured Redis Cloud pub/sub | Dec 8 |
| 13 | **Production outage** | 520 error, service unavailable | Emergent platform issue - resolved after redeploy | Dec 13 |
| 14 | **Debug endpoint bug** | `/api/debug/auction-state` failed on clubsWon string IDs | Fixed to handle both string IDs and dict objects | Dec 19 |
| 15 | **Debug report upload** | Debug reports only downloaded locally, support couldn't access | Added server upload with reference IDs, queryable via `/api/debug/reports` | Dec 19 |
| 16 | **Socket event logging** | Debug reports missing socket event data | Added `logSocketEvent()` calls to all 15 socket handlers in AuctionRoom.js | Dec 19 |

---

## ❌ FAILED FIX ATTEMPTS (Dec 19, 2025)

| Issue | Attempted Fix | Result | Status |
|-------|---------------|--------|--------|
| **ISSUE-016** | Remove `loadAuction()` from `onSold` handler | Broke countdown display between lots | REVERTED |
| ~~**ISSUE-018**~~ | ~~Auto-filter `loadAssets()` by competition~~ | ~~Multiple attempts failed~~ | ✅ RESOLVED Dec 20 - Backend fix in `get_league_assets()` |

**Lessons:**
- Agent made "incremental guesses" instead of thorough analysis
- Agent repeatedly ignored instructions to get approval before code changes
- Agent didn't check downstream dependencies before implementing fixes
- "Low risk" fixes can have hidden dependencies
- **Success (Dec 20):** Proper analysis of data flow before implementation led to clean backend fix

---

## 📋 MONITORING - Watch During Testing

| Item | What to Watch For |
|------|-------------------|
| Production stability | 520 errors, service unavailable |
| Self-outbid fix | Toast appears, input resets correctly |
| Bid lag improvement | Check console for tapToAckMs, serverLatencyMs |
| Roster updates | Does roster display update after winning? |
| "Complete Lot" button | Is it being used? If not, remove |
| Debug reports | Are commissioners using "Report Issue" button? |
| Bid input buttons | Are +1m/+2m buttons being used? Is read-only input confusing? |

---

## 🎯 RECOMMENDED NEXT ACTIONS

**If proceeding with E1:**
1. Configure Sentry (code ready, need DSN) - 30 min - CONFIG ONLY
2. Rate limiting enable - CONFIG ONLY
3. Backend-only fixes (ISSUE-017 Phase 2/3) - lower risk than frontend

**DO NOT attempt without thorough analysis:**
- ISSUE-016 (Roster Not Updating) - has hidden dependencies
- ISSUE-018 (Team Selection UX) - partial fix only, frontend display broken

---

## 📁 Related Documentation

| Document | Purpose |
|----------|---------|
| `/app/UI_UX_AUDIT_REPORT.md` | Full UI/UX review with screenshots |
| `/app/PRODUCTION_ENVIRONMENT_STATUS.md` | Current production state |
| `/app/PAYMENT_INTEGRATION_PLAN.md` | Post-pilot payment feature |
| `/app/MIGRATION_PLAN.md` | Contingency - move off Emergent |
| `/app/AGENT_ONBOARDING_CHECKLIST.md` | For new developers/agents |

---

## 📝 Update Instructions

**When finding a new issue:**
1. Add to appropriate priority section with Issue ID
2. Include: Summary, Cause, Fix, Risk, Benefit
3. Add file locations if known

**When fixing an issue:**
1. Move to "Recently Resolved" section
2. Add resolution date and solution summary
3. Update Quick Stats counts

---

**Document Version:** 2.1  
**Last Updated:** December 21, 2025
