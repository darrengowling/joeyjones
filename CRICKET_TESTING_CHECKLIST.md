# Cricket Testing Checklist - Before Real Auction

## 🎯 Testing Goal
Validate the complete cricket workflow before the real NZ vs England ODI competition on October 26, 2025.

---

## ✅ Pre-Testing Setup

### 1. Create Test League
- [ ] Sign in with test account
- [ ] Click "Create Your Competition"
- [ ] Set name: **"TEST - Cricket Demo"** (include "TEST" for easy cleanup)
- [ ] Select Sport: **Cricket** 🏏
- [ ] Budget: £400m
- [ ] Min/Max Managers: 3
- [ ] Players per Manager: 5
- [ ] Click Create

### 2. Invite Test Participants
- [ ] Copy invite token from league detail page
- [ ] Create 2 more test accounts (or use existing)
- [ ] Each account joins using invite token
- [ ] Verify all 3 participants appear in league

### 3. Import Fixtures
- [ ] Go to "My Competitions"
- [ ] Click "View Dashboard" on test league
- [ ] Click "Fixtures" tab
- [ ] Upload: `/app/scripts/create_nz_eng_fixtures_template.csv`
- [ ] Verify 3 fixtures appear:
  - [ ] Match 1: Oct 26, 2025 - Bay Oval, Mount Maunganui
  - [ ] Match 2: Oct 29, 2025 - Seddon Park, Hamilton
  - [ ] Match 3: Nov 1, 2025 - Basin Reserve, Wellington

---

## 🏏 Auction Testing

### 4. Start Auction
- [ ] Commissioner clicks "Start Auction" button
- [ ] Verify auction status changes to **"waiting"**
- [ ] All 3 participants enter auction room
- [ ] Verify waiting room shows:
  - [ ] Participant list with 3 managers
  - [ ] "Begin Auction" button (commissioner only)
  - [ ] "Waiting for commissioner..." message (others)

### 5. Begin Auction
- [ ] Commissioner clicks "Begin Auction"
- [ ] Verify first player appears (from 30 NZ/England players)
- [ ] Verify timer shows custom settings (20s bid time, 5s anti-snipe)
- [ ] Check player details:
  - [ ] Name visible
  - [ ] Team (England/New Zealand)
  - [ ] Role (Batsman/Bowler/All-rounder/Wicketkeeper)

### 6. Bidding Flow
- [ ] Manager 1 places first bid (£5m)
- [ ] Verify all 3 managers see the bid immediately
- [ ] Manager 2 bids higher (£7m)
- [ ] Verify current bid updates in real-time
- [ ] Let timer run down to test auto-advance
- [ ] Verify winner announced
- [ ] Verify budget deducted correctly

### 7. Budget Reserve Enforcement
- [ ] Manager wins 4th player (has 1 slot remaining)
- [ ] Try to bid more than (budget - £1m)
- [ ] Verify error: "Must reserve £1m for remaining slot"
- [ ] Verify can bid exactly (budget - £1m)

### 8. Complete Auction
- [ ] Continue until all 3 managers have 5 players each
- [ ] Verify auction completes
- [ ] Check final state:
  - [ ] All 15 players distributed (5 per manager)
  - [ ] All budgets deducted correctly
  - [ ] Auction status = "completed"

---

## 📊 Scoring Testing

### 9. Upload Test Match Scores
Use the example CSV or create your own test data:

```bash
# Use example file with fake stats
cd /app/scripts
./upload_match_scores.sh YOUR_LEAGUE_ID example_match_1_scores.csv
```

OR manually via API:
```bash
curl -X POST "https://auction-room-wizard.preview.emergentagent.com/api/scoring/YOUR_LEAGUE_ID/ingest" \
  -F "file=@example_match_1_scores.csv"
```

### 10. Verify Scoring Calculation
Check if points calculated correctly (use example file):
- [ ] Harry Brook: 85 runs + 1 catch = 95 points
- [ ] Jofra Archer: 8 runs + 4 wickets = 88 points
- [ ] Jos Buttler: 32 runs + 2 catches + 1 stumping = 62 points
- [ ] Kane Williamson: 102 runs = 102 points
- [ ] Mitchell Santner: 34 runs + 3 wickets = 94 points
- [ ] Tom Latham: 56 runs + 3 catches + 1 run out = 96 points

