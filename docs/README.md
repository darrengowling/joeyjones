# Sport X / Pick TV Documentation

**Last Updated:** December 28, 2025  
**Platform:** Fantasy Sports & Entertainment Auction Platform

---

## Quick Start

### For New Developers

1. Read [Architecture Overview](./ARCHITECTURE.md)
2. Review [Database Schema](./DATABASE_SCHEMA.md)
3. Check [API Reference](./API_REFERENCE.md)
4. See [Environment Variables](./ENV_VARIABLES.md)

### For AI Agents

1. **MANDATORY:** Read [Agent Onboarding](./guides/AGENT_ONBOARDING.md)
2. Check [Production Status](./operations/PRODUCTION_STATUS.md)
3. Review [Master TODO List](./MASTER_TODO_LIST.md)

### For Commissioners (Users)

1. [Adding New Competitions](./guides/ADDING_COMPETITIONS.md)
2. [CSV Import Guide](./guides/CSV_IMPORT.md)

---

## Documentation Index

### Core Reference

| Document | Purpose |
|----------|--------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System architecture, data flow |
| [API_REFERENCE.md](./API_REFERENCE.md) | All 61 API endpoints |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | MongoDB collections & schemas |
| [ENV_VARIABLES.md](./ENV_VARIABLES.md) | Environment configuration |
| [MASTER_TODO_LIST.md](./MASTER_TODO_LIST.md) | All tasks, issues, priorities |

### Guides

| Document | Audience |
|----------|----------|
| [guides/AGENT_ONBOARDING.md](./guides/AGENT_ONBOARDING.md) | AI Agents |
| [guides/ADDING_COMPETITIONS.md](./guides/ADDING_COMPETITIONS.md) | Developers |
| [guides/CSV_IMPORT.md](./guides/CSV_IMPORT.md) | Commissioners |
| [guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md) | Everyone |

### Features

| Document | Topic |
|----------|-------|
| [features/AUCTION_ENGINE.md](./features/AUCTION_ENGINE.md) | Core auction mechanics |
| [features/SCORING_SYSTEM.md](./features/SCORING_SYSTEM.md) | Points calculation |
| [features/REALTIME_SYNC.md](./features/REALTIME_SYNC.md) | Socket.IO & Redis |

### Operations

| Document | Topic |
|----------|-------|
| [operations/PRODUCTION_STATUS.md](./operations/PRODUCTION_STATUS.md) | Current production state |
| [operations/MIGRATION_PLAN.md](./operations/MIGRATION_PLAN.md) | Railway migration guide |
| [operations/DEPLOYMENT.md](./operations/DEPLOYMENT.md) | Deployment procedures |

### Products

| Document | Product |
|----------|--------|
| [products/SPORT_X.md](./products/SPORT_X.md) | Sport X (Fantasy Sports) |
| [products/PICK_TV.md](./products/PICK_TV.md) | Pick TV (Reality TV) |
| [products/SHARED_CODEBASE.md](./products/SHARED_CODEBASE.md) | What's shared |

### Archive

Historical documents (fixes, investigations, completed plans) are in [archive/](./archive/).

---

## Key Information

### Production URL

```
https://draft-kings-mobile.emergent.host
```

### Health Check

```bash
curl https://draft-kings-mobile.emergent.host/api/health
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18 + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| Database | MongoDB (Motor async) |
| Real-time | Socket.IO + Redis |
| Auth | JWT tokens |

### Critical Files

| File | Lines | Purpose |
|------|-------|--------|
| `/app/backend/server.py` | ~6,400 | Main backend (needs refactor) |
| `/app/frontend/src/pages/AuctionRoom.js` | ~1,400 | Auction UI |
| `/app/frontend/src/pages/LeagueDetail.js` | ~1,600 | League management |

---

## Recent Updates

| Date | Change |
|------|--------|
| Dec 28, 2025 | Documentation restructured into `/docs/` |
| Dec 28, 2025 | Added API_REFERENCE, DATABASE_SCHEMA, ENV_VARIABLES |
| Dec 28, 2025 | Created Pick TV onboarding prompt |
| Dec 21, 2025 | AFCON data fix, bid UI improvements |

---

**Document Version:** 1.0
