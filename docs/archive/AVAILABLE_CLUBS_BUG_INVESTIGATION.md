# Available Clubs Display Bug - Investigation & Fix Plan

**Issue:** After selecting and saving teams for competition, the "Available clubs in competition" section still shows "No clubs available"

---

## Root Cause Analysis

### Current Backend Endpoints:

**1. `GET /leagues/{league_id}/assets`** (line 1306)
- Returns: ALL assets for the sport (100+ clubs)
- Purpose: For team selection modal
- Issue: Does NOT filter by `assetsSelected`

**2. `GET /leagues/{league_id}/available-assets`** (line 2586)  
- Returns: ALL assets for the sport (100+ clubs)
- Purpose: Same as above
- Issue: Also does NOT filter by `assetsSelected`

**3. `PUT /leagues/{league_id}/assets`** (line 2519)
- Updates: `league.assetsSelected` field ✅
- Works correctly

### The Bug:

**Frontend** (LeagueDetail.js line 269):
```javascript
const response = await axios.get(`${API}/leagues/${leagueId}/assets`);
setAssets(response.data.assets || []);
```

This calls an endpoint that returns ALL assets, not the SELECTED assets.

**Backend Behavior:**
- Both endpoints return all 100+ assets for the sport
- Neither endpoint filters by `league.assetsSelected`
- The selected assets are stored but never retrieved

**Database Evidence:**
- League "prem5" has `assetsSelected: [6 team IDs]`
- But endpoint returns all ~100 football clubs
- Frontend likely filters somehow? Let me check...

### Why Shows "No clubs available"?

Looking at line 633-634:
```javascript
assets.length === 0 ? (
  <p>No clubs available.</p>
)
```

So `assets` array is EMPTY. But backend returns 100+ clubs...

**Ah! The issue might be:**
- Backend returns `{ assets: [...], total: 100 }`
- Frontend expects `response.data.assets`
- But response might be malformed?

OR

- There's conditional logic that filters assets
- And that filter returns empty array

Let me check what the actual issue is by testing...

---

## Solution

### Option 1: Create New Endpoint (Cleanest)

Create `GET /leagues/{league_id}/selected-assets` that returns ONLY the selected assets:

```python
@api_router.get("/leagues/{league_id}/selected-assets")
async def get_selected_assets_for_league(league_id: str):
    """Get the assets that have been selected for this league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    selected_asset_ids = league.get("assetsSelected", [])
    
    if not selected_asset_ids:
        return {"assets": [], "total": 0}
    
    # Fetch the actual asset data for selected IDs
    assets = await db.assets.find(
        {"id": {"$in": selected_asset_ids}},
        {"_id": 0}
    ).to_list(len(selected_asset_ids))
    
    return {
        "assets": assets,
        "total": len(assets)
    }
```

### Option 2: Modify Existing Endpoint (Simpler)

Modify `GET /leagues/{league_id}/assets` to check if assets have been selected:

```python
@api_router.get("/leagues/{league_id}/assets")
async def get_league_assets(league_id: str, ...):
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")
    selected_asset_ids = league.get("assetsSelected", [])
    
    # If assets have been selected, return only those
    if selected_asset_ids:
        assets = await db.assets.find(
            {"id": {"$in": selected_asset_ids}},
            {"_id": 0}
        ).to_list(len(selected_asset_ids))
        return {
            "assets": assets,
            "total": len(assets),
            "page": 1,
            "pageSize": len(assets)
        }
    
    # Otherwise return all assets for selection
    # ... existing code ...
```

---

## Recommended Fix: Option 1

Create a new endpoint specifically for displaying selected assets. This is cleaner because:
- Separates concerns (selection vs display)
- Doesn't break existing team selection flow
- Clear intent in endpoint name
- Frontend change is minimal

### Implementation Steps:

1. **Backend:** Add new endpoint `GET /leagues/{league_id}/selected-assets`
2. **Frontend:** Change LeagueDetail.js line 269 to call new endpoint
3. **Test:** Verify selected teams display correctly

---

## Testing Plan:

1. Create new competition
2. Select 6 teams and save
3. Verify "Available clubs in competition" shows those 6 teams
4. Verify team names and details display correctly
5. Test with both football and cricket
6. Verify empty state shows when no teams selected yet

---

**Ready for approval to implement Option 1.**
