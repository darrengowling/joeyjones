import { test, expect } from '@playwright/test';

// Guard: Skip cricket tests if SPORTS_CRICKET_ENABLED is not 'true'
test.describe.configure({ mode: process.env.SPORTS_CRICKET_ENABLED === 'true' ? 'default' : 'skip' });

test.describe('Cricket Smoke Test', () => {
  let leagueId: string;
  let userId: string;
  const testEmail = `cricket.smoke.${Date.now()}@test.com`;
  const testName = `Cricket Smoke Tester`;
  const leagueName = `Cricket Smoke League ${Date.now()}`;

  test.beforeAll(async () => {
    console.log('🏏 Cricket smoke tests starting...');
  });

  test('Complete cricket workflow: Auth → Create League → Auction → Scoring', async ({ page }) => {
    test.setTimeout(90000); // 90 seconds timeout
    
    console.log('🏏 Starting Cricket smoke test...');

    // Step 1: Auth - Sign in
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    await page.click('button:has-text("Sign In")');
    await page.fill('input[placeholder*="name"]', testName);
    await page.fill('input[placeholder*="email"]', testEmail);
    await page.click('button:has-text("Continue")');
    await page.waitForSelector('text=Create Your Competition', { timeout: 10000 });

    // Step 2: Create Cricket League  
    await page.click('button:has-text("Create Your Competition")');
    await page.waitForSelector('[data-testid="create-sport-select"]', { timeout: 10000 });
    
    // Verify cricket option exists (flag test)
    const cricketOption = await page.$('option[value="cricket"]');
    expect(cricketOption).toBeTruthy();
    
    await page.selectOption('[data-testid="create-sport-select"]', 'cricket');
    await page.fill('[data-testid="league-name-input"]', leagueName);
    await page.click('[data-testid="create-league-button"]');
    
    await page.waitForSelector(`h1:has-text("${leagueName}")`, { timeout: 15000 });
    
    // Extract league ID from URL
    leagueId = page.url().match(/\/league\/([a-f0-9-]+)/)?.[1] || '';
    expect(leagueId).toBeTruthy();

    // Step 3: Verify Cricket UI Elements
    await expect(page.locator('text=Player Slots')).toBeVisible();
    await expect(page.locator('text=compete for players')).toBeVisible();

    // Step 4: Start Auction 
    await page.click('button:has-text("Start Auction")');
    await page.waitForSelector('text=Auction Started', { timeout: 15000 });
    
    await page.click('button:has-text("Go to Auction")');
    await page.waitForLoadState('networkidle');
    
    // Verify "Players" not "Clubs"
    await expect(page.locator('text=Players Available for Ownership')).toBeVisible();

    // Step 5: Test CSV Scoring via API
    const csvContent = `matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
M1,P001,54,0,1,0,0
M1,P002,12,3,0,0,1
M1,P003,101,0,0,0,0`;

    // Upload scoring data and verify points
    const scoringResult = await page.evaluate(async ([csvData, leagueId]) => {
      const formData = new FormData();
      const blob = new Blob([csvData], { type: 'text/csv' });
      formData.append('file', blob, 'test_scores.csv');
      
      const response = await fetch(`/api/scoring/${leagueId}/ingest`, {
        method: 'POST',
        body: formData
      });
      
      return response.json();
    }, [csvContent, leagueId]);

    // Step 6: Verify Leaderboard Calculations
    expect(scoringResult.leaderboard).toBeTruthy();
    
    const p001 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P001');
    const p002 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P002');  
    const p003 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P003');
    
    // P001: 54 runs + 10(catch) + 10(half-century) = 74
    expect(p001?.totalPoints).toBe(74);
    
    // P002: 12 runs + 75(3 wickets) + 10(runOut) = 97  
    expect(p002?.totalPoints).toBe(97);
    
    // P003: 101 runs + 10(half-century) + 25(century) = 136
    expect(p003?.totalPoints).toBe(136);
    
    console.log('✅ Cricket smoke test passed!');
  });

  test.afterAll(async () => {
    console.log('🏏 Cricket smoke tests completed');
  });
});

// Additional test to ensure cricket flag is working correctly
test.describe('Cricket Flag Verification', () => {
  test('Cricket features should only be available when flag is enabled', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Sign in first
    await page.click('button:has-text("Sign In")');
    await page.fill('input[placeholder*="name"]', 'Flag Tester');
    await page.fill('input[placeholder*="email"]', `flag.test.${Date.now()}@test.com`);
    await page.click('button:has-text("Continue")');
    
    // Go to create league
    await page.click('button:has-text("Create Your Competition")');
    await page.waitForSelector('[data-testid="create-sport-select"]', { timeout: 10000 });
    
    // Verify cricket option is available when flag is enabled
    const cricketOption = await page.$('option[value="cricket"]');
    
    if (process.env.SPORTS_CRICKET_ENABLED === 'true') {
      expect(cricketOption).toBeTruthy();
      console.log('✅ Cricket option available with flag enabled');
    } else {
      expect(cricketOption).toBeFalsy();
      console.log('✅ Cricket option hidden with flag disabled');
    }
  });
});