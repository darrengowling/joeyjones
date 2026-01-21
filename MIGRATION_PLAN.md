# Migration Plan: Emergent → Railway (EU-West)

**Created:** December 13, 2025  
**Last Updated:** January 22, 2026  
**Version:** 4.3  
**Status:** READY TO EXECUTE  
**Target Platform:** Railway (EU-West/London)  
**Reason:** UK pilot users face ~700ms latency due to US-hosted Emergent

---

## Executive Summary

| Item | Details |
|------|---------|
| **Problem** | UK users experience ~700ms latency (US hosting) |
| **Solution** | Railway EU-West + MongoDB Atlas europe-west2 |
| **Expected Result** | p50 latency ~100-200ms (vs current 700ms) |
| **Monthly Cost (Phased)** | Month 1: **£20-29** (M0/M2) → Month 2+: **£65** (M10) |
| **Timeline** | 1-2 hours verification + 2-3 days migration |

**Key Decision:** Phase 0 diagnostic test determines if M10 (£45/mo) is needed or if M0/M2 (£0-9/mo) is sufficient

---

## Why Migration is Required

### Root Cause Analysis (January 2026)

**Stress testing confirmed the issue is infrastructure, not code:**

| Factor | Current (Emergent) | After Migration (Railway EU) |
|--------|-------------------|------------------------------|
| App server location | US | EU-West (London) |
| MongoDB location | US (shared cluster) | EU (your dedicated cluster) |
| Network round-trip to UK | ~100ms per call | ~10-20ms per call |
| DB calls per bid | 6-7 | 6-7 (same) |
| **Total latency per bid** | **~700ms** | **~100-200ms** |

### Hybrid Approach Ruled Out

We considered keeping Emergent + your own MongoDB, but:
- ❌ App server would still be in US
- ❌ UK users would still have ~100ms per request to US
- ❌ Only saves £15/month vs full migration
- ✅ **Full migration is the only solution for UK latency**

---

## Phase 0: Root Cause Verification

### ⚠️ LIMITATION DISCOVERED

**Phase 0 as originally designed is NOT EXECUTABLE.**

Emergent's MongoDB runs on `localhost:27017` internally and is not accessible from external services. Railway cannot connect to Emergent's database to isolate the geography variable.

**Original goal:** Deploy Railway EU → Emergent MongoDB (US) to test if latency is geography or database tier.  
**Blocker:** Emergent MongoDB is not externally accessible.

### Revised Options

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A: Skip Phase 0** | Proceed with M2, upgrade to M10 if alerts trigger | Simple, stress tests already show 700ms | Doesn't isolate root cause |
| **B: Modified Phase 0** | Create Atlas M0 (free) in US-East, test Railway EU → US Atlas | Tests geography hypothesis | Extra setup, not exact replica |
| **C: Start with M10** | Accept £45/mo for guaranteed performance | No risk, best backups | Higher cost if M2 would suffice |

### Recommendation

**Option A (Skip Phase 0)** is pragmatic given:
- Stress tests already confirmed 700ms latency
- Phased cost model (M2 → M10) manages cost risk
- Atlas alerts will trigger upgrade if M2 is insufficient
- £36/mo difference doesn't justify additional complexity

