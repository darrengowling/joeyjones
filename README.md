# Fantasy Sports Auction Platform

A real-time, multi-sport fantasy auction platform that enables commissioners to create competitions, conduct live player auctions, and manage ongoing tournaments with automated scoring.

## 🎯 Project Purpose

This platform provides a comprehensive fantasy sports experience for both **Football (Soccer)** and **Cricket** enthusiasts. Users can create private leagues, participate in live auction-style drafts, and compete throughout the season with real-time scoring based on player performance.

### Key Differentiators
- **Live Auction System**: Real-time bidding with Socket.IO for instant updates
- **Multi-Sport Support**: Football (Premier League, La Liga, etc.) and Cricket (Test matches, including The Ashes)
- **Automated Fixture Import**: One-click imports from external sports data APIs
- **Real-time Scoring**: Automatic point updates based on player performance
- **Commissioner Tools**: Full control over competition setup, auctions, and scoring

---

## 🚀 Key Features

### User Management
- JWT-based authentication
- User registration and login
- Role-based access (Commissioners vs Participants)

### Competition Management
- Create multi-sport competitions (Football or Cricket)
- Configure budget caps, squad sizes, and scoring rules
- Manage participants with unique invite tokens
- Dashboard with league tables, fixtures, and player stats

### Live Auction System
- Real-time bidding with WebSocket communication
- Waiting room for pre-auction participant gathering
- Automatic lot progression with configurable timers
- Budget tracking and validation
- Complete audit trail of all bids

### Fixture & Scoring
- **Football**: Import fixtures from Football-Data.org API
- **Cricket**: Import upcoming matches from Cricbuzz API (via RapidAPI)
- Manual score upload via CSV
- Automated point calculation based on sport-specific rules
- Real-time leaderboard updates

### Player Database
- Football: Premier League, La Liga, and other European leagues
- Cricket: International Test squads (Australia, England, New Zealand)
- Player metadata: nationality, role/position, stats

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React Context API
- **Real-time Communication**: Socket.IO Client
- **HTTP Client**: Axios
- **Routing**: React Router v6

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Real-time**: Socket.IO (python-socketio)
- **Authentication**: JWT (PyJWT)
- **Database**: MongoDB (motor async driver)
- **CORS**: FastAPI CORS middleware
- **Async Processing**: Python asyncio

### Database
- **MongoDB**: Document-based storage for users, leagues, auctions, fixtures, and player data

### Third-Party Integrations
- **Football-Data.org**: Football fixtures and live scores
- **Cricbuzz API** (RapidAPI): Cricket match schedules and scores
- **Sentry** (Optional): Error monitoring and performance tracking

---

## 📋 Prerequisites

- **Node.js**: v16+ and Yarn
- **Python**: 3.10+
- **MongoDB**: 4.4+ (running locally or remote)
- **API Keys**: 
  - Football-Data.org API key (for football)
  - RapidAPI key with Cricbuzz access (for cricket)

---

## ⚙️ Environment Setup

### Backend Environment Variables

Create `/app/backend/.env` file:

```bash
# Database Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000"
FRONTEND_ORIGIN="http://localhost:3000"

# Authentication
JWT_SECRET="your-super-secret-jwt-key-change-in-production"
JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production"

# Sport Configuration
SPORTS_CRICKET_ENABLED=true

# Feature Flags
FEATURE_MY_COMPETITIONS=true
FEATURE_ASSET_SELECTION=true
FEATURE_WAITING_ROOM=true

# Third-Party API Keys
API_FOOTBALL_KEY="your-api-football-key-here"
FOOTBALL_DATA_TOKEN="your-football-data-org-token-here"
RAPIDAPI_KEY="your-rapidapi-key-here"
CRICAPI_KEY="multisport-auction"

# Redis (Optional - for production scaling)
REDIS_URL=""
ENABLE_RATE_LIMITING=false

# Monitoring (Optional)
ENABLE_METRICS=true
SENTRY_DSN=""
SENTRY_ENVIRONMENT="development"
SENTRY_TRACES_SAMPLE_RATE=0.1

# Environment
ENV="development"
```

### Frontend Environment Variables

Create `/app/frontend/.env` file:

```bash
# Backend API URL
REACT_APP_BACKEND_URL="http://localhost:8001"

# WebSocket Configuration (for local development)
WDS_SOCKET_PORT=3000

# Feature Flags
REACT_APP_FEATURE_MY_COMPETITIONS=true
REACT_APP_FEATURE_ASSET_SELECTION=true

# Monitoring (Optional)
REACT_APP_SENTRY_DSN=""
REACT_APP_SENTRY_ENVIRONMENT="development"
REACT_APP_SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fantasy-sports-auction.git
cd fantasy-sports-auction
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

The backend will be available at `http://localhost:8001`

### 3. Frontend Setup

```bash
cd frontend

# Install Node dependencies
yarn install

# Start the React development server
yarn start
```

The frontend will be available at `http://localhost:3000`

### 4. Database Setup

Ensure MongoDB is running:

```bash
# If using local MongoDB
mongod --dbpath /path/to/your/data/directory

# Or use MongoDB Compass/Atlas for remote connection
```

The application will automatically create collections on first use.

---

