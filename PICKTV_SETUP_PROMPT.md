# Pick TV - Agent Setup Prompt

**Copy this entire document into the Emergent chat when starting the Pick TV project.**

---

## PROJECT CONTEXT

You are starting work on **Pick TV**, a fantasy entertainment platform for reality TV shows. This is a **new product** built on the existing **Sport X** fantasy sports platform codebase.

**Key Facts:**
- Pick TV shares 80%+ of code with Sport X (auction engine, auth, leagues, infrastructure)
- You are NOT building from scratch - you're adapting an existing working platform
- Your job is to configure and extend the Sport X codebase for reality TV shows

---

## CRITICAL FIRST STEPS

### Step 0: Clone the Sport X Codebase

**You must clone the Sport X repository FIRST before doing anything else.**

```bash
# Clone Sport X from GitHub (user provides URL)
cd /app
git clone https://github.com/USERNAME/sport-x.git .
```

**Ask the user for the GitHub repository URL if not provided.**

⚠️ **DO NOT proceed until the clone is complete and you have the codebase.**

### Step 1: Verify You Have the Codebase

Run this command to confirm you have the Sport X code:

```bash
ls -la /app/backend/server.py /app/frontend/src/pages/AuctionRoom.js
```

**If files exist:** You're ready. Proceed to Step 2.
**If files don't exist:** STOP. The clone failed. Ask the user for help.

### Step 2: Install Dependencies & Start Services

```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend  
cd /app/frontend
yarn install

# Restart services
sudo supervisorctl restart backend frontend
```

### Step 3: Read the Onboarding Document

```bash
cat /app/PICKTV_ONBOARDING_PROMPT.md
```

This document contains:
- What's reusable vs what needs building
- Database schema for contestants/episodes
- All API endpoints you inherit
- User flows that work out of the box
- Implementation phases (4-week plan)

**Do not proceed without reading this document.**

### Step 4: Read Supporting Documentation

After the onboarding doc, read these in order:

1. `/app/CORE_AUCTION_ENGINE.md` - The auction system you inherit
2. `/app/SHARED_CODEBASE.md` - What's shared between Sport X and Pick TV
3. `/app/DATABASE_SCHEMA.md` - All MongoDB collections
4. `/app/API_REFERENCE.md` - All 61 API endpoints

---

## WHAT YOU INHERIT (DO NOT REBUILD)

These features work TODAY with zero changes:

| Feature | Status |
|---------|--------|
| User registration & login | ✅ Working |
| JWT authentication | ✅ Working |
| League creation | ✅ Working |
| Invite links & joining | ✅ Working |
| Real-time auction bidding | ✅ Working |
| Budget tracking | ✅ Working |
| Roster management | ✅ Working |
| Socket.IO sync | ✅ Working |
| Multi-pod Redis scaling | ✅ Working |

**DO NOT rewrite any of these systems.**

---

## WHAT YOU NEED TO BUILD

| Feature | Priority | Description |
|---------|----------|-------------|
| Reality TV sport config | P0 | Add `reality_tv` to sports collection |
| Contestant data model | P0 | Extend assets for contestants |
| Episode results model | P0 | Extend fixtures for episodes |
| Elimination scoring | P0 | New scoring logic for eliminations |
| Episode entry UI | P0 | Commissioner enters episode results |
| Contestant cards | P1 | Display contestant photo/bio |
| Pick TV theming | P1 | Purple/gold color scheme, terminology |
| Elimination tracker | P2 | Visual timeline of eliminations |

---

## CONFIGURATION CHANGES (NOT CODE CHANGES)

### 1. Add Sport to Database

Insert into `sports` collection:

```javascript
{
  "key": "reality_tv",
  "name": "Reality TV",
  "active": true,
  "assetType": "CONTESTANT",
  "scoringSchema": {
    "type": "elimination",
    "rules": {
      "survives_episode": 5,
      "wins_challenge": 10,
      "wins_immunity": 15,
      "makes_final": 50,
      "wins_show": 100
    }
  },
  "uiHints": {
    "assetLabel": "Contestant",
    "assetPlural": "Contestants",
    "currencySymbol": "⭐",
    "currencyName": "Stars"
  }
}
```

### 2. Terminology Updates

| Sport X | Pick TV |
|---------|---------|
| Club | Contestant |
| Match | Episode |
| £500m | ⭐100 |
| Fixture | Episode |
| Your Clubs | Your Picks |

---

## COMMON MISTAKES TO AVOID

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Rewriting auction engine | Wastes time, introduces bugs | Use existing engine as-is |
| Creating new auth system | Already works perfectly | Use existing JWT auth |
| Hardcoding URLs/ports | Breaks deployment | Use environment variables |
| Looking for `clubs` collection | Doesn't exist | All assets in `assets` collection |
| Using status `"completed"` | Won't trigger scoring | Use status `"ft"` for completed |
| Forgetting `{"_id": 0}` in queries | Causes serialization errors | Always exclude _id |

---

## PROJECT STRUCTURE

```
/app/
├── backend/
│   ├── server.py           # Main backend - ADD Pick TV routes here
│   ├── models.py           # ADD contestant/episode models here
│   ├── scoring_service.py  # ADD elimination scoring here
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AuctionRoom.js      # Works as-is, update labels
│   │   │   ├── LeagueDetail.js     # Works as-is, update labels
│   │   │   └── CompetitionDashboard.js  # ADD episode timeline
│   │   └── components/
│   │       └── ui/                 # shadcn components - use these
│   └── package.json
├── PICKTV_ONBOARDING_PROMPT.md    # DETAILED implementation guide
├── CORE_AUCTION_ENGINE.md         # Auction documentation
├── SHARED_CODEBASE.md             # What's shared
├── DATABASE_SCHEMA.md             # MongoDB collections
├── API_REFERENCE.md               # All endpoints
└── docs/                          # Additional documentation
```

---

## ENVIRONMENT

- **Backend:** FastAPI on port 8001
- **Frontend:** React on port 3000
- **Database:** MongoDB (use `MONGO_URL` from .env)
- **Real-time:** Socket.IO with Redis

**DO NOT change ports or create new services.**

---

## TESTING APPROACH

1. **Inherited features:** Just verify they work (quick smoke test)
2. **New features:** Use testing subagent for thorough testing
3. **Auction flow:** Test with 2+ browser windows

---

## COMMUNICATION WITH USER

Before starting implementation:

1. Confirm you have read `PICKTV_ONBOARDING_PROMPT.md`
2. Summarize your understanding of what's inherited vs new
3. Propose Phase 1 implementation plan
4. Ask about sample show data (e.g., Survivor 47 contestants)

---

## SUCCESS CRITERIA

Pick TV MVP is complete when:

- [ ] Can create a "Reality TV" league
- [ ] Can add contestants to a show
- [ ] Auction works with contestants (not clubs)
- [ ] Commissioner can enter episode results
- [ ] Points calculate based on survival/eliminations
- [ ] Standings reflect elimination scoring
- [ ] UI shows "Contestants" not "Clubs"
- [ ] UI shows "⭐" not "£"

---

## START HERE

```bash
# 1. Verify codebase exists
ls /app/backend/server.py

# 2. Read onboarding document
cat /app/PICKTV_ONBOARDING_PROMPT.md

# 3. Check current sports in database
mongosh --quiet --eval "db.sports.find({}, {_id:0, key:1, name:1})" test_database

# 4. Report back to user with your understanding and proposed plan
```

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
