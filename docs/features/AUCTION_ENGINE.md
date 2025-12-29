# Core Auction Engine Documentation

**Created:** December 28, 2025  
**Purpose:** Document the auction engine mechanics for reuse in Pick TV and future products  
**Status:** REFERENCE DOCUMENT

---

## Overview

The auction engine is the core intellectual property of the platform. It handles:
- Real-time bidding via Socket.IO
- Timer management with anti-snipe protection
- Queue management (which asset is up for bid next)
- Bid validation and acceptance
- Automatic lot completion when timer expires
- Multi-user synchronization via Redis pub/sub

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUCTION ENGINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │    Timer     │    │    Queue     │    │    Bids      │       │
│  │  Management  │◄──►│  Management  │◄──►│  Processing  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │   Socket.IO     │                          │
│                    │   Event Layer   │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
├─────────────────────────────┼────────────────────────────────────┤
│                             │                                    │
│              ┌──────────────▼──────────────┐                    │
│              │      Redis Pub/Sub          │                    │
│              │   (Multi-pod sync)          │                    │
│              └─────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Auction State Model

**Location:** `/app/backend/models.py`

```python
class Auction(BaseModel):
    id: str
    leagueId: str
    status: str  # "active", "paused", "completed"
    
    # Current lot
    currentClubId: Optional[str]      # Asset being auctioned
    currentClubIndex: int = 0         # Position in queue
    
    # Timer
    bidTimerSeconds: int = 30         # Default bid window
    antiSnipeSeconds: int = 10        # Extra time on late bids
    timerEndsAt: Optional[datetime]   # When current lot expires
    
    # Queue
    clubQueue: List[str] = []         # Asset IDs in order
    completedClubs: List[str] = []    # Assets already sold
    unsoldClubs: List[str] = []       # Assets with no bids
    
    # Bidding
    currentBid: float = 0             # Current highest bid
    currentBidderId: Optional[str]    # User ID of highest bidder
    currentBidderName: Optional[str]  # Display name
    bidSequence: int = 0              # Bid counter for this lot
    minIncrement: float = 1           # Minimum bid increase
```

### 2. Bid Processing

**Location:** `/app/backend/server.py` (lines ~4200-4400)

**Bid Validation Rules:**
1. User must be authenticated
2. User must be a participant in the league
3. Auction must be active (not paused/completed)
4. Bid must be higher than current bid (not equal)
5. User cannot outbid themselves (self-outbid prevention)
6. User must have sufficient budget remaining
7. User's roster must not be full

**Bid Flow:**
```
1. Client sends POST /auction/{id}/bid with amount
   ↓
2. Server validates bid (rules above)
   ↓
3. If valid:
   - Update auction.currentBid
   - Update auction.currentBidderId
   - Update auction.currentBidderName
   - Increment auction.bidSequence
   - Check anti-snipe (extend timer if needed)
   - Save to database
   ↓
4. Emit socket events:
   - "bid_placed" (detailed, to bidder)
   - "bid_update" (summary, to all participants)
   ↓
5. Redis pub/sub broadcasts to all pods
```

### 3. Timer Management

**Location:** `/app/backend/server.py` (auction timer logic)

**Timer Mechanics:**
- Default: 30 seconds per lot
- Anti-snipe: If bid placed in last 10 seconds, timer extends by 10 seconds
- Timer stored as `timerEndsAt` (absolute datetime)
- Frontend calculates remaining time from server timestamp

**Timer Events:**
```javascript
// Server sends timer_sync periodically
{
  "type": "timer_sync",
  "timerEndsAt": "2025-12-28T14:30:00Z",
  "serverTime": "2025-12-28T14:29:45Z",
  "remainingMs": 15000
}
```

### 4. Queue Management

**Location:** `/app/backend/server.py` (auction queue logic)

**Queue Operations:**
- `clubQueue`: Full list of assets to auction (in order)
- `currentClubIndex`: Which position we're at
- `completedClubs`: Assets sold (have a winner)
- `unsoldClubs`: Assets with no bids (re-queue at end or skip)

**Lot Completion Flow:**
```
1. Timer expires OR "Complete Lot" button pressed
   ↓
2. If currentBid > 0:
   - Move currentClubId to completedClubs
   - Add asset to winner's clubsWon
   - Deduct bid amount from winner's budget
   - Emit "sold" event
   ↓
3. If currentBid == 0 (no bids):
   - Move currentClubId to unsoldClubs
   - Emit "unsold" event
   ↓
4. Advance to next lot:
   - currentClubIndex++
   - Set currentClubId to next in queue
   - Reset currentBid, currentBidderId, bidSequence
   - Start new timer
   - Emit "new_lot" event
   ↓
5. If no more lots:
   - Check if unsold clubs should be re-auctioned
   - If all done, set status = "completed"
   - Emit "auction_completed" event
```

### 5. Socket.IO Events

