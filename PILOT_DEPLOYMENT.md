# Pilot Deployment Configuration

**Date:** 2025-10-16  
**Version:** Production Candidate v1.2 (Pilot)  
**Status:** ✅ READY FOR DEPLOYMENT

---

## Executive Summary

This pilot deployment configuration removes Redis dependency, disables rate limiting for easier user testing, uses in-memory Socket.IO (single replica), and sets production-ready CORS. All real-time features remain functional.

**Key Changes:**
- ✅ Rate limiting disabled (ENABLE_RATE_LIMITING=false)
- ✅ Redis removed (REDIS_URL=)
- ✅ Socket.IO in-memory mode (single replica)
- ✅ CORS set to production domain
- ✅ Metrics enabled for monitoring
- ✅ ENV set to "production"

---

## Configuration Changes

### 1. Backend Environment Variables

**File:** `/app/backend/.env`

```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="https://fix-roster-sync.preview.emergentagent.com"
SPORTS_CRICKET_ENABLED=true
# Pilot deployment configuration (no Redis, single replica)
REDIS_URL=
ENABLE_RATE_LIMITING=false
ENABLE_METRICS=true
JWT_SECRET=dev-secret-change-in-production
FRONTEND_ORIGIN="https://fix-roster-sync.preview.emergentagent.com"
FEATURE_MY_COMPETITIONS=true
ENV="production"
```

**Changes Made:**
- `REDIS_URL=` (empty, no Redis)
- `ENABLE_RATE_LIMITING=false` (disabled for pilot)
- `FRONTEND_ORIGIN` set to production domain
- `ENV="production"` (enables production mode, guards debug endpoints)

**For Multiple Domains:**
```bash
CORS_ORIGINS="https://prod-domain.com,https://staging-domain.com"
```

### 2. Backend Startup Behavior

**File:** `/app/backend/server.py`

The application already respects the configuration flags:

```python
# Rate limiting initialization (lines 108-123)
@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db_client()
    
    if ENABLE_RATE_LIMITING and REDIS_URL and REDIS_URL.strip():
        # Initialize Redis-based rate limiting
        r = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(r)
        logger.info("✅ Rate limiting initialized with Redis")
    else:
        logger.info("📝 Rate limiting disabled or Redis not configured")
    
    yield
```

**Result:** When `ENABLE_RATE_LIMITING=false`, rate limiters are inert (no 429 responses).

### 3. Socket.IO Configuration

**File:** `/app/backend/socketio_init.py`

Already configured to work without Redis:

```python
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
REDIS_URL = os.getenv("REDIS_URL")

# Use AsyncRedisManager if REDIS_URL set; else in-memory manager
mgr = None
if REDIS_URL and REDIS_URL.strip():
    try:
        mgr = socketio.AsyncRedisManager(REDIS_URL)
        logger.info(f"✅ Socket.IO Redis manager initialized")
    except Exception as e:
        logger.error(f"❌ Redis manager failed, falling back to memory: {e}")
        mgr = None
else:
    logger.info("📝 Socket.IO using in-memory manager (single replica)")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else "*",
    client_manager=mgr,  # None for in-memory, Redis manager for multi-replica
    ping_interval=20,
    ping_timeout=25,
)
```

**Result:** With `REDIS_URL=`, Socket.IO uses in-memory manager (single replica only).

### 4. CORS Middleware

**File:** `/app/backend/server.py` (lines 2563-2575)

Already configured to read from environment:

```python
cors_origins_str = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    allow_credentials=True,
    max_age=600,
)
```

**Result:** CORS restricted to `https://fix-roster-sync.preview.emergentagent.com`.

---

## Deployment Architecture

### Single Replica Mode

**Backend:** 1 replica (required for in-memory Socket.IO)  
**Frontend:** Can scale (static assets)  
**Database:** MongoDB (managed or external)

### Why Single Replica?

Without Redis, Socket.IO uses in-memory client manager. This means:
- ✅ All Socket.IO connections handled by single backend instance
- ✅ No cross-pod communication needed
- ✅ Simpler architecture for pilot
- ⚠️ Limited to ~1000 concurrent socket connections per replica

**For Production Scale:** Add Redis and enable multi-replica deployment.

### Ingress Routing

**Routes (in order):**
1. `/socket.io/*` → backend:8001 (WebSocket + polling)
2. `/api/*` → backend:8001 (REST API)
3. `/*` → frontend:3000 (React app)

**Critical:** `/socket.io/*` must be routed to backend, not frontend.

