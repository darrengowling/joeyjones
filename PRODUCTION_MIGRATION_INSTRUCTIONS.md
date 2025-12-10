# Production Migration Instructions

## 🎯 Simple 3-Step Process to Fix Production Scoring

You don't need SSH access or production logs. Everything can be done via API calls from your browser or terminal.

---

## Step 1: Deploy the Code

Deploy the updated code to production through your normal deployment process.

**What's been added:**
- ✅ Enhanced migration script that runs automatically on startup
- ✅ API endpoints you can call to verify and trigger migration manually
- ✅ Better logging if things go wrong

---

## Step 2: Check if Migration is Needed

**Open in your browser:**
```
https://draft-kings-mobile.emergent.host/api/admin/migration/status
```

**Or use curl:**
```bash
curl https://draft-kings-mobile.emergent.host/api/admin/migration/status
```

**What you'll see:**

### ✅ If Migration Already Worked (Best Case):
```json
{
  "migration_needed": false,
  "summary": "✅ All correct",
  "details": [
    {
      "externalId": "61",
      "expected": "Chelsea FC",
      "actual": "Chelsea FC",
      "status": "✅ Correct"
    },
    ...
  ],
  "next_step": "No action needed"
}
```

**Result:** Skip to Step 4 - test your scoring!

### ❌ If Migration Still Needed:
```json
{
  "migration_needed": true,
  "summary": "❌ Migration needed",
  "details": [
    {
      "externalId": "61",
      "expected": "Chelsea FC",
      "actual": "Chelsea",  ← Wrong!
      "status": "❌ Needs update"
    },
    ...
  ],
  "next_step": "Call POST /api/admin/migration/run to fix"
}
```

**Result:** Continue to Step 3.

---

## Step 3: Run Migration Manually (If Needed)

**Open in your browser (yes, GET works too):**
```
https://draft-kings-mobile.emergent.host/api/admin/migration/run
```

**Or use curl:**
```bash
curl -X POST https://draft-kings-mobile.emergent.host/api/admin/migration/run
```

**What you'll see:**
```json
{
  "success": true,
  "message": "✅ Migration completed successfully",
  "details": "Team names have been updated to match the Football-Data.org API",
  "next_steps": [
    "1. Call GET /api/admin/migration/status to verify changes",
    "2. Test 'Update All Scores' in your leagues",
    "3. Verify league points are now being calculated"
  ]
}
```

**Then verify:** Call the status endpoint again (Step 2) to confirm all teams show "✅ Correct"

---

## Step 4: Test Your Scoring

### Test in MYCL 8 (or any league):

1. **Go to your league in the UI**
2. **Click "Update All Scores"**
3. **Check the standings**

**Expected result:** League points should now be calculated correctly!

### Debug if still not working:

If points still aren't calculating, check:

**A. Are there completed fixtures?**
```bash
curl "https://draft-kings-mobile.emergent.host/api/leagues/YOUR_LEAGUE_ID/fixtures" | grep '"status":"ft"'
```
You should see fixtures with `"status":"ft"` (full-time)

**B. Do fixtures have scores?**
Look for `"goalsHome"` and `"goalsAway"` in the fixtures

**C. Do participants have clubs?**
```bash
curl "https://draft-kings-mobile.emergent.host/api/leagues/YOUR_LEAGUE_ID/summary"
```
Check that participants have `"assetsOwned"` arrays with club IDs

---

## Troubleshooting

### Issue: "404 Not Found" when calling migration endpoints

**Cause:** Code not deployed yet or deployment failed

**Solution:** 
1. Verify deployment completed successfully
2. Try calling `/api/health` to see if backend is running
3. Redeploy if needed

---

### Issue: Migration status shows "❌ Needs update" even after running migration

**Cause:** Migration failed to run or encountered an error

**What to do:**
1. Call the migration endpoint again (it's safe to run multiple times)
2. If it still fails, check if there's a different error message
3. Contact support with the error details

---

### Issue: Migration works but scoring still doesn't work

**Cause:** Problem is not team names - something else is wrong

**Check:**
1. **Fixtures exist?** Call fixtures endpoint and verify you have data
2. **Fixtures have scores?** Check `goalsHome` and `goalsAway` are populated
3. **Fixtures marked complete?** Status should be `"ft"` not `"scheduled"`
4. **Participants own clubs?** Check `assetsOwned` arrays in league summary

---

## Quick Reference Commands

```bash
# Production URL
URL="https://draft-kings-mobile.emergent.host"

# Check migration status
curl $URL/api/admin/migration/status

# Run migration
curl -X POST $URL/api/admin/migration/run

# Get help
curl $URL/api/admin/migration/help

# Check backend health
curl $URL/api/health

# Check a specific league's fixtures
curl "$URL/api/leagues/YOUR_LEAGUE_ID/fixtures"

# Check league standings
curl "$URL/api/leagues/YOUR_LEAGUE_ID/summary"
```

---

## Why This Approach is Better

**Previous approach:**
- ❌ Relied on startup migration working silently
- ❌ No way to verify without production logs
- ❌ No way to trigger manually
- ❌ "Hope and pray" deployment

**New approach:**
- ✅ Startup migration still runs automatically (might work!)
- ✅ But if it doesn't, you can verify via API
- ✅ You can trigger it manually via API
- ✅ You can verify it worked via API
- ✅ No SSH or log access needed

---

## Expected Timeline

1. **Deploy:** 2-5 minutes
2. **Check status:** 5 seconds
3. **Run migration (if needed):** 30 seconds
4. **Test scoring:** 1-2 minutes

**Total:** Less than 10 minutes from deployment to verified fix

---

## Still Have Issues?

If after following all steps scoring still doesn't work:

1. Share the output of: `curl https://draft-kings-mobile.emergent.host/api/admin/migration/status`
2. Share the output of checking a league's fixtures
3. Describe exactly what happens when you click "Update All Scores"

This will help diagnose if the issue is actually something other than team names.

---

**Document Version:** 1.0  
**Created:** December 10, 2024  
**Tested in Preview:** ✅ Yes
