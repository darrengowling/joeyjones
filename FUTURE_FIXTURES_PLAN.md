# Future Fixtures - How The Fix Works Going Forward

## ✅ YES - The Fix Will Work For Future Fixtures

The fix is **date-agnostic** and will work for any future date, not just Nov 29-30.

---

## 🔄 How It Works For Any Date

### The Fix (Date Parameter Only):
```python
# Works for ANY date:
params = {"date": "2025-12-07"}  # Next week
params = {"date": "2025-12-14"}  # Two weeks from now
params = {"date": "2026-01-01"}  # Next year
```

### API-Football Free Tier Window:
- **3-day rolling window** (current behavior we observed)
- Always includes: Today, Tomorrow, Day After
- Example on Dec 5: Can access Dec 5, 6, 7
- Example on Dec 10: Can access Dec 10, 11, 12

**Your update feature will work as long as:**
- You update scores within this 3-day window
- Commissioner clicks "Update Scores" on match day or 1-2 days after

---

## 📥 How Fixtures Get External IDs (Current Process)

### Step 1: Seed Teams With API-Football IDs
**Script:** `/app/scripts/seed_epl_teams.py`

```python
EPL_TEAMS = [
    {"name": "Arsenal", "api_football_id": 42},
    {"name": "Brentford", "api_football_id": 55},
    {"name": "Chelsea", "api_football_id": 49},
    # ... 20 teams total
]

# Each team stored in assets collection:
{
  "name": "Brentford",
  "externalId": "55",          # ✅ API-Football team ID
  "apiFootballId": 55,         # ✅ Also stored separately
  "sportKey": "football"
}
```

### Step 2: Create Fixtures From Teams
**Script:** `/app/scripts/seed_epl_fixtures.py`

```python
FIXTURES = [
    {"home": "Brentford", "away": "Burnley", "date": "2025-11-29T15:00:00Z"},
    # ...
]

# Lookup teams and copy external IDs:
home_team = db.assets.find_one({"name": "Brentford"})
away_team = db.assets.find_one({"name": "Burnley"})

fixture = {
    "homeTeam": "Brentford",
    "awayTeam": "Burnley",
    "homeExternalId": home_team["externalId"],  # ✅ Copied from asset: "55"
    "awayExternalId": away_team["externalId"],  # ✅ Copied from asset: "44"
    "matchDate": "2025-11-29T15:00:00Z"
}
```

### Step 3: Update Scores Matches By External IDs
**Function:** `update_fixtures_from_api()` in `sports_data_client.py`

```python
# Match fixture with API response:
DB_fixture: homeExternalId="55", awayExternalId="44"
API_fixture: teams.home.id=55, teams.away.id=44
✅ MATCH! Update this fixture
```

---

## 🔮 For Future Match Days - The Process

### Option A: Manual Fixture Creation (Current Method)

**When you want to add fixtures for Dec 7, 2025:**

1. **Update the seed script** `/app/scripts/seed_epl_fixtures.py`:
   ```python
   FIXTURES = [
       {"home": "Arsenal", "away": "Chelsea", "date": "2025-12-07T15:00:00Z"},
       {"home": "Liverpool", "away": "Manchester City", "date": "2025-12-07T15:00:00Z"},
       # ... etc
   ]
   ```

2. **Run the seed script:**
   ```bash
   cd /app/scripts
   python3 seed_epl_fixtures_correct_db.py
   ```

3. **External IDs are automatically copied** from assets collection

4. **Update scores on match day:**
   - Click "Update Match Scores" button
   - Feature fetches API-Football data for Dec 7
   - Matches by external IDs
   - Updates scores ✅

### Option B: Automated Fixture Import (Recommended for Production)

**Create an API endpoint to import fixtures from API-Football:**

```python
@api_router.post("/fixtures/import")
async def import_fixtures_from_api(date: str, league_id: int = 39):
    """
    Import upcoming fixtures from API-Football for a specific date
    This ensures external IDs are always correct
    """
    client = APIFootballClient()
    
    # Fetch fixtures from API
    api_fixtures = await client.get_fixtures_by_date(date, league_id)
    
    for api_fixture in api_fixtures:
        # Get teams from our assets by external ID
        home_ext_id = str(api_fixture["teams"]["home"]["id"])
        away_ext_id = str(api_fixture["teams"]["away"]["id"])
        
        home_team = await db.assets.find_one({
            "externalId": home_ext_id,
            "sportKey": "football"
        })
        
        away_team = await db.assets.find_one({
            "externalId": away_ext_id,
            "sportKey": "football"
        })
        
        if not home_team or not away_team:
            continue  # Skip if teams not in our system
        
        # Create fixture
        fixture = {
            "id": str(uuid4()),
            "homeTeam": home_team["name"],
            "awayTeam": away_team["name"],
            "homeTeamId": home_team["id"],
            "awayTeamId": away_team["id"],
            "homeExternalId": home_ext_id,  # ✅ From API-Football
            "awayExternalId": away_ext_id,  # ✅ From API-Football
            "matchDate": api_fixture["fixture"]["date"],
            "status": "scheduled",
            "sportKey": "football"
        }
        
        await db.fixtures.insert_one(fixture)
    
    return {"imported": len(api_fixtures)}
```

