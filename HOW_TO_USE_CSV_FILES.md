# How to Use Cricket CSV Files

## Overview
There are 2 CSV files for cricket league management:
1. **Fixtures CSV** - Sets up the 3 ODI match schedule (one-time)
2. **Scoring CSV** - Records player performances after each match (3 times)

---

## 📅 PART 1: Import Fixtures CSV (One-Time Setup)

### Step 1: Create Cricket League
1. Go to homepage
2. Click **"Create Your Competition"**
3. Fill in:
   - Name: "NZ vs England ODI Fantasy"
   - Sport: **Cricket** ⚾
   - Budget: £400m
   - Managers: 3
   - Players per Manager: 5 (or 4-6)
4. Click Create
5. Share invite token with other 2 managers

### Step 2: Navigate to Fixtures Tab
1. After creating league, go to **"My Competitions"**
2. Click **"View Dashboard"** on your league
3. Click the **"Fixtures"** tab

### Step 3: Upload Fixtures CSV
1. You'll see a panel: **"Import Fixtures (CSV)"** (Commissioner only)
2. Click **"Choose File"**
3. Select: `/app/scripts/create_nz_eng_fixtures_template.csv`
4. Click **"Upload"**
5. Success message will appear

### What You'll See:
```
✅ Successfully imported 3 fixtures

Fixtures List:
📅 Match 1 - Oct 26, 2025 @ 2:00 PM - Bay Oval, Mount Maunganui
📅 Match 2 - Oct 29, 2025 @ 2:00 PM - Seddon Park, Hamilton
📅 Match 3 - Nov 1, 2025 @ 2:00 PM - Basin Reserve, Wellington
```

**Note:** All 3 managers can now see the fixtures in their dashboard.

---

## 🏏 PART 2: Upload Match Scores (After Each ODI)

### Workflow for Each Match:

**AFTER Match 1 completes on Oct 26:**

#### Step 1: Get Real Match Stats
Watch the match or check scores from:
- ESPNcricinfo
- Cricbuzz
- ICC official site

#### Step 2: Fill in the CSV
Open `/app/scripts/match_scoring_template.csv` and fill with real stats:

**Example for Match 1:**
```csv
matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
nz-eng-odi-1-2025,harry-brook,85,0,1,0,0
nz-eng-odi-1-2025,joe-root,45,0,0,0,0
nz-eng-odi-1-2025,jos-buttler,32,0,2,1,0
nz-eng-odi-1-2025,jofra-archer,8,4,0,0,0
nz-eng-odi-1-2025,ben-duckett,67,0,1,0,0
nz-eng-odi-1-2025,sam-curran,23,2,1,0,0
nz-eng-odi-1-2025,kane-williamson,102,0,0,0,0
nz-eng-odi-1-2025,mitchell-santner,34,3,0,0,0
nz-eng-odi-1-2025,tom-latham,56,0,3,0,1
nz-eng-odi-1-2025,matt-henry,12,3,1,0,0
nz-eng-odi-1-2025,rachin-ravindra,41,0,2,0,0
```

**Important:**
- `matchId` must match: `nz-eng-odi-1-2025` (from fixtures)
- `playerExternalId` must be lowercase with hyphens: `kane-williamson`
- Only include players who **actually played** in the match
- Only include **players that managers own** (though system handles all)

#### Step 3: Upload via API
```bash
# Using the helper script
cd /app/scripts
./upload_match_scores.sh YOUR_LEAGUE_ID match_1_scores.csv

# Or direct curl
curl -X POST "https://competition-hub-6.preview.emergentagent.com/api/scoring/YOUR_LEAGUE_ID/ingest" \
  -F "file=@match_1_scores.csv"
```

#### Step 4: View Updated Leaderboard
```bash
# Via API
curl "https://competition-hub-6.preview.emergentagent.com/api/scoring/YOUR_LEAGUE_ID/leaderboard"

# Or in UI (if we add the leaderboard view)
# Go to dashboard → Standings tab
```

