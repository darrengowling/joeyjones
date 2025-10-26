# URGENT: Cricket Auction Test Plan
**Time Sensitive:** Cricket auction in a few hours

---

## ✅ FIXES APPLIED (Just Now)

### 1. Final Team Display Bug - FIXED
**Changes:**
- Removed `loadClubs()` calls after `sold` and `auction_complete` events
- Now trusts event data directly instead of reloading from backend
- Should show correct "6/6 teams sold" immediately

### 2. Waiting Room Socket.IO - FIXED
**Changes:**
- Added `loadAuction()` call when `lot_started` event received in waiting state
- Forces UI transition from waiting room to active auction
- 3-second polling fallback for reliability

---

## 🧪 CRITICAL TESTS NEEDED

### Test 1: Waiting Room Flow (15 mins)
**Setup:**
- League: "Quick Test Waiting Room" (00039867-9555-4990-a5f5-f068f8afbcce)
- 2 users, 2 slots each
- 10s timer

**Steps:**
1. User 1 (commissioner) creates auction → should show waiting room
2. User 2 joins auction room → should see waiting room with User 1 listed
3. User 1 clicks "Begin Auction" → first club appears
4. **CRITICAL:** User 2 should see auction start within 3 seconds (no refresh)
5. Both users complete 4-club auction
6. **CRITICAL:** Final display should show "4/4 teams sold" immediately

**Expected Results:**
- ✅ Both users see waiting room
- ✅ User 2 transitions automatically (no refresh)
- ✅ Final count correct (4/4 not 3/4)

---

### Test 2: Cricket Scoring Flow (30 mins)
**Setup:**
- Create new cricket league: "Cricket Test Scoring"
- 2 users, 3 players each (6 total from 30 available)
- Run auction to completion

**Steps:**
1. Complete auction (6 players distributed)
2. Create test scoring CSV:
```csv
matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
nz-eng-odi-1-2025,harry-brook,50,0,1,0,0
nz-eng-odi-1-2025,kane-williamson,75,0,0,0,0
nz-eng-odi-1-2025,jofra-archer,5,3,0,0,0
nz-eng-odi-1-2025,mitchell-santner,20,2,1,0,0
nz-eng-odi-1-2025,jos-buttler,30,0,2,1,0
nz-eng-odi-1-2025,matt-henry,0,4,0,0,0
```

3. Upload scoring:
```bash
cd /app/scripts
./upload_match_scores.sh LEAGUE_ID test_scoring.csv
```

4. Check leaderboard:
```bash
curl "https://bidflowfix.preview.emergentagent.com/api/scoring/LEAGUE_ID/leaderboard" | jq
```

5. Verify points:
- Harry Brook: 50 + 10 = 60 points
- Kane Williamson: 75 points
- Jofra Archer: 5 + 60 = 65 points
- Mitchell Santner: 20 + 40 + 10 = 70 points
- Jos Buttler: 30 + 20 + 10 = 60 points
- Matt Henry: 0 + 80 = 80 points

6. Upload second match scores (different matchId: nz-eng-odi-2-2025)
7. Verify cumulative scoring

**Expected Results:**
- ✅ CSV upload succeeds
- ✅ Points calculated correctly (1pt/run, 20pts/wicket, 10pts/catch/stumping/runout)
- ✅ Leaderboard shows sorted managers
- ✅ Second match adds to cumulative totals

---

## 🚀 GO/NO-GO DECISION TREE

### After Test 1 (Waiting Room):
- ✅ **PASS:** Both users transition smoothly + final count correct → Proceed to Test 2
- ❌ **FAIL:** Users need refresh OR final count wrong → Fix immediately

### After Test 2 (Cricket Scoring):
- ✅ **PASS:** Scoring uploads, calculates, displays correctly → **GO FOR CRICKET AUCTION**
- ❌ **FAIL:** Scoring broken → **EMERGENCY FIX NEEDED**

---

## 📋 QUICK REFERENCE

**Test League ID:** 00039867-9555-4990-a5f5-f068f8afbcce
**User 1 (Commissioner):** daf691e3-8676-4935-811e-cc9641a40e3a
**User 2:** 69459fb4-fdb0-4057-85f7-d47008be40cb

**Auction URLs:**
- League: https://bidflowfix.preview.emergentagent.com/leagues/00039867-9555-4990-a5f5-f068f8afbcce
- Start Auction: POST /api/leagues/00039867-9555-4990-a5f5-f068f8afbcce/start-auction
- Get Auction: GET /api/leagues/00039867-9555-4990-a5f5-f068f8afbcce/auction

---

## ⏱️ TIME ESTIMATE

- Test 1 (Waiting Room): 15 minutes
- Test 2 (Cricket Scoring): 30 minutes
- **Total: 45 minutes**

If both pass → Cricket auction ready  
If either fails → Notify immediately for emergency fix

---

**START TESTING NOW**
