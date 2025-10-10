# My Competitions E2E Tests

This directory contains 5 stable, non-flaky Playwright tests for the "My Competitions" feature (Prompt 5).

## Test Files

### 1. `me_competitions_list.spec.ts`
**Purpose:** Verify My Competitions list navigation and View Dashboard button.

**Test Flow:**
- Login as new user
- Create a competition
- Navigate to `/app/my-competitions`
- Assert `my-competitions-page` testid is visible
- Assert at least one `comp-card-*` exists
- Click `comp-view-btn` button
- Verify lands on dashboard with `comp-dashboard` testid

**Key Assertions:**
- Competition list page loads
- Competition cards are visible
- View Dashboard navigation works

---

### 2. `competition_dashboard_tabs.spec.ts`
**Purpose:** Verify Competition Dashboard tab switching and testid visibility.

**Test Flow:**
- Create a league and get its ID
- Navigate to `/app/competitions/:id`
- Assert all tab buttons are visible: `tab-summary`, `tab-table`, `tab-fixtures`
- Click `tab-table` and verify `table-grid` is visible
- Click `tab-fixtures` and verify fixtures content (list or empty state)
- Click `tab-summary` and verify summary sections are visible

**Key Assertions:**
- All three tabs are clickable
- Tab content displays correctly
- All required testids are present

---

### 3. `league_table_zero_state.spec.ts`
**Purpose:** Verify league table shows zero points for all managers initially.

**Test Flow:**
- Create a league as commissioner
- Navigate to dashboard and open League Table tab
- Verify `table-grid` is visible
- Assert all managers have 0.0 points
- Verify tiebreakers (Goals/Runs and Wins/Wickets) are all 0
- Call `/api/leagues/:id/standings` API to verify backend data also shows 0 points

**Key Assertions:**
- Table displays with correct structure
- All point values are 0.0
- All tiebreaker values are 0
- API response matches UI state

---

### 4. `fixtures_import_csv.spec.ts`
**Purpose:** Verify commissioner CSV upload functionality and fixtures list update.

**Test Flow:**
- Login as commissioner
- Create a league
- Navigate to Fixtures tab
- Verify `fixtures-upload` panel is visible (commissioner only)
- Create sample CSV with 3 fixtures
- Upload CSV file
- Wait for success message
- Verify fixtures list is now visible (not empty state)
- Count fixture rows and verify count increased

**Key Assertions:**
- Upload panel visible for commissioners
- CSV upload succeeds
- Success message appears
- Fixtures list updates with new fixtures
- Empty state is removed

---

### 5. `socket_status_fixture_refresh.spec.ts` (PRIMARY ACCEPTANCE TEST)
**Purpose:** Verify real-time Socket.IO fixture updates across multiple browser contexts.

**Test Flow:**
- Open 2 browser contexts (Tab A: Commissioner, Tab B: Participant)
- Commissioner creates league
- Participant joins league
- Both navigate to dashboard Fixtures tab
- Both see empty state initially
- Commissioner (Tab A) uploads CSV with fixtures
- Tab A sees fixtures immediately
- **ACCEPTANCE:** Tab B sees fixtures update within 1-2 seconds WITHOUT page reload
- Verify Socket.IO `fixtures_updated` event triggered the refresh

**Key Assertions:**
- Both contexts see empty state initially
- CSV upload succeeds in Tab A
- Tab B receives real-time update (fixtures list appears)
- Update happens within 1-2 seconds
- No page reload required in Tab B

---

## Running the Tests

### Run all My Competitions tests:
```bash
npx playwright test tests/e2e/me_competitions_list.spec.ts
npx playwright test tests/e2e/competition_dashboard_tabs.spec.ts
npx playwright test tests/e2e/league_table_zero_state.spec.ts
npx playwright test tests/e2e/fixtures_import_csv.spec.ts
npx playwright test tests/e2e/socket_status_fixture_refresh.spec.ts
```

### Run all tests at once:
```bash
npx playwright test tests/e2e/me_competitions*.spec.ts tests/e2e/competition_dashboard*.spec.ts tests/e2e/league_table*.spec.ts tests/e2e/fixtures*.spec.ts tests/e2e/socket*.spec.ts
```

### Run in headed mode (see browser):
```bash
npx playwright test --headed tests/e2e/me_competitions_list.spec.ts
```

### Run with debug mode:
```bash
npx playwright test --debug tests/e2e/socket_status_fixture_refresh.spec.ts
```

---

## Test Design Principles

1. **Stability:** Each test creates its own data (users, leagues) to avoid conflicts
2. **Non-flaky:** Proper waits using `waitForSelector` with timeouts
3. **Isolation:** Tests use unique emails and league names with timestamps
4. **Clear Assertions:** Explicit checks for testids and UI states
5. **Cleanup:** Temporary files (CSV) are cleaned up after tests

---

## TestIDs Used

From Prompts 1-4, the following testids are verified:

**My Competitions Page:**
- `my-competitions-page`
- `comp-card-{leagueId}`
- `comp-status`
- `comp-view-btn`

**Competition Dashboard:**
- `comp-dashboard`
- `tab-summary`
- `tab-table`
- `tab-fixtures`

**Summary Tab:**
- `summary-roster`
- `summary-budget`
- `summary-managers`

**League Table Tab:**
- `table-grid`
- `table-row-{userId}`

**Fixtures Tab:**
- `fixtures-list`
- `fixtures-upload`
- `fixtures-empty`

---

## Expected Results

All 5 tests should pass, verifying:
- ✅ My Competitions list and navigation
- ✅ Dashboard tab switching
- ✅ Zero-point league table initialization
- ✅ CSV upload and fixtures display
- ✅ Real-time Socket.IO updates (PRIMARY acceptance criterion)
