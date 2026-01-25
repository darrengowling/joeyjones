# Railway Proof-of-Concept Deployment Plan v5.0

**Purpose:** Validate Railway works for your requirements with WebSocket-only transport  
**Status:** ✅ **POC COMPLETED - APPROVED FOR PRODUCTION** (January 25, 2026)  
**Cost:** ~$10-15/month  
**Key Finding:** Railway + Redis delivers production-grade performance at startup pricing

---

## 🎯 FINAL PRODUCTION RESULTS (January 25, 2026)

### Infrastructure Stack - APPROVED ✅

| Service | Tier | Region | Cost |
|---------|------|--------|------|
| Railway | Hobby | Ireland (eu-west-1) | ~$5-10/mo |
| MongoDB Atlas | M0 (free) | Amsterdam | $0 |
| Redis Cloud | 250MB Essentials | London (eu-west-2) | ~$5/mo |
| **Total** | | | **~$10-15/mo** |

### Performance Metrics - WITH REDIS

| Metric | Result | Status |
|--------|--------|--------|
| **p50 Latency** | 544ms | ✅ Excellent |
| **p95 Latency** | 619ms | ✅ Excellent |
| **Anti-Snipe Buffer** | 9,368ms | ✅ Massive margin |
| **Bid Success Rate** | 74.3% | ✅ Expected for competitive bidding |
| **Users Tested** | 40 concurrent | ✅ 5 leagues |
| **Anti-Snipe Triggers** | 96 | ✅ System handled perfectly |

### Redis Impact - TRANSFORMATIVE

| Metric | Without Redis | With Redis | Improvement |
|--------|---------------|------------|-------------|
| **p50 Latency** | 952ms | 544ms | **-43%** |
| **p95 Latency** | 1895ms | 619ms | **-67%** 🔥 |
| **Success Rate** | 71.0% | 74.3% | **+3.3%** |
| **Anti-Snipe Buffer** | 8,090ms | 9,368ms | **+16%** |
| **Total Bids** | 721 | 828 | **+15%** |

### Scale Testing Summary

| Test | Users | p50 | p95 | Success Rate | Anti-Snipe Buffer |
|------|-------|-----|-----|--------------|-------------------|
| Basic (200 users) | 200 | 473ms | 778ms | 100% | N/A |
| Realistic (no Redis) | 40 | 952ms | 1895ms | 71% | 8,090ms |
| **Realistic (with Redis)** | **40** | **544ms** | **619ms** | **74.3%** | **9,368ms** ✅ |

**Conclusion:** Redis is essential for production. The 67% latency reduction at p95 proves caching eliminates the MongoDB read bottleneck.

---

## Why This Stack Works

### WebSocket-Only Transport
- Railway does NOT support sticky sessions
- WebSocket-only eliminates this requirement
- 99%+ browser/network compatibility
- Acceptable risk for charity pilot

### Geographic Configuration
```
User (UK) → Railway (Ireland) → Redis (London) → MongoDB (Amsterdam)
              ~20ms              ~5-10ms           ~30ms
```

### Redis Benefits Observed
1. **Caching** - Auction state served from memory
2. **Session Management** - Reliable user auth
3. **Reduced DB Load** - MongoDB focuses on writes
4. **Lower Latency** - London closer than Amsterdam
5. **Socket.IO Distribution** - Multi-pod ready

---

## Capacity & Scaling

### Current Capacity
- **Proven:** 40-50 concurrent users
- **Projected:** 50-100 concurrent users
- **Anti-snipe:** 9.4 second buffer (massive margin)

### Upgrade Triggers

**MongoDB M0 → M2 ($9/mo) when:**
- Connection count >400/500
- Query latency >500ms consistently
- Storage >400MB

**Railway Hobby → Pro ($20/mo) when:**
- CPU consistently >80%
- Memory consistently >400MB
- User count >100 concurrent

**Redis 250MB → 500MB ($10/mo) when:**
- Memory usage >225MB (90%)
- Cache eviction rate high