**Location:** `/app/backend/socketio_init.py` + `/app/backend/server.py`

**Server → Client Events:**

| Event | Purpose | Payload |
|-------|---------|---------|
| `auction_state` | Full auction state sync | Entire auction object |
| `bid_update` | New bid placed | `{currentBid, bidderId, bidderName, bidSequence, timerEndsAt}` |
| `bid_placed` | Confirmation to bidder | Same as bid_update + validation details |
| `timer_sync` | Timer synchronization | `{timerEndsAt, serverTime, remainingMs}` |
| `sold` | Lot completed with winner | `{clubId, winnerId, winnerName, amount}` |
| `unsold` | Lot completed, no bids | `{clubId}` |
| `new_lot` | Next lot starting | `{clubId, clubName, index, timerEndsAt}` |
| `auction_completed` | Auction finished | `{auctionId, completedClubs, unsoldClubs}` |
| `auction_paused` | Commissioner paused | `{auctionId}` |
| `auction_resumed` | Commissioner resumed | `{auctionId, timerEndsAt}` |
| `participant_joined` | New user joined | `{userId, userName}` |
| `roster_update` | User's roster changed | `{userId, clubsWon, budgetRemaining}` |
| `error` | Error message | `{message, code}` |

**Client → Server Events:**

| Event | Purpose | Payload |
|-------|---------|---------|
| `join_auction` | Join auction room | `{auctionId, userId}` |
| `leave_auction` | Leave auction room | `{auctionId, userId}` |
| `place_bid` | Submit bid (alternative to REST) | `{auctionId, amount}` |

### 6. Redis Pub/Sub (Multi-Pod)

**Location:** `/app/backend/socketio_init.py`

**Purpose:** When running multiple server pods (for scaling), Socket.IO events must be broadcast to all pods so all connected clients receive updates.

**Configuration:**
```python
# Socket.IO with Redis adapter
import socketio

redis_url = os.environ.get('REDIS_URL')
if redis_url:
    mgr = socketio.AsyncRedisManager(redis_url)
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins='*',
        client_manager=mgr
    )
else:
    # Fallback to in-memory (single pod only)
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins='*'
    )
```

---

## Frontend Implementation

### AuctionRoom.js Structure

**Location:** `/app/frontend/src/pages/AuctionRoom.js` (~1,400 lines)

**Key State Variables:**
```javascript
const [auction, setAuction] = useState(null);        // Full auction state
const [currentClub, setCurrentClub] = useState(null); // Current lot details
const [bidAmount, setBidAmount] = useState("");       // User's bid input
const [timeRemaining, setTimeRemaining] = useState(0); // Countdown
const [participants, setParticipants] = useState([]); // All participants
const [myRoster, setMyRoster] = useState([]);         // User's won assets
const [socket, setSocket] = useState(null);           // Socket.IO connection
```

**Key Functions:**
```javascript
// Initialize socket connection
useEffect(() => {
  const newSocket = io(API_URL, { auth: { token } });
  newSocket.emit('join_auction', { auctionId, userId });
  setSocket(newSocket);
  return () => newSocket.disconnect();
}, [auctionId]);

// Handle bid placement
const placeBid = async () => {
  const response = await axios.post(`/auction/${auctionId}/bid`, {
    amount: parseFloat(bidAmount)
  });
  // Socket will broadcast update to all clients
};

// Handle socket events
useEffect(() => {
  if (!socket) return;
  
  socket.on('bid_update', (data) => {
    setAuction(prev => ({...prev, ...data}));
  });
  
  socket.on('sold', (data) => {
    // Update completed clubs, rosters
  });
  
  socket.on('new_lot', (data) => {
    // Load new club details, reset bid input
  });
  
  // ... more event handlers
}, [socket]);
```

**Timer Display:**
```javascript
// Countdown timer
useEffect(() => {
  if (!auction?.timerEndsAt) return;
  
  const interval = setInterval(() => {
    const remaining = new Date(auction.timerEndsAt) - new Date();
    setTimeRemaining(Math.max(0, Math.floor(remaining / 1000)));
    
    if (remaining <= 0) {
      // Timer expired - server will handle lot completion
    }
  }, 100);
  
  return () => clearInterval(interval);
}, [auction?.timerEndsAt]);
```

---

## Auction Configuration

### Per-Sport Settings

```javascript
// Football auction defaults
{
  bidTimerSeconds: 30,
  antiSnipeSeconds: 10,
  minIncrement: 1,          // £1m minimum bid increase
  startingBid: 0,           // Bidding starts at £0
  currency: "£",
  currencyUnit: "m"         // millions
}

// Cricket auction defaults
{
  bidTimerSeconds: 30,
  antiSnipeSeconds: 10,
  minIncrement: 0.5,        // ₹0.5 crore minimum
  startingBid: 0,
  currency: "₹",
  currencyUnit: "Cr"        // crores
}

// Reality TV (proposed)
{
  bidTimerSeconds: 20,      // Faster for entertainment
  antiSnipeSeconds: 5,
  minIncrement: 1,
  startingBid: 0,
  currency: "⭐",
  currencyUnit: ""          // Just "stars"
}
```

