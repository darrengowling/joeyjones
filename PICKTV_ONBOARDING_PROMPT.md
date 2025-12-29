# Pick TV - New Project Onboarding Prompt

**Created:** December 28, 2025  
**Purpose:** Complete onboarding document for starting the Pick TV project, detailing all reusable code, functionality, and user flows from Sport X  
**Status:** READY FOR USE

---

## ⚠️ CRITICAL: How to Start This Project

### Recommended Approach: Fork Sport X

**Pick TV should be started by FORKING the Sport X project**, not from scratch. This gives you:
- ✅ Full working auction engine
- ✅ Authentication system
- ✅ League management
- ✅ All infrastructure (Socket.IO, Redis, MongoDB)
- ✅ UI components and pages

### Steps to Start Pick TV Project

1. **In Emergent:** Use "Save to GitHub" on Sport X project
2. **Create new Emergent project** and connect to the forked GitHub repo
3. **OR** Ask Emergent support about forking an existing project
4. **First task:** Configure for Pick TV (theming, terminology, sport config)

### If Starting Fresh (Not Recommended)

If you must start from scratch, you'll need to:
1. Clone Sport X from GitHub: `https://github.com/[user]/sport-x` (get URL from user)
2. Copy all backend and frontend code
3. Reference documentation below for understanding

---

## 🎯 Project Overview

**Pick TV** is a fantasy entertainment platform where users draft reality TV contestants and earn points based on show outcomes. It shares the core auction engine and infrastructure with **Sport X** (fantasy sports), but targets elimination-based entertainment shows like Survivor, Bake Off, and Eurovision.

### Key Differences from Sport X

| Aspect | Sport X | Pick TV |
|--------|---------|--------|
| **Assets** | Football clubs, cricket players | TV show contestants |
| **Events** | Matches with scores | Episodes with eliminations |
| **Scoring** | Goals, wins, draws | Survival, challenge wins, final placement |
| **Data Source** | Football-Data.org API, CSV | Manual entry only (no API) |
| **Currency** | £ (millions) | ⭐ (Stars) |
| **Duration** | Season (months) | Show run (weeks) |

---

## 📚 Required Reading (In Order)

Before any implementation, read these documents from the Sport X codebase:

| # | Document | Location | Purpose | Read Time |
|---|----------|----------|---------|----------|
| 1 | `CORE_AUCTION_ENGINE.md` | `/app/` or GitHub | Reusable auction system | 15 min |
| 2 | `SHARED_CODEBASE.md` | `/app/` or GitHub | What's shared vs separate | 10 min |
| 3 | `REALITY_TV_TECHNICAL_SPEC.md` | `/app/` or GitHub | Full technical spec | 30 min |
| 4 | `DATABASE_SCHEMA.md` | `/app/` or `/app/docs/` | Database collections | 20 min |
| 5 | `API_REFERENCE.md` | `/app/` or `/app/docs/` | All 61 endpoints | 15 min |

**Note:** If forked, these files are in `/app/`. If cloned from GitHub, they're at repo root.

---

## 🏗️ Architecture Summary

### Technology Stack (Identical to Sport X)

