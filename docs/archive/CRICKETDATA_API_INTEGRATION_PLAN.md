# CricketData API Integration - Pre-Implementation Testing Plan

**Date**: 2025-10-25  
**Status**: ⚠️ **PLANNING PHASE - DO NOT IMPLEMENT YET**  
**Decision Point**: After today's auction, before NZ vs England ODI (tomorrow)

---

## 🎯 Goal

Integrate CricketData.org API for automatic live scoring updates to replace manual CSV uploads.

---

## ⚠️ CRITICAL CONTEXT: Previous Failures

**What Went Wrong Before:**
- Auto-updater integration broke the app
- Led to multiple rollbacks
- Caused stability issues over last few days
- Resulted in extended debugging and fixes

**Lessons Learned:**
- ✅ Test thoroughly before implementing
- ✅ Implement feature flag for instant rollback
- ✅ Keep manual CSV as fallback
- ✅ Test in isolation before integrating
- ✅ Have clear rollback plan

---

## 📋 Phase 1: API Testing (DO FIRST - Before Implementation)

### Test 1: API Connectivity & Authentication

**Goal**: Verify your API key works and understand response format

**Actions**:
```bash
# Test 1.1: Basic API connection
curl -X GET "https://api.cricketdata.org/endpoint" \
  -H "apikey: YOUR_API_KEY"

# Expected: 200 OK response with data

# Test 1.2: Check rate limits
# Document: Requests per minute/hour/day allowed

# Test 1.3: Check available endpoints
# Document: Which endpoints provide match scores, player stats
```

**Document**:
- [ ] API base URL
- [ ] Authentication method (header? query param?)
- [ ] Rate limits (calls per minute/hour)
- [ ] Available endpoints for live scores
- [ ] Response format (JSON structure)

---

### Test 2: Match Data Availability

**Goal**: Confirm NZ vs England ODI data will be available

**Actions**:
```bash
# Test 2.1: List upcoming matches
curl -X GET "https://api.cricketdata.org/matches?status=upcoming"

# Test 2.2: Search for NZ vs England series
# Look for: match IDs, team IDs, player IDs

# Test 2.3: Check if live scores available
# Test with a currently live match (if any)
```

**Document**:
- [ ] Match ID format from API
- [ ] How to get NZ vs England specific matches
- [ ] Player identification method (names? IDs?)
- [ ] Update frequency (real-time? 5min intervals?)

---

### Test 3: Data Mapping

**Goal**: Map CricketData API response to our schema

**Our Schema** (What we need):
```csv
matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
```

**API Response** (What they provide):
```json
{
  // Document actual structure from API
  "match": {
    "id": "...",
    "players": [
      {
        "name": "Harry Brook",
        "batting": { "runs": 75, "balls": 82 },
        "bowling": { "wickets": 0 },
        "fielding": { "catches": 1, "stumpings": 0, "runOuts": 0 }
      }
    ]
  }
}
```

**Mapping Challenge**:
```
API Player Name → Our externalId
"Harry Brook" → "harry-brook"

How to handle:
- Name variations (Jos Buttler vs Joseph Buttler)
- Missing stats (some players don't bat/bowl)
- Match status (in progress vs completed)
```

**Document**:
- [ ] Exact API response structure
- [ ] How to extract runs, wickets, catches, stumpings, runOuts
- [ ] Player name matching strategy
- [ ] Edge cases (DNP, retired hurt, etc.)

---

### Test 4: Real Match Simulation

**Goal**: Test with actual live/recent match data

**Actions**:
```bash
# Find a completed ODI match from last week
# Fetch the data
# Manually convert to our CSV format
# Compare with official scorecard

# Questions to answer:
# - Are stats accurate?
# - Are all players included?
# - Do wicket-keepers get stumping credits?
# - Are run-outs attributed correctly?
```

**Document**:
- [ ] Data accuracy (compare with Cricinfo/Cricbuzz)
- [ ] Completeness (all players present?)
- [ ] Edge cases discovered
- [ ] Time to fetch data after match ends

---

## 📋 Phase 2: Technical Design (After API Testing)

### Architecture Options

**Option A: Polling (Safer)**
```
Every 5 minutes:
1. Check if match is live
2. Fetch latest scores
3. Update our database
4. Recalculate leaderboard

Pros: Simple, predictable, easy to debug
Cons: Not real-time, API calls even when no match
```

**Option B: Webhooks (If Supported)**
```
CricketData sends us updates when:
- Match starts
- Score changes
- Match ends

Pros: Real-time, efficient
Cons: Complex, need public endpoint, harder to debug
```

**Option C: Hybrid**
```
Manual trigger by commissioner:
- Button: "Fetch Latest Scores"
- Runs on-demand
- Commissioner controls timing

Pros: Full control, no background jobs
Cons: Not automatic, commissioner involvement
```

**Recommendation**: Start with **Option C (Hybrid)** for safety

---

### Implementation Isolation

