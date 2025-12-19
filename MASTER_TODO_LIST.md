# Master TODO List - Sport X Platform

**Last Updated:** December 19, 2025  
**Purpose:** Single source of truth for all work items - issues, bugs, features, and technical debt

---

## Quick Stats

| Category | Count |
|----------|-------|
| 🔴 Immediate (Ready to Fix) | 1 |
| 🟡 Awaiting Info | 3 |
| 🟠 Medium Priority - Technical | 5 |
| 🟠 Medium Priority - UI/UX | 5 |
| 🟠 Medium Priority - Config | 2 |
| 🔵 Post-Pilot | 15 |
| ✅ Recently Resolved | 10 |

---

## 🔴 IMMEDIATE - Ready to Fix

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 1 | **ISSUE-016** | **Roster Not Updating** - User wins team but roster shows wrong count or "Full" prematurely | Race condition: `onSold` handler calls `loadAuction()` (line 264) which overwrites fresh socket data with stale HTTP response | Remove `loadAuction()` from `onSold` handler - trust socket event data (same pattern as Phase 1 bid fix) | 🟢 Low | Fixes roster display issues, improves mobile reliability |

**Files:** `/app/frontend/src/pages/AuctionRoom.js` (line 264)  
**Evidence:** "Ash friends test 2" - user reported "only got 1 team then full roster displayed"  
**Status:** ROOT CAUSE IDENTIFIED - Fix ready, awaiting approval

---

## 🟡 AWAITING INFO - Need Clarification

| # | Issue ID | Summary | Potential Causes | Potential Fix | Risk | Benefit |
|---|----------|---------|------------------|---------------|------|---------|
| 1 | **ISSUE-019** | **"Couldn't Place Bid"** - User pressed bid button but bid didn't go through | Budget exhausted (expected), roster full (expected), self-outbid rejection (expected), network timeout, or button stuck disabled (bug) | Depends on cause - may be expected behavior or need UI clarification | 🟢-🟡 | Clearer error messaging, better UX |
| 2 | **ISSUE-020** | **"United Offered 2 Times"** - Same team appeared twice in auction | Expected: unsold retry re-offers teams later with toast; OR bug: duplicate queue entry | If expected: improve "Re-offering" toast visibility; if bug: fix queue logic | 🟢-🟡 | Reduces user confusion |
| 3 | **ISSUE-021** | **"Roster Lagged"** - Roster display showed incorrect/delayed data in multiple places | Same race condition as ISSUE-016 (loadAuction overwriting socket data) | Same fix as ISSUE-016 | 🟢 Low | Consistent, real-time roster updates |

**Source:** "Ash friends test 2" testing (Dec 13, 2025)

**Questions Pending:**
- ISSUE-019: Was button disabled? Error message shown? Budget remaining?
- ISSUE-020: Did team go unsold first? Was there "Re-offering unsold team" toast?
- ISSUE-021: Likely same root cause as ISSUE-016 - needs confirmation

---

## 🟠 MEDIUM PRIORITY - Technical/Bugs

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 1 | **ISSUE-018** | **Team Selection UX Confusion** - Commissioners select "PL" but get all 74 teams from all competitions | `competitionCode` not used to filter teams on LeagueDetail page load. "Manage Teams" section below fold. | Auto-filter teams based on `competitionCode` when page loads (RECOMMENDED). Options: A) Auto-filter, B) Move to create modal, C) Warning before start, D) No default selection | 🟢 Low | Prevents wrong team selection, major UX improvement |
| 2 | **ISSUE-017 Phase 2** | **Backend Diagnostic Reads** - Unnecessary DB reads in bid hot path add latency | Diagnostic logging reads league + participants on every bid | Move diagnostic reads to async background task | 🟢 Low | ~50ms faster bid processing |
| 3 | **ISSUE-017 Phase 3** | **Backend findOneAndUpdate** - Extra DB read to get sequence number after update | Separate update + read operations | Use `findOneAndUpdate` with `returnDocument: "after"` | 🟡 Medium | Eliminates 1 DB round-trip per bid |
| 4 | **ISSUE-002** | **Commissioner Auth Checks** - Missing authorization checks on some endpoints | TODO comments never implemented (server.py lines 3436, 3555) | Add `require_commissioner` check to flagged endpoints | 🟡 Medium | Security improvement |
| 5 | **ISSUE-022** | **"Unknown" Manager Names** - Some manager names display as "Unknown" in auction | Missing `userName` in participant data or display logic bug | Verify data flow, ensure userName populated | 🟢 Low | Better user identification |

