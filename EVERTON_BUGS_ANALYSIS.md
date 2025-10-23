# Bug Fixes from Everton Testing Sessions

## Bugs Identified

### 1. Timer Display Issue ⏱️
**Issue:** Custom timer settings (45s/15s) not displayed in auction room
**Current:** Shows default 30s/10s
**Expected:** Show league's configured timers
**Priority:** 🟡 Medium (functional but confusing)

### 2. Auction Start Coordination 🚦
**Issue:** Non-commissioner users can only enter after auction starts, missing first 5-10s
**Current:** Auction starts immediately when commissioner clicks "Start"
**Expected:** Lobby system where all users ready up before first lot begins
**Priority:** 🔴 High (affects fairness)

### 3. Final Team Display (Again) 📊
**Issue:** Shows 8/9 teams sold when 9th team is actually allocated
**Current:** Last team not marked as "sold" in UI
**Expected:** All 9 teams show correct status
**Priority:** 🟡 Medium (UI issue, data correct)
**Note:** This was supposedly fixed earlier - needs investigation

### 4. Budget Enforcement - Reserve for Final Slot 💰
**Issue:** User can bid entire budget before filling all slots
**Example:** User with 2/3 slots filled, £100m remaining, bids £100m and wins
**Result:** No budget for 3rd slot, can't complete roster
**Expected:** System prevents bidding more than (remaining_budget - £1m) until last slot
**Priority:** 🔴 CRITICAL (breaks game fairness)

### 5. Roster Visibility 👥
**Issue:** Users can only see their own roster in dashboard
**Expected:** All users can view all rosters (transparency, competition)
**Priority:** 🟡 Medium (UX improvement)

---

## Technical Analysis

### Bug 1: Timer Display
**Location:** `/app/frontend/src/pages/AuctionRoom.js`
**Root Cause:** Not fetching or displaying league's timer settings

**Current Code:**
```javascript
// Probably showing hardcoded defaults
const timerDuration = 30; // Default
const antiSnipe = 10; // Default
```

**Fix Needed:**
```javascript
// Fetch from league object
const timerDuration = auction.timerSeconds || 30;
const antiSnipe = auction.antiSnipeSeconds || 10;
```

---

### Bug 2: Auction Start Coordination
**Location:** `/app/backend/server.py` + `/app/frontend/src/pages/AuctionRoom.js`
**Root Cause:** Auction starts immediately, no waiting room

**Current Flow:**
1. Commissioner clicks "Start Auction"
2. Auction starts immediately
3. First lot timer begins
4. Other users navigate to room after it's started

**Proposed Flow:**
1. Commissioner clicks "Start Auction" → Auction created but paused
2. All users enter auction room (lobby state)
3. Each user clicks "Ready" button
4. When all users ready (or commissioner forces start), first lot begins

**Implementation:**
- Add `waitingForUsers: boolean` to auction state
- Add `readyUsers: string[]` array
- Socket event: `user_ready` 
- Commissioner can force start if waiting too long
- Display "Waiting for users..." + ready count

---

### Bug 3: Final Team Display
**Location:** `/app/frontend/src/pages/AuctionRoom.js` + `/app/backend/server.py`
**Root Cause:** Race condition on final sale (previously "fixed")

**Investigation Needed:**
- Check if previous fix is working
- May be same issue recurring
- Need to verify auction_complete event includes final club state

**Quick Check:** Does everton2 auction have this issue in database?

---

### Bug 4: Budget Enforcement
**Location:** `/app/backend/server.py` - Bid validation
**Root Cause:** No check for reserve budget for remaining slots

**Current Validation:**
```python
# Only checks if bid > budget remaining
if bid_amount > participant["budgetRemaining"]:
    raise HTTPException(400, "Insufficient budget")
```

**Fix Needed:**
```python
# Calculate slots remaining
slots_remaining = club_slots - len(participant["clubsWon"])

# Must reserve £1m per remaining slot (except last)
if slots_remaining > 1:  # Not on final slot
    max_allowed_bid = participant["budgetRemaining"] - (slots_remaining - 1) * 1_000_000
    
    if bid_amount > max_allowed_bid:
        raise HTTPException(400, 
            f"Must reserve £{slots_remaining - 1}m for remaining {slots_remaining - 1} slot(s). "
            f"Max bid: £{max_allowed_bid/1_000_000}m"
        )
```

**Edge Cases:**
- Last slot: Can bid entire remaining budget
- What if budget < slots_remaining * £1m? (already in trouble)

---

### Bug 5: Roster Visibility
**Location:** `/app/frontend/src/pages/CompetitionDashboard.js`
**Root Cause:** Only showing current user's roster

**Current:** Probably filtering to userId
**Fix:** Show all participants' rosters in League tab or separate "Rosters" tab

**Options:**
1. Add "Rosters" tab showing everyone
2. Enhance "League" tab to show rosters inline
3. Add expandable rows in standings

---

## Fix Priority Order

### Phase 1: Critical Fixes (Must Do)
1. **Budget Enforcement** - Bug 4 (prevents game-breaking issue)
2. **Auction Start Coordination** - Bug 2 (fairness issue)

### Phase 2: Important Fixes
3. **Timer Display** - Bug 1 (confusing but not breaking)
4. **Final Team Display** - Bug 3 (recurring UI issue)

### Phase 3: Nice to Have
5. **Roster Visibility** - Bug 5 (UX enhancement)

---

## Implementation Plan

### Step 1: Budget Enforcement (30 min)
**File:** `/app/backend/server.py`
**Function:** `place_bid` endpoint

