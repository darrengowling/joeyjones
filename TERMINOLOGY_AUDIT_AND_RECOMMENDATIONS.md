# Terminology Audit and Recommendations

## Business Terminology (User's Definition)

1. **Competition** = Pre-auction phase (setup, running auction, team selection)
2. **League** = Post-auction phase (teams allocated, matches playing, scoring active)
3. **Tournament** = Real-world sporting event (Ashes, IPL, World Cup, EPL Matchday)

## Current Codebase State

### Backend (No Changes Recommended)
- Uses "league" throughout for entire lifecycle
- Status field differentiates phases: `"draft"`, `"auction_in_progress"`, `"completed"`
- **Decision**: Keep as-is - stable, working, no user-facing impact

### Frontend Current State

#### ✅ Already Correct (Uses "Competition")
| Location | Text | Status |
|----------|------|--------|
| CreateLeague.js | "Create Your Competition" | ✅ Correct |
| MyCompetitions.js | "My Competitions" | ✅ Correct |
| LeagueDetail.js title | "Competition \| Sport X" | ✅ Correct |
| CompetitionDashboard.js | Page uses "Competition Dashboard" | ✅ Correct |
| Help.js | All references use "Competition" | ✅ Correct |
| Navigation breadcrumbs | "My Competitions" | ✅ Correct |

#### ❌ Needs Update (Uses "League" in User-Facing Text)
| Location | Current Text | Should Be | Impact |
|----------|-------------|-----------|--------|
| **LeagueDetail.js:601** | "League Participants" | "Competition Participants" | Medium - Commissioner view |
| **LeagueDetail.js:668** | "League Settings" | "Competition Settings" | Medium - Commissioner view |
| **LeagueDetail.js:1172** | "League Standings" | "Standings" | Low - Generic term better |
| **LeagueDetail.js:1154** | "part of this league" | "part of your competition" | Low - Helper text |

### URL Structure (No Changes Recommended)

**Current URLs**:
- `/create-league` - Creates competition
- `/league/:leagueId` - League detail page
- `/competition/:leagueId` - Competition dashboard
- `/app/my-competitions` - User's competitions list

**Analysis**:
- URLs are internal plumbing - users don't care
- Changing URLs breaks bookmarks and external links
- Frontend labels matter more than URL paths
- **Decision**: Keep URLs as-is

## Proposed Changes (Minimal Risk)

### Change 1: LeagueDetail.js Headings
**File**: `/app/frontend/src/pages/LeagueDetail.js`

```javascript
// Line 601: Change heading
- <h3 className="text-lg font-semibold text-gray-900 mb-4">League Participants</h3>
+ <h3 className="text-lg font-semibold text-gray-900 mb-4">Competition Participants</h3>

// Line 668: Change heading
- <h3 className="text-lg font-semibold text-gray-900 mb-4">League Settings</h3>
+ <h3 className="text-lg font-semibold text-gray-900 mb-4">Competition Settings</h3>

// Line 1172: Change to generic term
- <h3 className="text-lg font-semibold text-gray-900">League Standings</h3>
+ <h3 className="text-lg font-semibold text-gray-900">Standings</h3>

// Line 1154: Change helper text
- <strong>Note:</strong> Teams in <span className="font-semibold text-blue-600">blue</span> are part of this league.
+ <strong>Note:</strong> Teams in <span className="font-semibold text-blue-600">blue</span> are in your competition.
```

**Risk**: ⚠️ NONE - Pure text changes, no logic affected

### Change 2: CompetitionDashboard.js Comment
**File**: `/app/frontend/src/pages/CompetitionDashboard.js`

```javascript
// Line 435: Update comment for clarity
- {/* League Info */}
+ {/* Competition Info */}
```

**Risk**: ⚠️ NONE - Comment only, not user-facing

## What We're NOT Changing (and Why)

### 1. Backend Code
- Collections: `leagues`, `league_participants`, `league_stats`
- Routes: `/api/leagues/*`
- Models: `League`, `LeagueCreate`
- **Reason**: Stable, working, no user-facing impact

### 2. URL Paths
- `/create-league`
- `/league/:id`
- `/competition/:id`
- **Reason**: Internal routing, users see page titles not URLs

### 3. Variable Names in Frontend
- `leagueId`, `league`, `leagues`
- **Reason**: Internal code, doesn't affect user experience

### 4. API Calls
- `axios.get(\`\${API}/leagues/...\`)`
- **Reason**: Backend contract, must stay consistent

## Risk Assessment

### Proposed Changes Risk: ✅ MINIMAL

**What Could Go Wrong?**
1. ❌ **Breaking API calls**: No - we're not changing any API endpoints or parameters
2. ❌ **Breaking logic**: No - only changing display text in JSX
3. ❌ **Breaking navigation**: No - no changes to routes or navigation code
4. ❌ **Breaking state**: No - variable names unchanged
5. ❌ **Confusing users**: No - actually reduces confusion by using consistent term

**What Could Be Improved?**
1. ✅ Consistent "Competition" terminology in user-facing text
2. ✅ Aligns with navigation ("My Competitions")
3. ✅ Matches page titles already in place
4. ✅ Reduces cognitive load for users

## Testing Checklist After Changes

### Manual Testing
- [ ] View LeagueDetail page as commissioner
- [ ] Check "Competition Participants" section renders
- [ ] Check "Competition Settings" section renders
- [ ] Check "Standings" heading renders
- [ ] Verify fixtures helper text displays correctly
- [ ] Navigate between pages - no broken links
- [ ] Create new competition - flow unchanged
- [ ] Join competition - flow unchanged

### Regression Testing
- [ ] Backend API calls still work (GET /leagues/:id)
- [ ] Socket.IO events still received
- [ ] State management unchanged
- [ ] Navigation still works
- [ ] Authentication still works

## Implementation Plan

### Phase 1: Text Changes (5 minutes)
1. Update 4 text strings in LeagueDetail.js
2. Update 1 comment in CompetitionDashboard.js

### Phase 2: Verification (5 minutes)
1. Visual check - load pages and verify text
2. Browser console - check for errors
3. Network tab - verify API calls unchanged

### Phase 3: Documentation (Already Done)
- This document serves as record of changes
- Future developers know the terminology mapping

## Future Considerations

### If Backend Refactor Ever Needed
1. Create migration script: `leagues` → `competitions`
2. Update all API routes: `/leagues/` → `/competitions/`
3. Update all models and schemas
4. Run comprehensive test suite
5. **Estimated effort**: 4-6 hours + testing
6. **Recommended timing**: Major version release, not before user testing

### Communication Guidelines
When discussing with user:
- ✅ Use: "Competition" for user-created games
- ✅ Use: "Tournament" for real-world events (Ashes, IPL)
- ✅ Use: "League" only when referring to post-auction state specifically
- ✅ Clarify context when term could be ambiguous

## Summary

### ✅ Safe to Proceed
- Only 4 text strings and 1 comment changing
- Zero logic changes
- Zero API changes
- Zero routing changes
- Improves user clarity

### 📋 Changes Summary
| File | Lines Changed | Type | Risk |
|------|---------------|------|------|
| LeagueDetail.js | 4 text strings | Display text | None |
| CompetitionDashboard.js | 1 comment | Comment | None |
| **Total** | **5 changes** | **Text only** | **✅ None** |

### 🎯 Outcome
- Users see consistent "Competition" terminology
- Backend remains stable
- No disruption to user flows
- Aligns with business terminology

---

**Recommendation**: ✅ PROCEED WITH CHANGES
**Confidence Level**: 100%
**Risk Level**: Minimal (text-only changes)
**Testing Required**: Basic visual verification
