# Waiting Room Feature - Complete Requirements Document

## OVERVIEW
The waiting room feature allows commissioners to coordinate auction starts so that all participants are present before bidding begins. Without this, users who join late miss the first 10-20 seconds of bidding.

---

## CURRENT BEHAVIOR (Reverted To)
1. Commissioner clicks "Start Auction"
2. Auction immediately created with `status="active"`
3. First team appears instantly with timer running
4. Users joining late miss early bids ❌

---

## DESIRED BEHAVIOR (To Implement)
1. Commissioner clicks "Start Auction"
2. Auction created with `status="waiting"`
3. All participants enter waiting room and see each other
4. Commissioner clicks "Begin Auction" when everyone ready
5. Auction changes to `status="active"` and first team appears
6. All users see first team simultaneously ✅

---

## BACKEND REQUIREMENTS

### 1. Auction Creation (POST /leagues/{league_id}/auction/start)

**Current (Reverted):**
```python
# Starts first lot immediately
status = "active"
currentLot = 1
currentClubId = first_club_id
# Emits 'lot_started' to auction room
```

**Required:**
```python
# Create in waiting state
status = "waiting"
currentLot = 0  # Not started yet
currentClubId = None
clubQueue = [shuffled_asset_ids]  # Prepared but not started

# Emit to league room
await sio.emit('league_status_changed', {
    'leagueId': league_id,
    'status': 'auction_created',
    'auctionId': auction_id
}, room=f"league:{league_id}")

return {"auctionId": auction_id, "status": "waiting"}
```

### 2. New Endpoint: Begin Auction (POST /auction/{auction_id}/begin)

**Requirements:**
- Only commissioner can call this endpoint
- Returns 403 for non-commissioners
- Changes auction status from "waiting" → "active"
- Starts first lot with timer
- Emits events to both rooms

**Implementation:**
```python
@api_router.post("/auction/{auction_id}/begin")
async def begin_auction(auction_id: str, commissionerId: str):
    # Verify auction exists and is waiting
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(404, "Auction not found")
    
    if auction["status"] != "waiting":
        raise HTTPException(400, f"Auction is not in waiting state")
    
    # Verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    if league["commissionerId"] != commissionerId:
        raise HTTPException(403, "Only the commissioner can start the auction")
    
    # Get first asset from queue
    first_asset_id = auction["clubQueue"][0]
    # ... load asset details ...
    
    # Start first lot
    timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
    lot_id = f"{auction_id}-lot-1"
    
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "currentClubId": first_asset_id,
            "currentLot": 1,
            "timerEndsAt": timer_end,
            "currentLotId": lot_id
        }}
    )
    
    # Create timer data
    ends_at_ms = int(timer_end.timestamp() * 1000)
    timer_data = create_timer_event(lot_id, ends_at_ms)
    
    # CRITICAL: Emit to AUCTION room (users already inside)
    await sio.emit('lot_started', {
        'club': asset_data,
        'lotNumber': 1,
        'timer': timer_data
    }, room=f"auction:{auction_id}")
    
    # Also emit to LEAGUE room (users not yet in auction room)
    await sio.emit('league_status_changed', {
        'leagueId': league["id"],
        'status': 'auction_active',
        'auctionId': auction_id
    }, room=f"league:{league['id']}")
    
    # Start timer
    asyncio.create_task(countdown_timer(auction_id, timer_end, lot_id))
    
    return {"message": "Auction started"}
```

### 3. Socket.IO Events (CRITICAL - Room Isolation)

**All auction events MUST include room parameter:**
```python
# ✅ CORRECT
await sio.emit('sold', data, room=f"auction:{auction_id}")
await sio.emit('bid_update', data, room=f"auction:{auction_id}")
await sio.emit('tick', timer_data, room=f"auction:{auction_id}")
await sio.emit('auction_complete', data, room=f"auction:{auction_id}")

# ❌ WRONG - broadcasts to ALL users
await sio.emit('sold', data)  # Missing room parameter!
```

**Event Checklist:**
- [ ] `lot_started` - room=f"auction:{auction_id}"
- [ ] `bid_update` - room=f"auction:{auction_id}"
- [ ] `bid_placed` - room=f"auction:{auction_id}"
- [ ] `sold` - room=f"auction:{auction_id}"
- [ ] `tick` - room=f"auction:{auction_id}"
- [ ] `anti_snipe` - room=f"auction:{auction_id}"
- [ ] `auction_complete` - room=f"auction:{auction_id}"
- [ ] `auction_paused` - room=f"auction:{auction_id}"
- [ ] `auction_resumed` - room=f"auction:{auction_id}"

