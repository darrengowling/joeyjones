# Team Selection Feature - Behind Feature Flag

**Date:** 2025-10-16  
**Type:** Feature Flag Implementation  
**Status:** ✅ DEPLOYED (Default: OFF)

---

## Summary

Re-introduced the team selection feature behind a feature flag `FEATURE_ASSET_SELECTION`. When disabled (default), the system works exactly as before using all available teams. When enabled, commissioners can optionally select specific teams for their auction.

---

## Feature Flag Configuration

### Backend (.env)

```bash
FEATURE_ASSET_SELECTION=false  # Default: OFF
```

### Frontend (.env)

```bash
REACT_APP_FEATURE_ASSET_SELECTION=false  # Default: OFF
```

### Behavior by Flag State

| Flag State | Backend Behavior | Frontend UI |
|------------|------------------|-------------|
| `false` (default) | Uses all available teams | Team selection hidden |
| `true` | Respects `assetsSelected` if provided | Shows team selection UI |

---

## Backend Implementation

### Feature Flag

**File:** `/app/backend/server.py`

```python
FEATURE_ASSET_SELECTION = os.environ.get('FEATURE_ASSET_SELECTION', 'false').lower() == 'true'
logger.info(f"Asset Selection feature enabled: {FEATURE_ASSET_SELECTION}")
```

### Auction Start Logic

**File:** `/app/backend/server.py` (lines 1287-1332)

```python
assets_selected = league.get("assetsSelected", [])
seed_mode = "all"  # Default mode

# Feature flag: Only use assetsSelected if FEATURE_ASSET_SELECTION is enabled
if FEATURE_ASSET_SELECTION and assets_selected and len(assets_selected) > 0:
    # Use commissioner's selected assets (feature flag ON + assets selected)
    seed_mode = "selected"
    if sport_key == "football":
        all_assets = await db.clubs.find({"id": {"$in": assets_selected}}).to_list(100)
    else:
        all_assets = await db.assets.find({
            "id": {"$in": assets_selected}, 
            "sportKey": sport_key
        }).to_list(100)
    
    # Validation
    if len(all_assets) == 0:
        raise HTTPException(400, "No valid selected teams found")
    
    logger.info("auction.seed_queue", extra={
        "mode": "selected",
        "selected_count": len(all_assets),
        "leagueId": league_id
    })
else:
    # Use all available assets (default or feature flag OFF)
    if sport_key == "football":
        all_assets = await db.clubs.find().to_list(100)
    else:
        all_assets = await db.assets.find({"sportKey": sport_key}).to_list(100)
    
    logger.info("auction.seed_queue", extra={
        "mode": "all",
        "selected_count": len(all_assets),
        "feature_enabled": FEATURE_ASSET_SELECTION
    })
```

### Key Points

1. **Feature flag checked FIRST**
2. **Only uses assetsSelected if:**
   - Flag is `true` AND
   - `assetsSelected` exists AND
   - `assetsSelected` is not empty
3. **Falls back to "all" if:**
   - Flag is `false` OR
   - No assets selected OR
   - Empty array
4. **Validates selected assets exist**
5. **Structured logging for mode tracking**

---

## Frontend Implementation

### Feature Flag

**File:** `/app/frontend/src/pages/CreateLeague.js`

```javascript
const FEATURE_ASSET_SELECTION = process.env.REACT_APP_FEATURE_ASSET_SELECTION === 'true';
```

### State Management

```javascript
const [availableAssets, setAvailableAssets] = useState([]);
const [teamMode, setTeamMode] = useState("all"); // "all" or "select"
const [selectedAssets, setSelectedAssets] = useState([]);
const [assetSearchTerm, setAssetSearchTerm] = useState("");
```

### Fetch Available Assets