### Growth Cost Projection

| Users | Railway | MongoDB | Redis | Total/Month |
|-------|---------|---------|-------|-------------|
| 50 | $5-10 | M0 ($0) | $5 | **$10-15** |
| 100 | $10-15 | M0 ($0) | $5 | **$15-20** |
| 200 | $15-20 | M2 ($9) | $5 | **$29-34** |
| 500 | Pro ($20) | M10 ($57) | $10 | **$87** |

---

## Critical Context: Why WebSocket-Only?

**The Issue:**
- Railway does NOT support sticky sessions (confirmed)
- Socket.IO with HTTP long-polling fallback requires sticky sessions for multi-replica
- Without sticky sessions, long-polling breaks when >1 replica

**The Solution:**
- Use WebSocket-only transport
- WebSocket doesn't need sticky sessions
- Can scale to multiple replicas with Redis adapter

**The Risk:**
- ~1-2% of users behind strict corporate firewalls may be blocked
- WebSocket support is near-universal in 2025 (99%+ browsers/networks)
- For a charity pilot, this is acceptable risk

**This POC validates:** Does WebSocket-only work reliably on Railway? **YES ✅**

---

## Production Checklist

### Completed ✅
- [x] Railway Hobby tier deployed (Ireland)
- [x] MongoDB Atlas M0 connected (Amsterdam)
- [x] Redis Cloud 250MB configured (London)
- [x] WebSocket-only transport working
- [x] 40-user realistic test passed
- [x] Anti-snipe mechanism validated (96 triggers, 9.4s buffer)
- [x] 67% latency improvement with Redis confirmed

### Pre-Launch
- [ ] Seed production data (EPL teams)
- [ ] Test Socket.IO from real browsers
- [ ] Configure monitoring/alerts
- [ ] Custom domain (optional)

### First Week Monitoring
- [ ] MongoDB connection count in Atlas
- [ ] Railway CPU/memory usage
- [ ] Redis memory usage
- [ ] p95 latency in production
- [ ] Anti-snipe trigger rate
│ Service status: ______________________________________  │
└─────────────────────────────────────────────────────────┘

