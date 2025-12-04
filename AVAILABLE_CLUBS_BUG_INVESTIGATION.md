# Available Clubs Display Bug - Investigation & Fix Plan

**Issue:** After selecting and saving teams for competition, the "Available clubs in competition" section still shows "No clubs available"

---

## Root Cause Analysis

### What Happens:

1. User creates competition
2. User selects teams (e.g., 10 clubs) and saves
3. Frontend calls `PUT /leagues/{league_id}/assets` with selected asset IDs
4. Backend stores these in `league.assetsSelected` field ✅
5. User views LeagueDetail page
6. Frontend calls `GET /leagues/{league_id}/assets`
7. **Backend returns ALL assets for the sport** (100+ clubs)
8. Frontend displays these correctly

**But wait... user reports "No clubs available"?**

Let me re-examine...

### Actually Looking at Code More Carefully:

The endpoint `GET /leagues/{league_id}/assets` (line 1306) returns:
- For football: ALL football clubs from database
- For cricket: ALL cricket assets from asset_service

This is CORRECT for the team selection modal (where you choose which teams to include).

But for the "Available clubs in competition" section (line 629), it should show:
- Only the SELECTED teams (from `league.assetsSelected`)
- Not all possible teams

### The Real Bug:

The frontend is calling the WRONG endpoint!

**Line 269:** `const response = await axios.get(`${API}/leagues/${leagueId}/assets`);`

This endpoint returns ALL assets for selection, not the selected assets for the competition.

There's actually a separate endpoint: `GET /leagues/{league_id}/available-assets` (line 2586)

Let me check what that does...

---

## Backend Endpoint Investigation

### Endpoint 1: `/leagues/{league_id}/assets` (line 1306)
**Purpose:** Get all available assets for team selection  
**Returns:** All clubs/players for that sport  
**Used by:** Team selection modal

### Endpoint 2: `/leagues/{league_id}/available-assets` (line 2586)
**Purpose:** Unknown, need to check

Let me examine this endpoint...
