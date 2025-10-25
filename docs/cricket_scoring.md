# Cricket Scoring System

## Overview

The Friends of Pifa cricket scoring system provides comprehensive points calculation for cricket player performances across matches. Commissioners can customize scoring rules per league while maintaining consistent calculation logic.

## Default Scoring Rules

### Base Points per Action
| Action | Points | Description |
|--------|--------|-------------|
| **Run** | 1 point | Per run scored |
| **Wicket** | 20 points | Per wicket taken (bowling) |
| **Catch** | 10 points | Per catch taken (fielding) |
| **Stumping** | 25 points | Per stumping (wicket-keeping) |
| **Run Out** | 20 points | Per run out (fielding/backing up) |

### Milestone Bonuses
| Milestone | Threshold | Bonus Points | Auto-Applied |
|-----------|-----------|--------------|--------------|
| **Half Century** | 50+ runs | +10 points | ❌ **DISABLED** |
| **Century** | 100+ runs | +25 points | ❌ **DISABLED** |
| **Five Wicket Haul** | 5+ wickets | +25 points | ❌ **DISABLED** |

**Note:** Milestone bonuses are **currently disabled** for NZ vs England series. Points are awarded purely for base actions (runs, wickets, catches, stumpings, run-outs).

## Sample CSV Format

### Required Columns
```csv
matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
```

### Example Data
```csv
matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
IPL_2024_M001,virat_kohli,89,0,1,0,0
IPL_2024_M001,ms_dhoni,45,0,2,3,1
IPL_2024_M001,jasprit_bumrah,12,4,0,0,0
IPL_2024_M001,rohit_sharma,67,0,1,0,0
IPL_2024_M001,ravindra_jadeja,23,2,1,0,1
IPL_2024_M002,virat_kohli,112,0,0,0,0
IPL_2024_M002,rashid_khan,8,5,1,0,0
```

### Points Calculation Examples

**Virat Kohli (Match 1): 89 runs, 1 catch**
- Runs: 89 × 1 = 89 points
- Catch: 1 × 10 = 10 points
- **Total: 99 points** *(no milestone bonuses)*

**MS Dhoni (Match 1): 45 runs, 2 catches, 3 stumpings, 1 run out**
- Runs: 45 × 1 = 45 points
- Catches: 2 × 10 = 20 points
- Stumpings: 3 × 25 = 75 points
- Run out: 1 × 20 = 20 points
- **Total: 160 points**

**Virat Kohli (Match 2): 112 runs**
- Runs: 112 × 1 = 112 points
- **Total: 112 points** *(no milestone bonuses)*

**Rashid Khan (Match 2): 8 runs, 5 wickets, 1 catch**
- Runs: 8 × 1 = 8 points
- Wickets: 5 × 20 = 100 points
- Catch: 1 × 10 = 10 points
- **Total: 118 points** *(no milestone bonuses)*

## Scoring Upload Process

### For Commissioners

1. **Prepare CSV Data**
   - Use the exact column headers: `matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts`
   - Ensure `playerExternalId` matches seeded cricket players (e.g., `virat_kohli`, `ms_dhoni`)
   - Use consistent `matchId` format (e.g., `IPL_2024_M001`)

2. **Upload via API** (UI coming soon)
   ```bash
   curl -X POST "https://your-domain/api/scoring/{leagueId}/ingest" \
        -F "file=@cricket_scores.csv"
   ```

3. **Verify Results**
   - Check leaderboard: `GET /api/scoring/{leagueId}/leaderboard`
   - Re-uploading same CSV gives identical totals (no double counting)

### Key Features
- **Upsert Logic**: Same match + player combination updates existing score
- **No Double Counting**: Re-uploading identical data maintains same totals
- **Multi-Match Support**: Points accumulate across different matches
- **Instant Updates**: Leaderboard updates immediately after upload

## Custom Scoring Overrides

Commissioners can customize scoring rules per league through the **Advanced: Scoring (Cricket)** panel in League Settings.

