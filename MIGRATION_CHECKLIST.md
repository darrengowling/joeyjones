# Migration Checklist: Emergent → Railway

**Last Updated:** January 22, 2026  
**Version:** 2.1  
**Estimated Time:** 1-2 hours (Phase 0) + 2-3 days (migration + validation + auth hardening)

---

## ⚠️ CRITICAL: Phase 0 Limitation

**Phase 0 as originally designed is NOT EXECUTABLE.**

Emergent's MongoDB runs on `localhost:27017` internally and is not accessible from external services like Railway. The original plan to test "Railway EU → Emergent MongoDB" cannot be performed.

### Revised Approach

**Skip Phase 0. Proceed directly to Phase 1 with M2 tier.**

Rationale:
- Stress tests already confirmed 700ms latency (evidence exists)
- Phased cost model (M2 → M10) manages risk
- Atlas alerts will trigger upgrade if M2 insufficient
- £36/mo savings doesn't justify workaround complexity

If M2 shows strain (CPU >70%, connections >400, latency >200ms), upgrade to M10.

---

## Phase 0: Root Cause Verification ~~(1-2 hours)~~ SKIPPED

~~**Goal:** Prove if latency is geography or database tier issue~~

**Status:** ❌ NOT EXECUTABLE - Emergent MongoDB not externally accessible

**Original steps preserved below for reference only. Do not attempt.**

<details>
<summary>Original Phase 0 (NOT EXECUTABLE - click to expand)</summary>

### Setup Railway Test Deployment (30 mins)

```
□ 0.1 Create Railway account
  - Go to railway.app
  - Sign up with GitHub
  - Verify email

□ 0.2 Create new project
  - Click "New Project"
  - Name: "sportx-phase0-test"
  
□ 0.3 Deploy backend only
  - Click "Deploy from GitHub repo"
  - Select your repo
  - Select backend directory if monorepo
  
□ 0.4 Configure environment variables
  - Copy ALL env vars from Emergent
  - CRITICAL: Use Emergent's MONGO_URL (not new Atlas cluster yet)
  - Add Railway domain to CORS_ORIGINS
  
□ 0.5 Wait for deployment
  - Watch build logs
  - Should complete in 3-5 minutes
  
□ 0.6 Get Railway backend URL
  - Copy from Railway dashboard
  - Format: https://sportx-backend-production-xxxx.up.railway.app
  
□ 0.7 Test health endpoint
  - curl https://your-railway-url.railway.app/api/health
  - Should return: {"status":"healthy","database":"connected"}
```

### Run Diagnostic Stress Test (30 mins)

```
□ 0.8 Update stress test command
python /app/tests/multi_league_stress_test.py \
  --backend-url https://your-railway-url.railway.app \
  --num-leagues 20
  
□ 0.9 Record results
  Current (Emergent US): _____ ms p50 latency
  Phase 0 (Railway EU + Emergent DB): _____ ms p50 latency
  
□ 0.10 Interpret results (check one):
  ☐ 150-250ms → Geography was issue → Use M0 (free) or M2 (£9/mo)
  ☐ 400-500ms → Mixed issue → Use M2 (£9/mo), upgrade to M10 later
  ☐ 650-700ms → Database throttling → Use M10 (£45/mo)
  
□ 0.11 Delete Phase 0 Railway deployment
  - Railway Dashboard → Project Settings → Delete Project
  - Keep results documented for reference
  
□ 0.12 Decide MongoDB tier for migration:
  Selected tier: _______ (M0/M2/M10)
  Monthly cost: £______
```

**STOP HERE until Phase 0 is complete. Do not proceed to Phase 1 without knowing which MongoDB tier to use.**

---

## Phase 1: MongoDB Atlas Setup (30 mins)

**Use the tier determined in Phase 0**

### Create Atlas Account & Cluster

```
□ 1.1 Go to mongodb.com/cloud/atlas/register
  - Sign up with your email
  - Verify email
  
□ 1.2 Create new organization
  - Name: "Sport X"
  - Skip inviting members
  
□ 1.3 Create new project
  - Name: "Sport X Production"
  - Skip adding members
  
□ 1.4 Create cluster (tier from Phase 0)
  - Click "Build a Database"
  - Select tier: _______ (M0/M2/M10 from Phase 0)
  - Cloud Provider: Google Cloud
  - Region: europe-west2 (London)
  - Cluster Name: sportx-production
  - Click "Create Cluster"
  
□ 1.5 Wait for cluster provisioning
  - M0/M2: ~5-10 minutes
  - M10: ~10-15 minutes
  - Status shows "Active" when ready
```

### Configure Security

```
□ 1.6 Create database user
  - Security → Database Access → Add New Database User
  - Authentication Method: Password
  - Username: sportx_admin
  - Password: (generate strong password, save to password manager)
  - Database User Privileges: "Atlas admin"
  - Click "Add User"
  
□ 1.7 Whitelist IP addresses
  - Security → Network Access → Add IP Address
  - Click "Allow access from anywhere" (0.0.0.0/0)
  - Comment: "Railway production - dynamic IPs require open access"
  - Note: Railway Starter plan uses dynamic IPs, cannot restrict further
  
□ 1.8 Get connection string
  - Click "Connect" on cluster
  - Choose "Connect your application"
  - Driver: Python 3.12 or later
  - Copy connection string
  - Format: mongodb+srv://sportx_admin:<password>@sportx-production.xxxxx.mongodb.net/
```

