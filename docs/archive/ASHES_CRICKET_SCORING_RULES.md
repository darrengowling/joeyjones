# The Ashes 2025/26 - Cricket Scoring Rules

## ✅ Scoring Configuration (Already in Database)

The cricket scoring rules from the previous NZ vs England ODI series are stored in the `sports` collection and will automatically apply to all cricket competitions, including The Ashes.

### Base Scoring Rules (Per Player Per Match)

| Event | Points | Description |
|-------|--------|-------------|
| **Run** | 1 point | Every run scored by a batsman |
| **Wicket** | 20 points | Every wicket taken by a bowler |
| **Catch** | 10 points | Every catch held by a fielder |
| **Stumping** | 25 points | Every stumping by a wicketkeeper |
| **Run-out** | 20 points | Every run-out assisted/completed |

### Milestones

**Status**: Disabled (No milestone bonuses for this configuration)

---

## 📊 Example Scoring Calculations

### Example 1: Opening Batsman
**Player**: Usman Khawaja scores 85 runs, takes 1 catch
- Runs: 85 × 1 = **85 points**
- Catch: 1 × 10 = **10 points**
- **Total**: **95 points**

### Example 2: Fast Bowler  
**Player**: Mitchell Starc takes 4 wickets, 1 catch
- Wickets: 4 × 20 = **80 points**
- Catch: 1 × 10 = **10 points**
- **Total**: **90 points**

### Example 3: Wicketkeeper
**Player**: Alex Carey scores 45 runs, 3 stumpings, 2 catches
- Runs: 45 × 1 = **45 points**
- Stumpings: 3 × 25 = **75 points**
- Catches: 2 × 10 = **20 points**
- **Total**: **140 points**

### Example 4: All-rounder
**Player**: Ben Stokes scores 62 runs, 2 wickets, 1 run-out
- Runs: 62 × 1 = **62 points**
- Wickets: 2 × 20 = **40 points**
- Run-out: 1 × 20 = **20 points**
- **Total**: **122 points**

---

## 🎯 How Scoring Works in The Ashes Competition

1. **Commissioner creates Ashes league** with selected Australian and English players
2. **Managers bid** on players during auction (mix of nationalities allowed)
3. **After each Test match**:
   - Cricbuzz API fetches match scorecard
   - Each player's performance (runs, wickets, catches, etc.) is recorded
   - Points calculated using the rules above
   - Manager points = sum of all their players' points
4. **Leaderboard updates** after each match
5. **Winner**: Manager with highest total points after all 5 Test matches

---

## 💾 Database Schema

**Location**: `test_database.sports` collection

```json
{
  "key": "cricket",
  "scoringSchema": {
    "type": "perPlayerMatch",
    "rules": {
      "run": 1,
      "wicket": 20,
      "catch": 10,
      "stumping": 25,
      "runOut": 20
    },
    "milestones": {}
  }
}
```

**Status**: ✅ Already configured and verified in database
**Effective**: All cricket competitions automatically use these rules
**No action required**: Rules are ready for The Ashes

---

## 🏏 Ready for The Ashes!

- ✅ Scoring rules configured
- ✅ 30 Ashes players seeded (14 AUS + 16 ENG)
- ✅ Cricbuzz API integrated
- ✅ Score update functionality working

**Next**: Create The Ashes competition and start the auction!
