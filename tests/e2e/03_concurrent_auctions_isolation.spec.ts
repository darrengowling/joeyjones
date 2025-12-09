/**
 * Prompt F - Test 3: Concurrent Auctions Isolation
 * Verifies Socket.IO events don't leak between separate auctions
 */

import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';
import { setUserSession } from './helpers/session';  // Prompt C

const BASE_URL = 'https://livebid-2.preview.emergentagent.com';

test.describe('03 - Concurrent Auctions Isolation', () => {
  let browserA1: Browser;
  let browserA2: Browser;
  let browserB1: Browser;
  let browserB2: Browser;
  
  let contextA1: BrowserContext;
  let contextA2: BrowserContext;
  let contextB1: BrowserContext;
  let contextB2: BrowserContext;
  
  let pageA1: Page; // Commissioner A, Auction 1
  let pageA2: Page; // Participant A, Auction 1
  let pageB1: Page; // Commissioner B, Auction 2
  let pageB2: Page; // Participant B, Auction 2
  
  let leagueIdA: string;
  let leagueIdB: string;
  let auctionIdA: string;
  let auctionIdB: string;
  
  let userA1: any, userA2: any, userB1: any, userB2: any;

  test.beforeAll(async () => {
    // Launch four separate browsers
    browserA1 = await chromium.launch({ headless: true });
    browserA2 = await chromium.launch({ headless: true });
    browserB1 = await chromium.launch({ headless: true });
    browserB2 = await chromium.launch({ headless: true });
    
    contextA1 = await browserA1.newContext();
    contextA2 = await browserA2.newContext();
    contextB1 = await browserB1.newContext();
    contextB2 = await browserB2.newContext();
    
    pageA1 = await contextA1.newPage();
    pageA2 = await contextA2.newPage();
    pageB1 = await contextB1.newPage();
    pageB2 = await contextB2.newPage();
  });

  test.afterAll(async () => {
    await pageA1.close();
    await pageA2.close();
    await pageB1.close();
    await pageB2.close();
    await contextA1.close();
    await contextA2.close();
    await contextB1.close();
    await contextB2.close();
    await browserA1.close();
    await browserA2.close();
    await browserB1.close();
    await browserB2.close();
  });

  test('Events in Auction A do not leak to Auction B', async () => {
    console.log('\n========================================');
    console.log('Test: Concurrent Auctions Isolation');
    console.log('========================================\n');

    const timestamp = Date.now();

    // Step 1: Create 4 users
    console.log('1️⃣ Creating 4 users...');
    
    const users = [
      { name: `IsolationE2E_CommA_${timestamp}`, email: `isolA1_${timestamp}@test.com` },
      { name: `IsolationE2E_ParticipantA_${timestamp}`, email: `isolA2_${timestamp}@test.com` },
      { name: `IsolationE2E_CommB_${timestamp}`, email: `isolB1_${timestamp}@test.com` },
      { name: `IsolationE2E_ParticipantB_${timestamp}`, email: `isolB2_${timestamp}@test.com` }
    ];
    
    const pages = [pageA1, pageA2, pageB1, pageB2];
    const userObjects = [];
    
    for (let i = 0; i < 4; i++) {
      const response = await pages[i].request.post(`${BASE_URL}/api/users`, {
        data: users[i]
      });
      const user = await response.json();
      userObjects.push(user);
      console.log(`   ✅ User ${i + 1}: ${user.name}`);
    }
    
    [userA1, userA2, userB1, userB2] = userObjects;

    // Step 2: Create League A
    console.log('\n2️⃣ Creating League A...');
    const leagueAResponse = await pageA1.request.post(`${BASE_URL}/api/leagues`, {
      data: {
        name: `E2E Isolation League A ${timestamp}`,
        sportKey: 'football',
        commissionerId: userA1.id,
        budget: 150000000,
        minManagers: 2,
        maxManagers: 2,
        clubSlots: 3,
        timerSeconds: 30,
        antiSnipeSeconds: 5
      }
    });
    const leagueA = await leagueAResponse.json();
    leagueIdA = leagueA.id;
    console.log(`   ✅ League A created: ${leagueA.name.substring(0, 20)}...`);

    // Step 3: Create League B
    console.log('\n3️⃣ Creating League B...');
    const leagueBResponse = await pageB1.request.post(`${BASE_URL}/api/leagues`, {
      data: {
        name: `E2E Isolation League B ${timestamp}`,
        sportKey: 'football',
        commissionerId: userB1.id,
        budget: 200000000,
        minManagers: 2,
        maxManagers: 2,
        clubSlots: 4,
        timerSeconds: 25,
        antiSnipeSeconds: 5
      }
    });
    const leagueB = await leagueBResponse.json();
    leagueIdB = leagueB.id;
    console.log(`   ✅ League B created: ${leagueB.name.substring(0, 20)}...`);

    // Step 4: Users join leagues
    console.log('\n4️⃣ Users joining leagues...');
    
    await pageA2.request.post(`${BASE_URL}/api/leagues/${leagueIdA}/join`, {
      data: {
        userId: userA2.id,
        displayName: userA2.name,
        inviteToken: leagueA.inviteToken
      }
    });
    console.log(`   ✅ User A2 joined League A`);

    await pageB2.request.post(`${BASE_URL}/api/leagues/${leagueIdB}/join`, {
      data: {
        userId: userB2.id,
        displayName: userB2.name,
        inviteToken: leagueB.inviteToken
      }
    });
    console.log(`   ✅ User B2 joined League B`);

    // Step 5: Start both auctions (waiting state)
    console.log('\n5️⃣ Starting both auctions...');
    
    const auctionAResponse = await pageA1.request.post(
      `${BASE_URL}/api/leagues/${leagueIdA}/auction/start`
    );
    const auctionAData = await auctionAResponse.json();
    auctionIdA = auctionAData.auctionId;
    console.log(`   ✅ Auction A: ${auctionIdA.substring(0, 8)}...`);

    const auctionBResponse = await pageB1.request.post(
      `${BASE_URL}/api/leagues/${leagueIdB}/auction/start`
    );
    const auctionBData = await auctionBResponse.json();
    auctionIdB = auctionBData.auctionId;
    console.log(`   ✅ Auction B: ${auctionIdB.substring(0, 8)}...`);

    // Step 6: All users enter their respective auction rooms
    console.log('\n6️⃣ Users entering auction rooms...');
    
    // Prompt C: Set user sessions before navigation
    await setUserSession(pageA1, userA1);
    await setUserSession(pageA2, userA2);
    await setUserSession(pageB1, userB1);
    await setUserSession(pageB2, userB2);
    
    await pageA1.goto(`${BASE_URL}/auction/${auctionIdA}`);
    await pageA1.waitForTimeout(1000);
    console.log(`   ✅ User A1 entered Auction A`);

    await pageA2.goto(`${BASE_URL}/auction/${auctionIdA}`);
    await pageA2.waitForTimeout(1000);
    console.log(`   ✅ User A2 entered Auction A`);

    await pageB1.goto(`${BASE_URL}/auction/${auctionIdB}`);
    await pageB1.waitForTimeout(1000);
    console.log(`   ✅ User B1 entered Auction B`);

    await pageB2.goto(`${BASE_URL}/auction/${auctionIdB}`);
    await pageB2.waitForTimeout(1000);
    console.log(`   ✅ User B2 entered Auction B`);

    // Step 7: Set up Socket.IO event listeners
    console.log('\n7️⃣ Setting up event listeners...');
    
    // Listen for lot_started events on all pages
    const eventPromises = {
      A1: pageA1.evaluate(() => {
        return new Promise((resolve) => {
          const timeout = setTimeout(() => resolve(null), 5000);
          if ((window as any).socket) {
            (window as any).socket.once('lot_started', (data: any) => {
              clearTimeout(timeout);
              resolve(data);
            });
          } else {
            clearTimeout(timeout);
            resolve(null);
          }
        });
      }),
      A2: pageA2.evaluate(() => {
        return new Promise((resolve) => {
          const timeout = setTimeout(() => resolve(null), 5000);
          if ((window as any).socket) {
            (window as any).socket.once('lot_started', (data: any) => {
              clearTimeout(timeout);
              resolve(data);
            });
          } else {
            clearTimeout(timeout);
            resolve(null);
          }
        });
      }),
      B1: pageB1.evaluate(() => {
        return new Promise((resolve) => {
          const timeout = setTimeout(() => resolve(null), 5000);
          if ((window as any).socket) {
            (window as any).socket.once('lot_started', (data: any) => {
              clearTimeout(timeout);
              resolve(data);
            });
          } else {
            clearTimeout(timeout);
            resolve(null);
          }
        });
      }),
      B2: pageB2.evaluate(() => {
        return new Promise((resolve) => {
          const timeout = setTimeout(() => resolve(null), 5000);
          if ((window as any).socket) {
            (window as any).socket.once('lot_started', (data: any) => {
              clearTimeout(timeout);
              resolve(data);
            });
          } else {
            clearTimeout(timeout);
            resolve(null);
          }
        });
      })
    };
    
    console.log(`   ✅ Event listeners set up`);

    // Step 8: Commissioner A begins Auction A
    console.log('\n8️⃣ Commissioner A beginning Auction A...');
    await pageA1.request.post(`${BASE_URL}/api/auction/${auctionIdA}/begin`);
    console.log(`   ✅ Auction A started`);

    // Step 9: Wait for events and check isolation
    console.log('\n9️⃣ Checking event isolation...');
    await pageA1.waitForTimeout(2000); // Give time for events to propagate
    
    const events = await Promise.all([
      eventPromises.A1,
      eventPromises.A2,
      eventPromises.B1,
      eventPromises.B2
    ]);
    
    const [eventA1, eventA2, eventB1, eventB2] = events;
    
    console.log(`   📊 User A1 received lot_started: ${eventA1 !== null}`);
    console.log(`   📊 User A2 received lot_started: ${eventA2 !== null}`);
    console.log(`   📊 User B1 received lot_started: ${eventB1 !== null}`);
    console.log(`   📊 User B2 received lot_started: ${eventB2 !== null}`);

    // Assertions: Users in Auction A should receive events, users in Auction B should NOT
    expect(eventA1).not.toBeNull();
    expect(eventA2).not.toBeNull();
    expect(eventB1).toBeNull();
    expect(eventB2).toBeNull();
    
    console.log(`   ✅ Auction A users received events`);
    console.log(`   ✅ Auction B users did NOT receive events`);

    // Step 10: Verify Auction B is still in waiting state
    console.log('\n🔟 Verifying Auction B state...');
    const auctionBState = await pageB1.request.get(`${BASE_URL}/api/auction/${auctionIdB}`);
    const auctionBData2 = await auctionBState.json();
    
    expect(auctionBData2.status).toBe('waiting');
    console.log(`   ✅ Auction B still in waiting state: ${auctionBData2.status}`);

    // Step 11: Verify UI state in both auctions
    console.log('\n1️⃣1️⃣ Verifying UI states...');
    
    // Auction A should show active auction
    const auctionAActive = await pageA1.locator('text=Current Bid').isVisible();
    expect(auctionAActive).toBe(true);
    console.log(`   ✅ Auction A shows active auction UI`);

    // Auction B should still show waiting room
    const auctionBWaiting = await pageB1.locator('text=Auction Waiting Room').isVisible();
    expect(auctionBWaiting).toBe(true);
    console.log(`   ✅ Auction B shows waiting room UI`);

    console.log('\n========================================');
    console.log('✅ ALL TESTS PASSED');
    console.log('========================================');
    console.log('\nTest Summary:');
    console.log('  - Two separate auctions created ✓');
    console.log('  - Only Auction A started ✓');
    console.log('  - Auction A users received lot_started ✓');
    console.log('  - Auction B users did NOT receive events ✓');
    console.log('  - Socket.IO room isolation working ✓');
  });
});