### League-Level Overrides

Commissioners can customize:
- `budget`: Total budget per user (default: 500m for football)
- `clubSlots`: How many assets each user can win (default: 3)
- `bidTimerSeconds`: Can be set per league
- `minIncrement`: Can be set per league

---

## Error Handling

### Bid Rejection Reasons

| Code | Message | Cause |
|------|---------|-------|
| `INSUFFICIENT_BUDGET` | "You don't have enough budget" | Bid > budgetRemaining |
| `ROSTER_FULL` | "Your roster is full" | clubsWon.length >= clubSlots |
| `SELF_OUTBID` | "You're already the highest bidder" | Trying to outbid yourself |
| `BID_TOO_LOW` | "Bid must be higher than current" | Bid <= currentBid |
| `AUCTION_NOT_ACTIVE` | "Auction is not active" | Status is paused/completed |
| `NOT_PARTICIPANT` | "You are not in this auction" | User not in league |

### Recovery Mechanisms

1. **Socket Disconnection:**
   - Client auto-reconnects
   - On reconnect, fetches full auction state via REST
   - Re-joins auction room

2. **State Desync:**
   - Timer sync events sent every 5 seconds
   - Clients can request full state refresh
   - Bid sequence numbers detect missed updates

3. **Server Crash:**
   - Auction state persisted to MongoDB
   - On restart, loads from database
   - Clients reconnect and resync

---

## Database Queries

### Key Auction Queries

```python
# Get active auction for a league
auction = await db.auctions.find_one({
    "leagueId": league_id,
    "status": "active"
}, {"_id": 0})

# Get all bids for current lot
bids = await db.bids.find({
    "auctionId": auction_id,
    "clubId": current_club_id
}, {"_id": 0}).sort("timestamp", -1).to_list(100)

# Update auction state after bid
await db.auctions.update_one(
    {"id": auction_id},
    {"$set": {
        "currentBid": new_bid,
        "currentBidderId": user_id,
        "currentBidderName": user_name,
        "bidSequence": bid_sequence + 1,
        "timerEndsAt": new_timer_end
    }}
)

# Record bid
await db.bids.insert_one({
    "id": str(uuid4()),
    "auctionId": auction_id,
    "clubId": current_club_id,
    "userId": user_id,
    "userName": user_name,
    "amount": bid_amount,
    "timestamp": datetime.now(timezone.utc)
})
```

---

## Performance Considerations

### Current Optimizations

1. **Removed unnecessary DB reads on bid_placed** (Dec 2025)
   - Previously: 2 HTTP GETs per bid per client
   - Now: Socket events only, no extra reads

2. **Redis for Socket.IO** (Dec 2025)
   - Enables multi-pod deployment
   - Handles concurrent users across servers

### Future Optimizations (ISSUE-017)

1. **Phase 2:** Move diagnostic reads to async background task
2. **Phase 3:** Use findOneAndUpdate instead of separate read/write
3. **Phase 4:** Consolidate bid_update + bid_placed into single event
4. **Phase 5:** Move bidding from REST to Socket.IO emit with ack

---

## Testing the Auction Engine

### Manual Testing Checklist

```
□ Start auction with 2+ users
□ Place bid - verify all users see update
□ Verify anti-snipe extends timer
□ Let timer expire - verify lot completes
□ Verify winner gets asset, budget deducted
□ Verify unsold assets handled correctly
□ Test with user at budget limit
□ Test with user at roster limit
□ Pause/resume auction
□ Disconnect/reconnect during auction
□ Multiple simultaneous bids
```

### Key Assertions

```javascript
// Bid must increase
expect(newBid).toBeGreaterThan(currentBid);

// Budget must be sufficient
expect(user.budgetRemaining).toBeGreaterThanOrEqual(bidAmount);

// Roster must have space
expect(user.clubsWon.length).toBeLessThan(league.clubSlots);

// Winner assigned on lot completion
expect(completedLot.winnerId).toBe(highestBidder.id);

// Budget deducted correctly
expect(winner.budgetRemaining).toBe(originalBudget - winningBid);
```

---

## Adapting for Pick TV

### What Changes

| Component | Sport X | Pick TV |
|-----------|---------|---------|
| Assets | Clubs/Players | Contestants |
| Currency | £ / ₹ | ⭐ Stars |
| Asset Display | Team logo, country | Photo, bio, tribe |
| Queue Source | Teams from competition | Contestants from show |
| Post-Auction | Match scoring | Episode scoring |

### What Stays the Same

- Bidding logic
- Timer management
- Anti-snipe
- Socket.IO events
- Redis pub/sub
- Bid validation rules
- Queue management
- State persistence

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
