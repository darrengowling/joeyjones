# UI/UX Audit Report - Sport X Platform

**Date:** December 13, 2025 (Updated Evening)  
**Prepared by:** Development Team  
**Purpose:** Comprehensive UI/UX review for pilot readiness and future improvements

---

## Executive Summary

A page-by-page UI/UX review was conducted across all key user flows. The platform is **functional and usable**, with several opportunities for improvement, particularly around:

1. **Team Selection UX** (Critical) - Users selecting a competition don't get filtered teams
2. **Mobile Experience** - Long scrolling, some layout issues
3. **Button Hierarchy** - Some secondary actions given equal weight
4. **Auction Clarity** - Bidder status could be clearer
5. **Real-time State Updates** - Roster display lag reported (technical fix in progress)

---

## User Testing Feedback (Dec 13 - "Ash friends test 2")

| Feedback | Likely Cause | Status |
|----------|--------------|--------|
| "Couldn't place a bid" | Multiple possibilities - awaiting clarification | INVESTIGATING |
| "1 team then full roster" | Race condition - fix identified | READY TO FIX |
| "United offered 2 times" | Possibly unsold retry (expected) - awaiting clarification | INVESTIGATING |
| "Roster lagged in 2 places" | Same race condition as above | READY TO FIX |

---

## Priority Matrix

| Priority | Issue | Page | Impact |
|----------|-------|------|--------|
| 🔴 High | Team selection doesn't filter based on competition | LeagueDetail | Commissioners start auctions with wrong teams |
| 🔴 High | Roster display lag / wrong count | AuctionRoom | User confusion, incorrect "Full" status |
| 🔴 High | "Unknown" manager names (verify if still occurring) | AuctionRoom | Confusing for users |
| 🟠 Medium | "Explore" button equal weight to primary actions | Home | Visual clutter, especially mobile |
| 🟠 Medium | No "you're winning/outbid" visual indicator | AuctionRoom | User confusion about bid status |
| 🟠 Medium | LeagueDetail excessive scrolling on mobile | LeagueDetail | Team selection missed below fold |
| 🟡 Low | No search on Help page | Help | Users must browse to find answers |
| 🟡 Low | Standings lack visual rank indicators | Dashboard | Missed engagement opportunity |

---

## Page-by-Page Analysis

---

### Page 1: MyCompetitions (Home)

**URL:** `/`

#### Screenshots
- Desktop: Shows hero section with tagline and 3 action buttons
- Mobile: Buttons stack vertically

#### ✅ What's Working
- Clear tagline: "Sports Gaming with Friends. No Gambling. All Game."
- Button hierarchy with filled primary, outlined secondary
- Mobile stacking works well
- Friendly empty state with trophy emoji

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| **"Explore" button prominence** | Equal weight to Create/Join | Demote to text link - reclaims vertical space | Medium |
| Sign In prominence for new users | Small button in corner | More prominent CTA if not signed in | Medium |
| Empty state when signed out | Generic message | "Sign in to see your competitions" | Medium |
| Value proposition | Brief description | Add 3 icons showing flow: Create → Auction → Score | Low |

#### Key Recommendation
**Demote "Explore Teams/Players" from button to text link** - This reclaims vertical space on mobile and clarifies the two primary actions (Create or Join).

---

### Page 2: Create Competition Modal

**URL:** Modal overlay on Home

#### Screenshots
- Desktop: Full form visible in modal
- Mobile: Requires scrolling

#### ✅ What's Working
- Clear title and logical field order
- Sport icons in dropdown
- Budget stepper with +/- buttons
- Flag icons for competitions
- Helper text for budget increments

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| **No preview of teams** | User doesn't know which teams they'll get | Add "X teams will be included" after Competition selection | High |
| Modal height on mobile | Requires scrolling | Consider 2-step wizard | Medium |
| Competition dropdown clarity | "Select which competition to run" | Make clearer this affects team availability | Medium |
| Timer settings cut off | Below fold on mobile | Group into Basic/Advanced sections | Low |

#### Key Recommendation
**Add team count preview** after competition selection: "Premier League selected → 20 teams will be available"

---

### Page 3: LeagueDetail

**URL:** `/league/{id}`

#### Screenshots
- Desktop: Settings, participants, team list
- Mobile: Very long scroll required

#### ✅ What's Working
- Clear status badge
- Invite token prominent with Copy button
- League Settings card clean
- Auction Info shows timer settings
- "How It Works" onboarding section

