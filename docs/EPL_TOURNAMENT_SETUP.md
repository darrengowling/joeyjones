# EPL Tournament Setup - November 29-30, 2025
## Real-World Pilot Testing

**Date**: November 23, 2025  
**Status**: Ready for Testing

---

## Overview

EPL tournament configured for November 29-30, 2025 fixtures to support real-world pilot testing with actual match data.

---

## Teams Seeded (All 20 EPL Teams)

All teams include API-FOOTBALL team IDs for automated score updates:

1. Arsenal (ID: 42)
2. Aston Villa (ID: 66)
3. AFC Bournemouth (ID: 35)
4. Brentford (ID: 55)
5. Brighton & Hove Albion (ID: 51)
6. Burnley (ID: 44)
7. Chelsea (ID: 49)
8. Crystal Palace (ID: 52)
9. Everton (ID: 45)
10. Fulham (ID: 36)
11. Leeds United (ID: 63)
12. Liverpool (ID: 40)
13. Manchester City (ID: 50)
14. Manchester United (ID: 33)
15. Newcastle United (ID: 34)
16. Nottingham Forest (ID: 65)
17. Sunderland (ID: 71)
18. Tottenham Hotspur (ID: 47)
19. West Ham United (ID: 48)
20. Wolverhampton Wanderers (ID: 39)

---

## Fixtures (November 29-30, 2025)

### Saturday, November 29, 2025

**15:00 GMT**
- Brentford vs Burnley
- Manchester City vs Leeds United
- Sunderland vs AFC Bournemouth
- Everton vs Newcastle United

**17:30 GMT**
- Tottenham Hotspur vs Fulham

### Sunday, November 30, 2025

**14:00 GMT**
- Crystal Palace vs Manchester United
- Aston Villa vs Wolverhampton Wanderers
- Nottingham Forest vs Brighton & Hove Albion

**16:30 GMT**
- West Ham United vs Liverpool
- Chelsea vs Arsenal

**Total**: 10 fixtures across 2 days

---

## Scoring Rules

**Points System:**
- Win: 3 points
- Draw: 1 point
- Loss: 0 points
- Goals scored: Added to team total

**Example:**
- Team wins 2-1: 3 points + 2 goals = 5 total points for that match
- Team draws 1-1: 1 point + 1 goal = 2 total points
- Team loses 0-2: 0 points + 0 goals = 0 total points

---

## API-FOOTBALL Integration

### Setup Requirements

1. **Get API Key** (Free Tier - 100 requests/day)
   - Visit: https://www.api-football.com
   - Sign up for free account
   - Get API key from dashboard

2. **Configure Environment Variable**
   ```bash
   # Add to /app/backend/.env
   API_FOOTBALL_KEY=your_api_key_here
   ```

3. **Restart Backend**
   ```bash
   sudo supervisorctl restart backend
   ```

### API Endpoints

**Manual Score Update** (Recommended for Nov 29-30)
```bash
curl -X POST https://fix-roster-sync.preview.emergentagent.com/api/fixtures/update-scores \
  -H "Content-Type: application/json"
```

**Get All Fixtures**
```bash
curl https://fix-roster-sync.preview.emergentagent.com/api/fixtures?sport_key=football
```

**Get Fixtures by Date**
```bash
curl https://fix-roster-sync.preview.emergentagent.com/api/fixtures?sport_key=football&date=2025-11-29
```

**Get Specific Fixture**
```bash
curl https://fix-roster-sync.preview.emergentagent.com/api/fixtures/{fixture_id}
```

### Update Frequency Strategy

**For November 29-30 Testing:**
- Manual trigger before each match window
- Manual trigger at halftime (check live scores)
- Manual trigger at fulltime (final scores)
- **Total**: ~6 manual triggers over 2 days = 6 API requests (well within 100/day limit)

**Future Automation Options:**
- Scheduled job every 15 minutes during match days
- Webhook-based updates (if API supports)
- Admin dashboard with "Update Scores" button

---

## CSV Backup Option

CSV upload remains available as fallback if API is unavailable.

