# Prompt 2 Implementation: Wire assetsSelected Through Endpoints

## Summary

Successfully wired the `assetsSelected` field through all create/update/read endpoints with proper logging to ensure the field is saved and returned correctly in all league operations.

## Changes Made

### 1. POST /api/leagues - Create with assetsSelected

**File:** `/app/backend/server.py` (lines 334-351)

**Changes:**
- Added structured logging after league creation
- Logs include: `leagueId`, `count`, `sportKey`, `mode` (selected/all)

```python
@api_router.post("/leagues", response_model=League, ...)
async def create_league(input: LeagueCreate):
    league_obj = League(**input.model_dump())
    await db.leagues.insert_one(league_obj.model_dump())
    
    # Metrics: Track league creation
    metrics.increment_league_created(input.sportKey)
    
    # Prompt 2: Log asset selection persistence
    assets_selected = league_obj.assetsSelected or []
    logger.info("league.assets_selection.persisted", extra={
        "leagueId": league_obj.id,
        "count": len(assets_selected),
        "sportKey": league_obj.sportKey,
        "mode": "selected" if assets_selected else "all"
    })
    
    return league_obj
```

**How it works:**
- Pydantic's `model_dump()` automatically includes all fields including `assetsSelected`
- Database insert persists the complete object
- Response model returns all fields including `assetsSelected`
- Logging tracks whether specific assets were selected or "all" mode

### 2. GET /api/leagues/{id} - Return assetsSelected

**File:** `/app/backend/server.py` (lines 389-394)

**Status:** Already working correctly ✅

```python
@api_router.get("/leagues/{league_id}", response_model=League)
async def get_league(league_id: str):
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return League(**league)  # ← Pydantic automatically includes assetsSelected
```

**How it works:**
- MongoDB returns complete document including `assetsSelected`
- `League(**league)` deserializes with all fields
- `response_model=League` ensures consistent schema

### 3. GET /api/leagues - Return assetsSelected in List

**File:** `/app/backend/server.py` (lines 353-361)

**Status:** Already working correctly ✅

```python
@api_router.get("/leagues", response_model=List[League])
async def get_leagues(sportKey: Optional[str] = None):
    query = {}
    if sportKey:
        query["sportKey"] = sportKey
    
    leagues = await db.leagues.find(query).to_list(100)
    return [League(**league) for league in leagues]  # ← Includes assetsSelected
```

**How it works:**
- Each league document is deserialized as `League` model
- All fields including `assetsSelected` are included
- Response model enforces consistent schema for list

### 4. PUT /api/leagues/{id}/assets - Update assetsSelected

**File:** `/app/backend/server.py` (lines 858-912)

**Changes:**
- Added structured logging after successful update
- Logs include: `leagueId`, `count`, `sportKey`, `mode`

```python
@api_router.put("/leagues/{league_id}/assets")
async def update_league_assets(league_id: str, asset_ids: List[str]):
    # ... validation logic ...
    
    # Update league with selected assets
    await db.leagues.update_one(
        {"id": league_id},
        {"$set": {"assetsSelected": cleaned_asset_ids}}
    )
    
    # Prompt 2: Log asset selection update
    logger.info("league.assets_selection.updated", extra={
        "leagueId": league_id,
        "count": len(cleaned_asset_ids),
        "sportKey": sport_key,
        "mode": "selected"
    })
    
    return {"message": f"Updated league with {len(cleaned_asset_ids)} selected teams", 
            "count": len(cleaned_asset_ids)}
```

**How it works:**
- MongoDB `$set` updates the `assetsSelected` field
- Logging tracks the update with asset count
- Response confirms the operation

## Testing Results

All tests passed ✅

### Test 1: POST /api/leagues - Save and Return
```
✅ League created with 9 selected assets
✅ CREATE response includes correct assetsSelected: 9 items
```

### Test 2: GET /api/leagues/{id} - Retrieve
```
✅ League retrieved
✅ GET response includes correct assetsSelected: 9 items
```

### Test 3: GET /api/leagues - List
```
✅ Retrieved 14 leagues
✅ LIST response includes correct assetsSelected: 9 items
```

### Test 4: PUT /api/leagues/{id}/assets - Update
```
✅ Assets updated: Updated league with 5 selected teams
✅ Update persisted correctly: 5 items
```

### Test 5: Backward Compatibility
```
✅ League created without assetsSelected
✅ CREATE response correctly handles missing assetsSelected (None)
✅ GET response correctly handles missing assetsSelected (None)
```

### Test 6: Logging Verification
```
✅ Found 'league.assets_selection.persisted' log entry
✅ Found 'league.assets_selection.updated' log entry
```

## Log Samples

### Create League with Assets
```json
{
  "level": "INFO",
  "logger": "server",
  "message": "league.assets_selection.persisted",
  "leagueId": "11a6ca2f-bd75-4561-a4c0-2c94b7fc318c",
  "count": 9,
  "sportKey": "football",
  "mode": "selected"
}
```