#### 🔴 CRITICAL ISSUE: Team Selection UX

**The Problem Flow:**
```
1. Commissioner creates competition, selects "Premier League"
              ↓
2. Lands on LeagueDetail page
              ↓
3. Page shows "74 clubs available" (ALL teams, not filtered)
              ↓
4. Commissioner sees Start Auction button above the fold
              ↓
5. Commissioner clicks Start (thinking they have PL teams)
              ↓
6. Auction includes PL + CL + AFCON teams ❌
```

**Root Cause:** The "Filter by Competition" dropdown exists but is:
- Below the fold
- Not auto-applied based on `competitionCode` from creation

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| **Auto-filter teams** | All 74 teams by default | Auto-apply filter based on league.competitionCode | **HIGH** |
| **Team selection below fold** | Easy to miss | Move up OR add summary card "20 PL teams selected" | High |
| Warning before Start | No warning | Confirm if multiple competitions selected | High |
| Mobile scrolling | 4+ screens | Collapsible sections or accordion | Medium |
| Duplicate info display | Settings shown multiple times | Consolidate into single view | Low |

#### Key Recommendation
**Auto-filter teams on page load:**
```javascript
if (league.competitionCode && league.competitionCode !== 'all') {
  const response = await axios.get(`${API}/clubs?sportKey=${league.sportKey}&competition=${league.competitionCode}`);
  setAvailableAssets(response.data);
  setSelectedAssetIds(response.data.map(t => t.id));
}
```

**Plus:** Add summary card near top: "✅ 20 Premier League teams selected for auction"

---

### Page 4: AuctionRoom

**URL:** `/auction/{id}`

#### Screenshots
- Desktop: Bidding interface with current lot, budgets, clubs sidebar
- Mobile: Compact layout with bid controls

#### ✅ What's Working
- Progress indicator: "Lot 4/6"
- Manager Budgets cards
- Large Current Bid display
- +5m, +10m, +20m, +50m quick buttons
- Roster indicator with Full/Active status
- Clubs Available sidebar with counts
- Friendly messaging during transitions

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| **Bidder status unclear** | Name shown but not prominent | Add "YOU'RE WINNING" (green) or "OUTBID" (red) indicator | High |
| **"Unknown" manager names** | Shows "Unknown" | Should show actual display names (verify if still occurring) | High |
| Input field context | Empty placeholder | Show "Current bid: £5m" label above input | High |
| Timer not visible in preparing | Hourglass shown | Show countdown to next lot | Medium |
| Debug button prominent | "Download Debug Report" visible | Hide or minimize for production | Medium |
| Bid history hidden | Below fold | Show last 2-3 bids inline | Medium |

#### Key Recommendation
**Add clear bidder status indicator:**
```
- If YOU are highest bidder: 🟢 "YOU'RE WINNING - £5m"
- If someone else: 🔴 "OUTBID - daz2 has £5m"
```

---

### Page 5: CompetitionDashboard

**URL:** `/competition/{id}`

#### Screenshots
- Three-tab structure: Summary, Standings, Fixtures
- Cards for roster, budget, league info

#### ✅ What's Working
- Clear 3-tab navigation
- Sport emoji visual identifier
- Color-coded status badges
- Your Roster card with prices
- Large budget display
- Commissioner tools (CSV upload, imports)
- Real-time Socket.IO updates

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| No visual rank indicators | Position as number only | Add 🥇🥈🥉 for top 3 | Low |
| No quick score preview | Must go to Fixtures tab | Show next fixture + latest results on Summary | Medium |
| Commissioner actions scattered | Multiple buttons | Group into "Admin Actions" section | Low |
| No refresh indicator | Updates silently | Add "Last updated: X mins ago" | Low |
| Tab bar not sticky | Scrolls away on mobile | Keep tabs visible | Medium |

#### Key Recommendation
**Add "Next Match" card to Summary tab** - Shows upcoming fixture with countdown to engage users between matches.

---

### Page 6: Help Page

**URL:** `/help`

#### Screenshots
- Desktop: Welcome banner, Quick Navigation grid, collapsible sections
- Mobile: Clean stacking, readable

#### ✅ What's Working
- Clear welcome banner with brand message
- Quick Navigation jump links
- Collapsible accordion sections with emoji icons
- Logical organization (Getting Started, Commissioners, Players, etc.)
- Step-by-step numbered instructions
- 💡 Tip callouts
- "Need More Help?" footer
- Excellent mobile layout

#### 🔶 Improvements Needed

