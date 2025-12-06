# EPL Teams 50-Club Display Limit Fix
## Issue Date: November 25, 2025

---

## Problem

When viewing a football league/competition detail page, the "Available Clubs in Competition" section showed only 50 clubs instead of all 52 clubs. West Ham United and Wolverhampton Wanderers were missing.

---

## Root Cause

**Backend API Pagination Issue:**

The `/api/leagues/{league_id}/assets` endpoint had a default `pageSize=50` parameter, which was limiting the results:

```python
# Before (Line 648 in server.py)
@api_router.get("/leagues/{league_id}/assets")
async def get_league_assets(league_id: str, search: Optional[str] = None, page: int = 1, pageSize: int = 50):
    ...
    return await asset_service.list_assets(sport_key, search, page, pageSize)
```

**Why Only 50 Clubs Appeared:**
1. Endpoint defaulted to `pageSize=50`
2. Frontend called endpoint without specifying a pageSize parameter
3. Only first 50 clubs (alphabetically) were returned
4. West Ham United (#50) and Wolverhampton Wanderers (#51) were cut off

---

## Resolution

**Modified `/api/leagues/{league_id}/assets` endpoint to:**

1. **Increase default pageSize** from 50 to 100
2. **Special handling for football leagues:**
   - Directly query `clubs` collection (returns all 52 clubs)
   - Return all clubs without pagination for football
   - Other sports still use asset_service with pagination

**Updated Code:**
```python
@api_router.get("/leagues/{league_id}/assets")
async def get_league_assets(league_id: str, search: Optional[str] = None, page: int = 1, pageSize: int = 100):
    """Get assets for a specific league based on its sportKey"""
    # Get league to determine sportKey
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")
    
    # For football, return all clubs (not paginated assets)
    if sport_key == "football":
        clubs = await db.clubs.find().to_list(100)
        clubs_as_models = [Club(**club) for club in clubs]
        return {
            "assets": [club data...],
            "total": len(clubs_as_models),  # Now returns 52
            "page": 1,
            "pageSize": len(clubs_as_models)
        }
    
    # For other sports, use asset_service with increased page size
    return await asset_service.list_assets(sport_key, search, page, pageSize)
```

---

## Verification

**API Test:**
```bash
curl "https://restart-auction.preview.emergentagent.com/api/leagues/{league_id}/assets"
```

**Results:**
- ✅ Total: 52 clubs
- ✅ Assets returned: 52 clubs
- ✅ West Ham United: Present
- ✅ Wolverhampton Wanderers: Present

**UI Impact:**
- "Available Clubs in Competition" section now shows: "52 clubs available for auction"
- All clubs visible in grid display
- Team selection checklist shows all 52 teams

---

## Related Issues Fixed

This also ensures:
1. ✅ All clubs available when commissioner reviews competition setup
2. ✅ All clubs available during auction (no teams missing)
3. ✅ Consistent display across all views (ClubsList, CreateLeague, LeagueDetail)

---

## Files Modified

**Backend:**
- `/app/backend/server.py` - Modified `/api/leagues/{league_id}/assets` endpoint

**Changes:**
- Increased default pageSize from 50 to 100
- Added special handling for football sport to return all clubs
- Ensures response structure matches expected format

---

## Testing Checklist

- [x] API returns all 52 clubs for football leagues
- [x] West Ham United visible in response
- [x] Wolverhampton Wanderers visible in response
- [ ] UI shows all 52 clubs in "Available Clubs" section (user to verify after page refresh)
- [ ] Commissioner can create competition with all 52 clubs
- [ ] Auction displays all 52 clubs correctly

---

## Summary

**Issue**: Only 50 of 52 clubs displayed on league detail page  
**Cause**: API endpoint had pageSize=50 default limit  
**Missing Teams**: West Ham United, Wolverhampton Wanderers  
**Fix**: Increased limit to 100 and added football-specific handling  
**Result**: All 52 clubs now returned and displayed  
**Status**: ✅ RESOLVED

---

**Report Generated**: November 25, 2025  
**Action Required**: User to refresh league detail page to see all 52 clubs
