# Deployment Guide

**Last Updated:** December 28, 2025  
**Purpose:** Deployment procedures for different environments

---

## Current Deployment (Emergent)

### Preview Environment

- **URL:** Auto-generated preview URL
- **Database:** Local MongoDB (localhost:27017)
- **Redis:** Not configured (single pod)
- **Hot Reload:** Enabled

### Production Environment

- **URL:** https://draft-kings-mobile.emergent.host
- **Database:** Emergent-managed MongoDB Atlas
- **Redis:** User's Redis Cloud instance
- **Deployment:** Via Emergent platform

### Deploying Changes

1. Make code changes in preview
2. Test thoroughly
3. Use Emergent "Deploy" button
4. Monitor health endpoint after deployment

---

## Planned Deployment (Railway)

See [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) for full details.

### Railway Setup

1. Create Railway project
2. Add backend service
3. Add frontend service
4. Configure environment variables
5. Connect to your MongoDB Atlas
6. Connect to your Redis Cloud

### Railway Configuration

**Backend (railway.json):**
```json
{
  "deploy": {
    "startCommand": "uvicorn server:socket_app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health"
  }
}
```

**Frontend (railway.json):**
```json
{
  "build": {
    "buildCommand": "yarn install && yarn build"
  },
  "deploy": {
    "startCommand": "npx serve -s build -l $PORT"
  }
}
```

---

## Post-Deployment Checklist

- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Socket.IO shows `"mode": "redis"` (production)
- [ ] Can create and join leagues
- [ ] Can run auction with 2+ users
- [ ] Scores calculate correctly

---

**Related:** [MIGRATION_PLAN.md](./MIGRATION_PLAN.md), [../ENV_VARIABLES.md](../ENV_VARIABLES.md)
