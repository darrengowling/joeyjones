# Adding New Competitions - Complete Guide

## ✅ Current Status

**Verified Competitions:**
- ✅ **UEFA Champions League** - 36 teams, all IDs verified against Football-Data.org API
- ✅ **English Premier League** - 20 teams, all IDs verified against Football-Data.org API
- ✅ **Africa Cup of Nations (AFCON)** - 24 teams, CSV-based (not on Football-Data.org free tier)

**All teams verified on:** December 10, 2024

---

## 🎯 Two Types of Competitions

### Type 1: API-Connected (Football-Data.org)

**Examples:** Champions League, Premier League, La Liga, Bundesliga, etc.

**Characteristics:**
- Automatic fixture import from API
- Automatic score updates from API
- Requires exact name + external ID matching
- Team names MUST match API exactly

**Available on Football-Data.org Free Tier:**
- ✅ UEFA Champions League (CL)
- ✅ Premier League (PL)
- ✅ Bundesliga (BL1)
- ✅ Serie A (SA)
- ✅ Ligue 1 (FL1)
- ✅ Eredivisie (DED)
- ✅ Primeira Liga (PPL)
- ✅ European Championship (EC)
- ✅ FIFA World Cup (WC)

### Type 2: CSV-Based

**Examples:** AFCON, lower-tier leagues, custom competitions

**Characteristics:**
- Manual CSV upload for fixtures
- Manual CSV upload for scores
- Can use any team names (no API constraint)
- External IDs can be custom (e.g., AFCON_001)
- More flexible but requires manual work

---

## 📋 Process: Adding an API-Connected Competition

### Step 1: Verify Competition is Available

Check if competition is on Football-Data.org free tier:

```bash
curl -H "X-Auth-Token: YOUR_TOKEN" \
  https://api.football-data.org/v4/competitions
```

**Look for:**
- Competition code (e.g., "BL1" for Bundesliga)
- Plan: "TIER_ONE" (free tier)

### Step 2: Get Team Data from API

```bash
curl -H "X-Auth-Token: YOUR_TOKEN" \
  https://api.football-data.org/v4/competitions/BL1/teams \
  > bundesliga_teams.json
```

### Step 3: Create Team Addition Script

Create a script like `/app/scripts/add_bundesliga_teams.py`:

```python
#!/usr/bin/env python3
"""
Add Bundesliga teams to the database
"""
import sys
sys.path.insert(0, '/app/backend')

from pymongo import MongoClient
import os
from datetime import datetime, timezone
from uuid import uuid4

# Load environment
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
db_name = os.getenv('DB_NAME', 'test_database')

client = MongoClient(mongo_url)
db = client[db_name]

# Teams from API (copy from API response)
BUNDESLIGA_TEAMS = [
    {"name": "FC Bayern München", "externalId": "5"},
    {"name": "Borussia Dortmund", "externalId": "4"},
    # ... add all teams
]

def add_teams():
    """Add all Bundesliga teams to the database"""
    
    print("="*70)
    print("ADDING BUNDESLIGA TEAMS")
    print("="*70)
    
    now = datetime.now(timezone.utc).isoformat()
    added_count = 0
    skipped_count = 0
    
    for team_data in BUNDESLIGA_TEAMS:
        team_name = team_data["name"]
        
        # Check if team already exists
        existing = db.assets.find_one({
            'name': team_name,
            'sportKey': 'football',
            'externalId': team_data["externalId"]
        })
        
        if existing:
            print(f"  ⏭️  {team_name} - Already exists")
            skipped_count += 1
            continue
        
        # Create team document
        team_doc = {
            "id": str(uuid4()),
            "sportKey": "football",
            "name": team_name,
            "externalId": team_data["externalId"],
            "city": "",
            "selected": True,
            "createdAt": now,
            "updatedAt": now,
            "competition": "Bundesliga",
            "competitionShort": "BL1",
            "competitions": ["Bundesliga"],  # Use full name
            "country": "Germany",
            "logo": None
        }
        
        db.assets.insert_one(team_doc)
        print(f"  ✅ {team_name}")
        added_count += 1
    
    print()
    print("="*70)
    print(f"Added: {added_count}, Skipped: {skipped_count}")
    print("="*70)

if __name__ == "__main__":
    add_teams()
```

### Step 4: Run Script in Preview First

```bash
cd /app/scripts
python3 add_bundesliga_teams.py
```

Verify teams were added correctly.

### Step 5: Create Migration Script for Production

Add to `/app/backend/migrate_team_names_v2.py`:

```python
# Bundesliga teams (if different from API)
bundesliga_updates = [
    # Only if names need updating
    ('Bayern München', 'FC Bayern München', '5', 'Bundesliga'),
]
```

### Step 6: Verify Against API

```bash
cd /app/backend
python3 verify_all_teams.py
```

Update script to include Bundesliga verification.

### Step 7: Deploy to Production

1. Deploy code with new teams
2. Check migration status: `/api/admin/migration/status`
3. Test fixture import for the new competition

---

