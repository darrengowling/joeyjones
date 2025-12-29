# UEFA Club Auction - Testing Guide

## Quick Test Flow

### 1. Verify Services Running
```bash
sudo supervisorctl status
```
All services should show RUNNING.

### 2. Seed UEFA Clubs (First Time Only)
```bash
curl -X POST http://localhost:8001/api/clubs/seed
```
Response: `{"message": "Seeded 36 UEFA Champions League clubs"}`

### 3. Test Backend APIs

#### Get All Clubs
```bash
curl http://localhost:8001/api/clubs | python3 -m json.tool | head -30
```

#### Create a User
```bash
curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith", "email": "john@example.com"}' \
  | python3 -m json.tool
```
Save the returned `id` for next steps.

#### Create a League
```bash
curl -X POST http://localhost:8001/api/leagues \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test League",
    "commissionerId": "YOUR_USER_ID_HERE",
    "budget": 1000,
    "minManagers": 2,
    "maxManagers": 12,
    "clubSlots": 3
  }' | python3 -m json.tool
```
Save the returned league `id`.

#### Start an Auction
```bash
curl -X POST http://localhost:8001/api/leagues/YOUR_LEAGUE_ID/auction/start \
  | python3 -m json.tool
```
Save the returned `auctionId`.

#### Get First Club ID
```bash
curl http://localhost:8001/api/clubs | python3 -c "import sys, json; clubs = json.load(sys.stdin); print(clubs[0]['id'])"
```

#### Start First Lot
```bash
curl -X POST http://localhost:8001/api/auction/YOUR_AUCTION_ID/start-lot/FIRST_CLUB_ID
```

#### Place a Bid
```bash
curl -X POST http://localhost:8001/api/auction/YOUR_AUCTION_ID/bid \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "YOUR_USER_ID",
    "clubId": "CLUB_ID",
    "amount": 100
  }' | python3 -m json.tool
```

#### Get Auction Status
```bash
curl http://localhost:8001/api/auction/YOUR_AUCTION_ID | python3 -m json.tool
```

### 4. Test Frontend (UI)

1. **Open Browser**: Navigate to your frontend URL
2. **Sign In**: Click "Sign In" and enter name + email
3. **View Clubs**: Click "View All Clubs" to see 36 UEFA CL clubs
4. **Create League**: Click "Create New League" and fill in details
5. **Start Auction**: Navigate to your league and click "Start Auction" (commissioner only)
6. **Bid on Clubs**: 
   - Click a club to start the lot (commissioner)
   - Enter bid amount and click "Place Bid"
   - Watch timer countdown
   - Test anti-snipe by bidding in last 30 seconds
7. **Complete Lot**: Click "Complete Lot" when timer expires

### 5. Test Real-Time Features

#### Test Anti-Snipe
1. Start a lot with 60-second timer
2. Wait until timer shows < 30 seconds
3. Place a bid
4. Timer should extend by 30 seconds
5. Alert should show: "🔥 Anti-snipe! Timer extended by 30 seconds"

#### Test Live Updates
1. Open auction room in two different browsers (or incognito)
2. Sign in as different users in each
3. Place bid in one browser
4. Verify other browser shows new bid instantly
5. Verify timer updates in both browsers simultaneously

### 6. Test Socket.IO Connection

#### Check Browser Console
1. Open browser developer tools (F12)
2. Navigate to auction room
3. Check console for:
   ```
   Socket connected
   Joined auction: {auctionId: "..."}
   ```

#### Test Events
Monitor console while:
- Placing bids → Should see "Bid placed:" logs
- Timer counting down → Should see timer_update events every second
- Starting lots → Should see "Lot started:" logs
- Anti-snipe triggered → Should see "Anti-snipe triggered:" logs

### 7. Expected Behavior

✅ **Timer**
- Counts down from 60 seconds
- Updates every second
- Extends by 30s if bid in last 30s
- Can extend multiple times

✅ **Bidding**
- Only allows bids higher than current highest
- Shows all bids in real-time
- Displays bidder name
- Sorts by amount (highest first)

✅ **Lot Completion**
- Timer expires → lot completes automatically
- Alert shows winner
- Club marked as "Sold" in available clubs list
- Ready for next lot

