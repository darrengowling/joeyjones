# Railway Proof-of-Concept Deployment Plan

**Purpose:** Validate Railway works for your requirements before committing to full migration  
**Time Required:** 1-2 hours  
**Cost:** $0 (free trial includes $5 credit)  
**Outcome:** Verified yes/no for each requirement + real latency numbers

---

## Prerequisites

Before starting, have ready:
- [ ] GitHub account (for deployment)
- [ ] Your codebase pushed to GitHub
- [ ] MongoDB Atlas connection string (your existing Redis Cloud)
- [ ] Redis Cloud connection string (your existing account)
- [ ] A UK-based device or VPN for latency testing

---

## Phase 1: Account Setup (5 mins)

```
□ 1.1 Go to railway.com
□ 1.2 Click "Start New Project"
□ 1.3 Sign up with GitHub (allows auto-deploy later)
□ 1.4 Verify email if required
□ 1.5 Note: You're on FREE TRIAL ($5 credit, no card required)

CHECKPOINT: You should see Railway dashboard
```

---

## Phase 2: Verify Region Availability (2 mins)

```
□ 2.1 Click "New Project" → "Empty Project"
□ 2.2 Click "Settings" (gear icon)
□ 2.3 Look for "Region" or "Environment" settings
□ 2.4 Check available regions:

RECORD FINDINGS:
┌─────────────────────────────────────────────┐
│ EU-West/London available?  [ ] YES  [ ] NO  │
│ Region options seen: _____________________  │
└─────────────────────────────────────────────┘

□ 2.5 Select EU-West/London if available
□ 2.6 If NOT available, STOP - Railway won't solve latency problem

CHECKPOINT: EU region confirmed available
```

---

## Phase 3: Deploy Backend (15 mins)

### Option A: Deploy from GitHub (Recommended)

```
□ 3.1 In your Railway project, click "New Service"
□ 3.2 Select "GitHub Repo"
□ 3.3 Authorize Railway to access your repos
□ 3.4 Select your SportX repository
□ 3.5 Railway should auto-detect it's Python

□ 3.6 Configure Root Directory (if monorepo):
      - Click service settings
      - Set Root Directory: /backend (or wherever server.py is)

□ 3.7 Configure Start Command:
      - uvicorn server:socket_app --host 0.0.0.0 --port $PORT

□ 3.8 DO NOT add environment variables yet - let it fail first
□ 3.9 Click "Deploy"
□ 3.10 Watch build logs

EXPECTED: Build succeeds, but app crashes (missing env vars)

RECORD FINDINGS:
┌─────────────────────────────────────────────┐
│ Build succeeded?           [ ] YES  [ ] NO  │
│ Build time: _______ seconds                 │
│ Error (if any): ___________________________│
└─────────────────────────────────────────────┘
```

### Option B: If GitHub deploy fails, try manual

```
□ 3.B1 Install Railway CLI: npm install -g @railway/cli
□ 3.B2 Login: railway login
□ 3.B3 Link project: railway link
□ 3.B4 Deploy: railway up
```

---

## Phase 4: Configure Environment Variables (10 mins)

```
□ 4.1 In Railway, click on your backend service
□ 4.2 Go to "Variables" tab
□ 4.3 Add each variable (click "New Variable" or use RAW editor):

REQUIRED VARIABLES:
┌────────────────────────────────────────────────────────────────┐
│ Variable                │ Value                                │
├────────────────────────────────────────────────────────────────┤
│ MONGO_URL               │ [Your Atlas connection string]       │
│ DB_NAME                 │ sport_x_production                   │
│ JWT_SECRET              │ [Generate: any 32+ char string]      │
│ REDIS_URL               │ [Your Redis Cloud URL]               │
│ FOOTBALL_DATA_TOKEN     │ eddf5fb8a13a4e2c9c5808265cd28579     │
│ RAPIDAPI_KEY            │ 62431ad8damshcc26bf0bb67d862p12ab40jsn9710a0c8967c │
│ CORS_ORIGINS            │ *                                    │
│ FRONTEND_ORIGIN         │ *                                    │
│ SENTRY_DSN              │ [Your Sentry DSN]                    │
└────────────────────────────────────────────────────────────────┘

□ 4.4 After adding variables, Railway auto-redeploys
□ 4.5 Watch deployment logs
□ 4.6 Wait for "Deployment successful" or equivalent

CHECKPOINT: Service shows as "Active" or "Running"
```