### Configure Connection String (HIGH PRIORITY)

```
□ 1.9 Enhance connection string with production parameters
  - Base: mongodb+srv://sportx_admin:PASSWORD@sportx-production.xxxxx.mongodb.net/sport_x
  - Add: ?maxPoolSize=50&connectTimeoutMS=10000&socketTimeoutMS=30000
  - Final: mongodb+srv://sportx_admin:PASSWORD@sportx-production.xxxxx.mongodb.net/sport_x?maxPoolSize=50&connectTimeoutMS=10000&socketTimeoutMS=30000
  
  Why these parameters:
  - maxPoolSize=50: Prevents connection exhaustion under load
  - connectTimeoutMS=10000: 10s connection timeout
  - socketTimeoutMS=30000: 30s socket timeout
  
□ 1.10 Save to password manager
  - Store: username, password, full connection string
```

### Create Database Indexes (HIGH PRIORITY)

**DO NOT SKIP - Critical for performance**

```
□ 1.11 Connect to cluster via MongoDB Compass or mongosh
  - Download Compass: https://www.mongodb.com/products/compass
  - Or use mongosh CLI
  - Paste connection string from 1.9
  
□ 1.12 Create database
  - use sport_x_production
  
□ 1.13 Create indexes (copy from Migration Plan v4.3)
  
  Core Collections:
  ☐ db.users.createIndex({ "id": 1 }, { unique: true })
  ☐ db.users.createIndex({ "email": 1 }, { unique: true })
  ☐ db.leagues.createIndex({ "id": 1 }, { unique: true })
  ☐ db.leagues.createIndex({ "inviteToken": 1 }, { unique: true })
  ☐ db.leagues.createIndex({ "commissionerId": 1 })
  ☐ db.leagues.createIndex({ "status": 1 })
  ☐ db.league_participants.createIndex({ "leagueId": 1, "userId": 1 }, { unique: true })
  ☐ db.league_participants.createIndex({ "leagueId": 1 })
  ☐ db.league_participants.createIndex({ "userId": 1 })
  ☐ db.assets.createIndex({ "id": 1 }, { unique: true })
  ☐ db.assets.createIndex({ "sportKey": 1 })
  ☐ db.assets.createIndex({ "externalId": 1 })
  ☐ db.assets.createIndex({ "competitionShort": 1 })
  ☐ db.assets.createIndex({ "sportKey": 1, "competitionShort": 1 })
  
  Auction Collections:
  ☐ db.auctions.createIndex({ "id": 1 }, { unique: true })
  ☐ db.auctions.createIndex({ "leagueId": 1 })
  ☐ db.auctions.createIndex({ "status": 1 })
  ☐ db.bids.createIndex({ "id": 1 }, { unique: true })
  ☐ db.bids.createIndex({ "auctionId": 1 })
  ☐ db.bids.createIndex({ "auctionId": 1, "clubId": 1 })
  ☐ db.bids.createIndex({ "userId": 1 })
  
  Scoring Collections:
  ☐ db.fixtures.createIndex({ "id": 1 }, { unique: true })
  ☐ db.fixtures.createIndex({ "leagueId": 1 })
  ☐ db.fixtures.createIndex({ "leagueId": 1, "status": 1 })
  ☐ db.fixtures.createIndex({ "externalMatchId": 1 })
  ☐ db.league_points.createIndex({ "leagueId": 1, "clubId": 1 }, { unique: true })
  ☐ db.league_points.createIndex({ "leagueId": 1 })
  ☐ db.standings.createIndex({ "leagueId": 1 }, { unique: true })
  
  Utility Collections:
  ☐ db.magic_links.createIndex({ "token": 1 }, { unique: true })
  ☐ db.magic_links.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 })
  ☐ db.debug_reports.createIndex({ "referenceId": 1 }, { unique: true })
  ☐ db.debug_reports.createIndex({ "auctionId": 1 })
  
□ 1.14 Verify indexes created
  - db.auctions.getIndexes()
  - db.bids.getIndexes()
  - Check each collection has expected indexes
```

### Set Up Monitoring Alerts (If using M0/M2)

**Skip this if you chose M10 after Phase 0**

```
□ 1.15 Configure Atlas alerts for M0/M2 monitoring
  - Atlas Dashboard → Alerts → Add Alert
  
  Alert 1: CPU Usage
  ☐ Metric: CPU Usage (%)
  ☐ Threshold: > 70% for 10 minutes
  ☐ Notification: Email to your address
  
  Alert 2: Connections
  ☐ Metric: Connections
  ☐ Threshold: > 400
  ☐ Notification: Email
  
  Alert 3: Query Execution Time (p99)
  ☐ Metric: Query Targeting - Scanned Objects / Returned
  ☐ Threshold: > 1000ms
  ☐ Notification: Email
  
  Why: These alerts tell you when to upgrade M0/M2 → M10
```

