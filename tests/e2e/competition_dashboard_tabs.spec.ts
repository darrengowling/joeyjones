import { test, expect } from '@playwright/test';

test.describe('Competition Dashboard Tabs', () => {
  let leagueId: string;

  test.beforeEach(async ({ page }) => {
    // Setup: Create a league and get its ID
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 5000 });
    
    const randomEmail = `testuser${Date.now()}@example.com`;
    await page.fill('input[placeholder*="name"]', 'Test User');
    await page.fill('input[placeholder*="email"]', randomEmail);
    
    const submitButtons = page.locator('button:has-text("Sign In")');
    await submitButtons.last().click();
    await page.waitForTimeout(2000);

    // Create a league
    await page.click('[data-testid="create-league-button"]');
    await page.waitForSelector('input[placeholder*="League Name"]', { timeout: 5000 });
    await page.fill('input[placeholder*="League Name"]', 'Tab Test League');
    
    const createCompButtons = page.locator('button:has-text("Create Competition")');
    await createCompButtons.click();
    await page.waitForTimeout(2000);

    // Extract league ID from URL (should be on league detail page)
    const currentUrl = page.url();
    const match = currentUrl.match(/\/league\/([^\/]+)/);
    if (match) {
      leagueId = match[1];
    }
  });

  test('should switch between dashboard tabs and verify testids', async ({ page }) => {
    // Navigate to competition dashboard
    await page.goto(`/app/competitions/${leagueId}`);
    await page.waitForSelector('[data-testid="comp-dashboard"]', { timeout: 10000 });

    // Assert dashboard is loaded
    await expect(page.locator('[data-testid="comp-dashboard"]')).toBeVisible();

    // Assert all tab buttons are visible
    await expect(page.locator('[data-testid="tab-summary"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-fixtures"]')).toBeVisible();

    // Switch to League Table tab
    await page.click('[data-testid="tab-table"]');
    await page.waitForTimeout(1000);

    // Assert League Table content is visible
    await expect(page.locator('[data-testid="table-grid"]')).toBeVisible({ timeout: 5000 });

    // Switch to Fixtures tab
    await page.click('[data-testid="tab-fixtures"]');
    await page.waitForTimeout(1000);

    // Assert Fixtures content is visible (either empty state or list)
    const fixturesList = page.locator('[data-testid="fixtures-list"]');
    const fixturesEmpty = page.locator('[data-testid="fixtures-empty"]');
    
    // One of these should be visible
    const isListVisible = await fixturesList.isVisible();
    const isEmptyVisible = await fixturesEmpty.isVisible();
    expect(isListVisible || isEmptyVisible).toBeTruthy();

    // Switch back to Summary tab
    await page.click('[data-testid="tab-summary"]');
    await page.waitForTimeout(1000);

    // Assert Summary content is visible
    await expect(page.locator('[data-testid="summary-roster"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="summary-budget"]')).toBeVisible();
    await expect(page.locator('[data-testid="summary-managers"]')).toBeVisible();

    console.log('✅ Competition Dashboard tabs test passed');
  });
});
