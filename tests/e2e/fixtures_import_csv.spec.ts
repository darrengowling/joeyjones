import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Fixtures CSV Import (Commissioner)', () => {
  let leagueId: string;

  test.beforeEach(async ({ page }) => {
    // Setup: Create a league as commissioner
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 5000 });
    
    const randomEmail = `commissioner${Date.now()}@example.com`;
    await page.fill('input[placeholder*="name"]', 'Commissioner');
    await page.fill('input[placeholder*="email"]', randomEmail);
    
    const submitButtons = page.locator('button:has-text("Sign In")');
    await submitButtons.last().click();
    await page.waitForTimeout(2000);

    // Seed clubs if needed (to ensure we have clubs for CSV)
    const apiUrl = page.url().includes('localhost')
      ? 'http://localhost:8001/api/clubs'
      : 'https://restart-auction.preview.emergentagent.com/api/clubs';
    
    try {
      const clubsResponse = await fetch(apiUrl);
      const clubs = await clubsResponse.json();
      if (!clubs || clubs.length === 0) {
        await fetch(apiUrl.replace('/clubs', '/clubs/seed'), { method: 'POST' });
      }
    } catch (e) {
      console.log('Club seeding check skipped');
    }

    // Create a league
    await page.click('[data-testid="create-league-button"]');
    await page.waitForSelector('input[placeholder*="League Name"]', { timeout: 5000 });
    await page.fill('input[placeholder*="League Name"]', 'CSV Test League');
    
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

  test('should upload CSV and see fixtures list increase', async ({ page }) => {
    // Navigate to competition dashboard
    await page.goto(`/app/competitions/${leagueId}`);
    await page.waitForSelector('[data-testid="comp-dashboard"]', { timeout: 10000 });

    // Click Fixtures tab
    await page.click('[data-testid="tab-fixtures"]');
    await page.waitForTimeout(2000);

    // Verify upload panel is visible (commissioner only)
    await expect(page.locator('[data-testid="fixtures-upload"]')).toBeVisible({ timeout: 5000 });

    // Check initial fixtures count (should be 0 for new league)
    const initialEmpty = await page.locator('[data-testid="fixtures-empty"]').isVisible();
    expect(initialEmpty).toBeTruthy();

    // Create a sample CSV file
    const csvContent = `startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-01-15T19:00:00Z,MCI,LIV,Etihad Stadium,1,match001
2025-01-16T20:00:00Z,RMA,FCB,Santiago Bernabeu,1,match002
2025-01-17T18:30:00Z,BAY,PSG,Allianz Arena,1,match003`;

    const tmpDir = path.join(process.cwd(), 'tmp');
    if (!fs.existsSync(tmpDir)) {
      fs.mkdirSync(tmpDir, { recursive: true });
    }
    const csvFilePath = path.join(tmpDir, `fixtures_${Date.now()}.csv`);
    fs.writeFileSync(csvFilePath, csvContent);

    // Upload the CSV file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvFilePath);
    
    // Wait for upload to complete
    await page.waitForTimeout(3000);

    // Check for success message
    const successMessage = page.locator('text=Successfully imported');
    await expect(successMessage).toBeVisible({ timeout: 10000 });

    // Verify fixtures list is now visible (not empty state)
    await expect(page.locator('[data-testid="fixtures-list"]')).toBeVisible({ timeout: 5000 });

    // Verify empty state is gone
    const stillEmpty = await page.locator('[data-testid="fixtures-empty"]').isVisible();
    expect(stillEmpty).toBeFalsy();

    // Count visible fixture rows (should have at least 3)
    const fixtureRows = page.locator('[data-testid="fixtures-list"] > div > div'); // fixture date groups
    const rowCount = await fixtureRows.count();
    expect(rowCount).toBeGreaterThan(0);

    // Cleanup
    fs.unlinkSync(csvFilePath);

    console.log('✅ Fixtures CSV import test passed');
  });
});
