# Master TODO List - Sport X Platform

**Last Updated:** December 13, 2025 (Evening)  
**Purpose:** Single source of truth for all work items, organized by priority and status

---

## Quick Stats

| Category | Count |
|----------|-------|
| 🔴 Immediate (Ready to Fix) | 1 |
| 🟡 Awaiting Info | 3 |
| 🟠 Medium Priority | 8 |
| 🔵 Post-Pilot | 8 |
| ✅ Recently Resolved | 8 |

---

## 🔴 IMMEDIATE - Ready to Implement

These items have clear solutions and can be implemented now:

| # | Item | Type | Effort | Risk | Notes |
|---|------|------|--------|------|-------|
| 1 | **Remove `loadAuction()` from `onSold` handler** | Bug Fix | 30 min | 🟢 Low | Root cause of ISSUE-016 (roster not updating). Same pattern as Phase 1 bid fix. |

---

## 🟡 AWAITING INFO - Need Clarification

These items need more detail from user testing before we can proceed:

| # | Item | Type | Source | Questions Pending |
|---|------|------|--------|-------------------|
| 1 | **"Couldn't place a bid"** (ISSUE-019) | Bug? | Ash friends test 2 | Was button disabled? Error message? Budget remaining? |
| 2 | **"United offered 2 times"** (ISSUE-020) | Bug or Expected? | Ash friends test 2 | Did team go unsold first? Was there "Re-offering" toast? |
| 3 | **"Roster lagged in 2 places"** (ISSUE-021) | Bug | Ash friends test 2 | Likely same as ISSUE-016 - need confirmation |

---

## 🟠 MEDIUM PRIORITY - Address Soon

### Technical / Bug Fixes

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 1 | Team selection auto-filter | ISSUE-018 | 2 hrs | Auto-filter based on competitionCode - DESIGN DECISION NEEDED |
| 2 | Backend: Remove diagnostic DB reads | ISSUE-017 Phase 2 | 30 min | Performance improvement |
| 3 | Backend: Use `findOneAndUpdate` | ISSUE-017 Phase 3 | 1 hr | Eliminate extra DB read |
| 4 | Commissioner authorization checks | ISSUE-002 | 2 hrs | TODO comments in server.py |
| 5 | Verify "Unknown" manager names | ISSUE-022 | 1 hr | Check if still occurring in production |

### UI/UX Improvements (from Audit)

| # | Item | Page | Effort | Priority |
|---|------|------|--------|----------|
| 6 | Demote "Explore" button to text link | Home | 30 min | Medium - reclaims mobile space |
| 7 | Add bidder status indicator | AuctionRoom | 2 hrs | High - "YOU'RE WINNING" / "OUTBID" |
| 8 | Add team count preview in create modal | CreateLeague | 1 hr | High - "20 PL teams will be included" |
| 9 | Show "Current bid: £Xm" above input | AuctionRoom | 30 min | Medium - clarity |
| 10 | Make tabs sticky on mobile | Dashboard | 1 hr | Medium |

### Configuration

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 11 | Configure Sentry | ISSUE-003 | 30 min | Code ready - need DSN from user |
| 12 | Enable rate limiting | - | 10 min | Config change - ENABLE_RATE_LIMITING=true |

---

## 🔵 POST-PILOT - Future Work

### Technical Debt

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 1 | Refactor server.py monolith | ISSUE-008 | 8 hrs | Split into routers |
| 2 | Refactor fixture import logic | ISSUE-009 | 4 hrs | Use externalId |
| 3 | Consolidate socket events | ISSUE-017 Phase 4 | 2 hrs | Single bid_committed event |
| 4 | Socket.IO for bid submission | ISSUE-017 Phase 5 | 4 hrs | Optional - higher risk |

### New Features

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 5 | Manual score entry UI | ISSUE-001 | 4 hrs | Backend exists |
| 6 | Auction history tab | ISSUE-011 | 4 hrs | Post-auction review |
| 7 | User-configurable scoring | ISSUE-010 | 4 hrs | Commissioner customization |
| 8 | Email notifications | ISSUE-012 | 6 hrs | SendGrid integration |

### Infrastructure

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 9 | Analytics integration | ISSUE-013 | 3 hrs | Google Analytics |
| 10 | Database backups | ISSUE-014 | 3 hrs | Daily automated |
| 11 | Payment integration | - | 25 hrs | See PAYMENT_INTEGRATION_PLAN.md |

### Nice to Have

| # | Item | Issue ID | Effort | Notes |
|---|------|----------|--------|-------|
| 12 | ESLint warning fix | ISSUE-004 | 30 min | Cosmetic |
| 13 | Cricket error messaging | ISSUE-007 | 2 hrs | Better error messages |
| 14 | Remove "Complete Lot" button | ISSUE-006 | 1 hr | If unused after testing |
| 15 | Mobile LeagueDetail scrolling | ISSUE-005 | 3 hrs | Collapsible sections |

---

## ✅ RECENTLY RESOLVED (Dec 2025)

| Date | Item | Solution |
|------|------|----------|
| Dec 13 | Self-outbid prevention | Backend validation + input reset |
| Dec 13 | Bid lag Phase 1 | Removed HTTP GETs from bid_placed handler |
| Dec 12 | 500 error on first bid | Pydantic serialization fix |
| Dec 12 | Screen freeze on auction delete | Socket.IO auction_deleted event |
| Dec 12 | Mobile horizontal scrolling | AuctionRoom responsive fix |
| Dec 12 | Bid validation (equal bids) | Require bid > current |
| Dec 8 | Socket.IO multi-pod | Redis Cloud configuration |

---

## 📋 MONITORING - Watch During Testing

| Item | What to Watch For |
|------|-------------------|
| Production stability | 520 errors, service unavailable |
| Self-outbid fix | Toast appears, input resets correctly |
| Bid lag improvement | Check console for tapToAckMs, serverLatencyMs |
| Roster updates | Does roster display update after winning? |
| "Complete Lot" button | Is it being used? If not, remove |

---

## 🎯 RECOMMENDED NEXT ACTIONS

**If no new issues reported:**
1. Implement ISSUE-016 fix (remove loadAuction from onSold) - 30 min
2. Deploy and test with users
3. Review performance metrics from console logs
4. Make design decision on team selection UX

**If waiting for more info:**
1. Focus on UI/UX quick wins (Explore button, bidder status indicator)
2. Configure Sentry for better error visibility

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

**Document Version:** 1.0  
**Last Updated:** December 13, 2025
