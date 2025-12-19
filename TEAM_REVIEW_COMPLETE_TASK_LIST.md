# Complete Task List for Team Review

**Last Updated:** December 19, 2025  
**Purpose:** Comprehensive task list with summary, cause, fix, risk, and benefit for each item

---

## 🔴 IMMEDIATE (Ready to Fix)

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 1 | **Roster Not Updating (ISSUE-016)** | User wins team but roster shows wrong count or "Full" prematurely | Race condition: `onSold` handler calls `loadAuction()` which overwrites fresh socket data with stale HTTP response | Remove `loadAuction()` from `onSold` handler - trust socket event data | 🟢 Low | Fixes roster display issues, improves mobile reliability |

---

## 🟡 AWAITING INFO (Need Clarification)

| # | Issue | Summary | Potential Causes | Potential Fix | Risk | Benefit |
|---|-------|---------|------------------|---------------|------|---------|
| 1 | **"Couldn't Place Bid" (ISSUE-019)** | User pressed bid button but bid didn't go through | Budget exhausted, roster full, self-outbid rejection, network timeout, or button stuck disabled | Depends on cause - may be expected behavior or need UI clarification | 🟢-🟡 | Clearer error messaging, better UX |
| 2 | **"United Offered 2 Times" (ISSUE-020)** | Same team appeared twice in auction | Expected: unsold retry re-offers teams later; OR bug: duplicate queue entry | If expected: improve "Re-offering" toast visibility; if bug: fix queue logic | 🟢-🟡 | Reduces user confusion |
| 3 | **"Roster Lagged" (ISSUE-021)** | Roster display showed incorrect/delayed data in multiple places | Same race condition as ISSUE-016 | Same fix as ISSUE-016 | 🟢 Low | Consistent, real-time roster updates |

---

## 🟠 MEDIUM PRIORITY - Technical/Bugs

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 1 | **Team Selection UX (ISSUE-018)** | Commissioners select "PL" but get all 74 teams from all competitions | `competitionCode` not used to filter teams on LeagueDetail page load | Auto-filter teams based on `competitionCode` when page loads | 🟢 Low | Prevents wrong team selection, major UX improvement |
| 2 | **Backend Diagnostic Reads (Phase 2)** | Unnecessary DB reads in bid hot path add latency | Diagnostic logging reads league + participants on every bid | Move diagnostic reads to async background task | 🟢 Low | ~50ms faster bid processing |
| 3 | **Backend findOneAndUpdate (Phase 3)** | Extra DB read to get sequence number after update | Separate update + read operations | Use `findOneAndUpdate` with `returnDocument: "after"` | 🟡 Medium | Eliminates 1 DB round-trip per bid |
| 4 | **Commissioner Auth (ISSUE-002)** | Missing authorization checks on some endpoints | TODO comments never implemented | Add `require_commissioner` check to flagged endpoints | 🟡 Medium | Security improvement |
| 5 | **"Unknown" Manager Names (ISSUE-022)** | Some manager names display as "Unknown" in auction | Missing `userName` in participant data or display logic bug | Verify data flow, ensure userName populated | 🟢 Low | Better user identification |

---

## 🟠 MEDIUM PRIORITY - UI/UX

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 6 | **Demote "Explore" Button** | "Explore Teams" has equal visual weight to Create/Join | Button hierarchy not optimized | Change from button to text link | 🟢 Low | Reclaims mobile space, clearer primary actions |
| 7 | **Bidder Status Indicator** | Users don't know if they're winning or outbid at a glance | No visual differentiation for current bidder | Add "YOU'RE WINNING" (green) / "OUTBID" (red) indicator | 🟢 Low | Major clarity improvement for auctions |
| 8 | **Team Count Preview** | Users don't know how many teams they'll get when creating competition | No preview shown after competition selection | Add "20 PL teams will be included" text after dropdown | 🟢 Low | Sets correct expectations |
| 9 | **Current Bid Label** | Bid input field lacks context for current bid amount | Only placeholder text, no label | Add "Current bid: £Xm" label above input | 🟢 Low | Clearer bidding context |
| 10 | **Sticky Tabs (Mobile)** | Dashboard tabs scroll away on mobile | Standard scroll behavior | Make tab bar sticky/fixed | 🟢 Low | Better mobile navigation |

---

## 🟠 MEDIUM PRIORITY - Configuration

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 11 | **Sentry Monitoring (ISSUE-003)** | No automated error tracking in production | `SENTRY_DSN` not configured | User creates Sentry account, adds DSN to env vars | 🟢 Low | Visibility into production errors |
| 12 | **Rate Limiting** | Rate limiting code exists but disabled | `ENABLE_RATE_LIMITING=false` for testing | Change to `true` in production env | 🟢 Low | Protection against API abuse |

---

## 🔵 POST-PILOT - Technical Debt

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 1 | **Refactor server.py (ISSUE-008)** | 5,917 line monolithic file | Rapid development, no time to split | Split into modular routers (auth, leagues, auctions, etc.) | 🟡 Medium | Maintainability, easier debugging |
| 2 | **Fixture Import Logic (ISSUE-009)** | Fuzzy name matching for fixture imports | Legacy implementation | Use `externalId` instead of name matching | 🟡 Medium | More reliable fixture imports |
| 3 | **Consolidate Socket Events (Phase 4)** | Two events per bid (`bid_update` + `bid_placed`) | Historical design | Merge into single `bid_committed` event | 🟡 Medium | Simpler client code, less state churn |
| 4 | **Socket.IO Bidding (Phase 5)** | HTTP POST for bids adds latency on mobile | Current architecture uses REST for bids | Use Socket.IO emit with ack for bidding | 🔴 Higher | Faster mobile bidding, fewer failure modes |

