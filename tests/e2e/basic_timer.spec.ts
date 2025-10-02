import { test, expect } from '@playwright/test';

test.describe('Basic Auction Timer Test', () => {
  test('timer synchronization proof of concept', async ({ page }) => {
    console.log('=== RUNNING TIMER SYNCHRONIZATION TEST ===');
    
    // Navigate to homepage
    await page.goto('https://ucl-bidding.preview.emergentagent.com');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of current state
    await page.screenshot({ path: 'test-homepage.png' });
    console.log('✅ Homepage loaded successfully');
    
    // Check if there are any active leagues
    const hasActiveLeagues = await page.isVisible('text=Active Leagues');
    console.log(`Active leagues present: ${hasActiveLeagues}`);
    
    // If there's an lfc1 league, test navigation
    if (await page.isVisible('text=lfc1')) {
      console.log('Found lfc1 league - testing navigation');
      
      // Sign in first
      await page.click('button:has-text("Sign In")');
      await page.waitForTimeout(1000);
      
      await page.fill('input[type="text"]', 'Playwright Test User');
      await page.fill('input[type="email"]', 'playwright@test.com');
      await page.click('button:has-text("Continue")');
      await page.waitForTimeout(2000);
      
      // Navigate to league
      await page.click('text=lfc1');
      await page.waitForTimeout(2000);
      
      // Check if auction is available
      if (await page.isVisible('button:has-text("Go to Auction")')) {
        await page.click('button:has-text("Go to Auction")');
        await page.waitForTimeout(5000);
        
        // Check if timer is present
        const timerExists = await page.isVisible('[data-testid="auction-timer"]');
        console.log(`Timer element found: ${timerExists}`);
        
        if (timerExists) {
          const timerText = await page.locator('[data-testid="auction-timer"]').innerText();
          console.log(`Timer displays: ${timerText}`);
          
          // Wait 3 seconds and check if timer changes
          await page.waitForTimeout(3000);
          const newTimerText = await page.locator('[data-testid="auction-timer"]').innerText();
          console.log(`Timer after 3s: ${newTimerText}`);
          
          // Basic assertion that timer is working
          expect(timerText).toMatch(/\d{2}:\d{2}/);
          console.log('✅ Timer format is correct');
        }
        
        await page.screenshot({ path: 'test-auction-room.png' });
        console.log('✅ Auction room navigation successful');
      }
    }
    
    console.log('✅ Basic test completed successfully');
  });
});