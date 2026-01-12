# Migration Plan: Emergent → Self-Hosted (Railway)

**Created:** December 13, 2025  
**Last Updated:** January 12, 2026  
**Status:** PLANNING - Infrastructure bottlenecks identified via stress testing  
**Target Platform:** Railway  
**Reason:** Control and stakeholder credibility after production outages

---

## ⚠️ Critical Update: Stress Test Findings (January 2026)

**Stress testing revealed infrastructure bottlenecks that must be addressed before or during migration:**

| Issue | Current Impact | Migration Implication |
|-------|---------------|----------------------|
| **MongoDB Latency** | ~700ms baseline (shared Emergent cluster) | Must provision dedicated Atlas cluster |
| **Redis Connections** | Upgraded to 256 (was 30) - now adequate | Current Redis Cloud account is portable |
| **Server Capacity** | 75% bid success at 20 leagues | Need adequate Railway resources |

### Performance Baselines (January 12, 2026)

| Scale | Bid Success | p50 Latency | p99 Latency | Status |
|-------|-------------|-------------|-------------|--------|
| 2 leagues (16 users) | 100% | 688ms | 1,517ms | ✅ Acceptable |
| 20 leagues (160 users) | 76% | 800ms | 3,121ms | ❌ Not acceptable |
| 50 leagues (400 users) | Unknown | Unknown | Unknown | ❌ Pilot target |

### Root Cause Analysis

**MongoDB Network Latency:**
- Emergent's shared cluster: `customer-apps.oxfwhh.mongodb.net`
- Preview (localhost): 357ms average → Production (remote): 713ms average
- **Gap of ~350-400ms is pure network overhead**

**Implication for Migration:**
- **DO NOT use free tier M0** for pilot with 250+ users
- **Provision M10 (~£45/month) minimum** in same region as Railway deployment
- Expected improvement: 700ms → 100-200ms latency

---

## Executive Summary

| Stage | Users | Monthly Cost | Key Components |
|-------|-------|--------------|----------------|
| **Pilot** | ≤250 | ~£50-65 | Railway, MongoDB Atlas **M10**, Redis Cloud Essentials, Sentry Free |
| **Small Scale** | 500-2,000 | ~£100-180 | Railway (scaled), Atlas M10/M20, Redis Paid, Sentry Paid |
| **Confident Scale** | 5k-10k | ~£300-600 | Railway (autoscaling), Atlas Production, Redis Larger Tier |

**⚠️ Updated January 2026:** Pilot cost increased from £10-15 to £50-65 due to MongoDB M10 requirement (stress testing showed M0 free tier insufficient for real-time bidding at scale).

---

## Pre-Migration: Refactor Recommendation

**Recommended approach:** Refactor FIRST, then migrate

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Week 1-2** | Backend refactor | Split `server.py` (~6,400 lines) into routes/services |
| **Week 3** | Testing | Add basic test coverage |
| **Week 4** | Migration | Deploy to Railway (Stage 1 - Pilot) |

**Why refactor first:**
- Smaller files = easier debugging during migration
- Tests verify nothing breaks
- Cleaner deployment scripts with modular code
- Railway deploy logs easier to read with isolated routes

---

## Current External Services (Already Portable)

| Service | Account Ownership | Action Needed |
|---------|-------------------|---------------|
| **MongoDB** | Emergent-managed (`customer-apps.oxfwhh.mongodb.net`) | ⚠️ **Create M10 Atlas cluster** (not M0 - see stress test findings) |
| **Redis Cloud** | ✅ Your account (Essentials tier - 256 connections) | Keep credentials - already portable and upgraded |
| **Football-Data.org** | ✅ Your account | Portable - API key in env vars |
| **Cricbuzz/RapidAPI** | ✅ Your account | Portable - API key in env vars |

**Note:** Redis was upgraded from Free (30 connections) to Essentials (256 connections) in January 2026 based on stress test findings showing connection exhaustion at scale.

---

## Stage 1: Pilot (≤250 users)

**Goal:** Validate live auctions and mobile experience with acceptable performance.  
**Estimated Monthly Cost:** ~£50-65 *(Updated from £10-15 based on stress testing)*

