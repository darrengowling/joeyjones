# Cricket Scoring Settings - Updated Configuration

**Date**: 2025-10-25  
**Status**: ✅ **UPDATED**

---

## 📊 Updated Cricket Scoring Rules

### Base Rules (Per Player Per Match):
```json
{
  "run": 1,         // 1 point per run scored
  "wicket": 20,     // 20 points per wicket taken
  "catch": 10,      // 10 points per catch
  "stumping": 25,   // ✅ UPDATED: 25 points per stumping (was 10)
  "runOut": 20      // ✅ UPDATED: 20 points per run-out (was 10)
}
```

### Milestones:
```json
{
  "milestones": {}  // ✅ DISABLED: No milestone bonuses for this tournament
}
```

---

## 📝 Changes Made:

| Field | Old Value | New Value | Change |
|-------|-----------|-----------|--------|
| `stumping` | 10 points | **25 points** | +15 points |
| `runOut` | 10 points | **20 points** | +10 points |
| `run` | 1 point | 1 point | No change |
| `wicket` | 20 points | 20 points | No change |
| `catch` | 10 points | 10 points | No change |
| Milestones | Empty | Empty | No change |

---

## 🎯 Impact:

**Wicket-Keepers**: More valuable (stumping worth 2.5x catch)  
**Fielding Teams**: Run-outs now worth 2x catch  
**Consistency**: Milestone bonuses disabled for tournament simplicity

---

## 💾 Database Update:

```javascript
// MongoDB Update Applied:
db.sports.updateOne(
  { key: 'cricket' },
  { $set: { 
    'scoringSchema.rules.stumping': 25,
    'scoringSchema.rules.runOut': 20
  }}
)

// Result: ✅ Modified 1 document
```

---

## 🧪 Example Calculations:

**Example 1: Batsman with 75 runs, 1 catch**
- Runs: 75 × 1 = 75 points
- Catch: 1 × 10 = 10 points
- **Total**: 85 points

**Example 2: Bowler with 3 wickets, 2 catches**
- Wickets: 3 × 20 = 60 points
- Catches: 2 × 10 = 20 points
- **Total**: 80 points

**Example 3: Wicket-Keeper with 30 runs, 2 stumpings, 1 catch**
- Runs: 30 × 1 = 30 points
- Stumpings: 2 × 25 = 50 points ← More valuable!
- Catch: 1 × 10 = 10 points
- **Total**: 90 points

**Example 4: All-rounder with 45 runs, 2 wickets, 1 run-out**
- Runs: 45 × 1 = 45 points
- Wickets: 2 × 20 = 40 points
- Run-out: 1 × 20 = 20 points ← Higher value!
- **Total**: 105 points

---

## ✅ Verification:

```bash
# Check updated settings:
mongosh test_database --eval "db.sports.findOne({key: 'cricket'}, {scoringSchema: 1})"

# Expected output:
{
  scoringSchema: {
    type: 'perPlayerMatch',
    rules: { 
      run: 1, 
      wicket: 20, 
      catch: 10, 
      stumping: 25,   // ✅ Updated
      runOut: 20      // ✅ Updated
    },
    milestones: {}    // ✅ Disabled
  }
}
```

---

## 📋 Applied To:

- **Database**: `test_database.sports` collection
- **Document**: `{key: 'cricket'}`
- **Effective**: Immediately for all new score uploads
- **Existing Scores**: Not retroactively changed (would need recompute if desired)

---

## 🔄 Next Steps:

1. **New Score Uploads**: Will automatically use new values (25 for stumping, 20 for run-out)
2. **Existing Leaderboards**: Current scores remain as calculated
3. **Recompute (Optional)**: If you want to recalculate existing scores with new values, run:
   ```bash
   # Re-upload match CSVs to recalculate with new scoring
   ```

---

**Configuration Updated**: 2025-10-25  
**Status**: ✅ Ready for tournament scoring
