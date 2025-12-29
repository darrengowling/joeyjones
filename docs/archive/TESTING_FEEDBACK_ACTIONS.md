# Testing Feedback - Action Items
## Sport X - Pre-Deployment User Requests

**Date:** December 5, 2024  
**Status:** Awaiting clarification & implementation

---

## 📋 UX IMPROVEMENTS (Post-Deployment)

### Issue: Users Forgetting to Save Team Selection

**Problem:** 
- Users select teams but forget to click "Save"
- Import Fixtures button doesn't appear (requires `assetsSelected` to be populated)
- Users confused why they can't import fixtures

**Proposed Solutions:**
1. **Auto-save** when teams are selected (no manual save needed)
2. **Clearer "Save Selection" button** - larger, more prominent styling
3. **Helper text/tooltip** - "Remember to save your selection!"
4. **Disable "Start Auction"** button until teams are saved
5. **Warning banner** - "You have unsaved team selections"

**Priority:** MEDIUM (UX polish)  
**Estimated Time:** 20-30 minutes

---

## 🏆 FEATURE REQUEST 1: Champions League Support

### User Request
Users creating Champions League competitions can't import fixtures - clubs don't have correct identifiers for Football-Data.org API.

### Current State
- Premier League teams work ✅
- Champions League teams missing API identifiers ❌

### Questions Needed:
1. **Which Champions League clubs are users trying to use?**
   - All teams from current season?
   - Specific clubs (e.g., top 8 from each league)?
   - How many teams total?

2. **What identifiers are needed?**
   - Football-Data.org competition ID for Champions League
   - Team IDs from the API
   - Do we need to update existing teams or add new records?

3. **How does fixture import work for Champions League?**
   - Is it a single competition code?
   - Group stage + knockout stage fixtures?
   - Different from league fixtures?

### Implementation Steps (Estimated):
1. Get Champions League competition ID from Football-Data.org
2. Map existing Premier League teams to their Champions League IDs (if different)
3. Test fixture import for Champions League
4. Update team selection to show "Champions League Participants"

**Priority:** HIGH (blocking user competitions)  
**Estimated Time:** TBD (depends on API structure)

---

## 🌍 FEATURE REQUEST 2: AFCON Tournament Support

### User Request
Deployment user group wants to run African Cup of Nations competition:
- **Tournament:** AFCON 2026
- **Teams:** 24 national teams
- **Start Date:** January 2026
- **Requirement:** Dropdown option for "AFCON only" team selection

### Implementation Requirements:

#### 1. Add AFCON Teams to Database
**Teams Needed (24):**
- Need full list of qualified teams
- National teams (not clubs)
- Team logos/badges
- Football-Data.org team IDs (if available)

#### 2. Add Competition/Tournament Filter
**UI Changes:**
- Team selection dropdown: Add "Competition" filter
  - Options: "Premier League", "Champions League", "AFCON", "All"
- Filter teams by competition when selecting

#### 3. Fixture Import for AFCON
**Questions:**
- Does Football-Data.org API support AFCON?
- What's the competition ID?
- Tournament structure (groups + knockout)?
- How to handle fixture import for tournaments vs leagues?

### Questions Needed:
1. **Do you have the list of 24 AFCON teams?**
2. **Is AFCON covered by Football-Data.org API?**
   - If yes: What's the competition ID?
   - If no: Alternative data source?
3. **When do you need this by?**
   - Before initial deployment?
   - Can be added post-deployment?

### Implementation Steps (Estimated):
1. Get AFCON team list (24 teams)
2. Add teams to database with `competition: "AFCON"` flag
3. Update team selection UI with competition filter dropdown
4. Test Football-Data.org API for AFCON fixtures
5. Update fixture import to handle tournament format
6. Test end-to-end AFCON competition flow

**Priority:** HIGH (requested by deployment user group)  
**Estimated Time:** 1-2 hours (depending on API availability)

---

## 🤔 CLARIFYING QUESTIONS

### For Champions League:
1. Which clubs are users trying to create competitions for?
2. Do these clubs already exist in our database (Premier League teams)?
3. What error message do users see when trying to import fixtures?

### For AFCON:
1. Can you provide the list of 24 qualified teams?
2. Is this blocking initial deployment or can it be added post-deployment?
3. Do you have access to an AFCON fixture data source?

### General:
1. Which is higher priority: Champions League or AFCON?
2. Is either blocking deployment to your test users?

---

## 📊 PRIORITY ASSESSMENT

| Feature | User Impact | Blocking Deployment? | Estimated Time |
|---------|-------------|---------------------|----------------|
| UX Improvements (Save reminder) | Medium | No | 20-30 min |
| Champions League Support | High | Possibly | 1-2 hours |
| AFCON Support | High | TBD | 1-2 hours |

---

## 🎯 RECOMMENDED APPROACH

### Option A: Implement Both Now (2-3 hours)
- Get clarifications on both features
- Implement Champions League support
- Implement AFCON support
- Test thoroughly before deployment

### Option B: Prioritize One (1-2 hours)
- Which is more urgent?
- Implement highest priority first
- Add second feature post-deployment

### Option C: Deploy as-is, Add Post-Deployment
- Current Premier League support works
- Add Champions League after deployment
- Add AFCON after deployment
- Lower risk, but delays user groups

---

**Awaiting your guidance on:**
1. Priority (Champions League vs AFCON vs both)
2. Timeline (before deployment vs after)
3. Answers to clarifying questions above