**If cost sensitivity is critical**, Option B can be attempted but adds 1-2 hours setup for inconclusive results (Atlas M0 US ≠ Emergent's managed MongoDB).

---

### Original Phase 0 Design (FOR REFERENCE ONLY - NOT EXECUTABLE)

**Goal:** Prove whether 700ms latency is caused by geography or database tier before committing to M10 (£45/mo)

**Time Required:** 1-2 hours  
**Cost:** £0 (uses existing Emergent MongoDB)  
**Status:** ❌ BLOCKED - Emergent MongoDB not externally accessible

### Why This Matters

Your stress test showed 700ms p50 latency, but we don't know if it's:
- **Geography** (US→UK network hops) → M0/M2 sufficient in EU (save £36-45/mo)
- **Database throttling** (M0 shared CPU) → M10 required (£45/mo justified)
- **Combination** of both → M2 initially, upgrade to M10 later

**Cost impact:** £432-540/year difference

### Quick Diagnostic Test

**Deploy backend to Railway EU but keep using Emergent's M0 database temporarily**

#### Setup (30 mins)

1. **Create Railway account** (free trial)
2. **Deploy backend only:**
   - Connect your GitHub repo
   - Use existing environment variables
   - **Key:** Point `MONGO_URL` to Emergent's MongoDB (not new Atlas cluster yet)
   - Set `CORS_ORIGINS` to allow Railway domain
3. **Get Railway backend URL** (e.g., `https://sportx-backend-xxx.railway.app`)

#### Stress Test (30 mins)

1. **Update stress test to use Railway backend:**
   ```bash
   python /app/tests/multi_league_stress_test.py \
     --backend-url https://sportx-backend-xxx.railway.app \
     --num-leagues 20
   ```

2. **Compare results:**

| Current (Emergent US) | Railway EU + Emergent DB | Diagnosis |
|----------------------|--------------------------|-----------|
| 700ms p50 latency | **150-250ms** | ✅ Geography was the main issue → **M0/M2 sufficient** |
| 700ms p50 latency | **400-500ms** | ⚠️ Mixed (geography + DB) → **Start M2, upgrade to M10 if needed** |
| 700ms p50 latency | **650-700ms** | ❌ Database is throttling → **M10 required** |

#### Decision Point

**Based on test results:**

- **If latency drops to 150-250ms:** 
  - Proceed with M0 (free) or M2 (£9/mo)
  - Save £36-45/mo (£432-540/year)
  - Monitor Atlas metrics, upgrade later if needed

- **If latency drops to 400-500ms:**
  - Start with M2 (£9/mo)
  - Set alerts: CPU >70%, connections >400
  - Upgrade to M10 when adding 3rd-5th charity

- **If latency stays at 650-700ms:**
  - Proceed directly to M10 (£45/mo)
  - Database throttling confirmed

### After Verification

Once you know the root cause:
1. Delete the Railway test deployment
2. Proceed with full migration using appropriate MongoDB tier
3. Update cost breakdown in your plan

---

## Target Architecture

```
UK Users
    │
    ▼
Railway (EU-West/London)
├── Backend Service (FastAPI + Socket.IO)
├── Frontend Service (React static)
│
└── External Services
    ├── MongoDB Atlas M0/M2/M10 (europe-west2/London) ← YOUR ACCOUNT
    ├── Redis Cloud Essentials (256 conn) ← YOUR EXISTING ACCOUNT
    ├── Sentry (error tracking) ← CONFIGURED
    ├── Football-Data.org API
    └── Cricbuzz/RapidAPI
```

---

## Cost Breakdown (Phased Approach)

### Phase 1: Owen McVeigh Pilot Only (Weeks 1-2)

**Scenario:** Single charity, ~50 users, 1-2 active leagues

| Service | Tier | Monthly Cost | Notes |
|---------|------|--------------|-------|
| Railway | Starter | ~£15 | EU-West hosting |
| MongoDB Atlas | **M0 (free)** or **M2** | **£0-9** | Decision based on Phase 0 test |
| Redis Cloud | Essentials (256 conn) | ~£5 | Already upgraded |
| Sentry | Free | £0 | Error tracking |
| **Total** | | **£20-29/month** | |

**M0 vs M2 decision:**
- **If Phase 0 test shows <250ms:** Use M0 (free)
- **If Phase 0 test shows 400-500ms:** Use M2 (£9/mo)
- **If Phase 0 test shows >650ms:** Skip to M10

**Why M0/M2 might be sufficient:**
- Owen McVeigh = 50 users × 2 connections = 100 connections (M0 limit: 500)
- Single league = low concurrent DB operations
- No connection exhaustion risk
- Has basic backups (M2 only)

**Risks of M0/M2:**
- Shared CPU (possible throttling under load)
- 500 connection limit (could hit if Socket.IO reconnects frequently)
- No point-in-time restore (M0), limited backups (M2)

**Monitoring strategy:**
- Set Atlas alerts: CPU >70%, connections >400, query latency >200ms
- If any alert triggers → upgrade to M10

---

### Phase 2: Scaling to 5+ Charities (Week 3+)

**Scenario:** 5-10 charities, 250-500 users, 10-20 concurrent leagues

| Service | Tier | Monthly Cost | Notes |
|---------|------|--------------|-------|
| Railway | Starter | ~£15 | EU-West hosting |
| MongoDB Atlas | **M10 (europe-west2)** | **~£45** | Dedicated cluster |
| Redis Cloud | Essentials (256 conn) | ~£5 | Already upgraded |
| Sentry | Free | £0 | Error tracking |
| **Total** | | **~£65/month** | |

**When to upgrade from M0/M2 → M10:**

Upgrade triggers (any one):
- ✅ Adding 3rd charity
- ✅ Total users approaching 250
- ✅ Atlas CPU consistently >70%
- ✅ Connections approaching 400
- ✅ Query latency degrading (p50 >200ms)
- ✅ Any connection pool exhaustion errors

**Why M10 at scale:**
- 500 users × 2 connections = 1,000 connections (M0/M2 limit: 500)
- 10-20 concurrent auctions = high DB operation volume
- Dedicated CPU prevents throttling
- Point-in-time restore protects pilot data
- Performance insights for optimization

---

### Cost Comparison (First 3 Months)

| Month | Scenario | Tier | Cost |
|-------|----------|------|------|
| **Month 1** | Owen McVeigh only | M2 | **£24** |
| **Month 2** | Adding charities 2-3 | M2 → M10 | **£24** → **£65** |
| **Month 3+** | 5-10 charities | M10 | **£65** |

**Total first 3 months:** £153  
**vs M10 from day 1:** £195  
**Savings:** £42

**Non-financial benefit:** Validates M10 is actually needed before committing to £540/year

---

## Pre-Migration Requirements

### ✅ Already Done
- [x] Sentry configured (backend DSN active)
- [x] Redis Cloud upgraded to Essentials (256 connections)
- [x] Stress test script ready (`/app/tests/multi_league_stress_test.py`)
- [x] Environment variables documented

### ⏳ Do After Migration (But Before Pilot)
- [ ] **Auth hardening** - MUST complete before external pilot users
  - **Why delayed:** Stress testing requires programmatic token access (dev mode)
  - **Timeline:** Complete within 24-48hrs after migration validated
  - **Components:**
    - SendGrid/Resend for email delivery
    - Rate limiting (3 requests/hour/email)
    - Remove token from API response
  - **Blocker for:** Sending pilot invitations to real users
  - **See Phase 11 in checklist for detailed steps**

### ❓ Decisions Needed
- [ ] **Custom domain** - e.g., sportx.app (optional for pilot)
- [ ] **Data migration** - Fresh start vs export existing data?
- [ ] **MongoDB tier** - Will be decided after Phase 0 verification

---

## Expected Performance After Migration

| Scale | Current (US) | Expected (EU) | Target |
|-------|--------------|---------------|--------|
| p50 latency | 700ms | 100-200ms | ≤200ms ✅ |
| p99 latency | 2800ms | 500-1000ms | ≤1500ms ✅ |
| Bid success (20 leagues) | 71-76% | 95%+ | ≥95% ✅ |

---

## Dual Development Workflow (Post-Migration)

**Strategy:** Railway for production, Emergent for development sandbox

```
Emergent (sandbox)
    ↓ Test feature
sandbox-repo (GitHub)
    ↓ Create PR
production-repo (GitHub, main branch)
    ↓ Auto-deploy
Railway (production)
```

### Setup
1. Create two GitHub repos:
   - `sportx-production` → Connected to Railway (auto-deploy on `main`)
   - `sportx-sandbox` → Connected to Emergent

2. Configure Railway auto-deploy:
   - Railway Dashboard → Service Settings → Source
   - Connect `sportx-production` repo
   - Enable "Auto Deploy" on `main` branch
   - Verify GitHub webhook is active

---

## Railway Configuration

### Backend Service

**Start command:**
```bash
uvicorn server:socket_app --host 0.0.0.0 --port $PORT
```

**Health check:**
```
Path: /api/health
Expected: HTTP 200 with {"status":"healthy","database":"connected"}
```

**Important:** Set replicas to 1 initially (Socket.IO sticky sessions requirement)

**Environment variables:**
```bash
# Database (YOUR Atlas cluster - EU region)
# Note: Add ?maxPoolSize=50 for production load
MONGO_URL=mongodb+srv://user:pass@YOUR-cluster.europe-west2.mongodb.net/sport_x?maxPoolSize=50
DB_NAME=sport_x_production

# Auth
JWT_SECRET=your-secure-secret-min-32-chars

# Redis (YOUR existing Redis Cloud - verify SSL format)
# Check format: redis:// vs rediss:// (SSL) vs redis://...?ssl=true
REDIS_URL=redis://user:pass@your-redis-cloud-host:port

# APIs
FOOTBALL_DATA_TOKEN=your-token
RAPIDAPI_KEY=your-key

# Sentry (already configured)
SENTRY_DSN=https://618d64387dd9bd3a8748f3671b530981@o4510411309907968.ingest.de.sentry.io/4510734931722320

# Production settings (update after frontend deployed)
CORS_ORIGINS=https://your-frontend-domain.com
FRONTEND_ORIGIN=https://your-frontend-domain.com

# Request timeout (recommended)
REQUEST_TIMEOUT_SECONDS=30
```

### Frontend Service

**Build command:**
```bash
yarn install --frozen-lockfile && yarn build
```

**Start command:**
```bash
npx serve -s build -l $PORT
```

**Environment variables:**
```bash
REACT_APP_BACKEND_URL=https://your-backend-service.railway.app
REACT_APP_SENTRY_DSN=
REACT_APP_SENTRY_ENVIRONMENT=production
```

---

## Database Index Strategy

**Critical indexes required for performance.** Run these on your new Atlas cluster after data migration.

### Core Collections

```javascript
// users collection
db.users.createIndex({ "id": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })

// leagues collection
db.leagues.createIndex({ "id": 1 }, { unique: true })
db.leagues.createIndex({ "inviteToken": 1 }, { unique: true })
db.leagues.createIndex({ "commissionerId": 1 })
db.leagues.createIndex({ "status": 1 })

// league_participants collection
db.league_participants.createIndex({ "leagueId": 1, "userId": 1 }, { unique: true })
db.league_participants.createIndex({ "leagueId": 1 })
db.league_participants.createIndex({ "userId": 1 })

// assets collection (teams, players, contestants)
db.assets.createIndex({ "id": 1 }, { unique: true })
db.assets.createIndex({ "sportKey": 1 })
db.assets.createIndex({ "externalId": 1 })
db.assets.createIndex({ "competitionShort": 1 })
db.assets.createIndex({ "sportKey": 1, "competitionShort": 1 })
```

### Auction & Bidding Collections

```javascript
// auctions collection
db.auctions.createIndex({ "id": 1 }, { unique: true })
db.auctions.createIndex({ "leagueId": 1 })
db.auctions.createIndex({ "status": 1 })

// bids collection
db.bids.createIndex({ "id": 1 }, { unique: true })
db.bids.createIndex({ "auctionId": 1 })
db.bids.createIndex({ "auctionId": 1, "clubId": 1 })
db.bids.createIndex({ "userId": 1 })
```

### Scoring Collections

```javascript
// fixtures collection
db.fixtures.createIndex({ "id": 1 }, { unique: true })
db.fixtures.createIndex({ "leagueId": 1 })
db.fixtures.createIndex({ "leagueId": 1, "status": 1 })
db.fixtures.createIndex({ "externalMatchId": 1 })

// league_points collection
db.league_points.createIndex({ "leagueId": 1, "clubId": 1 }, { unique: true })
db.league_points.createIndex({ "leagueId": 1 })

// standings collection
db.standings.createIndex({ "leagueId": 1 }, { unique: true })
```

### Utility Collections

```javascript
// magic_links collection (with TTL for auto-expiry)
db.magic_links.createIndex({ "token": 1 }, { unique: true })
db.magic_links.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 })

// debug_reports collection
db.debug_reports.createIndex({ "referenceId": 1 }, { unique: true })
db.debug_reports.createIndex({ "auctionId": 1 })
```

**Why critical:** Even with EU hosting, queries without indexes will be slow at scale. The bidding hot path queries `auctions`, `bids`, `league_participants`, and `assets` collections on every bid.

**Verification:** After creating indexes, run:
```javascript
db.auctions.getIndexes()
db.bids.getIndexes()
// etc.
```

---

## Monitoring & Alerts

### Railway Alerts (Recommended)
- Memory usage > 80% (15-min average)
- CPU usage > 80% (5-min average)
- Error rate > 5% (1-min window)
- Deployment failures

### Sentry Alerts (Recommended)
- New error type appears
- Error count > 10 in 1 hour
- Critical errors (500s, database connection failures)
- Socket.IO connection failures

### MongoDB Atlas Alerts (Phase 1: M0/M2 Monitoring)

**Critical alerts for knowing when to upgrade:**

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|-------------------|--------|
| CPU Usage | >70% sustained 10 min | >85% sustained 5 min | Upgrade to M10 |
| Connections | >400 | >450 | Upgrade to M10 |
| Query Execution Time (p50) | >200ms | >500ms | Check indexes, consider M10 |
| Query Execution Time (p99) | >1000ms | >2000ms | Upgrade to M10 |

**How to set up in Atlas:**
1. Atlas Dashboard → Your Cluster → Alerts
2. Click "Add Alert"
3. Configure each metric above
4. Set notification method (email)

### Key Metrics to Track

| Metric | Warning | Critical |
|--------|---------|----------|
| API p50 latency | >300ms | >500ms |
| API p99 latency | >1000ms | >2000ms |
| Bid success rate | <95% | <90% |
| Memory usage | >70% | >85% |
| Active connections | >200 | >250 |

---

## Security Considerations

### Current State (Migration Day 1-2)
- ⚠️ Auth in DEV MODE (token returned in response)
- ✅ Acceptable for: Internal testing, stress testing
- ❌ NOT acceptable for: External pilot users

### Hardened State (Day 3+)
- ✅ Magic link sent via email only
- ✅ Rate limiting prevents abuse
- ✅ Tokens not exposed in responses
- ✅ Ready for pilot users

---

## Rollback Plan

If Railway has issues:

1. **Immediate:** Emergent is still running - can revert DNS
2. **Data safe:** MongoDB Atlas is external - data persists regardless
3. **Alternative hosts:** Render, Fly.io have similar setup
4. **Timeline:** Can rollback in < 1 hour by reverting DNS/URLs

---

## Post-Migration Tasks

### Days 1-2: Migration & Validation
1. **Execute migration** following checklist
2. **Create database indexes** (see Database Index Strategy above)
3. **Run stress test** to validate latency improvement
4. **Monitor Sentry** for any new errors
5. **Verify all critical flows** work (auth, league creation, auction)

### Days 3-4: Auth Hardening (Before Pilot)
6. **Implement SendGrid email delivery**
7. **Add rate limiting** (3 requests/hour/email)
8. **Remove token from API response**
9. **Test complete auth flow** with real email
10. **Update stress test script** with --skip-auth flag

### Week 1: Stabilization
11. **Configure MongoDB backups** (verify enabled)
12. **Set up monitoring alerts** (Railway + Sentry + Atlas)
13. **Update documentation** with new URLs
14. **Prepare pilot user invitations**

---

## Emergency Contacts

| Issue | Contact/Resource |
|-------|------------------|
| Railway downtime | https://railway.statuspage.io |
| Railway support | https://railway.app/help |
| MongoDB Atlas issues | https://support.mongodb.com |
| Redis Cloud issues | https://support.redis.com |
| Critical bug alerts | Sentry → your email |
| Stress test failures | Check `/app/tests/multi_league_stress_test.py` logs |

---

## Resources

| Resource | Location |
|----------|----------|
| Migration Checklist | `/app/MIGRATION_CHECKLIST.md` |
| Database Schema | `/app/DATABASE_SCHEMA.md` |
| Stress Test Script | `/app/tests/multi_league_stress_test.py` |
| Master TODO List | `/app/MASTER_TODO_LIST.md` |
| Emergency Rebuild Prompt | `/app/docs/archive/EMERGENCY_REBUILD_PROMPT.md` |

---

## Gap Analysis (January 22, 2026)

### Areas Reviewed and Addressed

| Area | Status | Notes |
|------|--------|-------|
| Database indexes | ✅ Added | Corrected to match actual schema |
| Socket.IO sticky sessions | ✅ Added | Replicas = 1 note |
| Redis SSL format | ✅ Added | Verification note |
| Health check config | ✅ Added | Path and expected response |
| Monitoring alerts | ✅ Added | Thresholds defined, Atlas M0/M2 monitoring added |
| Security state | ✅ Added | DEV vs HARDENED documented |
| Emergency contacts | ✅ Added | Support links |
| Auth hardening timeline | ✅ Clarified | Day 3-4, before pilot |
| Cost optimization | ✅ Added | Phased M0/M2 → M10 approach |
| Root cause verification | ✅ Added | Phase 0 diagnostic test |

### 🔴 HIGH PRIORITY Gaps - Could Break Pilot

These items require attention before or immediately after migration:

#### 1. Connection Pool Sizing

| Aspect | Details |
|--------|---------|
| **Risk** | HIGH |
| **Issue** | 20 concurrent auctions × 8 users = high connection churn. Motor (MongoDB async driver) default pool may exhaust under load, causing bid failures. |
| **Symptoms** | `ServerSelectionTimeoutError`, intermittent bid failures, "connection pool exhausted" in logs |
| **Solution** | Add `?maxPoolSize=50` to MONGO_URL connection string |
| **When** | During migration (add to env var) |
| **Verification** | Monitor Atlas connections during stress test; should not approach limit |

**Implementation:**
```bash
# Instead of:
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/sport_x

# Use:
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/sport_x?maxPoolSize=50&connectTimeoutMS=10000&socketTimeoutMS=30000
```

#### 2. Request Timeouts

| Aspect | Details |
|--------|---------|
| **Risk** | HIGH |
| **Issue** | No explicit timeout configured. FastAPI default is no timeout. If a bid request hangs (DB issue, network blip), user sees infinite loading spinner. |
| **Symptoms** | Frozen UI, users refreshing repeatedly, duplicate bid attempts |
| **Solution** | Add request timeout middleware or per-route timeouts |
| **When** | Before pilot (can be added post-migration) |
| **Verification** | Test with simulated slow DB; requests should fail cleanly after 30s |

**Implementation options:**

Option A - Environment variable (simple):
```bash
REQUEST_TIMEOUT_SECONDS=30
```

Option B - FastAPI middleware (comprehensive):
```python
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=30.0)
        except asyncio.TimeoutError:
            return JSONResponse({"error": "Request timeout"}, status_code=504)

app.add_middleware(TimeoutMiddleware)
```

Option C - Per-route timeout (targeted):
```python
@api_router.post("/auction/{auction_id}/bid")
async def place_bid(...):
    try:
        result = await asyncio.wait_for(process_bid(...), timeout=10.0)
    except asyncio.TimeoutError:
        raise HTTPException(504, "Bid processing timeout")
```

**Recommendation:** Start with Option A (env var), implement Option C for bid endpoint if issues persist.

#### 3. API-Wide Rate Limiting

| Aspect | Details |
|--------|---------|
| **Risk** | MEDIUM-HIGH |
| **Issue** | Only auth endpoints have rate limiting planned. A malicious user or buggy client could spam bid requests, overwhelming the server. |
| **Symptoms** | Server slowdown, legitimate users affected, potential crash |
| **Solution** | Add general API rate limiting using `slowapi` or similar |
| **When** | Before pilot |
| **Verification** | Test by sending 100 requests/second; should get 429 responses after limit |

**Implementation:**
```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Global limit
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # 100 requests per minute per IP
    ...

# Or per-route
@api_router.post("/auction/{auction_id}/bid")
@limiter.limit("30/minute")  # 30 bids per minute per user
async def place_bid(...):
    ...
```

**Recommended limits:**
| Endpoint Pattern | Limit | Rationale |
|------------------|-------|-----------|
| `/api/auth/*` | 5/minute | Prevent brute force |
| `/api/auction/*/bid` | 30/minute | Normal bidding ~1/2 seconds |
| `/api/*` (general) | 100/minute | Prevent abuse |

#### 4. Backup Restore Testing

| Aspect | Details |
|--------|---------|
| **Risk** | MEDIUM-HIGH |
| **Issue** | Atlas M10 has point-in-time backups, but restore process never tested. If data corrupts during pilot, can you actually recover? |
| **Symptoms** | N/A until disaster strikes |
| **Solution** | Test restore to a separate temporary cluster before pilot |
| **When** | After migration, before pilot invitations sent |
| **Verification** | Successfully restore to temp cluster, verify data integrity |

**Test procedure:**
1. After migration, wait 24 hours for Atlas to have backup snapshots
2. Atlas Dashboard → Backup → Restore
3. Choose "Restore to a new cluster" (not production!)
4. Select cluster tier: M0 (free) is fine for testing
5. Wait for restore (~10-30 minutes depending on data size)
6. Connect to restored cluster, verify:
   - User count matches
   - League count matches
   - Sample queries return expected data
7. Delete test cluster to avoid charges

**Time required:** 1-2 hours  
**Cost:** £0 (M0 test cluster is free)

---

### 🟡 MEDIUM PRIORITY Gaps - Monitor During Pilot

| Area | Risk | Issue | Recommendation |
|------|------|-------|----------------|
| **Memory limits** | Medium | No explicit memory limit. Railway may OOM-kill if unbounded. | Monitor during stress test; set Railway memory limit if needed (512MB-1GB recommended) |
| **Graceful shutdown** | Medium | Uvicorn handles SIGTERM, but in-flight bids could be lost during deploy. | Accept risk for pilot; implement shutdown handler post-pilot if issues arise |
| **WebSocket ping/pong** | Medium | Socket.IO defaults may not handle flaky mobile connections well. | Monitor disconnect rates; tune `pingTimeout`/`pingInterval` if >5% disconnect rate |

---

### 🟢 LOWER PRIORITY Gaps - Address Post-Pilot

| Area | Risk | Notes |
|------|------|-------|
| **Log aggregation** | Low | Railway has logs, but no central aggregation. Consider Datadog/Papertrail if debugging becomes difficult. |
| **SSL/TLS certificate** | Low | Railway handles automatically. Verify after deploy by checking browser padlock. |
| **Cold start time** | Low | First request after deploy may be slow (~2-5s). Health check warmup helps. Not critical for pilot. |

---

### Pre-Migration Verification Checklist

Before executing migration, verify:

1. [ ] **Phase 0 diagnostic test completed** - Know which MongoDB tier to use
2. [ ] **Connection pool sizing** - `?maxPoolSize=50` added to MONGO_URL template
3. [ ] Redis connection string format confirmed (redis:// vs rediss://)
4. [ ] Football-Data.org API tier/limits documented
5. [ ] Current data volume for export (if not fresh start)
6. [ ] Atlas cluster provisioning time understood (~10 minutes for M0/M2, ~15 for M10)

### Post-Migration Verification Checklist

After migration, before pilot:

1. [ ] All database indexes created and verified
2. [ ] Stress test passes with target metrics (p50 <200ms, >95% success)
3. [ ] **Request timeout** implemented (at least env var)
4. [ ] **Rate limiting** implemented (at least on bid endpoint)
5. [ ] Auth hardening complete (email delivery working)
6. [ ] **Backup restore tested** on temporary cluster
7. [ ] Monitoring alerts configured (Railway + Sentry + Atlas)
8. [ ] Atlas performance metrics baseline established

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 4.3 | Jan 22, 2026 | Merged reviewer v4.2 with HIGH PRIORITY gap details. Added specific implementation code for connection pooling, timeouts, rate limiting. Added backup restore test procedure. Reorganized gaps by priority level. Added pre/post migration checklists with HIGH PRIORITY items. |
| 4.2 | Jan 22, 2026 | Added Phase 0 root cause verification test. Updated cost breakdown to phased approach (M0/M2 → M10). Added Atlas monitoring alerts for M0/M2. Updated executive summary with phased costs. |
| 4.1 | Jan 22, 2026 | Corrected database indexes to match actual schema (assets not teams, league_participants not leagues.managers). Added comprehensive gap analysis. Added key metrics table. Added TTL index for magic_links. |
| 4.0 | Jan 22, 2026 | Added: Database indexes, Socket.IO sticky sessions, monitoring alerts, auth hardening timeline clarification, security state documentation, emergency contacts |
| 3.1 | Jan 19, 2026 | Removed hybrid approach; Updated Sentry status; Added auth hardening requirement; Simplified document |
| 3.0 | Jan 12, 2026 | Added stress test findings |
| 2.0 | Dec 21, 2025 | Added Railway configurations |
| 1.0 | Dec 13, 2025 | Initial plan |