---

## Phase 2: Railway Project Setup (20 mins)

### Create Production Project

```
□ 2.1 Go to railway.app (or use existing account from Phase 0)
  - Sign in with GitHub
  
□ 2.2 Create new project
  - Click "New Project"
  - Name: "Sport X Production"
  
□ 2.3 Connect GitHub repository
  - Click "Deploy from GitHub repo"
  - Select your production repo
  - If monorepo, specify backend directory
  
□ 2.4 Configure auto-deploy
  - Service Settings → Source
  - Branch: main
  - Enable "Auto Deploy" checkbox
  - Verify GitHub webhook is active (check repo settings)
```

---

## Phase 3: Backend Service Configuration (30 mins)

### Verify Redis Connection Format (HIGH PRIORITY)

```
□ 3.0 Check Redis Cloud connection string format
  - Login to Redis Cloud dashboard (app.redislabs.com)
  - Go to your database → Configuration tab
  - Find "Public endpoint" section
  - Copy the connection string exactly as shown
  
  ☐ Check format:
    - If starts with "redis://" → Standard connection, use as-is
    - If starts with "rediss://" → SSL enabled, use as-is
    - If just host:port → Add "redis://" prefix
    
  ☐ Verify TLS/SSL setting matches:
    - Redis Cloud dashboard shows "TLS" enabled? → Use rediss://
    - Redis Cloud dashboard shows "TLS" disabled? → Use redis://
    
  ☐ Test connection locally (optional but recommended):
    redis-cli -u "YOUR_REDIS_URL" ping
    Expected response: PONG
    
  □ Record final Redis URL format: _______________________
```

### Configure Environment Variables

```
□ 3.1 Add all environment variables
  Railway Dashboard → Backend Service → Variables
  
  Database (NEW Atlas cluster):
  ☐ MONGO_URL=mongodb+srv://sportx_admin:PASSWORD@sportx-production.xxxxx.mongodb.net/sport_x?maxPoolSize=50&connectTimeoutMS=10000&socketTimeoutMS=30000
  ☐ DB_NAME=sport_x_production
  
  Auth:
  ☐ JWT_SECRET=(generate new 32+ char secret, save to password manager)
  
  Redis (existing Redis Cloud - use format verified in 3.0):
  ☐ REDIS_URL=(paste exact URL from Phase 3.0)
  
  APIs:
  ☐ FOOTBALL_DATA_TOKEN=(from existing env)
  ☐ RAPIDAPI_KEY=(from existing env)
  
  Sentry:
  ☐ SENTRY_DSN=https://618d64387dd9bd3a8748f3671b530981@o4510411309907968.ingest.de.sentry.io/4510734931722320
  ☐ SENTRY_ENVIRONMENT=production
  
  Production settings (temporary - will update after frontend deployed):
  ☐ CORS_ORIGINS=http://localhost:3000
  ☐ FRONTEND_ORIGIN=http://localhost:3000
  
  Request timeout (HIGH PRIORITY):
  ☐ REQUEST_TIMEOUT_SECONDS=30
  
□ 3.2 Configure service settings
  - Start Command: uvicorn server:socket_app --host 0.0.0.0 --port $PORT
  - Health Check Path: /api/health
  - Expected Response: HTTP 200
  - Replicas: 1 (IMPORTANT: Socket.IO requires sticky sessions)
  
□ 3.3 Configure build settings
  - Build Command: (leave default or specify if needed)
  - Install Command: pip install -r requirements.txt
  
□ 3.4 Deploy backend
  - Click "Deploy"
  - Wait for build to complete (3-5 minutes)
  - Check logs for errors
  
□ 3.5 Verify deployment
  - Get Railway backend URL from dashboard
  - Test: curl https://your-backend.railway.app/api/health
  - Should return: {"status":"healthy","database":"connected"}
  - Check connection to MongoDB Atlas (not Emergent)
```

### Implement Request Timeout (HIGH PRIORITY)

**Choose one implementation method:**

```
□ 3.6 Implement request timeout

  Option A: Environment variable (simple, already added in 3.1)
  - Requires custom middleware (add to server.py)
  - See Migration Plan v4.3 for middleware code
  
  Option B: Per-route timeout (recommended for pilot)
  - Add to bid endpoint only:
  
  @api_router.post("/auction/{auction_id}/bid")
  async def place_bid(...):
      try:
          result = await asyncio.wait_for(
              process_bid(...), 
              timeout=10.0  # 10 seconds for bid processing
          )
      except asyncio.TimeoutError:
          raise HTTPException(504, "Bid processing timeout")
      return result
  
  ☐ Implement chosen option
  ☐ Test with simulated slow DB (add time.sleep(15) in bid processing)
  ☐ Verify timeout triggers and returns 504 error
  ☐ Remove test delay
```

### Implement Rate Limiting (HIGH PRIORITY)