```javascript
useEffect(() => {
  // Fetch available assets when sport changes (if feature enabled)
  if (FEATURE_ASSET_SELECTION) {
    const fetchAssets = async () => {
      try {
        if (form.sportKey === "football") {
          const response = await axios.get(`${API}/clubs`);
          setAvailableAssets(response.data);
        } else {
          const response = await axios.get(`${API}/assets?sport=${form.sportKey}`);
          setAvailableAssets(response.data);
        }
      } catch (error) {
        console.error("Error fetching assets:", error);
      }
    };
    
    fetchAssets();
  }
}, [form.sportKey]);
```

### Submit Logic

```javascript
const handleSubmit = async (e) => {
  // ... existing validation ...
  
  // Validation: If team mode is "select" and no teams selected
  if (FEATURE_ASSET_SELECTION && teamMode === "select" && selectedAssets.length === 0) {
    alert("Please select at least one team for the auction, or choose 'Include all teams'");
    return;
  }

  const leagueData = { ...form, commissionerId: user.id };
  
  // Only include assetsSelected if feature enabled and teams are selected
  if (FEATURE_ASSET_SELECTION && teamMode === "select" && selectedAssets.length > 0) {
    leagueData.assetsSelected = selectedAssets;
  }
  
  const response = await axios.post(`${API}/leagues`, leagueData);
  // ...
};
```

### UI Components

**Radio Group:**
```jsx
<label>
  <input
    type="radio"
    value="all"
    checked={teamMode === "all"}
    data-testid="rules-team-mode-include-all"
  />
  <span>Include all teams</span>
</label>

<label>
  <input
    type="radio"
    value="select"
    checked={teamMode === "select"}
    data-testid="rules-team-mode-select"
  />
  <span>Select teams for auction</span>
</label>
```

**Team Checklist (visible when teamMode === "select"):**
```jsx
<div data-testid="rules-team-checklist">
  {availableAssets
    .filter(asset => asset.name.toLowerCase().includes(assetSearchTerm.toLowerCase()))
    .map(asset => (
      <label key={asset.id}>
        <input
          type="checkbox"
          checked={selectedAssets.includes(asset.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedAssets([...selectedAssets, asset.id]);
            } else {
              setSelectedAssets(selectedAssets.filter(id => id !== asset.id));
            }
          }}
        />
        <span>{asset.name}</span>
      </label>
    ))}
</div>
```

---

## Testing Instructions

### Test 1: Feature Flag OFF (Default)

**Setup:**
1. Verify `.env` files have `FEATURE_ASSET_SELECTION=false`
2. Restart services
3. Open Create League page

**Expected:**
- ✅ No team selection UI visible
- ✅ Form looks exactly as before
- ✅ League creation works normally
- ✅ Auction uses all 36 teams (football)
- ✅ Backend logs: `mode: "all"`

**Commands:**
```bash
# Check backend .env
grep FEATURE_ASSET_SELECTION /app/backend/.env
# Should show: FEATURE_ASSET_SELECTION=false

# Check frontend .env
grep FEATURE_ASSET_SELECTION /app/frontend/.env
# Should show: REACT_APP_FEATURE_ASSET_SELECTION=false

# Restart and test
sudo supervisorctl restart all
```

### Test 2: Feature Flag ON

**Setup:**
1. Update both `.env` files to `true`
2. Restart services
3. Open Create League page

**Expected:**
- ✅ Team selection section visible
- ✅ Radio group with two options
- ✅ "Include all teams" selected by default
- ✅ Checklist hidden initially
- ✅ When "Select teams" chosen, checklist appears

**Commands:**
```bash
# Enable feature flag
echo "FEATURE_ASSET_SELECTION=true" >> /app/backend/.env
echo "REACT_APP_FEATURE_ASSET_SELECTION=true" >> /app/frontend/.env

# Restart
sudo supervisorctl restart all
```

### Test 3: Select Specific Teams (Flag ON)

**Setup:**
1. Enable feature flag
2. Create league with 2 managers, 3 slots
3. Choose "Select teams for auction"
4. Select exactly 6 teams
5. Start auction

**Expected:**
- ✅ Only 6 teams in auction queue
- ✅ After 6 teams sold, auction completes
- ✅ No lot 7 started
- ✅ Backend logs: `mode: "selected", selected_count: 6`

