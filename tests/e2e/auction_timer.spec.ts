import { test, expect, Page } from '@playwright/test';

test.describe('Auction Timer Synchronization', () => {
  let page: Page;
  let auctionId: string;
  let lotId: string;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // Setup auction environment
    await setupAuctionEnvironment();
  });

  test.afterEach(async () => {
    await page.close();
  });

  async function setupAuctionEnvironment() {
    const baseUrl = 'https://ucl-bidding.preview.emergentagent.com';
    
    // Clean database and seed clubs
    await fetch(`${baseUrl}/api/clubs/seed`, { method: 'POST' });
    
    // Create user
    const userResponse = await fetch(`${baseUrl}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Timer Test User', email: 'timertest@playwright.com' })
    });
    const user = await userResponse.json();

    // Create league with short timer for testing
    const leagueResponse = await fetch(`${baseUrl}/api/leagues`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Timer Test League',
        commissionerId: user.id,
        budget: 1000.0,
        minManagers: 1,
        maxManagers: 2,
        clubSlots: 3
      })
    });
    const league = await leagueResponse.json();

    // Join league
    await fetch(`${baseUrl}/api/leagues/${league.id}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId: user.id, inviteToken: league.inviteToken })
    });

    // Start auction
    const auctionResponse = await fetch(`${baseUrl}/api/leagues/${league.id}/auction/start`, {
      method: 'POST'
    });
    const auctionData = await auctionResponse.json();
    auctionId = auctionData.auctionId;

    // Navigate to auction room
    await page.goto(`${baseUrl}/auction/${auctionId}`);
    
    // Wait for page to load and join auction
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-testid="auction-timer"]', { timeout: 10000 });
  }

  async function getCurrentTimerText(): Promise<string> {
    return await page.locator('[data-testid="auction-timer"]').innerText();
  }

  async function parseTimerSeconds(timerText: string): Promise<number> {
    const [mm, ss] = timerText.split(':').map(s => parseInt(s, 10));
    return mm * 60 + ss;
  }

  async function injectFakeSyncState(fakeSeq: number, fakeRemainingSeconds: number) {
    // Inject fake sync_state event with older sequence number
    await page.evaluate(({ seq, remainingSeconds }) => {
      const fakeEndTime = Date.now() + (remainingSeconds * 1000);
      const fakeTimer = {
        lotId: 'fake-lot-id',
        seq: seq,
        endsAt: fakeEndTime,
        serverNow: Date.now()
      };
      
      // Get the socket from window (if available) or trigger event manually
      if (window.socket && window.socket.emit) {
        // Simulate receiving a sync_state event
        window.socket.emit('sync_state', { timer: fakeTimer });
      } else {
        // Fallback: trigger custom event that the hook might listen to
        window.dispatchEvent(new CustomEvent('fake_sync_state', { 
          detail: { timer: fakeTimer }
        }));
      }
    }, { seq: fakeSeq, remainingSeconds: fakeRemainingSeconds });
  }

  test('sync_state cannot overwrite newer tick events', async () => {
    // Wait for auction to start and timer to show initial value
    await page.waitForSelector('[data-testid="auction-timer"]');
    
    // Wait until timer shows 00:08 or less
    await page.waitForFunction(() => {
      const timer = document.querySelector('[data-testid="auction-timer"]');
      if (!timer) return false;
      const [mm, ss] = timer.textContent.split(':').map(s => parseInt(s, 10));
      const totalSeconds = mm * 60 + ss;
      return totalSeconds <= 8;
    }, { timeout: 60000 });

    // Get current timer value
    const currentTimerText = await getCurrentTimerText();
    const currentSeconds = await parseTimerSeconds(currentTimerText);
    
    console.log(`Timer currently at: ${currentTimerText} (${currentSeconds}s)`);
    
    // Inject fake sync_state with older sequence number that would set timer to 00:10
    await injectFakeSyncState(1, 10); // Very low seq number, 10 seconds remaining
    
    // Wait a moment for any potential processing
    await page.waitForTimeout(500);
    
    // Verify timer hasn't jumped back to 00:10
    const afterSyncTimerText = await getCurrentTimerText();
    const afterSyncSeconds = await parseTimerSeconds(afterSyncTimerText);
    
    console.log(`Timer after fake sync: ${afterSyncTimerText} (${afterSyncSeconds}s)`);
    
    // Assert timer is still <= 8 seconds (hasn't jumped back)
    expect(afterSyncSeconds).toBeLessThanOrEqual(8);
    expect(afterSyncSeconds).toBeLessThanOrEqual(currentSeconds);
    
    console.log('✅ Stale sync_state correctly ignored');
  });

  test('anti-snipe extends timer and increases sequence', async () => {
    // Wait for auction to start
    await page.waitForSelector('[data-testid="auction-timer"]');
    
    // Wait until timer is in anti-snipe window (≤ 30 seconds, but > 5 seconds for reliability)
    await page.waitForFunction(() => {
      const timer = document.querySelector('[data-testid="auction-timer"]');
      if (!timer) return false;
      const [mm, ss] = timer.textContent.split(':').map(s => parseInt(s, 10));
      const totalSeconds = mm * 60 + ss;
      return totalSeconds <= 30 && totalSeconds > 5;
    }, { timeout: 60000 });

    const beforeBidTimerText = await getCurrentTimerText();
    const beforeBidSeconds = await parseTimerSeconds(beforeBidTimerText);
    
    console.log(`Timer before bid: ${beforeBidTimerText} (${beforeBidSeconds}s)`);
    
    // Place a bid to trigger anti-snipe
    await page.fill('[data-testid="bid-amount-input"]', '100');
    await page.click('button:has-text("Place Bid")');
    
    // Wait for anti-snipe alert
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Anti-snipe');
      await dialog.accept();
    });
    
    // Wait for timer to update (anti-snipe should extend it)
    await page.waitForTimeout(1000);
    
    const afterBidTimerText = await getCurrentTimerText();
    const afterBidSeconds = await parseTimerSeconds(afterBidTimerText);
    
    console.log(`Timer after anti-snipe bid: ${afterBidTimerText} (${afterBidSeconds}s)`);
    
    // Assert timer was extended (should be close to anti-snipe seconds, typically 30s)
    expect(afterBidSeconds).toBeGreaterThan(beforeBidSeconds);
    expect(afterBidSeconds).toBeGreaterThanOrEqual(25); // Should be around 30s, allow some tolerance
    
    console.log('✅ Anti-snipe correctly extended timer');
  });

  test('timer countdown is smooth and consistent', async () => {
    // Wait for auction to start
    await page.waitForSelector('[data-testid="auction-timer"]');
    
    // Record timer values over 3 seconds
    const timerReadings: number[] = [];
    const startTime = Date.now();
    
    while (Date.now() - startTime < 3000) {
      const timerText = await getCurrentTimerText();
      const seconds = await parseTimerSeconds(timerText);
      timerReadings.push(seconds);
      await page.waitForTimeout(100); // Check every 100ms
    }
    
    // Remove duplicates and sort
    const uniqueReadings = [...new Set(timerReadings)].sort((a, b) => b - a);
    
    console.log('Timer readings:', uniqueReadings);
    
    // Assert timer is counting down (values should be decreasing)
    expect(uniqueReadings.length).toBeGreaterThan(1);
    expect(uniqueReadings[0]).toBeGreaterThan(uniqueReadings[uniqueReadings.length - 1]);
    
    // Assert no large jumps (should decrease smoothly)
    for (let i = 1; i < uniqueReadings.length; i++) {
      const diff = uniqueReadings[i - 1] - uniqueReadings[i];
      expect(diff).toBeLessThanOrEqual(3); // Allow up to 3 second gaps
    }
    
    console.log('✅ Timer countdown is smooth and consistent');
  });

  test('lot progression works correctly', async () => {
    // Wait for first lot to start
    await page.waitForSelector('[data-testid="auction-timer"]');
    
    // Get current club name
    const firstClubName = await page.locator('h2').first().innerText();
    console.log(`First club: ${firstClubName}`);
    
    // Wait for lot to complete (timer reaches 00:00)
    await page.waitForFunction(() => {
      const timer = document.querySelector('[data-testid="auction-timer"]');
      if (!timer) return false;
      const [mm, ss] = timer.textContent.split(':').map(s => parseInt(s, 10));
      return mm === 0 && ss === 0;
    }, { timeout: 120000 });
    
    console.log('First lot completed');
    
    // Wait for next lot to start (new club should appear)
    await page.waitForFunction((previousClub) => {
      const currentClub = document.querySelector('h2');
      return currentClub && currentClub.textContent !== previousClub;
    }, firstClubName, { timeout: 10000 });
    
    const secondClubName = await page.locator('h2').first().innerText();
    console.log(`Second club: ${secondClubName}`);
    
    // Verify it's a different club
    expect(secondClubName).not.toBe(firstClubName);
    
    // Verify timer reset for new lot
    const newTimerText = await getCurrentTimerText();
    const newTimerSeconds = await parseTimerSeconds(newTimerText);
    expect(newTimerSeconds).toBeGreaterThan(50); // Should be close to 60 seconds
    
    console.log('✅ Lot progression working correctly');
  });
});