Add validation before accepting bid:
```python
# Get participant's current state
slots_remaining = league["clubSlots"] - len(participant["clubsWon"])

# Enforce reserve budget
if slots_remaining > 1:
    min_reserve = (slots_remaining - 1) * 1_000_000
    max_bid = participant["budgetRemaining"] - min_reserve
    
    if amount > max_bid:
        raise HTTPException(
            status_code=400,
            detail=f"Must reserve £{min_reserve/1_000_000:.0f}m for {slots_remaining - 1} remaining slot(s). Max bid: £{max_bid/1_000_000:.1f}m"
        )
```

**Test:** User with 1/3 slots, £100m budget should only bid max £98m

---

### Step 2: Auction Start Coordination (2-3 hours)
**Backend Changes:**
1. Add `status: "waiting"` to auction when created
2. Add `readyUsers: []` field
3. Add `/auction/{id}/ready` endpoint
4. Socket event `user_ready` broadcasts ready count
5. Change to `status: "active"` when all ready or commissioner forces

**Frontend Changes:**
1. Show "Waiting Room" UI when `status === "waiting"`
2. Display participant list with ready indicators
3. "I'm Ready" button for each user
4. Commissioner sees "Force Start" button after 30s
5. Countdown begins when status changes to "active"

---

### Step 3: Timer Display (30 min)
**File:** `/app/frontend/src/pages/AuctionRoom.js`

Fetch league settings and use them:
```javascript
const [timerSeconds, setTimerSeconds] = useState(30);
const [antiSnipeSeconds, setAntiSnipeSeconds] = useState(10);

// On auction load
useEffect(() => {
  if (auction?.leagueId) {
    // Fetch league
    axios.get(`${BACKEND_URL}/api/leagues/${auction.leagueId}`)
      .then(res => {
        setTimerSeconds(res.data.timerSeconds || 30);
        setAntiSnipeSeconds(res.data.antiSnipeSeconds || 10);
      });
  }
}, [auction]);
```

Display in UI:
```javascript
<div>Timer: {timerSeconds}s (extends by {antiSnipeSeconds}s on late bids)</div>
```

---

### Step 4: Final Team Display Investigation (1 hour)
Check if previous fix is working:
1. Review `/app/backend/server.py` - `auction_complete` event
2. Review `/app/frontend/src/pages/AuctionRoom.js` - `onAuctionComplete` handler
3. Test manually with everton2 data
4. If broken, re-apply fix with extra logging

---

### Step 5: Roster Visibility (1-2 hours)
**Option A: Simple "All Rosters" Section**
Add to CompetitionDashboard.js:

```javascript
// New tab: "Rosters"
{tab === 'rosters' && (
  <div>
    <h2>Team Rosters</h2>
    {participants.map(p => (
      <div key={p.userId}>
        <h3>{p.userName}</h3>
        <ul>
          {p.clubsWon.map(clubId => (
            <li>{getClubName(clubId)}</li>
          ))}
        </ul>
      </div>
    ))}
  </div>
)}
```

**Option B: Enhanced League Table**
Show rosters inline with standings (expandable rows)

---

## Testing Plan

### Test Case 1: Budget Enforcement
**Setup:** League with 3 slots, £300m budget
**Steps:**
1. User wins team for £100m (budget: £200m, slots: 2/3)
2. Try to bid £150m on next team
3. **Expected:** Rejected - "Must reserve £1m. Max bid: £149m"
4. Bid £149m, win (budget: £51m, slots: 2/3)
5. Try to bid £52m on final team
6. **Expected:** Rejected - "Max bid: £51m"
7. Bid £51m, win (budget: £0, slots: 3/3)
8. **Expected:** Auction completes, user has full roster

### Test Case 2: Auction Start Coordination
**Setup:** League with 3 users
**Steps:**
1. Commissioner starts auction
2. **Expected:** Auction room shows "Waiting for users"
3. Users 2 and 3 enter room
4. **Expected:** See "2/3 ready" counter
5. User 2 clicks "Ready"
6. **Expected:** "2/3 ready" (User 2 marked ready)
7. User 3 clicks "Ready"
8. **Expected:** "3/3 ready" → Countdown starts
9. First lot begins after countdown
10. **Expected:** All users see first team at same time

### Test Case 3: Timer Display
**Setup:** League with 45s timer, 15s anti-snipe
**Steps:**
1. Start auction
2. **Expected:** UI shows "Timer: 45s (extends by 15s on late bids)"
3. Place bid at 5s remaining
4. **Expected:** Timer extends to 15s

### Test Case 4: Roster Visibility
**Setup:** Completed auction with 3 users
**Steps:**
1. Go to Competition Dashboard
2. Navigate to "Rosters" or "League" tab
3. **Expected:** See all 3 users' rosters with team names

---

## Estimated Timeline

**Critical Fixes (Phase 1):**
- Budget enforcement: 30 min
- Auction start coordination: 2-3 hours
**Total Phase 1: 3-4 hours**

**Important Fixes (Phase 2):**
- Timer display: 30 min
- Final team display investigation: 1 hour
**Total Phase 2: 1.5 hours**

**Nice to Have (Phase 3):**
- Roster visibility: 1-2 hours
**Total Phase 3: 1-2 hours**

**Grand Total: 5.5-7.5 hours of work**

---

## Rollback Plan

**Current stable state:** 2025-10-22 00:22 UTC
**After fixes:** Create new checkpoint
**If issues:** Rollback to current state

---

## Questions Before Implementation

1. **Budget Reserve:** Confirm £1m minimum per slot is acceptable?
2. **Auction Start:** Should there be a maximum wait time before force-start?
3. **Roster Visibility:** Prefer tab or inline display?
4. **Priority:** Should I tackle all 5 or focus on critical first?

---

**Ready to implement when you confirm approach!**