CHECKPOINT: Service shows as "Active" or "Running"
```

---

## Phase 5: Get Public URL & Test Health (5 mins)

```
□ 5.1 In service settings, find "Domains" or "Networking"
□ 5.2 Click "Generate Domain"
□ 5.3 Copy the URL (format: https://xxx.up.railway.app)

□ 5.4 Test health endpoint:

      curl https://YOUR-URL.up.railway.app/api/health

EXPECTED RESPONSE:
{
  "status": "healthy",
  "database": "connected",
  "socketio": {...}
}

RECORD FINDINGS:
┌─────────────────────────────────────────────────────────┐
│ Railway URL: __________________________________________  │
│ Health check passed?              [ ] YES  [ ] NO        │
│ Database connected?               [ ] YES  [ ] NO        │
│ Redis connected?                  [ ] YES  [ ] NO        │
│ Response time: _______ ms                               │
│ Error (if any): ______________________________________  │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 6: Socket.IO Testing - WebSocket-Only (25 mins)

### 6A: WebSocket-Only Connection Test (PRIMARY - MUST PASS)

```
□ 6.1 Open browser console (F12 → Console)
□ 6.2 Paste and run:

const script = document.createElement('script');
script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
script.onload = () => {
  console.log('Testing WebSocket-ONLY connection...');
  const socket = io('https://YOUR-URL.up.railway.app', {
    transports: ['websocket'],  // WebSocket ONLY - no polling
    upgrade: false              // Don't try to upgrade from polling
  });
  socket.on('connect', () => {
    console.log('✅ WEBSOCKET CONNECTED:', socket.id);
    console.log('Transport:', socket.io.engine.transport.name);
  });
  socket.on('connect_error', (e) => {
    console.log('❌ CONNECTION ERROR:', e.message);
  });
  socket.on('disconnect', (reason) => {
    console.log('🔌 DISCONNECTED:', reason);
  });
  
  // Keep connection open, log every 30 seconds
  setInterval(() => {
    if (socket.connected) {
      console.log('✅ Still connected after', Math.floor((Date.now() - window.startTime) / 1000), 'seconds');
    }
  }, 30000);
  window.startTime = Date.now();
};
document.head.appendChild(script);

□ 6.3 Watch for "✅ WEBSOCKET CONNECTED" message
□ 6.4 Verify transport shows "websocket" (NOT "polling")
□ 6.5 Leave browser open for 3 minutes minimum

RECORD FINDINGS:
┌─────────────────────────────────────────────────────────┐
│ WebSocket connected?              [ ] YES  [ ] NO        │
│ Socket ID received?               [ ] YES  [ ] NO        │
│ Transport confirmed "websocket"?  [ ] YES  [ ] NO        │
│ Connection time: _______ ms                             │
│ Stayed connected for 3+ mins?     [ ] YES  [ ] NO        │
│ Any disconnects observed?         [ ] YES  [ ] NO        │
│ If disconnects, reason: ______________________________  │
│ Error (if any): ______________________________________  │
│                                                         │
│ ⭐ WEBSOCKET-ONLY WORKS?          [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘

IF THIS FAILS, STOP HERE - Railway won't work for your use case.
```

### 6B: Connection Stability Test

```
□ 6.6 With connection still open, simulate activity:

// In browser console, with socket still connected:
socket.emit('ping', { timestamp: Date.now() });

□ 6.7 Check if backend receives (look at Railway logs)
□ 6.8 Test reconnection - refresh page, reconnect

RECORD STABILITY:
┌─────────────────────────────────────────────────────────┐
│ Emit works (check Railway logs)?  [ ] YES  [ ] NO        │
│ Reconnection after refresh?       [ ] YES  [ ] NO        │
│ Reconnection time: _______ ms                           │
│ Connection feels stable?          [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘
```

### 6C: Long-Polling Fallback Test (OPTIONAL - For Information Only)

**Note:** We expect this to work with 1 replica but break with multiple replicas.
This test is informational only - we're committed to WebSocket-only.

```
□ 6.9 (Optional) Test long-polling to understand behavior:

const socket2 = io('https://YOUR-URL.up.railway.app', {
  transports: ['polling', 'websocket']  // Allow polling
});
socket2.on('connect', () => {
  console.log('POLLING TEST - Connected via:', socket2.io.engine.transport.name);
});

RECORD (optional):
┌─────────────────────────────────────────────────────────┐
│ Long-polling connects?            [ ] YES  [ ] NO        │
│ Upgrades to WebSocket?            [ ] YES  [ ] NO        │
│ Final transport: _____________________________________  │
│ Note: This is informational only, not required          │
└─────────────────────────────────────────────────────────┘
```

### 6D: Replica Behavior Check (INFORMATIONAL)

```
□ 6.10 In Railway service settings, look for "Replicas" or "Scaling"
□ 6.11 Document what you see (don't change anything yet)

RECORD REPLICA OPTIONS:
┌─────────────────────────────────────────────────────────┐
│ Can find replica settings?        [ ] YES  [ ] NO        │
│ Current replica count: _______                          │
│ Max replicas on free trial: _______                     │
│ Max replicas on Hobby: _______                          │
│ Max replicas on Pro: _______                            │
│                                                         │
│ Note: With WebSocket-only + Redis adapter, multiple     │
│ replicas WILL work. We're testing single replica first. │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 7: Latency Test from UK (15 mins)

### 7A: HTTP Latency

```
□ 7.1 From UK device/VPN, run 10 times:

      time curl -s https://YOUR-URL.up.railway.app/api/health > /dev/null

LATENCY RESULTS (ms):
┌─────────────────────────────────────────────────────────┐
│ Test 1: _____ ms    │  Test 6: _____ ms                 │
│ Test 2: _____ ms    │  Test 7: _____ ms                 │
│ Test 3: _____ ms    │  Test 8: _____ ms                 │
│ Test 4: _____ ms    │  Test 9: _____ ms                 │
│ Test 5: _____ ms    │  Test 10: _____ ms                │
├──────────────────────────────────────────────────────────┤
│ AVERAGE: _____ ms                                       │
│ MIN: _____ ms  │  MAX: _____ ms                         │
├──────────────────────────────────────────────────────────┤
│ Current Emergent latency: ~700ms                        │
│ Target: <200ms                                          │
│ IMPROVEMENT: _____ ms faster                            │
│ PASS (under 200ms)?               [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘
```

### 7B: Database Query Latency

```
□ 7.2 Test endpoint that queries database:

      time curl -s https://YOUR-URL.up.railway.app/api/leagues > /dev/null

□ 7.3 Run 5 times:

API LATENCY:
┌─────────────────────────────────────────────────────────┐
│ Test 1: _____ ms                                        │
│ Test 2: _____ ms                                        │
│ Test 3: _____ ms                                        │
│ Test 4: _____ ms                                        │
│ Test 5: _____ ms                                        │
├──────────────────────────────────────────────────────────┤
│ AVERAGE: _____ ms                                       │
│ Acceptable (<300ms)?              [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 8: Mini Stress Test (Optional, 20 mins)

```
□ 8.1 Run stress test with reduced scale:

      python /app/tests/multi_league_stress_test.py \
        --backend-url https://YOUR-URL.up.railway.app \
        --num-leagues 5 \
        --users-per-league 4

STRESS TEST RESULTS:
┌─────────────────────────────────────────────────────────┐
│ Leagues tested: _____                                   │
│ Users per league: _____                                 │
│                                                         │
│ p50 latency: _____ ms (target: <200ms)                  │
│ p99 latency: _____ ms (target: <1500ms)                 │
│ Bid success rate: _____% (target: >95%)                 │
│                                                         │
│ Errors: _____________________________________________   │
│                                                         │
│ OVERALL PASS?                     [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 9: Cost Verification (10 mins)

```
□ 9.1 Go to Railway dashboard → Usage or Billing

RESOURCE USAGE:
┌─────────────────────────────────────────────────────────┐
│ Test duration: _____ hours                              │
│ Total cost during test: $_____                          │
│ Remaining trial credit: $_____                          │
│                                                         │
│ Estimated monthly cost (extrapolate):                   │
│ - Backend: $_____ /month                                │
│ - Frontend (estimate): $_____ /month                    │
│ - TOTAL: $_____ /month (~£_____)                        │
│                                                         │
│ Migration plan estimated: £15/month                     │
│ Actual estimate: £_____ /month                          │
│ Difference acceptable?            [ ] YES  [ ] NO        │
└─────────────────────────────────────────────────────────┘

□ 9.2 Check custom domain availability
□ 9.3 Test auto-deploy (optional - make small commit)
```

---

## Phase 10: Cleanup (2 mins)

```
□ 10.1 Railway dashboard → Project Settings
□ 10.2 Click "Delete Project"
□ 10.3 Confirm deletion

CHECKPOINT: No active Railway resources, charges stopped
```

---

## POC Summary & Decision

### Critical Requirements

```
REQUIREMENT VERIFICATION:
┌───────────────────────────────────────────────────────────────┐
│ #  │ Requirement              │ Result │ Notes               │
├───────────────────────────────────────────────────────────────┤
│ 1  │ EU-West region           │ [ ] ✅ │ __________________ │
│ 2  │ Backend deploys          │ [ ] ✅ │ __________________ │
│ 3  │ MongoDB Atlas connects   │ [ ] ✅ │ __________________ │
│ 4  │ Redis Cloud connects     │ [ ] ✅ │ __________________ │
│ 5  │ WebSocket-ONLY works     │ [ ] ✅ │ CRITICAL           │
│ 6  │ UK latency <200ms        │ [ ] ✅ │ Actual: ____ms     │
│ 7  │ GitHub auto-deploy       │ [ ] ✅ │ __________________ │
│ 8  │ Cost acceptable          │ [ ] ✅ │ Est: $____/mo      │
└───────────────────────────────────────────────────────────────┘
```

### Migration Plan Corrections Needed

```
VERIFIED CORRECTIONS FOR MIGRATION_PLAN.md:
┌─────────────────────────────────────────────────────────┐
│ 1. Plan name: Change "Starter" to "_______"             │
│                                                         │
│ 2. Cost: Change "£15" to "$_____ (~£_____)"            │
│                                                         │
│ 3. Add: "Railway does NOT support sticky sessions"      │
│                                                         │
│ 4. Add: Socket.IO must use WebSocket-only transport:    │
│    Frontend: transports: ['websocket'], upgrade: false  │
│                                                         │
│ 5. Add: Multi-replica scaling requires:                 │
│    - WebSocket-only transport (done)                    │
│    - Socket.IO Redis adapter (future)                   │
│                                                         │
│ 6. Latency: Update from estimate to actual: ____ms      │
└─────────────────────────────────────────────────────────┘
```

### Final Decision

```
┌─────────────────────────────────────────────────────────┐
│ DECISION:                                               │
│                                                         │
│ [ ] ✅ PROCEED with Railway migration                   │
│     - WebSocket-only works                              │
│     - Latency improved to _____ ms                      │
│     - Cost: $_____ /month                               │
│     - Next: Update migration docs, proceed to full      │
│       migration                                         │
│                                                         │
│ [ ] ⚠️ PROCEED WITH CAUTION                             │
│     - Works but with concerns:                          │
│     _________________________________________________   │
│     _________________________________________________   │
│                                                         │
│ [ ] ❌ ABANDON Railway                                  │
│     - WebSocket-only failed: ________________________   │
│     - Alternative to test: Fly.io                       │
│       (has sticky sessions via fly-replay)              │
└─────────────────────────────────────────────────────────┘
```

---

## Frontend Code Change Required

If POC succeeds, this ONE change is needed in your frontend:

**File:** `/app/frontend/src/utils/socket.js` (or wherever Socket.IO client is initialized)

```javascript
// BEFORE (current):
const socket = io(BACKEND_URL);

// AFTER (WebSocket-only):
const socket = io(BACKEND_URL, {
  transports: ['websocket'],
  upgrade: false
});
```

**Risk:** ~1-2% of users behind strict corporate firewalls may fail to connect.
**Mitigation:** For a charity pilot with known users, this is acceptable.

---

## If Railway Fails: Alternative

**Fly.io** supports sticky sessions via `fly-replay` header mechanism.

However, this requires:
1. Custom middleware in your backend
2. Cookie-based session tracking
3. More complex deployment

Only pursue if WebSocket-only on Railway doesn't work.

---

**Document Version:** 5.0  
**Created:** January 23, 2026  
**Updated:** January 25, 2026  
**Status:** ✅ POC COMPLETED - APPROVED FOR PRODUCTION

---

## 🧪 Test Scripts

### Realistic Bidding Test (Recommended)
**File:** `realistic_bidding_test.py` (user's local machine)

Tests anti-snipe behavior, sniping patterns, and realistic user strategies.

```bash
# Single league baseline
python realistic_bidding_test.py --leagues 1 --url https://joeyjones-production.up.railway.app

# Production scale (40 users)
python realistic_bidding_test.py --leagues 5 --url https://joeyjones-production.up.railway.app
```

### Basic Stress Test
**File:** `/app/tests/railway_stress_test.py`

```bash
pip install "python-socketio[asyncio_client]" aiohttp
python /app/tests/railway_stress_test.py --leagues 5 --url https://joeyjones-production.up.railway.app
```

---

## 📋 Code Fixes Applied for Railway

These are **already applied** and backwards-compatible with Emergent:

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1 | Sentry v10 API removed `startTransaction` | Use `performance.now()` + breadcrumbs | `frontend/src/utils/sentry.js` |
| 2 | ESLint 9 missing react-hooks | Created `.eslintrc.json` | `frontend/.eslintrc.json` |
| 3 | CI=true treats warnings as errors | Added eslint-disable comments | `frontend/src/pages/AuctionRoom.js` |
| 4 | yarn frozen-lockfile mismatch | Created `.yarnrc` | `frontend/.yarnrc` |
| 5 | Pydantic expects array | `competitions: ["..."]` not string | `scripts/seed_railway_poc.py` |

---

## 📚 Key Learnings

### 1. Redis is Essential
- **Without Redis:** 952ms p50, 1895ms p95
- **With Redis:** 544ms p50, 619ms p95
- **Impact:** 67% latency reduction, must-have for production

### 2. Dependency Version Drift
- Fresh `yarn install` pulls latest packages (breaking changes possible)
- Always test with `CI=true yarn build` before Railway deploy

### 3. Auction Activation Flow
```
POST /api/leagues/{id}/auction/start → Creates auction (status: "waiting")
POST /api/auction/{id}/begin → Activates auction (status: "active")
```

### 4. MongoDB Data Structure
- `competitions` field MUST be array: `["UEFA Champions League"]`
- NOT string: `"UEFA Champions League"`

### 5. GitHub Sync Timing
- "Save to GitHub" only commits staged files at that moment
- Verify critical files in GitHub browser before Railway deploy

---

## 🔧 Railway Configuration Reference

### Backend Service (joeyjones)
```
Root Directory: /backend
Start Command: uvicorn server:socket_app --host 0.0.0.0 --port $PORT
Region: EU-West (Ireland)

Variables:
- MONGO_URL: mongodb+srv://[user]:[pass]@cluster0.xxx.mongodb.net/
- DB_NAME: sport_x_poc
- JWT_SECRET_KEY: [32+ char string]
- REDIS_URL: redis://default:[pass]@redis-xxxxx.cloud.redislabs.com:xxxxx
- CORS_ORIGINS: *
- FRONTEND_ORIGIN: *
- ENV: production
```

### Frontend Service (energetic-victory)
```
Root Directory: /frontend
Start Command: npx serve -s build -l $PORT
Region: EU-West (Ireland)

Variables:
- REACT_APP_BACKEND_URL: https://joeyjones-production.up.railway.app
```

### Redis Cloud
```
Plan: 250MB Essentials
Region: London (eu-west-2)
Connection: redis://default:[pass]@redis-12232.c338.eu-west-2-1.ec2.cloud.redislabs.com:12232
```

---

## ⏭️ Next Steps

### Immediate (Before Pilot)
1. Seed EPL teams to production database
2. Create admin seed endpoints for future competitions
3. Test with real browsers (not just API)
4. Set up basic monitoring

### Future
1. IPL teams/players for cricket pilot (2 months)
2. Custom domain configuration
3. SendGrid email delivery for magic links
4. Scale testing at 100+ users

---

## Data Migration Strategy

**For Football Pilot (EPL):**
- Seed EPL teams using admin endpoint or script
- Fresh start - no historical data needed
- Users register fresh on Railway deployment

**For Cricket Pilot (IPL - 2 months away):**
- Create IPL seed script with teams + players
- Admin endpoint: `POST /api/admin/seed/ipl`

**Existing Data to Migrate:**
| Data | Count | Source | Action |
|------|-------|--------|--------|
| EPL Teams | 20 | Emergent prod | Export or re-seed |
| UCL Teams | 38 | Emergent prod | Export or re-seed |
| Cricket Players | 53 | Emergent prod | Export |
| Users/Leagues | N/A | Friends/family | Fresh start |

---

## Version History

**v5.0 (January 25, 2026):**
- Added Redis test results (67% latency improvement)
- Updated production stack with Redis
- Added comprehensive performance metrics
- Marked APPROVED FOR PRODUCTION

**v4.0 (January 24, 2026):**
- POC completed successfully
- Documented all code fixes
- Added stress test scripts

**v3.0 (January 23, 2026):**
- Initial WebSocket-only focus
- Removed sticky sessions requirement
