import { test, expect } from '@playwright/test';

test.describe('My Competitions List', () => {
  test('should navigate to My Competitions page and view dashboard', async ({ page }) => {
    // Navigate to homepage
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

    // Create a league to ensure we have at least one competition
    await page.click('[data-testid="create-league-button"]');
    await page.waitForSelector('input[placeholder*="League Name"]', { timeout: 5000 });
    await page.fill('input[placeholder*="League Name"]', 'Test Competition');
    
    const createCompButtons = page.locator('button:has-text("Create Competition")');
    await createCompButtons.click();
    await page.waitForTimeout(2000);

    // Navigate to My Competitions page
    await page.goto('/app/my-competitions');
    await page.waitForSelector('[data-testid="my-competitions-page"]', { timeout: 10000 });

    // Assert page is loaded
    await expect(page.locator('[data-testid="my-competitions-page"]')).toBeVisible();

    // Assert at least one competition card exists
    const competitionCards = page.locator('[data-testid^="comp-card-"]');
    await expect(competitionCards.first()).toBeVisible({ timeout: 10000 });

    // Click View Dashboard button
    const viewButton = page.locator('[data-testid="comp-view-btn"]').first();
    await viewButton.click();
    await page.waitForTimeout(2000);

    // Assert we landed on the dashboard
    await expect(page.locator('[data-testid="comp-dashboard"]')).toBeVisible({ timeout: 10000 });
    
    console.log('✅ My Competitions list test passed');
  });
});
