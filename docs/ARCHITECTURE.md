# System Architecture

**Last Updated:** January 16, 2026  
**Purpose:** Consolidated system architecture documentation

---

## Overview

Sport X is a real-time fantasy sports auction platform supporting multiple sports (football, cricket) and entertainment formats (reality TV via Pick TV).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐         ┌─────────────────┐                    │
│  │  React Frontend │◄───────►│  FastAPI Backend │                   │
│  │  (Port 3000)    │  REST   │  (Port 8001)     │                   │
│  └────────┬────────┘         └────────┬─────────┘                   │
│           │                           │                              │
│           │ WebSocket                 │                              │
│           │                           │                              │
│           └──────────┬────────────────┘                              │
│                      │                                               │
│              ┌───────▼───────┐                                       │
│              │   Socket.IO   │                                       │
│              │ (Real-time)   │                                       │
│              └───────┬───────┘                                       │
│                      │                                               │
│         ┌────────────┼────────────┐                                  │
│         │            │            │                                  │
│    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐                            │
│    │ MongoDB │  │  Redis  │  │External │                            │
│    │  (Data) │  │(Pub/Sub)│  │  APIs   │                            │
│    └─────────┘  └─────────┘  └─────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### Frontend (React)

**Location:** `/app/frontend/`

| Aspect | Details |
|--------|--------|
| Framework | React 18 |
| Styling | Tailwind CSS + shadcn/ui |
| State | React hooks (useState, useEffect) |
| HTTP | Axios |
| Real-time | Socket.IO client |
| Port | 3000 |

**Key Pages:**
- `AuctionRoom.js` - Real-time auction UI
- `LeagueDetail.js` - League management
- `CompetitionDashboard.js` - Standings and fixtures
- `MyCompetitions.js` - User dashboard

### Backend (FastAPI)

**Location:** `/app/backend/`

| Aspect | Details |
|--------|--------|
| Framework | FastAPI |
| Python | 3.11 |
| Async | Full async/await |
| ASGI | Uvicorn |
| Port | 8001 |

**Key Files:**
- `server.py` - Main application (~6,400 lines)
- `models.py` - Pydantic models
- `scoring_service.py` - Points calculation
- `socketio_init.py` - Socket.IO setup

### Database (MongoDB)

| Aspect | Details |
|--------|--------|
| Driver | Motor (async) |
| Preview | localhost:27017 |
| Production | Emergent-managed Atlas |

See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for collection details.

### Real-time (Socket.IO + Redis)

| Aspect | Details |
|--------|--------|
| Library | python-socketio |
| Transport | WebSocket |
| Multi-pod | Redis adapter |
| Path | `/api/socket.io` |

---

## Data Flow

### Auction Bid Flow

```
1. User clicks "Place Bid"
   │
   ▼
2. POST /api/auction/{id}/bid
   │
   ▼
3. Backend validates:
   - User authenticated?
   - Bid > current bid?
   - Budget sufficient?
   - Roster not full?
   - Not self-outbid?
   │
   ▼
4. Update auction in MongoDB
   │
   ▼
5. Emit Socket.IO events:
   - bid_placed (to bidder)
   - bid_update (to all)
   │
   ▼
6. Redis pub/sub broadcasts to all pods
   │
   ▼
7. All connected clients update UI
```

### Scoring Flow

```
1. Fixture completes (status = "ft")
   │
   ▼
2. POST /api/leagues/{id}/score/recompute
   │
   ▼
3. Query all "ft" fixtures for league
   │
   ▼
4. Calculate points per asset:
   - Football: wins, draws, goals
   - Cricket: runs, wickets, catches
   │
   ▼
5. Update league_points collection
   │
   ▼
6. Aggregate user totals from owned assets
   │
   ▼
7. Update standings collection
```

---

## API Routes Structure

All routes prefixed with `/api/`:

```
/api/
├── health              # Health check
├── metrics             # Prometheus metrics
├── auth/               # Authentication
│   ├── magic-link
│   ├── verify-magic-link
│   ├── refresh
│   └── me
├── users/              # User management
├── sports/             # Sport configurations
├── assets/             # Teams/players/contestants
├── clubs/              # Football clubs (legacy)
├── leagues/            # League CRUD
│   ├── {id}/join
│   ├── {id}/participants
│   ├── {id}/fixtures/
│   ├── {id}/assets
│   ├── {id}/standings
│   ├── {id}/summary
│   ├── {id}/auction/
│   └── {id}/score/
├── fixtures/           # Fixture management
├── auction/            # Auction operations
│   ├── {id}/bid
│   ├── {id}/pause
│   ├── {id}/resume
│   └── {id}/complete-lot
├── scoring/            # Scoring endpoints
├── admin/              # Admin operations
└── debug/              # Debug endpoints
```

---

## Socket.IO Events

### Server → Client

| Event | Purpose |
|-------|--------|
| `auction_state` | Full auction sync |
| `bid_update` | New bid placed |
| `timer_sync` | Timer synchronization |
| `sold` | Lot completed with winner |
| `new_lot` | Next lot starting |
| `auction_completed` | Auction finished |

### Client → Server

| Event | Purpose |
|-------|--------|
| `join_auction` | Join auction room |
| `leave_auction` | Leave auction room |

---

## External Services

| Service | Purpose | Required |
|---------|---------|----------|
| MongoDB Atlas | Production database | Yes (managed by Emergent) |
| Redis Cloud | Socket.IO pub/sub | Yes (user's account) |
| Football-Data.org | Fixture/score API | For football |
| Cricbuzz/RapidAPI | Cricket data | For cricket |
| Sentry | Error tracking | Optional |

---

## Security

### Authentication

- JWT tokens with 24-hour expiry
- Magic link (passwordless) login
- Token refresh endpoint

### Authorization

- Commissioner: League creator, can manage league
- Participant: Joined league, can bid
- Public: Can view some data

### Data Protection

- Passwords hashed with bcrypt
- JWT secrets in environment variables
- CORS configured per environment

---

## Deployment

### Emergent Platform (Current)

```
Preview:    https://fastbid-platform.preview.emergentagent.com
Production: https://draft-kings-mobile.emergent.host
```

### Railway (Planned Migration)

See [MIGRATION_PLAN.md](./operations/MIGRATION_PLAN.md)

---

## Performance Considerations

### Current Optimizations

1. **Removed extra DB reads on bid** - No loadAuction/loadClubs on bid_placed
2. **Redis pub/sub** - Multi-pod Socket.IO scaling
3. **Async MongoDB** - Motor driver with connection pooling

### Known Bottlenecks

1. **server.py monolith** - 6,400 lines, needs refactor
2. **Diagnostic logging in bid path** - Should be async
3. **Separate bid events** - Could consolidate bid_update + bid_placed

---

## Related Documents

- [API_REFERENCE.md](./API_REFERENCE.md) - Endpoint details
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Collection schemas
- [features/AUCTION_ENGINE.md](./features/AUCTION_ENGINE.md) - Auction mechanics
- [features/REALTIME_SYNC.md](./features/REALTIME_SYNC.md) - Socket.IO details

---

**Document Version:** 1.0
