# Flexible Fixture Import for Commissioners

## ✅ Yes! Commissioners Can Import ANY Number of Fixtures

The CSV import system has **no minimum or maximum fixture requirements**. Commissioners can run competitions for:
- ✅ Just 1 match
- ✅ 2 or 3 selected matches
- ✅ All 5 Test matches
- ✅ Any combination they want

---

## 🎯 Use Cases

### Scenario 1: "Single Match Challenge"
**Situation**: Tests 1 and 2 are already done. Commissioner wants to run a competition just for the 3rd Test at the Gabba.

**CSV File** (`ashes_single_match.csv`):
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-12-14 23:30:00,australia,england,The Gabba - Brisbane,3rd Test,ashes-2025-test-3
```

**What Happens:**
1. Commissioner creates league with 15 players
2. Managers auction players
3. Commissioner imports this 1-fixture CSV
4. After the 3rd Test completes, commissioner clicks "Update Cricket Scores"
5. Winner determined by performance in THIS ONE MATCH ONLY

**Leaderboard Example:**
```
Final Standings (After 3rd Test):
1. Manager A: 245 points (Travis Head 150 runs, Nathan Lyon 3 wkts)
2. Manager B: 180 points (Ben Stokes 80 runs, 2 wkts)
3. Manager C: 120 points (Joe Root 100 runs)
```

---

### Scenario 2: "Boxing Day & New Year Special"
**Situation**: Commissioner wants to run a competition for just the last 2 Tests (4th and 5th).

**CSV File** (`ashes_last_two_tests.csv`):
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-12-26 23:30:00,australia,england,Melbourne Cricket Ground,4th Test - Boxing Day,ashes-2025-test-4
2026-01-03 23:30:00,australia,england,Sydney Cricket Ground,5th Test,ashes-2025-test-5
```

**What Happens:**
1. Commissioner creates league
2. Imports these 2 fixtures
3. After MCG match, commissioner updates scores → Leaderboard after Match 1
4. After SCG match, commissioner updates scores → Final standings (sum of both matches)

**Cumulative Scoring:**
```
After MCG (4th Test):
1. Manager A: 180 points
2. Manager B: 150 points
3. Manager C: 140 points

After SCG (5th Test) - FINAL:
1. Manager B: 320 points (150 + 170)  ← WINNER
2. Manager A: 305 points (180 + 125)
3. Manager C: 275 points (140 + 135)
```

---

### Scenario 3: "Full Series Challenge"
**Situation**: Commissioner wants the traditional full Ashes experience.

**CSV File** (`ashes_fixtures_examples.csv`):
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-11-21 23:30:00,australia,england,Perth Stadium,1st Test,ashes-2025-test-1
2025-12-06 03:30:00,australia,england,Adelaide Oval,2nd Test - Day/Night,ashes-2025-test-2
2025-12-14 23:30:00,australia,england,The Gabba - Brisbane,3rd Test,ashes-2025-test-3
2025-12-26 23:30:00,australia,england,Melbourne Cricket Ground,4th Test - Boxing Day,ashes-2025-test-4
2026-01-03 23:30:00,australia,england,Sydney Cricket Ground,5th Test,ashes-2025-test-5
```

**What Happens:**
- Manager points accumulate across all 5 Tests
- Most consistent performance wins

---

## 🔧 Technical Details

### How CSV Import Works

**Backend Logic** (`/app/backend/server.py`, line 1792):
```python
for row in reader:
    # Parse row data
    starts_at_str = row.get('startsAt', '').strip()
    home_external_id = row.get('homeAssetExternalId', '').strip()
    # ... more parsing ...
    
    # Create fixture
    fixture = Fixture(
        leagueId=league_id,        # ← Links to this league
        sportKey=sport_key,
        externalMatchId=external_match_id,
        # ... more fields ...
    )
    
    # Insert into database
    await db.fixtures.update_one(...)
    fixtures_imported += 1
