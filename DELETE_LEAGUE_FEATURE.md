# Delete League Feature

## Overview
Added functionality for league commissioners to delete leagues, keeping the UI clean during testing.

## Features

### Authorization
- ✅ Only the commissioner can delete their league
- ✅ Returns 403 error if non-commissioner attempts to delete
- ✅ Confirmation dialog prevents accidental deletion

### Cascade Delete
When a league is deleted, the system automatically removes:
1. **League** record
2. **All participants** in the league
3. **Associated auction** (if exists)
4. **All bids** for that auction

This ensures no orphaned data remains in the database.

## Backend Implementation

### Endpoint
```
DELETE /api/leagues/{league_id}?user_id={user_id}
```

**Query Parameters:**
- `user_id` (required): ID of the user attempting to delete

**Authorization:**
- Verifies user is the league commissioner
- Returns 403 if not authorized

**Response:**
```json
{
  "message": "League deleted successfully"
}
```

**Error Responses:**
- 404: League not found
- 403: Only the commissioner can delete this league

### Database Operations
```python
# 1. Delete league
await db.leagues.delete_one({"id": league_id})

# 2. Delete all participants
await db.league_participants.delete_many({"leagueId": league_id})

# 3. Find and delete auction
auction = await db.auctions.find_one({"leagueId": league_id})
if auction:
    # Delete all bids
    await db.bids.delete_many({"auctionId": auction["id"]})
    # Delete auction
    await db.auctions.delete_one({"id": auction["id"]})
```

## Frontend Implementation

### League Detail Page
**Location**: `/league/{leagueId}`

**Delete Button:**
- Visible only to commissioner
- Red color for clear warning
- Positioned next to "Start Auction" button

**Confirmation Dialog:**
```
Are you sure you want to delete "{league.name}"? 
This will remove all participants, auction data, and bids. 
This action cannot be undone.
```

**Success:**
- Shows alert: "League deleted successfully"
- Redirects to homepage

### Home Page (League Cards)
**Quick Delete:**
- Small 🗑️ Delete button on each league card
- Only visible to commissioner
- Click stops propagation (doesn't navigate to league detail)
- Same confirmation dialog
- Refreshes league list after deletion

## UI Elements

### League Detail Page
```jsx
{isCommissioner && (
  <button
    onClick={deleteLeague}
    className="px-6 py-3 rounded-lg font-semibold bg-red-600 text-white hover:bg-red-700"
    data-testid="delete-league-button"
  >
    Delete League
  </button>
)}
```

### Home Page League Card
```jsx
{isCommissioner && (
  <button
    onClick={(e) => handleDeleteLeague(league, e)}
    className="text-red-600 hover:text-red-800 text-sm font-semibold"
    data-testid={`delete-league-${league.id}`}
  >
    🗑️ Delete
  </button>
)}
```

## Testing

### Test Basic Delete
```bash
# Create league
USER_ID="<user-id>"
LEAGUE_ID="<league-id>"

# Delete league
curl -X DELETE "http://localhost:8001/api/leagues/$LEAGUE_ID?user_id=$USER_ID"
# Response: {"message": "League deleted successfully"}

# Verify deletion
curl http://localhost:8001/api/leagues/$LEAGUE_ID
# Response: {"detail":"League not found"}
```

### Test Authorization
```bash
# Try to delete with wrong user ID
curl -X DELETE "http://localhost:8001/api/leagues/$LEAGUE_ID?user_id=wrong-user-id"
# Response: {"detail":"Only the commissioner can delete this league"}
```

### Test Cascade Delete
```bash
# 1. Create league, join participants, start auction, place bids
# 2. Delete league
# 3. Verify all associated data is deleted:
#    - League: deleted
#    - Participants: deleted
#    - Auction: deleted
#    - Bids: deleted
```

See script in this file for full cascade delete test.

## Use Cases

### During Testing
1. **Cleanup Test Leagues**: Commissioners can quickly remove test leagues
2. **Reset Testing Environment**: Delete leagues with incorrect configurations
3. **Remove Abandoned Leagues**: Clean up leagues where participants didn't join

### Production Considerations
For production use, consider adding:
- Soft delete (mark as deleted, don't remove from DB)
- Audit trail (log who deleted what and when)
- Restore functionality (undo delete within time window)
- Archive data instead of permanent deletion
- Email notifications to all participants

## Safety Features

1. **Confirmation Dialog**: Prevents accidental deletion
2. **Authorization Check**: Only commissioner can delete
3. **Clear Warning Message**: Explains what will be deleted
4. **Cascade Delete**: Ensures no orphaned data
5. **Visual Indicators**: Red color for delete buttons

## Benefits for Testing

- ✅ **Clean UI**: Remove test leagues easily
- ✅ **Quick Reset**: Start fresh without database cleanup
- ✅ **Reduced Confusion**: Fewer abandoned leagues in list
- ✅ **Better UX**: Clear visual hierarchy of active leagues
- ✅ **Data Integrity**: Complete cleanup with cascade delete

## Example Usage

### Frontend (Manual Test)
1. Sign in as league commissioner
2. Navigate to league detail page
3. Click "Delete League" button
4. Confirm in dialog
5. Redirected to homepage
6. League no longer appears in list

### Frontend (Quick Delete from Home)
1. Sign in as league commissioner
2. Find your league in the list
3. Click 🗑️ Delete button on card
4. Confirm in dialog
5. League removed from list

### API (Programmatic)
```bash
# Get user and league IDs
USER_ID="9f2d3cdf-b338-425a-9f77-a6e2e28b9637"
LEAGUE_ID="2789ba4b-16ff-4e38-909f-006d4c993749"

# Delete league
curl -X DELETE "http://localhost:8001/api/leagues/$LEAGUE_ID?user_id=$USER_ID" \
  -H "Content-Type: application/json"
```

## Summary

The delete league feature provides a safe and efficient way to remove test leagues during development, with proper authorization checks and cascade deletion to maintain data integrity. Commissioners can delete leagues from both the league detail page and the homepage, with clear confirmation dialogs preventing accidental deletion.
