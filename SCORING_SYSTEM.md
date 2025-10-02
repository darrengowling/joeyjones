# Scoring System - Friends of Pifa

## Overview
The scoring system fetches real UEFA Champions League match results from OpenFootball and calculates points for clubs owned by league participants.

## Scoring Rules

### Points Calculation
Each club earns points based on their real Champions League performance:

- **Win**: 3 points
- **Draw**: 1 point  
- **Goal Scored**: 1 point per goal

**Example:**
- Bayern Munich wins 9-2: **12 points** (3 for win + 9 for goals)
- Real Madrid wins 3-1: **6 points** (3 for win + 3 for goals)
- PSV draws 1-1: **2 points** (1 for draw + 1 for goal)

### Standings Tiebreakers
1. Total Points (descending)
2. Goal Difference (descending)
3. Goals Scored (descending)

## Data Source

### OpenFootball
We use [OpenFootball](https://github.com/openfootball/champions-league) - an open data project with UEFA Champions League match results.

**Data URL:**
```
https://raw.githubusercontent.com/openfootball/champions-league/master/2024-25/cl.json
```

### Mock Data Fallback
If OpenFootball is unavailable, the system uses mock data with 14 sample matches from the 2024/25 season including:
- Bayern Munich 9-2 Dinamo Zagreb
- Real Madrid 3-1 VfB Stuttgart
- Liverpool 3-1 AC Milan
- Arsenal 2-0 Paris Saint-Germain
- Barcelona 5-0 Young Boys
- And more...

## Database Schema

### LeaguePoints Collection
```javascript
{
  id: "uuid",
  leagueId: "uuid",          // Which league this is for
  clubId: "uuid",             // Which club
  clubName: "string",         // Club name for display
  wins: 0,                    // Number of wins
  draws: 0,                   // Number of draws
  losses: 0,                  // Number of losses
  goalsScored: 0,             // Total goals scored
  goalsConceded: 0,           // Total goals conceded
  totalPoints: 0,             // Calculated total points
  lastUpdated: "datetime"     // When scores were last computed
}
```

## API Endpoints

### POST /api/leagues/:id/score/recompute
Recompute scores for all clubs in a league based on latest Champions League results.

**Request:**
```bash
curl -X POST http://localhost:8001/api/leagues/{league_id}/score/recompute
```

**Response:**
```json
{
  "message": "Scores recomputed successfully",
  "clubs_updated": 3,
  "total_matches_processed": 14
}
```

**Process:**
1. Fetches all participants in the league
2. Gets all clubs won by participants
3. Fetches Champions League match data from OpenFootball
4. Calculates points for each club
5. Updates LeaguePoints collection
6. Returns summary

### GET /api/leagues/:id/standings
Get current standings for a league, sorted by points.

**Request:**
```bash
curl http://localhost:8001/api/leagues/{league_id}/standings
```

**Response:**
```json
[
  {
    "id": "...",
    "leagueId": "...",
    "clubId": "...",
    "clubName": "Bayern Munich",
    "wins": 1,
    "draws": 0,
    "losses": 0,
    "goalsScored": 9,
    "goalsConceded": 2,
    "totalPoints": 12,
    "lastUpdated": "2025-10-02T18:38:23.655000"
  },
  {
    "id": "...",
    "leagueId": "...",
    "clubId": "...",
    "clubName": "Real Madrid",
    "wins": 1,
    "draws": 0,
    "losses": 0,
    "goalsScored": 3,
    "goalsConceded": 1,
    "totalPoints": 6,
    "lastUpdated": "2025-10-02T18:38:23.643000"
  }
]
```

## Club Seeding

### Seed Script
Run the seeding script to populate clubs from OpenFootball/UEFA data:

```bash
cd /app/backend
python3 seed_openfootball_clubs.py
```

**What it does:**
1. Clears existing clubs
2. Seeds 36 UEFA Champions League 2024/25 clubs
3. Shows breakdown by country

**Clubs Included (36 total):**
- 🇩🇪 Germany: 5 clubs (Bayern, Leverkusen, Dortmund, Stuttgart, Leipzig)
- 🇮🇹 Italy: 5 clubs (Inter, Milan, Juventus, Atalanta, Bologna)
- 🇪🇸 Spain: 4 clubs (Real Madrid, Barcelona, Atlético, Girona)
- 🇬🇧 England: 4 clubs (Man City, Arsenal, Liverpool, Aston Villa)
- 🇫🇷 France: 4 clubs (PSG, Monaco, Brest, Lille)
- 🇵🇹 Portugal: 3 clubs (Sporting, Benfica, Porto)
- 🇳🇱 Netherlands: 2 clubs (PSV, Feyenoord)
- Plus 9 more clubs from Belgium, Scotland, Austria, Czech Republic, Croatia, Switzerland, Serbia, Ukraine, Slovakia

## Frontend Integration

### League Detail Page
**Standings Table:**
- Shows all clubs in the league with their stats
- Top 3 positions highlighted in green
- Displays: Rank, Club, W, D, L, GF, GA, GD, Points
- Real-time data from Champions League results

**Recompute Button:**
- Visible only to league commissioner
- Updates scores based on latest CL results
- Shows loading state while computing
- Refreshes standings automatically

**Scoring Info:**
- Legend explaining abbreviations
- Scoring rules displayed
- Top 3 visual indicator

## Usage Flow

### 1. Create League & Auction
```bash
# Create league
# Start auction
# Managers bid on clubs
# Winners get clubs assigned to clubsWon[]
```

### 2. Compute Scores
**Option A - Via UI:**
1. Navigate to league detail page
2. Commissioner clicks "🔄 Recompute Scores"
3. System fetches CL results and calculates points
4. Standings table updates automatically

**Option B - Via API:**
```bash
curl -X POST http://localhost:8001/api/leagues/{league_id}/score/recompute
```

### 3. View Standings
**Via UI:**
- League detail page shows standings table
- Updates automatically after recompute

**Via API:**
```bash
curl http://localhost:8001/api/leagues/{league_id}/standings
```

## Scoring Logic

### Match Processing
For each club, the system:
1. Finds all CL matches where club played
2. Determines if club was team1 or team2
3. Checks match result (win/draw/loss)
4. Counts goals scored and conceded
5. Calculates points: (wins × 3) + (draws × 1) + (goals scored × 1)

### Example Calculation
**Bayern Munich vs Dinamo Zagreb: 9-2**

For Bayern Munich:
- Result: Win → 3 points
- Goals scored: 9 → 9 points
- **Total: 12 points**

For Dinamo Zagreb:
- Result: Loss → 0 points
- Goals scored: 2 → 2 points
- **Total: 2 points**

## Cron/Manual Trigger

### Current Implementation
- **Manual Trigger**: Commissioner clicks "Recompute Scores" button
- **API Trigger**: POST to `/api/leagues/:id/score/recompute`

### Future: Automated Cron
To add automated scoring updates:

**Option 1 - Python APScheduler:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def auto_recompute_all_leagues():
    leagues = await db.leagues.find({"status": "active"}).to_list(100)
    for league in leagues:
        await recompute_league_scores(db, league["id"])

# Run daily at 2 AM
scheduler.add_job(auto_recompute_all_leagues, 'cron', hour=2)
scheduler.start()
```

**Option 2 - External Cron:**
```bash
# Add to crontab
0 2 * * * curl -X POST http://localhost:8001/api/leagues/{league_id}/score/recompute
```

## Testing

### Test with Mock Data
```bash
# 1. Create league and participants
# 2. Assign clubs to participants (Bayern, Real Madrid, Liverpool)
# 3. Recompute scores

curl -X POST http://localhost:8001/api/leagues/test-league/score/recompute

# Expected results:
# - Bayern Munich: 12 points (1W, 9GF)
# - Real Madrid: 6 points (1W, 3GF)
# - Liverpool: 6 points (1W, 3GF)
```

### Full Integration Test
See `/app/SCORING_SYSTEM.md` script section for complete test flow.

## Benefits

1. **Real Data**: Uses actual Champions League results
2. **Automated**: Easy one-click score updates
3. **Transparent**: Clear scoring rules displayed to users
4. **Fair**: Based on real performance, not random
5. **Engaging**: Connects fantasy league to real football
6. **Competitive**: Clear standings and rankings

## Technical Details

### Dependencies
- `aiohttp`: For async HTTP requests to OpenFootball
- `motor`: For MongoDB async operations

### Performance
- Fetches ~14-50 matches per recompute
- Processes in < 2 seconds
- Caches results in database
- Minimal API calls (one per recompute)

### Error Handling
- Falls back to mock data if OpenFootball unavailable
- Returns clear error messages
- Logs all operations
- Graceful degradation

## Future Enhancements

1. **Real-time Updates**: WebSocket notifications when scores change
2. **Historical Tracking**: Track points over time
3. **Manager Leaderboard**: Aggregate points for all clubs owned by each manager
4. **Automated Cron**: Daily/weekly automatic score updates
5. **Bonus Points**: Additional rules (clean sheets, hat-tricks, etc.)
6. **Multiple Competitions**: Europa League, domestic leagues
7. **Player Points**: Individual player performance scoring
8. **Achievements**: Badges for milestones
9. **Predictions**: Manager predictions with bonus points

## Summary

The scoring system brings real-world Champions League performance into the Friends of Pifa fantasy league, creating an engaging and competitive experience based on actual match results. Commissioners can easily update scores, and all participants can view detailed standings with comprehensive statistics.