---

## Phase 5: Get Public URL & Test Health (5 mins)

```
□ 5.1 In service settings, find "Domains" or "Networking"
□ 5.2 Click "Generate Domain" (Railway provides free subdomain)
□ 5.3 Copy the URL (format: https://xxx.up.railway.app)

□ 5.4 Test health endpoint from your terminal:

      curl https://YOUR-URL.up.railway.app/api/health

EXPECTED RESPONSE:
{
  "status": "healthy",
  "database": "connected",
  "socketio": {...}
}

RECORD FINDINGS:
┌─────────────────────────────────────────────┐
│ Railway URL: _____________________________ │
│ Health check passed?       [ ] YES  [ ] NO  │
│ Database connected?        [ ] YES  [ ] NO  │
│ Redis connected?           [ ] YES  [ ] NO  │
│ Response time: _______ ms                   │
│ Error (if any): ___________________________│
└─────────────────────────────────────────────┘
```

---

## Phase 6: Test Socket.IO Connection (10 mins)

### 6A: Quick Browser Test

```
□ 6.1 Open browser console (F12 → Console)
□ 6.2 Paste and run:

const script = document.createElement('script');
script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
script.onload = () => {
  const socket = io('https://YOUR-URL.up.railway.app', {
    transports: ['websocket']
  });
  socket.on('connect', () => console.log('✅ CONNECTED:', socket.id));
  socket.on('connect_error', (e) => console.log('❌ ERROR:', e.message));
};
document.head.appendChild(script);

□ 6.3 Watch for "✅ CONNECTED" message

RECORD FINDINGS:
┌─────────────────────────────────────────────┐
│ WebSocket connected?       [ ] YES  [ ] NO  │
│ Socket ID received?        [ ] YES  [ ] NO  │
│ Error (if any): ___________________________│
└─────────────────────────────────────────────┘
```

### 6B: Test with Long-Polling Fallback

```
□ 6.4 Run same test but with long-polling:

const socket = io('https://YOUR-URL.up.railway.app', {
  transports: ['polling', 'websocket']
});

RECORD FINDINGS:
┌─────────────────────────────────────────────┐
│ Long-polling + WebSocket works? [ ] YES [ ] NO │
│ Notes: ___________________________________ │
└─────────────────────────────────────────────┘
```

---

## Phase 7: Latency Test from UK (15 mins)

### 7A: Simple Latency Test

```
□ 7.1 From UK device/VPN, run:

      time curl -s https://YOUR-URL.up.railway.app/api/health > /dev/null

□ 7.2 Run 10 times, record results:

LATENCY RESULTS (ms):
┌─────────────────────────────────────────────┐
│ Test 1: _____ ms                            │
│ Test 2: _____ ms                            │
│ Test 3: _____ ms                            │
│ Test 4: _____ ms                            │
│ Test 5: _____ ms                            │
│ Test 6: _____ ms                            │
│ Test 7: _____ ms                            │
│ Test 8: _____ ms                            │
│ Test 9: _____ ms                            │
│ Test 10: _____ ms                           │
├─────────────────────────────────────────────┤
│ AVERAGE: _____ ms                           │
│ Compare to Emergent: ~700ms                 │
│ Target: <200ms                              │
│ PASS?                      [ ] YES  [ ] NO  │
└─────────────────────────────────────────────┘
```

### 7B: API Endpoint Latency

```
□ 7.3 Test a real endpoint (leagues list):

      time curl -s https://YOUR-URL.up.railway.app/api/leagues > /dev/null

RECORD: _____ ms
```

---

## Phase 8: Mini Stress Test (Optional, 15 mins)

If you have time, run a scaled-down stress test:

```
□ 8.1 Ensure test users exist in your Atlas database
      (or create a few manually)

□ 8.2 Run stress test with reduced scale:

      python /app/tests/multi_league_stress_test.py \
        --backend-url https://YOUR-URL.up.railway.app \
        --num-leagues 5 \
        --users-per-league 4

□ 8.3 Record results:

STRESS TEST RESULTS:
┌─────────────────────────────────────────────┐
│ Leagues tested: _____                       │
│ Users per league: _____                     │
│ p50 latency: _____ ms (target: <200ms)      │
│ p99 latency: _____ ms (target: <1500ms)     │
│ Bid success rate: _____% (target: >95%)     │
│ Errors encountered: _____________________   │
│                                             │
│ OVERALL PASS?              [ ] YES  [ ] NO  │
└─────────────────────────────────────────────┘
```

---

## Phase 9: Cost Check (5 mins)

```
□ 9.1 Go to Railway dashboard → Usage or Billing
□ 9.2 Note resources consumed during testing:

RESOURCE USAGE:
┌─────────────────────────────────────────────┐
│ CPU usage: _____                            │
│ Memory usage: _____                         │
│ Egress: _____                               │
│ Estimated monthly cost: $_____              │
│                                             │
│ Within Hobby $5 credit?    [ ] YES  [ ] NO  │
└─────────────────────────────────────────────┘
```

---

## Phase 10: Cleanup (2 mins)

```
□ 10.1 Railway dashboard → Project Settings
□ 10.2 Click "Delete Project" 
□ 10.3 Confirm deletion
□ 10.4 This stops all charges

NOTE: You can recreate anytime for full migration
```

---

## POC Summary Checklist

Complete this before deciding on full migration:

```
REQUIREMENT VERIFICATION:
┌─────────────────────────────────────────────────────────────┐
│ #  │ Requirement              │ Verified │ Notes            │
├─────────────────────────────────────────────────────────────┤
│ 1  │ EU-West region           │ [ ] YES  │ ________________ │
│ 2  │ Backend deploys          │ [ ] YES  │ ________________ │
│ 3  │ MongoDB Atlas connects   │ [ ] YES  │ ________________ │
│ 4  │ Redis Cloud connects     │ [ ] YES  │ ________________ │
│ 5  │ WebSocket works          │ [ ] YES  │ ________________ │
│ 6  │ Long-polling works       │ [ ] YES  │ ________________ │
│ 7  │ UK latency <200ms        │ [ ] YES  │ Actual: ____ms   │
│ 8  │ GitHub auto-deploy       │ [ ] YES  │ ________________ │
│ 9  │ Cost within budget       │ [ ] YES  │ Est: $____/mo    │
└─────────────────────────────────────────────────────────────┘

DECISION:
┌─────────────────────────────────────────────────────────────┐
│ [ ] PROCEED with full Railway migration                     │
│ [ ] INVESTIGATE issues before proceeding:                   │
│     _________________________________________________      │
│ [ ] ABANDON Railway, consider alternatives:                 │
│     _________________________________________________      │
└─────────────────────────────────────────────────────────────┘
```

---

## If POC Succeeds: Next Steps

1. Update MIGRATION_PLAN.md with verified findings
2. Update MIGRATION_CHECKLIST.md with correct Railway details
3. Proceed with full migration following updated checklist
4. Deploy frontend service
5. Configure custom domain (optional)
6. Complete auth hardening before pilot

---

## If POC Fails: Alternatives to Investigate

| Platform | Why Consider |
|----------|--------------|
| Render | Similar to Railway, EU regions, free tier |
| Fly.io | Edge deployment, EU regions, sticky sessions |
| DigitalOcean App Platform | EU regions, predictable pricing |
| Google Cloud Run | EU regions, scales to zero |

---

## Notes

- This POC uses your PRODUCTION MongoDB Atlas - data is real
- Keep POC deployment SHORT to minimize any impact
- Delete POC project immediately after testing
- Do NOT share Railway URL publicly during testing

---

**Document Version:** 1.0  
**Created:** January 23, 2026