**Benefits:**
- No manual fixture entry
- External IDs guaranteed correct
- Works for any league/competition
- Can import weeks in advance

---

## 🛡️ How To Ensure External IDs Match (Quality Control)

### Rule #1: Single Source of Truth
**Assets collection is the master source for external IDs**

```python
# ✅ ALWAYS copy from assets:
home_team = await db.assets.find_one({"name": "Brentford"})
fixture["homeExternalId"] = home_team["externalId"]

# ❌ NEVER hardcode:
fixture["homeExternalId"] = "55"  # Don't do this
```

### Rule #2: Validate Teams Have External IDs
**Before creating fixtures, verify assets have external IDs:**

```python
async def validate_team_has_external_id(team_name: str) -> bool:
    team = await db.assets.find_one({"name": team_name, "sportKey": "football"})
    if not team:
        print(f"⚠️  Team not found: {team_name}")
        return False
    if not team.get("externalId"):
        print(f"⚠️  Team missing externalId: {team_name}")
        return False
    return True
```

### Rule #3: Seed Script Checklist
**When running `/app/scripts/seed_epl_teams.py`:**

1. ✅ Each team has correct `api_football_id` from API-Football docs
2. ✅ Team names match exactly (e.g., "Brighton & Hove Albion" not "Brighton")
3. ✅ Run team seed BEFORE fixture seed
4. ✅ Verify with: `db.assets.find({"externalId": {$exists: false}})`

### Rule #4: API-Football Team ID Reference
**Keep this reference updated:**

Source: https://www.api-football.com/documentation-v3#tag/Teams

```python
# Premier League 2024-2025 Team IDs (verified against API)
PREMIER_LEAGUE_TEAMS = {
    "Arsenal": 42,
    "Aston Villa": 66,
    "Brentford": 55,
    "Brighton & Hove Albion": 51,
    "Chelsea": 49,
    # ... etc
}
```

---

## 🔄 Ongoing Maintenance

### For Each New Season:
1. **Verify team IDs** (teams promoted/relegated may have different IDs)
2. **Update seed script** `/app/scripts/seed_epl_teams.py`
3. **Re-run team seed** to update assets
4. **Test with one fixture** before importing full schedule

### For Each Match Week:
1. **Update fixture seed script** with new dates/matchups
2. **Run fixture seed** (or use automated import endpoint)
3. **Verify fixtures created** with correct external IDs
4. **Update scores** within 3-day window after matches

---

## 📊 Verification Checklist

**After creating new fixtures, always verify:**

```bash
# Check fixtures have external IDs:
db.fixtures.find({
  "sportKey": "football",
  "homeExternalId": {$exists: false}
})
# Should return: 0 documents

# Verify external IDs match assets:
# (Run this Python check)
for fixture in fixtures:
    home_team = db.assets.find_one({"id": fixture["homeTeamId"]})
    if home_team["externalId"] != fixture["homeExternalId"]:
        print(f"❌ MISMATCH: {fixture['homeTeam']}")
```

---

## ⚠️ Important Limitations To Remember

### API-Football Free Tier:
- ✅ Can access fixtures 3 days into future
- ✅ Can update scores day-of or 1-2 days after
- ❌ Cannot update scores for matches >3 days old
- ❌ Cannot import fixtures >3 days into future

### Workaround:
- Import fixtures manually via seed scripts
- Use API-Football only for score updates (not fixture discovery)
- Update scores promptly after matches finish

---

## 🎯 Recommendations For Production

### Short Term (Pilot):
1. ✅ Use current seed scripts for fixture creation
2. ✅ Use fixed API-Football integration for score updates
3. ✅ Manually import fixtures for each match week

### Medium Term:
1. 🔄 Create automated fixture import endpoint
2. 🔄 Add admin UI for importing fixtures
3. 🔄 Add validation warnings for missing external IDs

### Long Term:
1. 🔮 Upgrade to paid API-Football plan
2. 🔮 Enable automatic fixture imports weeks in advance
3. 🔮 Add automated score updates via scheduled jobs

---

## ✅ SUMMARY

**Will the fix work for future fixtures?**
✅ YES - works for any date within API-Football's 3-day window

**How do we ensure external IDs match?**
✅ Copy from assets collection (single source of truth)
✅ Seed teams first with correct API-Football IDs
✅ Validate before creating fixtures

**What's the process going forward?**
1. Keep `/app/scripts/seed_epl_teams.py` updated with correct team IDs
2. Create fixtures by copying external IDs from assets
3. Update scores within 3-day window
4. (Optional) Build automated import endpoint for production

**Key principle:** 
Assets collection → Fixtures inherit external IDs → API-Football matches by external IDs → Scores update successfully
