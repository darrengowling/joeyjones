import { test, expect } from '@playwright/test';

test.describe('League Table Zero State', () => {
  let leagueId: string;
  let userId: string;

  test.beforeEach(async ({ page }) => {
    // Setup: Create a league
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 5000 });
    
    const randomEmail = `testuser${Date.now()}@example.com`;
    await page.fill('input[placeholder*="name"]', 'Test Manager');
    await page.fill('input[placeholder*="email"]', randomEmail);
    
    const submitButtons = page.locator('button:has-text("Sign In")');
    await submitButtons.last().click();
    await page.waitForTimeout(2000);

    // Create a league
    await page.click('[data-testid="create-league-button"]');
    await page.waitForSelector('input[placeholder*="League Name"]', { timeout: 5000 });
    await page.fill('input[placeholder*="League Name"]', 'Zero Points League');
    
    const createCompButtons = page.locator('button:has-text("Create Competition")');
    await createCompButtons.click();
    await page.waitForTimeout(2000);

    // Extract league ID from URL
    const currentUrl = page.url();
    const match = currentUrl.match(/\/league\/([^\/]+)/);
    if (match) {
      leagueId = match[1];
    }
  });

  test('should show zero points for all managers in league table', async ({ page, request }) => {
    // Navigate to competition dashboard
    await page.goto(`/app/competitions/${leagueId}`);
    await page.waitForSelector('[data-testid="comp-dashboard"]', { timeout: 10000 });

    // Click League Table tab
    await page.click('[data-testid="tab-table"]');
    await page.waitForTimeout(2000);

    // Wait for table to load
    await page.waitForSelector('[data-testid="table-grid"]', { timeout: 10000 });

    // Assert table grid is visible
    await expect(page.locator('[data-testid="table-grid"]')).toBeVisible();

    // Check that at least one table row exists
    const tableRows = page.locator('[data-testid^="table-row-"]');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThan(0);

    // Verify all managers have 0.0 points
    const pointsCells = page.locator('tbody tr td:nth-child(3)'); // 3rd column is Points
    const pointsCount = await pointsCells.count();
    
    for (let i = 0; i < pointsCount; i++) {
      const pointsText = await pointsCells.nth(i).textContent();
      expect(pointsText?.trim()).toBe('0.0');
    }

    // Verify tiebreakers are also 0
    const tiebreaker1Cells = page.locator('tbody tr td:nth-child(4)'); // Goals/Runs
    const tiebreaker2Cells = page.locator('tbody tr td:nth-child(5)'); // Wins/Wickets
    
    const tb1Count = await tiebreaker1Cells.count();
    for (let i = 0; i < tb1Count; i++) {
      const tb1Text = await tiebreaker1Cells.nth(i).textContent();
      expect(tb1Text?.trim()).toBe('0');
    }

    const tb2Count = await tiebreaker2Cells.count();
    for (let i = 0; i < tb2Count; i++) {
      const tb2Text = await tiebreaker2Cells.nth(i).textContent();
      expect(tb2Text?.trim()).toBe('0');
    }

    // Verify API response also has zero points
    const apiUrl = page.url().includes('localhost') 
      ? `http://localhost:8001/api/leagues/${leagueId}/standings`
      : `https://prelaunch-fix.preview.emergentagent.com/api/leagues/${leagueId}/standings`;
    
    const apiResponse = await request.get(apiUrl);
    expect(apiResponse.status()).toBe(200);
    
    const standings = await apiResponse.json();
    expect(standings.table).toBeDefined();
    expect(standings.table.length).toBeGreaterThan(0);
    
    // Verify all entries have 0 points in API response
    standings.table.forEach((entry: any) => {
      expect(entry.points).toBe(0);
    });

    console.log('✅ League Table zero state test passed');
  });
});
