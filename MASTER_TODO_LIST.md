# Master TODO List - Sport X Platform

**Last Updated:** January 10, 2026  
**Purpose:** Single source of truth for all work items - issues, bugs, features, and technical debt

---

## 🔴 HIGH PRIORITY - Redis Connection Limit Issue

**Status:** UPGRADED - Partial Improvement  
**Last Updated:** January 12, 2026

### Problem Summary
~~During 20-league stress tests, Redis Cloud sent alerts that connections reached **86% of limit**.~~ 

**UPDATE:** Upgraded to Redis Essentials (256 connections, ~£5/month). Connection exhaustion resolved but Socket.IO errors persist at scale.

### Post-Upgrade Test Results (Jan 12, 2026)

| Test | Scale | p50 | p99 | Bid Success | Socket Errors |
|------|-------|-----|-----|-------------|---------------|
| 1 | 20 leagues | 768ms | 6,665ms | 75.2% | Many |
| 2 | 2 leagues | 709ms | 2,968ms | 100% | Some |
| 3 (redeploy) | 2 leagues | 688ms | 1,517ms | 100% | Some |
| 4 (redeploy) | 20 leagues | 800ms | 3,121ms | 76.4% | Many |

### Key Findings Post-Upgrade

| Finding | Status |
|---------|--------|
| Connection exhaustion | ✅ Fixed (no more 86% alerts) |
| Small scale success rate | ✅ Fixed (100% at 2 leagues) |
| Large scale success rate | ❌ Still 75-76% at 20 leagues |
| Socket.IO errors at scale | ❌ Still occurring |
| Baseline latency (p50) | ❌ Still ~700-800ms (MongoDB issue) |

### Remaining Issues at Scale (20 leagues)

1. **Socket.IO namespace failures** - "One or more namespaces failed to connect"
2. **Poll/semaphore timeouts** - "The semaphore timeout period has expired"
3. **High p99 latency** - 3-6 seconds causing bid timeouts

### Revised Capacity Estimates

| Scale | Success Rate | p99 Latency | Verdict |
|-------|-------------|-------------|---------|
| 2-5 leagues | 100% | ~1.5-2s | ✅ Acceptable |
| 10 leagues | ~90% | ~2-3s | ⚠️ Marginal |
| 20 leagues | ~75% | ~3-6s | ❌ Not acceptable |
| 50 leagues (pilot) | Unknown | Unknown | ❌ Likely worse |

### Options to Improve Scale Performance

| Option | Effort | Expected Impact | Risk |
|--------|--------|-----------------|------|
| **MongoDB upgrade (M10)** | Medium | Reduce p50 700ms→100ms, fewer timeouts | Low |
| **Increase server pods** | Low | Better load distribution | Low |
| **Socket.IO tuning** | Medium | Reduce connection failures | Medium |
| **Connection pooling (server)** | Medium | More efficient DB/Redis use | Medium |
| **Rate limit bid frequency** | Low | Reduce server load | Low |

### Next Steps
1. ✅ Redis upgrade complete
2. ⏳ Contact Emergent re: MongoDB + pod scaling
3. ⏳ Investigate Socket.IO configuration for scale
4. ⏳ Consider MongoDB upgrade if Emergent can't help

---

## 🔴 HIGH PRIORITY - MongoDB Performance Investigation

**Status:** AWAITING EMERGENT RESPONSE  
**Last Updated:** January 11, 2026

### Problem Summary
Production bid latency is ~700-1100ms avg vs ~360ms in preview environment. Root cause identified as **network latency to Emergent's shared MongoDB Atlas cluster**.

### Key Findings

| Environment | MongoDB Location | Min Latency | Avg Latency |
|-------------|------------------|-------------|-------------|
| Preview | `localhost:27017` | ~306ms | ~360ms |
| Production | `customer-apps.oxfwhh.mongodb.net` (shared Atlas) | ~640ms | ~700-1100ms |

**The ~300-600ms difference is network round-trip to Emergent's shared MongoDB Atlas cluster.**

### Root Cause Analysis (Jan 11, 2026)
- Emergent uses a **shared MongoDB Atlas cluster** (`customer-apps.oxfwhh.mongodb.net`) for all customers
- Performance depends on "noisy neighbors" and Emergent's Atlas configuration
- Region unknown - may be different from where production app runs
- Cannot optimize further from application side - infrastructure is the bottleneck

### Attempted Fixes (Jan 10, 2026)

