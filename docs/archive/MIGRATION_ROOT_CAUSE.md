# Migration Failure - Root Cause Analysis

## The Actual Problem

The migration script was connecting to the **WRONG DATABASE** in production.

### Why It Failed

**Line of code that caused the issue:**
```python
from dotenv import load_dotenv
load_dotenv()  # ← This was at module level
```

### What Happened

1. **Preview Environment:**
   - Uses local MongoDB: `mongodb://localhost:27017`
   - Environment variables from `/app/backend/.env` file
   - `load_dotenv()` loads correct local connection string
   - Migration runs ✅

2. **Production Environment (Kubernetes):**
   - Uses MongoDB Atlas (cloud database)
   - Environment variables from **platform configuration** (not .env file)
   - When migration imports, `load_dotenv()` runs BEFORE server.py sets up environment
   - Migration either:
     - Loads wrong `.env` file (preview values) → connects to wrong database
     - OR .env file doesn't exist → MONGO_URL is empty/wrong
   - Migration appears to "succeed" but updates wrong database or fails silently

3. **Meanwhile, server.py:**
   - Uses environment variables from platform (correct Atlas connection)
   - Connects to correct production database
   - But migration already ran against wrong database

### The Fix

**Remove `load_dotenv()` from module level:**
```python
# OLD - Wrong
from dotenv import load_dotenv
load_dotenv()  # Runs when imported

# NEW - Correct  
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()  # Only runs when script executed directly
```

### Why This Matters

- **When run standalone:** `python migrate_team_names.py` → needs .env file ✅
- **When imported by server.py:** Uses environment already set up by platform ✅

### Lessons Learned

1. **Never call `load_dotenv()` at module level** in files that will be imported
2. **Preview and production have different environment variable sources**:
   - Preview: `.env` files
   - Production: Platform-managed environment variables
3. **Silent failures are dangerous** - migration appeared to succeed but did nothing
4. **Test database connections** - verify WHICH database the migration connects to

### Verification Steps for Production

After redeployment, check logs for:
1. "🔄 Running team name migration..."
2. "✅ Team name migration completed"
3. Team names in scoring logs should show NEW names:
   - "Chelsea FC" (not "Chelsea")
   - "Club Atlético de Madrid" (not "Atlético de Madrid")
   - "Atalanta BC" (not "Atalanta")

---

**This was the actual root cause. Not import paths. Not module structure. Database connection.**