**Verify:**
```bash
# Check logs after auction start
grep "auction.seed_queue" /var/log/supervisor/backend.err.log | tail -1
# Should show: {"mode": "selected", "selected_count": 6}
```

### Test 4: Validation (Flag ON, No Teams Selected)

**Setup:**
1. Enable feature flag
2. Choose "Select teams for auction"
3. Don't check any teams
4. Try to submit

**Expected:**
- ❌ Alert: "Please select at least one team..."
- ❌ Form not submitted
- ✅ Can switch back to "Include all teams"
- ✅ Can then submit successfully

---

## Use Cases

### Use Case 1: Default Behavior (Flag OFF)

**Who:** All users during initial pilot  
**Why:** Simplicity, no configuration needed  
**How:** Default `.env` setting

**Result:**
- Simple create league form
- All teams available in auction
- Works for most use cases

### Use Case 2: Custom Football League (Flag ON)

**Who:** Commissioner wanting specific teams  
**Why:** "Premier League only" or "Top 10 teams"  
**Example:** Select only 10 strongest teams  

**Result:**
- Auction only offers selected 10 teams
- Faster auctions
- More focused competition

### Use Case 3: Cricket Tournament (Flag ON)

**Who:** Cricket league commissioner  
**Why:** Need specific player subset (e.g., "Batsmen only")  
**Example:** Select 15 batsmen from 50 available players  

**Result:**
- Auction offers only selected 15 players
- Specialized tournament format
- Meets specific league requirements

### Use Case 4: Small League (Flag ON)

**Who:** 2-4 managers wanting quick auction  
**Why:** Don't want to cycle through 36 teams  
**Example:** Select 9 teams for 2 managers × 3 slots  

**Result:**
- Auction queue has 9 teams (6 needed + 3 buffer)
- Quick auction completion
- Better user experience

---

## Data Model

### League Schema

```javascript
{
  id: string,
  name: string,
  sportKey: string,
  commissionerId: string,
  budget: number,
  clubSlots: number,
  // ... other fields ...
  assetsSelected: string[]  // Optional: Array of asset IDs
}
```

### When assetsSelected is Used

**Feature Flag ON:**
```javascript
// Commissioner selected 6 specific teams
assetsSelected: [
  "chelsea",
  "liverpool",
  "man-city",
  "arsenal",
  "man-utd",
  "tottenham"
]
```

**Feature Flag OFF or "Include all teams":**
```javascript
// Field absent or empty
assetsSelected: undefined
// OR
assetsSelected: []
```

---

## Logging

### Backend Logs

**When using all teams:**
```json
{
  "event": "auction.seed_queue",
  "mode": "all",
  "selected_count": 36,
  "leagueId": "abc123",
  "sport": "football",
  "feature_enabled": false
}
```

**When using selected teams:**
```json
{
  "event": "auction.seed_queue",
  "mode": "selected",
  "selected_count": 6,
  "leagueId": "abc123",
  "sport": "football"
}
```

### How to Monitor

```bash
# Check if feature is being used
grep "auction.seed_queue" /var/log/supervisor/backend.err.log | jq .mode

# Count usage by mode
grep "auction.seed_queue" /var/log/supervisor/backend.err.log | grep -c "\"mode\": \"selected\""
grep "auction.seed_queue" /var/log/supervisor/backend.err.log | grep -c "\"mode\": \"all\""
```

---

## Migration Path

### Phase 1: Pilot (Current)

**Status:** Feature flag OFF  
**Users:** All pilot users  
**Behavior:** Use all teams (default)  
**Duration:** 1-2 weeks

**Goal:** Validate core auction completion fix

### Phase 2: Beta Testing

**Status:** Feature flag ON for specific leagues  
**Users:** 2-3 test commissioners  
**Behavior:** Can optionally select teams  
**Duration:** 1 week

**Goal:** Validate team selection works correctly

### Phase 3: General Availability

