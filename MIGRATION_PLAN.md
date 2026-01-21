# Migration Plan: Emergent → Railway (EU-West)

**Created:** December 13, 2025  
**Last Updated:** January 22, 2026  
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
| **Monthly Cost** | ~£65 (Railway £15 + Atlas M10 £45 + Redis £5) |
| **Timeline** | 2-3 days (migration + validation + auth hardening) |

---

## Why Migration is Required

### Root Cause Analysis (January 2026)

**Stress testing confirmed the issue is infrastructure, not code:**

| Factor | Current (Emergent) | After Migration (Railway EU) |
|--------|-------------------|------------------------------|
| App server location | US | EU-West (London) |
| MongoDB location | US (shared cluster) | EU (your dedicated M10) |
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
    ├── MongoDB Atlas M10 (europe-west2/London) ← YOUR ACCOUNT
    ├── Redis Cloud Essentials (256 conn) ← YOUR EXISTING ACCOUNT
    ├── Sentry (error tracking) ← CONFIGURED
    ├── Football-Data.org API
    └── Cricbuzz/RapidAPI
```

---

## Cost Breakdown (Phased)

### Phase 1: Validation & Single-Charity Pilot (Weeks 1-2)

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Railway | Starter | ~£15 |
| MongoDB Atlas | M2 (europe-west2) | ~£9 |
| Redis Cloud | Essentials (256 conn) | ~£5 |
| Sentry | Free | £0 |
| **Total** | | **~£29/month** |

### Phase 2: Multi-Charity Scale (Week 3+)

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Railway | Starter | ~£15 |
| MongoDB Atlas | M10 (europe-west2) | ~£45 |
| Redis Cloud | Essentials (256 conn) | ~£5 |
| Sentry | Free | £0 |
| **Total** | | **~£65/month** |

### Upgrade Triggers (M2 → M10)

Upgrade to M10 when ANY of these occur:
- Atlas connections > 400
- Atlas CPU > 70% sustained
- Query latency > 200ms average
- Adding 3rd+ charity to pilot
- Stress test shows degradation

**Rationale:** Start lean, validate assumptions, scale when proven necessary. Saves £36/month if M2 is sufficient.

---

## Pre-Migration Requirements

### ✅ Already Done
- [x] Sentry configured (backend DSN active)
- [x] Redis Cloud upgraded to Essentials (256 connections)
- [x] Stress test script ready (`/app/tests/multi_league_stress_test.py`)
- [x] Environment variables documented

---

## Phase 0: Root Cause Verification (CRITICAL)

**Goal:** Prove whether 700ms latency is geography or database tier before committing to M10

**Time required:** 1-2 hours

### Why This Matters

| Root Cause | Solution | Monthly Cost |
|------------|----------|--------------|
| Geography (US→UK network) | M0/M2 in EU sufficient | £0-9 |
| Database tier (shared CPU throttling) | M10 required | £45 |
| Both factors | M10 required | £45 |

**Cost impact:** £540/year difference between M0 and M10

### Diagnostic Test Setup (30 mins)

1. Create Railway account (railway.app)
2. Deploy backend only to Railway EU-West
3. **Keep using Emergent's existing MongoDB URL** (the US-hosted one)
4. Update CORS to allow Railway domain temporarily

### Run Diagnostic (30 mins)

```bash
# Run stress test against Railway EU backend (still using US database)
python multi_league_stress_test.py --leagues 5 --users 6 --url https://YOUR-RAILWAY-BACKEND.railway.app
```

### Interpret Results

| Current (Emergent) | Railway EU + US DB | Verdict | Action |
|--------------------|--------------------|---------| -------|
| 700ms | 150-250ms | **Geography was the issue** | ✅ Use M2 (£9/mo) |
| 700ms | 400-500ms | **Mixed (geography + DB)** | Start M2, monitor closely |
| 700ms | 650-700ms | **Database is the bottleneck** | ✅ Use M10 (£45/mo) |

### Decision Point

- **If latency drops significantly:** Proceed with M2, upgrade to M10 only if needed
- **If latency stays high:** Proceed directly to M10

### Skip Conditions

You may skip Phase 0 if:
- You're comfortable with £65/month regardless
- You want M10's point-in-time backups for data safety
- Time pressure requires proceeding immediately

---

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
MONGO_URL=mongodb+srv://user:pass@YOUR-cluster.europe-west2.mongodb.net/sport_x
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
12. **Set up monitoring alerts** (Railway + Sentry)
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
| Monitoring alerts | ✅ Added | Thresholds defined |
| Security state | ✅ Added | DEV vs HARDENED documented |
| Emergency contacts | ✅ Added | Support links |
| Auth hardening timeline | ✅ Clarified | Day 3-4, before pilot |
| Build command | ✅ Updated | --frozen-lockfile flag |

### Potential Gaps Remaining (Flagged for Review)

| Area | Risk | Notes |
|------|------|-------|
| **Connection pool sizing** | Medium | Motor (MongoDB driver) defaults may not be optimal. Consider `maxPoolSize=50` for M10. |
| **Request timeouts** | Medium | No explicit timeout config. FastAPI default is no timeout. Consider 30s limit. |
| **Graceful shutdown** | Low | Uvicorn handles SIGTERM, but in-flight bids could be lost. May need shutdown handler. |
| **Rate limiting (API-wide)** | Medium | Only auth rate limiting planned. Consider general API rate limiting for abuse prevention. |
| **Log aggregation** | Low | Railway has logs, but no central aggregation. Consider if needed for debugging. |
| **Backup restore testing** | Medium | Atlas M10 has backups, but restore process not tested. Should verify before pilot. |
| **SSL/TLS certificate** | Low | Railway handles this automatically, but should verify after deploy. |
| **WebSocket ping/pong** | Low | Socket.IO has defaults, but may need tuning for mobile clients with poor connections. |
| **Memory limits** | Medium | No explicit memory limit set. Railway may OOM-kill if unbounded. |
| **Cold start time** | Low | First request after deploy may be slow. Consider health check warmup. |

### Recommended Pre-Migration Verification

Before executing migration, verify:

1. [ ] **ROOT CAUSE VERIFICATION** - Complete Phase 0 diagnostic (geography vs database tier)
2. [ ] Redis connection string format (redis:// vs rediss://)
3. [ ] Football-Data.org API tier/limits
4. [ ] Current data volume for export (if not fresh start)
5. [ ] Atlas M2/M10 provisioning time (~5-10 minutes typically)

### Recommended Post-Migration Verification

After migration, before pilot:

1. [ ] All indexes created and verified
2. [ ] Stress test passes with target metrics
3. [ ] Auth hardening complete
4. [ ] Backup restore tested at least once
5. [ ] Monitoring alerts configured and tested

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 4.2 | Jan 22, 2026 | Added Phase 0 root cause verification test. Changed to phased cost model (M2→M10). Added upgrade triggers. Addresses reviewer feedback on unvalidated M10 assumption. |
| 4.1 | Jan 22, 2026 | Corrected database indexes to match actual schema (assets not teams, league_participants not leagues.managers). Added comprehensive gap analysis. Added key metrics table. Added TTL index for magic_links. |
| 4.0 | Jan 22, 2026 | Added: Database indexes, Socket.IO sticky sessions, monitoring alerts, auth hardening timeline clarification, security state documentation, emergency contacts |
| 3.1 | Jan 19, 2026 | Removed hybrid approach; Updated Sentry status; Added auth hardening requirement; Simplified document |
| 3.0 | Jan 12, 2026 | Added stress test findings |
| 2.0 | Dec 21, 2025 | Added Railway configurations |
| 1.0 | Dec 13, 2025 | Initial plan |