```
□ 3.7 Install rate limiting library
  - Add to requirements.txt: slowapi==0.1.9
  - Redeploy to install
  
□ 3.8 Add rate limiting to server.py
  
  from slowapi import Limiter
  from slowapi.util import get_remote_address
  
  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  
□ 3.9 Add rate limits to critical endpoints
  
  # Auth endpoints (already planned)
  @api_router.post("/auth/magic-link")
  @limiter.limit("3/hour")  # 3 requests per hour per email
  async def request_magic_link(...):
      ...
  
  # Bid endpoint (NEW - prevent abuse)
  @api_router.post("/auction/{auction_id}/bid")
  @limiter.limit("30/minute")  # 30 bids per minute per user
  async def place_bid(...):
      ...
  
  # General API limit (optional but recommended)
  @app.middleware("http")
  async def rate_limit_middleware(request, call_next):
      # 100 requests per minute per IP
      ...
  
□ 3.10 Test rate limiting
  - Send 35 requests in 1 minute to bid endpoint
  - Should get 429 "Too Many Requests" after 30 requests
  - Verify error message is clear
```

---

## Phase 4: Frontend Service Configuration (20 mins)

### Deploy Frontend

```
□ 4.1 Create frontend service in Railway
  - Railway Dashboard → New Service
  - Connect same GitHub repo
  - Specify frontend directory if monorepo
  
□ 4.2 Configure build settings
  - Build Command: yarn install --frozen-lockfile && yarn build
  - Start Command: npx serve -s build -l $PORT
  
□ 4.3 Add environment variables
  ☐ REACT_APP_BACKEND_URL=https://your-backend.railway.app
  ☐ REACT_APP_SENTRY_DSN=(leave blank or add if you have frontend Sentry)
  ☐ REACT_APP_SENTRY_ENVIRONMENT=production
  
□ 4.4 Deploy frontend
  - Click "Deploy"
  - Wait for build (5-10 minutes for React build)
  - Check logs for errors
  
□ 4.5 Get frontend URL
  - Copy from Railway dashboard
  - Format: https://sportx-frontend-production-xxxx.up.railway.app
```

### Update Backend CORS (Fix Chicken-Egg Problem)

```
□ 4.6 Update backend environment variables
  - Railway Dashboard → Backend Service → Variables
  - Update CORS_ORIGINS: https://your-frontend.railway.app
  - Update FRONTEND_ORIGIN: https://your-frontend.railway.app
  - Backend will auto-redeploy
  
□ 4.7 Verify CORS
  - Open frontend URL in browser
  - Open browser console (F12)
  - Should not see CORS errors
  - Test login flow
```

---

## Phase 5: Validation & Testing (1-2 hours)

### Test Critical Flows

```
□ 5.1 Test authentication
  ☐ Request magic link
  ☐ Receive email (if SendGrid configured, otherwise check logs for token)
  ☐ Click link, verify login works
  ☐ Check JWT token in browser storage
  
□ 5.2 Test league creation
  ☐ Create new league
  ☐ Verify league appears in database
  ☐ Check league settings save correctly
  
□ 5.3 Test league joining
  ☐ Generate invite link
  ☐ Join from different browser/incognito
  ☐ Verify participant added to league
  
□ 5.4 Test auction flow (manual)
  ☐ Start auction
  ☐ Place bid
  ☐ Verify bid appears in UI
  ☐ Verify bid saved to database
  ☐ Verify Socket.IO updates work (bid shows for all users)
  
□ 5.5 Test Socket.IO connections (thorough)
  - Open browser console (F12)
  - Look for Socket.IO connection logs
  - Should see: "Socket connected: <socket_id>"
  - Should NOT see frequent disconnects/reconnects
  
  Verification steps:
  ☐ Open frontend in 2 browser tabs (or 2 different browsers)
  ☐ Both tabs in same auction room
  ☐ Place bid in tab 1 → Should immediately appear in tab 2
  ☐ Place 10 rapid bids (1 per second) in tab 1
  ☐ Verify all 10 bids appear in tab 2 in correct order
  ☐ Check console for any Socket.IO errors or reconnects
  ☐ If >1 disconnect in 10 bids, investigate before proceeding
```

### Security State Verification

```
□ 5.6 Verify current security state
  ☐ Auth is in DEV MODE (token in API response)
  ☐ This is EXPECTED for stress testing
  ☐ Document: "Auth hardening required before pilot invitations"
  ☐ Set reminder: Complete Phase 11 before sending pilot invites
```

### Run Stress Test

```
□ 5.7 Prepare stress test
  - Update stress test script with new Railway backend URL
  - Verify test users exist in database
  
□ 5.8 Run stress test (20 leagues)
  python /app/tests/multi_league_stress_test.py \
    --backend-url https://your-backend.railway.app \
    --num-leagues 20
    
□ 5.9 Record results
  p50 latency: _____ ms (target: ≤200ms)
  p99 latency: _____ ms (target: ≤1500ms)
  Bid success rate: _____ % (target: ≥95%)
  
  ☐ Results meet targets
  ☐ If results don't meet targets, check:
    - Are database indexes created? (Phase 1.13)
    - Is connection pool configured? (Phase 1.9)
    - Check Railway logs for errors
    - Check Atlas metrics for CPU/connection issues
```

---