```
Frontend: React 18 + Tailwind CSS + shadcn/ui
Backend:  FastAPI (Python 3.11) + Socket.IO
Database: MongoDB (Motor async driver)
Cache:    Redis (Socket.IO pub/sub)
Auth:     JWT tokens
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PICK TV                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │  React Frontend │◄───►│  FastAPI Backend │                   │
│  │  (Pick TV Theme)│     │  (Shared Engine) │                   │
│  └─────────────────┘     └────────┬────────┘                    │
│                                   │                              │
│                          ┌────────┴────────┐                    │
│                          │    Socket.IO    │                    │
│                          │  (Real-time)    │                    │
│                          └────────┬────────┘                    │
│                                   │                              │
│              ┌────────────────────┼────────────────────┐        │
│              │                    │                    │        │
│       ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐  │
│       │   MongoDB   │     │    Redis    │     │   Manual    │  │
│       │ (Data Store)│     │  (Pub/Sub)  │     │ Score Entry │  │
│       └─────────────┘     └─────────────┘     └─────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ What You Get For Free (100% Reusable)

### 1. Auction Engine

The entire auction system works without modification:

| Feature | Implementation | Notes |
|---------|----------------|-------|
| **Real-time bidding** | Socket.IO events | Proven with 7+ concurrent users |
| **Timer management** | Server-side countdown | 30-second default, configurable |
| **Anti-snipe protection** | 10-second extension | Prevents last-second sniping |
| **Bid validation** | Backend checks | Budget, roster limits, self-outbid prevention |
| **Queue management** | Asset rotation | Automatic lot progression |
| **Multi-pod sync** | Redis pub/sub | Scales horizontally |

**Key Files:**
- `/app/backend/server.py` - Lines 4200-4600 (auction logic)
- `/app/frontend/src/pages/AuctionRoom.js` - Full auction UI

### 2. Authentication System

| Feature | Endpoint | Notes |
|---------|----------|-------|
| **Registration** | `POST /api/auth/register` | Email + password |
| **Login** | `POST /api/auth/login` | Returns JWT |
| **Magic Links** | `POST /api/auth/magic-link` | Email-based login |
| **Token Refresh** | `POST /api/auth/refresh` | Extend session |
| **Password Reset** | `POST /api/auth/reset-password` | Email flow |

**Key Files:**
- `/app/backend/server.py` - Lines 800-1200 (auth routes)
- `/app/frontend/src/pages/Auth.js` - Login/Register UI

### 3. League Management

| Feature | Endpoint | Notes |
|---------|----------|-------|
| **Create league** | `POST /api/leagues` | Commissioner creates |
| **Join league** | `POST /api/leagues/{id}/join` | Via invite token |
| **Leave league** | `POST /api/leagues/{id}/leave` | Before auction starts |
| **Delete league** | `DELETE /api/leagues/{id}` | Commissioner only |
| **Invite generation** | `POST /api/leagues/{id}/invite` | Magic link creation |

**Key Files:**
- `/app/backend/server.py` - Lines 1500-2200 (league routes)
- `/app/frontend/src/pages/LeagueDetail.js` - League management UI

### 4. User Management

| Feature | Endpoint | Notes |
|---------|----------|-------|
| **Profile** | `GET /api/me` | Current user info |
| **My competitions** | `GET /api/me/competitions` | User's leagues |
| **Update profile** | `PUT /api/me` | Name, preferences |

**Key Files:**
- `/app/backend/server.py` - Lines 1200-1500 (user routes)
- `/app/frontend/src/pages/MyCompetitions.js` - Dashboard UI

### 5. Infrastructure

| Component | Configuration | Notes |
|-----------|---------------|-------|
| **Database** | MongoDB via Motor | Async driver, connection pooling |
| **Socket.IO** | Redis adapter | Multi-pod ready |
| **CORS** | Configurable origins | Production-ready |
| **Rate limiting** | Built-in (disabled for pilot) | Ready to enable |
| **Health checks** | `/api/health` | For load balancers |

---

## 🔧 What Needs Configuration (Same Code, Different Config)

### 1. Sport Configuration

Add to `sports` collection in MongoDB:

```javascript
{
  "key": "reality_tv",
  "name": "Reality TV",
  "description": "Fantasy competitions for reality TV shows",
  "active": true,
  "assetType": "CONTESTANT",
  "scoringSchema": {
    "type": "elimination",
    "rules": {
      "survives_episode": 5,
      "wins_challenge": 10,
      "wins_immunity": 15,
      "makes_final": 50,
      "wins_show": 100
    }
  },
  "uiHints": {
    "assetLabel": "Contestant",
    "assetPlural": "Contestants",
    "currencySymbol": "⭐",
    "currencyName": "Stars",
    "budgetLabel": "Star Power"
  }
}
```

### 2. UI Terminology

The frontend uses sport config for labels. Configure these mappings:

| Sport X Term | Pick TV Term | Config Key |
|--------------|--------------|------------|
| "Club" | "Contestant" | `assetLabel` |
| "Clubs" | "Contestants" | `assetPlural` |
| "£500m" | "⭐100" | `currencySymbol` + value |
| "Your Clubs" | "Your Picks" | Component text |
| "Club Auction" | "Draft" | Component text |

### 3. Theme/Branding

```css
/* Sport X (current) */
:root {
  --primary-color: #1a365d;    /* Dark blue */
  --accent-color: #38a169;     /* Green */
}

/* Pick TV (new) */
:root[data-product="picktv"] {
  --primary-color: #7c3aed;    /* Purple */
  --accent-color: #f59e0b;     /* Orange/Gold */
}
```

---

## 🆕 What You Need to Build (Pick TV Specific)

### 1. Contestant Data Model Extension

**File:** `/app/backend/models.py`

```python
class ContestantMeta(BaseModel):
    age: Optional[int] = None
    occupation: Optional[str] = None
    hometown: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    tribe: Optional[str] = None      # Survivor
    team: Optional[str] = None       # Team-based shows
    status: str = "active"           # active, eliminated, winner
```

### 2. Episode Results Model

**File:** `/app/backend/models.py`

```python
class EpisodeResult(BaseModel):
    contestantId: str
    survived: bool = True
    eliminated: bool = False
    wonChallenge: bool = False
    wonImmunity: bool = False
    receivedVotes: int = 0