**CSV Format:**
```csv
fixture_id,home_team,away_team,match_date,status,goals_home,goals_away,winner
1,Brentford,Burnley,2025-11-29T15:00:00Z,finished,2,1,Brentford
```

**Upload via Existing Endpoint** (if needed):
```bash
POST /api/matches/upload-csv
```

---

## Commissioner Workflow

### Creating EPL Competition

1. **Navigate**: "Create Your Competition"
2. **Select Sport**: Football
3. **Competition Name**: e.g., "EPL Nov 29-30 Tournament"
4. **Configure Settings**:
   - Budget: £500M (default)
   - Manager slots: 2-8 participants
   - Club slots: 3-5 teams per manager
   - Timer: 30-60 seconds
   - Anti-snipe: 10 seconds

5. **Team Selection**:
   - All 20 EPL teams available
   - Select/deselect as needed
   - Commissioners can choose to include all 20 or subset

6. **Start Auction**: When all managers have joined

### Score Updates

**Manual Process (Recommended for Nov 29-30):**
1. Commissioner monitors match results
2. Uses admin panel to trigger score update
3. System fetches latest data from API-FOOTBALL
4. Leaderboards update automatically

**Automated Process (Future):**
- System checks scores every 15 minutes during match windows
- No manual intervention required
- Leaderboards update in real-time

---

## Testing Checklist

**Before Nov 29:**
- [ ] User creates API-FOOTBALL account
- [ ] Add API key to backend .env
- [ ] Restart backend
- [ ] Test manual score update endpoint
- [ ] Create test competition with EPL teams
- [ ] Run test auction with pilot users

**During Nov 29-30:**
- [ ] Trigger score updates 3x per day (pre-match, halftime, final)
- [ ] Monitor leaderboards for accurate updates
- [ ] Verify scoring: 3pts/win + goals scored
- [ ] Check API request quota (should use ~6 of 100 requests)

**After Nov 30:**
- [ ] Verify final standings
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan for automation if testing successful

---

## Rate Limiting Strategy

**Free Tier Limit**: 100 requests/day

**Nov 29-30 Usage Estimate:**
- 6 manual triggers × 1 request each = **6 requests total**
- **94 requests remaining** for other testing

**Best Practices:**
- Batch updates by date (1 request fetches all fixtures for that date)
- Avoid polling every minute
- Use manual triggers during pilot
- Monitor remaining requests via `/api/fixtures/stats` (if implemented)

---

## Troubleshooting

### Issue: "API_FOOTBALL_KEY not configured"
**Solution**: Add API key to `/app/backend/.env` and restart backend

### Issue: Score updates not working
**Check**:
1. API key is valid and not expired
2. Haven't exceeded 100 requests/day
3. Team external IDs match API-FOOTBALL team IDs
4. Fixtures have correct match dates

### Issue: Teams not appearing in competition creation
**Check**:
1. Teams seeded with `sportKey: "football"`
2. Backend restarted after seeding
3. Database connection working

---

## Files & Scripts

**Seeding Scripts:**
- `/app/scripts/seed_epl_teams.py` - Seeds all 20 EPL teams
- `/app/scripts/seed_epl_fixtures.py` - Seeds Nov 29-30 fixtures

**Integration Code:**
- `/app/backend/sports_data_client.py` - API-FOOTBALL client
- `/app/backend/server.py` - API endpoints for score updates

**Documentation:**
- `/app/docs/EPL_TOURNAMENT_SETUP.md` - This file
- API-FOOTBALL Playbook (provided separately)

---

## Next Steps

1. **User Action**: Create API-FOOTBALL account and get API key
2. **Configuration**: Add API key to backend .env
3. **Testing**: Create test competition with EPL teams
4. **Pilot**: Recruit testers for Nov 29-30 real-world tournament
5. **Monitoring**: Track score updates and user experience
6. **Iteration**: Automate if manual process works well

---

**Status**: ✅ Ready for API key configuration and testing  
**Timeline**: 6 days until Nov 29, 2025 tournament  
**Risk Level**: LOW - CSV fallback available if API issues arise

---
Generated: November 23, 2025
