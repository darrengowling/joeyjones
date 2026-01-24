# AGENT START HERE

**Read this file FIRST. Every session. No exceptions.**

---

## 🚨 CRITICAL: What Breaks If You Don't Read This

1. **Authentication** - Magic link returns token in response (DEV MODE). Production needs email delivery.
2. **Teams/Players** - Stored in `assets` collection, NOT `clubs` or `teams`
3. **Points** - Stored in `league_points` collection, NOT `league_participants`
4. **Competition names** - Exact match required: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"

---

## 📋 Your First 3 Actions

1. **Read** `/app/MASTER_TODO_LIST.md` - The source of truth for all tasks
2. **Check** what phase we're in: PRE-MIGRATION → PRE-PILOT → POST-PILOT
3. **Ask user** what they want before doing anything

---

## 🔴 Current Status (January 2026)

| Item | Status |
|------|--------|
| **Platform** | Emergent (US-hosted) - migrating to Railway (EU) |
| **Core Issue** | UK users get ~700ms latency due to US hosting |
| **Pilot** | 400 UK users - NOT READY until migration complete |
| **Auth** | Needs hardening (email delivery, rate limiting) |

---

## 📁 Key Files

| File | What It Contains |
|------|------------------|
| `/app/MASTER_TODO_LIST.md` | All tasks, priorities, phases |
| `/app/MIGRATION_PLAN.md` | Railway migration details |
| `/app/AGENT_ONBOARDING_PROMPT.md` | Full system architecture |
| `/app/backend/server.py` | Main API (~5900 lines - monolithic) |
| `/app/docs/OPERATIONS_PLAYBOOK.md` | Operational procedures |
| `/app/tests/multi_league_stress_test.py` | Load testing script |

---

## ⚠️ Rules

1. **ASK before implementing** - Get user approval first
2. **READ before editing** - View files before search_replace
3. **TEST after changing** - curl, screenshot, or testing agent
4. **DON'T assume broken** - If something looks wrong, verify with user first

---

## 🚨 Emergent GitHub Sync Warning

**"Save to GitHub" only commits staged changes at that moment.**

If you make changes AFTER a save, they WON'T be in GitHub until the next save. This affects Railway deployments which pull from GitHub.

**Symptoms:**
- Railway deploys fail with errors about files you "fixed"
- yarn.lock mismatch errors
- Code changes not taking effect on Railway

**Solution:**
- Always "Save to GitHub" AFTER all changes are complete
- Verify critical files in GitHub browser before Railway deploy
- For yarn.lock issues on Railway, use Install Command: `yarn install --no-frozen-lockfile`

---

## 🗄️ Database Quick Reference

```
assets           → Teams (football) and Players (cricket)
leagues          → Competition settings
league_participants → User budgets, rosters (clubsWon array)
league_points    → Team/player scores (NOT in league_participants)
auctions         → Active auction state
bids             → Bid history
fixtures         → Match data (status must be "ft" for scoring)
users            → User accounts
magic_links      → Auth tokens
```

---

## 📞 If Stuck

1. Check `/app/docs/archive/` for historical context
2. Search codebase: `grep -r "keyword" /app/backend/`
3. Ask the user - they know the system

---

**Last Updated:** January 16, 2026