**Status:** Feature flag ON by default  
**Users:** All users  
**Behavior:** Team selection available to all  
**Duration:** Ongoing

**Goal:** Full feature rollout

---

## Rollback Plan

### Quick Disable

**If issues occur with team selection:**

```bash
# Disable feature flag (both environments)
sed -i 's/FEATURE_ASSET_SELECTION=true/FEATURE_ASSET_SELECTION=false/' /app/backend/.env
sed -i 's/REACT_APP_FEATURE_ASSET_SELECTION=true/REACT_APP_FEATURE_ASSET_SELECTION=false/' /app/frontend/.env

# Restart services
sudo supervisorctl restart all
```

**Result:**
- Team selection UI disappears
- All auctions use all teams
- No data migration needed
- Existing leagues with `assetsSelected` ignored

### Rollback Triggers

**Disable feature if:**
- ❌ Team selection causes auction start failures
- ❌ Selected teams not loading correctly
- ❌ UI bugs preventing league creation
- ❌ Performance issues with large team lists

---

## Future Enhancements

### Short-Term (Week 2-3)

1. **Quick Select Presets**
   - "Top 10 teams"
   - "Bottom 10 teams"
   - "Random 10 teams"

2. **Team Sorting**
   - Sort by name
   - Sort by overall rating
   - Group by conference/division

3. **Bulk Actions**
   - "Select all"
   - "Clear all"
   - "Select first N teams"

### Medium-Term (Month 2)

4. **Save/Load Team Sets**
   - "Premier League Top 6"
   - "Championship Teams"
   - "My Custom Set"

5. **Team Preview**
   - Show team stats in checklist
   - Display team ratings
   - Visual preview

6. **Smart Recommendations**
   - "Recommended for 2 managers × 3 slots: 9 teams"
   - Auto-suggest appropriate count

---

## Performance Considerations

### Impact of Feature Flag

**With Flag OFF:**
- Zero overhead
- Code path unchanged
- No additional queries

**With Flag ON:**
- +1 API call to fetch available teams (frontend)
- Cached in component state
- Re-fetched only when sport changes
- Minimal UI overhead (hidden by default)

### Database Queries

**All Teams Mode:**
```javascript
db.clubs.find()  // ~36 clubs for football
```

**Selected Teams Mode:**
```javascript
db.clubs.find({"id": {"$in": selectedIds}})  // 6-10 clubs typically
```

**Impact:** Selected mode is actually FASTER (fewer documents)

---

## Files Modified

### Backend
1. `/app/backend/.env` - Added FEATURE_ASSET_SELECTION flag
2. `/app/backend/server.py` - Feature flag logic and auction seed

### Frontend
1. `/app/frontend/.env` - Added REACT_APP_FEATURE_ASSET_SELECTION flag
2. `/app/frontend/src/pages/CreateLeague.js` - Team selection UI

**Total Changes:**
- Backend: ~40 lines added
- Frontend: ~150 lines added
- Net: ~190 lines new code

---

## Acceptance Criteria

### With Flag OFF (Default)

- ✅ No team selection UI visible
- ✅ League creation works exactly as before
- ✅ Auctions use all available teams
- ✅ No breaking changes
- ✅ Logs show `mode: "all"`

### With Flag ON

- ✅ Team selection section visible in form
- ✅ Radio group with "Include all" selected by default
- ✅ "Select teams" shows searchable checklist
- ✅ Selected teams persisted to database
- ✅ Auction uses only selected teams
- ✅ Completion logic works correctly
- ✅ Logs show `mode: "selected"`

### Edge Case: 6 Teams for 2×3 Slots

- ✅ Auction offers exactly 6 teams
- ✅ After 6 wins, auction completes
- ✅ No lot 7 started
- ✅ Completion triggered correctly

---

**Feature Status:** ✅ DEPLOYED (Flag OFF by default)  
**Ready for:** Pilot testing with flag OFF, beta testing with flag ON  
**Production Safe:** Yes (feature hidden unless enabled)