### Customizable Elements

**Base Points:**
- Adjust points per run, wicket, catch, stumping, run out
- Supports decimal values (e.g., 1.5 points per run)

**Milestone Controls:**
- Enable/disable individual milestones
- Customize bonus points for each milestone
- Thresholds are fixed (50 for half-century, 100 for century, 5 for five-wicket haul)

### Example Custom Configuration
```json
{
  "rules": {
    "run": 2,
    "wicket": 30,
    "catch": 15,
    "stumping": 20,
    "runOut": 12
  },
  "milestones": {
    "halfCentury": {
      "enabled": true,
      "threshold": 50,
      "points": 15
    },
    "century": {
      "enabled": false,
      "threshold": 100,
      "points": 35
    },
    "fiveWicketHaul": {
      "enabled": true,
      "threshold": 5,
      "points": 40
    }
  }
}
```

### Override Behavior
- **Priority**: League overrides take precedence over default sport rules
- **Immediate Effect**: Changes apply to next CSV upload
- **Previous Matches**: Existing scores remain unchanged
- **Reset to Default**: Delete overrides to restore default scoring

## Available Cricket Players

The system includes 20 seeded IPL players from various franchises:

| Player | Franchise | Role |
|--------|-----------|------|
| Virat Kohli | Royal Challengers Bangalore | Batsman |
| MS Dhoni | Chennai Super Kings | Wicket-keeper |
| Rohit Sharma | Mumbai Indians | Batsman |
| Jasprit Bumrah | Mumbai Indians | Bowler |
| KL Rahul | Lucknow Super Giants | Wicket-keeper |
| Hardik Pandya | Mumbai Indians | All-rounder |
| Ravindra Jadeja | Chennai Super Kings | All-rounder |
| Rashid Khan | Gujarat Titans | Bowler |
| David Warner | Delhi Capitals | Batsman |
| Andre Russell | Kolkata Knight Riders | All-rounder |
| *...and 10 more players* | | |

**Note:** Use the `externalId` values (e.g., `virat_kohli`, `ms_dhoni`) in your CSV files.

## API Reference

### Scoring Endpoints

**Upload Match Data** (Commissioner Only)
```http
POST /api/scoring/{leagueId}/ingest
Content-Type: multipart/form-data

file: cricket_scores.csv
```

**Get Leaderboard**
```http
GET /api/scoring/{leagueId}/leaderboard
```

**Update Scoring Rules** (Commissioner Only)
```http
PUT /api/leagues/{leagueId}/scoring-overrides
Content-Type: application/json

{
  "scoringOverrides": {
    "rules": { "run": 1, "wicket": 25, ... },
    "milestones": { ... }
  }
}
```

### League Management

**Create Cricket League**
```http
POST /api/leagues
Content-Type: application/json

{
  "name": "My Cricket League",
  "commissionerId": "user-id",
  "budget": 100000000,
  "minManagers": 2,
  "maxManagers": 8,
  "clubSlots": 5,
  "sportKey": "cricket"
}
```

**Get Cricket Players**
```http
GET /api/leagues/{leagueId}/assets
```

## Troubleshooting

### Common Issues

**"No assets available for cricket sport"**
- Ensure cricket players are seeded: Run `python scripts/seed_cricket_players.py`

**"Invalid or missing rule" error**
- Check all required rules are present: run, wicket, catch, stumping, runOut
- Ensure values are numeric (integers or decimals)

**"Player not found" in CSV**
- Use correct `playerExternalId` values from seeded players
- Check spelling: `virat_kohli` not `Virat Kohli`

**Incorrect point calculations**
- Verify milestone thresholds: 50 (half-century), 100 (century), 5 (five-wicket haul)
- Remember bonuses are cumulative for runs-based milestones

### Support

For technical issues or questions:
1. Check this documentation first
2. Verify your CSV format matches the examples
3. Test with small datasets before full match uploads
4. Contact your system administrator for database-level issues

---

*Last updated: November 2024*
*Version: 1.0*