## Phase 6: Performance Monitoring Setup (30 mins)

### Railway Alerts

```
□ 6.1 Configure Railway alerts
  - Railway Dashboard → Project Settings → Alerts
  
  ☐ Memory usage > 80% (15-min average)
  ☐ CPU usage > 80% (5-min average)
  ☐ Error rate > 5% (1-min window)
  ☐ Deployment failures
  
□ 6.2 Set notification email
  - Add your email address
  - Test by triggering a test alert
```

### Sentry Alerts

```
□ 6.3 Configure Sentry alerts
  - Go to sentry.io → Your Project → Alerts
  
  ☐ New error type appears
  ☐ Error count > 10 in 1 hour
  ☐ Critical errors (500s, database connection failures)
  ☐ Socket.IO connection failures
  
□ 6.4 Test Sentry integration
  - Trigger a test error in backend
  - Verify appears in Sentry dashboard
  - Verify alert email received
```

### MongoDB Atlas Monitoring

```
□ 6.5 Verify Atlas alerts (if M0/M2 from Phase 1.15)
  - Atlas Dashboard → Alerts
  - Verify 3 alerts configured
  - Test by temporarily reducing threshold
  
□ 6.6 Establish baseline metrics
  - Atlas Dashboard → Metrics
  - Record current values:
    CPU usage: _____ %
    Connections: _____
    Query execution time (p50): _____ ms
    Query execution time (p99): _____ ms
  
  ☐ Screenshot metrics for comparison later
```

---

## Phase 7: Backup & Recovery (30 mins)

### Verify Backups Enabled

```
□ 7.1 Check Atlas backup configuration
  - Atlas Dashboard → Backup
  - M0: ❌ No automated backups (manual export only)
  - M2: ✅ Basic snapshots (24-hour intervals)
  - M10: ✅ Continuous backups + point-in-time restore
  
□ 7.2 If using M0 (no backups)
  - Document backup strategy: Manual exports before major changes
  - Set calendar reminder: Weekly manual export
  
  Export options:
  Option A - MongoDB Compass (GUI, easier):
    - Connect to cluster
    - Select database → Collection → Export Collection
    - Choose JSON format
    - Save to local backup folder
    
  Option B - mongodump CLI (requires MongoDB tools installed):
    mongodump --uri="mongodb+srv://..." --out=/backups/$(date +%Y%m%d)/
  
□ 7.3 If using M2 or M10
  - Verify backup schedule in Atlas dashboard
  - Retention: 7 days (M2) or configurable (M10)
```

### Test Backup Restore (HIGH PRIORITY - If M10 only)

**Skip this if using M0/M2 (no point-in-time restore)**

```
□ 7.4 Wait 24 hours after migration
  - Atlas needs time to create first backup snapshot
  - Set calendar reminder for 24 hours from now
  
□ 7.5 Test restore to temporary cluster
  - Atlas Dashboard → Backup → Restore
  - Select: Latest snapshot
  - Destination: "Restore to a new cluster"
  - Cluster tier: M0 (free) for testing
  - Region: Same as production
  - Click "Restore"
  
□ 7.6 Wait for restore to complete
  - Takes ~10-30 minutes depending on data size
  - Monitor progress in Atlas dashboard
  
□ 7.7 Verify restored data
  - Connect to test cluster via Compass/mongosh
  - Check:
    ☐ User count matches production
    ☐ League count matches production
    ☐ Sample queries return expected data
    ☐ Indexes are present (getIndexes())
  
□ 7.8 Delete test cluster
  - Atlas Dashboard → Test Cluster → Delete
  - Confirm deletion to avoid charges
  
□ 7.9 Document restore procedure
  - Add to runbook: "Tested restore on [date], took [X] minutes"
  - Note any issues encountered
```

---

## Phase 8: Documentation & Handoff (20 mins)

### Update Documentation

```
□ 8.1 Update environment variable documentation
  - Document new Railway URLs
  - Document MongoDB Atlas connection string (without password)
  - Document any new env vars added
  
□ 8.2 Update README
  - Replace Emergent references with Railway
  - Update deployment instructions
  - Add section: "Emergency: How to rollback to Emergent"
  
□ 8.3 Document monitoring dashboards
  - Railway: https://railway.app/project/[your-project-id]
  - Sentry: https://sentry.io/organizations/[your-org]/projects/[project]
  - Atlas: https://cloud.mongodb.com/v2/[project-id]
  
□ 8.4 Create runbook for common issues
  - High CPU on Atlas → Upgrade to M10
  - Connection pool exhaustion → Check MONGO_URL has maxPoolSize=50
  - Socket.IO disconnects → Check Railway replicas = 1
  - Slow bids → Check indexes exist, check Atlas query performance
```

### Create Rollback Plan

```
□ 8.5 Document rollback procedure
  1. Emergent is still running (keep for 30 days)
  2. To rollback: Update frontend REACT_APP_BACKEND_URL to Emergent URL
  3. Redeploy frontend
  4. Data: MongoDB Atlas is external, data persists
  5. Timeline: < 1 hour rollback time
  
□ 8.6 Keep Emergent credentials safe
  - Store in password manager
  - Label: "Emergency rollback only"
  - Delete Emergent after 30 days of stable Railway operation
```

