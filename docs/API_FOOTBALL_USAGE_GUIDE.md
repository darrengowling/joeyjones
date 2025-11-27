# API-FOOTBALL Integration - Usage Guide
## For Nov 29-30, 2025 EPL Tournament

**API Key**: ce31120a72a2158ab9e33a56233bf39f  
**Tier**: Free (100 requests/day)  
**Status**: ✅ Configured and Working

---

## How It Works

1. **Before Matches** (Now - Nov 28):
   - Fixtures display on league pages shows "Upcoming Matches"
   - Shows match dates and times
   - Teams highlighted if they're in the league

2. **During/After Matches** (Nov 29-30):
   - Trigger score update endpoint
   - System fetches latest results from API-FOOTBALL
   - Fixtures automatically update with scores
   - Click "Recompute Scores" to update league standings

---

## Usage Instructions

### Option 1: Manual Trigger (Recommended for Free Tier)

**When to trigger:**
- After Saturday matches (Nov 29 evening)
- After Sunday matches (Nov 30 evening)

**How to trigger:**
```bash
curl -X POST https://auctionpilot.preview.emergentagent.com/api/fixtures/update-scores
```

**What happens:**
- System fetches all Nov 29-30 fixtures from API-FOOTBALL
- Updates goals, winners, status in database
- Fixtures on league pages show updated scores
- Uses 1-2 API requests (fetches by date)

### Option 2: Via Browser (If you prefer)

Create a simple admin button (can add later if needed) or use the browser console:
```javascript
fetch('https://auctionpilot.preview.emergentagent.com/api/fixtures/update-scores', {
  method: 'POST'
}).then(r => r.json()).then(console.log);
```

---

## API Request Budget

**Free Tier Limit**: 100 requests/day  
**Expected Usage for Nov 29-30**: 2-6 requests total

**Breakdown:**
- Nov 29 score update: 1 request (fetches all Saturday fixtures)
- Nov 30 score update: 1 request (fetches all Sunday fixtures)
- Optional mid-match updates: 1 request each
- **Total**: 2-6 requests (well within limit)

**Remaining**: 94-98 requests for testing/other uses

---

## Step-by-Step: Nov 29-30 Tournament

### Before Tournament (Now)

1. ✅ API key configured
2. ✅ 20 EPL teams seeded
3. ✅ 10 fixtures seeded for Nov 29-30
4. ✅ Fixtures display on league pages
5. Users create leagues and run auctions

### Saturday, Nov 29

**Morning:**
- Users see "Upcoming Matches" on league pages
- Can check which teams are playing when

**Evening (after 17:30 GMT - last match ends):**
```bash
# Trigger score update
curl -X POST https://auctionpilot.preview.emergentagent.com/api/fixtures/update-scores

# Expected output:
# {
#   "status": "completed",
#   "updated": 5,  // 5 Saturday fixtures
#   "api_requests_remaining": 99
# }
```

- Fixtures update with scores
- Users can view results on league pages
- Standings not updated yet (wait for all matches)

### Sunday, Nov 30

**Evening (after 16:30 GMT - last match ends):**
```bash
# Trigger score update again
curl -X POST https://auctionpilot.preview.emergentagent.com/api/fixtures/update-scores

# Expected output:
# {
#   "status": "completed",
#   "updated": 5,  // 5 Sunday fixtures
#   "api_requests_remaining": 98
# }
```

### After All Matches Complete

**Update League Standings:**
1. Navigate to each league's detail page
2. Click "Recompute Scores" button
3. Standings update based on:
   - Wins: 3 points
   - Draws: 1 point
   - Goals scored: Added to total
4. Winner determined!

---

## Troubleshooting

### Issue: "API_FOOTBALL_KEY not configured"
**Solution**: Backend restart needed
```bash
sudo supervisorctl restart backend
```

### Issue: Score update returns 0 updated fixtures
**Possible causes:**
1. Matches haven't been played yet (check date)
2. API-FOOTBALL hasn't received results yet (try again in 10 mins)
3. External IDs don't match (check team mapping)

**Check fixture status:**
```bash
curl https://auctionpilot.preview.emergentagent.com/api/fixtures?sport_key=football&date=2025-11-29
```

### Issue: Standings not updating after score update
**Solution**: 
1. Verify fixtures have scores (check league page)
2. Click "Recompute Scores" button on league detail page
3. This recalculates standings from fixture data

### Issue: Rate limit exceeded (429 error)
**Daily limit**: 100 requests  
**Current usage**: Check response `api_requests_remaining` field  
**Solution**: Wait until next day (resets at midnight UTC)

---

## API Endpoints Reference

### Update Scores
```bash
POST /api/fixtures/update-scores
```
**Response:**
```json
{
  "status": "completed",
  "updated": 10,
  "errors": [],
  "api_requests_remaining": 98,
  "timestamp": "2025-11-30T18:00:00Z"
}
```

### Get Fixtures for League
```bash
GET /api/leagues/{league_id}/fixtures
```
**Response:**
```json
{
  "fixtures": [
    {
      "homeTeam": "Manchester City",
      "awayTeam": "Leeds United",
      "matchDate": "2025-11-29T15:00:00Z",
      "status": "finished",
      "goalsHome": 3,
      "goalsAway": 1,
      "winner": "Manchester City"
    }
  ],
  "total": 10
}
```

### Get All Fixtures
```bash
GET /api/fixtures?sport_key=football&date=2025-11-29
```

---

## Testing the Integration

**Test now (before Nov 29):**
```bash
# This will return no fixtures (date in future) but confirms API works
curl -X POST https://auctionpilot.preview.emergentagent.com/api/fixtures/update-scores
```

**Expected response:**
```json
{
  "status": "completed",
  "updated": 0,
  "api_requests_remaining": 99
}
```

**Test on Nov 29 evening:**
- Same command
- Should return `"updated": 5` or similar
- Fixtures will have scores

---

## Best Practices

1. **Don't over-poll**: Free tier has 100 req/day limit
2. **Batch updates**: Update once per day, not per match
3. **Manual trigger**: Better control than automated polling
4. **Check remaining**: Monitor `api_requests_remaining` in response
5. **Wait for completion**: Allow 5-10 mins after match ends for API to receive results

---

## Alternative: CSV Upload

If API-FOOTBALL is unavailable or rate-limited, you can still manually upload scores via CSV (existing feature):

1. Create CSV with match results
2. Upload via existing CSV endpoint
3. Click "Recompute Scores"

**CSV is your fallback** - API-FOOTBALL is the convenience layer.

---

## Summary

**Setup**: ✅ Complete  
**API Key**: ✅ Working (tested)  
**Free Tier**: ✅ Sufficient (2-6 of 100 requests needed)  
**Ready for Nov 29-30**: ✅ Yes  

**Your Action on Nov 29-30:**
1. Saturday evening: Run score update command
2. Sunday evening: Run score update command again
3. Visit league pages: Click "Recompute Scores"
4. Done! Winners determined.

---

**Documentation**: `/app/docs/API_FOOTBALL_USAGE_GUIDE.md`  
**Script Location**: `/app/backend/sports_data_client.py`  
**Test Script**: `/tmp/test_api_football.py`

---
**Last Updated**: November 25, 2025  
**Status**: Production Ready