## 📋 Process: Adding a CSV-Based Competition

Much simpler! No API constraints.

### Step 1: Create Teams Script

```python
CUSTOM_LEAGUE_TEAMS = [
    {"name": "Team A", "country": "Country"},
    {"name": "Team B", "country": "Country"},
    # ... add all teams
]

for i, team_data in enumerate(CUSTOM_LEAGUE_TEAMS, 1):
    team_doc = {
        "id": str(uuid4()),
        "sportKey": "football",
        "name": team_data["name"],
        "externalId": f"CUSTOM_{i:03d}",  # Custom IDs
        "selected": True,
        "competitionShort": "CUSTOM",
        "competitions": ["Custom League Name"],
        "country": team_data["country"]
    }
    # Insert...
```

### Step 2: Create CSV Template

Create fixture template similar to AFCON:

```csv
date,homeTeam,awayTeam,goalsHome,goalsAway
2025-01-15,Team A,Team B,,
2025-01-16,Team C,Team D,,
```

### Step 3: Users Upload Fixtures

Users can upload fixtures via UI using the CSV template.

---

## 🔍 Verification Checklist

After adding new competition:

- [ ] **Teams added to database** with correct `sportKey`, `competitionShort`, `competitions`
- [ ] **External IDs match API** (for API-connected competitions)
- [ ] **Names match API exactly** (for API-connected competitions)
- [ ] **Run verification script** (`python3 verify_all_teams.py`)
- [ ] **Test fixture import** in a test league
- [ ] **Test score update** with real fixtures
- [ ] **Test points calculation** - verify scoring works

---

## 🛠️ Maintenance Scripts

### Verify All Teams

```bash
cd /app/backend
python3 verify_all_teams.py
```

Shows:
- ✅ Teams that match API
- ⚠️ Name mismatches
- ❌ Invalid IDs

### Update Team Names

If API changes team names:

1. Add to `/app/backend/migrate_team_names_v2.py`:
   ```python
   new_updates = [
       ('Old Name', 'New Name', 'external_id', 'Competition Name'),
   ]
   ```

2. Deploy and run migration

3. Verify: `python3 verify_all_teams.py`

---

## 📝 Important Rules

### For API-Connected Competitions:

1. **Team names MUST match API exactly**
   - "Manchester United FC" ✅
   - "Man United" ❌

2. **External IDs MUST match API**
   - Get from: `/v4/competitions/{CODE}/teams`

3. **Competition names matter**
   - Use full names: "UEFA Champions League" not "CL"
   - Stored in `competitions` array field

4. **Test in preview first**
   - Add teams in preview
   - Verify against API
   - Then deploy to production

### For CSV-Based Competitions:

1. **Team names can be anything** (user-friendly)

2. **External IDs can be custom**
   - Format: `{COMP_CODE}_{NUMBER}`
   - Example: `AFCON_001`, `CUSTOM_001`

3. **Still use full competition names**
   - "Africa Cup of Nations" not "AFCON"

4. **Create CSV template**
   - Make it available for download
   - Include clear instructions

---

## 🚀 Quick Start Checklist

When adding a new competition:

1. [ ] Determine type: API-connected or CSV-based
2. [ ] If API: Verify it's on Football-Data.org free tier
3. [ ] Create addition script based on type
4. [ ] Test in preview environment
5. [ ] Run verification script
6. [ ] Deploy to production
7. [ ] Test end-to-end: fixture import → score update → points calculation

---

## 📞 Troubleshooting

### "Fixtures import but no points calculated"

**Cause:** Team names don't match API

**Fix:** 
1. Run `verify_all_teams.py` to find mismatches
2. Update migration script with corrections
3. Redeploy and run migration

### "Team not found when importing fixtures"

**Cause:** External ID doesn't match API

**Fix:**
1. Check API for correct ID
2. Update database with correct ID
3. Re-import fixtures

### "New competition not showing in UI"

**Cause:** Frontend might need updating

**Fix:**
1. Check if `competitionShort` matches what UI expects
2. May need to add competition to frontend dropdown

---

## 📚 Reference: Current Database Schema

```javascript
{
  "id": "uuid",
  "sportKey": "football",  // or "cricket"
  "name": "Team Name",  // MUST match API for API-connected
  "externalId": "123",  // MUST match API for API-connected
  "city": "",
  "selected": true,
  "createdAt": "ISO datetime",
  "updatedAt": "ISO datetime",
  "competition": "Competition Name",  // Deprecated, use competitions array
  "competitionShort": "CL",  // Competition code
  "competitions": ["Full Competition Name"],  // CRITICAL for matching
  "country": "Country",
  "logo": null,
  "uefaId": ""  // Optional
}
```

**Critical Fields:**
- `name` - Must match API exactly (for API-connected)
- `externalId` - Must match API exactly (for API-connected)
- `competitions` - Array with FULL competition name (e.g., "UEFA Champions League")

---

**Document Version:** 1.0  
**Created:** December 10, 2024  
**Last Verified:** December 10, 2024