---

## Phase 9: Pre-Pilot Readiness (1 hour)

### Final Pre-Pilot Checks

```
□ 9.1 Verify all HIGH PRIORITY items completed
  ☐ Connection pool sizing configured (Phase 1.9)
  ☐ Database indexes created (Phase 1.13)
  ☐ Request timeout implemented (Phase 3.6)
  ☐ Rate limiting implemented (Phase 3.9)
  ☐ Backup restore tested (Phase 7.5) - if M10 only
  
□ 9.2 Verify monitoring is working
  ☐ Railway alerts sending emails
  ☐ Sentry capturing errors
  ☐ Atlas alerts configured (if M0/M2)
  
□ 9.3 Verify performance targets met
  ☐ p50 latency ≤200ms
  ☐ p99 latency ≤1500ms
  ☐ Bid success rate ≥95%
  
□ 9.4 Security state check
  ☐ Auth is in DEV MODE (expected)
  ☐ Phase 11 (auth hardening) scheduled for next 24-48 hours
  ☐ NO pilot invitations sent yet
```

---

## Phase 10: Migration Complete Checklist

```
□ 10.1 All services deployed and healthy
  ☐ Backend responding to health checks
  ☐ Frontend loading correctly
  ☐ Database connected and indexed
  ☐ Socket.IO connections working
  
□ 10.2 Performance validated
  ☐ Stress test passed with target metrics
  ☐ Manual testing of critical flows passed
  ☐ No critical errors in Sentry
  
□ 10.3 Monitoring active
  ☐ Railway alerts configured
  ☐ Sentry alerts configured
  ☐ Atlas alerts configured (if M0/M2)
  
□ 10.4 Documentation updated
  ☐ URLs documented
  ☐ Runbook created
  ☐ Rollback plan documented
  
□ 10.5 HIGH PRIORITY items complete
  ☐ Connection pool configured
  ☐ Indexes created
  ☐ Request timeout implemented
  ☐ Rate limiting implemented
  ☐ Backup tested (if M10) or manual export scheduled (if M0)
```

---

## Phase 11: Auth Hardening (BEFORE Pilot Invitations)

**DO NOT SEND PILOT INVITATIONS UNTIL THIS PHASE IS COMPLETE**

**Timeline:** Complete within 24-48 hours after Phase 10

### Setup Email Delivery

```
□ 11.1 Choose email provider
  ☐ Option A: SendGrid (recommended, generous free tier)
  ☐ Option B: Resend (modern alternative)
  ☐ Option C: Amazon SES (if using AWS)
  
□ 11.2 Create SendGrid account (if chosen)
  - Go to sendgrid.com
  - Sign up for free tier (100 emails/day)
  - Verify email address
  
□ 11.3 Create API key
  - SendGrid Dashboard → Settings → API Keys
  - Create new key with "Mail Send" permissions
  - Copy key (save to password manager)
  
□ 11.4 Configure sender authentication
  - SendGrid → Settings → Sender Authentication
  - Option A: Single Sender Verification (quick, for testing)
  - Option B: Domain Authentication (professional, for production)
  - Verify sender email (e.g., noreply@sportx.app)
  
□ 11.5 Add SendGrid env var to Railway
  - Railway → Backend Service → Variables
  - Add: SENDGRID_API_KEY=your-key-here
  - Redeploy backend
```

### Implement Email-Only Token Delivery

```
□ 11.6 Update auth endpoint code
  
  Before (DEV MODE):
  return {
      "message": "Magic link sent",
      "token": token  # ❌ REMOVE THIS
  }
  
  After (PRODUCTION):
  return {
      "message": "Magic link sent to email"
      # Token only in email, not in response
  }
  
□ 11.7 Implement email sending
  
  import sendgrid
  from sendgrid.helpers.mail import Mail, Email, To, Content
  
  def send_magic_link_email(email: str, token: str):
      sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
      
      magic_link = f"{FRONTEND_ORIGIN}/auth/verify?token={token}"
      
      message = Mail(
          from_email=Email("noreply@sportx.app"),
          to_emails=To(email),
          subject="Your Sport X Login Link",
          html_content=Content("text/html", f"""
              <h2>Login to Sport X</h2>
              <p>Click the link below to login:</p>
              <a href="{magic_link}">{magic_link}</a>
              <p>This link expires in 15 minutes.</p>
              <p>If you didn't request this, please ignore this email.</p>
          """)
      )
      
      response = sg.send(message)
      return response.status_code == 202
  
□ 11.8 Deploy email implementation
  - Commit changes
  - Push to main branch
  - Railway auto-deploys
  - Monitor logs for email sending
  
□ 11.9 Test email delivery
  ☐ Request magic link via API
  ☐ Check email inbox (including spam folder)
  ☐ Verify email received within 30 seconds
  ☐ Click magic link, verify login works
  ☐ Verify token NOT in API response
```

### Update Stress Test for Hardened Auth