```

**Key Points:**
- ✅ No validation on fixture count
- ✅ Simple loop through CSV rows
- ✅ Each row = 1 fixture
- ✅ Imports exactly what's in the CSV

---

## 📊 Manager Scoring Across Multiple Fixtures

### How Points Accumulate

**Database Structure** (`league_points` collection):
```json
{
  "leagueId": "abc-123",
  "userId": "manager-001",
  "assetId": "mitchell-starc",
  "fixtureId": "fixture-001",      ← 3rd Test
  "points": 100                    ← 5 wickets × 20
}
{
  "leagueId": "abc-123",
  "userId": "manager-001",
  "assetId": "mitchell-starc",
  "fixtureId": "fixture-002",      ← 4th Test
  "points": 60                     ← 3 wickets × 20
}
```

**Leaderboard Calculation:**
```sql
-- Sum all points per manager
SELECT userId, SUM(points) as totalPoints
FROM league_points
WHERE leagueId = 'abc-123'
GROUP BY userId
ORDER BY totalPoints DESC
```

**Result:**
```
Manager A: 456 points (across 2 fixtures)
Manager B: 389 points (across 2 fixtures)
Manager C: 301 points (across 2 fixtures)
```

---

## 🎮 Commissioner Workflow for Single Match

### Step-by-Step: Running a 3rd Test Only Competition

**1. Create League**
```
Name: "Gabba Test Special"
Sport: Cricket
Players: Select 20 Ashes players
Budget: $500M
Managers: 4 spots
```

**2. Run Auction**
- Managers bid on players
- Each manager gets 5 players
- Auction completes

**3. Import Single Fixture**
- Upload CSV with JUST the 3rd Test
- System creates 1 fixture linked to this league

**4. Match Happens**
- Real world: Australia vs England at Gabba
- Travis Head: 140 runs
- Nathan Lyon: 4 wickets
- Ben Stokes: 75 runs, 2 wickets

**5. Update Scores**
- Commissioner clicks "🏏 Update Cricket Scores"
- Cricbuzz API fetches 3rd Test scorecard
- System finds the ONE fixture for this league
- Calculates manager points

**6. Winner Declared**
```
FINAL STANDINGS:
🥇 Manager A: 255 pts (Head: 140, Carey: 45, Boland: 2 wkts)
🥈 Manager B: 215 pts (Stokes: 115, Root: 100)
🥉 Manager C: 180 pts (Smith: 80, Lyon: 80, Starc: 20)
🏅 Manager D: 140 pts (Brook: 60, Cummins: 3 wkts)
```

**Competition ends after this ONE match!**

---

## 🧪 Testing Single Fixture Import

### Test with Backend

**1. Create test CSV:**
```bash
cat > /tmp/test_single_fixture.csv << 'EOF'
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-12-14 23:30:00,australia,england,The Gabba,3rd Test,test-match-001
EOF
```

**2. Import via API:**
```bash
curl -X POST "http://localhost:8001/api/leagues/{league_id}/fixtures/import-csv" \
  -F "file=@/tmp/test_single_fixture.csv" \
  -F "commissionerId={commissioner_id}"
```

**Expected Response:**
```json
{
  "message": "Successfully imported 1 fixtures",
  "fixturesImported": 1
}
```

**3. Verify:**
```bash
# Check fixtures in database
curl "http://localhost:8001/api/leagues/{league_id}/fixtures"
```

---

## ⚡ Benefits of Flexible Import

### For Commissioners:

1. **Mid-Season Entry**
   - Series already started? Join for remaining matches!
   - No need to wait for the next full series

2. **Time Management**
   - Busy schedule? Run a 1-match "quick competition"
   - Available all week? Run the full 5-Test series

3. **Testing**
   - Try a single match first
   - If successful, run full series next time

4. **Event-Specific**
   - "Boxing Day Test Only" competition
   - "Perth Test Special" (notorious bouncy pitch)
   - "SCG Finale" (series decider)

5. **Multiple Competitions**
   - Run one competition for Tests 1-3
   - Run another for Tests 4-5
   - Different player pools, different managers

---

## 📋 CSV Format Reference

### Required Fields:
- `startsAt`: Match start time (YYYY-MM-DD HH:MM:SS format)
- `homeAssetExternalId`: "australia" or "england"
- `awayAssetExternalId`: "australia" or "england"

### Optional Fields:
- `venue`: Stadium name (for display)
- `round`: "1st Test", "2nd Test", etc.
- `externalMatchId`: Unique identifier for API matching

### Important Notes:
- ✅ Times in UTC or local time (system will parse)
- ✅ `homeAssetExternalId` and `awayAssetExternalId` must match asset `externalId` values in database
- ✅ For Ashes, use "australia" and "england" (lowercase)
- ✅ Can import same CSV multiple times (upsert logic prevents duplicates)

---

## ✅ Summary

**Question**: Can commissioners run a competition for just 1 fixture?

**Answer**: **YES! Absolutely!**

- ✅ Import 1 fixture → Competition for that match only
- ✅ Import 2 fixtures → Competition across those 2 matches
- ✅ Import 5 fixtures → Full series competition
- ✅ **No restrictions on fixture count**

**The system is 100% flexible!**

---

## 📁 Example CSV Files Created

1. `/app/ashes_fixtures_examples.csv` - All 5 Tests
2. `/app/ashes_fixtures_single_match.csv` - Just 3rd Test
3. `/app/ashes_fixtures_last_two_tests.csv` - 4th & 5th Tests only

**Commissioners can use any of these or create their own!**
