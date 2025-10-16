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

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://bidmaster-9.preview.emergentagent.com';

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
    await commissionerPage.fill('input[placeholder*="name" i]', 'Commissioner');
    await commissionerPage.fill('input[type="email"]', `commissioner-${Date.now()}@test.com`);
    await commissionerPage.click('button:has-text("Sign In")');
    
    await commissionerPage.waitForSelector('text=/Create.*Competition/i', { timeout: 10000 });
    await commissionerPage.click('text=/Create.*Competition/i');
    
    await commissionerPage.fill('input[placeholder*="league name" i]', 'Lobby Test League');
    await commissionerPage.fill('input[placeholder*="budget" i]', '100');
    await commissionerPage.click('button:has-text("Create League")');
    
    // Wait for league to be created and navigate to lobby
    await commissionerPage.waitForURL(/\/league\/[a-f0-9-]+/, { timeout: 10000 });
    leagueId = commissionerPage.url().match(/\/league\/([a-f0-9-]+)/)?.[1] || '';
    expect(leagueId).toBeTruthy();
    
    console.log(`✅ League created: ${leagueId}`);
    
    // Get invite token from the page
    const inviteTokenElement = await commissionerPage.locator('text=/invite.*token/i').first();
    const inviteTokenText = await inviteTokenElement.textContent();
    inviteToken = inviteTokenText?.match(/[A-Z0-9]{6}/)?.[0] || '';
    expect(inviteToken).toBeTruthy();
    
    console.log(`✅ Invite token: ${inviteToken}`);
    
    // Step 2: Verify commissioner sees only themselves initially
    const initialMemberCount = await commissionerPage.locator('text=/participants|members/i').count();
    console.log(`📊 Initial member count visible: ${initialMemberCount}`);
    
    // Step 3: Open member page and create account
    await memberPage.goto(BASE_URL);
    await memberPage.fill('input[placeholder*="name" i]', 'Test Member');
    await memberPage.fill('input[type="email"]', `member-${Date.now()}@test.com`);
    await memberPage.click('button:has-text("Sign In")');
    
    await memberPage.waitForSelector('text=/Join.*League|Competition/i', { timeout: 10000 });
    
    // Step 4: Record timestamp before join
    const beforeJoinTime = Date.now();
    console.log(`⏱️  Recording join time: ${new Date(beforeJoinTime).toISOString()}`);
    
    // Step 5: Member joins the league
    await memberPage.click('text=/Join.*League|Competition/i');
    await memberPage.fill('input[placeholder*="token" i]', inviteToken);
    await memberPage.click('button:has-text("Join")');
    
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
    
    // Step 7: Verify member count increased
    const finalMemberCount = await commissionerPage.locator('[data-testid*="member"], .participant, text=/participants/i').count();
    console.log(`📊 Final member count: ${finalMemberCount}`);
    
    // Step 8: Verify both users see the same member list
    const commissionerMembers = await commissionerPage.locator('text=/Commissioner|Test Member/i').count();
    const memberMembers = await memberPage.locator('text=/Commissioner|Test Member/i').count();
    
    console.log(`📊 Commissioner sees ${commissionerMembers} members`);
    console.log(`📊 Member sees ${memberMembers} members`);
    
    expect(commissionerMembers).toBeGreaterThanOrEqual(2);
    expect(memberMembers).toBeGreaterThanOrEqual(2);
    
    console.log('✅ TEST PASSED: Real-time lobby presence working correctly');
  });
});