```
□ 11.10 Update stress test script
  
  Problem: Stress test currently expects token in response (DEV MODE)
  Solution: Add --skip-auth flag (recommended for speed)
  
  Recommended approach (Option A - quick fix):
  python /app/tests/multi_league_stress_test.py \
    --backend-url https://your-backend.railway.app \
    --num-leagues 20 \
    --skip-auth  # Uses pre-created test users with tokens
  
  Alternative (Option B - nice to have post-pilot):
  - Create test email addresses (user1@test.sportx.app, etc.)
  - Configure email catch-all for test domain
  - Parse emails for tokens in test suite
  
  ☐ Implement Option A (--skip-auth flag)
  ☐ Verify stress test still works with hardened auth
  ☐ Document: Option B is enhancement for post-pilot
```

### Rate Limiting Verification

```
□ 11.11 Verify auth rate limiting is active
  - Already implemented in Phase 3.9
  - Should be: 3 requests/hour per email
  
□ 11.12 Test rate limiting
  ☐ Request magic link 3 times for same email
  ☐ 4th request should return 429 "Too Many Requests"
  ☐ Verify clear error message shown to user
  ☐ Wait 1 hour, verify rate limit resets
```

### Security Audit

```
□ 11.13 Verify auth hardening complete
  ☐ Token NOT returned in API response
  ☐ Magic link only sent via email
  ☐ Rate limiting active on auth endpoint (3/hour)
  ☐ Rate limiting active on bid endpoint (30/minute)
  ☐ JWT secret is strong (32+ characters)
  ☐ Token expiry configured (15 minutes default)
  
□ 11.14 Test security with fresh eyes
  ☐ Open frontend in incognito window
  ☐ Request magic link
  ☐ Open browser DevTools → Network tab
  ☐ Verify API response does NOT contain token
  ☐ Check email, verify token only there
  ☐ Try to reuse token after expiry → should fail
  
□ 11.15 Update security state documentation
  ☐ Migration Plan: Update "Security Considerations" section
  ☐ Mark: Auth now in HARDENED MODE
  ☐ Document: Ready for external pilot users
```

---

## Phase 12: Pilot Readiness Final Checks

**YOU ARE NOW READY TO SEND PILOT INVITATIONS**

### Pre-Launch Checklist

```
□ 12.1 Infrastructure validated
  ☐ Railway services running stable for 24+ hours
  ☐ No critical errors in Sentry in last 24 hours
  ☐ Database performance within targets
  ☐ Monitoring alerts not triggering
  
□ 12.2 Auth system hardened
  ☐ Phase 11 complete (email-only token delivery)
  ☐ Rate limiting tested and working
  ☐ Test login flow from external email (not test accounts)
  
□ 12.3 Performance validated
  ☐ Stress test results meet targets
  ☐ Manual testing of full user journey complete
  ☐ Socket.IO real-time updates working
  
□ 12.4 Support infrastructure ready
  ☐ Error monitoring active (Sentry)
  ☐ Performance monitoring active (Railway + Atlas)
  ☐ Runbook created for common issues
  ☐ Your contact info available for emergency escalations
  
□ 12.5 Data safety verified
  ☐ Backups enabled (M2/M10) or manual export scheduled (M0)
  ☐ Backup restore tested (if M10)
  ☐ Rollback plan documented and understood
```

### Pilot Invitation Preparation

```
□ 12.6 Prepare pilot user list
  - Owen McVeigh Foundation: ____ users
  - Additional charity partners: ____ users
  - Total pilot users: ____ users
  
□ 12.7 Create invitation email template
  Subject: You're invited to Sport X pilot
  
  Body:
  - Welcome message
  - What Sport X is
  - How to get started
  - Login link: https://your-frontend.railway.app
  - Support contact (your email)
  - Feedback request
  
□ 12.8 Set expectations internally
  ☐ Monitor error rates closely in first 48 hours
  ☐ Be available for support questions
  ☐ Plan for rapid response to issues
  ☐ Daily check-ins on pilot progress
```

### Launch Monitoring Plan

```
□ 12.9 First 24 hours monitoring
  - Check Sentry every 2 hours
  - Monitor Railway metrics every 4 hours
  - Watch Atlas connections/CPU (if M0/M2)
  - Respond to user feedback within 2 hours
  
□ 12.10 First week monitoring
  - Daily Sentry review
  - Daily Railway metrics check
  - Monitor Atlas alerts (if M0/M2, watch for upgrade triggers)
  - Weekly performance review meeting
  
□ 12.11 Success metrics tracking
  Track weekly:
  ☐ Active users
  ☐ Active leagues
  ☐ Total bids placed
  ☐ Average bid latency
  ☐ Error rate
  ☐ User feedback themes
```

---

## Migration Complete 🎉

### Final Sign-Off

```
□ All phases complete (0-12)
□ All HIGH PRIORITY items addressed
□ Performance targets met
□ Security hardened
□ Monitoring active
□ Documentation updated
□ Pilot invitations ready to send

Migration completed by: _________________
Date: _________________
Railway backend URL: _________________
Railway frontend URL: _________________
MongoDB tier: _______ (M0/M2/M10)
Total cost: £______ /month

Next steps:
1. Send pilot invitations
2. Monitor closely for first 48 hours
3. Collect user feedback
4. If using M0/M2, watch for upgrade triggers
5. Schedule post-pilot review meeting
```

