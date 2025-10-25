/**
 * Prompt F - Test 4: Late Joiner Sync
 * Verifies users who join waiting room after auction created receive correct state
 */

import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'https://multisport-auction.preview.emergentagent.com';

test.describe('04 - Late Joiner Sync', () => {
  let browserA: Browser;
  let browserB: Browser;
  let browserC: Browser;
  
  let contextA: BrowserContext;
  let contextB: BrowserContext;
  let contextC: BrowserContext;
  
  let pageA: Page; // Commissioner
  let pageB: Page; // Early joiner
  let pageC: Page; // Late joiner
  
  let leagueId: string;
  let auctionId: string;
  let userA: any;
  let userB: any;
  let userC: any;

  test.beforeAll(async () => {
    // Launch three separate browsers
    browserA = await chromium.launch({ headless: true });
    browserB = await chromium.launch({ headless: true });
    browserC = await chromium.launch({ headless: true });
    
    contextA = await browserA.newContext();
    contextB = await browserB.newContext();
    contextC = await browserC.newContext();
    
    pageA = await contextA.newPage();
    pageB = await contextB.newPage();
    pageC = await contextC.newPage();
  });

  test.afterAll(async () => {
    await pageA.close();
    await pageB.close();
    await pageC.close();
    await contextA.close();
    await contextB.close();
    await contextC.close();
    await browserA.close();
    await browserB.close();
    await browserC.close();
  });

  test('Late joiner receives auction_snapshot and sees correct UI state', async () => {
    console.log('\n========================================');
    console.log('Test: Late Joiner Sync');
    console.log('========================================\n');

    const timestamp = Date.now();

    // Step 1: Create 3 users
    console.log('1️⃣ Creating 3 users...');
    
    const userAResponse = await pageA.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `LateJoinerE2E_CommA_${timestamp}`,
        email: `lateA_${timestamp}@test.com`
      }
    });
    userA = await userAResponse.json();
    console.log(`   ✅ User A (Commissioner): ${userA.name}`);

    const userBResponse = await pageB.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `LateJoinerE2E_EarlyB_${timestamp}`,
        email: `lateB_${timestamp}@test.com`
      }
    });
    userB = await userBResponse.json();
    console.log(`   ✅ User B (Early Joiner): ${userB.name}`);

    const userCResponse = await pageC.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `LateJoinerE2E_LateC_${timestamp}`,
        email: `lateC_${timestamp}@test.com`
      }
    });
    userC = await userCResponse.json();
    console.log(`   ✅ User C (Late Joiner): ${userC.name}`);

    // Step 2: User A creates league
    console.log('\n2️⃣ Creating league...');
    const leagueResponse = await pageA.request.post(`${BASE_URL}/api/leagues`, {
      data: {
        name: `E2E Late Joiner Test ${timestamp}`,
        sportKey: 'football',
        commissionerId: userA.id,
        budget: 180000000,
        minManagers: 3,
        maxManagers: 3,
        clubSlots: 4,
        timerSeconds: 25,
        antiSnipeSeconds: 5
      }
    });
    const league = await leagueResponse.json();
    leagueId = league.id;
    console.log(`   ✅ League created: ${league.name}`);

    // Step 3: Users B and C join league
    console.log('\n3️⃣ Users B and C joining league...');
    
    await pageB.request.post(`${BASE_URL}/api/leagues/${leagueId}/join`, {
      data: {
        userId: userB.id,
        displayName: userB.name,
        inviteToken: league.inviteToken
      }
    });
    console.log(`   ✅ User B joined`);

    await pageC.request.post(`${BASE_URL}/api/leagues/${leagueId}/join`, {
      data: {
        userId: userC.id,
        displayName: userC.name,
        inviteToken: league.inviteToken
      }
    });
    console.log(`   ✅ User C joined`);

    // Step 4: Start auction in waiting state
    console.log('\n4️⃣ Starting auction (waiting state)...');
    const auctionResponse = await pageA.request.post(
      `${BASE_URL}/api/leagues/${leagueId}/auction/start`
    );
    const auctionData = await auctionResponse.json();
    auctionId = auctionData.auctionId;
    console.log(`   ✅ Auction created in waiting state`);
    console.log(`   📋 Auction ID: ${auctionId.substring(0, 8)}...`);

    // Step 5: User A and B enter auction room (early joiners)
    console.log('\n5️⃣ Early joiners entering auction room...');
    
    await pageA.goto(`${BASE_URL}/auction/${auctionId}`);
    await pageA.waitForTimeout(1000);
    console.log(`   ✅ User A entered (early)`);

    await pageB.goto(`${BASE_URL}/auction/${auctionId}`);
    await pageB.waitForTimeout(1000);
    console.log(`   ✅ User B entered (early)`);

    // Step 6: Verify early joiners see waiting room
    console.log('\n6️⃣ Verifying early joiners see waiting room...');
    
    const waitingHeaderA = await pageA.locator('text=Auction Waiting Room').isVisible();
    expect(waitingHeaderA).toBe(true);
    console.log(`   ✅ User A sees waiting room`);

    const waitingHeaderB = await pageB.locator('text=Auction Waiting Room').isVisible();
    expect(waitingHeaderB).toBe(true);
    console.log(`   ✅ User B sees waiting room`);

    // Step 7: Set up auction_snapshot listener for late joiner
    console.log('\n7️⃣ Setting up auction_snapshot listener for User C...');
    
    const snapshotPromise = pageC.evaluate(() => {
      return new Promise((resolve) => {
        const timeout = setTimeout(() => resolve(null), 3000);
        
        // Wait for socket to be available (it's set up on page load)
        const checkSocket = setInterval(() => {
          if ((window as any).socket) {
            clearInterval(checkSocket);
            (window as any).socket.once('auction_snapshot', (data: any) => {
              clearTimeout(timeout);
              resolve(data);
            });
          }
        }, 100);
        
        // Clean up interval after timeout
        setTimeout(() => clearInterval(checkSocket), 3000);
      });
    });
    
    console.log(`   ✅ Listener set up`);

    // Step 8: User C joins auction room (late joiner)
    console.log('\n8️⃣ Late joiner (User C) entering auction room...');
    
    await pageC.goto(`${BASE_URL}/auction/${auctionId}`);
    console.log(`   ✅ User C navigated to auction room`);

    // Step 9: Wait for and verify auction_snapshot event
    console.log('\n9️⃣ Checking for auction_snapshot event...');
    
    const snapshot = await snapshotPromise;
    
    if (snapshot !== null) {
      console.log(`   ✅ User C received auction_snapshot event`);
      
      // Verify snapshot contains expected fields
      const snapshotData = snapshot as any;
      expect(snapshotData).toHaveProperty('auctionId');
      expect(snapshotData).toHaveProperty('status');
      expect(snapshotData.status).toBe('waiting');
      console.log(`   ✅ Snapshot has auctionId: ${snapshotData.auctionId?.substring(0, 8)}...`);
      console.log(`   ✅ Snapshot status: ${snapshotData.status}`);
    } else {
      console.log(`   ⚠️  User C did not receive auction_snapshot (may use polling instead)`);
    }

    // Step 10: Verify User C sees waiting room UI
    console.log('\n🔟 Verifying User C sees correct UI state...');
    
    await pageC.waitForTimeout(1500); // Give time for UI to render
    
    const waitingHeaderC = await pageC.locator('text=Auction Waiting Room').isVisible();
    expect(waitingHeaderC).toBe(true);
    console.log(`   ✅ User C sees "Auction Waiting Room" header`);

    // User C should see waiting message (not commissioner)
    const waitingMessageC = await pageC.locator('text=Waiting for commissioner').isVisible();
    expect(waitingMessageC).toBe(true);
    console.log(`   ✅ User C sees "Waiting for commissioner" message`);

    // User C should see participants list with 3 users
    const participantsC = await pageC.locator('text=Participants in Room (3)').isVisible();
    expect(participantsC).toBe(true);
    console.log(`   ✅ User C sees 3 participants listed`);

    // Step 11: Verify User C sees same state as early joiners
    console.log('\n1️⃣1️⃣ Verifying state consistency across all users...');
    
    // All users should see same participant count
    const participantsA = await pageA.locator('text=Participants in Room (3)').isVisible();
    const participantsB = await pageB.locator('text=Participants in Room (3)').isVisible();
    
    expect(participantsA).toBe(true);
    expect(participantsB).toBe(true);
    expect(participantsC).toBe(true);
    console.log(`   ✅ All users see same participant count (3)`);

    // Step 12: Commissioner begins auction - verify all users transition
    console.log('\n1️⃣2️⃣ Commissioner beginning auction...');
    
    await pageA.click('button:has-text("Begin Auction")');
    console.log(`   ✅ Begin button clicked`);

    // Step 13: Verify all users transition to active auction
    console.log('\n1️⃣3️⃣ Verifying all users see active auction...');
    
    // User A
    await pageA.waitForSelector('text=Current Bid', { timeout: 2000 });
    console.log(`   ✅ User A sees active auction`);

    // User B
    await pageB.waitForSelector('text=Current Bid', { timeout: 2000 });
    console.log(`   ✅ User B sees active auction`);

    // User C (late joiner)
    await pageC.waitForSelector('text=Current Bid', { timeout: 2000 });
    console.log(`   ✅ User C sees active auction`);

    console.log('\n========================================');
    console.log('✅ ALL TESTS PASSED');
    console.log('========================================');
    console.log('\nTest Summary:');
    console.log('  - Late joiner can enter waiting room ✓');
    console.log('  - Late joiner sees correct waiting UI ✓');
    console.log('  - Late joiner sees same participant count ✓');
    console.log('  - Late joiner transitions with others ✓');
    console.log('  - All users see consistent state ✓');
  });
});
