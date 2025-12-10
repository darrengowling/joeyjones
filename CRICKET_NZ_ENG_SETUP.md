# Cricket Setup: New Zealand vs England ODI Series (Oct 2025)

## ✅ COMPLETED SETUP

### 1. Player Database (30 Players)
**England Squad (16 players):**
- Batters: Harry Brook (C), Joe Root, Ben Duckett, Tom Banton
- All-rounders: Sam Curran, Liam Dawson, Jacob Bethell, Jamie Overton
- Wicketkeepers: Jos Buttler, Jamie Smith
- Bowlers: Jofra Archer, Brydon Carse, Adil Rashid, Rehan Ahmed, Luke Wood, Sonny Baker

**New Zealand Squad (14 players):**
- Batters: Kane Williamson, Devon Conway, Will Young
- All-rounders: Mitchell Santner (C), Michael Bracewell, Mark Chapman, Daryl Mitchell, Rachin Ravindra
- Wicketkeeper: Tom Latham
- Bowlers: Matt Henry, Kyle Jamieson, Jacob Duffy, Zak Foulkes, Nathan Smith

### 2. Scoring Rules (Updated)
```json
{
  "type": "perPlayerMatch",
  "rules": {
    "run": 1,        // 1 point per run
    "wicket": 20,    // 20 points per wicket
    "catch": 10,     // 10 points per catch
    "stumping": 10,  // 10 points per stumping
    "runOut": 10     // 10 points per run out
  },
  "milestones": {}   // No milestones/bonuses
}
```

### 3. ODI Series Schedule
| Match | Date & Time (UTC) | Venue | External ID |
|-------|------------------|-------|-------------|
| 1st ODI | Oct 26, 2025 @ 2:00 PM | Bay Oval - Mount Maunganui | nz-eng-odi-1-2025 |
| 2nd ODI | Oct 29, 2025 @ 2:00 PM | Seddon Park - Hamilton | nz-eng-odi-2-2025 |
| 3rd ODI | Nov 1, 2025 @ 2:00 PM | Basin Reserve - Wellington | nz-eng-odi-3-2025 |

**Note:** Times are in UTC (2:00 PM UTC = 3:00 PM NZDT)

### 4. League Configuration (Recommended)
- **Managers:** 3 participants
- **Budget:** £400m per manager
- **Players per Manager:** 4-6 (commissioner can adjust)
- **Sport:** Cricket
- **Auction Timer:** 20 seconds (customizable)
- **Anti-snipe:** 5 seconds (customizable)

---

## 📋 HOW TO USE

### Step 1: Create Cricket League
```bash
# Via UI or API
POST /api/leagues
{
  "name": "NZ vs England ODI Fantasy",
  "sportKey": "cricket",
  "commissionerId": "{userId}",
  "budget": 400000000,  // £400m
  "minManagers": 3,
  "maxManagers": 3,
  "clubSlots": 5,  // 5 players per manager (adjust 4-6)
  "timerSeconds": 20,
  "antiSnipeSeconds": 5
}
```

### Step 2: Import Fixtures
Upload `/app/scripts/create_nz_eng_fixtures_template.csv` via the Competition Dashboard:
1. Go to league → Fixtures tab
2. Click "Upload CSV"
3. Select the template file
4. Fixtures will be created with dates, venues

### Step 3: Run Auction
1. All 3 managers join the league
2. Commissioner starts auction
3. Each manager bids on 4-6 players from the 30-player pool
4. Auction completes when all managers have full rosters

### Step 4: Score Matches (After Each ODI)
**Option A: Manual CSV Upload**
1. After each match, fill in `/app/scripts/match_scoring_template.csv`:
   ```csv
   matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
   nz-eng-odi-1-2025,harry-brook,75,0,1,0,0
   nz-eng-odi-1-2025,jofra-archer,12,3,0,0,0
   nz-eng-odi-1-2025,kane-williamson,89,0,0,0,0
   ```