| Element | Vendor | What it does | Why it's right now | Cost |
|---------|--------|--------------|-------------------|------|
| App Hosting | Railway | Runs backend APIs, auctions, background jobs | Simple deploys, low ops overhead | £10-15 |
| Database | **MongoDB Atlas (M10)** | Stores users, auctions, bids, leagues | **⚠️ M10 required for latency** (M0 showed 700ms+ latency) | **£45** |
| Real-time Auctions | Socket.IO | Live bidding & updates | Designed for bursty real-time use | £0 |
| Pub/Sub | **Redis Cloud (Essentials)** | Syncs auctions across app instances | **⚠️ 256 connections required** (30 insufficient at scale) | **£5** |
| Authentication | Built-in (app-level) | Login, sessions, roles | Fast, zero cost, sufficient for pilot | £0 |
| File Storage | S3-compatible | Logos, CSV exports | Tiny usage, very cheap | £0 |
| Error Monitoring | Sentry (free) | Captures crashes and key issues | Fast feedback during testing | £0 |
| Logs | Railway built-in | Basic operational visibility | Enough signal for pilot | £0 |
| CDN | Cloudflare (free) | Frontend asset delivery | Faster global delivery | £0 |
| Payments | Disabled | Code is payment-ready, but no money flows | Keeps pilot friction-free and low-risk | N/A |

### ⚠️ Stage 1 Considerations (Updated January 2026)

| Item | Concern | Mitigation |
|------|---------|------------|
| **MongoDB M0 NOT sufficient** | Stress tests showed 700ms+ latency with shared cluster | **Use M10 minimum (~£45/mo)** - expect 100-200ms latency |
| **Redis Free NOT sufficient** | 30 connections caused 85% bid success at 20 leagues | **Use Essentials tier (~£5/mo)** - 256 connections |
| **Railway region selection** | Latency depends on proximity to MongoDB | **Deploy Railway in same region as Atlas cluster** |
| **Railway cold starts** | Lower tiers may have cold starts affecting Socket.IO | Test reconnection handling; consider "always on" instance |
| **Socket.IO at scale** | Namespace connection failures observed at 20 leagues | Monitor and consider Railway Pro if issues persist |

### Expected Performance After Migration (with M10 + Essentials Redis)

| Scale | Expected Bid Success | Expected p50 | Expected p99 |
|-------|---------------------|--------------|--------------|
| 2 leagues | 100% | ~100-150ms | ~300-500ms |
| 20 leagues | 95%+ | ~150-250ms | ~800-1200ms |
| 50 leagues | 90%+ | ~200-300ms | ~1000-1500ms |

*Based on preview environment performance (localhost MongoDB: 357ms p50) and expected M10 same-region improvement.*

---

## Stage 2: Small Scale (500-2,000 users)

**Goal:** Support real tournaments reliably with better performance and visibility.  
**Estimated Monthly Cost:** ~£80-150

| Element | Vendor | What it does | Why it's right | Cost |
|---------|--------|--------------|----------------|------|
| App Hosting | Railway (scaled) | Handles more traffic & concurrent auctions | Easy scaling without infra team | £30-50 |
| Database | MongoDB Atlas (M2/M5) | Dedicated capacity & better performance | Handles heavier auction writes | £20-60 |
| Real-time Auctions | Socket.IO | Live bidding & updates | Same real-time model, proven | £0 |
| Pub/Sub | Redis Cloud (paid) | Keeps sockets in sync across instances | Prevents lag at higher concurrency | £20-40 |
| Authentication | Built-in + hardened | Stronger auth & role enforcement | Avoids migration pain, still zero vendor cost | £0 |
| Monitoring | Sentry (paid) | Alerts & performance insight | Faster issue detection | £10-20 |
| Storage & bandwidth | S3-compatible | More exports/assets | Still low usage | £5-10 |
| Payments | Stripe (test mode) | Wired in test mode, UI gated by feature flags | Can be enabled per tournament when ready | N/A |

---

## Stage 3: Confident Scale (5k-10k users)

**Goal:** Support flagship tournaments, charity partners, and monetisation.  
**Estimated Monthly Cost:** ~£300-600

| Element | Vendor | What it does | Why it's right long-term | Cost |
|---------|--------|--------------|-------------------------|------|
| App Hosting | Railway (autoscaling) | High concurrency & redundancy | Predictable scaling, no infra team | £100-180 |
| Database | MongoDB Atlas (production tier) | High availability & backups | Reliable under sustained load | £120-250 |
| Real-time Auctions | Socket.IO | Core auction experience | Still the right abstraction | £0 |
| Pub/Sub | Redis Cloud (larger tier) | Low-latency auction sync | Maintains real-time feel at scale | £50-100 |
| Authentication | Built-in or Managed Auth | Secure user identity | Optional upgrade if partners require it | £0-50 |
| Monitoring & Analytics | Sentry + Analytics | Performance & usage insight | Data-driven improvements | £30-60 |
| Email & notifications | SendGrid / similar | Invites, reminders, results | Improves engagement | £10-30 |
| Payments | Live Stripe Checkout | Stripe Connect later if charity splits needed | Full monetisation capability | N/A |

