# Auction Reset Feature

## Overview
Allows commissioners to reset an auction and start fresh without recreating the league or re-inviting participants.

## Implementation

### Backend Endpoint
**Endpoint:** `POST /api/leagues/{league_id}/auction/reset`

**Authorization:** Commissioner only

**Requirements:**
- Auction must be paused or completed (cannot reset active auction)

**What It Does:**
1. Deletes all bids for the auction
2. Resets all participant data:
   - Clears `clubsWon` arrays
   - Resets `budgetRemaining` to original league budget
   - Resets `totalSpent` to 0
3. Deletes league_points records
4. Deletes standings records
5. Deletes the auction record
6. Sets league status back to "draft"

**What It Preserves:**
- League configuration (budget, slots, timer settings)
- Selected teams (`assetsSelected`)
- Fixtures (if imported)
- Participants (users remain joined to the league)

### Frontend Implementation
**File:** `/app/frontend/src/pages/AuctionRoom.js`

**Button Location:** In Commissioner Controls section (next to Pause/Resume buttons)

**Visibility:** Shows only when:
- User is commissioner
- Auction status is "paused" OR "completed"

**Button:** 🔄 Reset (orange button)

**Confirmation Dialog:** Explains what will be reset and preserved

**On Success:** Redirects to Competition Detail Page (`/league/:leagueId`) where commissioner can click "Start Auction" again

## User Flow

1. Commissioner pauses auction (if active)
2. Commissioner clicks "🔄 Reset" button in AuctionRoom
3. Confirms reset action in dialog
4. System resets auction data and participant rosters
5. Commissioner is redirected to Competition Detail Page
6. Commissioner clicks "Start Auction" to begin fresh
7. New auction starts with same participants, same teams, clean slate

## Testing Checklist

- [ ] Reset button appears for commissioner when auction is paused
- [ ] Reset button appears for commissioner when auction is completed
- [ ] Reset button does NOT appear when auction is active
- [ ] Reset button does NOT appear for non-commissioners
- [ ] Confirmation dialog displays correctly
- [ ] API call succeeds and returns success message
- [ ] Participants' budgets are reset to full amount
- [ ] Participants' clubsWon arrays are cleared
- [ ] All bids are deleted
- [ ] Auction record is deleted
- [ ] League status is set to "draft"
- [ ] Redirects to Competition Detail Page after reset
- [ ] Commissioner can start new auction successfully
- [ ] Participants remain in league (no need to re-invite)
- [ ] Selected teams are preserved
- [ ] Fixtures are preserved (if imported)

## Notes

- No socket.io events emitted (to avoid complexity near deployment)
- Frontend handles redirect after success
- League configuration remains unchanged
- Participants can immediately join the new auction without re-invitation