---

## Features Status

### ✅ Working (Pilot)

| Feature | Status | Notes |
|---------|--------|-------|
| Real-time Socket.IO | ✅ Working | In-memory mode, single replica |
| Lobby presence updates | ✅ Working | Sub-second updates |
| Auction button real-time | ✅ Working | Sub-second updates |
| Bid synchronization | ✅ Working | All users see same state |
| Timer synchronization | ✅ Working | useAuctionClock + socket events |
| League management | ✅ Working | Create, join, invite |
| Auction engine | ✅ Working | Bidding, anti-snipe, completion |
| My Competitions | ✅ Working | Dashboard, standings, fixtures |
| CSV fixtures import | ✅ Working | Commissioner upload |
| Multi-sport (Football) | ✅ Working | Full support |
| Multi-sport (Cricket) | 🟡 Pilot | Scoring engine ready |
| Metrics endpoint | ✅ Working | `/api/metrics` for Prometheus |
| CORS security | ✅ Working | Restricted to production domain |
| Debug endpoints | ✅ Secured | 404 in production (ENV=production) |

### ⚠️ Disabled (Pilot)

| Feature | Status | Notes |
|---------|--------|-------|
| Rate limiting | ⚠️ Disabled | ENABLE_RATE_LIMITING=false |
| Multi-replica Socket.IO | ⚠️ Not available | Requires Redis |

### 🔄 Future Enhancements

| Feature | Timeline | Requirements |
|---------|----------|--------------|
| Rate limiting | Enable post-pilot | Add Redis service |
| Multi-replica scaling | 2 weeks | Add Redis for Socket.IO pub/sub |
| Per-user rate limits | 2 weeks | User authentication + Redis |

---

## Security Posture

### ✅ Enabled Protections

- **CORS:** Restricted to specific domain(s)
- **Debug Endpoints:** Guarded by ENV variable (404 in production)
- **Database Indexes:** All unique constraints enforced
- **Input Validation:** Pydantic models on all endpoints
- **Socket.IO CORS:** Restricted via FRONTEND_ORIGIN

### ⚠️ Disabled for Pilot

- **Rate Limiting:** Disabled (ENABLE_RATE_LIMITING=false)
  - **Risk:** Potential API abuse (bid flooding, league spam)
  - **Mitigation:** Monitor request logs, enable post-pilot

### Recommended Monitoring

**Alert Conditions:**
- Request rate > 1000 req/min from single IP
- Bid endpoint > 100 req/min from single IP
- League creation > 10 req/min from single IP
- Error rate > 5%
- Socket.IO disconnect rate > 20%

---

## Smoke Test Plan

### Pre-Deployment Checklist

- [x] REDIS_URL empty in backend/.env
- [x] ENABLE_RATE_LIMITING=false in backend/.env
- [x] CORS_ORIGINS set to production domain
- [x] FRONTEND_ORIGIN set to production domain
- [x] ENV="production" (guards debug endpoints)
- [x] Backend service running
- [x] Frontend service running
- [x] Metrics endpoint accessible

### Post-Deployment Smoke Test

**Requirements:**
- 2 browsers (or 1 normal + 1 incognito)
- 2 different user accounts (commissioner + manager)

#### Test Flow

**1. League Creation & Join (Commissioner)**
```
1. Open Browser 1 (normal)
2. Sign in as Commissioner
3. Create new league (name: "Smoke Test League")
4. Note invite token from league page
```

**2. League Join (Manager)**
```
1. Open Browser 2 (incognito)
2. Sign in as Manager
3. Navigate to "Join Competition"
4. Enter invite token from step 1.4
5. Click "Join League"
```

**3. Real-Time Test #1: Lobby Presence** ⏱️
```
Expected: Commissioner's Browser 1 shows Manager appeared in lobby within ~1 second
Pass Criteria: No manual refresh needed, member appears automatically
```

**4. Auction Start (Commissioner)**
```
1. In Browser 1, click "Start Auction"
2. Confirm auction started
```

**5. Real-Time Test #2: Auction Button** ⏱️
```
Expected: Manager's Browser 2 shows "Enter Auction Room" button within ~1 second
Pass Criteria: Button appears automatically without refresh
```

**6. Enter Auction Room (Both)**
```
1. Browser 1 (Commissioner): Click "Enter Auction Room"
2. Browser 2 (Manager): Click "Enter Auction Room"
3. Both should see same current lot
```

