# Commissioner Guide: Updating Match Scores
## Simple Two-Button Process

**For**: League Commissioners  
**When**: After matches complete (Nov 29-30, 2025)

---

## Quick Steps

### After Matches Finish

**Step 1: Update Match Scores**
1. Go to your league page
2. Scroll to "Match Fixtures" section
3. Click **"Update Match Scores"** button (green button, top right)
4. Wait for confirmation: "Updated X match results!"
5. Fixtures now show scores (e.g., "Manchester City 3 - 1 Leeds United")

**Step 2: Update League Standings**
1. Scroll down to "League Standings" section
2. Click **"Recompute Scores"** button (blue button, top right)
3. Wait for confirmation: "Scores recomputed successfully!"
4. Standings now updated with winners!

**Done!** Your league now has latest results and rankings.

---

## When to Update

### Saturday, Nov 29
**After 17:30 GMT** (when last Saturday match finishes):
- Click "Update Match Scores"
- View Saturday results
- Don't update standings yet (wait for Sunday)

### Sunday, Nov 30
**After 16:30 GMT** (when last Sunday match finishes):
- Click "Update Match Scores" again
- View Sunday results
- **Now click "Recompute Scores"** to determine winners!

---

## What Each Button Does

### "Update Match Scores" (Green Button)
- Fetches latest match results from API-FOOTBALL
- Updates fixtures with goals and winners
- Shows "FT" (Full Time) status for completed matches
- **Location**: Top right of "Match Fixtures" section

### "Recompute Scores" (Blue Button)
- Calculates points for each team:
  - Win: 3 points
  - Draw: 1 point
  - Loss: 0 points
  - Plus: Goals scored
- Updates league standings
- Shows winner at top of table
- **Location**: Top right of "League Standings" section

---

## What You'll See

### Before Update
```
Match Fixtures
├─ Upcoming Matches
│  ├─ Manchester City vs Leeds United (Sat, 29 Nov, 15:00)
│  └─ Chelsea vs Arsenal (Sun, 30 Nov, 16:30)
```

### After "Update Match Scores"
```
Match Fixtures
├─ Completed Matches
│  ├─ Manchester City 3 - 1 Leeds United [FT]
│  └─ Chelsea 2 - 2 Arsenal [FT]
```

### After "Recompute Scores"
```
League Standings
1. John's Team - 18 pts (3 wins, 9 goals)
2. Sarah's Team - 15 pts (2 wins, 1 draw, 7 goals)
3. Mike's Team - 12 pts (2 wins, 6 goals)
```

---

## Troubleshooting

### "No new match results available yet"
**Meaning**: Matches haven't been played yet, or results not available in API  
**Solution**: Wait 5-10 minutes after match ends, then try again

### "Failed to update scores"
**Possible causes**:
- Internet connection issue
- API temporarily unavailable
- Daily limit reached (100 updates per day - very unlikely)

**Solution**: 
1. Wait a few minutes
2. Refresh the page
3. Try clicking "Update Match Scores" again

### Fixtures show scores but standings don't update
**Solution**: You need to click **both** buttons:
1. "Update Match Scores" - fetches results
2. "Recompute Scores" - calculates standings

---

## Tips

✅ **Do:**
- Update after all matches complete (Sunday evening is best)
- Click "Update Match Scores" first, then "Recompute Scores"
- Refresh page if scores don't appear immediately

❌ **Don't:**
- Click repeatedly if it's working (be patient)
- Update in middle of matches (wait for all to finish)
- Worry about API limits (you're well within the free tier)

---

## Quick Reference

| Action | Button | Color | Location | When |
|--------|--------|-------|----------|------|
| Fetch match results | Update Match Scores | Green | Fixtures section | After matches end |
| Calculate standings | Recompute Scores | Blue | Standings section | After updating scores |

**Remember**: Green first (get scores), then Blue (calculate rankings)

---

## Need Help?

**Button not visible?**
- Only commissioners can see these buttons
- Make sure you're logged in as the league creator

**Still stuck?**
- Check the in-app Help Center (top right navigation)
- Contact support with your league name and issue

---

**Last Updated**: November 25, 2025  
**Ready for**: Nov 29-30, 2025 Tournament
