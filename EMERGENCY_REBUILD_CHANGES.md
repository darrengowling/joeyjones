# Emergency Rebuild Prompt - Update Summary

**Date:** December 9, 2025  
**Status:** VERIFIED AND UPDATED

---

## Changes Made to Emergency Rebuild Document

### 1. Authentication System
**OLD**: Described traditional email/password registration  
**NEW**: Magic Link authentication (no passwords)
- 6-digit code sent to email
- JWT access + refresh tokens
- No `password` field in users collection

### 2. Database Schema Corrections

**Assets Collection (CRITICAL)**:
- ✅ Confirmed: ALL teams AND players in ONE `assets` collection
- ✅ Filter by `sportKey: "football"` for clubs
- ✅ Filter by `sportKey: "cricket"` for players
- ✅ NO separate `clubs` or `teams` collections
- ✅ Added exact competition names required:
  - "UEFA Champions League" (NOT "CL")
  - "English Premier League" (NOT "PL")
  - "Africa Cup of Nations" (NOT "AFCON")

**Leagues Collection**:
- ✅ Updated to match actual structure (budget, clubSlots, timerSeconds, antiSnipeSeconds)
- ✅ Added `competitionCode` field
- ✅ Removed outdated `participants` array (now in separate collection)

**League Participants Collection**:
- ✅ Added as separate collection (was embedded in old doc)
- ✅ Clarified: clubsWon array contains asset IDs
- ✅ Emphasized: Points NOT stored here

**Auctions Collection**:
- ✅ Added `usersInWaitingRoom` array (CRITICAL for waiting room feature)
- ✅ Added `bidSequence` monotonic counter
- ✅ Added pause-related fields
- ✅ Updated structure to match actual implementation

**Fixtures Collection**:
- ✅ Added `leagueId` field (CRITICAL for scoring)
- ✅ Added `homeTeamId`/`awayTeamId` fields
- ✅ Added `footballDataId` for API correlation
- ✅ Clarified status values: "ns", "live", "ft" (not "completed")

**League Points Collection**:
- ✅ Added as dedicated section
- ✅ Emphasized: THIS IS SOURCE OF TRUTH FOR SCORING
- ✅ Structure verified

**Standings Collection**:
- ✅ Added (was missing)
- ✅ Describes aggregated view

### 3. Critical Technical Details

**Team Name Matching**:
- ✅ NEW SECTION: Explains exact vs fuzzy matching
- ✅ Fixture import uses fuzzy (substring) matching
- ✅ Scoring uses exact matching
- ✅ All 56 teams must match API exactly
- ✅ References `/app/TEAM_UPDATES_COMPLETED.md`

**Socket.IO Enhancements**:
- ✅ Added `waiting_room_updated` event
- ✅ Explained Redis requirement for multi-pod
- ✅ Added conditional Redis setup code
- ✅ Clarified userId passed in event data (not session)

**Scoring Service**:
- ✅ Added `leagueId` filter requirement (prevents duplicate counting)
- ✅ Explained exact name matching requirement
- ✅ Added code example showing critical filter

**Pydantic Models**:
- ✅ Added requirement for `usersInWaitingRoom` field in Auction model

### 4. Frontend Structure Updates

**Pages**:
- ✅ Removed Login.js, Register.js (don't exist)
- ✅ MyCompetitions.js is home page with embedded auth
- ✅ Added ClubsList.js
- ✅ Added Help.js
- ✅ Added DebugFooter.js component

**Utils**:
- ✅ Added socket.js
- ✅ Added sentry.js

### 5. New Critical Gotchas Section

Added lessons learned from December 2025 fixes:
1. Team names MUST match API exactly (with detailed explanation)
2. Fixture import vs scoring - different matching logic
3. leagueId MUST be in fixtures (with code example)
4. usersInWaitingRoom field requirement
5. userId from event data (not session)

### 6. Environment Variables

**Backend**:
- ✅ Simplified to actual required vars
- ✅ Added REDIS_URL as optional
- ✅ Removed unused vars

**Frontend**:
- ✅ Simplified to essential REACT_APP_BACKEND_URL

### 7. Testing Checklist Updates

- ✅ Updated auth flow (magic link)
- ✅ Added waiting room participant count tests
- ✅ Added leagueId filter verification
- ✅ Added team name matching verification
- ✅ Added duplicate counting prevention test

### 8. References Added

Added links to critical documents:
- `/app/SYSTEM_ARCHITECTURE_AUDIT.md`
- `/app/TEAM_UPDATES_COMPLETED.md`
- `/app/AGENT_ONBOARDING_PROMPT.md`
- `/app/WAITING_ROOM_FIX_COMPLETE.md`

---

## Verification Method

All updates were verified by:
1. Querying actual MongoDB collections
2. Checking actual file structure
3. Reviewing current code implementation
4. Testing current production behavior
5. Zero assumptions or guesses made

---

## Files

- **Old version**: `/app/EMERGENCY_REBUILD_PROMPT_OLD.md` (preserved)
- **New version**: `/app/EMERGENCY_REBUILD_PROMPT.md` (active)
- **This summary**: `/app/EMERGENCY_REBUILD_CHANGES.md`

---

**The emergency rebuild prompt is now accurate and verified for the current production state.**