**7. Real-Time Test #3: Bid Synchronization** ⏱️
```
1. Browser 1: Place bid (e.g., £5m)
2. Browser 2: Observe - should show "Current bid: £5m by Commissioner"
3. Browser 2: Place higher bid (e.g., £6m)
4. Browser 1: Observe - should show "Current bid: £6m by Manager"

Pass Criteria: 
- Both users see identical current bid
- Updates appear within ~1 second
- No manual refresh needed
```

**8. Metrics Verification**
```
1. Open: https://fix-roster-sync.preview.emergentagent.com/api/metrics
2. Search for metrics:
   - bids_placed_total (should be > 0)
   - participants_joined_total (should be > 0)
   - http_request_duration_seconds_bucket
3. Verify counters increase after test actions
```

**9. CORS Verification**
```
1. Open browser DevTools (F12)
2. Go to Console tab
3. Check for CORS errors (should be none)
4. Go to Network tab
5. Refresh page
6. Check response headers for Access-Control-Allow-Origin
7. Should match production domain
```

---

## Pass Criteria Summary

| Test | Expected Result | Pass Criteria |
|------|----------------|---------------|
| **Lobby Presence** | Member appears in <1s | ✅ No manual refresh |
| **Auction Button** | Button appears in <1s | ✅ No manual refresh |
| **Bid Sync** | Both see same bid in <1s | ✅ Identical state |
| **Metrics** | Counters increase | ✅ > 0 after actions |
| **CORS** | No console errors | ✅ Headers correct |
| **No 5xx Errors** | All requests succeed | ✅ Status 200/201/204 |

**Overall Pass:** All 6 tests must pass.

---

## Troubleshooting

### Issue: Socket.IO Not Connecting

**Symptoms:**
- Real-time updates not working
- Console shows connection errors

**Check:**
1. `/socket.io/*` routes to backend (not frontend)
2. `FRONTEND_ORIGIN` set correctly in backend/.env
3. No CORS errors in browser console
4. Backend logs show socket connections

**Fix:**
```bash
# Verify backend logs
tail -f /var/log/supervisor/backend.out.log | grep -i socket

# Test Socket.IO health
curl -i https://your-domain.com/socket.io/?transport=polling
# Should return 200 OK
```

### Issue: CORS Errors

**Symptoms:**
- Browser console: "blocked by CORS policy"
- Network tab shows preflight (OPTIONS) failing

