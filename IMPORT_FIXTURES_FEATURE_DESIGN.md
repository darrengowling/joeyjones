# "Import Fixtures" Button - Feature Design

## 🎯 Feature Overview

Add an "Import Fixtures" button next to "Update Match Scores" in the Fixtures tab that automatically fetches upcoming fixtures from API-Football and creates them in the database.

---

## 🖼️ UI Design

### Location
**Competition Dashboard → Fixtures Tab**

```
┌─────────────────────────────────────────────────────────┐
│ Fixtures                                                 │
│                                                          │
│ [Import Fixtures] [Update Match Scores]                 │
│                                                          │
│ Nov 29, 2025                                            │
│ 03:00 PM  Brentford vs Burnley          [Scheduled]    │
│ ...                                                      │
└─────────────────────────────────────────────────────────┘
```

### Button Behavior

**Click "Import Fixtures"** →

```
┌─────────────────────────────────────────────┐
│ Import Fixtures from API-Football            │
├─────────────────────────────────────────────┤
│                                              │
│ Date Range:                                  │
│ From: [2025-12-07] To: [2025-12-14]         │
│                                              │
│ League: [English Premier League ▼]          │
│                                              │
│ ⚠️ Note: Free tier only accesses current    │
│    3-day window. Manual dates may not       │
│    return fixtures.                          │
│                                              │
│        [Cancel]  [Import Fixtures]           │
└─────────────────────────────────────────────┘
```

**After clicking "Import Fixtures":**

```
┌─────────────────────────────────────────────┐
│ ✅ Import Successful                         │
├─────────────────────────────────────────────┤
│                                              │
│ Imported 8 fixtures for Dec 7-14, 2025      │
│                                              │
│ ✓ Arsenal vs Chelsea                         │
│ ✓ Liverpool vs Manchester United             │
│ ✓ Tottenham vs Brighton                      │
│ ...                                          │
│                                              │
│ ⚠️ 2 fixtures skipped (teams not in system) │
│                                              │
│             [Close]                          │
└─────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### Backend Flow

```
1. User clicks "Import Fixtures"
   ↓
2. Modal opens with date range picker
   ↓
3. User selects: From=Dec 7, To=Dec 14
   ↓
4. POST /api/leagues/{leagueId}/fixtures/import
   {
     "startDate": "2025-12-07",
     "endDate": "2025-12-14",
     "leagueId": 39  // Premier League
   }
   ↓
5. Backend iterates through each date (Dec 7, 8, 9...14)
   ↓
6. For each date:
   - Call API-Football: GET /fixtures?date=2025-12-07
   - Filter for Premier League (league_id=39)
   - For each fixture:
     * Match home/away teams with assets by externalId
     * If both teams exist in our assets → Create fixture
     * If team missing → Skip (log warning)
   ↓
7. Return summary:
   {
     "imported": 8,
     "skipped": 2,
     "details": [...]
   }
```

### Database Operations

```python
# For each API fixture:
home_ext_id = str(api_fixture["teams"]["home"]["id"])  # e.g., "42"
away_ext_id = str(api_fixture["teams"]["away"]["id"])  # e.g., "49"

# Find teams in our assets
home_team = await db.assets.find_one({
    "externalId": home_ext_id,
    "sportKey": "football"
})

away_team = await db.assets.find_one({
    "externalId": away_ext_id,
    "sportKey": "football"
})

if home_team and away_team:
    # Create fixture
    fixture = {
        "id": str(uuid4()),
        "leagueId": league_id,  # Associate with competition
        "homeTeam": home_team["name"],
        "awayTeam": away_team["name"],
        "homeTeamId": home_team["id"],
        "awayTeamId": away_team["id"],
        "homeExternalId": home_ext_id,  # ✅ From API-Football
        "awayExternalId": away_ext_id,  # ✅ From API-Football
        "matchDate": api_fixture["fixture"]["date"],
        "status": "scheduled",
        "sportKey": "football",
        "competition": league_obj["name"]
    }
    await db.fixtures.insert_one(fixture)
