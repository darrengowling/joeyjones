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
    test.setTimeout(120000); // 2 minutes for complete workflow
    
    // Step 1: Auth - Sign in
    console.log('Step 1: Authentication');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Click Sign In
    await page.click('button:has-text("Sign In")');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 10000 });
    
    // Fill in details
    await page.fill('input[placeholder*="name"]', testName);
    await page.fill('input[placeholder*="email"]', testEmail);
    await page.click('button:has-text("Continue")');
    
    // Wait for successful sign in
    await page.waitForSelector('text=Create Your Competition', { timeout: 10000 });
    console.log('✅ Authentication successful');

    // Step 2: Create Cricket League
    console.log('Step 2: Creating Cricket League');
    await page.click('button:has-text("Create Your Competition")');
    await page.waitForSelector('[data-testid="create-sport-select"]', { timeout: 10000 });
    
    // Select Cricket sport
    await page.selectOption('[data-testid="create-sport-select"]', 'cricket');
    
    // Fill league details
    await page.fill('[data-testid="league-name-input"]', leagueName);
    await page.fill('[data-testid="league-budget-input"]', '100000000'); // £100M
    await page.fill('[data-testid="league-min-managers-input"]', '2');
    await page.fill('[data-testid="league-max-managers-input"]', '4');
    await page.fill('[data-testid="league-club-slots-input"]', '5'); // 5 players per manager
    
    // Create league
    await page.click('[data-testid="create-league-button"]');
    
    // Wait for league detail page
    await page.waitForSelector('h1:has-text("' + leagueName + '")', { timeout: 15000 });
    
    // Extract league ID from URL
    const url = page.url();
    const leagueMatch = url.match(/\/league\/([a-f0-9-]+)/);
    if (leagueMatch) {
      leagueId = leagueMatch[1];
      console.log(`✅ Cricket league created: ${leagueId}`);
    } else {
      throw new Error('Could not extract league ID from URL');
    }

    // Verify cricket-specific UI elements
    await expect(page.locator('text=Player Slots')).toBeVisible();
    await expect(page.locator('text=compete for players')).toBeVisible();
    console.log('✅ Cricket-specific UI verified');

    // Step 3: Start Auction and Verify Player Display
    console.log('Step 3: Starting Auction');
    
    // Start auction
    await page.click('button:has-text("Start Auction")');
    await page.waitForSelector('text=Auction Started', { timeout: 15000 });
    
    // Go to auction room
    await page.click('button:has-text("Go to Auction")');
    await page.waitForLoadState('networkidle');
    
    // Verify Players UI (not Clubs)
    await expect(page.locator('text=Players Available for Ownership')).toBeVisible();
    console.log('✅ Auction shows "Players" instead of "Clubs"');

    // Step 4: Nominate Player and Place Bid
    console.log('Step 4: Player Bidding');
    
    // Wait for timer and current player
    await page.waitForSelector('[data-testid="current-club-name"]', { timeout: 15000 });
    
    // Get current player name
    const currentPlayerName = await page.textContent('[data-testid="current-club-name"]');
    console.log(`Current player: ${currentPlayerName}`);
    
    // Place a bid
    await page.fill('[data-testid="bid-amount-input"]', '5000000'); // £5M bid
    await page.click('[data-testid="submit-bid-button"]');
    
    // Wait for bid confirmation
    await page.waitForSelector('text=Bid placed successfully', { timeout: 10000 });
    console.log('✅ Bid placed successfully');
    
    // Wait for lot to complete (either win or someone else bids higher)
    await page.waitForSelector('text=sold', { timeout: 30000 });
    console.log('✅ Lot completed');

    // Step 5: Upload CSV Scoring Data
    console.log('Step 5: CSV Scoring Upload');
    
    // Create test CSV content
    const csvContent = `matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
M1,P001,54,0,1,0,0
M1,P002,12,3,0,0,1
M1,P003,101,0,0,0,0`;

    // Create temporary CSV file
    const csvPath = path.join(__dirname, 'temp_cricket_scores.csv');
    await fs.writeFile(csvPath, csvContent);
    
    try {
      // Navigate back to league detail page for scoring upload
      await page.goto(`/league/${leagueId}`);
      await page.waitForLoadState('networkidle');
      
      // Look for scoring upload functionality (this might be in a different location)
      // Since we don't have a direct UI for CSV upload in the frontend yet, 
      // let's test the API directly via fetch
      await page.evaluate(async (csvData) => {
        const response = await fetch(`/api/scoring/${window.location.pathname.split('/')[2]}/ingest`, {
          method: 'POST',
          body: (() => {
            const formData = new FormData();
            const blob = new Blob([csvData], { type: 'text/csv' });
            formData.append('file', blob, 'test_scores.csv');
            return formData;
          })()
        });
        
        if (!response.ok) {
          throw new Error(`Scoring upload failed: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Scoring upload result:', result);
        
        // Store result for verification
        (window as any).scoringResult = result;
      }, csvContent);
      
      console.log('✅ CSV scoring data uploaded');

      // Step 6: Verify Leaderboard Totals
      console.log('Step 6: Verifying Leaderboard');
      
      // Get scoring result from page context
      const scoringResult = await page.evaluate(() => (window as any).scoringResult);
      
      if (!scoringResult || !scoringResult.leaderboard) {
        throw new Error('No leaderboard data available');
      }
      
      const leaderboard = scoringResult.leaderboard;
      
      // Find players and verify scores
      const p001 = leaderboard.find((p: any) => p.playerExternalId === 'P001');
      const p002 = leaderboard.find((p: any) => p.playerExternalId === 'P002');
      const p003 = leaderboard.find((p: any) => p.playerExternalId === 'P003');
      
      // Assert P001: 54 runs + 10 (1 catch) + 10 (half-century) = 74
      expect(p001?.totalPoints).toBe(74);
      console.log(`✅ P001 score verified: ${p001?.totalPoints} points (expected 74)`);
      
      // Assert P002: 12 runs + 75 (3 wickets * 25) + 10 (1 runOut) = 97
      expect(p002?.totalPoints).toBe(97);
      console.log(`✅ P002 score verified: ${p002?.totalPoints} points (expected 97)`);
      
      // Assert P003: 101 runs + 10 (half-century) + 25 (century) = 136
      expect(p003?.totalPoints).toBe(136);
      console.log(`✅ P003 score verified: ${p003?.totalPoints} points (expected 136)`);
      
      console.log('✅ All leaderboard totals verified correctly');
      
    } finally {
      // Cleanup: Remove temporary CSV file
      try {
        await fs.unlink(csvPath);
      } catch (e) {
        console.warn('Could not remove temporary CSV file:', e);
      }
    }
    
    console.log('🎉 Cricket smoke test completed successfully!');
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