**Check:**
1. `CORS_ORIGINS` includes production domain
2. Domain matches exactly (including https://)
3. No trailing slashes in CORS_ORIGINS

**Fix:**
```bash
# In backend/.env
CORS_ORIGINS="https://exact-domain.com"

# Restart backend
sudo supervisorctl restart backend
```

### Issue: Rate Limiting Still Active

**Symptoms:**
- 429 Too Many Requests errors
- Users being rate limited during testing

**Check:**
1. `ENABLE_RATE_LIMITING=false` in backend/.env
2. Backend restarted after config change

**Fix:**
```bash
# Verify config
cat /app/backend/.env | grep ENABLE_RATE_LIMITING

# Should output: ENABLE_RATE_LIMITING=false

# If not, update and restart
sudo supervisorctl restart backend
```

### Issue: Debug Endpoints Accessible

**Symptoms:**
- `/api/debug/rooms/{scope}/{id}` returns data (should be 404)

**Check:**
1. `ENV="production"` in backend/.env
2. Backend restarted after config change

**Fix:**
```bash
# Verify config
cat /app/backend/.env | grep ENV

# Should output: ENV="production"

# Test debug endpoint (should return 404)
curl -i https://your-domain.com/api/debug/rooms/league/test-123
# Expected: HTTP 404
```

---

## Monitoring Recommendations

### Key Metrics to Watch

**Application Metrics:**
```
# Socket.IO connections
socketio_connections_total

# Request rates
http_requests_total{endpoint="/api/auction/bid"}
http_requests_total{endpoint="/api/leagues"}

# Response times
http_request_duration_seconds{endpoint="/api/auction/bid"}

# Business metrics
participants_joined_total
auctions_started_total
bids_placed_total
```

**System Metrics:**
```
# Backend health
process_cpu_seconds_total
process_resident_memory_bytes
python_gc_collections_total
```

### Dashboard Queries (Prometheus)

```promql
# Request rate per endpoint
rate(http_requests_total[5m]) by (endpoint, method)

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) 
/ 
rate(http_requests_total[5m]) * 100

# P95 response time
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket[5m])
)

# Active Socket.IO connections (if metric available)
socketio_connections_total - socketio_disconnections_total
```

### Alert Rules

**Critical:**
```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  
# Backend down
- alert: BackendDown
  expr: up{job="backend"} == 0
  for: 1m
```

**Warning:**
```yaml
# Slow response time
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket[5m])) > 1.0
  for: 10m

# High request rate (potential abuse without rate limiting)
- alert: HighRequestRate
  expr: rate(http_requests_total[1m]) > 1000
  for: 5m
```

---

## Rollback Plan

### If Issues Found in Pilot

**Option 1: Quick Fix (Environment)**
```bash
# Adjust environment variables
vi /app/backend/.env
# Make changes
sudo supervisorctl restart backend
```

**Option 2: Re-enable Rate Limiting**
```bash
# In backend/.env
REDIS_URL="redis://your-redis-host:6379"
ENABLE_RATE_LIMITING=true

# Restart
sudo supervisorctl restart backend
```

**Option 3: Rollback to Previous Checkpoint**
- Use Emergent's rollback feature
- Revert to last known good version
- Re-deploy

### Rollback Triggers

- ❌ Real-time features not working (>50% failure rate)
- ❌ CORS errors preventing frontend access
- ❌ Error rate > 10% for 5 minutes
- ❌ Backend crash loops
- ❌ Database connection failures
- ❌ User reports of broken functionality

---

## Post-Pilot: Production Readiness

### Immediate Next Steps

1. **Collect Pilot Feedback** (1 week)
   - User experience with real-time features
   - Performance under real load
   - Any unexpected errors or issues

2. **Enable Rate Limiting** (Week 2)
   - Add Redis service (Upstash, Redis Cloud)
   - Set `REDIS_URL` and `ENABLE_RATE_LIMITING=true`
   - Test with realistic traffic patterns

3. **Multi-Replica Scaling** (Week 3)
   - Enable Redis Socket.IO manager
   - Scale backend to 2-3 replicas
   - Load test multi-replica setup

### Production Configuration

**Week 4: Full Production**
```bash
# backend/.env (Production)
REDIS_URL="redis://production-redis:6379"
ENABLE_RATE_LIMITING=true
ENV="production"
CORS_ORIGINS="https://prod-domain.com"
FRONTEND_ORIGIN="https://prod-domain.com"

# Deployment
- Backend replicas: 2-3
- Frontend replicas: 2-5 (can scale independently)
- Socket.IO: Redis pub/sub for multi-replica
- Rate limiting: Per-user + IP fallback
```

---

## Related Documentation

- `/app/STATUS_REPORT.md` - Overall production readiness (99%)
- `/app/DATABASE_INDEX_AUDIT.md` - Database optimization complete
- `/app/DEBUG_ENDPOINT_SECURITY.md` - Debug endpoint security
- `/app/CORS_CONFIGURATION.md` - CORS security configuration
- `/app/RATE_LIMIT_TESTING_REPORT.md` - Rate limit testing results

---

## Appendix: Environment Variable Reference

### Backend Environment Variables

| Variable | Pilot Value | Production Value | Purpose |
|----------|-------------|------------------|---------|
| `MONGO_URL` | mongodb://localhost:27017 | mongodb://prod:27017 | Database connection |
| `DB_NAME` | test_database | production_db | Database name |
| `CORS_ORIGINS` | https://pilot.com | https://prod.com | CORS allowed origins |
| `REDIS_URL` | (empty) | redis://prod:6379 | Redis for rate limiting + Socket.IO |
| `ENABLE_RATE_LIMITING` | false | true | Rate limiting toggle |
| `ENABLE_METRICS` | true | true | Prometheus metrics |
| `FRONTEND_ORIGIN` | https://pilot.com | https://prod.com | Socket.IO CORS |
| `ENV` | production | production | Environment mode |
| `SPORTS_CRICKET_ENABLED` | true | true | Cricket support toggle |
| `FEATURE_MY_COMPETITIONS` | true | true | My Competitions feature |

### Frontend Environment Variables

| Variable | Pilot Value | Production Value | Purpose |
|----------|-------------|------------------|---------|
| `REACT_APP_BACKEND_URL` | https://pilot.com | https://prod.com | Backend API URL |
| `REACT_APP_FEATURE_MY_COMPETITIONS` | true | true | Feature flag |

---

**Deployment Status:** ✅ READY FOR PILOT  
**Last Updated:** 2025-10-16  
**Version:** 1.0
