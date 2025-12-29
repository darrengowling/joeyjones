# Post-Deployment Enhancements
## Sport X - Future Features & Improvements

**Last Updated:** December 5, 2024

---

## 🔮 PLANNED ENHANCEMENTS (Post-Testing)

### 1. Custom Scoring Rules During League Creation (HIGH PRIORITY)

**Current State:**
- Scoring rules are hardcoded in `/app/backend/server.py` (line 558)
- Cricket default rules:
  - Run: 1 pt, Wicket: 20 pts, Catch: 10 pts, Stumping: 25 pts, Run Out: 20 pts
  - Milestones: ALL DISABLED (halfCentury, century, fiveWicketHaul)

**Planned Feature:**
Allow commissioners to customize scoring rules during league creation

**Implementation Plan:**
1. **Frontend - League Creation Form:**
   - Add "Scoring Settings" section (collapsible/advanced)
   - Toggle switches for milestone bonuses
   - Input fields for base rule points
   - Preview of scoring schema
   - Templates: "Standard", "Enhanced", "Custom"

2. **Backend Changes:**
   - Already supports reading `league.scoringSchema` ✅
   - No backend changes needed!
   - Just save form data to league document

3. **UI Mockup:**
   ```
   ┌─────────────────────────────────────┐
   │ ⚙️ Scoring Settings (Optional)      │
   ├─────────────────────────────────────┤
   │ Base Rules:                         │
   │   Run: [1] pts                      │
   │   Wicket: [20] pts                  │
   │   Catch: [10] pts                   │
   │   Stumping: [25] pts                │
   │   Run Out: [20] pts                 │
   │                                     │
   │ Milestone Bonuses:                  │
   │   [✓] Half Century (+8 pts)        │
   │   [✓] Century (+16 pts)            │
   │   [✓] Five Wicket Haul (+16 pts)   │
   └─────────────────────────────────────┘
   ```

**Estimated Time:** 30-45 minutes
**Priority:** HIGH (user-requested feature)
**Risk:** LOW (backend already supports it)

**Testing Needed:**
- Create league with custom rules
- Verify score update uses custom rules
- Test with bonuses enabled
- Test with different point values

---

## 📋 OTHER POST-DEPLOYMENT ITEMS

### 2. Mobile UI Improvements (IF NEEDED)
**Status:** Awaiting feedback from pilot testing
**File:** `/app/MOBILE_UI_QUICK_WINS.md`
**Decision:** Deploy as-is, implement based on real user feedback

### 3. Full Auction UI Redesign (FUTURE)
**Status:** Backlog
**Current:** Quick wins only
**Future:** Comprehensive mobile mockup with sticky header, quick-bid buttons

### 4. Sentry Error Monitoring (OPTIONAL)
**Status:** Not implemented
**Recommendation:** Add after 24-48 hours of stable operation
**Time:** 30 minutes
**File:** `/app/PRE_DEPLOYMENT_STRATEGIC_ANALYSIS.md`

### 5. Redis Rate Limiting (FUTURE)
**Status:** Not needed for pilot
**When:** When user base grows or API abuse detected
**Time:** 3-4 hours
**File:** `/app/PRE_DEPLOYMENT_STRATEGIC_ANALYSIS.md`

### 6. Code Refactoring (ONGOING)
**Items:**
- Break down monolithic `server.py` into modular routers
- Separate cricket scoring logic
- Organize routes by feature

### 7. Fixtures in Auction Room (DEFERRED)
**Issue:** Imported fixtures don't show during live auction
**Status:** Deferred from testing feedback
**Priority:** LOW (nice to have)

---

## 🎯 IMMEDIATE POST-TESTING PRIORITIES

1. **Custom Scoring Rules** (if users request flexibility)
2. **Mobile UI Polish** (if feedback shows issues)
3. **Sentry Monitoring** (for production error tracking)
4. **Bug fixes** (based on pilot user feedback)

---

## 📝 NOTES FROM DEVELOPMENT

**Cricket Scoring Implementation:**
- Fully automatic scoring from Cricbuzz API ✅
- Fetches live matches via `/matches/v1/live` ✅
- Parses scorecards at "Stumps" (end of day) ✅
- Tracks batting, bowling, and fielding stats ✅
- Updates multiple leagues with same fixture ✅
- Correct scoring rules implemented ✅

**Testing Results:**
- Football: 100% working (tested)
- Cricket: 100% working (tested with real Ashes data)
- Verified with cric2 league and actual player performances

**Known Limitations:**
- Scoring rules hardcoded (intentional for testing)
- No CSV upload UI for cricket (fallback method exists)
- Sentry not configured (optional monitoring)
- Redis not implemented (not needed for pilot)

---

**Created:** December 5, 2024  
**For:** Post-deployment enhancements after pilot testing