```

### 3. Elimination Scoring Service

**File:** `/app/backend/scoring_service.py`

Add new scoring function for elimination-based shows:

```python
async def calculate_elimination_scores(league_id: str, episode: dict):
    """Calculate points for Reality TV episodes"""
    # Implementation in REALITY_TV_TECHNICAL_SPEC.md
    pass
```

### 4. New API Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /api/leagues/{id}/episodes` | Create episode | P0 |
| `PUT /api/leagues/{id}/episodes/{ep}/results` | Enter results | P0 |
| `POST /api/episodes/{id}/eliminate` | Mark elimination | P0 |
| `GET /api/leagues/{id}/contestants` | List contestants | P1 |
| `GET /api/reality-tv/templates` | Show templates | P2 |

### 5. New Frontend Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `ContestantCard.js` | Display contestant photo/bio | P0 |
| `EpisodeResultsForm.js` | Commissioner enters results | P0 |
| `EliminationTracker.js` | Visual elimination order | P1 |
| `ContestantGrid.js` | Grid of all contestants | P1 |

---

## 📊 Database Collections

### Shared Collections (Use As-Is)

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `users` | User accounts | `id`, `email`, `name`, `passwordHash` |
| `leagues` | League definitions | `id`, `name`, `sportKey`, `commissionerId`, `status` |
| `league_participants` | User-league membership | `leagueId`, `userId`, `clubsWon`, `budgetRemaining` |
| `auctions` | Auction state | `id`, `leagueId`, `status`, `currentBid`, `timerEndsAt` |
| `bids` | Bid history | `auctionId`, `clubId`, `userId`, `amount`, `timestamp` |
| `sports` | Sport configurations | `key`, `name`, `scoringSchema`, `uiHints` |

### Pick TV Specific Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `assets` (extended) | Contestants | Add: `meta`, `currentStatus`, `eliminationEpisode` |
| `fixtures` (extended) | Episodes | Add: `episodeNumber`, `results`, `eliminatedContestants` |
| `show_templates` | Pre-built show configs | `showKey`, `scoringPreset`, `typicalContestants` |

---

## 🔄 User Flows (Reusable from Sport X)

### Flow 1: User Registration & Login

```
1. User visits site → Login/Register page
2. User registers with email/password OR uses magic link
3. JWT token issued → stored in localStorage
4. Redirect to My Competitions dashboard
```

**Files:** `Auth.js`, `server.py` (auth routes)

### Flow 2: Commissioner Creates League

```
1. User clicks "Create Competition"
2. Selects show (e.g., "Survivor 47")
3. Sets budget (⭐100), roster slots (5)
4. League created → redirect to League Detail
5. Commissioner shares invite link
```

**Files:** `CreateLeagueModal.js`, `LeagueDetail.js`

### Flow 3: User Joins League

```
1. User receives invite link
2. Clicks link → opens league join page
3. User authenticates (if not logged in)
4. User joins league → added to participants
5. Redirect to League Detail
```

**Files:** `JoinLeague.js`, `server.py` (join endpoint)

### Flow 4: Auction (100% Reusable)

```
1. Commissioner starts auction
2. All participants enter Waiting Room
3. Auction begins → first contestant displayed
4. Users place bids (real-time via Socket.IO)
5. Timer expires → winner assigned
6. Next contestant → repeat
7. Auction completes → redirect to dashboard
```

**Files:** `AuctionRoom.js`, `WaitingRoom.js`

### Flow 5: Episode Scoring (Pick TV Specific - NEW)

```
1. Episode airs on TV
2. Commissioner opens Episode Results form
3. Marks: who survived, challenges won, eliminations
4. Saves results → points calculated
5. Standings update → users notified
```

**Files:** `EpisodeResultsForm.js` (NEW), `scoring_service.py`

---

## 🎨 UI Components Reference

### Reusable Components

| Component | Location | Usage |
|-----------|----------|-------|
| `Button` | `/components/ui/button.js` | All buttons |
| `Card` | `/components/ui/card.js` | Content containers |
| `Input` | `/components/ui/input.js` | Form inputs |
| `Modal` | `/components/ui/dialog.js` | Dialogs |
| `Toast` | `/components/ui/toast.js` | Notifications |
| `Tabs` | `/components/ui/tabs.js` | Tab navigation |
| `Badge` | `/components/ui/badge.js` | Status indicators |

### Pages to Adapt

| Page | Adaptation Needed |
|------|-------------------|
| `MyCompetitions.js` | Change "clubs" terminology to "contestants" |
| `LeagueDetail.js` | Add episode management, contestant grid |
| `AuctionRoom.js` | Display contestant photo/bio instead of team logo |
| `CompetitionDashboard.js` | Episode timeline instead of fixture list |

---

## 🔌 Socket.IO Events (All Reusable)

### Server → Client

