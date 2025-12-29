# The Ashes Fixtures Architecture

## How Fixtures Connect to Commissioner Competitions

### 🏗️ Two-Tier System

The application uses a **two-tier fixture system** to support multiple commissioners running competitions based on the same real-world matches:

```
Real World: Australia vs England (5 Test Matches)
     ↓
     ↓ ONE SET OF REAL MATCHES
     ↓
├─→ Commissioner A's Ashes Competition (20 players selected)
├─→ Commissioner B's Ashes Competition (15 players selected)  
└─→ Commissioner C's Ashes Competition (25 players selected)
```

---

## 📊 Architecture Breakdown

### 1. **Shared Fixtures** (Future/Football Model)
- Stored **without** `leagueId`
- Represent real-world matches (e.g., "Arsenal vs Liverpool")
- **One fixture**, **many competitions** can reference it
- Updated via API (Football-Data.org for football, Cricbuzz for cricket)

### 2. **League-Specific Fixtures** (Current/Cricket Model)
- Stored **with** `leagueId` 
- Imported via CSV by each commissioner
- Each competition has its own copy of fixtures
- Commissioners manually trigger updates

---

## 🏏 Current Ashes Implementation (League-Specific Model)

### Step-by-Step Flow:

#### **1. Commissioner Creates Ashes Competition**
```javascript
POST /api/leagues
{
  "name": "Darren's Ashes 2025",
  "sportKey": "cricket",
  "assetsSelected": ["steven-smith", "ben-stokes", ...], // 20 players
  "budget": 500000000,
  "clubSlots": 10
}
```
**Result**: League created with ID `abc-123`

---

#### **2. Commissioner Imports Fixtures via CSV**
```javascript
POST /api/leagues/abc-123/fixtures/import-csv
```

**CSV Format:**
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-11-21 23:30:00,australia,england,Perth Stadium,1st Test,ashes-test-1
2025-12-06 03:30:00,australia,england,Adelaide Oval,2nd Test,ashes-test-2
2025-12-14 23:30:00,australia,england,Gabba,3rd Test,ashes-test-3
2026-12-26 23:30:00,australia,england,MCG,4th Test,ashes-test-4
2026-01-03 23:30:00,australia,england,SCG,5th Test,ashes-test-5
```

**Backend Creates Fixtures:**
```json
{
  "id": "fixture-001",
  "leagueId": "abc-123",           // ← Linked to this league ONLY
  "sportKey": "cricket",
  "externalMatchId": "ashes-test-1",
  "homeTeam": "Australia",
  "awayTeam": "England", 
  "startsAt": "2025-11-21T23:30:00Z",
  "venue": "Perth Stadium",
  "status": "scheduled",
  "source": "csv"
}
```

---

#### **3. Match Happens in Real World**
**Real Event**: Australia vs England, 1st Test at Perth
- Australia: 250 & 300
- England: 200 & 280
- **Australia wins by 70 runs**

**Players' Performances:**
- Mitchell Starc: 5 wickets → 100 points (5 × 20)
- Travis Head: 120 runs → 120 points (120 × 1)
- Ben Stokes: 75 runs, 2 wickets → 115 points

---

#### **4. Commissioner Updates Scores**

**Option A: CSV Upload (Manual)**
```javascript
POST /api/scoring/abc-123/ingest
// Upload CSV with player stats
```

**Option B: API Update (Automatic - YOUR NEW FEATURE!)**
```javascript
// Commissioner clicks "Update Cricket Scores" button
POST /api/cricket/update-scores

// Backend:
1. Calls Cricbuzz API → gets "Australia vs England" match data
2. Finds fixture by matching team names:
   db.fixtures.find({
     "leagueId": "abc-123",
     "homeTeam": "Australia", 
     "awayTeam": "England",
     "status": "scheduled"
   })