**Create Separate Service** (Don't touch existing code):
```python
# NEW FILE: backend/services/cricket_data_service.py

class CricketDataService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cricketdata.org"
    
    async def fetch_match_scores(self, match_id: str):
        """Fetch scores from CricketData API"""
        # Implementation here
        pass
    
    async def convert_to_csv_format(self, api_response):
        """Convert API response to our CSV schema"""
        # Implementation here
        pass

# NEW ENDPOINT: POST /api/scoring/{leagueId}/fetch-live
# Only accessible to commissioner
# Calls CricketDataService
# Falls back to manual CSV if fails
```

**Benefits**:
- Isolated from existing code
- Easy to disable
- Can test independently
- Doesn't affect manual CSV upload

---

### Feature Flag Strategy

```python
# backend/.env
CRICKET_LIVE_SCORING_ENABLED=false  # Start disabled
CRICKETDATA_API_KEY=your_actual_key
CRICKETDATA_BASE_URL=https://api.cricketdata.org

# backend/server.py
CRICKET_LIVE_SCORING = os.getenv('CRICKET_LIVE_SCORING_ENABLED', 'false').lower() == 'true'

if not CRICKET_LIVE_SCORING:
    # Hide "Fetch Live Scores" button
    # Only show manual CSV upload
```

**Rollback**: Set flag to `false` and restart backend (30 seconds)

---

## 📋 Phase 3: Risk Assessment

### What Could Break:

**1. Wrong Player Mapping**
```
Risk: "Harry Brook" from API doesn't match "harry-brook" in our DB
Impact: Player gets 0 points, users complain
Mitigation: 
- Pre-map all 30 players (manual mapping table)
- Log unmatched players
- Manual override capability
```

**2. Incomplete Data**
```
Risk: API missing stumpings/run-outs data
Impact: Wicket-keepers get fewer points than deserved
Mitigation:
- Compare with official scorecard
- Allow manual corrections
- Document API limitations
```

**3. API Downtime**
```
Risk: API unavailable during match
Impact: No score updates
Mitigation:
- Keep manual CSV upload available
- Retry logic with backoff
- Commissioner notification
```

**4. Rate Limiting**
```
Risk: Hit API rate limit during live match
Impact: Updates stop
Mitigation:
- Cache responses
- Smart polling (only when match live)
- Upgrade API plan if needed
```

**5. Incorrect Score Updates**
```
Risk: API gives wrong scores, overwrite correct data
Impact: Wrong leaderboard, user complaints
Mitigation:
- Show diff before applying
- Commissioner approval required
- Keep audit log
```

---

## 📋 Phase 4: Testing Checklist (Before Go-Live)

### Pre-Implementation Tests

- [ ] **API Key Works**: Test authentication successful
- [ ] **Match Data Available**: Confirm NZ vs England matches visible in API
- [ ] **Player Mapping**: All 30 players mapped correctly
- [ ] **Data Accuracy**: Compare API data with official scorecard
- [ ] **Response Time**: API responds within 2 seconds
- [ ] **Rate Limits**: Understand and documented
- [ ] **Error Handling**: Test with invalid match ID, bad auth, timeout

### Post-Implementation Tests (Staging)

- [ ] **Fetch Button Works**: Commissioner can click "Fetch Live Scores"
- [ ] **Data Conversion**: API response converts to correct CSV format
- [ ] **Points Calculation**: Scores calculate correctly (spot check 3 players)
- [ ] **Leaderboard Update**: Leaderboard updates after fetch
- [ ] **Manual Fallback**: CSV upload still works if API fetch fails
- [ ] **Feature Flag**: Disabling flag hides fetch button
- [ ] **No Regression**: Existing manual CSV upload unaffected

### During Live Match (NZ vs ENG ODI 1)

- [ ] **Real-Time Test**: Fetch scores during match
- [ ] **Accuracy Check**: Compare with live TV/Cricinfo
- [ ] **Performance**: No slowdown or errors
- [ ] **Commissioner UX**: Easy to use, clear feedback
- [ ] **Rollback Ready**: Can disable and use manual CSV immediately

---

## 📋 Phase 5: Go/No-Go Decision Framework

### ✅ GO Criteria (Safe to Implement)

**All of these must be TRUE**:
1. ✅ API testing complete and successful
2. ✅ All 30 players mapped correctly
3. ✅ Data accuracy verified (98%+ match with official scorecard)
4. ✅ Implementation isolated (separate service, feature flag)
5. ✅ Manual CSV still works as fallback
6. ✅ Rollback tested and working (< 1 minute)
7. ✅ Commissioner comfortable with hybrid approach
8. ✅ No critical bugs in current stable version
9. ✅ Time to test before ODI 1 (at least 4 hours)

### ❌ NO-GO Criteria (Stick with Manual CSV)

**Any of these is TRUE**:
1. ❌ API key doesn't work or rate limits too restrictive
2. ❌ Player mapping incomplete or unreliable
3. ❌ Data accuracy < 95%
4. ❌ Current app has stability issues
5. ❌ Not enough time to test properly
6. ❌ Commissioner uncomfortable with auto-updates
7. ❌ Unable to keep manual CSV as fallback

### 🟡 DEFER Criteria (Decide After ODI 1)

**Consider these**:
- Use manual CSV for ODI 1
- Test API integration during match
- Implement for ODI 2 & 3 if successful
- Reduces risk for first match

---

## 📋 Phase 6: Implementation Plan (If GO)

### Step 1: Create Cricket Data Service (1 hour)
```python
# File: backend/services/cricket_data_service.py
# - API client wrapper
# - Authentication
# - Error handling
# - Rate limiting
```

### Step 2: Create Mapping Table (30 minutes)
```python
# File: backend/services/player_mapping.py
CRICKETDATA_TO_EXTERNAL_ID = {
    "Harry Brook": "harry-brook",
    "Joe Root": "joe-root",
    # ... all 30 players
}
```

### Step 3: Add Fetch Endpoint (1 hour)
```python
# backend/server.py
@api_router.post("/scoring/{leagueId}/fetch-live")
async def fetch_live_scores(league_id: str, match_id: str):
    # Only if CRICKET_LIVE_SCORING_ENABLED
    # Call CricketDataService
    # Convert to CSV format
    # Use existing ingest logic
    # Return success/error
```

### Step 4: Add Frontend Button (30 minutes)
```jsx
// frontend/src/pages/CompetitionDashboard.js
{CRICKET_LIVE_SCORING_ENABLED && (
  <button onClick={handleFetchLiveScores}>
    🔄 Fetch Live Scores from CricketData
  </button>
)}
```

### Step 5: Test in Staging (2 hours)
- Run through all test scenarios
- Verify accuracy with test match
- Test rollback

### Step 6: Deploy with Flag OFF (15 minutes)
- Deploy to production
- Flag disabled
- No user-facing changes

### Step 7: Enable Flag (After Testing)
- Enable flag
- Restart backend
- Test fetch button
- Monitor for issues

**Total Time**: ~5 hours (if API testing already done)

---

## 📋 Phase 7: Rollback Plan

### Quick Rollback (30 seconds)
```bash
# Set flag to false
CRICKET_LIVE_SCORING_ENABLED=false

# Restart backend
sudo supervisorctl restart backend

# Result: Fetch button disappears, manual CSV still works
```

### Full Rollback (5 minutes)
```bash
# Remove new endpoint
# Remove CricketDataService
# Remove frontend button
# Redeploy

# Result: Back to 100% manual CSV
```

---

## 📋 Recommended Timeline

**Today (Before Auction)**:
- ✅ Share API key with me (secure method)
- ✅ Run Phase 1 API tests (30 minutes)
- ✅ Document findings

**After Auction (Today Evening)**:
- Review API test results
- Make GO/NO-GO decision
- If GO: Start implementation (5 hours)
- If NO-GO: Stick with manual CSV (proven & stable)

**Tomorrow Morning (Before ODI 1)**:
- If implemented: Test fetch functionality
- If working: Use for ODI 1
- If issues: Disable flag, use manual CSV

---

## 📝 Decision Matrix

| Scenario | Recommendation | Reasoning |
|----------|----------------|-----------|
| **API tests perfect, 4+ hours available** | ✅ GO | Safe to implement with proper testing |
| **API tests perfect, < 4 hours available** | 🟡 DEFER | Use manual for ODI 1, implement for ODI 2 |
| **API tests show issues** | ❌ NO-GO | Stick with proven manual CSV |
| **Any stability concerns** | ❌ NO-GO | Don't risk breaking stable app |
| **Commissioner uncertain** | ❌ NO-GO | Commissioner must be confident |

---

## 🎯 My Recommendation

**Conservative Approach** (Lowest Risk):
1. Run API tests today
2. Use **manual CSV for ODI 1** (tomorrow)
3. Implement auto-fetch during ODI 1 (test with live match)
4. Use auto-fetch for **ODI 2 & 3** if successful

**Benefits**:
- ✅ Proven system for first match
- ✅ Real-world testing with live match
- ✅ Learn API behavior during actual match
- ✅ Still get auto-updates for 2 of 3 matches
- ✅ Zero risk to tournament

**Aggressive Approach** (Higher Risk, Higher Reward):
1. Run API tests today (after auction)
2. Implement tonight if tests pass
3. Use auto-fetch for all 3 ODIs
4. Manual CSV as fallback if issues

**Benefits**:
- ✅ Full automation for all matches
- ✅ Showcase app's key advantage
- ⚠️ Risk of issues during tournament

---

## 📞 Next Steps

**After Today's Auction, You Decide**:

1. **Share API Key** (if you want to test)
2. **I Run API Tests** (30 minutes)
3. **Review Results Together**
4. **Make GO/NO-GO Decision**
5. **Either**: Implement (if GO) **OR** Document for future (if NO-GO)

**Your Call** - I'll support whatever you decide! 👍

---

**Document Status**: Ready for Review  
**Waiting For**: Auction completion + your decision
