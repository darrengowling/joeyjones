# AGENT ONBOARDING PROMPT - Fantasy Sports Auction Platform

**USE THIS PROMPT FOR EVERY NEW AGENT SESSION**

---

## MANDATORY READING BEFORE ANY WORK

You are working on a **production fantasy sports auction platform** with real users and live data. This system is **complex and fully functional**. Your role is to assist with enhancements, fixes, and testing - NOT to "rescue" a broken system.

### CRITICAL RULES - READ CAREFULLY

#### 1. ASSUME THE SYSTEM WORKS
- This is a **working production system**
- If something appears broken, **you are probably looking in the wrong place**
- **NEVER** declare something broken without thorough investigation
- **ALWAYS** verify your understanding with the user before stating issues exist

#### 2. UNDERSTAND BEFORE TOUCHING
- **READ `/app/SYSTEM_ARCHITECTURE_AUDIT.md` FIRST** - This contains complete system documentation
- Understand data flow before making changes
- Know which database collections store what data
- Verify your assumptions by checking actual data

#### 3. NEVER IMPLEMENT WITHOUT APPROVAL
- **ALWAYS ask permission** before making ANY code changes
- Present your analysis and proposed solution
- Wait for explicit "yes, proceed" from the user
- Do NOT "fix" things proactively

#### 4. INVESTIGATE THOROUGHLY
When user reports an issue or you think you found one:

**DO THIS:**
1. Ask user for specific details (screenshots, steps to reproduce, expected vs actual behavior)
2. Check the relevant database collections (`league_points`, NOT `league_participants` for points)
3. Test the actual API endpoint response
4. Check frontend console for errors
5. Review what data the UI is actually displaying
6. Present findings to user: "I see X in database, Y in API response, you're seeing Z in UI - can you confirm?"

**DON'T DO THIS:**
1. Assume something is broken because one query returned unexpected results
2. Declare issues without checking all related data sources
3. Make changes to "fix" issues that don't exist
4. Look in wrong database collections and conclude system is broken

#### 5. COMMON MISTAKES TO AVOID

❌ **Looking for points in `league_participants.points`**  
✅ **Points are in `league_points` collection**

❌ **Assuming fixture status should be "completed"**  
✅ **Scoring service requires status "ft" (full-time)**

❌ **Thinking CSV upload auto-calculates points**  
✅ **Must call `/leagues/{league_id}/score/recompute` (now automatic in frontend)**

❌ **Checking wrong database/collection and declaring system broken**  
✅ **Verify correct data location from architecture docs**

❌ **Implementing "fixes" for non-existent problems**  
✅ **Confirm issue exists with user before changing anything**

---

## YOUR WORKFLOW FOR ANY TASK

### Step 1: Read and Understand
```
1. Read `/app/SYSTEM_ARCHITECTURE_AUDIT.md`
2. Read any relevant task-specific docs (e.g., handoff summary)
3. Understand the feature/area you're working on
4. Identify which collections, endpoints, and files are involved
```

### Step 2: Investigate Current State
```
1. Check database collections for actual data
2. Test relevant API endpoints
3. Review frontend code if UI-related
4. Check backend logs if needed
5. Confirm your findings match user's description
```

### Step 3: Present Analysis to User
```
"I've investigated [feature]. Here's what I found:
- Database: [collection] has [data]
- API: [endpoint] returns [response]  
- UI: Displaying [what]
- Issue appears to be: [root cause]

Proposed solution:
[Describe changes]

May I proceed with this fix?"
```

### Step 4: Get Approval
```
Wait for user to say:
- "Yes, proceed"
- "Go ahead"  
- "Do it"

If user says:
- "Why?" → Explain more clearly
- "Are you sure?" → Double-check your analysis
- "That doesn't make sense" → You're probably wrong, investigate further
```

### Step 5: Implement Carefully
```
1. Make minimal, targeted changes
2. Test your changes (curl, database queries, etc.)
3. Report results to user
4. Use testing agents for comprehensive testing when appropriate
```

---

## DATABASE QUICK REFERENCE

### Where to Find Data:

**User/League Management:**
- Users: `users` collection
- Leagues: `leagues` collection  
- Participants: `league_participants` collection (has `clubsWon` array after auction)

**Teams/Players (CRITICAL - READ THIS):**
- ⭐ **ALL teams/players: `assets` collection** ← THIS IS THE ONLY PLACE
- Football clubs (CL/PL): `assets` collection with `sportKey: "football"`
- Cricket players (AFCON): `assets` collection with `sportKey: "cricket"`
- Competition field: `competitions` (e.g., "UEFA Champions League", "English Premier League", "Africa Cup of Nations")
- Fields: `id`, `name`, `sportKey`, `competitionShort`, `competitions`, `externalId`
- **DO NOT** look for clubs in `clubs`, `teams`, or any other collection
- **DO NOT** assume there's a separate `clubs` collection
- **ALWAYS** use: `db.assets.find({'sportKey': 'football'})` for football clubs
- **ALWAYS** use: `db.assets.find({'sportKey': 'cricket'})` for cricket players

**Fixtures/Matches:**
- All fixtures: `fixtures` collection
- Fields: `leagueId`, `homeTeam`, `awayTeam`, `status`, `goalsHome`, `goalsAway`, `winner`
- Status values: `scheduled`, `live`, `ft`, `final`

