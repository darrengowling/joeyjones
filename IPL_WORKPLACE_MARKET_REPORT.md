# IPL Workplace Market Report

**Created:** December 28, 2025  
**Target Market:** India - Corporate/Workplace Competitions  
**Target Launch:** IPL 2026 (March 26 - May 31, 2026)  
**Time to Launch:** ~3 months

---

## Executive Summary

The IPL Workplace product leverages existing cricket functionality to create a B2B offering for Indian corporations, enabling colleagues to compete against each other during the IPL season. The core auction and scoring mechanics are already built - primary work involves data seeding, API verification, and market-specific customizations.

### Opportunity Assessment

| Factor | Assessment |
|--------|------------|
| **Market Size** | India has 500M+ cricket fans, 50M+ office workers |
| **Timing** | IPL 2026: March 26 - May 31, 2026 (10 teams, 84 matches) |
| **Competition** | Dream11 dominates fantasy sports, but auction-based format is differentiated |
| **Technical Readiness** | 80% complete - cricket scoring exists |
| **Go-to-Market** | B2B through HR/engagement platforms, corporate partnerships |

---

## IPL 2026 Details

| Item | Details |
|------|---------|
| **Dates** | March 26 - May 31, 2026 |
| **Teams** | 10 franchises |
| **Matches** | 84 (expanded format) |
| **Format** | T20 |
| **Venues** | Multiple across India |

### IPL 2026 Teams

| Team | Short Name | City |
|------|------------|------|
| Chennai Super Kings | CSK | Chennai |
| Mumbai Indians | MI | Mumbai |
| Royal Challengers Bangalore | RCB | Bangalore |
| Kolkata Knight Riders | KKR | Kolkata |
| Delhi Capitals | DC | Delhi |
| Punjab Kings | PBKS | Mohali |
| Rajasthan Royals | RR | Jaipur |
| Sunrisers Hyderabad | SRH | Hyderabad |
| Gujarat Titans | GT | Ahmedabad |
| Lucknow Super Giants | LSG | Lucknow |

---

## Current Technical Readiness

### What Already Exists ✅

| Component | Status | Notes |
|-----------|--------|-------|
| Cricket sport configuration | ✅ Complete | Scoring schema defined |
| Player-based asset type | ✅ Complete | Unlike football (clubs) |
| Per-player match scoring | ✅ Complete | Runs, wickets, catches, etc. |
| Cricbuzz API integration | ✅ Complete | Via RapidAPI |
| Auction engine | ✅ Complete | Sport-agnostic |
| Real-time bidding | ✅ Complete | Socket.IO |
| League standings | ✅ Complete | Works for cricket |

### Cricket Scoring Schema (Already Configured)

```javascript
{
  "key": "cricket",
  "assetType": "PLAYER",
  "scoringSchema": {
    "type": "perPlayerMatch",
    "rules": {
      "run": 1,           // 1 point per run scored
      "wicket": 20,       // 20 points per wicket taken
      "catch": 10,        // 10 points per catch
      "stumping": 25,     // 25 points per stumping
      "runOut": 20        // 20 points per run out
    }
  },
  "uiHints": {
    "assetLabel": "Player",
    "assetPlural": "Players"
  }
}
```

---

## API Coverage Assessment

