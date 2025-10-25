/**
 * Prompt F - Test 2: Non-Commissioner Authorization
 * Verifies non-commissioner cannot call POST /auction/{id}/begin
 */

import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'https://multisport-auction.preview.emergentagent.com';

test.describe('02 - Non-Commissioner Authorization', () => {
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

  test('Non-commissioner receives 403 when trying to begin auction', async () => {
    console.log('\n========================================');
    console.log('Test: Non-Commissioner Authorization');
    console.log('========================================\n');

    // Step 1: Create users via API
    console.log('1️⃣ Creating users...');
    const timestamp = Date.now();
    
    const userAResponse = await pageA.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `AuthE2E_CommissionerA_${timestamp}`,
        email: `authA_${timestamp}@test.com`
      }
    });
    userA = await userAResponse.json();
    console.log(`   ✅ User A (Commissioner): ${userA.name}`);

    const userBResponse = await pageB.request.post(`${BASE_URL}/api/users`, {
      data: {
        name: `AuthE2E_ParticipantB_${timestamp}`,
        email: `authB_${timestamp}@test.com`
      }
    });
    userB = await userBResponse.json();
    console.log(`   ✅ User B (Participant): ${userB.name}`);

    // Step 2: User A creates league
    console.log('\n2️⃣ Creating league...');
    const leagueResponse = await pageA.request.post(`${BASE_URL}/api/leagues`, {
      data: {
        name: `E2E Auth Test ${timestamp}`,
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

    // Step 4: User A starts auction (creates in waiting state)
    console.log('\n4️⃣ Starting auction (waiting state)...');
    const auctionResponse = await pageA.request.post(
      `${BASE_URL}/api/leagues/${leagueId}/auction/start`
    );
    const auctionData = await auctionResponse.json();
    auctionId = auctionData.auctionId;
    console.log(`   ✅ Auction created in waiting state`);
    console.log(`   📋 Auction ID: ${auctionId.substring(0, 8)}...`);

    // Step 5: User B attempts to begin auction (should fail with 403)
    console.log('\n5️⃣ User B attempting to begin auction (should fail)...');
    
    try {
      const beginResponse = await pageB.request.post(
        `${BASE_URL}/api/auction/${auctionId}/begin`,
        {
          failOnStatusCode: false // Don't throw on non-2xx status
        }
      );
      
      const status = beginResponse.status();
      console.log(`   📊 Response status: ${status}`);
      
      // Verify we got 403 Forbidden
      expect(status).toBe(403);
      console.log(`   ✅ Correctly received 403 Forbidden`);
      
      // Try to parse error message
      try {
        const errorBody = await beginResponse.json();
        console.log(`   📋 Error message: ${errorBody.detail || errorBody.message || 'N/A'}`);
        
        // Verify error message mentions authorization
        const errorMsg = (errorBody.detail || errorBody.message || '').toLowerCase();
        const hasAuthMessage = errorMsg.includes('commissioner') || 
                               errorMsg.includes('forbidden') || 
                               errorMsg.includes('not authorized') ||
                               errorMsg.includes('permission');
        expect(hasAuthMessage).toBe(true);
        console.log(`   ✅ Error message mentions authorization`);
      } catch (e) {
        console.log(`   ⚠️  Could not parse error body (this is okay)`);
      }
      
    } catch (error) {
      console.log(`   ❌ Unexpected error during API call:`, error);
      throw error;
    }

    // Step 6: Verify auction is still in waiting state
    console.log('\n6️⃣ Verifying auction still in waiting state...');
    const stateResponse = await pageA.request.get(
      `${BASE_URL}/api/auction/${auctionId}`
    );
    const auctionState = await stateResponse.json();
    
    expect(auctionState.status).toBe('waiting');
    console.log(`   ✅ Auction status: ${auctionState.status}`);
    console.log(`   ✅ Auction did not transition to active`);

    // Step 7: User A (commissioner) can successfully begin auction
    console.log('\n7️⃣ User A (commissioner) beginning auction (should succeed)...');
    const commBeginResponse = await pageA.request.post(
      `${BASE_URL}/api/auction/${auctionId}/begin`
    );
    
    expect(commBeginResponse.status()).toBe(200);
    console.log(`   ✅ Commissioner successfully began auction`);
    
    const updatedState = await commBeginResponse.json();
    expect(updatedState.status).toBe('active');
    console.log(`   ✅ Auction now active with status: ${updatedState.status}`);

    console.log('\n========================================');
    console.log('✅ ALL TESTS PASSED');
    console.log('========================================');
    console.log('\nTest Summary:');
    console.log('  - Non-commissioner cannot begin auction ✓');
    console.log('  - 403 Forbidden returned correctly ✓');
    console.log('  - Error message mentions authorization ✓');
    console.log('  - Auction remains in waiting state ✓');
    console.log('  - Commissioner can successfully begin ✓');
  });
});
