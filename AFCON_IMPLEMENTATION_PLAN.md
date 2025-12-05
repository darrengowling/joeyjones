# AFCON Implementation Plan

## Overview
Add support for AFCON 2025/26 competition with 24 qualified teams using manual CSV import for fixtures and scores (since AFCON is not covered by Football-Data.org free tier).

---

## 1. Teams to Add (24 Teams)

### Group A
- Morocco (hosts)
- Mali
- Zambia
- Comoros

### Group B
- Egypt
- South Africa
- Angola
- Zimbabwe

### Group C
- Nigeria
- Tunisia
- Uganda
- Tanzania

### Group D
- Senegal
- DR Congo (Democratic Republic of Congo)
- Benin
- Botswana

### Group E
- Algeria
- Burkina Faso
- Equatorial Guinea
- Sudan

### Group F
- Ivory Coast
- Cameroon
- Gabon
- Mozambique

---

## 2. Team Data Structure

Each team needs the following fields (based on existing football teams):

```json
{
  "id": "uuid",
  "sportKey": "football",
  "name": "Team Name",
  "externalId": "AFCON_{sequential_number}",  // e.g., AFCON_001
  "city": "",  // Can be empty or capital city
  "selected": true,
  "createdAt": "ISO timestamp",
  "updatedAt": "ISO timestamp",
  "apiFootballId": "",  // Not applicable
  "competition": "Africa Cup of Nations",
  "competitionShort": "AFCON",
  "country": "Country Name",  // e.g., "Morocco", "Egypt"
  "logo": null,
  "uefaId": "",  // Not applicable
  "competitions": ["Africa Cup of Nations"]
}
```

---

## 3. Implementation Steps

### Step 1: Create AFCON Teams Script
**File:** `/app/scripts/add_afcon_teams.py`

**Purpose:** Bulk insert 24 AFCON teams into the assets collection

**Logic:**
1. Define list of 24 teams with their countries
2. For each team:
   - Generate UUID
   - Set `competitionShort: "AFCON"`
   - Set `competitions: ["Africa Cup of Nations"]`
   - Set `externalId` as sequential (AFCON_001 to AFCON_024)
   - Set `country` field to respective nation
3. Insert into database
4. Log results

### Step 2: Update Frontend - Competition Selection
**Files:** 
- `/app/frontend/src/App.js` (league creation modal)
- `/app/frontend/src/pages/CreateLeague.js` (if applicable)

**Changes:**
1. Add "AFCON" to competition dropdown where "PL" and "CL" exist
2. Update filter logic to support `competitionShort: "AFCON"`

**Example:**
```jsx
<option value="AFCON">AFCON (24)</option>
```

### Step 3: Verify CSV Import Works for AFCON
**Existing endpoint:** `POST /api/leagues/{league_id}/fixtures/import-csv`

**CSV Format (already supported):**
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-12-21T20:00:00Z,AFCON_001,AFCON_002,Stadium Name,Group A Matchday 1,AFCON_MATCH_001
```

**Testing Required:**
- Create AFCON league
- Upload CSV with sample fixtures
- Verify fixtures display correctly

### Step 4: Manual Score Updates
**CONFIRMED APPROACH: Both CSV and Manual UI Entry**

**Method 1: CSV Upload (Bulk Updates)**
- Extend CSV import to include score columns (goalsHome, goalsAway, status)
- Useful for commissioners who want to update multiple matches at once

**Method 2: Manual UI Entry (Individual Updates)**
- Add inline editing in fixtures table on league detail page
- Allow commissioners to click and edit scores directly
- Useful for quick updates after individual matches

---

## 4. CSV Template for AFCON Fixtures

Create a template CSV commissioners can download:

**File:** `/app/public/templates/afcon_fixtures_template.csv`

```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId,goalsHome,goalsAway,status
2025-12-21T20:00:00Z,AFCON_001,AFCON_002,Stade Mohammed V,Group A MD1,AFCON_001,,,scheduled
2025-12-21T23:00:00Z,AFCON_003,AFCON_004,Stade Mohammed V,Group A MD1,AFCON_002,,,scheduled
```

**Fields:**
- `startsAt`: ISO timestamp (required)
- `homeAssetExternalId`: Team's externalId (e.g., AFCON_001)
- `awayAssetExternalId`: Team's externalId (e.g., AFCON_002)
- `venue`: Stadium name (optional)
- `round`: Match round/stage (optional)
- `externalMatchId`: Unique match identifier (optional, for updates)
- `goalsHome`: Goals scored by home team (optional, for score updates)
- `goalsAway`: Goals scored by away team (optional, for score updates)
- `status`: Match status - "scheduled", "in_progress", "completed" (optional)

---

## 5. Backend Changes Required

### A. Extend CSV Import to Handle Scores
**File:** `/app/backend/server.py`
**Endpoint:** `POST /api/leagues/{league_id}/fixtures/import-csv`

**Current behavior:** Only creates/updates fixtures with basic info
**Needed:** Accept and update score fields (goalsHome, goalsAway, status)

**Logic:**
```python
# After line 2546 in existing CSV import
goals_home = row.get('goalsHome', '').strip()
goals_away = row.get('goalsAway', '').strip()
status = row.get('status', '').strip() or 'scheduled'

