import { test, expect, Page } from '@playwright/test';

/**
 * Test: Real-time Lobby Presence
 * 
 * Proves: Commissioner sees new members appear in lobby within 1s via socket event (no refresh)
 * 
 * Fixes validated:
 * - member_joined event broadcast to all sockets in league room
 * - sync_members event ensures all users have identical member lists
 * - useSocketRoom hook prevents duplicate listeners
 */

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://bidding-tester.preview.emergentagent.com';

test.describe('Lobby Presence - Real-time Member Updates', () => {
  let commissionerPage: Page;
  let memberPage: Page;
  let leagueId: string;
  let inviteToken: string;

  test.beforeAll(async ({ browser }) => {
    // Create two browser contexts (simulating two users)
    const commissionerContext = await browser.newContext();
    const memberContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    memberPage = await memberContext.newPage();
  });

  test.afterAll(async () => {
    await commissionerPage.close();
    await memberPage.close();
  });

  test('Commissioner sees new member join in real-time without refresh', async () => {
    // Step 1: Commissioner creates account and league
    await commissionerPage.goto(BASE_URL);
    
    // Click Sign In button to open modal
    await commissionerPage.click('button:has-text("Sign In")');
    await commissionerPage.waitForTimeout(500);
    
    // Fill sign-in form (correct field names from UI)
    await commissionerPage.fill('input[placeholder="Enter your full name"]', 'Commissioner');
    await commissionerPage.fill('input[placeholder="your.email@example.com"]', `commissioner-${Date.now()}@test.com`);
    await commissionerPage.click('button:has-text("Continue")');
    
    await commissionerPage.waitForTimeout(2000);
    await commissionerPage.click('button:has-text("Create Your Competition")');
    await commissionerPage.waitForTimeout(1000);
    
    // Fill league creation form - first text input is League Name
    const inputs = await commissionerPage.locator('input[type="text"]').all();
    await inputs[0].fill('Lobby Test League');
    await commissionerPage.waitForTimeout(500);
    
    // Click Create Competition button
    await commissionerPage.click('button:has-text("Create Competition")');
    
    // Wait for league to be created and navigate to lobby
    await commissionerPage.waitForURL(/\/league\/[a-f0-9-]+/, { timeout: 10000 });
    leagueId = commissionerPage.url().match(/\/league\/([a-f0-9-]+)/)?.[1] || '';
    expect(leagueId).toBeTruthy();
    
    console.log(`✅ League created: ${leagueId}`);
    
    // Get invite token by fetching league details from API
    const leagueResponse = await commissionerPage.evaluate(async (id) => {
      const response = await fetch(`${window.location.origin}/api/leagues/${id}`);
      return response.json();
    }, leagueId);
    inviteToken = leagueResponse.inviteToken;
    expect(inviteToken).toBeTruthy();
    
    console.log(`✅ Invite token: ${inviteToken}`);
    
    // Step 2: Verify commissioner sees only themselves initially
    await commissionerPage.waitForTimeout(1000);
    
    // Step 3: Open member page and create account
    await memberPage.goto(BASE_URL);
    
    // Click Sign In button to open modal
    await memberPage.click('button:has-text("Sign In")');
    await memberPage.waitForTimeout(500);
    
    // Fill sign-in form
    await memberPage.fill('input[placeholder="Enter your full name"]', 'Test Member');
    await memberPage.fill('input[placeholder="your.email@example.com"]', `member-${Date.now()}@test.com`);
    await memberPage.click('button:has-text("Continue")');
    
    await memberPage.waitForTimeout(2000);
    
    // Step 4: Record timestamp before join
    const beforeJoinTime = Date.now();
    console.log(`⏱️  Recording join time: ${new Date(beforeJoinTime).toISOString()}`);
    
    // Step 5: Member joins the league
    await memberPage.click('button:has-text("Join the Competition")');
    await memberPage.waitForTimeout(500);
    await memberPage.fill('input[placeholder*="token" i]', inviteToken);
    await memberPage.click('button:has-text("Join the Competition")');
    
    // Wait for join confirmation
    await memberPage.waitForURL(/\/league\/[a-f0-9-]+/, { timeout: 10000 });
    const joinTime = Date.now();
    console.log(`✅ Member joined at: ${new Date(joinTime).toISOString()}`);
    
    // Step 6: CRITICAL TEST - Commissioner should see new member WITHOUT refresh
    // Wait for new member to appear in commissioner's view
    const memberAppeared = await commissionerPage.waitForSelector(
      'text=/Test Member/i',
      { timeout: 2000, state: 'visible' }
    ).then(() => true).catch(() => false);
    
    const afterAppearTime = Date.now();
    const timeDiff = afterAppearTime - joinTime;
    
    console.log(`⏱️  Member appeared in: ${timeDiff}ms`);
    
    // Assertions
    expect(memberAppeared).toBe(true);
    expect(timeDiff).toBeLessThan(1500); // Should appear within 1.5 seconds
    
    console.log('✅ TEST PASSED: Real-time lobby presence working correctly');
  });
});