| Fix | Result | Notes |
|-----|--------|-------|
| Remove diagnostic query | ❌ Made worse in prod | Works in preview |
| Remove duplicate league query | ❌ Made worse in prod | Works in preview |
| Increase maxPoolSize (5→50) | ❌ No improvement / worse | Pool size not the bottleneck |
| Both fixes together in preview | ✅ 50% improvement | Confirms fixes work, prod infra is issue |

### Decision: Options to Pursue

| Option | Effort | Impact | Risk | Recommendation |
|--------|--------|--------|------|----------------|
| **1. Contact Emergent Support** | Low | Unknown | Low | ✅ DO FIRST |
| **2. Bring Your Own MongoDB** | Medium (2-4 hrs) | High | Low | ✅ BACKUP PLAN |
| **3. Aggressive Caching** | Medium | Medium | High | ⚠️ AVOID - complex |
| **4. Migrate off Emergent** | High (1-2 weeks) | High | Medium | ❌ LAST RESORT |

### Option 1: Contact Emergent Support (DO FIRST)

**Send this to Emergent support (Discord/Email):**

```
Subject: Infrastructure Support Request - Real-Time Auction Platform Performance

Hi Emergent team,

We're preparing for a 400-user pilot of our real-time auction platform and have been 
running stress tests to validate infrastructure readiness. We've identified performance 
bottlenecks that we'd like your help to resolve.

CURRENT SETUP:
- MongoDB: customer-apps.oxfwhh.mongodb.net (Emergent-managed)
- Redis: Redis Cloud Essentials (256 connections) - our account
- Multi-pod deployment with Socket.IO

STRESS TEST RESULTS (January 12, 2026):

| Scale | Bid Success | p50 Latency | p99 Latency |
|-------|-------------|-------------|-------------|
| 2 leagues (16 users) | 100% | 688ms | 1,517ms |
| 20 leagues (160 users) | 76% | 800ms | 3,121ms |

KEY FINDING:
When testing in preview (localhost MongoDB), we achieved:
- p50: 357ms
- p99: 416ms
- 100% success rate

This suggests the ~350ms latency difference is due to network distance to the 
shared MongoDB cluster. Our real-time bidding requires lower latency for 
acceptable user experience.

QUESTIONS:
1. What region is the MongoDB cluster (customer-apps.oxfwhh.mongodb.net) hosted in?
2. What region(s) are our application pods deployed to?
3. Is it possible to get a dedicated MongoDB instance, or placement in the same 
   region as our app pods?
4. How many pods are currently allocated to our deployment?
5. Can we increase pod count for better load distribution?

CONTEXT:
- We've already upgraded Redis from free (30 connections) to Essentials (256) 
  which improved connection stability
- Our target is 50 concurrent leagues (400 users) at 99%+ bid success rate
- Current architecture requires 7-8 DB queries per bid

We have detailed stress test reports available if helpful. Please let us know 
what options are available to improve our production performance.

Thanks,
[Your name]
```

**Contact:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh
- Include Job ID from chat interface

### Option 2: Bring Your Own MongoDB (BACKUP PLAN)

If Emergent can't help, set up your own Atlas cluster:

**Steps:**
1. Create MongoDB Atlas account at mongodb.com
2. Create M10 cluster (~$60/month) in **same region as Emergent production app**
3. Export data: `mongodump --uri="<emergent-mongo-url>"`
4. Import data: `mongorestore --uri="<your-new-mongo-url>"`
5. Update `MONGO_URL` environment variable in Emergent production
6. Redeploy from Emergent - everything else stays the same

**Expected improvement:**
- p50: 821ms → ~100-200ms
- p99: 5254ms → ~500ms
- Bid success: 85% → 99%+

**Pros:**
- Still manage/deploy from Emergent
- Full control over DB region, tier, configuration
- Dedicated resources (no noisy neighbors)

**Cons:**
- Additional cost (~$60/month)
- You're responsible for backups
- Migration effort (2-4 hours)

### Test Results Archive

| Date | Config | Environment | p50 | p95 | p99 | Success |
|------|--------|-------------|-----|-----|-----|---------|
| Jan 10 | 5 leagues, 6 users | Preview (with fixes) | 357ms | 407ms | 416ms | 100% |
| Jan 10 | 5 leagues, 6 users | Production (baseline) | 713ms | 818ms | 961ms | 100% |
| Jan 10 | 20 leagues, 8 users | Production | 809ms | 1479ms | 2079ms | 100% |
| Jan 10 | 20 leagues, 8 users | Production (pool=50) | - | - | - | worse |
| Jan 10 | 20 leagues, 8 users | Production (pool=5 reset) | 821ms | 2732ms | 5254ms | 85% |

