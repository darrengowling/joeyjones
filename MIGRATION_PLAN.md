# Migration Plan: Emergent → Railway (EU-West)

**Created:** December 13, 2025  
**Last Updated:** January 19, 2026  
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
| **Timeline** | 1-2 days (without refactor) |

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

## Cost Breakdown

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Railway | Starter | ~£15 |
| MongoDB Atlas | M10 (europe-west2) | ~£45 |
| Redis Cloud | Essentials (256 conn) | ~£5 |
| Sentry | Free | £0 |
| **Total** | | **~£65/month** |

---

## Pre-Migration Requirements

### ✅ Already Done
- [x] Sentry configured (backend DSN active)
- [x] Redis Cloud upgraded to Essentials (256 connections)
- [x] Stress test script ready (`/app/tests/multi_league_stress_test.py`)
- [x] Environment variables documented

### ⏳ Do Before Migration
- [ ] **Auth hardening** - Magic link currently returns token in response (dev mode)
  - Needs SendGrid/Resend for email delivery
  - Add rate limiting (3/hour/email)
  - Can do after migration if needed for pilot speed

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

---

## Railway Configuration

### Backend Service

**Start command:**
```bash
uvicorn server:socket_app --host 0.0.0.0 --port $PORT
```

**Environment variables:**
```bash
# Database (YOUR Atlas cluster - EU region)
MONGO_URL=mongodb+srv://user:pass@YOUR-cluster.europe-west2.mongodb.net/sport_x
DB_NAME=sport_x_production

# Auth
JWT_SECRET=your-secure-secret-min-32-chars

# Redis (YOUR existing Redis Cloud)
REDIS_URL=redis://user:pass@your-redis-cloud-host:port

# APIs
FOOTBALL_DATA_TOKEN=your-token
RAPIDAPI_KEY=your-key

# Sentry (already configured)
SENTRY_DSN=https://618d64387dd9bd3a8748f3671b530981@o4510411309907968.ingest.de.sentry.io/4510734931722320

# Production settings
CORS_ORIGINS=https://your-frontend-domain.com
FRONTEND_ORIGIN=https://your-frontend-domain.com
```

### Frontend Service

**Build command:**
```bash
yarn install && yarn build
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

## Rollback Plan

If Railway has issues:

1. **Immediate:** Emergent is still running - can revert DNS
2. **Data safe:** MongoDB Atlas is external - data persists regardless
3. **Alternative hosts:** Render, Fly.io have similar setup

---

## Post-Migration Tasks

1. **Run stress test** to validate latency improvement
2. **Monitor Sentry** for any new errors
3. **Auth hardening** (if not done pre-migration)
4. **Update documentation** with new URLs
5. **Configure backups** (Atlas M10 includes automated backups)

---

## Resources

| Resource | Location |
|----------|----------|
| Migration Checklist | `/app/MIGRATION_CHECKLIST.md` |
| Stress Test Script | `/app/tests/multi_league_stress_test.py` |
| Master TODO List | `/app/MASTER_TODO_LIST.md` |
| Emergency Rebuild Prompt | `/app/docs/archive/EMERGENCY_REBUILD_PROMPT.md` |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 3.1 | Jan 19, 2026 | Removed hybrid approach (ruled out); Updated Sentry status; Added auth hardening requirement; Simplified document |
| 3.0 | Jan 12, 2026 | Added stress test findings |
| 2.0 | Dec 21, 2025 | Added Railway configurations |
| 1.0 | Dec 13, 2025 | Initial plan |