if goals_home and goals_away:
    fixture_doc["goalsHome"] = int(goals_home)
    fixture_doc["goalsAway"] = int(goals_away)
    
    if int(goals_home) > int(goals_away):
        fixture_doc["winner"] = "home"
    elif int(goals_away) > int(goals_home):
        fixture_doc["winner"] = "away"
    else:
        fixture_doc["winner"] = "draw"

fixture_doc["status"] = status
```

### B. Add AFCON to Competition Mappings (Optional)
**File:** `/app/backend/football_data_client.py` (if needed)

Since AFCON uses CSV only, no API changes needed here.

---

## 6. Frontend Changes Required

### A. Add AFCON to Competition Dropdown
**Files:**
- `/app/frontend/src/App.js` (line ~147 - league creation modal)
- `/app/frontend/src/pages/CreateLeague.js` (if separate)
- `/app/frontend/src/pages/LeagueDetail.js` (line ~917 - team filter)

**Change:**
```jsx
<select value={competitionCode} onChange={(e) => setCompetitionCode(e.target.value)}>
  <option value="PL">Premier League</option>
  <option value="CL">Champions League</option>
  <option value="AFCON">AFCON</option>  {/* ADD THIS */}
</select>
```

### B. Update Team Filter Dropdown
**Files:**
- `/app/frontend/src/pages/LeagueDetail.js` (line ~917)
- `/app/frontend/src/pages/CreateLeague.js` (line ~313)

**Change:**
```jsx
<option value="all">All Teams ({availableAssets.length})</option>
<option value="EPL">Premier League Only (20)</option>
<option value="UCL">Champions League Only (36)</option>
<option value="AFCON">AFCON Only (24)</option>  {/* ADD THIS */}
```

### C. CSV Upload UI (Already Exists)
Verify existing CSV upload button in league detail page works for AFCON leagues.

---

## 7. Testing Plan

### Phase 1: Teams
1. Run script to add 24 AFCON teams
2. Verify teams appear in database
3. Verify teams show in team selection when creating AFCON league

### Phase 2: League Creation
1. Create AFCON league with competitionCode: "AFCON"
2. Select 4-8 AFCON teams
3. Verify league creation succeeds

### Phase 3: CSV Fixture Import
1. Create sample CSV with 2-3 AFCON fixtures
2. Upload CSV via commissioner account
3. Verify fixtures display in league detail page

### Phase 4: CSV Score Update
1. Create CSV with same fixtures but with scores
2. Upload CSV to update scores
3. Verify scores display correctly
4. Verify winner calculation works

### Phase 5: Auction & Next Fixture
1. Run auction for AFCON league
2. Verify "next fixture" displays correctly for AFCON teams
3. Verify auction completion and fixtures tab

---

## 8. Potential Issues & Solutions

### Issue 1: externalId Conflicts
**Problem:** AFCON_001 might conflict with other sports
**Solution:** Use prefix like "AFCON_001" (already planned)

### Issue 2: Team Name Variations
**Problem:** "Côte d'Ivoire" vs "Ivory Coast"
**Solution:** Use official AFCON names consistently

### Issue 3: CSV Score Updates vs Fixture Creation
**Problem:** Need to differentiate between new fixtures and score updates
**Solution:** Use `externalMatchId` as unique identifier for upserts

### Issue 4: No API for Score Fetching
**Problem:** All scores must be manually entered
**Solution:** Document this clearly for commissioners, provide CSV templates

---

## 9. Documentation Needed

### For Commissioners:
1. **AFCON Quick Start Guide:**
   - How to create AFCON league
   - How to download fixture template
   - How to upload fixtures
   - How to update scores

2. **CSV Template with Examples:**
   - Sample fixtures for each group
   - Sample score updates

### For Developers:
1. Update README with AFCON support notes
2. Document CSV format in API documentation

---

## 10. Deployment Checklist

- [ ] Run `add_afcon_teams.py` script in production
- [ ] Verify 24 teams in database
- [ ] Test league creation with AFCON
- [ ] Test CSV fixture import
- [ ] Test CSV score update
- [ ] Test auction flow
- [ ] Provide CSV template to pilot users
- [ ] Document manual score update process

---

## 11. Estimated Effort

**Backend:**
- Add AFCON teams script: 30 mins
- Extend CSV import for scores: 45 mins
- Testing: 30 mins

**Frontend:**
- Add competition dropdown option: 15 mins
- Update filter dropdowns: 15 mins
- Testing: 30 mins

**Documentation:**
- User guide: 30 mins
- CSV templates: 15 mins

**Total: ~3.5 hours**

---

## 12. User Requirements - CONFIRMED ✅

1. **Logos:** Not needed - set to null
2. **CSV Templates:** Pre-populate with group stage fixtures (36 matches)
3. **Score Updates:** Both CSV upload AND manual UI entry
4. **Team Naming:** Use English names (e.g., "Ivory Coast" not "Côte d'Ivoire")
5. **Multi-year Support:** Not needed - single 4-week tournament (Dec 21, 2025 - Jan 18, 2026)

---

## Implementation Order

1. **Backend First:** Add teams script → Test in database
2. **Frontend:** Add competition options → Test team selection
3. **CSV Enhancement:** Extend for scores → Test import/update
4. **End-to-End:** Create league → Import fixtures → Update scores → Run auction
5. **Documentation:** Templates and guides

---

This plan covers all aspects of AFCON implementation. Please review and provide feedback before I proceed with implementation.
