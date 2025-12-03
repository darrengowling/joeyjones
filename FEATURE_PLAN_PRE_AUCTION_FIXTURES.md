# Feature Plan: Optional Pre-Auction Fixture Import

**Status:** Planned for post-deployment implementation  
**Priority:** P2 (After group testing completes)  
**Complexity:** Low (UI addition only, backend endpoints already exist)

---

## 🎯 Goal

Enable commissioners to **optionally** import fixtures BEFORE starting an auction, so participants can see upcoming opponents during bidding and make strategic decisions.

**Example:** "I won't bid high for Arsenal if their next match is vs Manchester City (H)"

---

## 📋 Decision: Option 3 - Optional Pre-Auction Import

### Why Optional?
- ✅ Backward compatible (current post-auction flow still works)
- ✅ Commissioner choice (some competitions don't need it)
- ✅ No wasted API calls on test/abandoned auctions
- ✅ Flexible for different competition types

### When to Use?
- **Football:** Single-match or short-season competitions where opponents matter
- **Cricket - Yes:** Tournaments like IPL with multiple teams
- **Cricket - No:** Series like The Ashes (always AUS vs ENG, no need)

---

## 🔧 Implementation Plan

### 1. UI Changes (LeagueDetail.js)

**Location:** After player selection, BEFORE "Begin Strategic Competition" button

**When to show:**
- `league.status === "pending"`
- `isCommissioner === true`

**What to show:**

```jsx
{/* Optional: Import Fixtures Before Auction */}
{league.status === "pending" && isCommissioner && (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
    <div className="flex items-start gap-3">
      <span className="text-2xl">💡</span>
      <div className="flex-1">
        <h3 className="font-semibold text-gray-900 mb-2">
          Import Fixtures Before Auction (Optional)
        </h3>
        <p className="text-sm text-gray-600 mb-3">
          Import fixtures now so managers can see upcoming opponents during bidding. 
          This helps strategic decisions—for example, avoiding teams facing tough matches.
        </p>
        
        {/* Show loading state */}
        {importingFixtures ? (
          <div className="text-sm text-blue-600">Importing fixtures...</div>
        ) : fixturesImported ? (
          <div className="text-sm text-green-600 flex items-center gap-2">
            <span>✅</span> Fixtures imported successfully
          </div>
        ) : (
          <div className="flex gap-3">
            {league.sportKey === 'football' && (
              <button 
                onClick={handleImportFootballFixtures}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                Import Football Fixtures
              </button>
            )}
            
            {league.sportKey === 'cricket' && (
              <button 
                onClick={handleImportCricketFixture}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                Import Next Cricket Match
              </button>
            )}
            
            <button 
              onClick={() => setShowFixtureCard(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium"
            >
              Skip for Now
            </button>
          </div>
        )}
        
        <p className="text-xs text-gray-500 mt-3">
          You can skip this and import fixtures later from the Competition Dashboard after the auction.
        </p>
      </div>
    </div>
  </div>
)}
```

---

### 2. Frontend Logic (LeagueDetail.js)

**New State Variables:**
```javascript
const [importingFixtures, setImportingFixtures] = useState(false);
const [fixturesImported, setFixturesImported] = useState(false);
const [showFixtureCard, setShowFixtureCard] = useState(true);
```

**Handler Functions:**
```javascript
const handleImportFootballFixtures = async () => {
  setImportingFixtures(true);
  try {
    const response = await axios.post(
      `${API}/leagues/${leagueId}/fixtures/import-from-api`,
      { days: 7 } // Import next 7 days of fixtures
    );
    setFixturesImported(true);
    // Show success message
    alert(`✅ Imported ${response.data.fixturesImported || 0} fixtures successfully`);
  } catch (error) {
    console.error("Error importing fixtures:", error);
    alert("❌ Failed to import fixtures. You can try again later from the Competition Dashboard.");
  } finally {
    setImportingFixtures(false);
  }
};

const handleImportCricketFixture = async () => {
  setImportingFixtures(true);
  try {
    const response = await axios.post(
      `${API}/leagues/${leagueId}/fixtures/import-next-cricket-fixture`
    );
    setFixturesImported(true);
    alert(`✅ Imported next cricket fixture successfully`);
  } catch (error) {
    console.error("Error importing fixture:", error);
    alert("❌ Failed to import fixture. You can try again later from the Competition Dashboard.");
  } finally {
    setImportingFixtures(false);
  }
};
```

---

### 3. Backend Changes

**NO CHANGES NEEDED** - Endpoints already exist:
- ✅ `POST /leagues/{league_id}/fixtures/import-from-api` (football)
- ✅ `POST /leagues/{league_id}/fixtures/import-next-cricket-fixture` (cricket)

---

### 4. AuctionRoom Display

**Current Code (Already Works):**
```javascript
// When currentClub changes, load next fixture
useEffect(() => {
  if (currentClub && currentClub.id) {
    loadNextFixture(currentClub.id);
  } else {
    setNextFixture(null);
  }
}, [currentClub]);

const loadNextFixture = async (assetId) => {
  try {
    const response = await axios.get(`${API}/assets/${assetId}/next-fixture`);
    if (response.data.fixture) {
      setNextFixture(response.data.fixture);
    } else {
      setNextFixture(null);
    }
  } catch (error) {
    setNextFixture(null); // Fail gracefully
  }
};
```

**Display (Already Compressed):**
```javascript
{nextFixture && (
  <div className="text-sm text-gray-600 mb-4">
    Next match: {nextFixture.opponent} ({nextFixture.isHome ? 'H' : 'A'})
  </div>
)}
```

**✅ No changes needed** - Will automatically display if fixtures exist

---

## 🧪 Testing Plan

### Test Cases:

1. **Football - Import Before Auction**
   - Create football league
   - Import fixtures (7 days)
   - Start auction
   - Verify "Next match: [Team] (H/A)" displays for each team
   - Complete auction
   - Verify scoring still works

2. **Football - Skip Import**
   - Create football league
   - Click "Skip for Now"
   - Start auction
   - Verify no "Next match" displays (graceful)
   - Complete auction
   - Import fixtures from Competition Dashboard (existing flow)
   - Verify it works

3. **Cricket - Import Before Auction (IPL-style)**
   - Create cricket league
   - Import next fixture
   - Start auction
   - Verify "Next match: [Team] (H/A)" displays
   - Complete auction

4. **Cricket - Skip Import (Ashes-style)**
   - Create Ashes league
   - Click "Skip for Now" (not needed for AUS vs ENG)
   - Start auction
   - Verify no display
   - Complete auction

5. **API Error Handling**
   - Create league
   - Disconnect from internet / break API key
   - Try to import fixtures
   - Verify error message is user-friendly
   - Verify "Skip" option still works
   - Verify auction can proceed without fixtures

---

## 📊 Impact Analysis

### User Experience:
- ✅ Adds strategic depth to bidding
- ✅ Optional = no disruption to current workflow
- ✅ Clear value proposition in UI

### Technical Impact:
- ✅ Zero API call increase (same total, just timing shifts)
- ✅ No breaking changes
- ✅ Backward compatible
- ✅ Low complexity (UI addition only)

### Testing Impact:
- ✅ Being optional avoids wasting API calls on test/abandoned auctions
- ✅ Commissioners creating 100s of tests won't trigger imports unless they choose to

---

## 🚀 Implementation Steps

### Phase 1: UI Implementation
1. Add fixture import card to LeagueDetail.js
2. Add state management (importing, imported, show/hide)
3. Add handler functions for both sports
4. Add "Skip for Now" functionality

### Phase 2: Testing
1. Manual testing of all 5 test cases above
2. Test with real API keys (Football-Data.org, Cricbuzz)
3. Test error scenarios
4. Test mobile responsiveness

### Phase 3: Documentation
1. Update Help.js user guide (add pre-auction import option)
2. Update README.md with new workflow
3. Take screenshots for documentation

---

## 📝 Estimated Effort

- **Development:** 1-2 hours
- **Testing:** 1 hour
- **Documentation:** 30 minutes
- **Total:** 2.5-3.5 hours

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Commissioner forgets to import | ✅ Still works - can import later (current flow) |
| API calls fail during import | ✅ Error handling shows friendly message, auction proceeds |
| Fixtures change after import | ℹ️ Acceptable - fixtures are snapshot at import time |
| Commissioner confused by option | ✅ Clear explanation + "Skip" option in UI |

---

## 🎯 Success Criteria

Feature is successful when:
- ✅ Commissioners can import fixtures before auctions
- ✅ "Next match: X (H/A)" displays during auction when fixtures exist
- ✅ Skipping import doesn't break anything
- ✅ Current post-auction workflow still works
- ✅ No increase in total API calls
- ✅ User feedback confirms it adds strategic value

---

## 📅 Implementation Timeline

**WAIT FOR:**
- ✅ Group testing to complete
- ✅ Deployment to succeed
- ✅ User feedback on current functionality

**THEN IMPLEMENT:**
- Post-testing phase (likely 1-2 weeks after deployment)
- Low priority compared to critical bug fixes

---

**This document will be reference for implementation after deployment completes.**