```

---

## 🎨 Implementation Details

### Backend Endpoint

**Location:** `/app/backend/server.py`

```python
@api_router.post("/leagues/{league_id}/fixtures/import")
async def import_fixtures_for_league(
    league_id: str,
    start_date: str,  # YYYY-MM-DD
    end_date: str,    # YYYY-MM-DD
    api_league_id: int = 39  # Default: Premier League
):
    """
    Import fixtures from API-Football for date range
    Creates fixtures only for teams that exist in our assets collection
    """
    from sports_data_client import APIFootballClient
    from datetime import datetime, timedelta
    
    # Validate league exists
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    client = APIFootballClient()
    
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    imported_fixtures = []
    skipped_fixtures = []
    
    # Iterate through date range
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Fetch fixtures for this date
        api_fixtures = await client.get_fixtures_by_date(date_str, api_league_id)
        
        for api_fixture in api_fixtures:
            # Extract team IDs
            home_ext_id = str(api_fixture["teams"]["home"]["id"])
            away_ext_id = str(api_fixture["teams"]["away"]["id"])
            
            # Find teams in our assets
            home_team = await db.assets.find_one({
                "externalId": home_ext_id,
                "sportKey": "football"
            }, {"_id": 0})
            
            away_team = await db.assets.find_one({
                "externalId": away_ext_id,
                "sportKey": "football"
            }, {"_id": 0})
            
            if not home_team or not away_team:
                # Skip if teams not in our system
                skipped_fixtures.append({
                    "home": api_fixture["teams"]["home"]["name"],
                    "away": api_fixture["teams"]["away"]["name"],
                    "reason": "Team not in assets collection"
                })
                continue
            
            # Check if fixture already exists
            existing = await db.fixtures.find_one({
                "homeExternalId": home_ext_id,
                "awayExternalId": away_ext_id,
                "matchDate": api_fixture["fixture"]["date"]
            })
            
            if existing:
                skipped_fixtures.append({
                    "home": home_team["name"],
                    "away": away_team["name"],
                    "reason": "Already exists"
                })
                continue
            
            # Create fixture
            fixture = {
                "id": str(uuid4()),
                "leagueId": league_id,
                "homeTeam": home_team["name"],
                "awayTeam": away_team["name"],
                "homeTeamId": home_team["id"],
                "awayTeamId": away_team["id"],
                "homeExternalId": home_ext_id,
                "awayExternalId": away_ext_id,
                "matchDate": api_fixture["fixture"]["date"],
                "status": "scheduled",
                "goalsHome": None,
                "goalsAway": None,
                "winner": None,
                "sportKey": "football",
                "competition": league["name"],
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            await db.fixtures.insert_one(fixture)
            imported_fixtures.append({
                "home": home_team["name"],
                "away": away_team["name"],
                "date": fixture["matchDate"]
            })
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return {
        "status": "completed",
        "imported": len(imported_fixtures),
        "skipped": len(skipped_fixtures),
        "fixtures": imported_fixtures,
        "skipped_details": skipped_fixtures,
        "api_requests_used": (end - start).days + 1,
        "api_requests_remaining": client.get_requests_remaining()
    }
```

---

### Frontend Implementation

**Location:** `/app/frontend/src/pages/CompetitionDashboard.js`

```javascript
const [importModalOpen, setImportModalOpen] = useState(false);
const [importDateRange, setImportDateRange] = useState({
  startDate: new Date().toISOString().split('T')[0],
  endDate: new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0]
});

const handleImportFixtures = async () => {
  try {
    setLoading(true);
    const response = await fetch(
      `${API_URL}/api/leagues/${leagueId}/fixtures/import`,
      {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          start_date: importDateRange.startDate,
          end_date: importDateRange.endDate,
          api_league_id: 39  // Premier League
        })
      }
    );
    
    const result = await response.json();
    
    if (response.ok) {
      toast.success(
        `✅ Imported ${result.imported} fixtures. ${result.skipped} skipped.`
      );
      // Refresh fixtures list
      fetchFixtures();
      setImportModalOpen(false);
    } else {
      toast.error(result.detail || 'Failed to import fixtures');
    }
  } catch (error) {
    toast.error('Error importing fixtures');
  } finally {
    setLoading(false);
  }
};

// In the render:
<div className="flex gap-2">
  <button 
    onClick={() => setImportModalOpen(true)}
    className="btn-primary"
  >
    Import Fixtures
  </button>
  
  <button 
    onClick={handleUpdateScores}
    className="btn-secondary"
  >
    Update Match Scores
  </button>
</div>
```

---

## ⚠️ API-Football Free Tier Limitations

### Problem: 3-Day Rolling Window

```
Today: Dec 5, 2025
API can access: Dec 5, 6, 7 (3-day window)

