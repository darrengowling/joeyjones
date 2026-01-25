# Railway Migration Checklist

**Created:** January 25, 2026  
**Status:** POC Complete → Production Migration In Progress

---

## Current State Summary

| Component | Local (Emergent) | Railway | Status |
|-----------|------------------|---------|--------|
| Sports | 2 | 2 | ✅ Complete |
| Football Teams | 74 | 56 | ⚠️ Missing UCL/AFCON teams |
| Cricket Players | 252 | 125 | ✅ Curated (intentional) |
| EPL externalIds | 20/20 | 20/20 | ✅ Complete |
| Leagues | 552 | 92 | ⚠️ Test data only |
| Users | 853 | 665 | ⚠️ Test data |

---

## ✅ COMPLETED

### Infrastructure
- [x] Railway backend deployed (joeyjones-production)
- [x] Railway frontend deployed (energetic-victory-production)
- [x] MongoDB Atlas connected (sport_x_poc)
- [x] Redis Cloud connected (for Socket.IO)
- [x] WebSocket-only transport (bypasses sticky sessions)

### Environment Variables (Backend)
- [x] MONGO_URL
- [x] DB_NAME
- [x] JWT_SECRET_KEY
- [x] REDIS_URL
- [x] CORS_ORIGINS / FRONTEND_ORIGIN
- [x] SENTRY_DSN + config
- [x] FOOTBALL_DATA_TOKEN
- [x] API_FOOTBALL_KEY
- [x] RAPIDAPI_KEY
- [x] SPORTS_CRICKET_ENABLED=true

### Environment Variables (Frontend)
- [x] REACT_APP_BACKEND_URL
- [x] REACT_APP_SENTRY_DSN + config

### Database - Sports
- [x] Football sport configured
- [x] Cricket sport configured

### Database - Football
- [x] 20 EPL teams seeded
- [x] EPL teams have externalId (for fixture imports)
- [x] UCL teams seeded (36)
- [ ] UCL teams externalId (not critical - season underway)
- [ ] AFCON teams (manual CSV import only)

### Database - Cricket
- [x] 125 curated IPL 2026 players seeded
- [x] Players have nationality, role, franchise
- [ ] Cricbuzz player IDs (wait for IPL 2026 series)

### Features Tested
- [x] User authentication (magic links)
- [x] Create competition (Football)
- [x] Create competition (Cricket/IPL)
- [x] EPL fixture import from API
- [x] Real-time auction (WebSocket)
- [ ] Cricket fixture import (needs IPL 2026 series)
- [ ] Score updates (needs live matches)

---

## ⚠️ REMAINING TASKS

### P0 - Required for Pilot

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1 | **Test full auction flow** | 30 min | Create league, invite users, run auction |
| 2 | **Test fixture scoring** | 30 min | Import fixtures, simulate match completion |

### P1 - Post-Pilot (Production)

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 5 | Add UCL team externalIds | 30 min | For future UCL competitions |
| 6 | Export all local football teams | 15 min | Get full 74 teams into Railway |
| 7 | Clean up test leagues/users | 15 min | Remove POC test data |

### P2 - Future

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 8 | Upgrade MongoDB Atlas tier | 5 min | M0 free → paid for production |
| 9 | Upgrade Railway tier | 5 min | Hobby → Pro for production |
| 10 | Set up monitoring/alerts | 1 hr | Sentry alerts, uptime monitoring |
| 11 | Configure backup schedule | 30 min | MongoDB Atlas backups |

---

## Environment Variable Reference

### Railway Backend (joeyjones-production)
```
MONGO_URL=mongodb+srv://darts_admin:***@cluster0.edjfwnl.mongodb.net/?appName=Cluster0
DB_NAME=sport_x_poc
JWT_SECRET_KEY=***
REDIS_URL=redis://default:***@redis-12232.c338.eu-west-2-1.ec2.cloud.redislabs.com:12232
CORS_ORIGINS=*
FRONTEND_ORIGIN=*
ENV=production
SENTRY_DSN=https://***@o4510411309907968.ingest.de.sentry.io/4510768829366352
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
FOOTBALL_DATA_TOKEN=eddf5fb8a13a4e2c9c5808265cd28579
API_FOOTBALL_KEY=ce31120a72a2158ab9e33a56233bf39f
RAPIDAPI_KEY=62431ad8damshcc26bf0bb67d862p12ab40jsn9710a0c8967c
SPORTS_CRICKET_ENABLED=true
```

### Railway Frontend (energetic-victory-production)
```
REACT_APP_BACKEND_URL=https://joeyjones-production.up.railway.app
REACT_APP_SENTRY_DSN=https://***@o4510411309907968.ingest.de.sentry.io/4510768829366352
REACT_APP_SENTRY_ENVIRONMENT=production
REACT_APP_SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## Quick Commands

### Seed EPL externalIds to Railway
```bash
python /app/scripts/update_railway_epl_external_ids.py "mongodb+srv://..."
```

### Check Railway database counts
```bash
python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
async def check():
    db = AsyncIOMotorClient('mongodb+srv://...')['sport_x_poc']
    print('Football:', await db.assets.count_documents({'sportKey': 'football'}))
    print('Cricket:', await db.assets.count_documents({'sportKey': 'cricket'}))
asyncio.run(check())
"
```

---

## Notes

1. **Why 125 cricket players vs 252?** - Curated list of probable IPL 2026 starters. The full 252 includes bench players who won't play.

2. **Why 56 football teams vs 74?** - Railway has EPL (20) + UCL (36). Local also has AFCON and duplicates.

3. **externalId purpose** - Required for football-data.org API to import fixtures and scores automatically.

4. **Cricbuzz integration** - Waiting for IPL 2026 series to appear in API (~2 weeks before tournament).
