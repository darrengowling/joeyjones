# Load Testing Best Practices
## Preventing Test Data Pollution

**Created**: November 25, 2025  
**Issue**: Load test data (2,389 leagues, 331 users) interfered with production app functionality

---

## Problem

During Socket.IO load testing, we created thousands of test leagues and users. This caused:
1. **Invite token issues**: `/api/leagues` endpoint limited to 100 results, hiding new real leagues
2. **Performance degradation**: Unnecessary database bloat
3. **Confusion**: Test data mixed with real user data
4. **Testing difficulties**: Hard to identify real issues vs test artifacts

---

## Solution Implemented

**Cleanup Scripts Created:**
- `/app/scripts/cleanup_load_test_data.py` - Removes load test leagues, participants, auctions, bids
- `/app/scripts/cleanup_load_test_users.py` - Removes load test users

**Cleanup Results:**
- ✅ Deleted 2,389 load test leagues
- ✅ Deleted 331 load test users
- ✅ Kept 4 real leagues (fopifa1, prem1, prem2, prem3)
- ✅ Kept 162 real users

---

## Best Practices for Future Load Testing

### Option 1: Use Separate Test Database (RECOMMENDED)

**Setup:**
```bash
# Create separate test database in MongoDB
# Use different DB_NAME for load testing
DB_NAME=load_test_database  # Instead of test_database
```

**Advantages:**
- ✅ Complete isolation from production data
- ✅ Can delete entire database after testing
- ✅ No risk of mixing test and real data
- ✅ Easy to reset for repeated testing

**Disadvantages:**
- ⚠️ Need to manage multiple database connections
- ⚠️ Slightly more complex setup

---

### Option 2: Mark Test Data with Flags (Current Approach)

**Implementation:**
- Add `isLoadTest: true` field to all test entities
- Use consistent naming patterns (e.g., "Load Test League", "loadtest@")
- Run cleanup script after testing

**Advantages:**
- ✅ Simple to implement
- ✅ Uses existing database
- ✅ Cleanup scripts provided

**Disadvantages:**
- ⚠️ Risk of forgetting to clean up
- ⚠️ Test data temporarily pollutes production database
- ⚠️ Manual cleanup required

---

### Option 3: Automated Cleanup on Test Completion

**Implementation:**
```python
# In load test scripts
async def cleanup_after_test():
    # Delete all entities created during this test run
    test_run_id = "test_20251125_001"
    await db.leagues.delete_many({"testRunId": test_run_id})
    await db.users.delete_many({"testRunId": test_run_id})
```

**Advantages:**
- ✅ Automatic cleanup
- ✅ No manual intervention needed
- ✅ Clean database after each test

**Disadvantages:**
- ⚠️ Need to track test run IDs
- ⚠️ If script fails, cleanup might not run

---

## Recommended Workflow for Load Testing

### Before Testing

1. **Decide on approach**:
   - For destructive/large tests: Use separate database
   - For quick tests: Use flags and cleanup scripts

2. **Document test plan**:
   - How many test entities will be created?
   - How will they be identified?
   - When will cleanup happen?

3. **Take database backup**:
   ```bash
   /app/scripts/backup_mongodb.sh
   ```

### During Testing

1. **Use consistent naming**:
   - Leagues: "Load Test League [timestamp]"
   - Users: "loadtest_user_[id]@test.com"

2. **Add identifying fields**:
   ```python
   league_data = {
       "name": "Load Test League",
       "isLoadTest": True,  # Flag for cleanup
       "testRunId": test_run_id
   }
   ```

3. **Monitor data growth**:
   ```python
   # Check counts during test
   leagues_count = await db.leagues.count_documents({})
   if leagues_count > 1000:
       print("⚠️ Warning: High number of leagues created")
   ```

### After Testing

1. **Run cleanup scripts immediately**:
   ```bash
   python /app/scripts/cleanup_load_test_data.py
   python /app/scripts/cleanup_load_test_users.py
   ```

2. **Verify cleanup**:
   ```bash
   # Check remaining counts
   curl https://cricket-fantasy-app-2.preview.emergentagent.com/api/leagues | python -c "import sys, json; print(len(json.load(sys.stdin)))"
   ```

3. **Document results**:
   - What was tested
   - What data was created
   - What was cleaned up
   - Any issues encountered

---

## Updated Load Testing Scripts

### Add Cleanup to run_auction_test.sh

```bash
# At end of script
echo "Load test complete. Running cleanup..."
python /app/scripts/cleanup_load_test_data.py
python /app/scripts/cleanup_load_test_users.py
echo "Cleanup complete!"
```

### Modify setup_test_auction.py

```python
# Add flag to created entities
league_data = {
    "name": f"Socket.IO Load Test {int(time.time())}",
    "isLoadTest": True,  # Mark for cleanup
    "testRunId": f"socketio_test_{int(time.time())}",
    ...
}
```

---

## Quick Reference Commands

**Clean up load test data:**
```bash
python /app/scripts/cleanup_load_test_data.py
python /app/scripts/cleanup_load_test_users.py
```

**Check database status:**
```bash
# Count leagues
curl https://cricket-fantasy-app-2.preview.emergentagent.com/api/leagues | python -c "import sys, json; print(f'Leagues: {len(json.load(sys.stdin))}')"

# Check users (requires database access)
python -c "import asyncio; from motor.motor_asyncio import AsyncIOMotorClient; print(asyncio.run((lambda: AsyncIOMotorClient('mongodb://localhost:27017')['test_database'].users.count_documents({}))()))"
```

**Backup before load testing:**
```bash
/app/scripts/backup_mongodb.sh
```

---

## Prevention Checklist

**Before any load test:**
- [ ] Decide: separate database or cleanup scripts?
- [ ] Take database backup
- [ ] Document what will be created
- [ ] Set up cleanup automation or reminders

**During load test:**
- [ ] Use consistent naming patterns
- [ ] Add identifying flags to test data
- [ ] Monitor database growth

**After load test:**
- [ ] Run cleanup scripts immediately
- [ ] Verify cleanup was successful
- [ ] Document test results
- [ ] Check app functionality works normally

---

## Summary

**Lesson Learned**: Load test data must be isolated or cleaned up to prevent interference with production functionality.

**Recommended Approach**: 
1. Use separate test database for large-scale load tests
2. Use cleanup scripts for smaller tests
3. Always clean up immediately after testing
4. Document and verify cleanup

**Key Takeaway**: Test data hygiene is critical for maintaining a usable pilot/production environment.

---

**Document Version**: 1.0  
**Last Updated**: November 25, 2025  
**Cleanup Scripts**: `/app/scripts/cleanup_load_test_*.py`