2. Upload via: `POST /api/scoring/{leagueId}/ingest`
3. Leaderboard updates automatically

**Option B: API Score Scraping (Future Enhancement)**
Potential sources for automated score retrieval:
- **CricketData.org** - Free API with basic match stats
- **Self-hosted scraper** - Use sanwebinfo/cricket-api (scrapes Cricbuzz)
- **Manual integration** - ESPN Cricinfo unofficial scraping

**Scoring Calculation Example:**
```
Harry Brook: 75 runs + 1 catch = (75 × 1) + (1 × 10) = 85 points
Jofra Archer: 12 runs + 3 wickets = (12 × 1) + (3 × 20) = 72 points
Kane Williamson: 89 runs = 89 × 1 = 89 points
```

### Step 5: View Leaderboard
```bash
GET /api/scoring/{leagueId}/leaderboard

# Returns sorted leaderboard with accumulated points across all matches
```

---

## 🧪 TESTING CHECKLIST

### Pre-Series (Before Oct 26)
- [ ] Create test league with 3 managers
- [ ] Import fixtures from CSV
- [ ] Run test auction with 30 players
- [ ] Verify each manager can select 4-6 players
- [ ] Test budget constraints (£400m)

### During Series (Oct 26 - Nov 1)
- [ ] Upload Match 1 scores after completion
- [ ] Verify leaderboard updates correctly
- [ ] Check points calculation (1pt/run, 20pts/wicket, etc.)
- [ ] Upload Match 2 & 3 scores
- [ ] Verify cumulative scoring across matches

### Post-Series (After Nov 1)
- [ ] Verify final standings
- [ ] Check all 3 matches reflected in leaderboard
- [ ] Export results if needed

---

## 🔍 VERIFICATION COMMANDS

**Check Players Loaded:**
```bash
curl "https://prod-stable-soccer.preview.emergentagent.com/api/assets?sportKey=cricket" | jq '.pagination.total'
# Should return: 30
```

**Check Scoring Rules:**
```bash
curl "https://prod-stable-soccer.preview.emergentagent.com/api/sports/cricket" | jq '.scoringSchema'
# Verify: run=1, wicket=20, catch=10, stumping=10, runOut=10, milestones={}
```

**Check Fixtures Template:**
```bash
cat /app/scripts/create_nz_eng_fixtures_template.csv
```

---

## 📊 SCORE SCRAPING OPTIONS

### Option 1: CricketData.org (Recommended)
- **Pros:** Free API, JSON format, reliable
- **Cons:** May have rate limits
- **Setup:** Register for API key, create integration script

### Option 2: Self-Hosted Scraper
- **Tool:** sanwebinfo/cricket-api (GitHub)
- **Pros:** Free, customizable
- **Cons:** Requires hosting, unofficial (may break), legal concerns
- **Setup:** Deploy on Vercel/Docker, point to Cricbuzz

### Option 3: Manual Entry (Current)
- **Pros:** 100% accurate, no API dependencies
- **Cons:** Manual work after each match
- **Time:** ~5-10 minutes per match to fill CSV

**Recommendation:** Start with manual CSV upload for Oct 2025 series. If successful, build automated scraper for future series.

---

## 🚀 NEXT STEPS

1. **User creates test league** with cricket sport
2. **Test auction flow** with 30 NZ/England players
3. **Prepare scoring workflow** (manual or automated)
4. **Monitor Oct 26** for first ODI
5. **Upload scores** within 1-2 hours of match completion
6. **Review leaderboard** and iterate

---

## 📝 FILES CREATED
- `/app/scripts/seed_nz_eng_players.py` - Player seeding script
- `/app/scripts/create_nz_eng_fixtures_template.csv` - Fixtures template
- `/app/scripts/match_scoring_template.csv` - Scoring template
- `/app/CRICKET_NZ_ENG_SETUP.md` - This documentation

**Status:** ✅ Cricket ready for NZ vs England ODI series testing!