**Files:**
- ISSUE-018: `/app/frontend/src/pages/LeagueDetail.js`
- ISSUE-017: `/app/backend/server.py` (bid hot path)
- ISSUE-002: `/app/backend/server.py` (lines 3436, 3555)
- ISSUE-022: `/app/frontend/src/pages/AuctionRoom.js`, `/app/backend/server.py`

---

## 🟠 MEDIUM PRIORITY - UI/UX

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 6 | - | **Demote "Explore" Button** - "Explore Teams" has equal visual weight to Create/Join | Button hierarchy not optimized | Change from button to text link | 🟢 Low | Reclaims mobile space, clearer primary actions |
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
| 12 | - | **Rate Limiting** - Rate limiting code exists but disabled | `ENABLE_RATE_LIMITING=false` for testing | Change to `true` in production env | 🟢 Low | Protection against API abuse |

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

---

## 🔵 POST-PILOT - Infrastructure & Nice to Have

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 10 | **ISSUE-013** | **Analytics** - No visibility into user behavior | Not implemented | Add Google Analytics | 🟢 Low | Usage insights |
| 11 | **ISSUE-014** | **Database Backups** - Risk of data loss | No automated backups | Configure MongoDB Atlas daily backups | 🟢 Low | Data protection |
| 12 | **ISSUE-004** | **ESLint Warnings** - Build output cluttered with warnings | Missing ESLint rule config | Add rule to eslintrc | 🟢 Low | Cleaner builds |
| 13 | **ISSUE-007** | **Cricket Error Messages** - Generic error messages for cricket | Insufficient error handling | Add specific error messages | 🟢 Low | Better user feedback |
| 14 | **ISSUE-005** | **LeagueDetail Scrolling** - Excessive scrolling on mobile | Long page design | Add collapsible sections or tabs | 🟢 Low | Better mobile UX |
| 15 | **ISSUE-006** | **"Complete Lot" Button** - Button may be redundant | Added for now-fixed bug | Monitor usage, remove if unused | 🟢 Low | Cleaner UI |

---

## ✅ RECENTLY RESOLVED (Dec 2025)

| # | Issue | Summary | Solution | Date |
|---|-------|---------|----------|------|
| 1 | **Debug report** | Debug report only captured client-side data, couldn't diagnose server issues | Enhanced to capture 15 socket events + server state. Auto-uploads to MongoDB with reference ID. Query via `/api/debug/reports` | Dec 19 |
| 2 | **Self-outbid** | Users could increase their own winning bid | Backend validation + input reset on rejection | Dec 13 |
| 3 | **Bid lag Phase 1** | 2 HTTP GETs per bid per client causing lag | Removed loadAuction/loadClubs from bid_placed handler | Dec 13 |
| 4 | **500 on first bid** | Server error on initial bid | Fixed Pydantic serialization, None handling | Dec 12 |
| 5 | **Frozen on delete** | Screen froze when auction deleted | Added auction_deleted socket event | Dec 12 |
| 6 | **Horizontal scroll** | Mobile auction room had horizontal scroll | Fixed responsive layout | Dec 12 |
| 7 | **Equal bid accepted** | Bids equal to current were accepted | Changed to require bid > current | Dec 12 |
| 8 | **Multi-pod Socket.IO** | Socket.IO didn't work across pods | Configured Redis Cloud pub/sub | Dec 8 |
| 9 | **Production outage** | 520 error, service unavailable | Emergent platform issue - resolved after redeploy | Dec 13 |
| 10 | **Debug endpoint bug** | `/api/debug/auction-state` failed on clubsWon string IDs | Fixed to handle both string IDs and dict objects | Dec 19 |

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

---

## 🎯 RECOMMENDED NEXT ACTIONS

**Immediate:**
1. Configure Sentry (code ready, need DSN) - 30 min
2. Implement ISSUE-016 fix (remove loadAuction from onSold) - 30 min
3. Deploy and test with users

**After user feedback on ISSUE-019/020/021:**
4. Address based on clarification received

**When ready for UI/UX:**
5. Team selection auto-filter (ISSUE-018) - needs design decision
6. Bidder status indicator ("YOU'RE WINNING") - 2 hrs

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

**Document Version:** 2.0  
**Last Updated:** December 19, 2025
