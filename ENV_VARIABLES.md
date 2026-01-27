# Environment Variables Reference

**Created:** December 28, 2025  
**Purpose:** Complete environment variable documentation for deployment and migration  
**Status:** ACTIVE

---

## Overview

| Category | Variables | Required |
|----------|-----------|----------|
| Database | 2 | Yes |
| Authentication | 2 | Yes |
| CORS | 2 | Yes |
| Features | 4 | No |
| External APIs | 4 | Conditional |
| Monitoring | 4 | No |
| Infrastructure | 2 | Production |

---

## Backend Environment Variables

**File:** `/app/backend/.env`

### Required (Application Won't Start Without)

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` or `mongodb+srv://...` | **Yes** |
| `DB_NAME` | Database name | `test_database` | **Yes** |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | `your-secure-secret-min-32-chars` | **Yes** |
| `JWT_SECRET_KEY` | Alias for JWT_SECRET | Same as above | **Yes** |

### CORS & Origins

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000,https://yourdomain.com` | **Yes** |
| `FRONTEND_ORIGIN` | Primary frontend URL | `https://yourdomain.com` | No |

### Feature Flags

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `SPORTS_CRICKET_ENABLED` | Enable cricket sport | `false` | `true`/`false` |
| `FEATURE_MY_COMPETITIONS` | Enable My Competitions page | `true` | `true`/`false` |
| `FEATURE_ASSET_SELECTION` | Enable asset selection UI | `false` | `true`/`false` |
| `FEATURE_WAITING_ROOM` | Enable auction waiting room | `true` | `true`/`false` |

### External APIs

| Variable | Description | Required For | How to Get |
|----------|-------------|--------------|------------|
| `FOOTBALL_DATA_TOKEN` | Football-Data.org API key | Football fixture import | https://www.football-data.org/client/register |
| `RAPIDAPI_KEY` | RapidAPI key | Cricket data | https://rapidapi.com/ |
| `CRICAPI_KEY` | Cricket API key | Cricket scoring | Via RapidAPI |
| `API_FOOTBALL_KEY` | Alternative football API | Optional | https://www.api-football.com/ |

### Monitoring & Observability

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `SENTRY_DSN` | Sentry error tracking DSN | Empty (disabled) | Get from Sentry dashboard |
| `SENTRY_ENVIRONMENT` | Environment name for Sentry | `pilot` | `development`, `staging`, `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance sampling rate | `0.1` | 0.0 to 1.0 |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | `true`/`false` |

### Infrastructure

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `REDIS_URL` | Redis connection string | None (in-memory) | Required for multi-pod Socket.IO |
| `ENABLE_RATE_LIMITING` | Enable API rate limiting | `true` | Disable for testing |
| `ENV` | Environment identifier | `production` | `development`, `staging`, `production` |

---

## Frontend Environment Variables

**File:** `/app/frontend/.env`

### Required

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `REACT_APP_BACKEND_URL` | Backend API URL | `https://your-backend.com` | **Yes** |

### Optional

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `REACT_APP_BUILD_HASH` | Git commit hash for debugging | Auto-generated | Shows in footer |
| `WDS_SOCKET_PORT` | WebSocket dev server port | `0` | Development only |
| `REACT_APP_FEATURE_MY_COMPETITIONS` | Feature flag override | `true` | |
| `REACT_APP_FEATURE_ASSET_SELECTION` | Feature flag override | `true` | |
| `REACT_APP_SENTRY_DSN` | Frontend Sentry DSN | Empty | Same as backend or separate |
| `REACT_APP_SENTRY_ENVIRONMENT` | Frontend Sentry environment | `pilot` | |
| `REACT_APP_SENTRY_TRACES_SAMPLE_RATE` | Frontend performance sampling | `0.1` | |

---

## Environment Configurations

### Development (Local)

```bash
# Backend .env
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
JWT_SECRET=development-secret-min-32-characters-long
JWT_SECRET_KEY=development-secret-min-32-characters-long
CORS_ORIGINS=http://localhost:3000
ENV=development
SPORTS_CRICKET_ENABLED=true
FEATURE_MY_COMPETITIONS=true
FEATURE_ASSET_SELECTION=true
FEATURE_WAITING_ROOM=true
ENABLE_RATE_LIMITING=false
ENABLE_METRICS=true

# Frontend .env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=0
```

### Emergent Preview

```bash
# Backend .env (auto-configured)
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
# ... rest auto-configured

# Frontend .env (auto-configured)
REACT_APP_BACKEND_URL=https://sporty-ui.preview.emergentagent.com
```

### Emergent Production

```bash
# Backend (configured in Emergent deployment settings)
MONGO_URL=mongodb+srv://...@customer-apps.oxfwhh.mongodb.net/...
DB_NAME=production_db
REDIS_URL=redis://...  # User's Redis Cloud
ENV=production

# Frontend (configured in Emergent deployment settings)
REACT_APP_BACKEND_URL=https://your-app.emergent.host
```

### Railway Deployment