**Response Example:**
```json
{
  "leagueId": "abc123",
  "leaderboard": [
    {
      "userId": "user1",
      "displayName": "Manager Alice",
      "totalPoints": 247.0,
      "players": [
        {"name": "Kane Williamson", "points": 102},
        {"name": "Harry Brook", "points": 95},
        {"name": "Tom Latham", "points": 50}
      ]
    },
    {
      "userId": "user2",
      "displayName": "Manager Bob",
      "totalPoints": 198.0,
      ...
    }
  ]
}
```

#### Step 5: Repeat for Match 2 & 3
- After Match 2 (Oct 29): Upload with `matchId: nz-eng-odi-2-2025`
- After Match 3 (Nov 1): Upload with `matchId: nz-eng-odi-3-2025`
- Points accumulate across all matches

---

## 📊 Points Calculation Reference

| Action | Points | Example |
|--------|--------|---------|
| Run | 1 | 85 runs = 85 points |
| Wicket | 20 | 4 wickets = 80 points |
| Catch | 10 | 2 catches = 20 points |
| Stumping | 10 | 1 stumping = 10 points |
| Run Out | 10 | 1 run out = 10 points |

**Example Player Score:**
```
Jos Buttler:
- 32 runs = 32 × 1 = 32 points
- 2 catches = 2 × 10 = 20 points
- 1 stumping = 1 × 10 = 10 points
TOTAL = 62 points
```

---

## 🎯 Quick Reference

### Player External IDs (for CSV):
**England:**
- harry-brook, joe-root, ben-duckett, tom-banton
- jos-buttler, jamie-smith
- sam-curran, liam-dawson, jacob-bethell, jamie-overton
- jofra-archer, brydon-carse, adil-rashid, rehan-ahmed, luke-wood, sonny-baker

**New Zealand:**
- kane-williamson, devon-conway, will-young
- tom-latham
- mitchell-santner, michael-bracewell, mark-chapman, daryl-mitchell, rachin-ravindra
- matt-henry, kyle-jamieson, jacob-duffy, zak-foulkes, nathan-smith

### Match IDs:
- Match 1: `nz-eng-odi-1-2025`
- Match 2: `nz-eng-odi-2-2025`
- Match 3: `nz-eng-odi-3-2025`

---

## 🔧 Troubleshooting

**"Player not found" error:**
- Check spelling: must be lowercase with hyphens
- Example: "Kane Williamson" → `kane-williamson`

**"Match ID not found" error:**
- Ensure fixtures were imported first
- Check match ID matches exactly: `nz-eng-odi-1-2025`

**"Duplicate entry" error:**
- Can't upload same match twice (prevents double counting)
- To fix stats: delete from database first, then re-upload

**"Unauthorized" error:**
- Only commissioner can upload scores
- Check you're using commissioner's user ID

---

## 📁 File Locations

All CSV files are in `/app/scripts/`:
- `create_nz_eng_fixtures_template.csv` - Fixtures (use once)
- `match_scoring_template.csv` - Template for scoring (copy 3 times)
- `upload_match_scores.sh` - Helper script for uploading

**Recommended:** Create 3 copies of the scoring template:
```bash
cp match_scoring_template.csv match_1_scores.csv
cp match_scoring_template.csv match_2_scores.csv
cp match_scoring_template.csv match_3_scores.csv
```

Then fill each after the respective match completes.

---

## ✅ Summary Timeline

**Before Oct 26:**
1. Create cricket league ✓
2. Upload fixtures CSV ✓
3. Run auction (3 managers pick 5 players each) ✓

**After Oct 26 Match 1:**
1. Fill match_1_scores.csv with real stats
2. Upload via script or API
3. Check leaderboard

**After Oct 29 Match 2:**
1. Fill match_2_scores.csv
2. Upload
3. Check updated leaderboard (cumulative)

**After Nov 1 Match 3:**
1. Fill match_3_scores.csv
2. Upload
3. Final leaderboard - declare winner! 🏆

---

Need help? Check `/app/CRICKET_NZ_ENG_SETUP.md` for full technical details.
