import { test, expect, Page } from '@playwright/test';

/**
 * Test: Real-time Enter Auction Room Button
 * 
 * Proves: When commissioner starts auction, all users see "Enter Auction Room" button
 *         appear immediately via socket event (no refresh)
 * 
 * Fixes validated:
 * - league_status_changed event with status: 'auction_started'
 * - Event broadcast to all sockets in league room
 * - Button appears instantly on all client UIs
 */

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://auction-hardening.preview.emergentagent.com';

test.describe('Enter Auction Room Button - Real-time Appearance', () => {
  let commissionerPage: Page;
  let member1Page: Page;
  let member2Page: Page;
  let leagueId: string;
  let inviteToken: string;

  test.beforeAll(async ({ browser }) => {
    const commissionerContext = await browser.newContext();
    const member1Context = await browser.newContext();
    const member2Context = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    member1Page = await member1Context.newPage();
    member2Page = await member2Context.newPage();
  });

  test.afterAll(async () => {
    await commissionerPage.close();
    await member1Page.close();
    await member2Page.close();
  });

  test('All users see Enter Auction Room button appear via socket event', async () => {
    // Step 1: Commissioner creates league
    await commissionerPage.goto(BASE_URL);
    await commissionerPage.click('button:has-text("Sign In")');
    await commissionerPage.waitForTimeout(500);
    await commissionerPage.fill('input[placeholder="Enter your full name"]', 'Commissioner');
    await commissionerPage.fill('input[placeholder="your.email@example.com"]', `comm-${Date.now()}@test.com`);
    await commissionerPage.click('button:has-text("Continue")');
    
    await commissionerPage.waitForTimeout(2000);
    await commissionerPage.click('button:has-text("Create Your Competition")');
    await commissionerPage.waitForTimeout(1000);
    
    const inputs = await commissionerPage.locator('input[type="text"]').all();
    await inputs[0].fill('Button Test League');
    await commissionerPage.waitForTimeout(500);
    await commissionerPage.click('button:has-text("Create Competition")');
    
    await commissionerPage.waitForURL(/\/league\/[a-f0-9-]+/, { timeout: 10000 });
    leagueId = commissionerPage.url().match(/\/league\/([a-f0-9-]+)/)?.[1] || '';
    
    const leagueResponse = await commissionerPage.evaluate(async (id) => {
      const response = await fetch(`${window.location.origin}/api/leagues/${id}`);
      return response.json();
    }, leagueId);
    inviteToken = leagueResponse.inviteToken;
    
    console.log(`✅ League created: ${leagueId}`);
    console.log(`✅ Invite token: ${inviteToken}`);
    
    // Step 2: Two members join the league
    for (const [index, page] of [[1, member1Page], [2, member2Page]] as [number, Page][]) {
      await page.goto(BASE_URL);
      await page.click('button:has-text("Sign In")');
      await page.waitForTimeout(500);
      await page.fill('input[placeholder="Enter your full name"]', `Member ${index}`);
      await page.fill('input[placeholder="your.email@example.com"]', `member${index}-${Date.now()}@test.com`);
      await page.click('button:has-text("Continue")');
      
      await page.waitForTimeout(2000);
      await page.click('button:has-text("Join the Competition")');
      await page.waitForTimeout(500);
      await page.fill('input[placeholder*="token" i]', inviteToken);
      await page.click('button:has-text("Join the Competition")');
      
      await page.waitForURL(/\/league\/[a-f0-9-]+/, { timeout: 10000 });
      console.log(`✅ Member ${index} joined`);
    }
    
    // Step 3: Wait a moment for all WebSocket connections to stabilize
    await commissionerPage.waitForTimeout(1000);
    
    // Step 4: Verify button is NOT visible before auction starts
    const buttonBeforeStart = await member1Page.locator('text=/Enter.*Auction.*Room/i').count();
    console.log(`📊 Button visible before start: ${buttonBeforeStart}`);
    expect(buttonBeforeStart).toBe(0);
    
    // Step 5: Record timestamp and start auction
    const beforeStartTime = Date.now();
    console.log(`⏱️  Starting auction at: ${new Date(beforeStartTime).toISOString()}`);
    
    // Use the data-testid attribute for more reliable selection
    await commissionerPage.click('[data-testid="start-auction-button"]');
    
    // Wait for auction to start
    await commissionerPage.waitForTimeout(500);
    
    const auctionStartedTime = Date.now();
    console.log(`✅ Auction started at: ${new Date(auctionStartedTime).toISOString()}`);
    
    // Step 6: CRITICAL TEST - Both members should see button WITHOUT refresh
    const member1ButtonPromise = member1Page.waitForSelector(
      'text=/Enter.*Auction.*Room/i',
      { timeout: 2000, state: 'visible' }
    ).then(() => Date.now());
    
    const member2ButtonPromise = member2Page.waitForSelector(
      'text=/Enter.*Auction.*Room/i',
      { timeout: 2000, state: 'visible' }
    ).then(() => Date.now());
    
    const [member1ButtonTime, member2ButtonTime] = await Promise.all([
      member1ButtonPromise,
      member2ButtonPromise
    ]);
    
    const member1Delay = member1ButtonTime - auctionStartedTime;
    const member2Delay = member2ButtonTime - auctionStartedTime;
    
    console.log(`⏱️  Member 1 saw button in: ${member1Delay}ms`);
    console.log(`⏱️  Member 2 saw button in: ${member2Delay}ms`);
    
    // Assertions
    expect(member1Delay).toBeLessThan(1500); // Should appear within 1.5 seconds
    expect(member2Delay).toBeLessThan(1500);
    
    // Step 7: Verify all users can see the button
    const member1Button = await member1Page.locator('text=/Enter.*Auction.*Room/i').count();
    const member2Button = await member2Page.locator('text=/Enter.*Auction.*Room/i').count();
    
    console.log(`📊 Member 1 sees button: ${member1Button > 0}`);
    console.log(`📊 Member 2 sees button: ${member2Button > 0}`);
    
    expect(member1Button).toBeGreaterThan(0);
    expect(member2Button).toBeGreaterThan(0);
    
    // Step 8: Verify buttons are clickable (navigate to auction room)
    await member1Page.click('text=/Enter.*Auction.*Room/i');
    await member1Page.waitForURL(/\/auction\/[a-f0-9-]+/, { timeout: 5000 });
    console.log(`✅ Member 1 successfully entered auction room`);
    
    await member2Page.click('text=/Enter.*Auction.*Room/i');
    await member2Page.waitForURL(/\/auction\/[a-f0-9-]+/, { timeout: 5000 });
    console.log(`✅ Member 2 successfully entered auction room`);
    
    console.log('✅ TEST PASSED: Real-time auction button appearance working correctly');
  });
});
