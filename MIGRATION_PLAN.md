# Migration Plan: Emergent → Self-Hosted

**Created:** December 13, 2025  
**Status:** CONTINGENCY PLAN - Monitor Emergent for 24-48 hours before decision  
**Reason:** Production outage (520 error) during active user testing

---

## Step 1: Export Your Code

**From Emergent:**
1. **GitHub Repo** - Your code should already be connected. Verify at Profile → GitHub
2. **Download Code** - Use the "Download" option in Emergent if GitHub isn't connected

**Key Files to Ensure You Have:**
```
/app/
├── backend/
│   ├── server.py           # Main backend (5900+ lines)
│   ├── auth.py             # JWT/Magic Link auth
│   ├── socketio_init.py    # Socket.IO with Redis
│   ├── models.py           # Pydantic models
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables (template)
├── frontend/
│   ├── src/                # React app
│   ├── package.json        # Node dependencies
│   └── .env                # Frontend env vars (template)
└── Documentation (optional but useful)
    ├── PRODUCTION_ENVIRONMENT_STATUS.md
    ├── OUTSTANDING_ISSUES.md
    ├── AGENT_ONBOARDING_CHECKLIST.md
    ├── SYSTEM_ARCHITECTURE_AUDIT.md
    └── UI_UX_AUDIT_REPORT.md
```

---

## Step 2: External Services (Already Portable)

| Service | Current | Action Needed |
|---------|---------|---------------|
| **MongoDB** | Emergent-managed | Migrate to MongoDB Atlas (free tier available) |
| **Redis** | Redis Cloud | ✅ Already external - just keep credentials |
| **Football-Data.org** | API key in .env | ✅ Portable |
| **Cricbuzz/RapidAPI** | API key in .env | ✅ Portable |

---

## Step 3: Choose New Platform

**Recommended Options:**

| Platform | Backend | Frontend | Cost | Effort |
|----------|---------|----------|------|--------|
| **Railway** | ✅ Python/FastAPI | ✅ React | $5-20/mo | Low |
| **Render** | ✅ Python/FastAPI | ✅ React | $7-25/mo | Low |
| **Fly.io** | ✅ Docker | ✅ Docker | $5-15/mo | Medium |
| **Vercel + Railway** | Railway for backend | Vercel for frontend | $5-20/mo | Low |
| **AWS/GCP** | Full control | Full control | Variable | High |

**Recommendation:** **Railway** or **Render** - both support:
- Python/FastAPI natively
- WebSockets (Socket.IO)
- Environment variables
- Custom domains
- Easy deployment from GitHub

---

## Step 4: Environment Variables to Configure

**Backend (.env):**
```bash
# Database
MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
DB_NAME="sport_x_production"

# Auth
JWT_SECRET="your-secure-secret"

# Redis (for Socket.IO)
REDIS_URL="redis://user:pass@redis-cloud-host:port"

# APIs
FOOTBALL_DATA_TOKEN="your-token"
RAPIDAPI_KEY="your-key"

# Optional
SENTRY_DSN="your-sentry-dsn"
CORS_ORIGINS="https://your-frontend-domain.com"
ENV="production"
ENABLE_RATE_LIMITING="false"
ENABLE_METRICS="true"
```

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL="https://your-backend-domain.com"
REACT_APP_SENTRY_DSN=""
REACT_APP_SENTRY_ENVIRONMENT="production"
```

---

## Step 5: Migration Checklist

```
□ 1. Export code from Emergent (GitHub or Download)
□ 2. Create MongoDB Atlas cluster
   - Export data from current DB if needed
   - Get connection string
□ 3. Keep Redis Cloud credentials (already external)
□ 4. Choose hosting platform (Railway/Render)
□ 5. Deploy backend:
   - Connect GitHub repo
   - Set environment variables
   - Verify health endpoint works
□ 6. Deploy frontend:
   - Update REACT_APP_BACKEND_URL
   - Deploy to same platform or Vercel/Netlify
□ 7. Configure custom domain
□ 8. Test all flows:
   - Sign in (Magic Link)
   - Create competition
   - Run auction
   - Socket.IO real-time updates
□ 9. Update DNS for production domain
□ 10. Monitor for 24-48 hours
```

---

## Step 6: Data Migration (MongoDB)

**Option A: Fresh Start**
- Create new MongoDB Atlas cluster
- Re-seed teams/players using existing scripts
- Users re-register

**Option B: Export/Import Data**
```bash
# Export from current (need access)
mongodump --uri="current-mongo-url" --out=./backup

# Import to Atlas
mongorestore --uri="atlas-mongo-url" ./backup
```

---

## Step 7: Platform-Specific Deployment

### Railway Deployment

1. Create Railway account at https://railway.app
2. Connect GitHub repository
3. Create two services:
   - **Backend**: Point to `/app/backend`, set Python buildpack
   - **Frontend**: Point to `/app/frontend`, set Node buildpack
4. Add environment variables in Railway dashboard
5. Railway auto-assigns URLs, or add custom domain

### Render Deployment

1. Create Render account at https://render.com
2. Create Web Service for backend:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn server:socket_app --host 0.0.0.0 --port $PORT`
3. Create Static Site for frontend:
   - Build command: `yarn build`
   - Publish directory: `build`
4. Add environment variables in Render dashboard

---

## Estimated Timeline

| Task | Time |
|------|------|
| Code export + review | 1 hour |
| MongoDB Atlas setup | 1 hour |
| Platform setup (Railway/Render) | 2 hours |
| Backend deployment + testing | 2 hours |
| Frontend deployment + testing | 1 hour |
| Domain configuration | 1 hour |
| End-to-end testing | 2 hours |
| **Total** | **~10 hours** |

---

## Decision Criteria

**Stay on Emergent if:**
- Outage was one-time incident
- Support is responsive and helpful
- Platform stabilizes within 24 hours

**Migrate if:**
- Repeated outages occur
- Support is unresponsive
- Lack of visibility into issues continues
- Business risk outweighs migration effort

---

## Notes

- The codebase is fully portable (standard FastAPI + React)
- No Emergent-specific dependencies in the code
- Redis is already external (Redis Cloud)
- Only MongoDB needs migration if moving

---

**Last Updated:** December 13, 2025