---

## Hidden Costs to Budget

| Item | Notes | Est. Cost |
|------|-------|-----------|
| **Domain name** | e.g., sportx.app | £10-15/year |
| **SSL Certificate** | Railway includes free Let's Encrypt | £0 |
| **Email transactional** | SendGrid free tier (100/day) | £0 initially |
| **Football-Data.org API** | Check rate limits on free tier | May need paid tier |

---

## Railway-Specific Deployment Requirements

### Architecture on Railway

```
┌─────────────────────────────────────────────────────────┐
│                      Railway Project                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Backend   │  │  Frontend   │  │  Redis (optional)│ │
│  │   Service   │  │   Service   │  │    if not using  │ │
│  │  (FastAPI)  │  │   (React)   │  │   Redis Cloud    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                                │
│         └────────────────┼────────────────────────────────┤
│                          │                                │
│                    Custom Domain                          │
│                  (sportx.app etc)                         │
└─────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │    External Services     │
              ├──────────────────────────┤
              │  • MongoDB Atlas         │
              │  • Redis Cloud           │
              │  • Football-Data.org API │
              │  • Sentry                │
              └──────────────────────────┘
```

### Backend Service Configuration

**railway.json (Backend):**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "uvicorn server:socket_app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Procfile (Alternative):**
```
web: uvicorn server:socket_app --host 0.0.0.0 --port $PORT
```

**requirements.txt notes:**
- Ensure `uvicorn[standard]` for WebSocket support
- Include `gunicorn` as fallback

### Frontend Service Configuration

**railway.json (Frontend):**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "yarn install && yarn build"
  },
  "deploy": {
    "startCommand": "npx serve -s build -l $PORT"
  }
}
```

**Or use Static Site deployment:**
- Build command: `yarn build`
- Publish directory: `build`

### Environment Variables (Railway Dashboard)

**Backend Service:**
```bash
# Database (YOUR Atlas cluster)
MONGO_URL=mongodb+srv://user:pass@YOUR-cluster.mongodb.net/sport_x
DB_NAME=sport_x_production

# Auth
JWT_SECRET=your-secure-secret-min-32-chars

# Redis (YOUR Redis Cloud)
REDIS_URL=redis://user:pass@your-redis-cloud-host:port

# APIs
FOOTBALL_DATA_TOKEN=your-token
RAPIDAPI_KEY=your-key

# Production settings
ENV=production
CORS_ORIGINS=https://your-frontend-domain.com
ENABLE_RATE_LIMITING=false
ENABLE_METRICS=true

# Optional
SENTRY_DSN=your-sentry-dsn
```

**Frontend Service:**
```bash
REACT_APP_BACKEND_URL=https://your-backend-service.railway.app
REACT_APP_SENTRY_DSN=
REACT_APP_SENTRY_ENVIRONMENT=production
```

### Railway WebSocket Considerations

| Item | Details |
|------|---------|
| **WebSocket Support** | ✅ Railway supports WebSockets natively |
| **Connection Limits** | No hard limit, but monitor memory usage |
| **Sticky Sessions** | Not needed with Redis pub/sub for Socket.IO |
| **Health Checks** | Configure `/api/health` endpoint |
| **Cold Starts** | Hobby plan may have cold starts - test Socket.IO reconnection |
| **Always On** | Pro plan ($20/mo) prevents cold starts |

### Railway CLI Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Open dashboard
railway open
```

### Multi-Service Setup

```bash
# Create project
railway init

# Add backend service
cd backend
railway add

# Add frontend service  
cd ../frontend
railway add

# Set env vars
railway variables set MONGO_URL="mongodb+srv://..."
railway variables set REDIS_URL="redis://..."
```

---

## Migration Checklist

### Pre-Migration (Do First)
```
□ 1. Code refactor (optional but recommended)
   □ Split server.py into routes/services
   □ Add basic test coverage
   □ Verify all tests pass locally

□ 2. Verify external service access
   □ Redis Cloud - confirm credentials work
   □ Football-Data.org - check API rate limits
   □ Cricbuzz/RapidAPI - verify key is active
```

