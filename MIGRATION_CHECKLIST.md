# Migration Checklist: Emergent → Railway

**Last Updated:** January 19, 2026  
**Estimated Time:** 1-2 days

---

## Phase 1: Pre-Migration Setup

### MongoDB Atlas (Your Account)
```
□ 1.1 Go to mongodb.com/cloud/atlas
□ 1.2 Create account or sign in
□ 1.3 Create new cluster:
      □ Tier: M10 Dedicated (~£45/month)
      □ Region: europe-west2 (London) ← CRITICAL for UK latency
      □ Name: sport-x-production
□ 1.4 Wait for cluster to provision (~5-10 minutes)
□ 1.5 Database Access → Add Database User:
      □ Username: sport-x-app
      □ Password: [generate and save securely]
      □ Role: readWriteAnyDatabase
□ 1.6 Network Access → Add IP Address:
      □ Click "Allow Access from Anywhere" (0.0.0.0/0)
      □ Note: Required for Railway's dynamic IPs
□ 1.7 Get connection string:
      □ Click "Connect" → "Connect your application"
      □ Copy string, replace <password> with actual password
      □ Add database name: /sport_x_production?
```

**Your MongoDB connection string:**
```
mongodb+srv://sport-x-app:<password>@sport-x-production.xxxxx.mongodb.net/sport_x_production?retryWrites=true&w=majority
```

### Railway Account
```
□ 1.8 Go to railway.app
□ 1.9 Create account (GitHub login recommended)
□ 1.10 Create new project
```

---

## Phase 2: Data Migration (Choose One)

### Option A: Fresh Start (Recommended for Pilot)
```
□ 2A.1 Skip data export
□ 2A.2 Plan to re-seed teams/players using app import features
□ 2A.3 Users will re-register (acceptable for pilot)
```

### Option B: Export/Import Existing Data
```
□ 2B.1 Export from Emergent MongoDB:
       mongodump --uri="[EMERGENT_MONGO_URL]" --out=./backup
□ 2B.2 Import to your Atlas cluster:
       mongorestore --uri="[YOUR_ATLAS_URL]" ./backup
□ 2B.3 Verify data imported correctly
```

---

## Phase 3: Backend Deployment

### Create Backend Service
```
□ 3.1 In Railway project, click "New Service"
□ 3.2 Select "GitHub Repo" 
□ 3.3 Connect your repository
□ 3.4 Set root directory to /backend (if monorepo)
```

### Configure Backend
```
□ 3.5 Settings → Start Command:
      uvicorn server:socket_app --host 0.0.0.0 --port $PORT

□ 3.6 Settings → Health Check Path:
      /api/health

□ 3.7 Variables → Add all environment variables:
      □ MONGO_URL=[your Atlas connection string]
      □ DB_NAME=sport_x_production
      □ JWT_SECRET=[generate secure 32+ char string]
      □ REDIS_URL=[your Redis Cloud URL]
      □ FOOTBALL_DATA_TOKEN=[your token]
      □ RAPIDAPI_KEY=[your key]
      □ SENTRY_DSN=https://618d64387dd9bd3a8748f3671b530981@o4510411309907968.ingest.de.sentry.io/4510734931722320
      □ CORS_ORIGINS=[frontend URL - add after frontend deployed]
      □ FRONTEND_ORIGIN=[frontend URL - add after frontend deployed]
```

### Verify Backend
```
□ 3.8 Deploy and wait for build to complete
□ 3.9 Test health endpoint:
      curl https://[your-backend].railway.app/api/health
      Expected: {"status":"healthy","database":"connected",...}
□ 3.10 Note the backend URL for frontend config
```

---

## Phase 4: Frontend Deployment

### Create Frontend Service
```
□ 4.1 In same Railway project, click "New Service"
□ 4.2 Select "GitHub Repo" (same repo)
□ 4.3 Set root directory to /frontend
```

### Configure Frontend
```
□ 4.4 Settings → Build Command:
      yarn install && yarn build

□ 4.5 Settings → Start Command:
      npx serve -s build -l $PORT

□ 4.6 Variables → Add:
      □ REACT_APP_BACKEND_URL=https://[your-backend].railway.app
      □ REACT_APP_SENTRY_ENVIRONMENT=production
```

### Update Backend CORS
```
□ 4.7 Go back to Backend service → Variables
□ 4.8 Update CORS_ORIGINS and FRONTEND_ORIGIN with frontend URL
□ 4.9 Redeploy backend
```