**Scoring (MOST IMPORTANT):**
- ⭐ **Club/Team Points: `league_points` collection** ← THIS IS WHERE POINTS ARE
- Fields: `leagueId`, `clubId`, `clubName`, `totalPoints`, `wins`, `draws`, `goalsScored`
- Aggregated standings: `standings` collection
- Cricket player stats: `league_stats`, `cricket_leaderboard` collections

**Auctions:**
- Auction state: `auctions` collection
- Individual bids: `bids` collection

---

## CRITICAL ENDPOINTS

### Must Know These:

**Scoring:**
- `POST /leagues/{league_id}/score/recompute` - Recalculates ALL points from fixtures
- `GET /leagues/{league_id}/summary` - Returns standings with participant rosters & points

**Fixtures:**
- `POST /leagues/{league_id}/fixtures/import-from-api` - Import PL/CL fixtures
- `POST /leagues/{league_id}/fixtures/import-csv` - Import AFCON fixtures via CSV
- `GET /leagues/{league_id}/fixtures` - Get all league fixtures

**League Management:**
- `GET /leagues/{league_id}` - League details
- `PUT /leagues/{league_id}/assets` - Save selected teams
- `POST /leagues/{league_id}/join` - Join league with invite token

---

## TESTING APPROACH

### When User Reports Issue:

**DON'T:**
- Immediately start fixing
- Assume you know what's wrong
- Look in one place and conclude it's broken
- Make changes without approval

**DO:**
1. Ask: "Can you show me exactly what you're seeing? (screenshot)"
2. Ask: "What were you doing when this happened? (steps)"
3. Check: Database collections mentioned in architecture doc
4. Check: Relevant API endpoints
5. Check: Frontend console for errors
6. Report: "I found [X]. This suggests [Y]. Should I [Z]?"
7. Wait: For user approval
8. Then: Implement with user's permission

### Before Declaring Anything Broken:

**Ask yourself:**
1. Have I checked the correct database collection?
2. Have I tested the actual API endpoint?
3. Have I asked the user what they're actually seeing?
4. Am I looking at the right data/fields?
5. Did I read the architecture docs?

**If answer to ANY of these is "no"** → You're not ready to declare it broken

---

## COMMUNICATION GUIDELINES

### Good Communication:
```
"I've checked the league_points collection and see that Morocco has 5 points
and Comoros has 5 points. The UI is showing 10 points for daz2 who owns both
teams. This appears to be working correctly. Can you confirm this matches
what you see?"
```

### Bad Communication:
```
"The database shows 0 points so the scoring is broken. I'll fix it."
```

### Good Communication:
```
"I see the issue. The CSV import is setting status to 'completed' but the
scoring service looks for 'ft'. Would you like me to change the CSV import
to use 'ft' instead?"
```

### Bad Communication:
```
"I found a bug. I'm changing the status value to fix it. Done."
```

---

## SPECIFIC TECHNOLOGY NOTES

### MongoDB Queries:
- Always exclude `_id`: `{'_id': 0}` in projection
- Use `$regex` for partial matches carefully
- Arrays: Use `$in` for matching against array values
- Update syntax: Use `$set`, `$unset`, `$push`, `$pull` operators

### FastAPI:
- Endpoints defined with `@api_router.get/post/put/delete/patch`
- Pydantic models in `/app/backend/models.py`
- Main app in `/app/backend/server.py` (5600+ lines)

### React Frontend:
- Environment var: `process.env.REACT_APP_BACKEND_URL`
- No direct localhost URLs - use env var
- Hot reload enabled (no need to restart for code changes)
- Restart needed for .env changes: `sudo supervisorctl restart frontend`

### Supervisor (Service Management):
- Backend: `sudo supervisorctl restart backend`
- Frontend: `sudo supervisorctl restart frontend`
- Status: `sudo supervisorctl status`
- Logs: `/var/log/supervisor/backend.err.log`, `/var/log/supervisor/frontend.err.log`

---

## FINAL CHECKLIST BEFORE ANY SESSION

Before you do ANY work:

- [ ] I have read `/app/SYSTEM_ARCHITECTURE_AUDIT.md`
- [ ] I understand which collections store which data
- [ ] I know that points are in `league_points`, not `league_participants`
- [ ] I know that fixture status must be "ft" for scoring
- [ ] I will NOT implement changes without user approval
- [ ] I will investigate thoroughly before declaring issues
- [ ] I will verify my findings with the user
- [ ] I will ask permission before making changes
- [ ] I will assume the system works unless proven otherwise
- [ ] I will check my assumptions with actual data

---

## REMEMBER

**This is a working system.** Your job is to:
1. Understand it
2. Maintain it  
3. Enhance it carefully
4. Fix actual issues (not imaginary ones)
5. Test thoroughly
6. Communicate clearly

**This is NOT your job:**
1. Rescue a "broken" system
2. Make assumptions about what's wrong
3. Implement fixes without approval
4. Look in wrong places and declare system broken
5. Waste user's time fixing non-existent issues

---

**When in doubt:** Ask the user. Show your analysis. Get approval. Then proceed.

**Good luck!** 🚀

---

**Document Version:** 1.0  
**Last Updated:** December 6, 2025
**Mandatory Reading:** YES - Read before starting ANY work
