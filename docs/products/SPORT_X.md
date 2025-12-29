# Sport X - Fantasy Sports Platform

**Last Updated:** December 28, 2025  
**Purpose:** Sport X specific documentation

---

## Overview

Sport X is the original fantasy sports auction platform supporting:
- **Football** - Premier League, Champions League, AFCON
- **Cricket** - Various series

## Supported Competitions

### Football

| Competition | Code | Teams | Source |
|-------------|------|-------|--------|
| Premier League | PL | 20 | Football-Data.org API |
| Champions League | CL | 36 | Football-Data.org API |
| AFCON | AFCON | 24 | CSV import |

### Cricket

| Series | Code | Players | Source |
|--------|------|---------|--------|
| Custom | Various | 30 | CSV import |

## Scoring Rules

### Football

| Event | Points |
|-------|--------|
| Win | 3 |
| Draw | 1 |
| Goal | 1 |

### Cricket

| Event | Points |
|-------|--------|
| Run | 1 |
| Wicket | 20 |
| Catch | 10 |
| Stumping | 25 |
| Run Out | 20 |

## Data Sources

### Football-Data.org

- Free tier: 10 calls/minute
- Provides fixtures and live scores
- Requires `FOOTBALL_DATA_TOKEN`

### CSV Import

- Manual fixture upload
- Manual score entry via UI
- Used for AFCON and cricket

## Key Endpoints

| Purpose | Endpoint |
|---------|----------|
| Import PL/CL fixtures | `POST /api/leagues/{id}/fixtures/import-from-api` |
| Import CSV fixtures | `POST /api/leagues/{id}/fixtures/import-csv` |
| Recompute scores | `POST /api/leagues/{id}/score/recompute` |

---

**Related:** [SHARED_CODEBASE.md](./SHARED_CODEBASE.md), [../features/SCORING_SYSTEM.md](../features/SCORING_SYSTEM.md)