### Update League Assets
```json
{
  "level": "INFO",
  "logger": "server",
  "message": "league.assets_selection.updated",
  "leagueId": "11a6ca2f-bd75-4561-a4c0-2c94b7fc318c",
  "count": 5,
  "sportKey": "football",
  "mode": "selected"
}
```

### Create League without Assets (All Teams)
```json
{
  "level": "INFO",
  "logger": "server",
  "message": "league.assets_selection.persisted",
  "leagueId": "60b52f98-a034-40b9-9a91-ec18205b8927",
  "count": 0,
  "sportKey": "football",
  "mode": "all"
}
```

## API Request/Response Examples

### Creating League with Selected Assets

**Request:**
```bash
POST /api/leagues
{
  "name": "Premier League Fantasy",
  "commissionerId": "user-123",
  "sportKey": "football",
  "budget": 500000000,
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,
  "assetsSelected": [
    "club-id-1",
    "club-id-2",
    "club-id-3"
  ]
}
```

**Response:**
```json
{
  "id": "league-uuid",
  "name": "Premier League Fantasy",
  "commissionerId": "user-123",
  "sportKey": "football",
  "budget": 500000000,
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 3,
  "status": "pending",
  "inviteToken": "abc123de",
  "assetsSelected": [
    "club-id-1",
    "club-id-2",
    "club-id-3"
  ],
  "createdAt": "2025-01-15T10:30:00Z",
  "timerSeconds": 30,
  "antiSnipeSeconds": 10
}
```

### Retrieving League

**Request:**
```bash
GET /api/leagues/{league_id}
```

**Response:**
```json
{
  "id": "league-uuid",
  "name": "Premier League Fantasy",
  "assetsSelected": [
    "club-id-1",
    "club-id-2",
    "club-id-3"
  ],
  // ... other fields ...
}
```

### Updating League Assets

**Request:**
```bash
PUT /api/leagues/{league_id}/assets
[
  "club-id-4",
  "club-id-5",
  "club-id-6"
]
```

**Response:**
```json
{
  "message": "Updated league with 3 selected teams",
  "count": 3
}
```

## Database Schema

MongoDB documents now correctly store `assetsSelected`:

```javascript
{
  "_id": ObjectId("..."),
  "id": "league-uuid",
  "name": "My League",
  "commissionerId": "user-uuid",
  "sportKey": "football",
  "budget": 500000000,
  "clubSlots": 3,
  "assetsSelected": [    // ✅ Persisted correctly
    "club-id-1",
    "club-id-2",
    "club-id-3"
  ],
  "status": "pending",
  "inviteToken": "abc123de",
  "createdAt": ISODate("2025-01-15T10:30:00Z"),
  "timerSeconds": 30,
  "antiSnipeSeconds": 10
}
```

## Error Handling

All endpoints properly handle:

1. **Missing Field** - Returns `null` or omits field (backward compatible)
2. **Empty Array** - Converted to `null` by validation (treated as "all")
3. **Invalid Asset IDs** - Rejected with 400 error
4. **Update After Auction Start** - Rejected with 400 error

## Acceptance Criteria Verification

✅ **After create/edit, retrieving the league shows the assetsSelected array**
- POST response includes field
- GET by ID includes field
- GET list includes field
- PUT updates persist correctly

✅ **No exceptions when the field is absent**
- Leagues without `assetsSelected` work correctly
- Field returns as `null` in responses
- No database errors or crashes

✅ **Logging present for persistence and updates**
- Create operations log with `league.assets_selection.persisted`
- Update operations log with `league.assets_selection.updated`
- Logs include structured data (leagueId, count, mode, sportKey)

## Files Modified

1. `/app/backend/server.py`
   - Added logging to `POST /api/leagues` (line 344-349)
   - Added logging to `PUT /leagues/{league_id}/assets` (line 905-910)
   - GET endpoints already working correctly (no changes needed)

## Backward Compatibility

✅ **All existing endpoints continue to work**
- Leagues created before this feature have `assetsSelected: null`
- GET endpoints return `null` for missing field
- No breaking changes to API responses
- Default behavior: `null` = "include all teams"

## Integration with Auction System

The auction start logic already consumes `assetsSelected` from the league document:

```python
# From server.py lines 1288-1331
assets_selected = league.get("assetsSelected", [])

if FEATURE_ASSET_SELECTION and assets_selected and len(assets_selected) > 0:
    # Use commissioner's selected assets
    all_assets = await db.clubs.find({"id": {"$in": assets_selected}}).to_list(100)
else:
    # Use all available assets (default)
    all_assets = await db.clubs.find().to_list(100)
```

Since the field is now properly saved and retrieved, this integration works seamlessly.

## Next Steps

With Prompt 2 complete:
- ✅ Field is saved to database on create
- ✅ Field is updated via PUT endpoint
- ✅ Field is returned in all GET endpoints
- ✅ Logging tracks create and update operations
- ✅ Backward compatibility maintained

**Ready for next prompt or user testing.**