### 11. View Leaderboard
```bash
# Via API
curl "https://auction-room-wizard.preview.emergentagent.com/api/scoring/YOUR_LEAGUE_ID/leaderboard" | jq

# Check output:
# - All 3 managers listed
# - Points accumulated for their players
# - Sorted by total points
```

- [ ] Manager with Kane Williamson should have 102+ points
- [ ] Points correctly sum across all their players
- [ ] Leaderboard sorted highest to lowest

### 12. Test Multi-Match Scoring
- [ ] Create `match_2_test_scores.csv` with different matchId
- [ ] Upload second match scores
- [ ] Verify leaderboard updates with **cumulative** points
- [ ] Confirm Match 1 + Match 2 points added together

---

## 🎨 UI/UX Testing

### 13. Dashboard Verification
Go to Competition Dashboard:
- [ ] **Summary Tab:**
  - [ ] Shows league name, status
  - [ ] "Your Roster" displays your 5 players with names & prices
  - [ ] "Your Budget" shows remaining budget
  - [ ] "Managers List" shows ALL 3 managers with their rosters (Bug Fix 5)
  - [ ] Each manager's card shows their players and budget
  
- [ ] **League Table Tab:**
  - [ ] Shows all 3 managers
  - [ ] Points column populated after scoring upload
  - [ ] Current user row highlighted
  - [ ] Cricket-specific tiebreakers (Runs/Wickets columns)

- [ ] **Fixtures Tab:**
  - [ ] Shows all 3 ODI fixtures
  - [ ] Dates and venues visible
  - [ ] Commissioner sees "Upload Scores" option

### 14. Roster Visibility (Bug Fix 5)
In Managers List section:
- [ ] See Manager 1's full roster (5 players with names/prices)
- [ ] See Manager 2's full roster (5 players with names/prices)
- [ ] See Manager 3's full roster (5 players with names/prices)
- [ ] Your own roster highlighted with blue border
- [ ] Budget remaining shown for each manager

### 15. Mobile Testing (Optional)
- [ ] Test on mobile browser
- [ ] Verify auction room responsive
- [ ] Verify dashboard tabs work
- [ ] Verify CSV upload works

---

## 🗑️ Cleanup After Testing

### 16. Review Test Data
```bash
cd /app/scripts
python cleanup_test_cricket_data.py list
```

This shows all cricket leagues. Verify which ones are tests.

### 17. Delete Test Leagues (Dry Run First)
```bash
# Dry run - see what would be deleted
python cleanup_test_cricket_data.py clean-test

# Output shows leagues matching "test", "debug", or "demo"
# Reviews all related data that would be deleted
```

### 18. Confirm Deletion
```bash
# Actually delete test leagues
python cleanup_test_cricket_data.py clean-test --confirm

# Type "DELETE" when prompted
# Removes: leagues, auctions, bids, participants, fixtures, standings, stats
```

### 19. Verify Cleanup
```bash
# List cricket leagues again
python cleanup_test_cricket_data.py list

# Should show no test leagues remaining
# Only real leagues (if any) remain
```

---

## 🚀 Ready for Real Auction

### Before Oct 26:
- [ ] All testing complete
- [ ] Test data cleaned up
- [ ] Create **real** league: "NZ vs England ODI Series"
- [ ] Share invite token with real participants
- [ ] Import fixtures (same CSV works)
- [ ] Wait for participants to join

### On Oct 26 (Before Match 1):
- [ ] Run auction with real participants
- [ ] All managers select their 5 players
- [ ] Auction completes successfully

### After Each Match:
- [ ] Fill scoring CSV with real match stats
- [ ] Upload scores
- [ ] Check leaderboard
- [ ] Announce standings to participants

---

## 📝 Testing Notes

**Common Issues to Watch For:**
1. **Timer not displaying custom settings** - Should show 20s/5s (Bug Fix 1)
2. **Waiting room not showing** - Should appear before auction begins (Bug Fix 2)
3. **Budget reserve not enforcing** - Should block bids leaving < £1m/slot (Bug Fix 3)
4. **Can't see other rosters** - Should see all managers' players (Bug Fix 5)

**Report any issues found during testing!**

---

## ✅ Sign-Off Checklist

Before declaring cricket ready:
- [ ] All test cases passed
- [ ] No critical bugs found
- [ ] Scoring calculations correct
- [ ] CSV uploads work smoothly
- [ ] Leaderboard displays properly
- [ ] Test data cleaned up
- [ ] Ready to create real league

---

**Once all tests pass, cricket is ready for the Oct 26 pilot! 🎉**