---

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: High latency (>300ms) after migration**
```
Check:
1. Are database indexes created? (Phase 1.13)
2. Is connection pool configured? (Phase 1.9 - check MONGO_URL)
3. Railway region set to EU-West? (should show London)
4. Atlas cluster in europe-west2? (check cluster settings)

Solution: Review Phase 1 and Phase 3 configurations
```

**Issue: Connection pool exhaustion errors**
```
Symptoms: "ServerSelectionTimeoutError" in logs
Check:
1. MONGO_URL includes ?maxPoolSize=50
2. Atlas connections graph in dashboard
3. If using M0/M2, might be hitting 500 connection limit

Solution: 
- M0/M2: Upgrade to M10 (Phase 1.4 upgrade procedure)
- M10: Increase maxPoolSize to 100
```

**Issue: Socket.IO disconnects frequently**
```
Symptoms: Users report bids not appearing, frequent "reconnecting" messages
Check:
1. Railway replicas = 1 (Socket.IO needs sticky sessions)
2. Browser console shows connection errors
3. CORS configured correctly

Solution: Railway settings → Replicas = 1, restart service
```

**Issue: Rate limiting blocking legitimate users**
```
Symptoms: Users can't login, get 429 errors
Check:
1. Rate limit thresholds (3/hour for auth, 30/min for bids)
2. Are users sharing same IP? (office/school network)

Solution: 
- Temporarily increase limit during testing
- Use token-based rate limiting instead of IP-based (post-pilot)
```

**Issue: Emails not sending**
```
Symptoms: Users request login but don't receive email
Check:
1. SendGrid API key valid (test in SendGrid dashboard)
2. Sender email verified in SendGrid
3. Check spam folders
4. Backend logs show email sending attempt

Solution: Review Phase 11.2-11.5, re-verify sender authentication
```

**Issue: M0/M2 performance degrading**
```
Symptoms: Atlas alerts triggering, CPU >70%, connections >400
Check:
1. Atlas dashboard → Metrics
2. Number of active users/leagues
3. Query performance (slow queries)

Solution: Upgrade to M10 following Phase 1.4 procedure:
1. Create M10 cluster
2. Use Atlas migration tool to copy data
3. Update MONGO_URL in Railway
4. Verify indexes exist on new cluster
5. Test before switching traffic
```

**Issue: Redis connection failures**
```
Symptoms: Socket.IO not working, "Redis connection refused" in logs
Check:
1. REDIS_URL format correct (redis:// vs rediss://)
2. Redis Cloud dashboard shows database is running
3. Connection string matches exactly what Redis Cloud shows

Solution:
- Verify format in Phase 3.0
- Test with redis-cli locally
- Check Redis Cloud firewall settings (should allow all IPs)
```

---

## Appendix: MongoDB Tier Upgrade Procedure

**When to upgrade M0/M2 → M10:**
- CPU consistently >70%
- Connections approaching 400
- Query latency p50 >200ms
- Adding 3rd-5th charity partner
- Atlas alerts triggering repeatedly

**Upgrade steps:**
```
1. Create M10 cluster in same region (europe-west2)
   - Atlas → Create New Cluster
   - Tier: M10
   - Region: europe-west2 (same as M0/M2)
   - Name: sportx-production-m10

2. Migrate data using Atlas Live Migration
   - Atlas → M10 Cluster → Migration
   - Source: Your M0/M2 cluster
   - Click "I'm ready to migrate"
   - Wait for sync (10-30 minutes)

3. Verify data migrated
   - Connect to M10 cluster
   - Verify counts: users, leagues, auctions, bids
   - Check sample queries return expected data

4. Create indexes on M10 cluster
   - Run all index creation commands from Phase 1.13
   - Verify: db.auctions.getIndexes()

5. Update Railway MONGO_URL
   - Get M10 connection string
   - Add: ?maxPoolSize=50&connectTimeoutMS=10000&socketTimeoutMS=30000
   - Update Railway env var
   - Backend auto-redeploys

6. Verify production using M10
   - Check Railway logs: "Connected to MongoDB"
   - Test login, create league, place bid
   - Monitor Atlas M10 metrics

7. Delete M0/M2 cluster (after 48 hours of stable M10)
   - Atlas → Old Cluster → Delete
   - Saves cost if you were on M2
```

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | Jan 22, 2026 | Added Phase 3.0 Redis SSL verification step. Fixed Phase 1.7 Railway IP note. Enhanced Phase 5.5 Socket.IO testing. Added Atlas UI export option for M0 backups. Clarified Phase 11.10 recommendation. Added Redis troubleshooting. |
| 2.0 | Jan 22, 2026 | Complete rewrite: Added Phase 0 diagnostic test, HIGH PRIORITY items (connection pooling, timeouts, rate limiting, backup testing), auth hardening phase, pilot readiness checklist, troubleshooting guide, M0/M2→M10 upgrade procedure |
| 1.0 | Dec 21, 2025 | Initial checklist |