## 📦 Seeding Initial Data

### Football Players (Premier League)

```bash
cd backend
python seed_openfootball_clubs.py
```

### Cricket Players (The Ashes)

```bash
cd backend
python seed_ashes_players.py
```

---

## 🧪 Running Tests

### Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Frontend Tests (Playwright)

```bash
cd tests
yarn install
npx playwright test
```

---

## 📖 API Documentation

Once the backend is running, visit:

- **Interactive Docs**: `http://localhost:8001/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8001/redoc` (ReDoc)

### Key Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

#### Competitions
- `GET /api/leagues` - List all competitions
- `POST /api/leagues` - Create new competition
- `GET /api/leagues/{league_id}` - Get competition details
- `DELETE /api/leagues/{league_id}` - Delete competition (commissioners only)

#### Auctions
- `POST /api/auctions` - Create auction
- `POST /api/auctions/{auction_id}/start` - Start auction
- `POST /api/auctions/{auction_id}/bid` - Place bid

#### Fixtures
- `POST /api/leagues/{league_id}/fixtures/import-football` - Import football fixtures
- `POST /api/leagues/{league_id}/fixtures/import-next-cricket` - Import next cricket fixture
- `GET /api/leagues/{league_id}/fixtures` - Get all fixtures

---

## 🎮 User Workflow

### For Commissioners

1. **Create Account** → Register at `/register`
2. **Create Competition** → Set sport, budget, squad size
3. **Select Players** → Choose player pool from available assets
4. **Invite Participants** → Share unique competition code
5. **Start Auction** → Launch live bidding session
6. **Import Fixtures** → One-click import from sports APIs
7. **Monitor Scoring** → Track real-time points and standings

### For Participants

1. **Create Account** → Register at `/register`
2. **Join Competition** → Enter competition code
3. **Join Auction** → Enter waiting room when ready
4. **Bid on Players** → Compete in live auction
5. **Manage Squad** → View team and standings
6. **Track Performance** → Monitor fixture results

---

## 🔑 Getting API Keys

### Football-Data.org

1. Visit [https://www.football-data.org/](https://www.football-data.org/)
2. Register for a free account
3. Navigate to your dashboard to get your API key
4. Free tier: 10 requests/minute, 12 competitions

### RapidAPI (Cricbuzz)

1. Visit [https://rapidapi.com/](https://rapidapi.com/)
2. Sign up for an account
3. Subscribe to "Cricbuzz Cricket" API
4. Copy your RapidAPI key from the dashboard
5. Free tier: Limited requests per month

---

## 🏗️ Project Structure

```
/app/
├── backend/
│   ├── server.py                    # Main FastAPI application
│   ├── models.py                    # Pydantic models
│   ├── auth.py                      # JWT authentication
│   ├── socketio_init.py             # Socket.IO configuration
│   ├── scoring_service.py           # Scoring logic
│   ├── football_data_client.py      # Football API client
│   ├── rapidapi_client.py           # Cricbuzz API client
│   ├── seed_*.py                    # Data seeding scripts
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Backend environment variables
│
├── frontend/
│   ├── src/
│   │   ├── pages/                   # React page components
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── MyCompetitions.js
│   │   │   ├── CreateLeague.js
│   │   │   ├── LeagueDetail.js
│   │   │   ├── CompetitionDashboard.js
│   │   │   └── AuctionRoom.js
│   │   ├── components/              # Reusable components
│   │   │   └── ui/                  # shadcn/ui components
│   │   ├── App.js                   # Main App component
│   │   └── index.js                 # Entry point
│   ├── package.json                 # Node dependencies
│   └── .env                         # Frontend environment variables
│
├── docs/                            # Additional documentation
├── scripts/                         # Utility scripts
└── tests/                           # Test suites
```

---

## 🐛 Troubleshooting

### Backend won't start
- Check MongoDB is running: `mongosh` or MongoDB Compass
- Verify `.env` file exists in `/app/backend/`
- Check port 8001 is not in use: `lsof -i :8001`

### Frontend won't connect to backend
- Verify `REACT_APP_BACKEND_URL` in frontend `.env` matches backend URL
- Check CORS settings in backend `.env` include frontend origin
- Ensure backend is running and accessible

### Auction not starting
- Verify player data exists in MongoDB `assets` collection
- Check player `createdAt` and `updatedAt` fields are ISO strings, not datetime objects
- Review backend logs for serialization errors

### Fixtures not importing
- Verify API keys are valid and have remaining quota
- Check network connectivity to external APIs
- Review backend logs for API error responses

---

## 📝 Additional Documentation

- **Scoring Rules**: See `/app/ASHES_CRICKET_SCORING_RULES.md` for cricket scoring
- **Architecture**: See `/app/ASHES_FIXTURES_ARCHITECTURE.md` for fixture design
- **Operations**: See `/app/docs/OPERATIONS_PLAYBOOK.md` for production guidance

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Football data powered by [Football-Data.org](https://www.football-data.org/)
- Cricket data powered by [Cricbuzz via RapidAPI](https://rapidapi.com/cricbuzz/api/cricbuzz-cricket)
- UI components from [shadcn/ui](https://ui.shadcn.com/)

---

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ for fantasy sports enthusiasts**