---

## FRONTEND REQUIREMENTS

### 1. Waiting Room UI (AuctionRoom.js)

**Add conditional render BEFORE main auction UI:**
```javascript
// After loading check, before main auction render
if (auction?.status === "waiting") {
  const isCommissioner = league?.commissionerId === user?.id;
  
  const handleBeginAuction = async () => {
    try {
      await axios.post(`${API}/auction/${auctionId}/begin`, null, {
        params: { commissionerId: user.id }
      });
      // Don't reload here - let Socket.IO events handle it
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to start auction");
    }
  };
  
  return (
    <div className="waiting-room">
      <h1>Auction Waiting Room</h1>
      
      <div className="participants">
        <h3>Participants in Room:</h3>
        {participants.map(p => (
          <div key={p.userId}>{p.userName}</div>
        ))}
      </div>
      
      {isCommissioner ? (
        <button onClick={handleBeginAuction}>
          Begin Auction
        </button>
      ) : (
        <p>Waiting for commissioner to start...</p>
      )}
    </div>
  );
}

// Continue with normal auction UI...
```

### 2. Socket.IO Event Handling

**CRITICAL: Must handle lot_started to transition from waiting:**
```javascript
const onLotStarted = (data) => {
  console.log("Lot started:", data);
  
  // Set the club and timer from event
  setCurrentClub(data.club);
  setCurrentLotId(data.timer.lotId);
  
  // Reload auction to update status from "waiting" to "active"
  loadAuction();
  
  // Clear bid state
  setCurrentBid(null);
  setCurrentBidder(null);
  setBidSequence(0);
};
```

**Why loadAuction() is needed:**
- `lot_started` event contains club and timer data
- But frontend checks `auction.status === "waiting"` for conditional render
- Need to reload auction to get `status="active"` from backend
- This triggers re-render and shows main auction UI

### 3. LeagueDetail Page Updates

**Must handle `auction_active` status event:**
```javascript
const onLeagueStatusChanged = (data) => {
  if (data.leagueId === leagueId) {
    if (data.status === 'auction_created' || 
        data.status === 'auction_started' || 
        data.status === 'auction_active') {
      setLeague(prev => ({
        ...prev,
        status: 'active',
        activeAuctionId: data.auctionId
      }));
    }
  }
};
```

**Why this matters:**
- Users on league detail page see "Enter Auction Room" button
- When commissioner begins, backend emits `auction_active` to league room
- Frontend must update to show button is clickable

### 4. Polling Fallback (Optional but Recommended)

**For reliability if Socket.IO fails:**
```javascript
// In waiting room component
useEffect(() => {
  if (auction?.status === "waiting") {
    const poll = setInterval(() => {
      loadAuction();
    }, 2000);  // Poll every 2 seconds
    
    return () => clearInterval(poll);
  }
}, [auction?.status]);
```

---

## TESTING REQUIREMENTS

### Test Scenario 1: Basic Flow
1. Create league with 2 users
2. User 1 (commissioner) starts auction
3. **Verify:** Auction status = "waiting"
4. **Verify:** User 1 sees waiting room with "Begin Auction" button
5. User 2 enters auction room
6. **Verify:** User 2 sees waiting room with both participants listed
7. **Verify:** User 2 sees "Waiting for commissioner..." message
8. User 1 clicks "Begin Auction"
9. **Verify:** Within 1 second, both users see first team with timer
10. **Verify:** Both users can place bids

### Test Scenario 2: Late Joiner
1. Create league with 2 users
2. User 1 starts auction (waiting room appears)
3. User 1 clicks "Begin Auction" BEFORE User 2 enters
4. User 2 then enters auction room
5. **Verify:** User 2 sees active auction (not waiting room)
6. **Verify:** User 2 sees current team and can bid

### Test Scenario 3: Non-Commissioner Cannot Start
1. Create league with 2 users
2. User 1 (commissioner) starts auction
3. User 2 (non-commissioner) tries to call `/auction/{id}/begin`
4. **Verify:** Returns 403 error
5. **Verify:** Auction remains in "waiting" state

### Test Scenario 4: Multiple Concurrent Auctions
1. Create 2 separate leagues (League A, League B)
2. Start both auctions simultaneously
3. Enter waiting rooms in both
4. Begin both auctions
5. **Verify:** Users in League A only see League A events
6. **Verify:** Users in League B only see League B events
7. **Verify:** No cross-contamination of bids/sold notifications

