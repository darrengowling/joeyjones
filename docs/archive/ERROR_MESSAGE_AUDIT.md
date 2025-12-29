# Error Message Improvement - Safety Audit

## 🔍 Current Error Handling Patterns

### Pattern 1: Try-Catch with Toast
```javascript
try {
  await someAction();
  toast.success("Success message");
} catch (e) {
  console.error("Error:", e);
  toast.error("Generic error message");
}
```

### Pattern 2: Backend HTTPException
```python
if not condition:
    raise HTTPException(status_code=400, detail="Error message")
```

### Pattern 3: Frontend Error States
```javascript
const [error, setError] = useState("");
if (error) {
  return <div>Error: {error}</div>
}
```

---

## 📊 Error Messages Found

### Frontend Files Scanned:
1. `/app/frontend/src/App.js`
2. `/app/frontend/src/pages/LeagueDetail.js`
3. `/app/frontend/src/pages/AuctionRoom.js`
4. `/app/frontend/src/pages/CompetitionDashboard.js`
5. `/app/frontend/src/pages/MyCompetitions.js`

### Backend Files Scanned:
1. `/app/backend/server.py`

---

## ✅ SAFE TO CHANGE (Message Text Only)

### 1. Frontend Toast Messages
**Location**: Inside `catch` blocks
**Current**: `toast.error("Error starting auction")`
**Safe Change**: Update message text only
**Risk**: ZERO - only changes display text

**Examples:**
- App.js line 227: `toast.error("Error signing in")`
- LeagueDetail.js line 404: `toast.error("Error starting auction")`
- CompetitionDashboard.js line 199: `toast.error("Failed to update scores. Please try again.")`

### 2. Backend HTTPException Messages
**Location**: Inside route handlers
**Current**: `HTTPException(status_code=400, detail="Invalid token")`
**Safe Change**: Update `detail` text only
**Risk**: ZERO - doesn't affect status codes or logic

**Examples:**
- server.py line 1526: `detail="Invalid or expired invite token"`
- server.py line 3162: `detail="Minimum 2 managers required"`
- server.py line 2146: `detail="Cannot import fixtures while auction is in progress"`

### 3. Frontend Error State Messages
**Location**: Error display components
**Current**: `<div>Error loading data</div>`
**Safe Change**: Update message text
**Risk**: ZERO - only display

---

## ⚠️ DO NOT CHANGE (Logic/Flow)

### 1. Error Handling Logic
**DON'T touch:**
- `try/catch` structure
- `if/else` conditions
- Error propagation (`throw e`)
- Status code checks (`e.response.status`)

### 2. Error Types/Classes
**DON'T change:**
- `HTTPException` class usage
- Error status codes (400, 401, 404, 500)
- `catch (e)` variable names used in logic

### 3. Conditional Rendering Based on Errors
**DON'T change:**
- `if (error) return <Component />`
- Error state variable names if used in conditions
- Boolean flags like `hasError`

---

## 🎯 Safe Implementation Strategy

### Step 1: Backend Error Messages
**What**: Update `HTTPException` detail text
**How**: Replace detail text only, keep status codes
**Files**: `/app/backend/server.py`

**Example:**
```python
# BEFORE
raise HTTPException(status_code=400, detail="Error")

# AFTER
raise HTTPException(status_code=400, detail="Can't start auction: Need at least 2 participants")
```

### Step 2: Frontend Toast Messages
**What**: Update `toast.error()` text
**How**: Replace message string only
**Files**: Various frontend pages

**Example:**
```javascript
// BEFORE
toast.error("Error starting auction");

// AFTER
toast.error("Can't start auction: Need at least 2 participants. Share invite code with friends!");
```

### Step 3: Add Context from Backend Errors
**What**: Show backend error details when available
**How**: Use `e.response?.data?.detail` or fallback
**Files**: Frontend catch blocks

**Example:**
```javascript
// BEFORE
catch (e) {
  toast.error("Error starting auction");
}

// AFTER
catch (e) {
  const message = e.response?.data?.detail || "Error starting auction. Please try again.";
  toast.error(message);
}
```

---

## 🧪 Testing Checklist

After changes, verify:
- [ ] All try-catch blocks still catch errors
- [ ] Toast notifications still appear
- [ ] Backend still returns proper status codes
- [ ] Frontend still handles errors gracefully
- [ ] No logic changes, only message text
- [ ] Error states still trigger correctly

---

## 📋 Specific Changes Planned

### High Priority (User-facing critical flows)

**1. Start Auction Errors**
- Current: "Error starting auction"
- New: Check for specific conditions (no participants, no teams)
- Add: Actionable guidance

**2. Fixture Import Errors**
- Current: "Failed to import fixture. Please try again."
- New: Add reason (API limit, network, no upcoming matches)
- Add: When to retry

**3. Score Update Errors**
- Current: "Failed to update scores. Please try again."
- New: Add reason (API issue, fixture not complete)
- Add: What to check

**4. Join League Errors**
- Current: "Invalid or expired invite token"
- New: Add suggestions (check code, ask commissioner)

**5. Authentication Errors**
- Current: "Error signing in"
- New: Add reason (email not found, link expired)
- Add: What to do (check email, request new link)

---

## ✅ Safety Guarantees

### What Will NOT Change:
1. ❌ Error handling flow (try/catch/throw)
2. ❌ HTTP status codes (400, 401, 404, etc.)
3. ❌ Conditional logic based on errors
4. ❌ Error propagation patterns
5. ❌ Error state variable names used in logic
6. ❌ API error response structure

### What WILL Change:
1. ✅ Error message text (more helpful)
2. ✅ Toast notification messages (more actionable)
3. ✅ HTTPException detail text (more specific)
4. ✅ User-facing error displays (more guidance)

---

## 🎯 Implementation Approach

**Conservative Strategy:**
1. Change ONE message at a time
2. Test that flow still works
3. Verify error still displays
4. Move to next message

**No Bulk Changes:**
- Will NOT do find/replace across files
- Will NOT change all errors at once
- Will NOT modify error handling patterns

**Focus on Top 10 Most Common Errors:**
- Start with highest-impact user flows
- Skip rare edge cases for now
- Can expand post-pilot if needed

---

## ✅ CONCLUSION

**Risk Assessment: VERY LOW**

Changes are limited to:
- Display text only
- Message strings
- User-facing content

Changes do NOT affect:
- Application logic
- Error handling flow
- API contracts
- Data validation
- Security checks

**Ready to proceed with implementation.**