### Files Created
- `/app/tests/multi_league_stress_test.py` - Automated stress test script
- `/app/tests/README.md` - Test instructions
- Results output: `stress_test_results_YYYYMMDD_HHMMSS.json` and `.txt`

### Known Script Limitations (Jan 11, 2026)

| Issue | Cause | Impact |
|-------|-------|--------|
| £0M spent displayed | Wrong field name or server doesn't populate `totalSpent` | Metric incorrect, not affecting test validity |
| Excessive "roster full" rejections | Script polls HTTP, lags behind real-time Socket.IO state | Expected behavior for polling-based test |
| Incomplete sales count | Race condition - exit loop before all sales propagate | May under-count, latency metrics still valid |

**Note:** Latency measurements are valid. Auxiliary metrics (spend, exact lot counts) may be slightly off due to polling vs real-time state. Revisit if precise stats needed.

### Next Steps
1. ⏳ Contact Emergent support with performance data
2. ⏳ Wait for response (1 week max)
3. If no help → Proceed with Option 2 (Bring Your Own MongoDB)

---

## 🟡 MEDIUM PRIORITY - Database Call Optimization

**Status:** PLANNED - After hybrid infrastructure test  
**Last Updated:** January 12, 2026

### Problem Summary
Each bid requires 7-8 database calls. With remote MongoDB (~100ms/call), this adds ~700ms latency per bid. Even with same-region MongoDB (~20ms/call), reducing calls would improve performance.

### Current DB Calls in `place_bid` Endpoint

| # | Call | Purpose | Can Optimize? |
|---|------|---------|---------------|
| 1 | `db.auctions.find_one()` | Get auction state | ✅ Required |
| 2 | `db.users.find_one()` | Get user name/email | ⚠️ Could cache per auction session |
| 3 | `db.leagues.find_one()` | Get league settings | ❌ **Unnecessary** - settings never change during auction |
| 4 | `db.league_participants.find_one()` | Check budget & roster | ✅ Required (budget changes each bid) |
| 5 | `db.bids.insert_one()` | Save the bid | ✅ Required |
| 6 | `db.auctions.update_one()` | Update current bid | ⚠️ Combine with #7 |
| 7 | `db.auctions.find_one()` | Get updated sequence | ❌ **Redundant** - use find_one_and_update |
| 8 | `db.auctions.update_one()` | Anti-snipe timer | ⚠️ Conditional, could combine |

### Optimization Opportunities

**Quick Win #1: Combine calls 6+7 (Low Risk)**
```python
# Current: 2 calls
await db.auctions.update_one({"id": auction_id}, {"$set": {...}, "$inc": {"bidSequence": 1}})
updated_auction = await db.auctions.find_one({"id": auction_id}, {"bidSequence": 1})

# Optimized: 1 call
from pymongo import ReturnDocument
updated_auction = await db.auctions.find_one_and_update(
    {"id": auction_id},
    {"$set": {...}, "$inc": {"bidSequence": 1}},
    return_document=ReturnDocument.AFTER,
    projection={"bidSequence": 1, "_id": 0}
)
```
**Saves:** 1 DB call (~100ms with remote MongoDB)

**Quick Win #2: Remove league query (Low Risk)**

League settings (timer, antisnipe, budget, roster slots) **never change once auction starts**. The auction document already contains `leagueId` and should contain cached league settings.

```python
# Current: Fetches league every bid
league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
max_slots = league.get("clubSlots", 3)

# Optimized: Use auction's cached settings (set at auction start)
max_slots = auction.get("clubSlots", 3)  # Already in auction doc
```
**Saves:** 1 DB call (~100ms with remote MongoDB)

**Requires:** Ensure auction document includes `clubSlots`, `timerSeconds`, `antiSnipeSeconds`, `budget` when auction is created.

**Medium Win #3: Cache user info per auction session (Medium Risk)**

User name/email don't change during an auction. Could cache on first bid.

```python
# Cache key: f"auction:{auction_id}:user:{user_id}"
# Store: {"name": "...", "email": "..."}
# TTL: Duration of auction
```
**Saves:** 1 DB call per subsequent bid (~100ms each)
**Risk:** Cache invalidation if user updates profile mid-auction (unlikely)

### Impact Analysis