User wants to import: Dec 7-14
✅ Dec 7: Can fetch
❌ Dec 8-14: Will return empty (outside window)
```

### Solutions

**Option 1: Smart Date Range Validation**
```javascript
// Frontend warns user:
if (endDate > today + 3 days) {
  showWarning(
    "Free tier only accesses 3-day window. " +
    "Fixtures beyond [date] may not be available."
  );
}
```

**Option 2: Manual Entry Fallback**
```
Import from API (gets Dec 5-7)
+ Manual entry for Dec 8-14 (use seed scripts)
= Complete fixture list
```

**Option 3: Allow Future Dates (User Awareness)**
```
Let user try any date range
Show clear messaging:
  "Attempted Dec 7-14"
  "✅ Imported 5 fixtures (Dec 7-9)"
  "⚠️ No fixtures found for Dec 10-14 (outside API window)"
```

---

## 🎯 Feature Benefits

### ✅ Advantages

1. **Eliminates Manual Work**
   - No more editing seed scripts
   - No more running Python scripts manually
   - One-click fixture creation

2. **Guarantees Correct External IDs**
   - IDs come directly from API-Football
   - No risk of typos or mismatches
   - Automatic team matching

3. **Prevents Duplicates**
   - Checks if fixture already exists
   - Won't create duplicate fixtures

4. **User-Friendly**
   - Commissioners can do it themselves
   - No technical knowledge required
   - Immediate feedback

5. **Flexible**
   - Can import any date range
   - Can import for multiple competitions
   - Can re-import if needed

### ⚠️ Limitations

1. **API Window Restriction**
   - Free tier: Only 3-day window accessible
   - Can't import far future fixtures
   - Must import close to match dates

2. **Team Availability**
   - Only imports fixtures for teams in assets collection
   - If new team promoted, must seed that team first

3. **API Quota Usage**
   - Uses 1 API call per day in date range
   - e.g., 7-day range = 7 API calls
   - Monitor quota usage (100/day limit)

---

## 🧪 Testing Plan

### Test Cases

**Test 1: Import Within 3-Day Window**
```
Date range: Today to Today+2
Expected: All fixtures imported successfully
```

**Test 2: Import Outside Window**
```
Date range: Today+5 to Today+10
Expected: No fixtures found (graceful handling)
```

**Test 3: Team Not In Assets**
```
Fixture: Ipswich vs Southampton (newly promoted teams)
Expected: Skipped with clear reason
```

**Test 4: Duplicate Prevention**
```
Import same date range twice
Expected: Second import skips existing fixtures
```

**Test 5: API Quota Exhaustion**
```
Import when at 100/100 requests
Expected: Error message, no partial imports
```

---

## 📊 Effort Estimate

### Backend
- New endpoint: 1-2 hours
- Error handling: 30 mins
- Testing: 1 hour
**Total: 2-3 hours**

### Frontend
- Import modal UI: 1 hour
- API integration: 30 mins
- Success/error handling: 30 mins
**Total: 2 hours**

### Testing
- Manual testing: 1 hour
- Edge cases: 1 hour
**Total: 2 hours**

**Overall: 6-7 hours**

---

## 🚀 Recommendation

**Should we implement this?**

**YES - with caveats:**

✅ **Implement for pilot** if you want to eliminate manual seed scripts
✅ **Implement with clear messaging** about 3-day window limitation
✅ **Keep seed scripts as backup** for long-range planning

**OR**

⏸️ **Wait until after pilot** if current seed script process is working fine
⏸️ **Upgrade API plan first** to remove 3-day limitation
⏸️ **Then implement** as a premium feature

---

## 🎯 My Recommendation

**For your pilot (150 users):**
- ⏸️ **Hold off on this feature** for now
- ✅ **Use current seed scripts** (they work, low risk)
- ✅ **Implement the score update fix** (critical for pilot)
- 🔮 **Add import feature post-pilot** once you have user feedback

**Why wait:**
1. Seed scripts are working fine
2. One more feature = one more risk
3. Pilot is imminent - minimize changes
4. Can add this feature during pilot if needed

---

## Summary

**Can we do it?** YES - totally feasible  
**Should we do it now?** DEBATABLE - depends on priorities  
**Effort required?** 6-7 hours  
**Risk level?** Medium (new feature, untested)  

**Your call - what do you think?**