```bash
# Backend Service Variables
MONGO_URL=mongodb+srv://user:pass@your-cluster.mongodb.net/sport_x
DB_NAME=sport_x_production
JWT_SECRET=your-production-secret-min-32-characters
JWT_SECRET_KEY=your-production-secret-min-32-characters
CORS_ORIGINS=https://your-frontend.railway.app,https://yourdomain.com
FRONTEND_ORIGIN=https://yourdomain.com
REDIS_URL=redis://user:pass@your-redis-cloud:port
ENV=production
SPORTS_CRICKET_ENABLED=true
FEATURE_MY_COMPETITIONS=true
FEATURE_ASSET_SELECTION=true
FEATURE_WAITING_ROOM=true
ENABLE_RATE_LIMITING=true
ENABLE_METRICS=true
FOOTBALL_DATA_TOKEN=your-api-token
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production

# Frontend Service Variables
REACT_APP_BACKEND_URL=https://your-backend.railway.app
REACT_APP_SENTRY_DSN=https://xxx@sentry.io/xxx
REACT_APP_SENTRY_ENVIRONMENT=production
```

---

## Variable Details

### MONGO_URL

**Format Options:**

```bash
# Local MongoDB
MONGO_URL=mongodb://localhost:27017

# MongoDB Atlas (SRV)
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# MongoDB Atlas (Standard)
MONGO_URL=mongodb://username:password@host1:27017,host2:27017/?replicaSet=rs0

# With options
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=myapp&maxPoolSize=5&retryWrites=true&timeoutMS=10000&w=majority
```

### REDIS_URL

**Format:**

```bash
# Redis Cloud
REDIS_URL=redis://default:password@redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345

# Local Redis
REDIS_URL=redis://localhost:6379

# With TLS
REDIS_URL=rediss://user:pass@host:port
```

**Notes:**
- Required for multi-pod Socket.IO deployment
- Without REDIS_URL, Socket.IO uses in-memory mode (single pod only)
- Production health check shows `"mode": "redis"` when properly configured

### JWT_SECRET

**Requirements:**
- Minimum 32 characters
- Use cryptographically random string
- Keep secret and never commit to git

**Generate:**
```bash
openssl rand -hex 32
```

### CORS_ORIGINS

**Format:**
- Comma-separated URLs
- No trailing slashes
- Include protocol (http/https)

```bash
# Single origin
CORS_ORIGINS=https://yourdomain.com

# Multiple origins
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://www.yourdomain.com
```

---

## Feature Flags

### Backend Feature Flags

| Flag | Effect When `true` | Effect When `false` |
|------|-------------------|--------------------|
| `SPORTS_CRICKET_ENABLED` | Cricket sport appears in `/api/sports` | Cricket hidden |
| `FEATURE_MY_COMPETITIONS` | My Competitions data returned | Feature disabled |
| `FEATURE_ASSET_SELECTION` | Asset selection endpoints active | Feature disabled |
| `FEATURE_WAITING_ROOM` | Waiting room flow enabled | Direct to auction |

### Frontend Feature Flags

Frontend reads from backend `/api/sports` and `/api/health` for feature state.
Overrides available via `REACT_APP_FEATURE_*` variables.

---

## Security Checklist

### Production Requirements

- [ ] `JWT_SECRET` is unique and secure (not default)
- [ ] `MONGO_URL` uses authentication
- [ ] `CORS_ORIGINS` lists only allowed domains
- [ ] `ENABLE_RATE_LIMITING=true`
- [ ] API keys are not committed to git
- [ ] `ENV=production` is set

### Never Commit

```
# Add to .gitignore
.env
.env.local
.env.production
*.env
```

---

## Troubleshooting

### "Database not connected"

```bash
# Check MONGO_URL is set
echo $MONGO_URL

# Test connection
mongosh "$MONGO_URL" --eval "db.serverStatus()"
```

### "Socket.IO not syncing across pods"

```bash
# Check REDIS_URL is set
echo $REDIS_URL

# Check health endpoint
curl https://your-app.com/api/health | jq '.socketio'
# Should show: "mode": "redis"
```

### "CORS errors"

```bash
# Verify CORS_ORIGINS includes your frontend URL
# Check for trailing slashes (remove them)
# Ensure protocol matches (http vs https)
```

### "JWT invalid"

```bash
# Ensure JWT_SECRET matches between restarts
# Check JWT_SECRET_KEY is also set (legacy alias)
```

---

## Migration Notes

### From Emergent to Railway

1. **MONGO_URL**: Create your own MongoDB Atlas cluster and update
2. **REDIS_URL**: Already using Redis Cloud? Keep same URL
3. **JWT_SECRET**: Generate new for production
4. **CORS_ORIGINS**: Update with Railway domains
5. **All API keys**: Copy from Emergent deployment settings

### Environment Variable Checklist

| Variable | Emergent Source | Railway Target |
|----------|-----------------|----------------|
| MONGO_URL | Auto-configured | Your Atlas cluster |
| DB_NAME | Auto-configured | Your database name |
| REDIS_URL | Deployment settings | Same (your Redis Cloud) |
| JWT_SECRET | Deployment settings | Generate new |
| CORS_ORIGINS | Deployment settings | Railway URLs |
| FOOTBALL_DATA_TOKEN | Deployment settings | Same (portable) |
| SENTRY_DSN | Deployment settings | Your Sentry project |

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
