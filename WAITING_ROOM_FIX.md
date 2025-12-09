# Waiting Room Participant Count Fix

**Issue:** Participants in the auction waiting room see "Participants Ready (0)" even after entering the waiting room.

**Root Cause:** 
- Backend was correctly storing `usersInWaitingRoom` array in MongoDB
- Backend Pydantic `Auction` model did not include this field
- When serializing auction data for API responses, Pydantic excluded the field
- Frontend received auction data without `usersInWaitingRoom`
- Frontend code `auction?.usersInWaitingRoom?.length || 0` always evaluated to 0

**Fix Applied:**
Added `usersInWaitingRoom` field to the Auction Pydantic model in `/app/backend/models.py`:

```python
usersInWaitingRoom: Optional[List[str]] = []  # Track users who have clicked "Enter Auction"
```

**Location:** Line 269 in `/app/backend/models.py`

**Impact:**
- ✅ GET `/api/auction/{auction_id}` now includes `usersInWaitingRoom` in response
- ✅ Frontend can now read the correct participant count
- ✅ Participants will see "Participants Ready (X)" with accurate count
- ✅ No changes to Socket.IO logic (zero risk to real-time functionality)
- ✅ Backward compatible (field is optional with default empty array)

**Testing:**
1. Backend restarted successfully after model change
2. API endpoint verified to include `usersInWaitingRoom` field
3. Ready for preview environment testing

**Next Steps:**
1. User to test in preview environment
2. Verify participant count updates correctly when users click "Enter Auction"
3. Deploy to production along with CL club name fixes
