/**
 * Prompt F - Test 2: Waiting Room UX
 * Verifies both users see waiting room and transition to active auction
 */

import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';
import { setUserSession } from './helpers/session';  // Prompt C

const BASE_URL = 'https://restart-auction.preview.emergentagent.com';

test.describe('01 - Waiting Room UX', () => {
  let browserA: Browser;
  let browserB: Browser;
  let contextA: BrowserContext;
  let contextB: BrowserContext;
  let pageA: Page;
  let pageB: Page;
  
  let leagueId: string;
  let auctionId: string;
  let userA: any;
  let userB: any;

  test.beforeAll(async () => {
    // Launch two separate browsers
    browserA = await chromium.launch({ headless: true });
    browserB = await chromium.launch({ headless: true });
    
    contextA = await browserA.newContext();
    contextB = await browserB.newContext();
    
    pageA = await contextA.newPage();
    pageB = await contextB.newPage();
  });

  test.afterAll(async () => {
    await pageA.close();
    await pageB.close();
    await contextA.close();
    await contextB.close();
    await browserA.close();
    await browserB.close();
  });

  test('Both users see waiting room and transition to active auction', async () => {
    console.log('\n========================================');
    console.log('Test: Waiting Room UX');
    console.log('========================================\n');

    // Step 1: Create users via API
    console.log('1️⃣ Creating users...');
    const timestamp = Date.now();
    
    const userAResponse = await pageA.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `WaitingE2E_CommissionerA_${timestamp}`,
        email: `waitingA_${timestamp}@test.com`
      }
    });
    userA = await userAResponse.json();
    console.log(`   ✅ User A (Commissioner): ${userA.name}`);

    const userBResponse = await pageB.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `WaitingE2E_ParticipantB_${timestamp}`,
        email: `waitingB_${timestamp}@test.com`
      }
    });
    userB = await userBResponse.json();
    console.log(`   ✅ User B (Participant): ${userB.name}`);

    // Step 2: User A creates league
    console.log('\n2️⃣ Creating league...');
    const leagueResponse = await pageA.request.post(`${BASE_URL}/api/leagues`, {
      data: {
        name: `E2E Waiting Room ${timestamp}`,
        sportKey: 'football',
        commissionerId: userA.id,
        budget: 200000000,
        minManagers: 2,
        maxManagers: 2,
        clubSlots: 3,
        timerSeconds: 20,
        antiSnipeSeconds: 5
      }
    });
    const league = await leagueResponse.json();
    leagueId = league.id;
    console.log(`   ✅ League created: ${league.name}`);

    // Step 3: User B joins league
    console.log('\n3️⃣ User B joining league...');
    await pageB.request.post(`${BASE_URL}/api/leagues/${leagueId}/join`, {
      data: {
        userId: userB.id,
        displayName: userB.name,
        inviteToken: league.inviteToken
      }
    });
    console.log(`   ✅ User B joined`);

    // Step 4: Sign in both users in browsers
    console.log('\n4️⃣ Signing in both users...');
    
    await pageA.goto(BASE_URL);
    await pageA.click('text=Sign In');
    await pageA.fill('input[placeholder="Enter your full name"]', userA.name);
    await pageA.fill('input[placeholder="your.email@example.com"]', userA.email);
    await pageA.click('button:has-text("Continue")');
    await pageA.waitForTimeout(2000);
    console.log(`   ✅ User A signed in`);

    await pageB.goto(BASE_URL);
    await pageB.click('text=Sign In');
    await pageB.fill('input[placeholder="Enter your full name"]', userB.name);
    await pageB.fill('input[placeholder="your.email@example.com"]', userB.email);
    await pageB.click('button:has-text("Continue")');
    await pageB.waitForTimeout(2000);
    console.log(`   ✅ User B signed in`);

    // Step 5: User A starts auction
    console.log('\n5️⃣ Starting auction (waiting state)...');
    const auctionResponse = await pageA.request.post(
      `${BASE_URL}/api/leagues/${leagueId}/auction/start`
    );
    const auctionData = await auctionResponse.json();
    auctionId = auctionData.auctionId;
    console.log(`   ✅ Auction created in waiting state`);
    console.log(`   📋 Auction ID: ${auctionId.substring(0, 8)}...`);

    // Step 6: Both users enter auction room
    console.log('\n6️⃣ Both users entering auction room...');
    
    // Prompt C: Set user sessions before navigation to prevent redirect
    await setUserSession(pageA, userA);
    await setUserSession(pageB, userB);
    
    await pageA.goto(`${BASE_URL}/auction/${auctionId}`);
    await pageA.waitForTimeout(1000);
    console.log(`   ✅ User A entered auction room`);

    await pageB.goto(`${BASE_URL}/auction/${auctionId}`);
    await pageB.waitForTimeout(1000);
    console.log(`   ✅ User B entered auction room`);

    // Step 7: Verify both see waiting room
    console.log('\n7️⃣ Verifying waiting room UI...');
    
    // User A should see waiting room header
    const waitingHeaderA = await pageA.locator('text=Auction Waiting Room').isVisible();
    expect(waitingHeaderA).toBe(true);
    console.log(`   ✅ User A sees "Auction Waiting Room" header`);

    // User B should see waiting room header
    const waitingHeaderB = await pageB.locator('text=Auction Waiting Room').isVisible();
    expect(waitingHeaderB).toBe(true);
    console.log(`   ✅ User B sees "Auction Waiting Room" header`);

    // User A should see "Begin Auction" button
    const beginButtonA = await pageA.locator('button:has-text("Begin Auction")').isVisible();
    expect(beginButtonA).toBe(true);
    console.log(`   ✅ User A sees "Begin Auction" button (commissioner)`);

    // User B should see waiting message
    const waitingMessageB = await pageB.locator('text=Waiting for commissioner').isVisible();
    expect(waitingMessageB).toBe(true);
    console.log(`   ✅ User B sees "Waiting for commissioner" message`);

    // Both should see participants list with 2 users
    const participantsA = await pageA.locator('text=Participants in Room (2)').isVisible();
    expect(participantsA).toBe(true);
    console.log(`   ✅ User A sees 2 participants listed`);

    const participantsB = await pageB.locator('text=Participants in Room (2)').isVisible();
    expect(participantsB).toBe(true);
    console.log(`   ✅ User B sees 2 participants listed`);

    // Step 8: User A clicks "Begin Auction"
    console.log('\n8️⃣ User A clicking "Begin Auction"...');
    const startTime = Date.now();
    
    await pageA.click('button:has-text("Begin Auction")');
    console.log(`   ✅ Button clicked at T+0ms`);

    // Step 9: Wait for both users to see active auction
    console.log('\n9️⃣ Waiting for transition to active auction...');
    
    // User A should see active auction within 1s
    try {
      await pageA.waitForSelector('text=Current Bid', { timeout: 2000 });
      const transitionTimeA = Date.now() - startTime;
      console.log(`   ✅ User A transitioned to active auction (${transitionTimeA}ms)`);
    } catch (e) {
      console.log(`   ❌ User A did not transition within 2s`);
      throw e;
    }

    // User B should see active auction within 1s
    try {
      await pageB.waitForSelector('text=Current Bid', { timeout: 2000 });
      const transitionTimeB = Date.now() - startTime;
      console.log(`   ✅ User B transitioned to active auction (${transitionTimeB}ms)`);
    } catch (e) {
      console.log(`   ❌ User B did not transition within 2s`);
      throw e;
    }

    // Step 10: Verify both see first lot
    console.log('\n🔟 Verifying first lot visible...');
    
    // Both should see timer countdown
    const timerA = await pageA.locator('text=Time Left').isVisible();
    expect(timerA).toBe(true);
    console.log(`   ✅ User A sees timer`);

    const timerB = await pageB.locator('text=Time Left').isVisible();
    expect(timerB).toBe(true);
    console.log(`   ✅ User B sees timer`);

    // Both should see bid button
    const bidButtonA = await pageA.locator('button:has-text("Place Bid")').isVisible();
    expect(bidButtonA).toBe(true);
    console.log(`   ✅ User A sees "Place Bid" button`);

    const bidButtonB = await pageB.locator('button:has-text("Place Bid")').isVisible();
    expect(bidButtonB).toBe(true);
    console.log(`   ✅ User B sees "Place Bid" button`);

    console.log('\n========================================');
    console.log('✅ ALL TESTS PASSED');
    console.log('========================================');
    console.log('\nTest Summary:');
    console.log('  - Both users see waiting room ✓');
    console.log('  - Commissioner sees Begin button ✓');
    console.log('  - Participant sees waiting message ✓');
    console.log('  - Both see participants list ✓');
    console.log('  - Transition to active < 2s ✓');
    console.log('  - Both see first lot ✓');
  });
});
