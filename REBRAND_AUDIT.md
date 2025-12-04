# Rebrand Audit: "Friends of PIFA" → "Sport X"

## ✅ SAFE TO CHANGE (UI/Display Text Only)

### Frontend Files - Display Text
1. **`/app/frontend/src/App.js`**
   - Line 788: `<span>Friends of PIFA</span>` → Header/logo text
   - Line 918: `<h2>Welcome to Friends of PIFA</h2>` → Homepage welcome

2. **`/app/frontend/src/pages/Help.js`**
   - Line 70: `<h2>Welcome to Friends of PIFA!</h2>` → Help section title
   - Line 110: `Friends of PIFA uses a secure...` → Auth description

3. **`/app/frontend/src/pages/MyCompetitions.js`**
   - Line 150: `← Friends of PIFA` → Back button text

### Documentation Files (Optional)
- `./STATUS_REPORT.md` - Title
- `./UI_UX_REVIEW_AND_IMPROVEMENTS.md` - References
- `./CHAT_FEATURE_IMPLEMENTATION_PLAN.md` - Multiple references
- `./PRE_DEPLOYMENT_STATUS.md` - References

**Impact**: Zero code logic impact - these are pure display strings

---

## ❌ DO NOT CHANGE (Code/Logic/References)

### Test Files
- `./production_readiness_test.py` - Test email: `prod.test@friendsofpifa.com`
- `./backend/smoke_test.py` - Test banner text
- `./backend/test_seed_one_player.py` - Variable names `fopifa1_player`

**Reason**: Test fixtures, not user-facing. Can be updated later if needed.

### Historical Data
- `./.git/` - Git history
- `./docs/` - Historical documentation

**Reason**: Archival, not active code

---

## 🗄️ DATABASE CHECK

### Collections: ✅ CLEAR
- No collection names contain "pifa"

### Documents: ✅ CLEAR
- No leagues with "pifa" in name (user-created leagues like "lfc1", "prem10" etc.)
- No assets/clubs/players with "pifa" in name

### Field Names: ✅ CLEAR
- No database schema fields reference "pifa"

---

## 🔍 CODE LOGIC CHECK

### Variable Names: ✅ CLEAR
- No variables named `pifa*` or `friendsOfPifa*` in production code
- Only test files have `fopifa1_player` (test fixtures)

### API Endpoints: ✅ CLEAR
- No routes like `/api/pifa/*`
- No query parameters with "pifa"

### Configuration: ✅ CLEAR
- No environment variables with "pifa"
- No config keys with "pifa"

---

## 📋 REBRAND CHECKLIST

### Must Change (User-Facing)
- [ ] Header logo text (App.js line 788)
- [ ] Homepage welcome (App.js line 918)
- [ ] Help section title (Help.js line 70)
- [ ] Help auth description (Help.js line 110)
- [ ] My Competitions back button (MyCompetitions.js line 150)

### Optional (Documentation)
- [ ] README.md (if any references)
- [ ] Status reports and planning docs

### Do Not Change
- [ ] Test files (not user-facing)
- [ ] Git history
- [ ] Historical docs

---

## 🛡️ SAFETY VERIFICATION

### Pre-Rebrand Checks
✅ No database collections or fields affected
✅ No API endpoints affected
✅ No business logic affected
✅ No authentication logic affected
✅ No variable names in production code affected

### Post-Rebrand Validation
- [ ] Frontend compiles without errors
- [ ] All pages load correctly
- [ ] Search for any missed "Friends of PIFA" references
- [ ] Visual inspection of header, homepage, help section

---

## 🚀 EXECUTION PLAN

### Phase 1: Core UI (15 minutes)
1. Update App.js header (line 788)
2. Update App.js homepage (line 918)
3. Update Help.js title (line 70)
4. Update Help.js auth text (line 110)
5. Update MyCompetitions.js back button (line 150)

### Phase 2: Verification (5 minutes)
1. Restart frontend
2. Clear browser cache / use incognito
3. Visual check all affected pages
4. Search for any remaining "Friends of PIFA"

### Phase 3: Documentation (5 minutes)
1. Update PRE_DEPLOYMENT_STATUS.md
2. Update any user-facing README sections

**Total Time: ~25 minutes**

---

## ✅ CONCLUSION

**Rebrand is 100% SAFE**

- All changes are UI/display text only
- No code logic, routes, APIs, or database affected
- No breaking changes
- No migrations needed
- Simple find/replace in 5 files

**Risk Level: ZERO**
