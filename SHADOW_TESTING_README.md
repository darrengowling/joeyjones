# Shadow Testing Guide - CricketData API

## 🎯 Purpose
Test the CricketData.org API WITHOUT integrating into the live app.
**Zero risk** - runs completely separately from production.

## 📅 Schedule
- **ODI 1**: Oct 26, 2025 @ 2:00 PM UTC (1:00 AM GMT Oct 27)
- **ODI 2**: Oct 29, 2025 @ 2:00 PM UTC
- **ODI 3**: Nov 1, 2025 @ 2:00 PM UTC

## 🚀 Quick Start

### Test API Connectivity (Do this first!)
```bash
cd /app/scripts
python test_cricketdata_api.py --connectivity
```

### List All Current Matches
```bash
python test_cricketdata_api.py --list-matches
```

### Find NZ vs England Match
```bash
python test_cricketdata_api.py --find-match
```

### Test Specific Match by ID
```bash
python test_cricketdata_api.py --match-id <match-id>
```

### Full Test for ODI 1
```bash
python test_cricketdata_api.py --test-match 1
```

### Live Monitoring (every 5 minutes)
```bash
python test_cricketdata_api.py --test-match 1 --monitor
```

### Custom Monitoring Interval
```bash
# Monitor every 15 minutes (900 seconds)
python test_cricketdata_api.py --test-match 1 --monitor --interval 900
```

## 📋 Testing Workflow for ODI 1 (Tomorrow)

### Before Match (12:00 AM GMT - 1 hour before)
```bash
# 1. Test API connectivity
python test_cricketdata_api.py --connectivity

# 2. See if match appears yet
python test_cricketdata_api.py --list-matches
```

### When Match Starts (1:00 AM GMT)
```bash
# Start live monitoring (every 5 minutes)
python test_cricketdata_api.py --test-match 1 --monitor
```

**What it does:**
- Fetches match data every 5 minutes
- Saves snapshots to `/app/artifacts/`
- Shows live updates in terminal
- Press Ctrl+C to stop

### During Match
- Let the script run in background
- Focus on your manual CSV process (production)
- Script runs independently - zero interference

### After Match
```bash
# Check saved artifacts
ls -lh /app/artifacts/

# Review test report
cat /app/artifacts/test_report_odi1.md
```

## 📁 What Gets Saved

All data saved to `/app/artifacts/`:

```
/app/artifacts/
├── api_scorecard_<match-id>_<timestamp>.json   # API responses
├── test_report_odi1.md                          # Test report template
├── api_scorecard_<match-id>_<timestamp>.json   # Multiple snapshots
└── ...
```

## 🔍 What We're Testing

### 1. API Reliability
- ✅ Does it work during live match?
- ✅ Response times under 5 seconds?
- ✅ No downtime/errors?

### 2. Data Completeness
- ✅ All 30 players present?
- ✅ Runs, wickets, catches tracked?
- ✅ Stumpings tracked? (critical for us)
- ✅ Run-outs tracked?

### 3. Data Accuracy
- ✅ Matches official scorecard?
- ✅ Real-time updates working?
- ✅ Final scores correct?

### 4. Player Mapping
- ✅ All player names match our database?
- ✅ No name variations causing issues?

## 📊 After Testing - Decision Framework

### ✅ GO for ODI 2 if:
- Accuracy >95%
- All 30 players mapped
- No API downtime
- Stumpings & run-outs tracked
- Response times <5s

### 🟡 MODIFY if:
- Accuracy 90-95%
- Some players need manual mapping
- Minor data delays

### ❌ STICK WITH MANUAL if:
- Accuracy <90%
- API downtime during match
- Missing critical stats
- Data quality concerns

## 🛠️ Troubleshooting

### "API not accessible"
```bash
# Check if API key is correct
grep "API_KEY" /app/scripts/test_cricketdata_api.py

# Test with curl
curl "https://api.cricketdata.org/v1/current_matches?apikey=82fec341-b050-4b1c-9a9d-72359c591820"
```

### "Match not found"
- Match may not be listed yet (try 30 min before start)
- Try --list-matches to see what's available
- Note the match ID for later use

### Script stops unexpectedly
```bash
# Run in background with logging
nohup python test_cricketdata_api.py --test-match 1 --monitor > /app/artifacts/monitor.log 2>&1 &

# Check log
tail -f /app/artifacts/monitor.log
```

## 📞 Support

If you encounter issues:
1. Check `/app/artifacts/` for saved data
2. Review error messages in terminal
3. Share artifacts for analysis

## ⚠️ Important Notes

- **This DOES NOT affect your live app**
- **Manual CSV remains your production system**
- **Users will never see this API data**
- **Completely safe to test**

## 🎯 Success Criteria

After ODI 1, we want to answer:
1. Can we trust this API for live scoring?
2. Is the data complete and accurate?
3. Can we map all players correctly?
4. Should we use it for ODI 2 & 3?

---

**Ready to test tomorrow at 1:00 AM GMT!** 🏏
