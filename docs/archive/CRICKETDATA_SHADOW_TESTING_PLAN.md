# CricketData API Shadow Testing - ODI 1 Test Plan

**Date**: ODI 1 (Oct 26, 2025)  
**Goal**: Test API without integrating into live app  
**Method**: Standalone testing script + manual comparison

---

## 🎯 Testing Approach: Shadow Testing

**Concept**: 
- Run API tests in parallel to your manual CSV process
- Compare API data with official scorecard
- Identify issues WITHOUT affecting the live app
- Manual CSV remains your production system

**Zero Risk**: Live app untouched, users unaffected

---

## 📋 Method 1: Standalone Python Test Script

**I'll create a simple test script that runs independently**:

```python
# File: /app/scripts/test_cricketdata_api.py

import requests
import json
from datetime import datetime

class CricketDataAPITester:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.cricketdata.org"  # Adjust to actual
        self.results = []
    
    def test_match_fetch(self, match_id):
        """Fetch live match data"""
        print(f"\n🔍 Fetching match: {match_id}")
        print(f"⏰ Time: {datetime.now()}")
        
        try:
            response = requests.get(
                f"{self.base_url}/matches/{match_id}",
                headers={"apikey": self.api_key},
                timeout=10
            )
            
            print(f"✅ Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.analyze_response(data)
                self.save_snapshot(data)
                return data
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    def analyze_response(self, data):
        """Analyze API response structure"""
        print("\n📊 Response Analysis:")
        print(f"- Keys: {list(data.keys())}")
        
        # Try to find player stats
        if 'players' in data:
            print(f"- Players found: {len(data['players'])}")
            if data['players']:
                sample = data['players'][0]
                print(f"- Sample player keys: {list(sample.keys())}")
        
        # Try to find scores
        if 'scores' in data:
            print(f"- Scores structure: {type(data['scores'])}")
    
    def save_snapshot(self, data):
        """Save API response for later analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/artifacts/api_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved to: {filename}")
    
    def convert_to_csv(self, data):
        """Test conversion to our CSV format"""
        print("\n🔄 Testing CSV Conversion:")
        
        csv_rows = []
        # Attempt to extract players and stats
        # This is where we'll discover the actual structure
        
        print(f"- Would generate {len(csv_rows)} CSV rows")
        return csv_rows
    
    def compare_with_official(self, api_data, official_scorecard):
        """Compare API data with official scorecard"""
        print("\n⚖️  Comparison Analysis:")
        # Manual comparison function
        pass

# Usage during ODI 1
if __name__ == "__main__":
    # Replace with your actual API key
    API_KEY = "your_cricketdata_api_key"
    
    tester = CricketDataAPITester(API_KEY)
    
    # Test with NZ vs England ODI 1
    # Replace with actual match ID from CricketData
    MATCH_ID = "nz-eng-odi-1-2025"  
    
    # Run test
    data = tester.test_match_fetch(MATCH_ID)
    
    if data:
        tester.convert_to_csv(data)
```

**How to Use**:
```bash
# During ODI 1, run this every 15-30 minutes
python /app/scripts/test_cricketdata_api.py

# Saves snapshots to /app/artifacts/
# No impact on live app
```

---

## 📋 Method 2: Manual Testing Checklist

**During ODI 1 (Tomorrow 2:00 PM UTC)**:

### Pre-Match (1:30 PM UTC)
- [ ] Run script to test API authentication
- [ ] Verify match ID is available in API
- [ ] Check if pre-match data available (team lineups)
- [ ] Document API response structure

### During Match (2:00 PM - 6:00 PM UTC)
**Every 30 minutes**:
- [ ] Run test script to fetch live scores
- [ ] Save API snapshot
- [ ] Note what's available (runs? wickets? catches?)
- [ ] Check if player stats updating
- [ ] Compare with TV/Cricinfo scorecard
- [ ] Document any discrepancies

### Post-Match (After 6:00 PM UTC)
- [ ] Run final fetch
- [ ] Get complete scorecard from API
- [ ] Compare with official scorecard (Cricinfo/Cricbuzz)
- [ ] Calculate accuracy percentage
- [ ] Note any missing stats (stumpings? run-outs?)
- [ ] Document conversion challenges

---

## 📋 Method 3: Comparison Spreadsheet

**Create a comparison table**:

| Player | Official Runs | API Runs | Match? | Official Wickets | API Wickets | Match? |
|--------|---------------|----------|--------|------------------|-------------|--------|
| Harry Brook | 75 | ? | ? | 0 | ? | ? |
| Jofra Archer | 12 | ? | ? | 3 | ? | ? |
| Kane Williamson | 89 | ? | ? | 0 | ? | ? |

**Fill in during/after match**:
1. Official column: From TV/Cricinfo (your manual CSV source)
2. API column: From test script output
3. Match?: Are they identical?

**Calculate Accuracy**:
```
Total fields: 30 players × 5 stats = 150 data points
Matches: Count how many match exactly
Accuracy: (Matches / Total) × 100%

Goal: >95% accuracy
```

---

## 📋 Method 4: Live Observation Notes

**Document during the match**:

```markdown
# ODI 1 API Testing Notes

## 2:00 PM - Match Start
- [ ] API shows match as "live"?
- [ ] Initial scores available?
- [ ] Response time: ___ seconds

## 2:30 PM - 10 Overs
- [ ] Stats updating?
- [ ] Harry Brook: TV shows 25 runs, API shows ___
- [ ] Delay between TV and API: ___ minutes

## 3:00 PM - 20 Overs  
- [ ] First wicket: TV shows Archer 1-15, API shows ___
- [ ] Catches credited correctly?

## 4:00 PM - 30 Overs
- [ ] Detailed stats available?
- [ ] Stumpings tracked? (if any)
- [ ] Run-outs tracked? (if any)

## 6:00 PM - Match End
- [ ] Final scorecard available within ___ minutes
- [ ] All players included?
- [ ] All stats match official scorecard?
```

---

## 📋 Method 5: Player Mapping Test

**Test player name matching**:

```python
# Create mapping file
PLAYER_MAPPING = {
    # API Name : Our externalId
    "Harry Brook": "harry-brook",
    "Jos Buttler": "jos-buttler",
    "Joe Root": "joe-root",
    # ... all 30 players
}

# Test function
def test_player_matching(api_player_name):
    """Test if API player name maps to our database"""
    if api_player_name in PLAYER_MAPPING:
        our_id = PLAYER_MAPPING[api_player_name]
        print(f"✅ {api_player_name} → {our_id}")
        
        # Check if exists in our database
        # query: db.assets.find_one({"externalId": our_id})
        return True
    else:
        print(f"❌ {api_player_name} → NO MATCH")
        return False

# Run for all players in API response
for player in api_response['players']:
    test_player_matching(player['name'])
```

---

## 📋 What We Learn from Shadow Testing

**After ODI 1, we'll know**:

1. **API Reliability**
   - Does it work during live match?
   - Response times acceptable?
   - Any downtime/errors?

2. **Data Completeness**
   - All stats available (runs, wickets, catches)?
   - Stumpings tracked?
   - Run-outs attributed correctly?

3. **Data Accuracy**
   - How closely matches official scorecard?
   - Any systematic errors?
   - Edge cases handled?

4. **Player Mapping**
   - Can we match all 30 players?
   - Name variations?
   - Any unmapped players?

5. **Timing**
   - How fresh is the data?
   - Delay from live action?
   - When does final scorecard appear?

6. **Technical Issues**
   - Rate limiting problems?
   - Authentication issues?
   - Response format as expected?

---

## 📋 Decision Framework After ODI 1

### ✅ GO for ODI 2 & 3 if:
- Accuracy >95%
- All 30 players mapped successfully
- No API downtime during match
- Stats complete (including stumpings/run-outs)
- Conversion to CSV format straightforward
- Response times <5 seconds

### 🟡 MODIFY Approach if:
- Accuracy 90-95% (need to identify issues)
- Some players unmapped (create manual overrides)
- Minor data delays (adjust polling frequency)
- Missing some stats (document limitations)

### ❌ STICK WITH MANUAL if:
- Accuracy <90%
- API downtime during match
- Critical stats missing (stumpings/run-outs)
- Player mapping unreliable
- Data quality concerns

---

## 🔧 What You'll Do During ODI 1

**Your Manual Process (Production)**:
1. Watch match/check scorecard
2. Fill in CSV manually (as planned)
3. Upload CSV to app
4. Users see updated leaderboard

**My Shadow Testing (Background)**:
1. Run test script every 30 minutes
2. Save API responses
3. Compare with your CSV data
4. Document findings

**After Match**:
1. Compare API snapshots with your CSV
2. Calculate accuracy
3. Review notes together
4. Make GO/NO-GO decision for ODI 2

---

## 📁 Deliverables from Testing

After ODI 1, I'll provide:

1. **API Test Report**
   - Accuracy percentage
   - All API response samples
   - Player mapping validation
   - Timing analysis

2. **Comparison Spreadsheet**
   - Side-by-side: Official vs API
   - Discrepancies highlighted
   - Missing data noted

3. **Technical Assessment**
   - API reliability score
   - Data completeness score
   - Implementation feasibility rating

4. **GO/NO-GO Recommendation**
   - Clear decision with reasoning
   - Risk assessment if GO
   - Implementation time estimate if GO

---

## 🎯 Benefits of This Approach

**Zero Risk Testing**:
- ✅ Live app completely unaffected
- ✅ Manual CSV is your production system
- ✅ Test with real match data
- ✅ Learn API behavior in action
- ✅ Make informed decision for ODI 2

**Real-World Validation**:
- ✅ Not just sample data - actual tournament match
- ✅ Test under real conditions
- ✅ Discover edge cases
- ✅ Validate player mapping with live data

**Time Efficient**:
- ✅ Testing runs in background
- ✅ You focus on manual CSV (as planned)
- ✅ No implementation work wasted if API unsuitable
- ✅ Quick decision after match

---

## 📞 What I Need from You

**Before ODI 1 (Tomorrow)**:
1. Your CricketData API key
2. How to access match data (endpoint URL if you know it)
3. Any documentation from CricketData about ODI matches

**During ODI 1**:
- Nothing! Focus on your manual CSV
- I'll run tests in background

**After ODI 1**:
- 30 minutes to review results together
- Decide: GO for ODI 2 or STICK with manual

---

## ✅ Summary

**You asked**: "How do we test without integrating?"

**Answer**: Shadow testing with standalone script
- Runs completely separately from live app
- No code changes to production
- Tests real match data
- Compares with your manual CSV
- Zero risk to users

**Timeline**:
- Tomorrow: Manual CSV (production) + Shadow testing (background)
- After match: Review and decide
- ODI 2: Use API if tests successful, or continue manual

**Your exposure**: Zero - manual CSV works regardless

Ready to create the test script once you share the API key! 🚀
