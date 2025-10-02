# Friends of Pifa

Bid for exclusive ownership of UCL teams and compete with friends!

## About
Friends of Pifa is a real-time auction platform where you can bid on UEFA Champions League clubs, build your dream team, and compete with friends in fantasy leagues with budget management.

## Features
- Create and join leagues with invite tokens
- Real-time bidding with anti-snipe protection
- Budget tracking and enforcement
- 36 UEFA Champions League 2025/26 qualifying clubs
- Live auction room with Socket.IO

## Tech Stack
- **Backend**: FastAPI + Python SocketIO + MongoDB
- **Frontend**: React 19 + Socket.IO Client + Tailwind CSS
- **Database**: MongoDB
- **Real-time**: Socket.IO (WebSocket)

## Quick Start

### Start Services
```bash
sudo supervisorctl restart all
```

### Seed UEFA Clubs
```bash
curl -X POST http://localhost:8001/api/clubs/seed
```

### Access App
Open your browser and navigate to the frontend URL.

## Documentation
- `/app/IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `/app/NEW_FEATURES.md` - Recent features and testing guide
- `/app/TEST_GUIDE.md` - Comprehensive testing guide
