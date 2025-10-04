import { test, expect } from '@playwright/test';

// Guard: Skip cricket tests if SPORTS_CRICKET_ENABLED is not 'true'
if (process.env.SPORTS_CRICKET_ENABLED !== 'true') {
  test.skip();
}

test.describe('Cricket Smoke Test', () => {
  test('Cricket API and Scoring Workflow', async ({ page, request }) => {
    console.log('🏏 Starting Cricket API smoke test...');
    
    // Step 1: Create user via API
    const userResponse = await request.post('/api/users', {
      data: {
        name: `Cricket Smoke Tester ${Date.now()}`,
        email: `cricket.smoke.${Date.now()}@test.com`
      }
    });
    expect(userResponse.ok()).toBeTruthy();
    const user = await userResponse.json();
    
    // Step 2: Create Cricket League via API
    const leagueResponse = await request.post('/api/leagues', {
      data: {
        name: `Cricket Smoke League ${Date.now()}`,
        commissionerId: user.id,
        budget: 100000000,
        minManagers: 2,
        maxManagers: 4,
        clubSlots: 5,
        sportKey: "cricket"
      }
    });
    expect(leagueResponse.ok()).toBeTruthy();
    const league = await leagueResponse.json();
    
    console.log(`✅ Cricket league created: ${league.id}`);
    
    // Step 3: Verify sports endpoint shows cricket (flag test)
    const sportsResponse = await request.get('/api/sports');
    expect(sportsResponse.ok()).toBeTruthy();
    const sports = await sportsResponse.json();
    
    const cricketSport = sports.find((s: any) => s.key === 'cricket');
    expect(cricketSport).toBeTruthy();
    expect(cricketSport.assetType).toBe('PLAYER');
    console.log('✅ Cricket sport available (flag enabled)');
    
    // Step 4: Verify cricket players are available
    const assetsResponse = await request.get(`/api/leagues/${league.id}/assets`);
    expect(assetsResponse.ok()).toBeTruthy();
    const assetsData = await assetsResponse.json();
    
    expect(assetsData.assets.length).toBeGreaterThan(0);
    console.log(`✅ ${assetsData.assets.length} cricket players available for auction`);
    
    // Step 5: Upload CSV Scoring Data
    const csvContent = `matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
M1,P001,54,0,1,0,0
M1,P002,12,3,0,0,1
M1,P003,101,0,0,0,0`;

    const scoringResponse = await request.post(`/api/scoring/${league.id}/ingest`, {
      multipart: {
        file: {
          name: 'test_scores.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(csvContent)
        }
      }
    });
    
    expect(scoringResponse.ok()).toBeTruthy();
    const scoringResult = await scoringResponse.json();
    
    // Step 6: Verify Leaderboard Calculations
    expect(scoringResult.leaderboard).toBeTruthy();
    expect(scoringResult.processedRows).toBe(3);
    
    const p001 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P001');
    const p002 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P002');
    const p003 = scoringResult.leaderboard.find((p: any) => p.playerExternalId === 'P003');
    
    // P001: 54 runs + 10(catch) + 10(half-century) = 74
    expect(p001?.totalPoints).toBe(74);
    console.log(`✅ P001 score verified: ${p001?.totalPoints} points`);
    
    // P002: 12 runs + 75(3 wickets * 25) + 10(runOut) = 97
    expect(p002?.totalPoints).toBe(97);
    console.log(`✅ P002 score verified: ${p002?.totalPoints} points`);
    
    // P003: 101 runs + 10(half-century) + 25(century) = 136
    expect(p003?.totalPoints).toBe(136);
    console.log(`✅ P003 score verified: ${p003?.totalPoints} points`);
    
    // Step 7: Verify leaderboard endpoint
    const leaderboardResponse = await request.get(`/api/scoring/${league.id}/leaderboard`);
    expect(leaderboardResponse.ok()).toBeTruthy();
    const leaderboardData = await leaderboardResponse.json();
    
    expect(leaderboardData.leaderboard.length).toBe(3);
    expect(leaderboardData.leaderboard[0].totalPoints).toBe(136); // P003 should be first
    
    console.log('🎉 Cricket smoke test passed!');
  });

  test('Cricket flag controls sport availability', async ({ request }) => {
    // Test that cricket is available when SPORTS_CRICKET_ENABLED=true
    const sportsResponse = await request.get('/api/sports');
    expect(sportsResponse.ok()).toBeTruthy();
    const sports = await sportsResponse.json();
    
    const cricketSport = sports.find((s: any) => s.key === 'cricket');
    
    if (process.env.SPORTS_CRICKET_ENABLED === 'true') {
      expect(cricketSport).toBeTruthy();
      console.log('✅ Cricket available when flag enabled');
    } else {
      expect(cricketSport).toBeFalsy();
      console.log('✅ Cricket hidden when flag disabled');
    }
  });
});

// Test to verify football E2E is unaffected
test.describe('Football E2E Unaffected', () => {
  test('Football functionality still works with cricket enabled', async ({ request }) => {
    // Create football user and league
    const userResponse = await request.post('/api/users', {
      data: {
        name: `Football Tester ${Date.now()}`,
        email: `football.test.${Date.now()}@test.com`
      }
    });
    const user = await userResponse.json();
    
    const leagueResponse = await request.post('/api/leagues', {
      data: {
        name: `Football League ${Date.now()}`,
        commissionerId: user.id,
        budget: 500000000,
        minManagers: 2,
        maxManagers: 8,
        clubSlots: 3,
        sportKey: "football"
      }
    });
    expect(leagueResponse.ok()).toBeTruthy();
    const league = await leagueResponse.json();
    
    // Verify football assets work
    const assetsResponse = await request.get(`/api/leagues/${league.id}/assets`);
    expect(assetsResponse.ok()).toBeTruthy();
    const assetsData = await assetsResponse.json();
    
    expect(assetsData.assets.length).toBeGreaterThan(0);
    // Football assets should have 'country' field (clubs), not 'meta' field (players)
    expect(assetsData.assets[0].country).toBeTruthy();
    
    console.log('✅ Football functionality unaffected by cricket implementation');
  });
});