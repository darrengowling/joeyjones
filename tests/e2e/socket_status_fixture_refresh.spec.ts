import { test, expect, chromium } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Socket.IO Real-time Fixture Refresh', () => {
  test('should refresh fixtures in Tab B when Tab A uploads CSV', async () => {
    const browser = await chromium.launch();
    
    // Context A: Commissioner
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    // Context B: Another user
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    let leagueId: string;
    let inviteToken: string;

    try {
      // === SETUP: Create league and join from both contexts ===

      // Context A: Login as commissioner
      await pageA.goto('/');
      await pageA.waitForLoadState('networkidle');
      await pageA.click('[data-testid="login-button"]');
      await pageA.waitForSelector('input[placeholder*="name"]', { timeout: 5000 });
      
      const commissionerEmail = `commissioner${Date.now()}@example.com`;
      await pageA.fill('input[placeholder*="name"]', 'Commissioner');
      await pageA.fill('input[placeholder*="email"]', commissionerEmail);
      
      let submitButtons = pageA.locator('button:has-text("Sign In")');
      await submitButtons.last().click();
      await pageA.waitForTimeout(2000);

      // Create a league
      await pageA.click('[data-testid="create-league-button"]');
      await pageA.waitForSelector('input[placeholder*="League Name"]', { timeout: 5000 });
      await pageA.fill('input[placeholder*="League Name"]', 'Socket Test League');
      
      const createCompButtons = pageA.locator('button:has-text("Create Competition")');
      await createCompButtons.click();
      
      // Intercept alert to get invite token
      pageA.on('dialog', async dialog => {
        const message = dialog.message();
        const tokenMatch = message.match(/invite token.*?:\s*([a-zA-Z0-9-]+)/);
        if (tokenMatch) {
          inviteToken = tokenMatch[1];
        }
        await dialog.accept();
      });
      
      await pageA.waitForTimeout(3000);

      // Extract league ID from URL
      const currentUrl = pageA.url();
      const match = currentUrl.match(/\/league\/([^\/]+)/);
      if (match) {
        leagueId = match[1];
      }

      expect(leagueId).toBeTruthy();

      // Context B: Login as participant
      await pageB.goto('/');
      await pageB.waitForLoadState('networkidle');
      await pageB.click('[data-testid="login-button"]');
      await pageB.waitForSelector('input[placeholder*="name"]', { timeout: 5000 });
      
      const participantEmail = `participant${Date.now()}@example.com`;
      await pageB.fill('input[placeholder*="name"]', 'Participant');
      await pageB.fill('input[placeholder*="email"]', participantEmail);
      
      submitButtons = pageB.locator('button:has-text("Sign In")');
      await submitButtons.last().click();
      await pageB.waitForTimeout(2000);

      // Join the league if we have invite token
      if (inviteToken) {
        await pageB.click('[data-testid="join-league-button"]');
        await pageB.waitForSelector('input[placeholder*="token"]', { timeout: 5000 });
        await pageB.fill('input[placeholder*="token"]', inviteToken);
        
        const joinButtons = pageB.locator('button:has-text("Join")');
        await joinButtons.click();
        await pageB.waitForTimeout(2000);

        pageB.on('dialog', async dialog => {
          await dialog.accept();
        });
      }

      // === TEST: Real-time fixture refresh ===

      // Both contexts: Navigate to dashboard fixtures tab
      await pageA.goto(`/app/competitions/${leagueId}`);
      await pageA.waitForSelector('[data-testid="comp-dashboard"]', { timeout: 10000 });
      await pageA.click('[data-testid="tab-fixtures"]');
      await pageA.waitForTimeout(2000);

      await pageB.goto(`/app/competitions/${leagueId}`);
      await pageB.waitForSelector('[data-testid="comp-dashboard"]', { timeout: 10000 });
      await pageB.click('[data-testid="tab-fixtures"]');
      await pageB.waitForTimeout(2000);

      // Verify both see empty state initially
      const emptyA = await pageA.locator('[data-testid="fixtures-empty"]').isVisible();
      const emptyB = await pageB.locator('[data-testid="fixtures-empty"]').isVisible();
      expect(emptyA).toBeTruthy();
      expect(emptyB).toBeTruthy();

      // Context A: Upload CSV
      const csvContent = `startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId
2025-02-15T19:00:00Z,MCI,LIV,Etihad Stadium,1,sockettest001
2025-02-16T20:00:00Z,RMA,FCB,Santiago Bernabeu,1,sockettest002`;

      const tmpDir = path.join(process.cwd(), 'tmp');
      if (!fs.existsSync(tmpDir)) {
        fs.mkdirSync(tmpDir, { recursive: true });
      }
      const csvFilePath = path.join(tmpDir, `socket_fixtures_${Date.now()}.csv`);
      fs.writeFileSync(csvFilePath, csvContent);

      const fileInput = pageA.locator('input[type="file"]');
      await fileInput.setInputFiles(csvFilePath);
      
      // Wait for upload to complete in Context A
      await pageA.waitForTimeout(2000);

      // Check Context A sees fixtures
      const successMessage = pageA.locator('text=Successfully imported');
      await expect(successMessage).toBeVisible({ timeout: 10000 });
      await expect(pageA.locator('[data-testid="fixtures-list"]')).toBeVisible({ timeout: 5000 });

      // === ACCEPTANCE TEST: Context B should see fixtures update within 1-2s ===
      console.log('⏳ Waiting for real-time update in Context B...');
      
      // Wait for fixtures list to appear in Context B (real-time update)
      await expect(pageB.locator('[data-testid="fixtures-list"]')).toBeVisible({ timeout: 5000 });
      
      // Verify empty state is gone in Context B
      const stillEmptyB = await pageB.locator('[data-testid="fixtures-empty"]').isVisible();
      expect(stillEmptyB).toBeFalsy();

      // Verify Context B has fixtures
      const fixtureRowsB = pageB.locator('[data-testid="fixtures-list"] > div > div');
      const rowCountB = await fixtureRowsB.count();
      expect(rowCountB).toBeGreaterThan(0);

      console.log('✅ Socket.IO real-time fixture refresh test passed');

      // Cleanup
      fs.unlinkSync(csvFilePath);

    } finally {
      await contextA.close();
      await contextB.close();
      await browser.close();
    }
  });
});
