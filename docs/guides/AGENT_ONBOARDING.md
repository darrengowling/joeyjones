# Agent Onboarding Checklist

**Last Updated:** December 21, 2025  
**Purpose:** Mandatory steps for every new agent before starting any work

---

## ⚠️ CRITICAL: DO NOT SKIP THESE STEPS

Previous agents have wasted significant time and resources by:
- Looking at preview environment config instead of production
- Referencing outdated documentation
- Making assumptions without verification
- Attempting to "fix" things that weren't broken
- **Making code changes without explicit user approval**
- **Making "incremental guesses" instead of thorough analysis**
- **Ignoring repeated instructions from user**
- **Introducing new bugs while fixing existing ones (e.g., ISSUE-016 fix broke countdown display)**
- **Setting up unnecessary external services (see MongoDB Atlas failure below)**

**This checklist prevents those mistakes.**

---

## 🚨 CRITICAL: MONGODB CONFIGURATION (Dec 21, 2025)

### ⛔ DO NOT TELL USERS TO SET UP EXTERNAL MONGODB

**Emergent provides managed MongoDB Atlas automatically for all deployments (under Emergent's account).**

A previous agent incorrectly told the user to create their own MongoDB Atlas cluster, believing it was required for production. This was **completely unnecessary** and caused confusion when the user received "inactive cluster" warnings for an unused database.

**Production MONGO_URL (auto-configured by Emergent):**
```
mongodb+srv://...@customer-apps.oxfwhh.mongodb.net/...
```

| Environment | Database | Host | Management |
|-------------|----------|------|------------|
| **Preview** | Local MongoDB | `localhost:27017` | Emergent (automatic) |
| **Production** | Emergent Managed Atlas | `customer-apps.oxfwhh.mongodb.net` | Emergent (automatic) |

**DO NOT:**
- ❌ Tell users to create MongoDB Atlas clusters
- ❌ Configure external database URLs for production
- ❌ Tell users they need to set up external databases

**Emergent handles all database infrastructure via their own Atlas account. No user-side setup required.**

---

## 🔴 ABSOLUTE RULES (Dec 21, 2025)

1. **NEVER make code changes without explicit user approval**
2. **NEVER assume - verify everything first**
3. **NEVER make incremental guesses - do thorough analysis**
4. **NEVER set up external services without confirming they're actually needed**
5. **Present complete plan before ANY implementation**
6. **Check downstream effects before proposing fixes**
7. **Test ALL related functionality, not just the fix**

---

## ⚠️ KNOWN AGENT FAILURES (Learn from these)

### MongoDB Atlas Setup (Dec 2025) - UNNECESSARY
- **Task:** Set up production database
- **Result:** Created external MongoDB Atlas cluster that was never used
- **Root cause:** Agent didn't understand that Emergent provides managed MongoDB automatically
- **Impact:** User received confusing "inactive cluster" warnings, wasted time investigating
- **Lesson:** **Do not set up external infrastructure without verifying it's actually needed**

### ISSUE-016 Attempt (Dec 19, 2025) - FAILED
- **Task:** Remove `loadAuction()` from `onSold` handler to fix race condition
- **Result:** Broke countdown display between lots
- **Root cause:** Agent didn't check what else depended on `loadAuction()`
- **Status:** Reverted, marked as "Agent unable to complete fix"

### ISSUE-018 Attempt (Dec 19, 2025) - PARTIAL
- **Task:** Auto-filter teams by competition code
- **Result:** Multiple failed attempts, broke team selection display
- **Root cause:** Agent made incremental guesses instead of understanding full data flow
- **Status:** Backend fix working, frontend `loadAvailableAssets()` working, but `loadAssets()` changes reverted

---

## 📋 Mandatory Onboarding Steps

### Step 1: Verify Production Health (DO THIS FIRST)

```bash
# Run this command BEFORE anything else
curl -s "https://draft-kings-mobile.emergent.host/api/health" | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "socketio": {
    "mode": "redis",
    "redis_configured": true,
    "multi_pod_ready": true
  }
}
```

**⚠️ If Socket.IO shows `"mode": "in-memory"` in production, this is a PROBLEM.**

---

### Step 2: Read These Documents (In Order)

| Order | Document | Purpose |
|-------|----------|--------|
| 1 | `/app/PRODUCTION_ENVIRONMENT_STATUS.md` | Current state of production |
| 2 | `/app/OUTSTANDING_ISSUES.md` | Known issues and priorities |
| 3 | `/app/AGENT_ONBOARDING_PROMPT.md` | System architecture overview |
| 4 | `/app/SYSTEM_ARCHITECTURE_AUDIT.md` | Database schema and data flow |

```bash
# Quick read command
head -100 /app/PRODUCTION_ENVIRONMENT_STATUS.md
head -100 /app/OUTSTANDING_ISSUES.md
```

---

### Step 3: Understand the Environment Difference

**CRITICAL:** Production and Preview have DIFFERENT configurations!

| Setting | Production | Preview/Local |
|---------|------------|---------------|
| REDIS_URL | ✅ SET (in deployment settings) | ❌ NOT in .env file |
| Socket.IO Mode | `redis` (multi-pod) | `in-memory` (single pod) |
| Rate Limiting | Configured (disabled) | Not configured |

**The local `.env` file does NOT reflect production configuration.**

To see production config, check the health endpoint, NOT the local `.env`.

---

### Step 4: Verify Current User Testing Status

Ask the user:
1. Is there active user testing happening right now?
2. Any issues reported from current testing?
3. What is the immediate priority?

**DO NOT make changes during active testing without explicit approval.**

---

### Step 5: Check Recent Changes

```bash
# View recent commits
cd /app && git log --oneline -10

# Check recent documentation updates
ls -lt /app/*.md | head -10
```

---

### Step 6: Verify Database State

```bash
# Check collection counts
mongosh --quiet --eval "db.getCollectionNames().forEach(c => { print(c + ': ' + db[c].countDocuments({})) })" test_database
```

**Key Collections:**
- `assets`: Should have 127 (football clubs + cricket players)
- `leagues`: Active competitions
- `users`: Registered users
- `league_points`: Scoring data (source of truth for points)

---

## 🚫 Common Mistakes to Avoid

### Mistake 1: Trusting Local .env for Production State
❌ **Wrong:** "Redis isn't configured" (based on local .env)  
✅ **Right:** Check `/api/health` endpoint for actual production state

### Mistake 2: Looking in Wrong Database Collection
❌ **Wrong:** Looking for points in `league_participants`  
✅ **Right:** Points are in `league_points` collection

### Mistake 3: Looking for Teams in Wrong Collection
❌ **Wrong:** Looking for `clubs` or `teams` collection  
✅ **Right:** ALL teams/players are in `assets` collection

### Mistake 4: Assuming Fixture Status Values
❌ **Wrong:** Setting fixture status to `"completed"`  
✅ **Right:** Scoring requires status `"ft"` (full-time)

### Mistake 5: Making Changes Without Approval
❌ **Wrong:** "I'll fix this real quick"  
✅ **Right:** Present analysis to user, get explicit approval

---

## ✅ Pre-Work Verification Checklist

Before starting ANY work, confirm:

- [ ] Ran production health check
- [ ] Read PRODUCTION_ENVIRONMENT_STATUS.md
- [ ] Read OUTSTANDING_ISSUES.md  
- [ ] Understand production uses Redis (even if local doesn't)
- [ ] Asked user about current testing status
- [ ] Know what the immediate priority is
- [ ] Will get approval before making changes

---

## 🔍 Quick Reference Commands

### Production Health
```bash
curl -s "https://draft-kings-mobile.emergent.host/api/health" | python3 -m json.tool
```

### Check Production Sports
```bash
curl -s "https://draft-kings-mobile.emergent.host/api/sports" | python3 -m json.tool
```

### Database Counts
```bash
mongosh --quiet --eval "db.getCollectionNames().forEach(c => { print(c + ': ' + db[c].countDocuments({})) })" test_database
```

### Backend Logs
```bash
tail -50 /var/log/supervisor/backend.err.log
```

### Frontend Logs
```bash
tail -50 /var/log/supervisor/frontend.err.log
```

### Restart Services (only if needed)
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

---

## 📞 When to Ask the User

**ALWAYS ask before:**
- Making any code changes
- Restarting services during testing
- Running database migrations
- Deploying to production

**Ask for clarification when:**
- Instructions are ambiguous
- Reported issue doesn't match what you see
- You're unsure which environment to check
- Priority isn't clear

---

## 📝 After Completing Work

1. Update `/app/PRODUCTION_ENVIRONMENT_STATUS.md` with any changes
2. Update `/app/OUTSTANDING_ISSUES.md` (move fixed items to Resolved)
3. Test your changes
4. Report results to user with evidence
5. Get user verification before considering task complete

---

**Document Version:** 1.0  
**Mandatory Reading:** YES - Every new agent session