### Migration Steps
```
□ 3. Create MongoDB Atlas cluster (YOUR account)
   □ Create M0 free tier cluster
   □ Whitelist Railway IPs (0.0.0.0/0 for dynamic)
   □ Create database user
   □ Get connection string
   □ Export data from current production if needed

□ 4. Set up Railway project
   □ Create Railway account (https://railway.app)
   □ Connect GitHub repository
   □ Create backend service
   □ Create frontend service

□ 5. Configure backend service
   □ Set start command: uvicorn server:socket_app --host 0.0.0.0 --port $PORT
   □ Add all environment variables
   □ Configure health check endpoint
   □ Deploy and verify /api/health responds

□ 6. Configure frontend service
   □ Set build command: yarn install && yarn build
   □ Set REACT_APP_BACKEND_URL to backend service URL
   □ Deploy and verify site loads

□ 7. Test critical flows
   □ Sign in (Magic Link)
   □ Create competition
   □ Join competition
   □ Run auction with 2+ users
   □ Socket.IO real-time updates
   □ Score updates
   □ Verify Redis pub/sub working

□ 8. Domain configuration
   □ Add custom domain in Railway
   □ Configure DNS records
   □ Verify SSL certificate provisioned

□ 9. Monitoring setup
   □ Configure Sentry DSN
   □ Set up Railway alerts
   □ Test error reporting

□ 10. Go-live
   □ Update DNS to point to Railway
   □ Monitor for 24-48 hours
   □ Keep Emergent as fallback temporarily
```

### Post-Migration
```
□ 11. Cleanup
   □ Remove Emergent deployment (after stable period)
   □ Delete unused MongoDB Atlas cluster (your Cluster0)
   □ Update all documentation

□ 12. Backup strategy
   □ Configure Atlas automated backups (paid tier)
   □ Or implement manual export routine
```

---

## Data Migration Options

### Option A: Fresh Start (Recommended for Pilot)
- Create new MongoDB Atlas cluster
- Re-seed teams/players using existing scripts
- Users re-register (acceptable for pilot scale)

### Option B: Export/Import Data
```bash
# Export from Emergent's managed DB (need API access)
# Use your app's export endpoints or contact Emergent support

# Import to your Atlas cluster
mongorestore --uri="mongodb+srv://YOUR-atlas-url" ./backup
```

---

## Rollback Plan

If Railway has issues:

1. **Immediate:** Point DNS back to Emergent (if still active)
2. **Short-term:** Deploy to alternative (Render, Fly.io)
3. **Data:** MongoDB Atlas is external - data safe regardless of hosting

---

## Questions to Resolve Before Migration

| Question | Status | Notes |
|----------|--------|-------|
| Custom domain purchased? | ❓ | e.g., sportx.app |
| Football-Data.org tier? | ❓ | Check rate limits for 250+ users |
| Staging environment needed? | ❓ | Separate Railway project? |
| Data migration approach? | ❓ | Fresh start vs export/import |
| ~~Backup strategy for M0?~~ | ✅ | N/A - Using M10 which has automated backups |
| **MongoDB Atlas region?** | ❓ | **Must match Railway region for low latency** |
| **Railway region?** | ❓ | **Choose based on user location + Atlas region** |
| **Emergent support response?** | ⏳ | Contacted re: dedicated MongoDB - awaiting response |

---

## Stress Testing Resources

Testing scripts and documentation created during January 2026 investigation:

| Resource | Location | Purpose |
|----------|----------|---------|
| Stress test script | `/app/tests/multi_league_stress_test.py` | Automated load testing |
| Test README | `/app/tests/README.md` | Usage instructions |
| Full stress test report | `/app/STRESS_TEST_REPORT.md` | Detailed findings |
| Master TODO list | `/app/MASTER_TODO_LIST.md` | All issues and status |

**To run stress test against new Railway deployment:**
```bash
pip install "python-socketio[asyncio_client]" aiohttp
python multi_league_stress_test.py --leagues 5 --users 8 --teams 4 --url https://your-railway-url.railway.app
```

---

## Estimated Timeline

| Task | Time |
|------|------|
| Code refactor (if doing) | 1-2 weeks |
| MongoDB Atlas setup | 1 hour |
| Railway project setup | 2 hours |
| Backend deployment + testing | 2-3 hours |
| Frontend deployment + testing | 1-2 hours |
| Domain configuration | 1 hour |
| End-to-end testing | 2-3 hours |
| Monitoring setup | 1 hour |
| **Total (with refactor)** | **2-3 weeks** |
| **Total (without refactor)** | **1-2 days** |

---

**Document Version:** 2.0  
**Last Updated:** December 21, 2025
