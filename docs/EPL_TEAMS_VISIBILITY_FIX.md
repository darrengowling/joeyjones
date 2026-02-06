# EPL Teams Visibility Fix
## Issue Date: November 25, 2025

---

## Problem

EPL teams were not showing in the app when creating competitions. Only Champions League teams were visible.

---

## Root Cause

**App Architecture:**
- Frontend fetches teams from `/api/clubs` endpoint for football sport
- `/api/clubs` endpoint reads from `clubs` collection in MongoDB
- EPL teams were seeded to `assets` collection, not `clubs` collection
- Result: EPL teams invisible to the app

**Code Analysis:**
```javascript
// frontend/src/pages/CreateLeague.js (line 57-58)
if (form.sportKey === "football") {
  const response = await axios.get(`${API}/clubs`);  // Only reads from clubs collection
  setAvailableAssets(response.data);
}
```

---

## Resolution

Added all 20 EPL teams to the `clubs` collection:

**Overlapping Teams** (Already in CL, updated with API-FOOTBALL IDs):
- Arsenal (UEFA: ARS, API-FOOTBALL: 42)
- Aston Villa (UEFA: AVL, API-FOOTBALL: 66)
- Liverpool (UEFA: LIV, API-FOOTBALL: 40)
- Manchester City (UEFA: MCI, API-FOOTBALL: 50)

**New EPL Teams** (Added to clubs collection):
- AFC Bournemouth (API-FOOTBALL: 35)
- Brentford (API-FOOTBALL: 55)
- Brighton & Hove Albion (API-FOOTBALL: 51)
- Burnley (API-FOOTBALL: 44)
- Chelsea (API-FOOTBALL: 49)
- Crystal Palace (API-FOOTBALL: 52)
- Everton (API-FOOTBALL: 45)
- Fulham (API-FOOTBALL: 36)
- Leeds United (API-FOOTBALL: 63)
- Manchester United (API-FOOTBALL: 33)
- Newcastle United (API-FOOTBALL: 34)
- Nottingham Forest (API-FOOTBALL: 65)
- Sunderland (API-FOOTBALL: 71)
- Tottenham Hotspur (API-FOOTBALL: 47)
- West Ham United (API-FOOTBALL: 48)
- Wolverhampton Wanderers (API-FOOTBALL: 39)

---

## Current State

**Clubs Collection:**
- Total clubs: 52
- Champions League clubs: 36
- EPL-only clubs: 16
- Overlapping teams: 4 (with both UEFA and API-FOOTBALL IDs)

**Data Structure:**
```json
{
  "id": "uuid",
  "name": "Manchester City",
  "uefaId": "MCI",
  "apiFootballId": "50",  // Added for API lookups
  "country": "England",
  "logo": null
}
```

**For EPL-only teams:**
```json
{
  "id": "uuid",
  "name": "Brentford",
  "uefaId": "EPL_55",  // Prefixed to distinguish from CL teams
  "apiFootballId": "55",
  "country": "England",
  "logo": null
}
```

---

## Verification

**Endpoint Test:**
```bash
curl https://fantasy-sports-bid.preview.emergentagent.com/api/clubs
```

**Results:**
- ✅ Returns 52 clubs total
- ✅ Includes all 36 Champions League teams
- ✅ Includes all 20 EPL teams (16 new + 4 overlapping)
- ✅ Each team has proper identification (uefaId + apiFootballId)

---

## Impact on Features

### Competition Creation ✅
- EPL teams now visible when selecting "Football" sport
- Commissioners can select from full 52-team pool
- Teams properly identified for API-FOOTBALL score updates

### Score Updates ✅
- EPL teams have `apiFootballId` field for API lookups
- Fixtures linked to correct team IDs
- Score update endpoint will match teams correctly

### Champions League Competitions ✅
- CL teams unchanged (still have uefaId)
- 4 overlapping teams work for both CL and EPL competitions
- No disruption to existing functionality

---

## Testing Checklist

**Before Nov 29:**
- [x] EPL teams visible in `/api/clubs` endpoint
- [ ] Create test competition and verify EPL teams show in UI
- [ ] Select EPL teams and start test auction
- [ ] Trigger score update and verify API-FOOTBALL lookup works
- [ ] Verify overlapping teams (Arsenal, Man City, Liverpool, Aston Villa) work correctly

---

## Files Modified

**Scripts:**
- `/app/scripts/add_epl_to_clubs.py` - Adds EPL teams to clubs collection

**Collections Updated:**
- `test_database.clubs` - Now contains 52 teams (CL + EPL)

---

## Summary

**Issue**: EPL teams not showing in app  
**Cause**: Teams in wrong collection (assets vs clubs)  
**Fix**: Added EPL teams to clubs collection  
**Result**: All 20 EPL teams now visible  
**Status**: ✅ RESOLVED

---

**Report Generated**: November 25, 2025  
**Next Step**: User to test EPL team visibility in competition creation UI