| Event | Purpose | Payload |
|-------|---------|--------|
| `auction_state` | Full auction sync | Auction object |
| `bid_update` | New bid placed | `{currentBid, bidderId, bidderName}` |
| `sold` | Lot completed with winner | `{clubId, winnerId, amount}` |
| `new_lot` | Next lot starting | `{clubId, clubName, timerEndsAt}` |
| `auction_completed` | Auction finished | `{auctionId}` |
| `timer_sync` | Timer synchronization | `{timerEndsAt, remainingMs}` |

### Client → Server

| Event | Purpose | Payload |
|-------|---------|--------|
| `join_auction` | Join auction room | `{auctionId, userId}` |
| `leave_auction` | Leave auction room | `{auctionId}` |

---

## 🧪 Testing Checklist

### Core Flows (Must Pass)

```
□ User can register and login
□ User can create a "Reality TV" league
□ User can share invite link
□ Other users can join via link
□ Commissioner can start auction
□ Bidding works in real-time
□ Timer countdown displays correctly
□ Anti-snipe extends timer
□ Contestants assigned to winners
□ Budget deducted correctly
□ Auction completes successfully
```

### Pick TV Specific (After Implementation)

```
□ Contestant cards display photo/bio
□ Episode results form works
□ Eliminations recorded correctly
□ Points calculated per episode
□ Standings reflect elimination status
□ Eliminated contestants marked visually
□ Winner/finale bonuses applied
```

---

## 📁 File Reference

### Backend Files

| File | Lines | Purpose |
|------|-------|--------|
| `server.py` | ~6,400 | Main application (routes, Socket.IO) |
| `models.py` | ~400 | Pydantic models |
| `scoring_service.py` | ~500 | Scoring logic |
| `socketio_init.py` | ~100 | Socket.IO configuration |

### Frontend Files

| File | Lines | Purpose |
|------|-------|--------|
| `AuctionRoom.js` | ~1,400 | Auction UI |
| `LeagueDetail.js` | ~1,600 | League management |
| `CompetitionDashboard.js` | ~800 | Standings, fixtures |
| `MyCompetitions.js` | ~400 | User dashboard |
| `Auth.js` | ~300 | Login/Register |

---

## 🚀 Implementation Phases

### Phase 1: Core Setup (Week 1)

1. Add `reality_tv` sport to database
2. Extend Asset model for contestants
3. Extend Fixture model for episodes
4. Create sample show data (Survivor 47)
5. Test auction with contestant assets

### Phase 2: Episode Scoring (Week 2)

1. Create EpisodeResult model
2. Implement elimination scoring service
3. Build Episode Results entry UI
4. Test full flow: auction → episode → standings

### Phase 3: UI Polish (Week 3)

1. ContestantCard component
2. EliminationTracker visualization
3. Theme/branding for Pick TV
4. Mobile optimization

### Phase 4: Templates & Launch (Week 4)

1. Create show templates (Survivor, Bake Off, Eurovision)
2. Commissioner documentation
3. User testing
4. Production deployment

---

## ⚠️ Common Pitfalls

### From Sport X Development

| Pitfall | How to Avoid |
|---------|-------------|
| Looking for teams in `clubs` collection | ALL assets are in `assets` collection |
| Assuming fixture status is "completed" | Scoring requires status "ft" |
| Points in `league_participants` | Points are in `league_points` collection |
| Hardcoding URLs | Always use environment variables |
| Missing `_id` exclusion in queries | Add `{"_id": 0}` to all MongoDB queries |

### Pick TV Specific

| Pitfall | How to Avoid |
|---------|-------------|
| Forgetting manual data entry | Build easy-to-use episode entry UI |
| Scoring before episode marked complete | Require status "ft" before scoring |
| Not handling eliminated contestants | Filter active contestants in auction |
| Timezone issues with air dates | Store all dates in UTC |

---

## 📞 Support Resources

### Documentation

- `CORE_AUCTION_ENGINE.md` - Auction mechanics
- `SHARED_CODEBASE.md` - What's shared
- `REALITY_TV_TECHNICAL_SPEC.md` - Full spec
- `SYSTEM_ARCHITECTURE_AUDIT.md` - Database schema

### Code Examples

- Sport X implementation shows all patterns
- Copy/adapt from existing components
- Follow established conventions

### Testing

- Use testing subagent for comprehensive tests
- Manual testing checklist above
- Production health check: `/api/health`

---

## ✅ Ready to Start Checklist

Before writing code:

- [ ] Read all 5 required documents
- [ ] Understand auction engine mechanics
- [ ] Know which components are reusable
- [ ] Know what needs to be built
- [ ] Have sample contestant data ready
- [ ] Understand episode scoring model
- [ ] Know the UI terminology changes

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025  
**Status:** READY FOR NEW PROJECT