### Verify Frontend
```
□ 4.10 Deploy and wait for build
□ 4.11 Open frontend URL in browser
□ 4.12 Verify site loads without errors
```

---

## Phase 5: Critical Flow Testing

### Authentication
```
□ 5.1 Sign in with magic link
□ 5.2 Verify token received (dev mode) or email sent (if hardened)
□ 5.3 Complete sign in
□ 5.4 Verify user session persists
```

### League Management
```
□ 5.5 Create new competition
□ 5.6 Select teams
□ 5.7 Invite another user (use invite code)
□ 5.8 Second user joins league
```

### Auction (CRITICAL)
```
□ 5.9 Start auction with 2+ users
□ 5.10 Verify real-time updates (both users see bids)
□ 5.11 Complete auction
□ 5.12 Verify rosters assigned correctly
```

### Post-Auction
```
□ 5.13 View competition dashboard
□ 5.14 Import fixtures
□ 5.15 Trigger score update
□ 5.16 Verify points calculated
```

---

## Phase 6: Performance Validation

### Run Stress Test
```
□ 6.1 From local machine:
      pip install "python-socketio[asyncio_client]" aiohttp
      
□ 6.2 Small test:
      python multi_league_stress_test.py --leagues 2 --users 6 --teams 4 --url https://[your-backend].railway.app

□ 6.3 Medium test:
      python multi_league_stress_test.py --leagues 10 --users 8 --teams 4 --url https://[your-backend].railway.app
```

### Verify Targets Met
```
□ 6.4 p50 latency ≤200ms (was ~700ms on Emergent)
□ 6.5 Bid success ≥95% at 10 leagues
□ 6.6 No Socket.IO connection errors
```

---

## Phase 7: Domain & DNS (Optional for Pilot)

### Custom Domain
```
□ 7.1 Purchase domain (e.g., sportx.app)
□ 7.2 In Railway → Frontend service → Settings → Domains
□ 7.3 Add custom domain
□ 7.4 Configure DNS records as shown
□ 7.5 Wait for SSL certificate (automatic)
□ 7.6 Update Backend CORS_ORIGINS with new domain
```

---

## Phase 8: Monitoring Setup

### Sentry (Already Configured)
```
□ 8.1 Verify errors appearing in Sentry dashboard
□ 8.2 Trigger test error to confirm
□ 8.3 Set up alert rules if desired
```

### Railway Monitoring
```
□ 8.4 Review Railway metrics dashboard
□ 8.5 Set up usage alerts if desired
```

---

## Phase 9: Go-Live

### Final Checks
```
□ 9.1 All Phase 5 tests pass
□ 9.2 Stress test shows improved latency
□ 9.3 Sentry receiving events
□ 9.4 No console errors in browser
```

### Switch Over
```
□ 9.5 Update any external links to new URL
□ 9.6 Notify pilot users of new URL
□ 9.7 Monitor closely for 24-48 hours
```

### Keep Emergent as Backup
```
□ 9.8 Keep Emergent running for 1 week
□ 9.9 If issues, can revert quickly
□ 9.10 After stable period, sunset Emergent deployment
```

---

## Phase 10: Post-Migration

### Immediate (Week 1)
```
□ 10.1 Monitor Sentry daily for errors
□ 10.2 Check Railway metrics for resource usage
□ 10.3 Gather user feedback on performance
```

### Short-term (Before Pilot)
```
□ 10.4 Auth hardening (SendGrid email delivery)
□ 10.5 Verify Atlas automated backups enabled
□ 10.6 Update all documentation with new URLs
```

---

## Rollback Procedure

If critical issues arise:

```
1. □ Keep Emergent deployment running during transition
2. □ If Railway fails, direct users back to Emergent URL
3. □ MongoDB Atlas data is external - safe regardless
4. □ Investigate issue, fix, redeploy to Railway
5. □ Resume migration when stable
```

---

## Key Contacts & Resources

| Resource | Location |
|----------|----------|
| Railway Dashboard | https://railway.app/dashboard |
| MongoDB Atlas | https://cloud.mongodb.com |
| Redis Cloud | https://app.redislabs.com |
| Sentry | https://sentry.io |
| Migration Plan | `/app/MIGRATION_PLAN.md` |
| Stress Test Script | `/app/tests/multi_league_stress_test.py` |

---

## Notes

_Use this space to record any issues or decisions during migration:_

```
Date: 
Issue: 
Resolution: 

Date: 
Issue: 
Resolution: 
```