### Current Integration: Cricbuzz via RapidAPI

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/matches/v1/recent` | Recent matches | ✅ Working |
| `/matches/v1/live` | Live matches | ✅ Working |
| `/matches/v1/upcoming` | Upcoming matches | ✅ Working |
| `/mcenter/v1/{matchId}/scard` | Match scorecard | ✅ Working |

### IPL 2026 Coverage Concerns

| Concern | Risk Level | Mitigation |
|---------|------------|------------|
| **Fixture availability** | 🟡 Medium | Official IPL fixtures typically released 4-6 weeks before season |
| **Player roster changes** | 🟡 Medium | IPL Mega Auction in late 2025 - rosters will change |
| **API rate limits** | 🟡 Medium | Free tier: 100 requests/day - may need paid tier |
| **Live scoring accuracy** | 🟢 Low | Cricbuzz is reliable for IPL |
| **Ball-by-ball data** | 🟢 Low | Available via scorecard endpoint |

### API Rate Limit Analysis

| Scenario | Daily Requests | Free Tier (100/day) | Paid Tier Needed? |
|----------|----------------|---------------------|-------------------|
| 10 users, 1 match/day | ~50 | ✅ OK | No |
| 50 users, 2 matches/day | ~150 | ❌ Exceeds | Yes |
| 250 users, 2 matches/day | ~600 | ❌ Exceeds | Yes (Pro tier) |

**Recommendation:** Budget for RapidAPI Pro tier (~$50-100/month during IPL season)

### Alternative API Options

| Provider | Coverage | Cost | Reliability |
|----------|----------|------|-------------|
| **Cricbuzz (RapidAPI)** | Full IPL | Free tier limited | ⭐⭐⭐⭐ Good |
| **ESPNcricinfo** | Full IPL | No official API (scraping) | ⭐⭐⭐ Risky |
| **SportsRadar** | Full IPL | Enterprise pricing | ⭐⭐⭐⭐⭐ Excellent |
| **CricAPI** | Partial | Freemium | ⭐⭐⭐ Variable |

---

## Work Required

### Phase 1: Data Preparation (January 2026)

| Task | Effort | Priority | Dependencies |
|------|--------|----------|--------------|
| Monitor IPL 2026 fixture release | Ongoing | High | BCCI announcement |
| Seed IPL teams (10 franchises) | 2 hours | High | None |
| Seed IPL player rosters | 4-8 hours | High | Post-auction (Dec 2025/Jan 2026) |
| Create IPL competition template | 2 hours | Medium | Teams seeded |
| Verify Cricbuzz API for IPL | 2 hours | High | IPL fixtures available |

### Phase 2: Feature Enhancements (February 2026)

| Task | Effort | Priority | Notes |
|------|--------|----------|-------|
| Workplace branding/theming | 1 week | Medium | Corporate look & feel |
| Company/team grouping | 3-5 days | Medium | Group users by company |
| Invite-by-email (corporate) | 2-3 days | Medium | Bulk invite support |
| Leaderboard enhancements | 2-3 days | Low | Cross-company rankings |
| Hindi localization | 1 week | Low | Optional for launch |

### Phase 3: Launch Preparation (March 2026)

| Task | Effort | Priority | Notes |
|------|--------|----------|-------|
| Import IPL 2026 fixtures | 2 hours | High | Once BCCI releases |
| Beta testing with pilot company | 1 week | High | Validate full flow |
| Performance testing | 2-3 days | High | Handle concurrent users |
| Documentation/user guides | 2-3 days | Medium | Hindi + English |

---

## Scoring Refinements for IPL

### Current Scoring (May Need Adjustment)

| Action | Current Points | IPL Suggestion | Rationale |
|--------|---------------|----------------|-----------|
| Run scored | 1 | 1 | Standard |
| Wicket taken | 20 | 25 | T20 wickets are valuable |
| Catch | 10 | 10 | Standard |
| Stumping | 25 | 25 | Standard |
| Run out | 20 | 15 | Slightly lower than wicket |
| **Six** | 0 | +2 bonus | T20 excitement |
| **Four** | 0 | +1 bonus | Reward boundaries |
| **50+ runs** | 0 | +10 bonus | Milestone reward |
| **100+ runs** | 0 | +25 bonus | Rare in T20 |
| **3+ wickets** | 0 | +10 bonus | Bowling milestone |
| **Maiden over** | 0 | +15 bonus | Rare in T20 |

### Implementation

```javascript
// Enhanced IPL Scoring Schema
{
  "key": "cricket_ipl",
  "name": "IPL T20",
  "assetType": "PLAYER",
  "scoringSchema": {
    "type": "perPlayerMatch",
    "rules": {
      "run": 1,
      "six_bonus": 2,
      "four_bonus": 1,
      "wicket": 25,
      "catch": 10,
      "stumping": 25,
      "runOut": 15,
      "maiden": 15
    },
    "milestones": {
      "runs_50": 10,
      "runs_100": 25,
      "wickets_3": 10,
      "wickets_5": 25
    }
  }
}
```

---

## Workplace-Specific Features

### Must Have (Launch)

| Feature | Description | Effort |
|---------|-------------|--------|
| Company grouping | Users belong to a company | Medium |
| Private leagues | Only colleagues can join | Low (exists) |
| Corporate branding | Logo, colors per company | Medium |
| Admin dashboard | HR can view engagement | Medium |

### Nice to Have (Post-Launch)

| Feature | Description | Effort |
|---------|-------------|--------|
| SSO integration | Login via company credentials | High |
| Slack/Teams integration | Notifications in work chat | Medium |
| Inter-company leagues | Company vs company | Medium |
| Prizes/rewards | Integration with HR platforms | Medium |
| Analytics dashboard | Engagement metrics for HR | Medium |

---

## Go-to-Market Strategy

### Target Segments

| Segment | Company Size | Decision Maker | Channel |
|---------|--------------|----------------|---------|
| Tech Companies | 100-5000 | HR/Culture team | Direct sales, LinkedIn |
| Startups | 20-100 | Founders | Product Hunt, Twitter |
| BPOs/Call Centers | 1000+ | HR Director | Partnerships |
| Banks/Financial | 5000+ | Employee Engagement | Enterprise sales |

### Pricing Model Options

| Model | Description | Price Point |
|-------|-------------|-------------|
| **Freemium** | Free for <50 users, paid above | £0 / £2-5 per user/season |
| **Per-company** | Flat fee per company | £99-499/season |
| **Enterprise** | Custom pricing, SLAs | £1000+/season |

### Launch Timeline

```
January 2026
├── Week 1-2: Seed IPL teams & players (post mega-auction)
├── Week 3-4: Workplace feature development

