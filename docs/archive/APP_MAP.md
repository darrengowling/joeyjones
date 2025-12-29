# Sport X Application Map
**Last Updated:** 2025-11-28  
**Purpose:** Complete reference for navigation, bug reporting, and feature planning

---

## Page Index

| # | Page Name | Route | Auth Required | Parent Page |
|---|-----------|-------|---------------|-------------|
| 1 | Home Page | `/` | No | - |
| 2 | Help Center | `/help` | No | Home |
| 3 | Browse Teams | `/clubs` | No | Home |
| 4 | My Competitions | `/app/my-competitions` | Yes | Home |
| 5 | Create Competition | `/app/create-league` | Yes | My Competitions |
| 6 | Competition Detail | `/app/competition/:id` | Yes | My Competitions |
| 7 | Competition Dashboard | `/app/league/:id` | Yes | My Competitions |
| 8 | Auction Waiting Room | `/auction/:id` (waiting) | Yes | Competition Dashboard |
| 9 | Auction Room (Live) | `/auction/:id` (active) | Yes | Auction Waiting Room |
| 10 | Auction Complete | `/auction/:id` (completed) | Yes | Auction Room |

---

## Navigation Flow

```
HOME PAGE
├── Help Center
├── Browse Teams
└── [Login via Magic Link]
    └── MY COMPETITIONS
        ├── Create Competition
        │   └── Team Selection → Create → Competition Detail
        │
        └── [Select Competition]
            └── COMPETITION DASHBOARD
                ├── Tabs:
                │   ├── Summary (default)
                │   ├── League Table
                │   ├── Fixtures
                │   ├── Match Breakdown
                │   └── Competition Detail
                │
                └── [Commissioner: Start Auction]
                    └── AUCTION WAITING ROOM
                        └── [Begin Auction]
                            └── AUCTION ROOM (LIVE)
                                └── [Auction Completes]
                                    └── AUCTION COMPLETE
```

---

## Detailed Page Breakdown

### 1. HOME PAGE
**Route:** `/`  
**Auth:** Not required  
**Page Identifier:** None (landing page)

**Elements:**
- App branding
- Login button (magic link)
- Navigation to Help Center
- Navigation to Browse Teams

**Navigation From Here:**
- → Help Center
- → Browse Teams
- → My Competitions (after login)

---

### 2. HELP CENTER
**Route:** `/help`  
**Auth:** Not required  
**Page Identifier:** "HELP CENTER"

**Elements:**
- User guide/manual
- FAQs
- How to play instructions
- Back to Home button

**Navigation From Here:**
- ← Home Page

---

### 3. BROWSE TEAMS
**Route:** `/clubs`  
**Auth:** Not required  
**Page Identifier:** "BROWSE TEAMS"

**Elements:**
- List of all available teams/clubs
- Filter by sport
- Team information
- Back to Home button

**Navigation From Here:**
- ← Home Page

---

### 4. MY COMPETITIONS
**Route:** `/app/my-competitions`  
**Auth:** Required (redirects to home if not logged in)  
**Page Identifier:** "MY COMPETITIONS"

**Elements:**
- List of competitions user is participating in
- Competition cards showing:
  - Competition name
  - Sport type
  - Number of participants
  - Status (pending, active, completed)
  - Next auction time (if scheduled)
- "Create Your Competition" button
- User name display
- Logout option

**States:**
- Empty state (no competitions)
- Populated state (shows competitions)

**Navigation From Here:**
- → Create Competition
- → Competition Dashboard (click on competition card)
- ← Home Page

---

### 5. CREATE COMPETITION
**Route:** `/app/create-league`  
**Auth:** Required  
**Page Identifier:** "CREATE COMPETITION"

**Elements:**
- Sport selection dropdown
- Budget per Manager input
- Min/Max Managers input
- Clubs per Manager input
- Timer settings (Bidding Timer, Anti-Snipe)
- Team Selection (if enabled):
  - Filter by competition (EPL/UCL/All)
  - Team checkboxes
  - Selected count display
- Create button
- Back to My Competitions button

**States:**
- Empty form
- Team selection mode (when teams are being selected)