3. Updates fixture status → "completed"
4. Stores scorecard data
5. Extracts player stats (Starc: 5 wkts, Head: 120 runs, etc.)
6. Updates league_points collection for each manager
```

---

#### **5. Manager Points Updated**

**Manager 1 owns**: Mitchell Starc, Travis Head
- Points: 100 (Starc) + 120 (Head) = **220 points**

**Manager 2 owns**: Ben Stokes, Joe Root (40 runs)
- Points: 115 (Stokes) + 40 (Root) = **155 points**

**Manager 3 owns**: Steve Smith (60 runs), Pat Cummins (3 wickets)
- Points: 60 (Smith) + 60 (Cummins) = **120 points**

**Leaderboard after Match 1:**
1. Manager 1: 220 pts
2. Manager 2: 155 pts
3. Manager 3: 120 pts

---

## 🔄 For Multiple Commissioners

### Scenario: 3 Commissioners Running Ashes Competitions

**Commissioner A** (League ID: `aaa-111`):
- Selected 15 players
- Imports fixtures → Creates 5 fixtures with `leagueId: aaa-111`
- Updates scores → Only their fixtures/players update

**Commissioner B** (League ID: `bbb-222`):
- Selected 20 players (different mix)
- Imports fixtures → Creates 5 fixtures with `leagueId: bbb-222`
- Updates scores → Only their fixtures/players update

**Commissioner C** (League ID: `ccc-333`):
- Selected 12 players
- Imports fixtures → Creates 5 fixtures with `leagueId: ccc-333`
- Updates scores → Only their fixtures/players update

**Each competition is isolated!**
- Same real-world matches
- Different player selections
- Different managers
- Independent scoring

---

## 🆚 Comparison: Current vs Ideal Architecture

### Current (CSV-Based):
```
Real Match: AUS vs ENG
     ↓
Commissioner A imports CSV → Fixtures (leagueId: A)
Commissioner B imports CSV → Fixtures (leagueId: B)
Commissioner C imports CSV → Fixtures (leagueId: C)

Each clicks "Update Scores" → Updates their fixtures
```
**Pros**: Complete isolation, commissioner control
**Cons**: Duplicate data, manual CSV creation

---

### Ideal (Shared Fixtures):
```
Real Match: AUS vs ENG
     ↓
ONE shared fixture (no leagueId)
     ↓
Competition A references it
Competition B references it
Competition C references it

API update → Updates ONE fixture → All competitions see update
```
**Pros**: No duplication, automatic updates
**Cons**: More complex, requires migration

---

## 📋 Database Schema

### Fixtures Collection:
```json
{
  "id": "unique-id",
  "leagueId": "abc-123",              // Links to specific competition
  "sportKey": "cricket",
  "externalMatchId": "ashes-test-1",  // For API matching
  "homeTeam": "Australia",
  "awayTeam": "England",
  "startsAt": "2025-11-21T23:30:00Z",
  "status": "scheduled|completed",
  "scorecard": {...},                  // From Cricbuzz API
  "source": "csv"
}
```

### Leagues Collection:
```json
{
  "id": "abc-123",
  "name": "Darren's Ashes 2025",
  "sportKey": "cricket",
  "commissionerId": "user-456",
  "assetsSelected": ["steven-smith", "ben-stokes", ...]
}
```

### League Points Collection:
```json
{
  "leagueId": "abc-123",
  "userId": "manager-789",
  "assetId": "mitchell-starc",
  "fixtureId": "fixture-001",
  "points": 100
}
```

---

## ✅ Summary

**For The Ashes:**
1. Each commissioner imports their own set of 5 Test match fixtures via CSV
2. Fixtures are linked to that specific league via `leagueId`
3. When commissioner clicks "Update Cricket Scores":
   - Cricbuzz API fetches real match data
   - Updates fixtures for THAT league only
   - Player stats → Manager points for THAT league
4. Multiple commissioners can run independent Ashes competitions
5. Same real-world matches, different competitions, isolated scoring

**Your Cricbuzz integration works perfectly with this model!** ✅
