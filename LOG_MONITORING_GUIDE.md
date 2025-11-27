# Auction Log Monitoring Guide

## Quick Reference for Testing & Debugging

---

## 🔍 Real-Time Log Monitoring

### During Your Test Auction:

```bash
# Watch auction-specific logs in real-time
tail -f /var/log/supervisor/backend.out.log | grep "COMPLETE_LOT\|COMPLETION_CHECK"
```

---

## 📊 What to Look For

### ✅ HEALTHY Auction Completion (Final Lot)

You should see logs like this when the final lot completes:

```
🎬 COMPLETE_LOT START for auction abc-123
   Lot 6/6, Club: Leeds United
   Bids found: 1, Winning bid: £7,000,000
   BEFORE: User daz2 has 2 clubs, spent £10,000,000
   AFTER: User daz2 now has 3 clubs, spent £17,000,000
   DB Update: modified_count=1
✅ Club sold - Leeds to daz2 for £7,000,000

🔍 COMPLETION_CHECK [Auction: abc-123]:
   currentLot=6, clubQueue_length=6, unsold=0
   Logic: (6 <= 6) = True
   clubs_remaining=True, should_complete=False
   eligible_bidders=1, all_managers_full=False
   
🔍 COMPLETION_CHECK [Auction: abc-123]:
   currentLot=6, clubQueue_length=6, unsold=0
   Logic: (6 <= 6) = True  
   clubs_remaining=False, should_complete=True
   eligible_bidders=0, all_managers_full=True

✅ AUCTION COMPLETED: abc-123 - 6 sold, 0 unsold
```

**Key indicators:**
- `COMPLETE_LOT START` - Lot processing begins
- `BEFORE` and `AFTER` - Club is being awarded
- `DB Update: modified_count=1` - Database actually updated
- `Club sold` - Confirmation message
- `clubs_remaining=True` first, then `False` - Logic progresses correctly
- `AUCTION COMPLETED` - Final confirmation

---

### 🚨 PROBLEM Signs to Watch For

#### Issue 1: Bid Not Awarded
```
🎬 COMPLETE_LOT START for auction abc-123
   Lot 6/6, Club: Leeds United
   Bids found: 1, Winning bid: £7,000,000
   BEFORE: User daz2 has 2 clubs, spent £10,000,000
   ❌ CRITICAL: Participant NOT FOUND for user daz2
```
**Problem:** Participant lookup failed
**Action:** Check user IDs match between bids and participants

#### Issue 2: Early Completion
```
🔍 COMPLETION_CHECK [Auction: abc-123]:
   currentLot=6, clubQueue_length=6, unsold=0
   Logic: (6 <= 6) = True
   clubs_remaining=False, should_complete=True    <-- ⚠️ Wrong!
   
✅ AUCTION COMPLETED: abc-123 - 5 sold, 0 unsold  <-- Only 5 sold!
```
**Problem:** Auction completed before processing final lot
**Action:** Logic error - report immediately

#### Issue 3: No Completion Logs
```
🎬 COMPLETE_LOT START for auction abc-123
   Lot 6/6, Club: Leeds United
   
[nothing more...]
```
**Problem:** `complete_lot()` crashed or hung
**Action:** Check error logs for exceptions

---

## 🛠️ Useful Log Commands

### Check Backend Status
```bash
sudo supervisorctl status backend
```

### View Last 100 Lines of Logs
```bash
tail -n 100 /var/log/supervisor/backend.out.log
```

### View Error Logs Only
```bash
tail -n 50 /var/log/supervisor/backend.err.log
```

### Search for Specific Auction
```bash
grep "abc-123" /var/log/supervisor/backend.out.log | tail -n 50
```

### Search for Errors in Last Hour
```bash
grep -i "error\|exception\|critical" /var/log/supervisor/backend.out.log | tail -n 50
```

### Watch for Auction Completion Events
```bash
tail -f /var/log/supervisor/backend.out.log | grep "AUCTION COMPLETED\|should_complete"
```

---

## 📋 Testing Checklist with Log Verification

For each test scenario, verify the logs show correct behavior:

### Test 1: Basic 3-Club Auction
- [ ] Start auction, see `currentLot=1`
- [ ] Complete lot 1, see `currentLot=2`
- [ ] Complete lot 2, see `currentLot=3`
- [ ] Complete lot 3, see:
  - `Lot 3/3`
  - `clubs_remaining=True` (while processing)
  - `clubs_remaining=False` (after processing)
  - `AUCTION COMPLETED: ... 3 sold`

### Test 2: Final Lot Single Bidder
- [ ] Lot 3 completes with 1 bid
- [ ] See `Bids found: 1`
- [ ] See `BEFORE: User has 2 clubs`
- [ ] See `AFTER: User has 3 clubs`
- [ ] See `DB Update: modified_count=1`
- [ ] Auction completes successfully

### Test 3: Anti-Snipe on Final Lot
- [ ] Bid placed in last 2 seconds of final lot
- [ ] See timer extension message (anti-snipe)
- [ ] Final lot still completes correctly
- [ ] Bid is awarded

---

## 🔴 When to Stop Testing & Report

Stop testing and report to me if you see:

1. **"CRITICAL: Participant NOT FOUND"** - Database inconsistency
2. **Auction completes with fewer clubs than expected** - Premature completion
3. **`modified_count=0`** - Database update failed
4. **Any Python exceptions** - Code crash
5. **Lot processing stops mid-auction** - Hung state

In any of these cases:
1. Note the auction ID from the logs
2. Save the full log section (last 200 lines)
3. Share with me for investigation

---

## ✅ Success Indicators

You can be confident the auction worked if:

1. All `COMPLETE_LOT` sequences finish with `Club sold` or `unsold`
2. Final `COMPLETION_CHECK` shows `should_complete=True`
3. `AUCTION COMPLETED` message appears
4. Participant counts match expected (check UI or database)
5. No error messages in logs

---

## 📞 Quick Support

If you see something unexpected:

```bash
# Capture last 200 lines of relevant logs
tail -n 200 /var/log/supervisor/backend.out.log > auction_logs.txt

# Share auction_logs.txt with me
```

I can diagnose issues much faster with the actual logs.

---

**Remember:** The logs are your friend! They now show the exact internal state and logic flow. If something goes wrong, the logs will tell us exactly where and why.
