# Database Consolidation Plan

## Current State (Confirmed)

### Collections
- **clubs**: 52 documents (UCL + EPL teams)
- **assets**: 50 documents (Cricket players + EPL teams)
- **fixtures**: 19 documents (Cricket matches + Football fixtures)
- **leagues**: 22 documents
- **auctions**: 19 documents
- **bids**: 289 documents
- **league_participants**: 43 documents
- **users**: 175 documents

### The Duplicate Problem
**20 EPL teams exist in BOTH collections:**
- AFC Bournemouth, Aston Villa, Brentford, Brighton, Burnley, Crystal Palace, Fulham, Liverpool, Manchester United, Nottingham Forest, etc.

### Current Usage
- **11 leagues use CLUBS**
- **1 league uses ASSETS**
- **All football fixtures link to ASSETS**
- **Result: 11 leagues cannot show fixtures for their teams**

### Relationship Analysis

```
CLUBS (52)
├── UCL teams (32): Real Madrid, Barcelona, etc.
└── EPL teams (20): Arsenal, Liverpool, etc.

ASSETS (50)
├── Cricket players (30): Harry Brook, Joe Root, etc.
└── EPL teams (20): Arsenal, Liverpool, etc. [DUPLICATES]

LEAGUES (22)
├── 11 → reference CLUBS.id
└── 1 → reference ASSETS.id

AUCTIONS (19)
├── 11 → clubQueue references CLUBS.id
└── 8 → clubQueue references ASSETS.id

FIXTURES (19)
├── Cricket (9) → homeAssetId/awayAssetId reference ASSETS.id
└── Football (10) → homeTeamId/awayTeamId reference ASSETS.id [BROKEN]

BIDS (289)
└── clubId references ??? (mix of both, some orphaned)

LEAGUE_PARTICIPANTS (43)
└── clubsWon references ??? (mix of both)
```

## The Problem

**Auctions using CLUBS cannot link to fixtures that reference ASSETS.**

Example:
- League "prem19" uses Arsenal from CLUBS (id: `41badd9c...`)
- Fixture "Chelsea vs Arsenal" uses Arsenal from ASSETS (id: `d4f3eddc...`)
- These IDs don't match → cannot show "next fixture" in auction

## Consolidation Strategy

### Option A: Migrate Everything to ASSETS (RECOMMENDED)

**Why ASSETS:**
1. Already has multi-sport support (cricket + football)
2. Fixtures already link to ASSETS
3. Has `externalId` field for API-Football integration
4. More flexible schema

**Steps:**

1. **Backup Database**
   ```bash
   mongodump --uri="mongodb://localhost:27017/test_database" --out=/backup
   ```

