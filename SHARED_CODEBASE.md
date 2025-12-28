# Shared Codebase Architecture: Sport X ↔ Pick TV

**Created:** December 28, 2025  
**Purpose:** Define the shared components, configuration strategy, and deployment separation for running Sport X (fantasy sports) and Pick TV (reality TV) from a single codebase  
**Status:** ACTIVE REFERENCE

---

## Overview

Sport X and Pick TV share the same auction engine, authentication system, and core infrastructure. They differ in:
- Asset types (clubs/players vs contestants)
- Scoring logic (match results vs episode outcomes)
- UI theming and terminology
- Data sources (APIs vs manual entry)

This document defines what is shared, what is configured, and what is separated.

---

## Shared Components (100% Reusable)

| Component | Location | Notes |
|-----------|----------|-------|
| **Auction Engine** | `server.py` (Socket.IO handlers) | See `CORE_AUCTION_ENGINE.md` |
| **Authentication** | `server.py` (`/api/auth/*`) | JWT-based, no changes needed |
| **League Management** | `server.py` (`/api/leagues/*`) | Generic CRUD operations |
| **User Management** | `server.py` (`/api/users/*`) | Profile, preferences |
| **Invite System** | `server.py` (`/api/leagues/*/invite`) | Magic links, tokens |
| **Budget Tracking** | Auction logic | Currency-agnostic |
| **Roster Management** | League/auction logic | Slot-based limits |
| **Socket.IO Infrastructure** | `server.py`, Redis pub/sub | Real-time sync |
| **Database Layer** | MongoDB via Motor | Collection-based separation |

---

## Configured Components (Same Code, Different Config)

### 1. Sport Configuration (`sports` collection)

Each "sport" (including Reality TV) is defined in the database:

```javascript
// Sport X - Football
{
  "sportKey": "football",
  "displayName": "Football",
  "assetTerm": "club",
  "assetTermPlural": "clubs",
  "currency": "£",
  "currencySuffix": "m",
  "defaultBudget": 500,
  "scoringType": "match_results",
  "dataSource": "football-data.org"
}

// Pick TV - Survivor
{
  "sportKey": "survivor",
  "displayName": "Survivor",
  "assetTerm": "contestant",
  "assetTermPlural": "contestants", 
  "currency": "⭐",
  "currencySuffix": "",
  "defaultBudget": 100,
  "scoringType": "elimination",
  "dataSource": "manual"
}
```

### 2. UI Terminology (Frontend)

The frontend reads sport config and adapts labels:

| Context | Sport X | Pick TV |
|---------|---------|---------|
| Asset card title | "Club" | "Contestant" |
| Budget display | "£500m remaining" | "⭐100 remaining" |
| Auction header | "Club Auction" | "Draft" |
| Roster section | "Your Clubs" | "Your Picks" |
| Scoring tab | "Match Results" | "Episode Results" |

**Implementation:** Single component set with conditional rendering based on `sportKey`.

### 3. Scoring Logic (`scoring_service.py`)

Scoring is already sport-aware:

```python
def calculate_scores(league_id: str):
    league = await get_league(league_id)
    sport = await get_sport(league["sportKey"])
    
    if sport["scoringType"] == "match_results":
        return calculate_match_scores(league_id)
    elif sport["scoringType"] == "elimination":
        return calculate_elimination_scores(league_id)
    elif sport["scoringType"] == "points_based":
        return calculate_points_scores(league_id)
```

---

## Separated Components (Pick TV Specific)

### 1. Assets Collection

Sport X uses `clubs` and `assets` collections. Pick TV adds:

```javascript
// contestants collection
{
  "id": "contestant-001",
  "showKey": "survivor-47",
  "name": "Jane Doe",
  "photo": "url",
  "bio": "Marketing manager from Texas",
  "tribe": "Gata",
  "status": "active",  // active, eliminated, winner
  "eliminatedEpisode": null
}
```

### 2. Events/Fixtures

Sport X: `fixtures` collection (matches with scores)
Pick TV: `episodes` collection (episodes with outcomes)

```javascript
// episodes collection
{
  "id": "ep-001",
  "showKey": "survivor-47",
  "episodeNumber": 1,
  "airDate": "2024-09-18",
  "title": "Episode 1",
  "eliminations": ["contestant-003"],
  "immunityWinner": "contestant-007",
  "rewardWinner": null,
  "tribalCouncil": true
}
```

### 3. Scoring Rules

Each show type has specific scoring:

```javascript
// Show scoring config
{
  "showKey": "survivor-47",
  "rules": {
    "survivalPoints": 10,      // Per episode survived
    "immunityWin": 25,
    "rewardWin": 10,
    "fireWin": 50,
    "finalistBonus": 100,
    "winnerBonus": 200,
    "eliminationPenalty": 0    // No penalty, just stop earning
  }
}
```

---

## Deployment Strategy

### Option A: Single Deployment, Route-Based (Recommended for MVP)

```
https://sportx.com/         → Sport X frontend
https://sportx.com/api/     → Shared backend

https://picktv.com/         → Pick TV frontend (separate build)
https://picktv.com/api/     → Same shared backend (proxied)
```

**Pros:** Single backend to maintain, shared database
**Cons:** Downtime affects both products

### Option B: Separate Deployments, Shared Database

```
┌─────────────────┐     ┌─────────────────┐
│   Sport X Pod   │     │   Pick TV Pod   │
│  (Frontend +    │     │  (Frontend +    │
│   Backend)      │     │   Backend)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │   MongoDB   │
              │   (Shared)  │
              └─────────────┘
```

**Pros:** Independent scaling, isolated failures
**Cons:** Code sync required between deployments

### Option C: Fully Separate (Future)

Complete fork with separate databases. Only for when products diverge significantly.

---

## Database Separation

### Shared Collections (Both Products)

| Collection | Purpose |
|------------|---------|
| `users` | User accounts, auth |
| `leagues` | League definitions |
| `auctions` | Auction state |
| `bids` | Bid history |
| `rosters` | User-asset assignments |
| `sports` | Sport/show configurations |

### Sport X Only

| Collection | Purpose |
|------------|---------|
| `clubs` | Football clubs |
| `assets` | Cricket players, AFCON teams |
| `fixtures` | Match schedule and results |
| `standings` | Calculated league standings |

### Pick TV Only

| Collection | Purpose |
|------------|---------|
| `contestants` | Show contestants |
| `episodes` | Episode data and outcomes |
| `shows` | Show metadata |
| `picks_standings` | Pick TV specific standings |

---

## Environment Configuration

### Shared Environment Variables

```bash
# Both products use these
MONGO_URL=mongodb://...
REDIS_URL=redis://...
JWT_SECRET=...
```

### Product-Specific Variables

```bash
# Sport X
FOOTBALL_DATA_API_KEY=...
CRICBUZZ_API_KEY=...
PRODUCT_NAME="Sport X"
DEFAULT_SPORT="football"

# Pick TV  
PRODUCT_NAME="Pick TV"
DEFAULT_SPORT="survivor"
MANUAL_SCORING_ENABLED=true
```

---

## Frontend Theming

### CSS Variables Approach

```css
/* Sport X theme */
:root[data-product="sportx"] {
  --primary-color: #1a365d;
  --accent-color: #38a169;
  --logo-url: url('/sportx-logo.svg');
}

/* Pick TV theme */
:root[data-product="picktv"] {
  --primary-color: #7c3aed;
  --accent-color: #f59e0b;
  --logo-url: url('/picktv-logo.svg');
}
```

### Build-Time Separation

```bash
# Sport X build
REACT_APP_PRODUCT=sportx yarn build

# Pick TV build
REACT_APP_PRODUCT=picktv yarn build
```

---

## Migration Path

### Phase 1: Configuration (Current)
- Add Pick TV sport configs to `sports` collection
- Add show-specific scoring rules
- Test with manual contestant/episode entry

### Phase 2: UI Adaptation
- Add product detection to frontend
- Implement theme switching
- Add Pick TV specific components (contestant cards, episode timeline)

### Phase 3: Separate Builds
- Create Pick TV frontend build config
- Deploy to separate domain
- Share backend via proxy or separate instance

### Phase 4: Optional Fork
- Only if products diverge significantly
- Maintain shared auction engine as npm package

---

## Key Files Reference

| File | Shared/Separate | Notes |
|------|-----------------|-------|
| `server.py` | Shared | Sport-agnostic auction engine |
| `scoring_service.py` | Shared | Switch on `scoringType` |
| `models.py` | Shared | Generic models |
| `AuctionRoom.js` | Shared | Uses sport config for labels |
| `LeagueDetail.js` | Shared | Asset display varies by sport |
| `CompetitionDashboard.js` | Mostly shared | Scoring display varies |
| `ContestantCard.js` | Pick TV only | New component |
| `EpisodeTimeline.js` | Pick TV only | New component |

---

## Testing Strategy

### Shared Tests (Run for Both)
- Authentication flow
- League creation/join
- Auction mechanics
- Bid validation
- Real-time sync

### Product-Specific Tests
- Sport X: Fixture import, match scoring
- Pick TV: Episode entry, elimination scoring

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025