| Issue | Current | Suggested | Priority |
|-------|---------|-----------|----------|
| No search | Must browse/scroll | Add search bar for quick answers | Medium |
| No video tutorials | Text only | Embed 60-90 second walkthroughs | Medium |
| No contextual help | Help page standalone | Add "?" icons on other pages linking to relevant sections | Medium |
| FAQ collapsed by default | Hidden | Show top 3 FAQs expanded | Low |
| "Contact support" vague | Generic text | Add actual email address | Low |

#### Key Recommendation
**Add search bar** and **contextual "?" help icons** on key pages (Auction, Dashboard) linking to relevant sections.

---

## Mobile-Specific Issues Summary

| Page | Issue | Severity |
|------|-------|----------|
| Home | Buttons take too much vertical space | Medium |
| Create Modal | Form requires scrolling | Medium |
| LeagueDetail | 4+ screens of scrolling, team selection missed | High |
| AuctionRoom | Bid status unclear, roster may be cut off | Medium |
| Dashboard | Tab bar scrolls away | Low |
| Help | ✅ Works well | - |

---

## Recommended Quick Wins

These can be implemented with minimal effort for maximum impact:

| # | Change | Page | Effort | Impact |
|---|--------|------|--------|--------|
| 1 | Auto-filter teams based on competitionCode | LeagueDetail | 2 hrs | High |
| 2 | Add "X teams selected" summary card | LeagueDetail | 1 hr | High |
| 3 | Demote "Explore" to text link | Home | 30 min | Medium |
| 4 | Add YOU'RE WINNING/OUTBID indicator | AuctionRoom | 2 hrs | High |
| 5 | Show "Current bid: £Xm" above input | AuctionRoom | 30 min | Medium |
| 6 | Add 🥇🥈🥉 to standings | Dashboard | 30 min | Low |
| 7 | Make tabs sticky on mobile | Dashboard | 1 hr | Medium |

---

## Design System Notes

### Current Strengths
- Consistent use of Tailwind CSS
- shadcn/ui components provide good baseline
- Emoji usage adds personality
- Color coding for status (green=good, red=warning, blue=info)

### Opportunities
- Standardize button hierarchy across all pages
- Create reusable "status indicator" component for auction
- Mobile-first approach for new features
- Consider collapsible/accordion pattern for long pages

---

## Next Steps

1. **Immediate (Before Pilot):**
   - Fix team selection auto-filtering
   - Add team count summary on LeagueDetail

2. **Short-term (During Pilot):**
   - Add bidder status indicator
   - Demote "Explore" button
   - Gather more mobile feedback

3. **Post-Pilot:**
   - Full mobile optimization pass
   - Help page search
   - Video tutorials
   - Dashboard visual enhancements

---

## Appendix: Screenshot Capture Guide

To capture fresh screenshots for sharing, visit these URLs:

### Page URLs for Screenshots

| Page | Desktop (1920x800) | Mobile (390x844) |
|------|-------------------|------------------|
| **Home** | `http://localhost:3000` | Same |
| **Create Modal** | Click "Create Your Competition" on Home | Same |
| **LeagueDetail** | `http://localhost:3000/league/{league_id}` | Same (scroll to see team selection) |
| **AuctionRoom** | `http://localhost:3000/auction/{auction_id}` | Same |
| **Dashboard** | `http://localhost:3000/competition/{league_id}` | Same |
| **Help** | `http://localhost:3000/help` | Same |

### Production URLs

| Page | URL |
|------|-----|
| **Home** | `https://draft-kings-mobile.emergent.host` |
| **Help** | `https://draft-kings-mobile.emergent.host/help` |

### Key Screenshots to Capture

1. **Home Page** - Shows button hierarchy issue (Explore equal to Create/Join)
2. **LeagueDetail scrolled down** - Shows team selection filter below fold
3. **AuctionRoom with active bid** - Shows bidding interface (reference red3 screenshot from testing)
4. **Help Page** - Shows well-structured help sections

### Screenshot from User Testing (Reference)

The user shared a screenshot during testing showing the AuctionRoom with:
- Current Bid: £5m
- Bidder: daz2
- +5m, +10m, +20m, +50m buttons
- Input field showing "15"

This screenshot demonstrates both the working bid controls and the self-outbid fix in action.

---

## Change Log

| Date | Change |
|------|--------|
| Dec 13, 2025 | Initial audit report created |

---

**Report Version:** 1.0  
**Last Updated:** December 13, 2025