---

## 🔵 POST-PILOT - New Features

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 5 | **Manual Score Entry (ISSUE-001)** | No UI for manual score updates | Backend exists, frontend not built | Build score entry UI in CompetitionDashboard | 🟢 Low | Commissioners can fix scores without CSV |
| 6 | **Auction History (ISSUE-011)** | Can't review bid history after auction | Feature not implemented | Add history tab showing all bids, prices, winners | 🟢 Low | Post-auction review capability |
| 7 | **Custom Scoring (ISSUE-010)** | All leagues use same scoring rules | Hardcoded scoring | Add commissioner UI to customize points | 🟡 Medium | Flexibility for different tournaments |
| 8 | **Email Notifications (ISSUE-012)** | Users must manually check app | No email integration | Integrate SendGrid for invites, reminders, results | 🟡 Medium | Better user engagement |
| 9 | **Payment Integration** | No entry fees or charity donations | Feature not built | Stripe Connect integration (see PAYMENT_INTEGRATION_PLAN.md) | 🟡 Medium | Revenue capability, charity support |

---

## 🔵 POST-PILOT - Infrastructure

| # | Issue | Summary | Cause | Fix | Risk | Benefit |
|---|-------|---------|-------|-----|------|---------|
| 10 | **Analytics (ISSUE-013)** | No visibility into user behavior | Not implemented | Add Google Analytics | 🟢 Low | Usage insights |
| 11 | **Database Backups (ISSUE-014)** | Risk of data loss | No automated backups | Configure MongoDB Atlas daily backups | 🟢 Low | Data protection |
| 12 | **ESLint Warning (ISSUE-004)** | Build output cluttered with warnings | Missing ESLint rule config | Add rule to eslintrc or remove disable comments | 🟢 Low | Cleaner builds |
| 13 | **Cricket Errors (ISSUE-007)** | Generic error messages for cricket | Insufficient error handling | Add specific error messages | 🟢 Low | Better user feedback |
| 14 | **LeagueDetail Scrolling (ISSUE-005)** | Excessive scrolling on mobile | Long page design | Add collapsible sections or tabs | 🟢 Low | Better mobile UX |
| 15 | **"Complete Lot" Button (ISSUE-006)** | Button may be redundant | Added for now-fixed bug | Monitor usage, remove if unused | 🟢 Low | Cleaner UI |

---

## ✅ RECENTLY RESOLVED (Dec 2025)

| # | Issue | Summary | Solution | Date |
|---|-------|---------|----------|------|
| 1 | **Debug report incomplete** | Debug report only captured client-side data, couldn't diagnose server issues | Enhanced to capture all 15 socket events + fetch server-side auction state via `/api/debug/auction-state/{id}` | Dec 19 |
| 2 | Self-outbid | Users could increase their own winning bid | Backend validation + input reset on rejection | Dec 13 |
| 3 | Bid lag Phase 1 | 2 HTTP GETs per bid per client causing lag | Removed loadAuction/loadClubs from bid_placed | Dec 13 |
| 4 | 500 on first bid | Server error on initial bid | Fixed Pydantic serialization, None handling | Dec 12 |
| 5 | Frozen on delete | Screen froze when auction deleted | Added auction_deleted socket event | Dec 12 |
| 6 | Horizontal scroll | Mobile auction room had horizontal scroll | Fixed responsive layout | Dec 12 |
| 7 | Equal bid accepted | Bids equal to current were accepted | Changed to require bid > current | Dec 12 |
| 8 | Multi-pod Socket.IO | Socket.IO didn't work across pods | Configured Redis Cloud pub/sub | Dec 8 |
| 9 | Production outage | 520 error, service unavailable | Emergent platform issue - resolved after redeploy | Dec 13 |

---

## 📊 QUICK STATS

| Category | Count |
|----------|-------|
| 🔴 Immediate (Ready to Fix) | 1 |
| 🟡 Awaiting Info | 3 |
| 🟠 Medium Priority - Technical | 5 |
| 🟠 Medium Priority - UI/UX | 5 |
| 🟠 Medium Priority - Config | 2 |
| 🔵 Post-Pilot - Technical Debt | 4 |
| 🔵 Post-Pilot - Features | 5 |
| 🔵 Post-Pilot - Infrastructure | 6 |
| ✅ Recently Resolved | 9 |

---

## 📁 Related Documentation

| Document | Purpose |
|----------|---------|
| `/app/OUTSTANDING_ISSUES.md` | Detailed issue descriptions |
| `/app/UI_UX_AUDIT_REPORT.md` | Full UI/UX review |
| `/app/PRODUCTION_ENVIRONMENT_STATUS.md` | Current production state |
| `/app/PAYMENT_INTEGRATION_PLAN.md` | Post-pilot payment feature |
| `/app/MIGRATION_PLAN.md` | Contingency - move off Emergent |
| `/app/AGENT_ONBOARDING_CHECKLIST.md` | For new developers |

---

**Document Version:** 1.1  
**Last Updated:** December 19, 2025