| Scenario | DB Calls | Remote MongoDB | Same-Region MongoDB |
|----------|----------|----------------|---------------------|
| Current | 7-8 | ~700-800ms | ~140-160ms |
| Quick wins only (#1, #2) | 5-6 | ~500-600ms | ~100-120ms |
| All optimizations | 3-4 | ~300-400ms | ~60-80ms |

### Implementation Priority

| Optimization | Effort | Risk | Latency Saved | Priority |
|--------------|--------|------|---------------|----------|
| #1: Combine update+find | 30 min | 🟢 Low | ~100ms | ✅ Do first |
| #2: Remove league query | 1-2 hrs | 🟢 Low | ~100ms | ✅ Do second |
| #3: Cache user info | 2-3 hrs | 🟡 Medium | ~100ms/bid | ⏳ Later |

### Prerequisites

Before implementing #2 (remove league query), verify auction document contains:
- [ ] `clubSlots` - roster limit per user
- [ ] `timerSeconds` - lot timer duration
- [ ] `antiSnipeSeconds` - anti-snipe extension
- [ ] `budget` - starting budget per user

### When to Implement

1. **Test hybrid infrastructure first** - May reduce latency enough without code changes
2. **If hybrid achieves 93%+ success** - Consider optimizations for further improvement
3. **If hybrid <90% success** - Implement quick wins before full migration decision

### Files to Modify

- `/app/backend/server.py` - `place_bid` function (line ~4720)
- `/app/backend/server.py` - `start_auction` function (ensure settings cached)

---

## 🟠 MEDIUM PRIORITY - Schema Change Management

**Status:** PROCESS TO IMPLEMENT  
**Last Updated:** January 11, 2026

### Problem
MongoDB is schema-less, which means:
- Missing required fields → silent failures, not errors
- Renamed fields → old documents have wrong field names
- Data type changes → runtime errors on old documents

Without a formal process, schema changes can cause subtle bugs that are hard to diagnose.

### Current State
- One migration function exists: `migrate_team_names()` (runs on startup)
- No formal tracking of schema changes
- No validation that documents have required fields

### Recommended Process

**For every code change that affects database structure:**

1. **Document the change** in CHANGELOG.md:
   ```
   ## Jan 15, 2026
   - SCHEMA: Added `displayName` field to `users` collection (optional, defaults to email prefix)
   - SCHEMA: Renamed `clubId` → `teamId` in `bids` collection (MIGRATION REQUIRED)
   ```

2. **Determine if migration is needed:**
   | Change Type | Migration Needed? |
   |-------------|-------------------|
   | Add optional field | ❌ No |
   | Add required field | ✅ Yes - backfill existing docs |
   | Rename field | ✅ Yes - update existing docs |
   | Change data type | ✅ Yes - convert existing docs |
   | Add index | ⚠️ Maybe - can be slow on large collections |
   | Remove field | ❌ No (but clean up old data eventually) |

3. **If migration needed, write a migration function:**
   ```python
   async def migrate_YYYYMMDD_description():
       """Migration: Rename clubId to teamId in bids collection"""
       result = await db.bids.update_many(
           {"clubId": {"$exists": True}, "teamId": {"$exists": False}},
           [{"$set": {"teamId": "$clubId"}}, {"$unset": "clubId"}]
       )
       logger.info(f"Migrated {result.modified_count} bids")
   ```

4. **Test migration on copy of production data before deploying**

### Schema Change Log

| Date | Collection | Change | Migration | Status |
|------|------------|--------|-----------|--------|
| Dec 2025 | `assets` | Added `teamName` field | `migrate_team_names()` | ✅ Done |
| - | - | - | - | - |

*(Add new schema changes here)*

### Future Improvements (Post-Pilot)

| Improvement | Effort | Benefit |
|-------------|--------|---------|
| Add `schemaVersion` field to all documents | Medium | Track which version each doc is |
| Startup validation of required fields | Medium | Catch missing fields early |
| Migration runner with version tracking | High | Automated, safe migrations |

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

## 🔴 MIGRATION PRE-REQUISITES (Confirm Before Migration)

**Status:** AWAITING USER INPUT  
**Priority:** HIGH - Required before any migration work proceeds  
**Reason:** Previous agent assumptions led to unnecessary work (e.g., MongoDB Atlas Cluster0 setup). Migration plan accuracy depends on confirmed details.

| # | Item | What's Needed | Status |
|---|------|---------------|--------|
| 1 | **Redis Cloud Account** | Confirm connection string/URL from your Redis Cloud dashboard | ❓ Pending |
| 2 | **MongoDB Atlas Cluster0** | Clarify: Did you create this, or was it set up by an agent? Can it be deleted? | ❓ Pending |
| 3 | **Football-Data.org API** | Confirm API tier and rate limits (free tier may not support 250+ users) | ❓ Pending |
| 4 | **Custom Domain** | Confirm if domain purchased for production (e.g., sportx.app) | ❓ Pending |
| 5 | **Data Migration Approach** | Decision: Fresh start (re-seed) or export/import existing data? | ❓ Pending |
| 6 | **Staging Environment** | Decision: Separate Railway project for staging, or single project? | ❓ Pending |

**Why This Matters:**
- Agent cannot access external dashboards (Railway, Redis Cloud, Atlas, Football-Data.org)
- Previous assumptions about MongoDB configuration were incorrect
- Migration plan must be based on confirmed facts, not assumptions

**Action:** User to provide details when ready. Agent will update MIGRATION_PLAN.md accordingly.

---

## 🔵 POST-PILOT - Technical Debt

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 0 | **STRESS-TEST** | **Competitive Bidding Test Mode** - Current stress test only tests "happy path" (one bid per lot) | Anti-snipe and bidding wars not tested | Add competitive bidding mode with multiple users bidding on same lot | 🟡 Medium | Realistic load testing for pilot |
| 1 | **ISSUE-008** | **Refactor server.py** - 5,917 line monolithic file | Rapid development, no time to split | Split into modular routers (auth, leagues, auctions, fixtures, scoring, assets) | 🟡 Medium | Maintainability, easier debugging |
| 2 | **ISSUE-009** | **Fixture Import Logic** - Fuzzy name matching for fixture imports | Legacy implementation | Use `externalId` instead of name matching | 🟡 Medium | More reliable fixture imports |
| 3 | **ISSUE-017 Phase 4** | **Consolidate Socket Events** - Two events per bid (`bid_update` + `bid_placed`) | Historical design | Merge into single `bid_committed` event | 🟡 Medium | Simpler client code, less state churn |
| 4 | **ISSUE-017 Phase 5** | **Socket.IO Bidding** - HTTP POST for bids adds latency on mobile | Current architecture uses REST for bids | Use Socket.IO emit with ack for bidding | 🔴 Higher | Faster mobile bidding, fewer failure modes |

---

## 🔵 POST-PILOT - New Features

| # | Issue ID | Summary | Cause | Fix | Risk | Benefit |
|---|----------|---------|-------|-----|------|---------|
| 5 | **ISSUE-026** | **Scalable Fixture Template Management** - Updating CSV templates requires code deploy | Templates are static files served via hardcoded endpoints; frontend references specific filenames | Build admin UI for commissioners to upload/manage fixture templates per league, OR store templates in database with dynamic serving | 🟢 Low | No redeploy needed to update fixtures; scales to multiple leagues; reduces cost/friction of tournament updates |
| 6 | **ISSUE-001** | **Manual Score Entry UI** - No UI for manual score updates | Backend exists, frontend not built | Build score entry UI in CompetitionDashboard | 🟢 Low | Commissioners can fix scores without CSV |
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

## ❌ FAILED FIX ATTEMPTS & AGENT ERRORS

### MongoDB Atlas Setup (Dec 2025) - UNNECESSARY WORK
| Item | Details |
|------|---------|
| **What happened** | Agent set up external MongoDB Atlas cluster for production |
| **Why it was wrong** | Emergent provides managed MongoDB automatically - no external setup needed |
| **Impact** | User received confusing "inactive cluster" warnings, wasted time investigating |
| **Lesson** | **Do not set up external infrastructure without verifying it's actually needed** |

### Code Fix Failures (Dec 19, 2025)

| Issue | Attempted Fix | Result | Status |
|-------|---------------|--------|--------|
| **ISSUE-016** | Remove `loadAuction()` from `onSold` handler | Broke countdown display between lots | REVERTED |
| ~~**ISSUE-018**~~ | ~~Auto-filter `loadAssets()` by competition~~ | ~~Multiple attempts failed~~ | ✅ RESOLVED Dec 20 - Backend fix in `get_league_assets()` |

**Lessons:**
- Agent made "incremental guesses" instead of thorough analysis
- Agent repeatedly ignored instructions to get approval before code changes
- Agent didn't check downstream dependencies before implementing fixes
- Agent set up unnecessary external services without understanding platform capabilities
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