2. **Add Missing Teams to ASSETS**
   - Copy 32 UCL teams from CLUBS to ASSETS
   - Keep existing 20 EPL teams in ASSETS (don't duplicate)
   - Map CLUBS.id → ASSETS.id for duplicates

3. **Update All References**
   - leagues.assetsSelected: Update IDs from CLUBS to ASSETS
   - auctions.clubQueue: Update IDs from CLUBS to ASSETS
   - auctions.currentClubId: Update IDs from CLUBS to ASSETS
   - league_participants.clubsWon: Update IDs from CLUBS to ASSETS
   - bids.clubId: Update IDs from CLUBS to ASSETS

4. **Update Football Fixtures**
   - Change homeTeamId/awayTeamId to match new ASSETS IDs

5. **Verify Everything Works**
   - Test auctions
   - Test fixture display
   - Test bids
   - Test leaderboards

6. **Delete CLUBS Collection**
   - Once verified, remove CLUBS entirely

### Option B: Migrate Everything to CLUBS (NOT RECOMMENDED)

**Problems:**
- CLUBS schema is rigid (designed for football only)
- Would need to restructure for multi-sport
- Fixtures already work with ASSETS
- More work, less flexible

## Detailed Migration Script

### Phase 1: Create ID Mapping (30 min)

```python
# Build mapping of CLUBS.id → ASSETS.id for duplicates
id_mapping = {}

for each EPL team in CLUBS:
    matching_asset = find in ASSETS where name matches
    if matching_asset:
        id_mapping[club.id] = asset.id
    else:
        # Team only in CLUBS, will be copied to ASSETS
        id_mapping[club.id] = None  # Will be new ID
```

### Phase 2: Copy UCL Teams to ASSETS (30 min)

```python
for each UCL team in CLUBS:
    if team.name not in ASSETS:
        new_asset = {
            id: club.id,  # Keep same ID
            name: club.name,
            sportKey: "football",
            externalId: club.uefaId,  # Map to external
            meta: {
                country: club.country,
                competition: club.competition,
                logo: club.logo
            }
        }
        insert into ASSETS
```

### Phase 3: Update All References (1-2 hours)

```python
# Update leagues
for each league in LEAGUES:
    for each asset_id in league.assetsSelected:
        if asset_id in id_mapping:
            league.assetsSelected[i] = id_mapping[asset_id]
    save league

# Update auctions
for each auction in AUCTIONS:
    for each club_id in auction.clubQueue:
        if club_id in id_mapping:
            auction.clubQueue[i] = id_mapping[club_id]
    
    if auction.currentClubId in id_mapping:
        auction.currentClubId = id_mapping[auction.currentClubId]
    
    save auction

# Update participants
for each participant in LEAGUE_PARTICIPANTS:
    for each club_id in participant.clubsWon:
        if club_id in id_mapping:
            participant.clubsWon[i] = id_mapping[club_id]
    save participant

# Update bids
for each bid in BIDS:
    if bid.clubId in id_mapping:
        bid.clubId = id_mapping[bid.clubId]
    save bid
```

### Phase 4: Update Fixtures (30 min)

```python
# Football fixtures already link to ASSETS - verify they're correct
for each fixture in FIXTURES where sportKey='football':
    verify homeTeamId exists in ASSETS
    verify awayTeamId exists in ASSETS
    if not, fix mapping
```

### Phase 5: Verification (1 hour)

```python
# Check all references are valid
for each league in LEAGUES:
    for each asset_id in league.assetsSelected:
        assert asset_id exists in ASSETS

for each auction in AUCTIONS:
    for each club_id in auction.clubQueue:
        assert club_id exists in ASSETS

for each participant in LEAGUE_PARTICIPANTS:
    for each club_id in participant.clubsWon:
        assert club_id exists in ASSETS

for each bid in BIDS:
    assert bid.clubId exists in ASSETS

for each fixture in FIXTURES:
    assert fixture.homeAssetId exists in ASSETS
    assert fixture.awayAssetId exists in ASSETS

print("All references valid!")
```

### Phase 6: Delete CLUBS (5 min)

```python
# Only after full verification
db.clubs.drop()
```

## Testing Plan

### Test Case 1: Existing Auction
- Open prem19 auction
- Verify teams display correctly
- Verify bids work
- Verify auction completes properly

### Test Case 2: Fixtures
- Open league dashboard
- Navigate to fixtures tab
- Verify all fixtures display with correct team names

### Test Case 3: New Auction
- Create new league
- Select teams
- Start auction
- Verify everything works

### Test Case 4: Leaderboards
- Check that clubsWon still maps correctly
- Verify scores calculate properly

## Rollback Plan

If migration fails:
1. Stop all operations
2. Restore from mongodump backup
3. Identify what failed
4. Fix script
5. Try again

## Timeline

- **Planning & Backup**: 30 min
- **Migration Script**: 2 hours
- **Execution**: 30 min
- **Testing**: 1 hour
- **Verification**: 30 min
- **Total**: ~5 hours

## Success Criteria

✅ All 22 leagues work
✅ All 19 auctions work
✅ All 289 bids reference valid teams
✅ All 19 fixtures link correctly
✅ "Next fixture" feature can be implemented
✅ No orphaned references
✅ CLUBS collection deleted

## Risk Assessment

**Low Risk:**
- Database backup exists
- Can rollback if needed
- No data deletion (only restructuring)

**Medium Risk:**
- 289 bids to update
- 43 participants to update
- Must update atomically

**High Risk:**
- If mapping is wrong, references break
- Testing must be thorough
- Pilot could be affected if rushed

## Recommendation

**DO THIS BEFORE PILOT**

The current architecture will cause issues during the pilot:
- Users won't see fixtures for their teams
- Any new feature will hit the same problems
- Support burden will be high

Better to fix now than explain to users why things don't work.