✅ **Rooms**
- Users in same auction see same updates
- Users in different auctions don't interfere

### 8. Common Issues & Solutions

#### Backend Not Starting
```bash
tail -n 50 /var/log/supervisor/backend.err.log
```
Check for import errors or syntax issues.

#### Frontend Not Compiling
```bash
tail -n 50 /var/log/supervisor/frontend.err.log
```
Check for JavaScript syntax errors.

#### Socket.IO Not Connecting
- Verify backend is running: `curl http://localhost:8001/api/`
- Check CORS settings in server.py
- Check browser console for connection errors

#### No Clubs Showing
```bash
curl -X POST http://localhost:8001/api/clubs/seed
```
Seed the database first.

### 9. Complete End-to-End Test Script

```bash
#!/bin/bash

# Seed clubs
echo "Seeding clubs..."
curl -s -X POST http://localhost:8001/api/clubs/seed

# Create user
echo -e "\n\nCreating user..."
USER_RESPONSE=$(curl -s -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}')
USER_ID=$(echo $USER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "User ID: $USER_ID"

# Create league
echo -e "\n\nCreating league..."
LEAGUE_RESPONSE=$(curl -s -X POST http://localhost:8001/api/leagues \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test League\", \"commissionerId\": \"$USER_ID\", \"budget\": 1000, \"minManagers\": 2, \"maxManagers\": 12, \"clubSlots\": 3}")
LEAGUE_ID=$(echo $LEAGUE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "League ID: $LEAGUE_ID"

# Start auction
echo -e "\n\nStarting auction..."
AUCTION_RESPONSE=$(curl -s -X POST http://localhost:8001/api/leagues/$LEAGUE_ID/auction/start)
AUCTION_ID=$(echo $AUCTION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['auctionId'])")
echo "Auction ID: $AUCTION_ID"

# Get first club
echo -e "\n\nGetting first club..."
CLUB_ID=$(curl -s http://localhost:8001/api/clubs | python3 -c "import sys, json; clubs = json.load(sys.stdin); print(clubs[0]['id'])")
echo "Club ID: $CLUB_ID"

# Start lot
echo -e "\n\nStarting lot..."
curl -s -X POST http://localhost:8001/api/auction/$AUCTION_ID/start-lot/$CLUB_ID

# Place bid
echo -e "\n\nPlacing bid..."
curl -s -X POST http://localhost:8001/api/auction/$AUCTION_ID/bid \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"$USER_ID\", \"clubId\": \"$CLUB_ID\", \"amount\": 100}"

# Get auction status
echo -e "\n\nAuction status:"
curl -s http://localhost:8001/api/auction/$AUCTION_ID | python3 -m json.tool

echo -e "\n\n✅ Test complete!"
```

Save this as `/app/test_auction.sh` and run:
```bash
chmod +x /app/test_auction.sh
./test_auction.sh
```

### 10. Performance Testing

#### Concurrent Bidding
Test with multiple users bidding simultaneously:
1. Open 3-5 browser windows
2. Sign in as different users
3. Join same auction
4. All bid at same time
5. Verify no race conditions
6. Verify all bids recorded correctly

#### Anti-Snipe Stress Test
1. Start a lot
2. Place bid at exactly 29 seconds remaining
3. Place another bid at exactly 29 seconds (after first extension)
4. Repeat 5 times
5. Verify timer extends each time
6. Verify all bids recorded

## Success Criteria

✅ All 36 UEFA CL clubs seeded
✅ Users can sign in with name + email
✅ Leagues can be created
✅ Auctions can be started
✅ Commissioners can start lots
✅ Users can place bids
✅ Timer counts down correctly
✅ Anti-snipe works (extends timer)
✅ Real-time updates via Socket.IO
✅ Lot completes with winner
✅ UI is responsive and updates live
✅ Multiple users can bid simultaneously
✅ Rooms isolate different auctions

## Next Steps After Testing

1. Report any bugs found
2. Request feature enhancements
3. Test with real users
4. Add monitoring/analytics
5. Optimize performance
6. Add mobile support
7. Deploy to production
