# AGENT START HERE

**Read this file FIRST. Every session. No exceptions.**

---

## 🚨 CRITICAL: What Breaks If You Don't Read This

1. **Authentication** - Magic link returns token in response (DEV MODE). Production needs email delivery.
2. **Teams/Players** - Stored in `assets` collection, NOT `clubs` or `teams`
3. **Points** - Stored in `league_points` collection, NOT `league_participants`
4. **Competition names** - Exact match required: "UEFA Champions League", "English Premier League", "Africa Cup of Nations"
5. **Team logos** - Use `teamLogoMapping.js` for local assets, NOT API URLs
6. **Football-Data.org** - Teams must have `footballDataId` for fixture imports

---

## 📋 Your First 3 Actions

1. **Read** `/app/MASTER_TODO_LIST.md` - The source of truth for all tasks
2. **Check** what phase we're in: ~~PRE-MIGRATION~~ → **PRE-PILOT** → POST-PILOT
3. **Ask user** what they want before doing anything

---

## 🔴 Current Status (January 30, 2026)

| Item | Status |
|------|--------|
| **Platform** | Railway EU (MIGRATED ✅) |
| **Preview DB** | MongoDB Atlas (same as production) |
| **Production DB** | MongoDB Atlas |
| **Pilot** | 400 UK users - Final polish phase |
| **Football Teams** | 63 clubs + 42 national teams = 105 total |
| **Football-Data.org IDs** | 100% coverage (105/105) |
| **Auth** | Needs hardening (email delivery, rate limiting) |

---

## 📁 Key Files

| File | What It Contains |
|------|------------------|
| `/app/MASTER_TODO_LIST.md` | All tasks, priorities, phases |
| `/app/SESSION_CHANGES.md` | Detailed session work log |
| `/app/backend/server.py` | Main API (~5900 lines - monolithic) |
| `/app/frontend/src/utils/teamLogoMapping.js` | Team name → logo file mapping |
| `/app/frontend/src/components/TeamCrest.jsx` | Logo display component |
| `/app/docs/OPERATIONS_PLAYBOOK.md` | Operational procedures |

---

## 🗄️ Database Quick Reference

```
assets           → Teams (football) and Players (cricket)
                   - footballDataId: ID for Football-Data.org API
                   - type: 'national_team' for WC2026 teams
                   - competitionCode: 'WC2026', 'CL', 'PL', etc.
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

## 🖼️ Logo System Quick Reference

**Folder structure:**
```
/app/frontend/public/assets/clubs/
├── football/          → Club team logos (63 teams)
├── cricket/           → IPL team logos (10 teams)
└── national_teams/    → World Cup 2026 badges (42 teams)
```

**Mapping file:** `/app/frontend/src/utils/teamLogoMapping.js`
- `footballLogoMapping` - Club teams
- `cricketLogoMapping` - IPL teams
- `nationalTeamLogoMapping` - National teams

**Component:** `/app/frontend/src/components/TeamCrest.jsx`
- Conditionally adds white backdrop for dark logos (Tottenham, Newcastle, Juventus)

**To add new logos:**
1. Convert SVG to PNG: `cairosvg input.svg -o output.png -W 256 -H 256`
2. Copy to appropriate assets folder
3. Add mapping to `teamLogoMapping.js`
4. Update `footballDataId` using `/app/scripts/populate_football_data_ids.py`

---

## 🔧 Useful Scripts

| Script | Purpose |
|--------|---------|
| `/app/scripts/standardize_team_names.py` | Rename teams to official API names |
| `/app/scripts/merge_duplicate_teams.py` | Remove duplicate team entries |
| `/app/scripts/populate_football_data_ids.py` | Add Football-Data.org IDs to all teams |
| `/app/scripts/seed_railway_poc.py` | Seed football teams for new environment |

---

## ⚠️ Rules

1. **ASK before implementing** - Get user approval first
2. **READ before editing** - View files before search_replace
3. **TEST after changing** - curl, screenshot, or testing agent
4. **DON'T assume broken** - If something looks wrong, verify with user first
5. **DON'T save to GitHub** - Until user explicitly approves (triggers Railway auto-deploy)

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

## 📞 If Stuck

1. Check `/app/SESSION_CHANGES.md` for recent work
2. Check `/app/MASTER_TODO_LIST.md` for priorities
3. Search codebase: `grep -r "keyword" /app/backend/`
4. Ask the user - they know the system

---

**Last Updated:** January 30, 2026