**Navigation From Here:**
- → Competition Detail (after creation)
- ← My Competitions

---

### 6. COMPETITION DETAIL (Non-Commissioner View)
**Route:** `/app/competition/:id`  
**Auth:** Required  
**Page Identifier:** "COMPETITION DETAIL PAGE"

**Elements:**
- Competition name
- Join token display
- Number of participants
- Competition rules (budget, slots, etc.)
- Sport type
- Back button

**Who Sees This:**
- Non-commissioners who need to join
- Shows before user joins the competition

**Navigation From Here:**
- ← My Competitions

---

### 7. COMPETITION DASHBOARD
**Route:** `/app/league/:id`  
**Auth:** Required  
**Page Identifier:** "COMPETITION DASHBOARD"

**Tab Structure:**

#### Tab 1: SUMMARY (Default)
**Elements:**
- Your Roster (clubs owned)
- Budget Remaining
- Position in league
- Next auction info (if pending)
- Commissioner controls:
  - Start Auction button
  - Schedule Auction button

#### Tab 2: LEAGUE TABLE
**Elements:**
- Rankings table:
  - Position
  - Manager name
  - Points
  - Goals For
  - Goals Against
  - Goal Difference

#### Tab 3: FIXTURES
**Elements:**
- List of all fixtures
- User's teams highlighted
- Match dates and times
- Results (if completed)
- Filter by date/round

#### Tab 4: MATCH BREAKDOWN
**Elements:**
- Detailed match results
- Individual player/team performance
- Points breakdown
- Empty state (if no matches played)

#### Tab 5: COMPETITION DETAIL
**Elements:**
- Competition settings
- Participant list
- Join token (for inviting others)
- Rules and budget info

**Commissioner-Only Elements:**
- Start Auction button (on Summary tab)
- Schedule Auction option
- Manage participants

**Navigation From Here:**
- → Auction Waiting Room (commissioner starts auction)
- ← My Competitions

---

### 8. AUCTION WAITING ROOM
**Route:** `/auction/:id` (status: waiting)  
**Auth:** Required  
**Page Identifier:** "AUCTION ROOM" (same as live)

**Elements:**
- List of participants in waiting room
- "Waiting for commissioner..." message
- Participant avatars/names
- Commissioner controls:
  - "Begin Auction" button
  - Cancel button

**Who Can Access:**
- All participants in the competition
- Commissioner has control buttons

**Navigation From Here:**
- → Auction Room (Live) when commissioner starts
- ← Competition Dashboard (if cancelled)

---

### 9. AUCTION ROOM (LIVE)
**Route:** `/auction/:id` (status: active)  
**Auth:** Required  
**Page Identifier:** "AUCTION ROOM"

**Main Elements:**

1. **Header Section:**
   - Competition name
   - Current Lot number / Total lots
   - Auction status

2. **Current Club Section:**
   - Club name
   - Club details (country, UEFA ID)
   - **Next Fixture Card** (NEW FEATURE):
     - Opponent
     - Home/Away
     - Match date and time
     - Time until match (e.g., "in 2d")
     - Competition name

3. **Bidding Section:**
   - Current highest bid amount
   - Current highest bidder name
   - Timer countdown
   - Bid input field (pre-filled with current bid)
   - "Place Bid" button

4. **Sidebar:**
   - Manager Budgets list
   - Current Club Ownership (who owns what)
   - Clubs Available count

5. **Commissioner Controls:**
   - Pause Auction
   - Complete Lot (force move to next)
   - Delete Auction

**States:**
- Active bidding (timer running)
- Between lots (3-second countdown)
- Paused (commissioner paused)

**Key Features:**
- Real-time updates via WebSocket
- Anti-snipe timer extension
- Automatic lot completion
- Live budget updates

**Navigation From Here:**
- → Auction Complete (when all lots sold)
- ← Competition Dashboard (if auction cancelled)

---

### 10. AUCTION COMPLETE
**Route:** `/auction/:id` (status: completed)  
**Auth:** Required  
**Page Identifier:** "AUCTION ROOM"

**Elements:**
- "Auction Complete!" message
- Final manager budgets
- Clubs sold count
- Summary of who won what
- Link back to Competition Dashboard