February 2026
├── Week 1-2: Beta with pilot company
├── Week 3: Iterate based on feedback
├── Week 4: Import IPL fixtures (when released)

March 2026
├── Week 1-2: Marketing push
├── Week 3: Soft launch
├── March 26: IPL 2026 starts 🏏
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| IPL fixtures delayed | Low | High | Manual fixture entry as backup |
| API rate limits hit | Medium | Medium | Upgrade to paid tier, caching |
| Player roster changes mid-season | Low | Medium | Admin tools to update players |
| Low corporate adoption | Medium | High | Focus on tech companies, free tier |
| Competition from Dream11 | Medium | Medium | Differentiate on auction format |
| Time zone complexity | Low | Low | IST as primary, UTC in database |

---

## Cost Estimates

### Development Costs

| Item | Hours | Rate (est.) | Cost |
|------|-------|-------------|------|
| Data seeding (teams, players) | 10 | Internal | - |
| Workplace features | 40 | Internal | - |
| Testing & QA | 20 | Internal | - |
| **Total Development** | 70 hours | | |

### Operational Costs (Per Season)

| Item | Monthly | Per Season (2.5 months) |
|------|---------|-------------------------|
| RapidAPI Pro tier | £40-80 | £100-200 |
| Railway hosting (if migrated) | £30-50 | £75-125 |
| MongoDB Atlas | £0-20 | £0-50 |
| **Total Operational** | | **£175-375/season** |

---

## Success Metrics

| Metric | Target (Season 1) | Stretch Goal |
|--------|-------------------|--------------|
| Companies onboarded | 10 | 25 |
| Total users | 500 | 2,000 |
| Auctions completed | 50 | 200 |
| User retention (weekly active) | 60% | 75% |
| NPS score | 30+ | 50+ |

---

## Next Steps

1. **Immediate (This Week)**
   - [ ] Verify RapidAPI Cricbuzz coverage for IPL
   - [ ] Monitor IPL 2026 mega auction (player rosters)
   - [ ] Document API rate limit requirements

2. **January 2026**
   - [ ] Seed IPL teams and players
   - [ ] Build workplace features
   - [ ] Identify pilot company

3. **February 2026**
   - [ ] Beta test with pilot
   - [ ] Import IPL fixtures
   - [ ] Marketing preparation

4. **March 2026**
   - [ ] Launch before IPL starts (March 26)

---

## Appendix: IPL Player Data Sources

For seeding IPL player rosters:

| Source | Data Available | Format |
|--------|----------------|--------|
| IPL Official Site | Teams, squads | Manual/scrape |
| ESPNcricinfo | Full player profiles | Manual/scrape |
| Cricbuzz | Player IDs for API | API |
| Wikipedia | Historical data | Manual |

**Recommendation:** Wait for IPL 2026 mega auction results (typically December 2025/January 2026) before seeding players, as rosters change significantly.

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025  
**Status:** PLANNING