### Test Scenario 5: Socket.IO Failure Fallback
1. Disable Socket.IO connection (simulate network issue)
2. Commissioner begins auction
3. **Verify:** Non-commissioner sees transition within 2 seconds via polling
4. Re-enable Socket.IO
5. **Verify:** Events work normally again

---

## KNOWN PITFALLS (What Went Wrong Before)

### 1. React Hooks Violations
**Problem:** Adding `useEffect` inside conditionals or after conditional returns
**Solution:** ALL hooks must be at top level, before any conditional returns

```javascript
// ❌ WRONG
if (auction?.status === "waiting") {
  useEffect(() => { ... }, []);  // Hooks violation!
  return <WaitingRoom />;
}

// ✅ CORRECT
useEffect(() => {
  if (auction?.status === "waiting") {
    // Polling logic inside conditional
  }
}, [auction?.status]);

if (auction?.status === "waiting") {
  return <WaitingRoom />;
}
```

### 2. Missing Room Parameters
**Problem:** Socket.IO events broadcasting to ALL users instead of specific auction
**Solution:** Every auction event MUST have `room=f"auction:{auction_id}"`

### 3. Event Name Mismatches
**Problem:** Backend emits `auction_active`, frontend listens for `auction_started`
**Solution:** Frontend must handle ALL variations:
```javascript
if (data.status === 'auction_created' || 
    data.status === 'auction_started' || 
    data.status === 'auction_active')
```

### 4. Stale Closure in Event Handlers
**Problem:** Event handlers have old `auction` state, conditions never match
**Solution:** Don't rely on closure state in event handlers - always reload or use refs

### 5. Race Condition on Transition
**Problem:** Backend emits `lot_started`, frontend hasn't updated `auction.status` yet
**Solution:** Call `loadAuction()` in `onLotStarted` handler to force status update

---

## IMPLEMENTATION CHECKLIST

### Backend:
- [ ] Modify auction creation to use `status="waiting"`
- [ ] Add POST `/auction/{auction_id}/begin` endpoint
- [ ] Verify commissioner-only access (403 for others)
- [ ] Emit `auction_created` to league room on creation
- [ ] Emit `lot_started` to auction room when begin is called
- [ ] Emit `auction_active` to league room when begin is called
- [ ] Verify ALL auction events have room parameter
- [ ] Test with 2 concurrent auctions to verify isolation

### Frontend (AuctionRoom.js):
- [ ] Add waiting room conditional render
- [ ] Show participant list in waiting room
- [ ] Show "Begin Auction" button for commissioner only
- [ ] Show "Waiting..." message for non-commissioners
- [ ] Handle `lot_started` event to transition from waiting
- [ ] Call `loadAuction()` in `onLotStarted` handler
- [ ] Add polling fallback (2s interval) for reliability
- [ ] Ensure all hooks at top level (before conditionals)

### Frontend (LeagueDetail.js):
- [ ] Handle `auction_active` status event
- [ ] Update "Enter Auction Room" button visibility
- [ ] Add polling fallback (3s interval) for reliability

### Testing:
- [ ] Test basic 2-user flow end-to-end
- [ ] Test late joiner (enters after auction started)
- [ ] Test non-commissioner cannot start (403)
- [ ] Test concurrent auctions (no cross-contamination)
- [ ] Test Socket.IO failure fallback (polling works)
- [ ] Test with 3+ users to verify scalability

---

## ESTIMATED COMPLEXITY

**Backend:** Medium (2-3 hours)
- New endpoint with permissions
- State management changes
- Event emission updates

**Frontend:** Medium (2-3 hours)
- New UI component
- Event handling
- State transition logic

**Testing:** High (3-4 hours)
- Multiple scenarios
- Edge cases
- Concurrent auction testing

**Total:** 7-10 hours for complete, tested implementation

---

## SUCCESS CRITERIA

1. ✅ Commissioner can coordinate auction start
2. ✅ All participants see each other in waiting room
3. ✅ Non-commissioners cannot start auction
4. ✅ Transition from waiting to active is smooth (<1 second)
5. ✅ No users miss the first bid opportunity
6. ✅ Multiple concurrent auctions remain isolated
7. ✅ Works reliably even if Socket.IO has delays
8. ✅ No React errors or console warnings
9. ✅ User experience is intuitive and professional

---

## FINAL NOTES

This feature is CRITICAL for user experience but introduces significant complexity:
- State management across waiting/active states
- Socket.IO room isolation must be perfect
- Frontend must handle async state transitions gracefully
- Testing must cover concurrent scenarios

**Recommendation:** Implement with dedicated focus, test thoroughly with multiple concurrent users before deploying to production.