**Navigation From Here:**
- ← Competition Dashboard

---

## Page States Reference

### Empty States
- My Competitions (no competitions joined)
- Match Breakdown (no matches played yet)
- Fixtures (no fixtures scheduled)

### Populated States
- My Competitions (showing competition cards)
- Competition Dashboard (all tabs with data)
- Auction Room (active bidding)

### Error States
- Authentication required (redirect to home)
- Competition not found
- Auction not found
- Network error during loading

---

## User Roles & Permissions

### Non-Authenticated User
**Can Access:**
- Home Page
- Help Center
- Browse Teams

**Cannot Access:**
- My Competitions
- Any competition pages
- Auction pages

### Authenticated User (Participant)
**Can Access:**
- All non-authenticated pages
- My Competitions
- Competitions they've joined (dashboard)
- Auctions for their competitions

**Can Do:**
- Join competitions via invite token
- View competition details
- Participate in auctions (place bids)
- View fixtures and league table

**Cannot Do:**
- Start auctions
- Pause/control auctions
- Delete auctions

### Authenticated User (Commissioner)
**Can Access:**
- Everything a participant can access

**Additional Powers:**
- Create competitions
- Start auctions
- Pause auctions
- Complete lot manually
- Delete auctions
- Manage competition settings

---

## Key Features by Page

| Page | Key Features |
|------|--------------|
| Home | Login, Navigation |
| Help Center | User manual, FAQs |
| Browse Teams | Team directory |
| My Competitions | Competition list, Create button |
| Create Competition | Team selection, Configuration |
| Competition Detail | Join token, Rules |
| Dashboard - Summary | Roster, Budget, Start Auction |
| Dashboard - League Table | Rankings, Points |
| Dashboard - Fixtures | Match schedule, User teams highlighted |
| Dashboard - Match Breakdown | Detailed results |
| Dashboard - Competition Detail | Settings, Participants |
| Auction Waiting Room | Participant list, Begin button |
| Auction Room (Live) | **Next Fixture Card**, Real-time bidding, Timer |
| Auction Complete | Final results, Summary |

---

## Recent Features Added

### ✅ Page Identifiers (P1)
- Small uppercase label on each page
- Makes bug reporting easier
- Format: "PAGE NAME" above main heading

### ✅ Next Fixture Card (P1)
- Displays on Auction Room during live bidding
- Shows opponent, venue, date, time until match
- Only appears if team has an upcoming fixture
- Helps bidders make strategic decisions

---

## Planned Features (Not Yet Implemented)

### 📋 Auction History Tab
- New tab on Competition Dashboard
- Shows list of past auctions
- Click to view completed auction details
- Keeps auction page focused on live bidding

### 📋 Commissioner Selects Gameweek (P2)
- Feature to import fixtures by gameweek
- Uses API-Football integration
- Allows commissioner to schedule match days

### 📋 Code Refactoring (P2)
- Break down monolithic server.py
- Merge duplicate pages (LeagueDetail → CompetitionDashboard)
- Delete legacy clubs collection

---

## Notes for Bug Reporting

When reporting a bug, please include:
1. **Page Name** (from page identifier label or this map)
2. **Route/URL** (from browser address bar)
3. **User Role** (participant or commissioner)
4. **Page State** (empty, populated, loading, error)
5. **Screenshot** (if possible)
6. **Steps to Reproduce**

Example:
> **Page:** Auction Room (Live)  
> **Route:** `/auction/82a2a50c-dae0-4b06-b8fb-2ef8c7bd35d7`  
> **Role:** Commissioner  
> **State:** Active bidding, Lot 2/4  
> **Issue:** Timer not showing next fixture card for Arsenal

---

## Technical Notes

- **Frontend Framework:** React
- **Backend Framework:** FastAPI (Python)
- **Database:** MongoDB
- **Real-time:** Socket.IO (WebSocket)
- **Authentication:** Magic Link (passwordless)
- **Deployment:** Kubernetes cluster

---

## File Locations

- **Frontend Pages:** `/app/frontend/src/pages/`
- **Backend Routes:** `/app/backend/server.py`
- **Database Collections:** MongoDB `test_database`

---

**End of App Map**
