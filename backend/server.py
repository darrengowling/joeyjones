from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Depends, Request, Response, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import json
from pathlib import Path
from typing import List, Optional
import socketio
import asyncio
import uuid
import csv
import io
from datetime import datetime, timedelta, timezone
import time
from contextlib import asynccontextmanager

# Production hardening imports
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as aioredis
from socketio_init import sio
import metrics
from auction.completion import compute_auction_status
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration

from models import (
    User, UserCreate,
    Club,
    Sport,
    League, LeagueCreate,
    LeagueParticipant, LeagueParticipantCreate,
    Auction, AuctionCreate,
    Bid, BidCreate,
    LeaguePoints,
    Fixture, Standing, StandingEntry,
    MagicLink, AuthTokenResponse
)
from services.sport_service import SportService
from services.asset_service import AssetService
from services.scoring.cricket import get_cricket_points
from uefa_clubs import UEFA_CL_CLUBS
from scoring_service import recompute_league_scores, get_league_standings
from auth import (
    generate_magic_token,
    hash_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_commissioner,
    MAGIC_LINK_EXPIRE_MINUTES,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility function to remove MongoDB _id from documents
def remove_id(doc):
    """Remove _id field from MongoDB document for JSON serialization"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [remove_id(item) for item in doc]
    if isinstance(doc, dict):
        return {k: remove_id(v) for k, v in doc.items() if k != '_id'}
    return doc

# Initialize Sentry for error tracking (Production Hardening Day 6)
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'pilot')
SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1'))

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
            PyMongoIntegration(),
        ],
        # Send additional context
        send_default_pii=False,  # Don't send personally identifiable info
        attach_stacktrace=True,
        # Performance monitoring
        enable_tracing=True,
        # Release tracking (optional - can be set from CI/CD)
        release=os.environ.get('SENTRY_RELEASE', 'unknown'),
    )
    logger.info(f"✅ Sentry error tracking initialized (env: {SENTRY_ENVIRONMENT})")
else:
    logger.info("⚠️  Sentry DSN not configured - error tracking disabled")

# MongoDB connection
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# Global variables for database connection and services
client = None
db = None
sport_service = None
asset_service = None

async def startup_db_client():
    global client, db, sport_service, asset_service
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Create indexes for My Competitions collections - Prompt 1
    try:
        # Fixtures indexes
        await db.fixtures.create_index([("leagueId", 1), ("startsAt", 1)])
        await db.fixtures.create_index([("leagueId", 1), ("status", 1)])
        await db.fixtures.create_index([("leagueId", 1), ("externalMatchId", 1)])
        
        # Standings indexes  
        await db.standings.create_index([("leagueId", 1)], unique=True)
        
        # Bids indexes - CRITICAL for auction performance
        await db.bids.create_index([("auctionId", 1), ("createdAt", -1)])
        await db.bids.create_index([("userId", 1), ("createdAt", -1)])
        await db.bids.create_index([("auctionId", 1), ("amount", -1)])
        
        # League stats indexes - CRITICAL for scoring/leaderboards
        await db.league_stats.create_index([
            ("leagueId", 1), ("matchId", 1), ("playerExternalId", 1)
        ], unique=True)
        await db.league_stats.create_index([("leagueId", 1), ("points", -1)])
        await db.league_stats.create_index([("leagueId", 1), ("playerExternalId", 1)])
        
        # Assets indexes - CRITICAL for multi-sport queries
        await db.assets.create_index("sportKey")
        await db.assets.create_index([("sportKey", 1), ("name", 1)])
        await db.assets.create_index([("sportKey", 1), ("externalId", 1)])
        
        # Clubs indexes - for legacy football data
        await db.clubs.create_index("leagueId")
        await db.clubs.create_index([("leagueId", 1), ("owner", 1)])
        await db.clubs.create_index("uefaId")
        
        # Auctions indexes
        await db.auctions.create_index("leagueId")
        await db.auctions.create_index([("leagueId", 1), ("status", 1)])
        
        # Leagues indexes
        await db.leagues.create_index("sportKey")
        await db.leagues.create_index("commissionerId")
        await db.leagues.create_index("inviteToken", sparse=True)
        
        # Participants indexes
        await db.league_participants.create_index("userId")
        await db.league_participants.create_index([("leagueId", 1), ("joinedAt", 1)])
        
        # Users indexes - CRITICAL for auth
        await db.users.create_index("email", unique=True)
        
        logger.info("✅ Production database indexes created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {e}")
    
    # Initialize services after database connection
    sport_service = SportService(db)
    asset_service = AssetService(db)

# Sports feature flags
SPORTS_CRICKET_ENABLED = os.environ.get('SPORTS_CRICKET_ENABLED', 'false').lower() == 'true'
logger.info(f"Cricket feature enabled: {SPORTS_CRICKET_ENABLED}")

# Prompt 6: Feature flag for My Competitions feature
FEATURE_MY_COMPETITIONS = os.environ.get('FEATURE_MY_COMPETITIONS', 'true').lower() == 'true'
logger.info(f"My Competitions feature enabled: {FEATURE_MY_COMPETITIONS}")

FEATURE_ASSET_SELECTION = os.environ.get('FEATURE_ASSET_SELECTION', 'false').lower() == 'true'
logger.info(f"Asset Selection feature enabled: {FEATURE_ASSET_SELECTION}")

# Prompt G: Feature flag for Waiting Room (Auction Start Control)
FEATURE_WAITING_ROOM = os.environ.get('FEATURE_WAITING_ROOM', 'true').lower() == 'true'
logger.info(f"Waiting Room feature enabled: {FEATURE_WAITING_ROOM}")

# Socket.IO server imported from socketio_init.py (with Redis scaling support)

# Production hardening configuration
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL")

# Rate limiting helper - returns dependency only if rate limiting is enabled and Redis is available
def get_rate_limiter(times: int, seconds: int):
    if ENABLE_RATE_LIMITING and REDIS_URL and REDIS_URL.strip():
        return Depends(RateLimiter(times=times, seconds=seconds))
    else:
        # Return a dummy dependency that does nothing
        async def dummy_limiter():
            pass
        return Depends(dummy_limiter)

# Prompt B: Auth dependency - reads X-User-ID header, returns 401 if missing
def require_user_id(request: Request) -> str:
    """
    Dependency that extracts user ID from X-User-ID header.
    Raises 401 if header is missing.
    """
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required: X-User-ID header missing")
    return user_id

# Lifespan management for rate limiting
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Initialize database connection and indexes
    await startup_db_client()
    
    if ENABLE_RATE_LIMITING and REDIS_URL and REDIS_URL.strip():
        try:
            r = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            await FastAPILimiter.init(r)
            logger.info("✅ Rate limiting initialized with Redis")
        except Exception as e:
            logger.error(f"❌ Rate limiting initialization failed: {e}")
    else:
        logger.info("📝 Rate limiting disabled or Redis not configured")
    
    yield
    
    # Shutdown
    logger.info("🔄 Application shutdown")

# Create the main app with lifespan management
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ===== HEALTH CHECK ENDPOINT (Production Hardening Day 10) =====
@api_router.get("/health")
async def health_check():
    """
    System health check endpoint
    Returns 200 (healthy) or 503 (degraded)
    """
    try:
        # Check database connectivity
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "database": "disconnected",
                "error": str(e)
            }
        )


# ===== SPORTS DATA API ENDPOINTS (Day 13) =====
@api_router.post("/fixtures/update-scores")
async def update_fixture_scores(fixture_ids: List[str] = None):
    """
    Manually trigger fixture score updates from API-FOOTBALL
    If fixture_ids provided, update only those fixtures
    Otherwise, update all EPL fixtures for Nov 29-30, 2025
    """
    from sports_data_client import update_fixtures_from_api
    
    try:
        result = await update_fixtures_from_api(db, fixture_ids)
        return {
            "status": "completed",
            "updated": result["updated"],
            "errors": result.get("errors", []),
            "api_requests_remaining": result.get("requests_remaining", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating fixture scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating scores: {str(e)}")


@api_router.get("/fixtures")
async def get_fixtures(sport_key: str = "football", date: str = None):
    """
    Get all fixtures for a sport, optionally filtered by date
    Date format: YYYY-MM-DD
    """
    try:
        query = {"sportKey": sport_key}
        
        if date:
            query["matchDate"] = {
                "$gte": f"{date}T00:00:00Z",
                "$lte": f"{date}T23:59:59Z"
            }
        
        fixtures = await db.fixtures.find(query, {"_id": 0}).to_list(length=None)
        
        return {
            "fixtures": fixtures,
            "count": len(fixtures)
        }
    except Exception as e:
        logger.error(f"Error fetching fixtures: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching fixtures")


@api_router.get("/fixtures/{fixture_id}")
async def get_fixture_by_id(fixture_id: str):
    """Get detailed information for a specific fixture"""
    try:
        fixture = await db.fixtures.find_one({"id": fixture_id}, {"_id": 0})
        
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")
        
        return fixture
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fixture {fixture_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching fixture")


@api_router.get("/leagues/{league_id}/fixtures")
async def get_league_fixtures(league_id: str):
    """
    Get fixtures for teams that are part of this league
    Shows which matches the league's teams are playing in
    """
    try:
        # Get league details
        league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        sport_key = league.get("sportKey", "football")
        
        # Get teams selected for this league
        selected_asset_ids = league.get("assetsSelected", [])
        
        if not selected_asset_ids:
            # No teams selected yet
            return {
                "fixtures": [],
                "message": "No teams selected for this league yet"
            }
        
        # Get team details from assets collection (post-migration all teams are in assets)
        teams = await db.assets.find({"id": {"$in": selected_asset_ids}}, {"_id": 0}).to_list(length=None)
        team_names = [team["name"] for team in teams]
        
        if not team_names:
            return {
                "fixtures": [],
                "message": "No teams found for this league"
            }
        
        # Get fixtures where any of the league's teams are playing
        fixtures = await db.fixtures.find({
            "sportKey": sport_key,
            "$or": [
                {"homeTeam": {"$in": team_names}},
                {"awayTeam": {"$in": team_names}}
            ]
        }, {"_id": 0}).sort("matchDate", 1).to_list(length=None)
        
        # Add flag to indicate if team is in this league
        for fixture in fixtures:
            fixture["homeTeamInLeague"] = fixture["homeTeam"] in team_names
            fixture["awayTeamInLeague"] = fixture["awayTeam"] in team_names
        
        return {
            "fixtures": fixtures,
            "total": len(fixtures),
            "leagueTeams": team_names
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fixtures for league {league_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching fixtures")

# Add metrics endpoint to API router
@api_router.get("/metrics")
def get_metrics():
    """Prometheus metrics endpoint"""
    if not metrics.ENABLE_METRICS:
        return Response(status_code=404, content="Metrics disabled")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Middleware for API request metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track API request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status = response.status_code
    
    metrics.record_api_request(method, endpoint, status, duration)
    
    return response

# Rate limiting exception handler
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    """Handle rate limiting responses"""
    endpoint = request.url.path
    metrics.increment_rate_limited(endpoint)
    return Response(
        status_code=429,
        content='{"error": "rate_limited", "hint": "Please retry later"}',
        headers={"Content-Type": "application/json"}
    )

# Store active timers and sequence numbers
active_timers = {}
lot_sequences = {}  # Track sequence numbers per lot

def get_next_seq(lot_id: str) -> int:
    """Get next sequence number for a lot"""
    if lot_id not in lot_sequences:
        lot_sequences[lot_id] = 0
    lot_sequences[lot_id] += 1
    return lot_sequences[lot_id]

def create_timer_event(lot_id: str, ends_at_ms: int) -> dict:
    """Create standardized timer event data"""
    import time
    return {
        "lotId": lot_id,
        "seq": get_next_seq(lot_id),
        "endsAt": ends_at_ms,
        "serverNow": int(time.time() * 1000)
    }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== USER ENDPOINTS =====
@api_router.post("/users", response_model=User)
async def create_user(input: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": input.email}, {"_id": 0})
    if existing:
        return User(**existing)
    
    user_obj = User(**input.model_dump())
    await db.users.insert_one(user_obj.model_dump())
    return user_obj

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/auth/magic-link")
async def send_magic_link(email_input: dict, request: Request):
    """
    Generate a secure magic link for authentication
    Note: Rate limiting removed for load testing (Redis not configured)
    
    Flow:
    1. Validate email
    2. Create or find user
    3. Generate secure token with 15-minute expiry
    4. Store hashed token in database
    5. Return token (in pilot mode) or send via email (production)
    """
    email = email_input.get("email", "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    
    # Check if user exists, create if not
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        # Create new user
        user_create = UserCreate(name=email.split("@")[0], email=email)
        user_obj = User(**user_create.model_dump())
        await db.users.insert_one(user_obj.model_dump())
        user = user_obj.model_dump()
        logger.info(f"Created new user: {email}")
    
    # Generate secure magic token
    magic_token = generate_magic_token()
    token_hash = hash_token(magic_token)
    
    # Calculate expiry time
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
    
    # Store magic link in database
    magic_link = MagicLink(
        email=email,
        tokenHash=token_hash,
        expiresAt=expires_at,
        ipAddress=request.client.host if request.client else None
    )
    await db.magic_links.insert_one(magic_link.model_dump())
    
    # Create index for automatic cleanup of expired tokens
    await db.magic_links.create_index("expiresAt", expireAfterSeconds=0)
    
    logger.info(f"Generated magic link for {email}, expires at {expires_at}")
    
    # For pilot: Return token directly
    # In production: Send email with magic link
    return {
        "message": "Magic link generated successfully",
        "email": email,
        "token": magic_token,  # Remove this in production
        "expiresIn": MAGIC_LINK_EXPIRE_MINUTES * 60,  # seconds
        "note": "In production, this token would be sent via email"
    }

@api_router.post("/auth/verify-magic-link", response_model=AuthTokenResponse)
async def verify_magic_link(token_input: dict):
    """
    Verify magic link token and issue JWT tokens
    
    Flow:
    1. Validate token format
    2. Find magic link by hashed token
    3. Check expiration and usage status
    4. Mark token as used (one-time use)
    5. Generate JWT access and refresh tokens
    6. Return tokens and user info
    """
    email = token_input.get("email", "").strip().lower()
    token = token_input.get("token", "").strip()
    
    if not email or not token:
        raise HTTPException(status_code=400, detail="Email and token required")
    
    # Hash the provided token to compare with stored hash
    token_hash = hash_token(token)
    
    # Find the magic link
    magic_link = await db.magic_links.find_one({
        "email": email,
        "tokenHash": token_hash
    }, {"_id": 0})
    
    if not magic_link:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")
    
    # Check if token has expired
    expires_at = magic_link["expiresAt"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Magic link has expired")
    
    # Check if token has already been used (one-time use)
    if magic_link.get("used", False):
        raise HTTPException(status_code=401, detail="Magic link has already been used")
    
    # Mark token as used
    await db.magic_links.update_one(
        {"id": magic_link["id"]},
        {
            "$set": {
                "used": True,
                "usedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    # Find user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"lastLogin": datetime.now(timezone.utc)}}
    )
    
    # Generate JWT tokens
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": "manager"  # Default role
        }
    )
    
    refresh_token = create_refresh_token(user["id"])
    
    logger.info(f"User {email} authenticated successfully via magic link")
    
    return AuthTokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=User(**user)
    )

@api_router.post("/auth/refresh", response_model=AuthTokenResponse)
async def refresh_access_token(refresh_token_input: dict):
    """
    Refresh an access token using a refresh token
    
    Flow:
    1. Validate refresh token
    2. Check token type
    3. Find user
    4. Generate new access token
    5. Return new token
    """
    refresh_token = refresh_token_input.get("refreshToken", "").strip()
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    # Decode and validate refresh token
    try:
        payload = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Find user
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new access token
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": "manager"
        }
    )
    
    logger.info(f"Refreshed access token for user {user['email']}")
    
    return AuthTokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,  # Return same refresh token
        expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=User(**user)
    )

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    Requires valid JWT token
    """
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user)

# ===== SPORT ENDPOINTS =====
@api_router.get("/sports", response_model=List[Sport])
async def get_sports():
    """Get available sports (filter cricket by flag)"""
    return await sport_service.list_sports(enabled_only=True)

@api_router.get("/sports/{sport_key}", response_model=Sport)
async def get_sport(sport_key: str):
    """Get specific sport by key"""
    sport = await sport_service.get_sport(sport_key)
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
    return sport

@api_router.get("/assets")
async def get_assets(sportKey: str, search: Optional[str] = None, page: int = 1, pageSize: int = 50):
    """Get assets for a specific sport with pagination and optional search"""
    if not sportKey:
        raise HTTPException(status_code=400, detail="sportKey parameter is required")
    
    return await asset_service.list_assets(sportKey, search, page, pageSize)

@api_router.get("/leagues/{league_id}/assets")
async def get_league_assets(league_id: str, search: Optional[str] = None, page: int = 1, pageSize: int = 100):
    """Get assets for a specific league based on its sportKey"""
    # Get league to determine sportKey
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")  # Default to football for backward compatibility
    
    # For football, return all clubs (not paginated assets)
    if sport_key == "football":
        clubs = await db.clubs.find({}, {"_id": 0}).to_list(100)
        clubs_as_models = [Club(**club) for club in clubs]
        # Format to match asset_service response structure
        return {
            "assets": [{"id": c.id, "name": c.name, "uefaId": c.uefaId, "country": c.country, "logo": c.logo} for c in clubs_as_models],
            "total": len(clubs_as_models),
            "page": 1,
            "pageSize": len(clubs_as_models)
        }
    
    # For other sports, use asset_service with increased page size
    return await asset_service.list_assets(sport_key, search, page, pageSize)

# ===== CLUB ENDPOINTS =====
@api_router.get("/clubs", response_model=List[Club])
async def get_clubs(competition: str = None):
    """
    Get all football clubs, optionally filtered by competition
    competition: 'EPL', 'UCL', or None for all
    """
    query = {}
    if competition:
        if competition.upper() == "EPL":
            # Include clubs with competitionShort="EPL" OR "English Premier League" in competitions array
            query = {
                "$or": [
                    {"competitionShort": "EPL"},
                    {"competitions": "English Premier League"}
                ]
            }
        elif competition.upper() == "UCL":
            # Include clubs with competitionShort="UCL" OR "UEFA Champions League" in competitions array
            query = {
                "$or": [
                    {"competitionShort": "UCL"},
                    {"competitions": "UEFA Champions League"}
                ]
            }
    
    clubs = await db.clubs.find(query).to_list(100)
    return [Club(**club) for club in clubs]

@api_router.post("/clubs/seed")
async def seed_clubs():
    # Clear existing clubs
    await db.clubs.delete_many({})
    
    # Insert UEFA CL clubs
    clubs = []
    for club_data in UEFA_CL_CLUBS:
        club = Club(**club_data)
        clubs.append(club.model_dump())
    
    if clubs:
        await db.clubs.insert_many(clubs)
    
    return {"message": f"Seeded {len(clubs)} UEFA Champions League clubs"}

# ===== LEAGUE ENDPOINTS =====
@api_router.post("/leagues", response_model=League)
async def create_league(input: LeagueCreate):
    logger.info(f"🏆 CREATE_LEAGUE START: {input.name}")
    
    # Prompt 4: Validate assets selection size
    from models import validate_assets_selection_size
    try:
        validate_assets_selection_size(
            input.assetsSelected,
            input.clubSlots,
            input.minManagers,
            logger
        )
    except ValueError as e:
        logger.error(f"❌ League validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    league_obj = League(**input.model_dump())
    logger.info(f"   League object created: ID={league_obj.id}")
    
    try:
        result = await db.leagues.insert_one(league_obj.model_dump())
        logger.info(f"   ✅ Database insert successful: inserted_id={result.inserted_id}")
    except Exception as e:
        logger.error(f"   ❌ CRITICAL: Database insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create league: {str(e)}")
    
    # Metrics: Track league creation
    metrics.increment_league_created(input.sportKey)
    
    # Prompt 2: Log asset selection persistence
    assets_selected = league_obj.assetsSelected or []
    logger.info("league.assets_selection.persisted", extra={
        "leagueId": league_obj.id,
        "count": len(assets_selected),
        "sportKey": league_obj.sportKey,
        "mode": "selected" if assets_selected else "all"
    })
    
    logger.info(f"✅ CREATE_LEAGUE COMPLETE: {league_obj.name}")
    return league_obj

@api_router.get("/leagues", response_model=List[League])
async def get_leagues(sportKey: Optional[str] = None):
    """Get leagues, optionally filtered by sport"""
    query = {}
    if sportKey:
        query["sportKey"] = sportKey
    
    leagues = await db.leagues.find(query).to_list(100)
    return [League(**league) for league in leagues]

@api_router.get("/leagues/search")
async def search_leagues(name: str = None):
    """Search leagues by name"""
    if not name:
        return []
    
    # Case-insensitive search
    leagues = await db.leagues.find({
        "name": {"$regex": f"^{name}$", "$options": "i"}
    }).to_list(100)
    
    # Return league info without sensitive data
    results = []
    for league in leagues:
        results.append({
            "id": league["id"],
            "name": league["name"],
            "inviteToken": league["inviteToken"],
            "budget": league["budget"],
            "minManagers": league["minManagers"],
            "maxManagers": league["maxManagers"],
            "status": league["status"]
        })
    
    return results

@api_router.get("/leagues/by-token/{invite_token}")
async def get_league_by_token(invite_token: str):
    """Find a league by its invite token (for debugging join issues)"""
    normalized_token = invite_token.strip().lower()
    
    # Search for league with matching token
    league = await db.leagues.find_one({
        "inviteToken": {"$regex": f"^{invite_token}$", "$options": "i"}
    })
    
    if not league:
        # List all leagues to help debug
        all_leagues = await db.leagues.find({}).to_list(100)
        return {
            "found": False,
            "searchedToken": invite_token,
            "normalizedToken": normalized_token,
            "totalLeagues": len(all_leagues),
            "availableTokens": [l.get("inviteToken") for l in all_leagues[:10]]
        }
    
    return {
        "found": True,
        "league": {
            "id": league["id"],
            "name": league["name"],
            "inviteToken": league["inviteToken"],
            "status": league["status"]
        }
    }

@api_router.get("/leagues/{league_id}", response_model=League)
async def get_league(league_id: str):
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return League(**league)

@api_router.post("/leagues/{league_id}/join")
async def join_league(league_id: str, participant_input: LeagueParticipantCreate):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify invite token (trim whitespace and normalize case to handle copy-paste issues)
    input_token = participant_input.inviteToken.strip().lower()
    league_token = league["inviteToken"].strip().lower()
    
    if league_token != input_token:
        # Provide more helpful error message
        error_msg = f"Invalid invite token. The correct token for league '{league['name']}' is '{league_token}'"
        raise HTTPException(status_code=403, detail=error_msg)
    
    # Check if already joined
    existing = await db.league_participants.find_one({
        "leagueId": league_id,
        "userId": participant_input.userId
    }, {"_id": 0})
    if existing:
        return {"message": "Already joined", "participant": LeagueParticipant(**existing)}
    
    # Check max managers limit
    participant_count = await db.league_participants.count_documents({"leagueId": league_id})
    if participant_count >= league["maxManagers"]:
        raise HTTPException(status_code=400, detail="League is full")
    
    # Get user details
    user = await db.users.find_one({"id": participant_input.userId}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create participant
    participant = LeagueParticipant(
        leagueId=league_id,
        userId=participant_input.userId,
        userName=user["name"],
        userEmail=user["email"],
        budgetRemaining=league["budget"],
        totalSpent=0.0,
        clubsWon=[]
    )
    await db.league_participants.insert_one(participant.model_dump())
    
    # Metrics: Track participant joining
    metrics.increment_participant_joined()
    
    # Get current room size
    room_sockets = sio.manager.rooms.get(f"league:{league_id}", set())
    room_size = len(room_sockets)
    
    # JSON log for debugging
    logger.info(json.dumps({
        "event": "member_joined",
        "leagueId": league_id,
        "userId": participant.userId,
        "displayName": participant.userName,
        "countAfter": room_size,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    # Emit member_joined event to league room  
    await sio.emit('member_joined', {
        'userId': participant.userId,
        'displayName': participant.userName,
        'joinedAt': participant.joinedAt.isoformat()
    }, room=f"league:{league_id}")
    
    # Also emit legacy participant_joined for backward compatibility
    await sio.emit('participant_joined', {
        'leagueId': league_id,
        'participant': participant.model_dump(mode='json'),
        'message': f"{participant.userName} joined the league"
    }, room=f"league:{league_id}")
    
    # Send complete member list to ALL users in league room
    all_participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    members = []
    for p in all_participants:
        members.append({
            'userId': p['userId'],
            'displayName': p['userName'],
            'joinedAt': p['joinedAt'].isoformat() if isinstance(p['joinedAt'], datetime) else p['joinedAt']
        })
    
    await sio.emit('sync_members', {
        'leagueId': league_id,
        'members': members
    }, room=f"league:{league_id}")
    
    # Prompt A: Emit participants_changed for waiting room live updates
    await sio.emit('participants_changed', {
        'leagueId': league_id,
        'count': len(all_participants)
    }, room=f"league:{league_id}")
    
    # Prompt A: Also emit to auction room if auction exists and is in waiting state
    auction = await db.auctions.find_one({"leagueId": league_id, "status": "waiting"}, {"_id": 0})
    if auction:
        await sio.emit('participants_changed', {
            'leagueId': league_id,
            'count': len(all_participants)
        }, room=f"auction:{auction['id']}")
        
        logger.info("participants_changed.emitted", extra={
            "leagueId": league_id,
            "auctionId": auction['id'],
            "count": len(all_participants),
            "rooms": [f"league:{league_id}", f"auction:{auction['id']}"]
        })
    
    return {"message": "Joined league successfully", "participant": participant}

@api_router.get("/leagues/{league_id}/participants")
async def get_league_participants(league_id: str):
    """Prompt A: Server-authoritative participants with count - normalized response"""
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    
    # Normalize participant data with safe defaults
    normalized_participants = []
    for p in participants:
        normalized_participants.append({
            "userId": p.get("userId", ""),
            "userName": p.get("userName", p.get("displayName", "Unknown")),
            "userEmail": p.get("userEmail", ""),
            "budgetRemaining": p.get("budgetRemaining", 0),
            "clubsWon": p.get("clubsWon", 0)
        })
    
    # Return count + participants array
    return {
        "count": len(normalized_participants),
        "participants": normalized_participants
    }

@api_router.get("/leagues/{league_id}/members")
async def get_league_members(league_id: str):
    """Prompt A: Get ordered league members for real-time updates"""
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).sort("joinedAt", 1).to_list(100)
    
    # Return simplified member list
    members = []
    for p in participants:
        members.append({
            'userId': p['userId'],
            'displayName': p['userName'],
            'joinedAt': p['joinedAt'].isoformat() if isinstance(p['joinedAt'], datetime) else p['joinedAt']
        })
    
    return members

# ===== MY COMPETITIONS ENDPOINTS - PROMPT 1 =====

@api_router.get("/me/competitions")
async def get_my_competitions(userId: str):
    """Get all competitions for a user - Prompt 6: Feature flag protected"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Find all leagues where user is a participant
    participants = await db.league_participants.find({"userId": userId}, {"_id": 0}).to_list(100)
    league_ids = [p["leagueId"] for p in participants]
    
    if not league_ids:
        return []
    
    # Get league details
    leagues = await db.leagues.find({"id": {"$in": league_ids}}).to_list(100)
    
    competitions = []
    for league in leagues:
        # Determine league status
        auction = await db.auctions.find_one({"leagueId": league["id"]}, {"_id": 0})
        if not auction:
            status = "pre_auction"
        elif auction["status"] == "active":
            status = "auction_live"
        else:
            status = "auction_complete"
        
        # Get user's assets for this league with full details (name, price)
        participant = next((p for p in participants if p["leagueId"] == league["id"]), None)
        asset_ids = participant.get("clubsWon", []) if participant else []
        
        # Enrich with team names and prices from bids
        assets_owned = []
        for asset_id in asset_ids:
            # Get the winning bid for this asset
            winning_bid = await db.bids.find_one({
                "auctionId": auction["id"] if auction else None,
                "clubId": asset_id,
                "userId": userId
            }, sort=[("amount", -1)])
            
            # Get asset details - query correct collection based on sport
            sport_key = league.get("sportKey", "football")
            if sport_key == "football":
                asset = await db.clubs.find_one({"id": asset_id}, {"_id": 0})
            else:
                # For cricket and other sports, use assets collection
                asset = await db.assets.find_one({"id": asset_id}, {"_id": 0})
            
            if asset:
                # Get name from appropriate field based on sport
                if sport_key == "football":
                    asset_name = asset.get("clubName") or asset.get("name", "Unknown Team")
                else:
                    # For cricket, use playerName
                    asset_name = asset.get("playerName") or asset.get("name", "Unknown Player")
                
                assets_owned.append({
                    "id": asset_id,
                    "name": asset_name,
                    "price": winning_bid["amount"] if winning_bid else 0
                })
            else:
                # Fallback if asset not found
                fallback_name = "Team" if sport_key == "football" else "Player"
                assets_owned.append({
                    "id": asset_id,
                    "name": fallback_name,
                    "price": winning_bid["amount"] if winning_bid else 0
                })
        
        # Get manager count
        manager_count = await db.league_participants.count_documents({"leagueId": league["id"]})
        
        # Get next fixture
        next_fixture = await db.fixtures.find_one({
            "leagueId": league["id"],
            "startsAt": {"$gte": datetime.now(timezone.utc)},
            "status": "scheduled"
        }, {"_id": 0}, sort=[("startsAt", 1)])
        
        next_fixture_at = next_fixture["startsAt"] if next_fixture else None
        
        # Serialize DateTime objects to ISO strings
        starts_at = league.get("startsAt")
        starts_at_iso = starts_at.isoformat() if starts_at and isinstance(starts_at, datetime) else starts_at
        
        competitions.append({
            "leagueId": league["id"],
            "name": league["name"],
            "sportKey": league["sportKey"],
            "status": status,
            "assetsOwned": assets_owned,
            "managersCount": manager_count,
            "timerSeconds": league.get("timerSeconds", 30),
            "antiSnipeSeconds": league.get("antiSnipeSeconds", 10),
            "startsAt": starts_at_iso,
            "nextFixtureAt": next_fixture_at.isoformat() if next_fixture_at else None
        })
    
    return competitions

@api_router.get("/leagues/{league_id}/summary")
async def get_league_summary(league_id: str, userId: str):
    """Get detailed league summary - Prompt 6: Feature flag protected"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get commissioner details
    commissioner = await db.users.find_one({"id": league["commissionerId"]}, {"_id": 0})
    
    # Get user's roster with enriched details (name and price)
    participant = await db.league_participants.find_one({"leagueId": league_id, "userId": userId}, {"_id": 0})
    asset_ids = participant.get("clubsWon", []) if participant else []
    
    # Enrich roster with asset names and prices
    user_roster = []
    auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    
    for asset_id in asset_ids:
        # Get the winning bid for this asset
        winning_bid = await db.bids.find_one({
            "auctionId": auction["id"] if auction else None,
            "clubId": asset_id,
            "userId": userId
        }, sort=[("amount", -1)])
        
        # Get asset details
        sport_key = league.get("sportKey", "football")
        if sport_key == "football":
            asset = await db.clubs.find_one({"id": asset_id}, {"_id": 0})
        else:
            asset = await db.assets.find_one({"id": asset_id, "sportKey": sport_key}, {"_id": 0})
        
        if asset:
            user_roster.append({
                "id": asset_id,
                "name": asset.get("clubName") or asset.get("name", "Unknown Team"),
                "price": winning_bid["amount"] if winning_bid else 0
            })
        else:
            # Fallback if asset not found
            user_roster.append({
                "id": asset_id,
                "name": "Team",
                "price": winning_bid["amount"] if winning_bid else 0
            })
    
    user_budget_remaining = participant.get("budgetRemaining", 0) if participant else 0
    
    # Get all managers with their rosters (Everton Bug Fix 5: Roster Visibility)
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    managers = []
    
    for p in participants:
        # Get manager's roster with enriched details
        manager_asset_ids = p.get("clubsWon", [])
        manager_roster = []
        
        for asset_id in manager_asset_ids:
            # Get the winning bid for this asset by this manager
            winning_bid = await db.bids.find_one({
                "auctionId": auction["id"] if auction else None,
                "clubId": asset_id,
                "userId": p["userId"]
            }, sort=[("amount", -1)])
            
            # Get asset details
            sport_key = league.get("sportKey", "football")
            if sport_key == "football":
                asset = await db.clubs.find_one({"id": asset_id}, {"_id": 0})
            else:
                asset = await db.assets.find_one({"id": asset_id, "sportKey": sport_key}, {"_id": 0})
            
            if asset:
                manager_roster.append({
                    "id": asset_id,
                    "name": asset.get("clubName") or asset.get("name", "Unknown Team"),
                    "price": winning_bid["amount"] if winning_bid else 0
                })
            else:
                # Fallback if asset not found
                manager_roster.append({
                    "id": asset_id,
                    "name": "Team",
                    "price": winning_bid["amount"] if winning_bid else 0
                })
        
        managers.append({
            "id": p["userId"],
            "name": p["userName"],
            "roster": manager_roster,
            "budgetRemaining": p.get("budgetRemaining", 0)
        })
    
    # Determine status
    if not auction:
        status = "pre_auction"
    elif auction["status"] == "active":
        status = "auction_live"  
    else:
        status = "auction_complete"
    
    return {
        "leagueId": league_id,
        "name": league["name"],
        "sportKey": league["sportKey"],
        "status": status,
        "commissioner": {
            "id": league["commissionerId"],
            "name": commissioner["name"] if commissioner else "Unknown"
        },
        "yourRoster": user_roster,  # Now enriched with name and price
        "yourBudgetRemaining": user_budget_remaining,
        "managers": managers,  # Now includes roster and budget for each manager
        "totalBudget": league["budget"],
        "clubSlots": league["clubSlots"],
        "timerSeconds": league.get("timerSeconds", 30),
        "antiSnipeSeconds": league.get("antiSnipeSeconds", 10)
    }

@api_router.get("/leagues/{league_id}/standings")
async def get_league_standings(league_id: str):
    """Get current league standings - Prompt 6: Feature flag protected"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Get league
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Always get current participants to ensure standings reflect all members
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    
    # Check if standings exist
    standing = await db.standings.find_one({"leagueId": league_id}, {"_id": 0})
    
    if not standing:
        # Create zeroed standings with ALL current participants
        table = []
        for participant in participants:
            table.append({
                "userId": participant["userId"],
                "displayName": participant["userName"],
                "points": 0.0,
                "assetsOwned": participant.get("clubsWon", []),
                "tiebreakers": {"goals": 0, "wins": 0, "runs": 0, "wickets": 0}
            })
        
        # Sort by displayName for initial order
        table.sort(key=lambda x: x["displayName"])
        
        standing_obj = Standing(
            leagueId=league_id,
            sportKey=league["sportKey"],
            table=table
        )
        
        await db.standings.insert_one(standing_obj.model_dump())
        
        return standing_obj.model_dump(mode='json')
    
    # Standing exists - ensure it includes ALL current participants
    existing_table = standing.get("table", [])
    existing_user_ids = {entry["userId"] for entry in existing_table}
    
    # Find participants not in standings
    missing_participants = [p for p in participants if p["userId"] not in existing_user_ids]
    
    if missing_participants:
        # Add missing participants with 0 points
        for participant in missing_participants:
            existing_table.append({
                "userId": participant["userId"],
                "displayName": participant["userName"],
                "points": 0.0,
                "assetsOwned": participant.get("clubsWon", []),
                "tiebreakers": {"goals": 0, "wins": 0, "runs": 0, "wickets": 0}
            })
        
        # Update standings in database
        await db.standings.update_one(
            {"leagueId": league_id},
            {"$set": {"table": existing_table}}
        )
        
        standing["table"] = existing_table
    
    # Update assetsOwned for all participants to reflect current state
    for entry in standing["table"]:
        participant = next((p for p in participants if p["userId"] == entry["userId"]), None)
        if participant:
            entry["assetsOwned"] = participant.get("clubsWon", [])
    
    # Re-sort by points (descending), then by displayName
    standing["table"].sort(key=lambda x: (-x["points"], x["displayName"]))
    
    return Standing(**standing).model_dump(mode='json')

@api_router.get("/leagues/{league_id}/match-breakdown")
async def get_match_breakdown(league_id: str):
    """Get match-by-match scoring breakdown for all managers"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")
    
    # Get all fixtures for this league (completed only, ordered by date)
    fixtures = await db.fixtures.find({
        "leagueId": league_id,
        "status": "completed"
    }, {"_id": 0}).sort("startsAt", 1).to_list(100)
    
    # Get all participants
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    
    # Get league stats (contains per-player/team per-match scoring)
    league_stats = await db.league_stats.find({"leagueId": league_id}, {"_id": 0}).to_list(1000)
    
    # Build match names from fixtures
    match_names = []
    fixture_external_ids = []
    for idx, fixture in enumerate(fixtures):
        # Create match name from fixture data
        if fixture.get("homeAssetId") and fixture.get("awayAssetId"):
            # Get asset names for match label
            if sport_key == "football":
                home = await db.clubs.find_one({"id": fixture["homeAssetId"]}, {"_id": 0})
                away = await db.clubs.find_one({"id": fixture["awayAssetId"]}, {"_id": 0})
            else:
                home = await db.assets.find_one({"id": fixture["homeAssetId"]}, {"_id": 0})
                away = await db.assets.find_one({"id": fixture["awayAssetId"]}, {"_id": 0})
            
            home_name = home.get("name", "Team") if home else "Team"
            away_name = away.get("name", "Team") if away else "Team"
            match_name = f"Match {idx + 1}: {home_name[:10]} vs {away_name[:10]}"
        else:
            # International or generic fixture
            match_name = f"Match {idx + 1}"
        
        match_names.append(match_name)
        fixture_external_ids.append(fixture.get("externalMatchId", f"match-{idx+1}"))
    
    # Build manager breakdown
    managers = []
    for participant in participants:
        user_id = participant["userId"]
        user_name = participant.get("userName", participant.get("displayName", "Unknown"))
        asset_ids = participant.get("clubsWon", [])
        
        # Get assets owned by this manager
        assets = []
        match_totals = {}
        
        for asset_id in asset_ids:
            # Get asset name
            if sport_key == "football":
                asset = await db.clubs.find_one({"id": asset_id}, {"_id": 0})
                asset_name = asset.get("clubName") or asset.get("name", "Unknown") if asset else "Unknown"
            else:
                asset = await db.assets.find_one({"id": asset_id}, {"_id": 0})
                asset_name = asset.get("playerName") or asset.get("name", "Unknown") if asset else "Unknown"
            
            # Get scores for this asset across all matches
            match_scores = {}
            for idx, ext_match_id in enumerate(fixture_external_ids):
                # Find stat entry for this asset in this match
                stat = next((s for s in league_stats 
                           if s.get("playerExternalId") == asset.get("externalId") 
                           and s.get("matchId") == ext_match_id), None)
                
                # Use 'points' field (not 'fantasyPoints')
                score = stat.get("points", 0) if stat else 0
                match_scores[f"match_{idx}"] = score
                
                # Add to manager's total for this match
                if f"match_{idx}" not in match_totals:
                    match_totals[f"match_{idx}"] = 0
                match_totals[f"match_{idx}"] += score
            
            assets.append({
                "assetId": asset_id,
                "assetName": asset_name,
                "matchScores": match_scores
            })
        
        # Calculate overall total
        overall_total = sum(match_totals.values())
        
        managers.append({
            "userId": user_id,
            "userName": user_name,
            "assets": assets,
            "matchTotals": match_totals,
            "overallTotal": overall_total
        })
    
    # Sort managers by overall total (descending)
    managers.sort(key=lambda m: m["overallTotal"], reverse=True)
    
    return {
        "managers": managers,
        "matchNames": match_names,
        "fixtureCount": len(fixtures)
    }

@api_router.post("/leagues/{league_id}/fixtures/import-csv")
async def import_fixtures_csv(league_id: str, file: UploadFile = File(...), commissionerId: str = None):
    """Import fixtures from CSV - Commissioner only - Prompt 6"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Verify league exists and get commissioner
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Prompt 6: Permissions - lock CSV import to commissioner; return 403 otherwise
    if not commissionerId or league["commissionerId"] != commissionerId:
        raise HTTPException(
            status_code=403, 
            detail="Only the league commissioner can import fixtures"
        )
    
    # Prompt 6: Validation - refuse import when auction is not auction_complete
    auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    if auction and auction["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot import fixtures while auction is in progress. Please complete the auction first."
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        import csv
        import io
        
        reader = csv.DictReader(io.StringIO(csv_content))
        fixtures_imported = 0
        
        sport_key = league["sportKey"]
        
        for row in reader:
            # Parse row data
            starts_at_str = row.get('startsAt', '').strip()
            home_external_id = row.get('homeAssetExternalId', '').strip()
            away_external_id = row.get('awayAssetExternalId', '').strip()
            venue = row.get('venue', '').strip() or None
            round_val = row.get('round', '').strip() or None
            external_match_id = row.get('externalMatchId', '').strip() or None
            
            if not starts_at_str:
                continue  # Skip rows without start time
            
            # Parse datetime
            try:
                starts_at = datetime.fromisoformat(starts_at_str.replace('Z', '+00:00'))
            except ValueError:
                continue  # Skip invalid dates
            
            # For international matches (no home/away specified), create fixture with nulls
            if not home_external_id and not away_external_id:
                fixture = Fixture(
                    leagueId=league_id,
                    sportKey=sport_key,
                    externalMatchId=external_match_id,
                    homeAssetId=None,
                    awayAssetId=None,
                    startsAt=starts_at,
                    venue=venue,
                    round=round_val,
                    status="scheduled",
                    source="csv"
                )
                
                # Upsert fixture by external match ID or time
                if external_match_id:
                    await db.fixtures.update_one(
                        {"leagueId": league_id, "externalMatchId": external_match_id},
                        {"$set": fixture.model_dump()},
                        upsert=True
                    )
                else:
                    await db.fixtures.update_one(
                        {"leagueId": league_id, "startsAt": starts_at},
                        {"$set": fixture.model_dump()},
                        upsert=True
                    )
                
                fixtures_imported += 1
                continue
            
            # Look up asset IDs
            if sport_key == "football":
                home_asset = await db.clubs.find_one({"uefaId": home_external_id}, {"_id": 0})
                away_asset = await db.clubs.find_one({"uefaId": away_external_id}, {"_id": 0}) if away_external_id else None
            else:
                # For cricket, look up by externalId or name
                home_asset = await db.assets.find_one({
                    "sportKey": sport_key,
                    "$or": [
                        {"externalId": home_external_id},
                        {"name": home_external_id}
                    ]
                })
                away_asset = await db.assets.find_one({
                    "sportKey": sport_key,
                    "$or": [
                        {"externalId": away_external_id},
                        {"name": away_external_id}
                    ]
                }) if away_external_id else None
            
            if not home_asset:
                logger.warning(f"Home asset not found: {home_external_id}")
                continue
                
            home_asset_id = home_asset["id"]
            away_asset_id = away_asset["id"] if away_asset else None
            
            # Create fixture
            fixture = Fixture(
                leagueId=league_id,
                sportKey=sport_key,
                externalMatchId=external_match_id,
                homeAssetId=home_asset_id,
                awayAssetId=away_asset_id,
                startsAt=starts_at,
                venue=venue,
                round=round_val,
                status="scheduled",
                source="csv"
            )
            
            # Upsert fixture
            if external_match_id:
                # Update by external match ID
                await db.fixtures.update_one(
                    {"leagueId": league_id, "externalMatchId": external_match_id},
                    {"$set": fixture.model_dump()},
                    upsert=True
                )
            else:
                # Update by home/away/time combination
                await db.fixtures.update_one(
                    {
                        "leagueId": league_id,
                        "homeAssetId": home_asset_id,
                        "awayAssetId": away_asset_id,
                        "startsAt": starts_at
                    },
                    {"$set": fixture.model_dump()},
                    upsert=True
                )
            
            fixtures_imported += 1
        
        # Prompt 4: Emit fixtures_updated event to league room
        await sio.emit('fixtures_updated', {
            'leagueId': league_id,
            'countChanged': fixtures_imported
        }, room=f"league:{league_id}")
        
        return {
            "message": f"Successfully imported {fixtures_imported} fixtures",
            "fixturesImported": fixtures_imported
        }
        
    except Exception as e:
        logger.error(f"Error importing fixtures: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@api_router.delete("/leagues/{league_id}/fixtures/clear")
async def clear_all_fixtures(league_id: str, commissionerId: str = Query(...)):
    """Delete all fixtures from a league - Commissioner only"""
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Verify league exists and commissioner
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if league["commissionerId"] != commissionerId:
        raise HTTPException(status_code=403, detail="Only the league commissioner can delete fixtures")
    
    # Delete all fixtures
    result = await db.fixtures.delete_many({"leagueId": league_id})
    
    # Emit update event
    await sio.emit('fixtures_updated', {
        'leagueId': league_id,
        'countChanged': -result.deleted_count
    }, room=f"league:{league_id}")
    
    return {
        "message": f"Successfully deleted {result.deleted_count} fixtures",
        "fixturesDeleted": result.deleted_count
    }

@api_router.put("/leagues/{league_id}/assets")
async def update_league_assets(league_id: str, asset_ids: List[str]):
    """Prompt 1: Update selected assets for league (commissioner only)"""
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if auction has started (block edits after start)
    existing_auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    if existing_auction:
        raise HTTPException(status_code=400, detail="Cannot edit teams after auction has started")
    
    # Validate and clean the asset IDs using helper
    from models import validate_assets_selected
    try:
        cleaned_asset_ids = validate_assets_selected(asset_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # If cleaned list is None or empty, reject (must select at least one)
    if not cleaned_asset_ids:
        raise HTTPException(status_code=400, detail="Must select at least one team for the auction")
    
    # Prompt 4: Validate assets selection size
    from models import validate_assets_selection_size
    try:
        validate_assets_selection_size(
            cleaned_asset_ids,
            league.get("clubSlots", 3),
            league.get("minManagers", 2),
            logger
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate that all asset IDs exist for this sport
    sport_key = league.get("sportKey", "football")
    if sport_key == "football":
        # Validate club IDs
        valid_assets = await db.clubs.find({"id": {"$in": cleaned_asset_ids}}).to_list(len(cleaned_asset_ids))
    else:
        # Validate other sport assets
        valid_assets = await db.assets.find({
            "id": {"$in": cleaned_asset_ids},
            "sportKey": sport_key
        }).to_list(len(cleaned_asset_ids))
    
    if len(valid_assets) != len(cleaned_asset_ids):
        raise HTTPException(status_code=400, detail="Some asset IDs are invalid for this sport")
    
    # Update league with selected assets
    await db.leagues.update_one(
        {"id": league_id},
        {"$set": {"assetsSelected": cleaned_asset_ids}}
    )
    
    # Prompt 2: Log asset selection update
    logger.info("league.assets_selection.updated", extra={
        "leagueId": league_id,
        "count": len(cleaned_asset_ids),
        "sportKey": sport_key,
        "mode": "selected"
    })
    
    return {"message": f"Updated league with {len(cleaned_asset_ids)} selected teams", "count": len(cleaned_asset_ids)}

@api_router.get("/leagues/{league_id}/available-assets")
async def get_available_assets_for_league(league_id: str):
    """Prompt E: Get all available assets that can be selected for a league"""
    # Get league to determine sport
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")
    
    if sport_key == "football":
        # Get all clubs
        assets = await db.clubs.find({}, {"_id": 0}).to_list(100)
        return [{"id": asset["id"], "name": asset["name"], "country": asset.get("country")} for asset in assets]
    else:
        # Get assets for other sports
        assets = await db.assets.find({"sportKey": sport_key}, {"_id": 0}).to_list(100)
        return [{"id": asset["id"], "name": asset["name"], "meta": asset.get("meta")} for asset in assets]

@api_router.delete("/leagues/{league_id}")
async def delete_league(league_id: str, commissioner_id: str = None, user_id: str = None):
    """Delete a league and all associated data - only commissioner can do this"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Accept either commissioner_id or user_id parameter
    requesting_user_id = commissioner_id or user_id
    
    # Verify commissioner permissions
    if requesting_user_id and league["commissionerId"] != requesting_user_id:
        raise HTTPException(status_code=403, detail="Only the commissioner can delete this league")
    
    # Check if auction is active
    existing_auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    if existing_auction and existing_auction["status"] == "active":
        raise HTTPException(status_code=400, detail="Cannot delete league with active auction. Pause or complete the auction first.")
    
    # Cascade delete all related data
    delete_results = {}
    
    # Delete bids
    bid_result = await db.bids.delete_many({"auctionId": {"$in": [existing_auction["id"]] if existing_auction else []}})
    delete_results["bids"] = bid_result.deleted_count
    
    # Delete auction
    if existing_auction:
        auction_result = await db.auctions.delete_one({"leagueId": league_id})
        delete_results["auction"] = auction_result.deleted_count
        
        # Cancel any active timers
        if existing_auction["id"] in active_timers:
            active_timers[existing_auction["id"]].cancel()
            del active_timers[existing_auction["id"]]
    
    # Delete league participants
    participant_result = await db.league_participants.delete_many({"leagueId": league_id})
    delete_results["participants"] = participant_result.deleted_count
    
    # Delete league points
    points_result = await db.league_points.delete_many({"leagueId": league_id})
    delete_results["points"] = points_result.deleted_count
    
    # Delete the league itself
    league_result = await db.leagues.delete_one({"id": league_id})
    delete_results["league"] = league_result.deleted_count
    
    logger.info(f"Deleted league {league_id}: {delete_results}")
    
    return {
        "message": "League deleted successfully",
        "deletedData": delete_results
    }

@api_router.put("/leagues/{league_id}/scoring-overrides")
async def update_league_scoring_overrides(league_id: str, request: dict):
    """Update scoring overrides for a cricket league (commissioner only)"""
    
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify this is a cricket league
    if league.get("sportKey", "football") != "cricket":
        raise HTTPException(status_code=400, detail="Scoring overrides are only supported for cricket leagues")
    
    # TODO: Add commissioner authorization check when auth is implemented
    
    # Get scoring overrides from request
    scoring_overrides = request.get("scoringOverrides")
    
    # Validate scoring overrides structure if provided
    if scoring_overrides:
        # Basic validation
        if "rules" not in scoring_overrides:
            raise HTTPException(status_code=400, detail="Scoring overrides must include 'rules' section")
        
        rules = scoring_overrides["rules"]
        required_rules = ["run", "wicket", "catch", "stumping", "runOut"]
        
        for rule in required_rules:
            if rule not in rules or not isinstance(rules[rule], (int, float)):
                raise HTTPException(status_code=400, detail=f"Invalid or missing rule: {rule}")
        
        # Validate milestones if provided
        if "milestones" in scoring_overrides:
            milestones = scoring_overrides["milestones"]
            for milestone_name, milestone_data in milestones.items():
                if not isinstance(milestone_data, dict):
                    continue
                if "enabled" in milestone_data:
                    if not isinstance(milestone_data["enabled"], bool):
                        raise HTTPException(status_code=400, detail=f"Milestone {milestone_name} 'enabled' must be boolean")
                if "points" in milestone_data:
                    if not isinstance(milestone_data["points"], (int, float)):
                        raise HTTPException(status_code=400, detail=f"Milestone {milestone_name} 'points' must be numeric")
                if "threshold" in milestone_data:
                    if not isinstance(milestone_data["threshold"], (int, float)):
                        raise HTTPException(status_code=400, detail=f"Milestone {milestone_name} 'threshold' must be numeric")
                
                # Ensure all milestones have required threshold values
                if milestone_data.get("enabled"):
                    if "threshold" not in milestone_data:
                        # Set default thresholds if not provided
                        default_thresholds = {
                            "halfCentury": 50,
                            "century": 100,
                            "fiveWicketHaul": 5
                        }
                        milestone_data["threshold"] = default_thresholds.get(milestone_name, 1)
    
    # Update the league
    update_data = {
        "scoringOverrides": scoring_overrides,
        "updatedAt": datetime.now(timezone.utc)
    }
    
    result = await db.leagues.update_one(
        {"id": league_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update scoring overrides")
    
    # Return updated league
    updated_league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    return League(**updated_league)

# ===== SCORING ENDPOINTS =====
@api_router.post("/leagues/{league_id}/score/recompute")
async def recompute_scores(league_id: str):
    """
    Recompute scores for all clubs in a league based on Champions League results
    Fetches data from OpenFootball and applies scoring rules:
    - Win: 3 points
    - Draw: 1 point
    - Goal scored: 1 point
    """
    try:
        result = await recompute_league_scores(db, league_id)
        return result
    except Exception as e:
        logger.error(f"Error recomputing scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leagues/{league_id}/standings")
async def get_standings(league_id: str):
    """
    Get current standings for a league, sorted by total points
    """
    try:
        standings = await get_league_standings(db, league_id)
        return [LeaguePoints(**s) for s in standings]
    except Exception as e:
        logger.error(f"Error getting standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scoring/{league_id}/ingest")
async def ingest_cricket_scoring(league_id: str, file: UploadFile = File(...)):
    """
    Ingest cricket scoring data from CSV file (commissioner only)
    
    CSV columns: matchId, playerExternalId, runs, wickets, catches, stumpings, runOuts
    """
    # Verify league exists and get league data
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # TODO: Add commissioner authorization check here when auth is implemented
    # For now, we'll proceed without auth check
    
    # Verify this is a cricket league
    if league.get("sportKey", "football") != "cricket":
        raise HTTPException(status_code=400, detail="Scoring ingest is only supported for cricket leagues")
    
    # Determine scoring schema - use league overrides or sport default
    scoring_schema = league.get("scoringOverrides")
    if not scoring_schema:
        # Get default schema from sport
        sport = await db.sports.find_one({"key": "cricket"}, {"_id": 0})
        if not sport:
            raise HTTPException(status_code=500, detail="Cricket sport configuration not found")
        scoring_schema = sport.get("scoringSchema")
    
    if not scoring_schema:
        raise HTTPException(status_code=500, detail="No scoring schema available")
    
    # Parse CSV file
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Validate CSV headers
        expected_columns = {"matchId", "playerExternalId", "runs", "wickets", "catches", "stumpings", "runOuts"}
        actual_columns = set(csv_reader.fieldnames or [])
        missing_columns = expected_columns - actual_columns
        
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing required CSV columns: {missing_columns}")
        
        # Process each row
        processed_rows = 0
        updated_rows = 0
        leaderboard_updates = {}  # Track points by playerExternalId for leaderboard
        match_ids_processed = set()  # Track which matches were uploaded
        
        for row in csv_reader:
            try:
                match_id = row["matchId"].strip()
                player_external_id = row["playerExternalId"].strip()
                
                if not match_id or not player_external_id:
                    logger.warning(f"Skipping row with empty matchId or playerExternalId: {row}")
                    continue
                
                # Track this match ID
                match_ids_processed.add(match_id)
                
                # Prepare performance data for points calculation
                performance_data = {
                    "runs": int(row.get("runs", 0)),
                    "wickets": int(row.get("wickets", 0)),
                    "catches": int(row.get("catches", 0)),
                    "stumpings": int(row.get("stumpings", 0)),
                    "runOuts": int(row.get("runOuts", 0))
                }
                
                # Calculate points using the cricket scoring function
                points = get_cricket_points(performance_data, scoring_schema)
                
                # Prepare document for upsert
                stat_document = {
                    "leagueId": league_id,
                    "matchId": match_id,
                    "playerExternalId": player_external_id,
                    "points": points,
                    "performance": performance_data,
                    "updatedAt": datetime.now(timezone.utc)
                }
                
                # Upsert into league_stats
                result = await db.league_stats.update_one(
                    {
                        "leagueId": league_id,
                        "matchId": match_id,
                        "playerExternalId": player_external_id
                    },
                    {"$set": stat_document},
                    upsert=True
                )
                
                processed_rows += 1
                if result.upserted_id or result.modified_count > 0:
                    updated_rows += 1
                
                # Track for leaderboard update
                if player_external_id not in leaderboard_updates:
                    leaderboard_updates[player_external_id] = 0
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing CSV row {processed_rows + 1}: {str(e)}")
                continue
        
        # Update leaderboard projection - recalculate total points per player
        leaderboard_results = []
        for player_external_id in leaderboard_updates:
            # Calculate total points and stats for this player across all matches
            pipeline = [
                {"$match": {"leagueId": league_id, "playerExternalId": player_external_id}},
                {"$group": {
                    "_id": None, 
                    "totalPoints": {"$sum": "$points"},
                    "totalRuns": {"$sum": "$performance.runs"},
                    "totalWickets": {"$sum": "$performance.wickets"},
                    "totalCatches": {"$sum": "$performance.catches"},
                    "totalStumpings": {"$sum": "$performance.stumpings"},
                    "totalRunOuts": {"$sum": "$performance.runOuts"}
                }}
            ]
            
            result = await db.league_stats.aggregate(pipeline).to_list(1)
            if result:
                total_points = result[0]["totalPoints"]
                total_runs = result[0].get("totalRuns", 0)
                total_wickets = result[0].get("totalWickets", 0)
                total_catches = result[0].get("totalCatches", 0)
                total_stumpings = result[0].get("totalStumpings", 0)
                total_run_outs = result[0].get("totalRunOuts", 0)
            else:
                total_points = 0
                total_runs = 0
                total_wickets = 0
                total_catches = 0
                total_stumpings = 0
                total_run_outs = 0
            
            # Update or create leaderboard entry
            await db.cricket_leaderboard.update_one(
                {"leagueId": league_id, "playerExternalId": player_external_id},
                {
                    "$set": {
                        "leagueId": league_id,
                        "playerExternalId": player_external_id,
                        "totalPoints": total_points,
                        "totalRuns": total_runs,
                        "totalWickets": total_wickets,
                        "totalCatches": total_catches,
                        "totalStumpings": total_stumpings,
                        "totalRunOuts": total_run_outs,
                        "updatedAt": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            leaderboard_results.append({
                "playerExternalId": player_external_id, 
                "totalPoints": total_points,
                "runs": total_runs,
                "wickets": total_wickets,
                "catches": total_catches,
                "stumpings": total_stumpings,
                "runOuts": total_run_outs
            })
        
        # Update standings table with aggregated stats per manager
        # Get all participants to calculate their total points from owned players
        participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
        
        updated_table = []
        for participant in participants:
            user_id = participant["userId"]
            assets_owned = participant.get("clubsWon", [])  # player IDs
            
            # Get player external IDs from asset IDs
            assets = await db.assets.find({"id": {"$in": assets_owned}}).to_list(100)
            player_external_ids = [asset.get("externalId") for asset in assets if asset.get("externalId")]
            
            # Calculate totals for this manager
            manager_points = 0
            manager_runs = 0
            manager_wickets = 0
            manager_catches = 0
            manager_stumpings = 0
            manager_run_outs = 0
            
            for player_ext_id in player_external_ids:
                player_leaderboard = await db.cricket_leaderboard.find_one({
                    "leagueId": league_id,
                    "playerExternalId": player_ext_id
                }, {"_id": 0})
                if player_leaderboard:
                    manager_points += player_leaderboard.get("totalPoints", 0)
                    manager_runs += player_leaderboard.get("totalRuns", 0)
                    manager_wickets += player_leaderboard.get("totalWickets", 0)
                    manager_catches += player_leaderboard.get("totalCatches", 0)
                    manager_stumpings += player_leaderboard.get("totalStumpings", 0)
                    manager_run_outs += player_leaderboard.get("totalRunOuts", 0)
            
            updated_table.append({
                "userId": user_id,
                "displayName": participant.get("userName", "Unknown"),
                "points": manager_points,
                "assetsOwned": assets_owned,
                "tiebreakers": {
                    "goals": 0,
                    "wins": 0,
                    "runs": manager_runs,
                    "wickets": manager_wickets,
                    "catches": manager_catches,
                    "stumpings": manager_stumpings,
                    "runOuts": manager_run_outs
                }
            })
        
        # Sort by points descending
        updated_table.sort(key=lambda x: x["points"], reverse=True)
        
        # Update standings document
        await db.standings.update_one(
            {"leagueId": league_id},
            {"$set": {"table": updated_table}},
            upsert=True
        )
        
        # Auto-update fixture status to "completed" for all matches in the uploaded CSV
        fixtures_updated = 0
        for match_id in match_ids_processed:
            result = await db.fixtures.update_one(
                {"leagueId": league_id, "externalMatchId": match_id},
                {"$set": {"status": "completed"}}
            )
            if result.modified_count > 0:
                fixtures_updated += 1
        
        logger.info(f"Auto-marked {fixtures_updated} fixture(s) as completed for league {league_id}")
        
        return {
            "message": "Cricket scoring data ingested successfully",
            "processedRows": processed_rows,
            "updatedRows": updated_rows,
            "leaderboardUpdates": len(leaderboard_updates),
            "fixturesCompleted": fixtures_updated,
            "leaderboard": sorted(leaderboard_results, key=lambda x: x["totalPoints"], reverse=True)
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid CSV file format. Please ensure the file is UTF-8 encoded.")
    except HTTPException:
        # Re-raise HTTPExceptions (like missing columns) without modification
        raise
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@api_router.get("/scoring/{league_id}/leaderboard")
async def get_cricket_leaderboard(league_id: str):
    """
    Get cricket leaderboard for a league
    """
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get leaderboard data
    leaderboard = await db.cricket_leaderboard.find(
        {"leagueId": league_id}
    ).sort("totalPoints", -1).to_list(100)
    
    return {
        "leagueId": league_id,
        "leaderboard": [
            {
                "playerExternalId": entry["playerExternalId"],
                "totalPoints": entry["totalPoints"],
                "updatedAt": entry["updatedAt"]
            }
            for entry in leaderboard
        ]
    }

# ===== AUCTION ENDPOINTS =====
@api_router.post("/leagues/{league_id}/auction/start")
async def start_auction(league_id: str):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if assets are available for this sport
    sport_key = league.get("sportKey", "football")
    if sport_key == "football":
        # Check if clubs are seeded
        club_count = await db.clubs.count_documents({})
        if club_count == 0:
            # Auto-seed clubs if none exist
            from uefa_clubs import UEFA_CL_CLUBS
            clubs_to_insert = []
            for club_data in UEFA_CL_CLUBS:
                club = Club(**club_data)
                clubs_to_insert.append(club.model_dump())
            
            if clubs_to_insert:
                await db.clubs.insert_many(clubs_to_insert)
                logger.info(f"Auto-seeded {len(clubs_to_insert)} clubs for auction")
    
    # Check if we have assets for this sport
    asset_count = await asset_service.count_assets(sport_key)
    if asset_count == 0:
        raise HTTPException(status_code=400, detail=f"No assets available for {sport_key} sport. Please seed {sport_key} assets first.")
    
    # Check if auction already exists
    existing_auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    if existing_auction:
        return {"message": "Auction already exists", "auctionId": existing_auction["id"]}
    
    # Create auction with league timer settings (Prompt D)
    logger.info(f"🎬 START_AUCTION: Creating auction for league {league_id}")
    
    auction_create = AuctionCreate(
        leagueId=league_id,
        bidTimer=league.get("timerSeconds", 30),
        antiSnipeSeconds=league.get("antiSnipeSeconds", 10)
    )
    auction_obj = Auction(**auction_create.model_dump())
    
    try:
        result = await db.auctions.insert_one(auction_obj.model_dump())
        logger.info(f"   ✅ Auction created: ID={auction_obj.id}, inserted_id={result.inserted_id}")
    except Exception as e:
        logger.error(f"   ❌ CRITICAL: Auction insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create auction: {str(e)}")
    
    # Update league status
    try:
        await db.leagues.update_one(
            {"id": league_id},
            {"$set": {"status": "active"}}
        )
        logger.info(f"   ✅ League status updated to active")
    except Exception as e:
        logger.error(f"   ❌ Failed to update league status: {str(e)}")
    
    # Get assets based on feature flag and league selection
    import random
    assets_selected = league.get("assetsSelected", [])
    seed_mode = "all"  # Default mode
    
    # Feature flag: Only use assetsSelected if FEATURE_ASSET_SELECTION is enabled
    if FEATURE_ASSET_SELECTION and assets_selected and len(assets_selected) > 0:
        # Use commissioner's selected assets (feature flag ON + assets selected)
        seed_mode = "selected"
        if sport_key == "football":
            all_assets = await db.clubs.find({"id": {"$in": assets_selected}}).to_list(100)
        else:
            all_assets = await db.assets.find({
                "id": {"$in": assets_selected}, 
                "sportKey": sport_key
            }).to_list(100)
        
        # Validation: Ensure selected assets are valid
        if len(all_assets) == 0:
            raise HTTPException(
                status_code=400, 
                detail="No valid selected teams found. Please select teams in league settings before starting auction."
            )
        
        logger.info("auction.seed_queue", extra={
            "leagueId": league_id,
            "mode": "selected",
            "selected_count": len(all_assets),
            "sportKey": sport_key
        })
    else:
        # Use all available assets for this sport (default behavior or feature flag OFF)
        if sport_key == "football":
            all_assets = await db.clubs.find({}, {"_id": 0}).to_list(100)
        else:
            all_assets = await db.assets.find({"sportKey": sport_key}, {"_id": 0}).to_list(100)
        
        logger.info("auction.seed_queue", extra={
            "leagueId": league_id,
            "mode": "all",
            "selected_count": len(all_assets),
            "sportKey": sport_key,
            "feature_enabled": FEATURE_ASSET_SELECTION
        })
    
    random.shuffle(all_assets)
    
    # Prompt G: Feature flag - determines if auction starts in "waiting" or "active" state
    if FEATURE_WAITING_ROOM:
        # NEW BEHAVIOR: Create auction in "waiting" state (Prompt B)
        if all_assets:
            # Initialize asset queue (randomized order)
            asset_queue = [asset["id"] for asset in all_assets]
            
            # Update auction with queue, but stay in "waiting" state
            await db.auctions.update_one(
                {"id": auction_obj.id},
                {"$set": {
                    "status": "waiting",
                    "currentLot": 0,  # Not started yet
                    "currentClubId": None,
                    "clubQueue": asset_queue,
                    "unsoldClubs": [],
                    "timerEndsAt": None,  # No timer yet
                    "currentLotId": None,
                    "minimumBudget": 1000000.0
                }}
            )
            
            # Prompt G: Structured logging for auction creation
            logger.info("auction.created", extra={
                "leagueId": league_id,
                "auctionId": auction_obj.id,
                "status": "waiting",
                "assetCount": len(asset_queue),
                "sportKey": sport_key,
                "feature": "waiting_room_enabled"
            })
            
            # Emit to LEAGUE room (not auction room - users haven't entered yet)
            await sio.emit('league_status_changed', {
                'leagueId': league_id,
                'status': 'auction_created',
                'auctionId': auction_obj.id
            }, room=f"league:{league_id}")
            
            # Prompt G: Log league status change event
            league_room_size = len(sio.manager.rooms.get(f"league:{league_id}", {}).get("/", set()))
            logger.info("league_status_changed.emitted", extra={
                "leagueId": league_id,
                "auctionId": auction_obj.id,
                "status": "auction_created",
                "room": f"league:{league_id}",
                "roomSize": league_room_size
            })
            
            logger.info(f"Created auction {auction_obj.id} in waiting state with {len(asset_queue)} assets queued")
        else:
            logger.error(f"Failed to create auction {auction_obj.id} - no assets available")
            raise HTTPException(status_code=500, detail="No assets available to auction")
        
        return {"auctionId": auction_obj.id, "status": "waiting"}
    
    else:
        # OLD BEHAVIOR: Start auction immediately in "active" state (pre-waiting room)
        if all_assets:
            # Initialize asset queue
            asset_queue = [asset["id"] for asset in all_assets]
            
            # Get first asset
            first_asset_id = asset_queue[0]
            if sport_key == "football":
                first_asset = await db.clubs.find_one({"id": first_asset_id}, {"_id": 0})
            else:
                first_asset = await db.assets.find_one({"id": first_asset_id, "sportKey": sport_key}, {"_id": 0})
            
            if not first_asset:
                raise HTTPException(status_code=404, detail="First asset not found")
            
            # Start first lot immediately
            lot_id = f"{auction_obj.id}-lot-1"
            timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction_obj.bidTimer)
            
            await db.auctions.update_one(
                {"id": auction_obj.id},
                {"$set": {
                    "status": "active",
                    "currentClubId": first_asset_id,
                    "currentLot": 1,
                    "clubQueue": asset_queue,
                    "unsoldClubs": [],
                    "timerEndsAt": timer_end,
                    "currentLotId": lot_id,
                    "minimumBudget": 1000000.0
                }}
            )
            
            # Prompt G: Log legacy immediate start
            logger.info("auction.created", extra={
                "leagueId": league_id,
                "auctionId": auction_obj.id,
                "status": "active",
                "assetCount": len(asset_queue),
                "sportKey": sport_key,
                "feature": "waiting_room_disabled_legacy_behavior"
            })
            
            # Create timer event
            if timer_end.tzinfo is None:
                timer_end = timer_end.replace(tzinfo=timezone.utc)
            ends_at_ms = int(timer_end.timestamp() * 1000)
            timer_data = create_timer_event(lot_id, ends_at_ms)
            
            # Prepare asset data for emission
            if sport_key == "football":
                asset_data = Club(**first_asset).model_dump()
            else:
                asset_data = first_asset.copy()
                if "_id" in asset_data:
                    del asset_data["_id"]
            
            # Emit auction start and first lot
            await sio.emit('league_status_changed', {
                'leagueId': league_id,
                'status': 'auction_started',
                'auctionId': auction_obj.id
            }, room=f"league:{league_id}")
            
            await sio.emit('lot_started', {
                'club': asset_data,
                'lotNumber': 1,
                'timer': timer_data
            }, room=f"auction:{auction_obj.id}")
            
            # Start timer countdown
            asyncio.create_task(countdown_timer(auction_obj.id, timer_end, lot_id))
            
            logger.info(f"Created and started auction {auction_obj.id} immediately (legacy mode) with {len(asset_queue)} assets")
        else:
            logger.error(f"Failed to create auction {auction_obj.id} - no assets available")
            raise HTTPException(status_code=500, detail="No assets available to auction")
        
        return {"auctionId": auction_obj.id, "status": "active"}

@api_router.get("/leagues/{league_id}/state")
async def get_league_state(league_id: str):
    """
    Prompt B: Lightweight endpoint to get league status and active auction
    Returns: {leagueId, status, activeAuctionId (if exists)}
    """
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check for active auction
    auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    
    return {
        "leagueId": league_id,
        "status": league.get("status", "pending"),
        "activeAuctionId": auction["id"] if auction else None
    }

@api_router.post("/auction/{auction_id}/begin")
async def begin_auction(
    auction_id: str,
    user_id: str = Depends(require_user_id)
):
    """Prompt B: Commissioner manually starts the auction with proper auth (401/403 clarity)"""
    
    # Prompt G: Check feature flag - return 404 if waiting room feature is disabled
    if not FEATURE_WAITING_ROOM:
        logger.warning("begin_auction.feature_disabled", extra={
            "auctionId": auction_id,
            "feature": "waiting_room_disabled"
        })
        raise HTTPException(status_code=404, detail="Waiting room feature is not enabled")
    
    # Verify auction exists and is waiting
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction["status"] != "waiting":
        raise HTTPException(status_code=400, detail=f"Auction is not in waiting state (current: {auction['status']})")
    
    # Verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Prompt B: Check if current user is the commissioner - return 403 if not
    if league["commissionerId"] != user_id:
        logger.warning("begin_auction.unauthorized", extra={
            "auctionId": auction_id,
            "leagueId": auction["leagueId"],
            "userId": user_id,
            "commissionerId": league["commissionerId"]
        })
        raise HTTPException(status_code=403, detail="Only the commissioner can start the auction")
    
    # Prompt G: Log begin_auction call
    auction_room_size = len(sio.manager.rooms.get(f"auction:{auction_id}", {}).get("/", set()))
    logger.info("begin_auction.called", extra={
        "auctionId": auction_id,
        "leagueId": auction["leagueId"],
        "userId": user_id,
        "commissionerId": league["commissionerId"],
        "auctionRoomSize": auction_room_size
    })
    
    # Get sport key for asset retrieval
    sport_key = league.get("sportKey", "football")
    
    # Get the club queue
    asset_queue = auction.get("clubQueue", [])
    if not asset_queue:
        raise HTTPException(status_code=400, detail="No assets in auction queue")
    
    # Get first asset details
    first_asset_id = asset_queue[0]
    if sport_key == "football":
        first_asset = await db.clubs.find_one({"id": first_asset_id}, {"_id": 0})
    else:
        first_asset = await db.assets.find_one({"id": first_asset_id, "sportKey": sport_key}, {"_id": 0})
    
    if not first_asset:
        raise HTTPException(status_code=404, detail="First asset not found")
    
    # Start first lot
    lot_id = f"{auction_id}-lot-1"
    timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction.get("bidTimer", 30))
    
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "currentClubId": first_asset_id,
            "currentLot": 1,
            "timerEndsAt": timer_end,
            "currentLotId": lot_id
        }}
    )
    
    # Create timer event
    if timer_end.tzinfo is None:
        timer_end = timer_end.replace(tzinfo=timezone.utc)
    ends_at_ms = int(timer_end.timestamp() * 1000)
    timer_data = create_timer_event(lot_id, ends_at_ms)
    
    # Prepare asset data for emission
    if sport_key == "football":
        asset_data = Club(**first_asset).model_dump()
    else:
        asset_data = first_asset.copy()
        if "_id" in asset_data:
            del asset_data["_id"]
    
    # Emit lot start to auction room
    await sio.emit('lot_started', {
        'club': asset_data,
        'lotNumber': 1,
        'timer': timer_data
    }, room=f"auction:{auction_id}")
    
    # Prompt G: Log lot_started emission
    logger.info("lot_started.emitted", extra={
        "auctionId": auction_id,
        "leagueId": auction["leagueId"],
        "lotNumber": 1,
        "assetId": first_asset_id,
        "room": f"auction:{auction_id}",
        "roomSize": auction_room_size
    })
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end, lot_id))
    
    logger.info(f"Commissioner started auction {auction_id}, first lot: {first_asset.get('name')}")
    
    # Emit to league room as well
    await sio.emit('league_status_changed', {
        'leagueId': league["id"],
        'status': 'auction_active',
        'auctionId': auction_id,
        'message': 'Auction has begun!'
    }, room=f"league:{league['id']}")
    
    return {"message": "Auction started successfully", "auctionId": auction_id, "firstAsset": first_asset.get("name")}


@api_router.get("/leagues/{league_id}/auction")
async def get_league_auction(league_id: str):
    """Get the auction for a specific league"""
    auction = await db.auctions.find_one({"leagueId": league_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="No auction found for this league")
    return {"auctionId": auction["id"], "status": auction["status"]}

@api_router.get("/auction/{auction_id}/clubs")
async def get_auction_clubs(auction_id: str):
    """Get all clubs in the auction with their status (upcoming/current/sold/unsold)"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get club queue - these are the ONLY clubs in this auction
    club_queue = auction.get("clubQueue", [])
    unsold_clubs = auction.get("unsoldClubs", [])
    current_club_id = auction.get("currentClubId")
    current_lot = auction.get("currentLot", 0)
    
    # Prompt 3: Only get clubs that are in the auction queue
    # This respects assetsSelected - if 9 clubs selected, only those 9 are in queue
    if not club_queue:
        return {
            "clubs": [],
            "summary": {
                "totalClubs": 0,
                "soldClubs": 0,
                "unsoldClubs": 0,
                "remainingClubs": 0
            }
        }
    
    # Get league to determine sport
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    sport_key = league.get("sportKey", "football") if league else "football"
    
    # Fetch only clubs that are in the auction queue
    if sport_key == "football":
        auction_clubs = await db.clubs.find({"id": {"$in": club_queue}}).to_list(len(club_queue))
    else:
        auction_clubs = await db.assets.find({
            "id": {"$in": club_queue},
            "sportKey": sport_key
        }).to_list(len(club_queue))
    
    # Get all bids to determine sold clubs
    all_bids = await db.bids.find({"auctionId": auction_id}, {"_id": 0}).to_list(1000)
    
    # Group bids by club to find winners
    bids_by_club = {}
    for bid in all_bids:
        club_id = bid["clubId"]
        if club_id not in bids_by_club or bid["amount"] > bids_by_club[club_id]["amount"]:
            bids_by_club[club_id] = bid
    
    clubs_with_status = []
    
    for club in auction_clubs:
        club.pop('_id', None)  # Remove MongoDB ID
        
        # Determine club status
        club_id = club["id"]
        status = "upcoming"  # Default status
        winner = None
        winning_bid = None
        lot_number = None
        
        # Find lot number if club is in queue
        try:
            lot_index = club_queue.index(club_id)
            lot_number = lot_index + 1
        except ValueError:
            lot_number = None
        
        if club_id == current_club_id:
            status = "current"
        elif club_id in unsold_clubs:
            status = "unsold"
        elif club_id in bids_by_club:
            # Club has bids and lot has passed
            winning_bid_data = bids_by_club[club_id]
            winner = winning_bid_data.get("userName", "Unknown")
            winning_bid = winning_bid_data.get("amount", 0)
            status = "sold"
        # If none of above, status remains "upcoming"
        
        # Add club with status
        club_data = Club(**club).model_dump() if sport_key == "football" else club
        clubs_with_status.append({
            **club_data,
            "status": status,
            "lotNumber": lot_number,
            "winner": winner,
            "winningBid": winning_bid
        })
    
    # Sort by status first, then alphabetically (hide draw order for strategy)
    def sort_key(club):
        if club["status"] == "current":
            return (0, club["name"])  # Current lot first
        elif club["status"] == "sold":
            return (1, club.get("lotNumber", 999))  # Sold by lot order for history
        elif club["status"] == "unsold":
            return (2, club["name"])  # Unsold alphabetically
        else:  # upcoming
            return (3, club["name"])  # Upcoming alphabetically (hide draw order)
    
    clubs_with_status.sort(key=sort_key)
    
    return {
        "clubs": clubs_with_status,
        "summary": {
            "totalClubs": len(auction_clubs),  # Prompt 3: Only clubs in auction queue
            "soldClubs": len([c for c in clubs_with_status if c["status"] == "sold"]),
            "unsoldClubs": len([c for c in clubs_with_status if c["status"] == "unsold"]),
            "remainingClubs": len([c for c in clubs_with_status if c["status"] in ["upcoming", "current"]])
        }
    }

@api_router.get("/auction/{auction_id}")
async def get_auction(auction_id: str):
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get all bids for this auction
    bids = await db.bids.find({"auctionId": auction_id}, {"_id": 0}).to_list(1000)
    
    # Get current asset if exists
    current_asset = None
    if auction.get("currentClubId"):
        # First get the league to determine sport
        league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
        sport_key = league.get("sportKey", "football") if league else "football"
        
        if sport_key == "football":
            # Get from clubs collection for football
            asset = await db.clubs.find_one({"id": auction["currentClubId"]}, {"_id": 0})
            if asset:
                current_asset = Club(**asset)
        else:
            # Get from assets collection for other sports
            asset = await db.assets.find_one({"id": auction["currentClubId"]}, {"_id": 0})
            if asset:
                # Clean up MongoDB fields for JSON serialization
                if "_id" in asset:
                    del asset["_id"]
                current_asset = asset
    
    return {
        "auction": Auction(**auction),
        "bids": [Bid(**bid) for bid in bids],
        "currentClub": current_asset  # Keep field name for backward compatibility
    }

@api_router.post("/auction/{auction_id}/bid")
async def place_bid(auction_id: str, bid_input: BidCreate):
    # Metrics: Track bid processing time
    start_time = time.time()
    
    # Verify auction exists and is active
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction["status"] != "active":
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # Get user details
    user = await db.users.find_one({"id": bid_input.userId}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get league
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get participant to check budget
    participant = await db.league_participants.find_one({
        "leagueId": auction["leagueId"],
        "userId": bid_input.userId
    }, {"_id": 0})
    if not participant:
        raise HTTPException(status_code=403, detail="User is not a participant in this league")
    
    # Check minimum bid amount
    minimum_budget = auction.get("minimumBudget", 1000000.0)  # Default £1m
    if bid_input.amount < minimum_budget:
        metrics.increment_bid_rejected("minimum_bid")
        raise HTTPException(
            status_code=400, 
            detail=f"Bid must be at least £{minimum_budget:,.0f}"
        )
    
    # Check if user has enough budget
    if bid_input.amount > participant["budgetRemaining"]:
        metrics.increment_bid_rejected("insufficient_budget")
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient budget. You have £{participant['budgetRemaining']:,.0f} remaining"
        )
    
    # Everton Bug Fix: Enforce budget reserve for remaining slots
    # User must keep £1m per remaining slot (except on final slot)
    clubs_won_count = len(participant.get("clubsWon", []))
    max_slots = league.get("clubSlots", 3)
    slots_remaining = max_slots - clubs_won_count
    
    if slots_remaining > 1:  # Not on final slot
        # Must reserve £1m per remaining slot
        reserve_needed = (slots_remaining - 1) * 1_000_000
        max_allowed_bid = participant["budgetRemaining"] - reserve_needed
        
        if bid_input.amount > max_allowed_bid:
            metrics.increment_bid_rejected("insufficient_reserve")
            raise HTTPException(
                status_code=400,
                detail=f"Must reserve £{reserve_needed/1_000_000:.0f}m for {slots_remaining - 1} remaining slot(s). "
                       f"Max bid: £{max_allowed_bid/1_000_000:.1f}m"
            )
    
    # Check if user has reached roster limit (Prompt C: Roster enforcement)
    clubs_won_count = len(participant.get("clubsWon", []))
    max_slots = league.get("clubSlots", 3)  # Default to 3 if not set
    if clubs_won_count >= max_slots:
        metrics.increment_bid_rejected("roster_full")
        raise HTTPException(
            status_code=400,
            detail=f"Roster full. You already own {clubs_won_count}/{max_slots} teams"
        )
    
    # Get current club from auction
    current_club_id = auction.get("currentClubId")
    if not current_club_id:
        raise HTTPException(status_code=400, detail="No club currently being auctioned")
    
    # Create bid
    bid_obj = Bid(
        auctionId=auction_id,
        clubId=current_club_id,
        userId=bid_input.userId,
        amount=bid_input.amount,
        userName=user["name"],
        userEmail=user["email"]
    )
    await db.bids.insert_one(bid_obj.model_dump())
    
    # Metrics: Track successful bid
    metrics.increment_bid_accepted(auction_id)
    metrics.observe_bid_latency(time.time() - start_time)
    
    # Update auction with current bid info and increment sequence atomically (Prompt B)
    current_bidder = {
        "userId": bid_input.userId,
        "displayName": user["name"]
    }
    
    # Use atomic increment to avoid race conditions in rapid bidding
    update_result = await db.auctions.update_one(
        {"id": auction_id},
        {
            "$set": {
                "currentBid": bid_input.amount,
                "currentBidder": current_bidder
            },
            "$inc": {
                "bidSequence": 1
            }
        }
    )
    
    # Get the updated sequence number
    updated_auction = await db.auctions.find_one({"id": auction_id}, {"bidSequence": 1})
    new_bid_sequence = updated_auction.get("bidSequence", 1)
    
    # Get room size for debugging
    room_sockets = sio.manager.rooms.get(f"auction:{auction_id}", set())
    room_size = len(room_sockets)
    
    # JSON log for debugging
    logger.info(json.dumps({
        "event": "bid_update",
        "auctionId": auction_id,
        "lotId": auction.get("currentLotId"),
        "seq": new_bid_sequence,
        "amount": bid_input.amount,
        "bidderId": bid_input.userId,
        "bidderName": user["name"],
        "roomSize": room_size,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    # Emit bid update to all users (Everyone sees current bid)
    await sio.emit('bid_update', {
        'lotId': auction.get("currentLotId"),
        'amount': bid_input.amount,
        'bidder': current_bidder,
        'seq': new_bid_sequence,
        'serverTime': datetime.now(timezone.utc).isoformat()
    }, room=f"auction:{auction_id}")
    
    # Also emit legacy bid_placed for backward compatibility
    await sio.emit('bid_placed', {
        'bid': bid_obj.model_dump(mode='json'),
        'auctionId': auction_id,
        'clubId': current_club_id
    }, room=f"auction:{auction_id}")
    
    # Check for anti-snipe
    if auction.get("timerEndsAt"):
        timer_end = auction["timerEndsAt"]
        if timer_end.tzinfo is None:
            timer_end = timer_end.replace(tzinfo=timezone.utc)
        time_remaining = (timer_end - datetime.now(timezone.utc)).total_seconds()
        if time_remaining <= auction["antiSnipeSeconds"] and time_remaining > 0:
            # Extend timer
            new_end_time = datetime.now(timezone.utc) + timedelta(seconds=auction["antiSnipeSeconds"])
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {"timerEndsAt": new_end_time}}
            )
            
            # Get lot ID and create anti-snipe timer data
            lot_id = auction.get("currentLotId")
            if not lot_id and auction.get("currentLot"):
                lot_id = f"{auction_id}-lot-{auction['currentLot']}"
            
            if lot_id:
                ends_at_ms = int(new_end_time.timestamp() * 1000)
                timer_data = create_timer_event(lot_id, ends_at_ms)
                
                await sio.emit('anti_snipe', timer_data, room=f"auction:{auction_id}")
                
                logger.info(f"Anti-snipe triggered for lot {lot_id}: seq={timer_data['seq']}, new end={timer_data['endsAt']}")
    
    # DIAGNOSTIC: Check what completion status should be after this bid
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
    auction_state = {
        "lots_sold": sum(1 for p in participants for c in p.get("clubsWon", [])),
        "current_lot": auction.get("currentLot", 0),
        "total_lots": len(auction.get("clubQueue", [])),
        "unsold_count": len(auction.get("unsoldClubs", []))
    }
    status = compute_auction_status(league, participants, auction_state)
    logger.info(f"🔍 AUCTION_STATUS after bid: {json.dumps(status)}")
    
    # Note: Roster fullness check moved to complete_lot (after clubs are awarded)
    
    return {"message": "Bid placed successfully", "bid_obj": bid_obj}

@api_router.post("/auction/{auction_id}/start-lot/{club_id}")
async def start_lot(auction_id: str, club_id: str):
    # Verify auction and club exist
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    club = await db.clubs.find_one({"id": club_id}, {"_id": 0})
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # DIAGNOSTIC: Check completion status before starting next lot
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
    auction_state = {
        "lots_sold": sum(1 for p in participants for c in p.get("clubsWon", [])),
        "current_lot": auction.get("currentLot", 0),
        "total_lots": len(auction.get("clubQueue", [])),
        "unsold_count": len(auction.get("unsoldClubs", []))
    }
    status = compute_auction_status(league, participants, auction_state)
    logger.info(f"🔍 AUCTION_STATUS before starting lot: {json.dumps(status)}")
    
    # Update auction with current lot
    new_lot_number = auction["currentLot"] + 1
    lot_id = f"{auction_id}-lot-{new_lot_number}"
    timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
    
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "currentClubId": club_id,
            "currentLot": new_lot_number,
            "currentLotId": lot_id,
            "timerEndsAt": timer_end
        }}
    )
    
    # Create timer data
    if timer_end.tzinfo is None:
        timer_end = timer_end.replace(tzinfo=timezone.utc)
    ends_at_ms = int(timer_end.timestamp() * 1000)
    timer_data = create_timer_event(lot_id, ends_at_ms)
    
    # Emit lot start
    await sio.emit('lot_started', {
        'club': Club(**club).model_dump(),
        'lotNumber': new_lot_number,
        'timer': timer_data
    }, room=f"auction:{auction_id}")
    
    logger.info(f"Manual start lot {lot_id}: {club['name']}, seq={timer_data['seq']}")
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end, lot_id))
    
    return {"message": "Lot started", "club": Club(**club)}

@api_router.post("/auction/{auction_id}/complete-lot")
async def complete_lot(auction_id: str):
    logger.info(f"🎬 COMPLETE_LOT START for auction {auction_id}")
    
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    current_club_id = auction.get("currentClubId")
    current_lot = auction.get("currentLot", 0)
    club_queue_length = len(auction.get("clubQueue", []))
    
    logger.info(f"   Lot {current_lot}/{club_queue_length}, Club: {current_club_id}")
    
    if not current_club_id:
        raise HTTPException(status_code=400, detail="No current club to complete")
    
    # Get bids for current club
    bids = await db.bids.find({
        "auctionId": auction_id,
        "clubId": current_club_id
    }, {"_id": 0}).sort("amount", -1).to_list(1)
    
    winning_bid = bids[0] if bids else None
    
    logger.info(f"   Bids found: {len(bids)}, Winning bid: {winning_bid['amount'] if winning_bid else 'None'}")
    
    # Remove MongoDB _id from winning bid
    if winning_bid:
        winning_bid.pop('_id', None)
    
    # Handle sold vs unsold scenarios
    if winning_bid:
        # CLUB SOLD - Update winner's budget and clubs
        participant = await db.league_participants.find_one({
            "leagueId": auction["leagueId"],
            "userId": winning_bid["userId"]
        }, {"_id": 0})
        
        if participant:
            user_winning_clubs = participant.get("clubsWon", [])
            user_total_spent = participant.get("totalSpent", 0.0)
            
            logger.info(f"   BEFORE: User {winning_bid['userId']} has {len(user_winning_clubs)} clubs, spent £{user_total_spent:,.0f}")
            
            # Idempotency check: Don't add club if already awarded
            if current_club_id in user_winning_clubs:
                logger.info(f"   ⚠️ Club {current_club_id} already awarded to {winning_bid['userId']}, skipping duplicate")
                return
            
            # Add this club and amount
            user_winning_clubs.append(current_club_id)
            user_total_spent += winning_bid["amount"]
            
            # Calculate remaining budget
            league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
            budget_remaining = league["budget"] - user_total_spent
            
            # Update participant
            update_result = await db.league_participants.update_one(
                {"leagueId": auction["leagueId"], "userId": winning_bid["userId"]},
                {"$set": {
                    "clubsWon": user_winning_clubs,
                    "totalSpent": user_total_spent,
                    "budgetRemaining": budget_remaining
                }}
            )
            
            logger.info(f"   AFTER: User {winning_bid['userId']} now has {len(user_winning_clubs)} clubs, spent £{user_total_spent:,.0f}")
            logger.info(f"   DB Update: modified_count={update_result.modified_count}")
            
        else:
            logger.error(f"   ❌ CRITICAL: Participant NOT FOUND for user {winning_bid['userId']}")
            
        logger.info(f"✅ Club sold - {current_club_id} to {winning_bid['userId']} for £{winning_bid['amount']:,}")
    
    else:
        # CLUB UNSOLD - Add to unsold queue for re-offering later
        current_unsold = auction.get("unsoldClubs", [])
        if current_club_id not in current_unsold:
            current_unsold.append(current_club_id)
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {"unsoldClubs": current_unsold}}
            )
        
        logger.info(f"Club unsold - {current_club_id} moved to end of queue")
    
    # Get updated participants
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
    for p in participants:
        p.pop('_id', None)
    
    # Check if all rosters are now full (after awarding this club)
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    max_slots = league.get("clubSlots", 3)
    all_full = all(len(p.get("clubsWon", [])) >= max_slots for p in participants)
    
    if all_full:
        logger.info(f"🏁 All rosters full after lot complete - completing auction early")
        # Clear current lot/club before completing
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {"currentClubId": None, "currentLot": auction.get("currentLot", 0)}}
        )
        await check_auction_completion(auction_id)
        return  # Don't proceed to next lot
    
    # Get current club/player details for the event
    current_asset = None
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    sport_key = league.get("sportKey", "football") if league else "football"
    
    if sport_key == "football":
        current_asset = await db.clubs.find_one({"id": current_club_id}, {"_id": 0})
    else:
        current_asset = await db.assets.find_one({"id": current_club_id, "sportKey": sport_key}, {"_id": 0})
    
    asset_name = current_asset.get("name") if current_asset else "Unknown"
    
    # Emit sold/unsold event
    current_lot_id = auction.get("currentLotId")
    if not current_lot_id and auction.get("currentLot"):
        current_lot_id = f"{auction_id}-lot-{auction['currentLot']}"
    
    sold_data = {}
    if current_lot_id:
        sold_timer_data = create_timer_event(current_lot_id, int(datetime.now(timezone.utc).timestamp() * 1000))
        sold_data['timer'] = sold_timer_data
    
    await sio.emit('sold', {
        'clubId': current_club_id,
        'clubName': asset_name,  # Include player/club name
        'winningBid': Bid(**winning_bid).model_dump(mode='json') if winning_bid else None,
        'unsold': not bool(winning_bid),  # Flag if club went unsold
        'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants],
        **sold_data
    }, room=f"auction:{auction_id}")
    
    # Check if there's a next club to auction
    logger.info(f"🔍 BEFORE get_next_club: currentLot={auction.get('currentLot')}, queueLen={len(auction.get('clubQueue', []))}")
    next_club_id = await get_next_club_to_auction(auction_id)
    logger.info(f"🔍 AFTER get_next_club: next_club_id={next_club_id}")
    
    logger.info(f"auction.next_lot_decision", extra={
        "auction_id": auction_id,
        "will_start_next": bool(next_club_id and auction.get('status') == 'active'),
        "next_club_id": next_club_id if next_club_id else None
    })
    
    if next_club_id:
        # Three-second pause before next lot to prevent bid bleed and give thinking time
        logger.info(f"⏸️  Starting 3-second pause before next lot")
        
        # Emit countdown to all clients
        for countdown in [3, 2, 1]:
            await sio.emit("next_team_countdown", {
                "seconds": countdown,
                "message": f"Next team in {countdown}..."
            }, room=f"auction:{auction_id}")
            await asyncio.sleep(1)
        
        # Clear countdown overlay
        await sio.emit("next_team_countdown", {
            "seconds": 0,
            "message": "Starting..."
        }, room=f"auction:{auction_id}")
        
        await start_next_lot(auction_id, next_club_id)
    else:
        # No more clubs - auction is complete
        # Pass final club info to completion check
        await check_auction_completion(
            auction_id,
            final_club_id=current_club_id,
            final_winning_bid=winning_bid
        )


async def get_next_club_to_auction(auction_id: str) -> Optional[str]:
    """Get the next club to auction, considering queue and unsold clubs"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        return None
    
    club_queue = auction.get("clubQueue", [])
    unsold_clubs = auction.get("unsoldClubs", [])
    current_lot = auction.get("currentLot", 0)
    
    logger.info(f"🔍 get_next_club_to_auction: currentLot={current_lot}, queueLen={len(club_queue)}, check={current_lot < len(club_queue)}")
    
    # Check if we're still in the initial round
    if current_lot < len(club_queue):
        # Return next club in initial queue
        next_id = club_queue[current_lot]
        logger.info(f"🔍 Returning next club from queue: {next_id}")
        return next_id
    
    # Initial round complete - check for unsold clubs
    if unsold_clubs:
        # Check if any participants can still bid (budget + roster slots) - Prompt C
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
        league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
        minimum_budget = auction.get("minimumBudget", 1000000.0)
        max_slots = league.get("clubSlots", 3) if league else 3
        
        # Check for eligible bidders (has budget AND roster space)
        eligible_bidders = []
        for p in participants:
            has_budget = p.get("budgetRemaining", 0) >= minimum_budget
            has_slots = len(p.get("clubsWon", [])) < max_slots
            if has_budget and has_slots:
                eligible_bidders.append(p)
        
        if eligible_bidders:
            # Return first unsold club and remove it from unsold list
            next_unsold = unsold_clubs[0]
            remaining_unsold = unsold_clubs[1:]
            
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {"unsoldClubs": remaining_unsold}}
            )
            
            logger.info(f"Re-offering unsold club: {next_unsold}")
            return next_unsold
    
    # No more clubs to offer
    return None


async def start_next_lot(auction_id: str, next_club_id: str):
    """Start the next lot with the given club"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        return
    
    # Get league to determine sport
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        logger.error(f"League not found for auction {auction_id}")
        return
    
    sport_key = league.get("sportKey", "football")
    
    # Get club/asset details based on sport
    if sport_key == "football":
        next_club = await db.clubs.find_one({"id": next_club_id}, {"_id": 0})
    else:
        next_club = await db.assets.find_one({"id": next_club_id, "sportKey": sport_key}, {"_id": 0})
    
    if not next_club:
        logger.error(f"Club/Asset not found: {next_club_id} (sport: {sport_key})")
        return
    
    next_lot_number = auction["currentLot"] + 1
    next_lot_id = f"{auction_id}-lot-{next_lot_number}"
    timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
    
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "currentClubId": next_club_id,
            "currentLot": next_lot_number,
            "currentLotId": next_lot_id,
            "timerEndsAt": timer_end,
            "currentBid": None,
            "currentBidder": None
        }}
    )
    
    # Remove _id for serialization
    next_club.pop('_id', None)
    
    # Create timer data
    if timer_end.tzinfo is None:
        timer_end = timer_end.replace(tzinfo=timezone.utc)
    ends_at_ms = int(timer_end.timestamp() * 1000)
    timer_data = create_timer_event(next_lot_id, ends_at_ms)
    
    # Emit lot start - send appropriate data based on sport
    lot_data = {
        'lotNumber': next_lot_number,
        'timer': timer_data,
        'isUnsoldRetry': next_club_id and next_club_id in (auction.get("unsoldClubs", []))
    }
    
    if sport_key == "football":
        lot_data['club'] = Club(**next_club).model_dump()
    else:
        # For cricket and other sports, send raw asset data
        lot_data['club'] = next_club
    
    await sio.emit('lot_started', lot_data, room=f"auction:{auction_id}")
    
    logger.info(f"Started lot {next_lot_number}: {next_club['name']}")
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end, next_lot_id))


async def check_auction_completion(auction_id: str, final_club_id: str = None, final_winning_bid: dict = None):
    """Check if auction is complete and handle completion (idempotent)"""
    logger.info(f"🔍 check_auction_completion CALLED for {auction_id}")
    
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        logger.warning(f"❌ check_auction_completion: Auction {auction_id} not found")
        return
    
    # Idempotent: If already completed, do nothing (return fast)
    if auction.get("status") == "completed":
        logger.info(f"✅ Auction {auction_id} already completed - returning")
        return
    
    # Get league info for roster limits
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        logger.warning(f"❌ check_auction_completion: League not found for auction {auction_id}")
        return
    
    unsold_clubs = auction.get("unsoldClubs", [])
    club_queue = auction.get("clubQueue", [])
    current_lot = auction.get("currentLot", 0)
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
    minimum_budget = auction.get("minimumBudget", 1000000.0)
    max_slots = league.get("clubSlots", 3)
    
    # Calculate remaining demand (sum of max(0, slots - clubsWon) per manager)
    remaining_demand = 0
    all_managers_full = True
    eligible_bidders = []
    
    for participant in participants:
        clubs_won = len(participant.get("clubsWon", []))
        has_budget = participant.get("budgetRemaining", 0) >= minimum_budget
        has_slots = clubs_won < max_slots
        
        # Calculate demand for this manager
        demand = max(0, max_slots - clubs_won)
        remaining_demand += demand
        
        if has_slots and has_budget:
            eligible_bidders.append(participant)
            all_managers_full = False
    
    # Check if there are more clubs to auction (either in queue or unsold to retry)
    # NOTE: currentLot is 1-based. Use < to check if more lots exist AFTER current one
    clubs_remaining = (current_lot < len(club_queue)) or len(unsold_clubs) > 0
    
    # Auction should end if: no clubs remaining, no eligible bidders, or all managers are full
    should_complete = not clubs_remaining or not eligible_bidders or all_managers_full
    
    # DEFENSIVE LOGGING: Track exact values for debugging
    logger.info(f"🔍 COMPLETION_CHECK [Auction: {auction_id}]:")
    logger.info(f"   currentLot={current_lot}, clubQueue_length={len(club_queue)}, unsold={len(unsold_clubs)}")
    logger.info(f"   Logic: ({current_lot} <= {len(club_queue)}) = {current_lot <= len(club_queue)}")
    logger.info(f"   clubs_remaining={clubs_remaining}, should_complete={should_complete}")
    logger.info(f"   eligible_bidders={len(eligible_bidders)}, all_managers_full={all_managers_full}")
    
    # Structured logging
    logger.info("auction.completion_check", extra={
        "auction_id": auction_id,
        "remaining_demand": remaining_demand,
        "status": auction.get("status"),
        "all_managers_full": all_managers_full,
        "eligible_bidders": len(eligible_bidders),
        "clubs_remaining": clubs_remaining,
        "should_complete": should_complete,
        "current_lot": current_lot,
        "club_queue_length": len(club_queue)
    })
    
    if should_complete:
        # Atomically set status to completed (only if currently active)
        result = await db.auctions.update_one(
            {"id": auction_id, "status": "active"},
            {"$set": {
                "status": "completed",
                "completedAt": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Check if we actually updated (atomic guard against double-completion)
        if result.modified_count == 0:
            logger.info(f"⚠️ Auction {auction_id} was not updated (already completed or not active)")
            return
        
        # Update league status
        await db.leagues.update_one(
            {"id": auction["leagueId"]},
            {"$set": {"status": "completed"}}
        )
        
        # Calculate final statistics
        total_clubs_sold = 0
        total_unsold = len(unsold_clubs)
        
        for p in participants:
            total_clubs_sold += len(p.get("clubsWon", []))
        
        # Determine completion reason for better user feedback
        completion_reason = "completed"
        if all_managers_full:
            completion_reason = "All managers have filled their rosters"
        elif not eligible_bidders:
            completion_reason = "No managers can afford minimum bid"
        elif not clubs_remaining:
            completion_reason = "All available teams have been sold"
        
        await sio.emit('auction_complete', {
            'message': f'Auction completed! {total_clubs_sold} teams sold, {total_unsold} unsold.',
            'reason': completion_reason,
            'clubsSold': total_clubs_sold,
            'clubsUnsold': total_unsold,
            'finalClubId': final_club_id,  # Include final club sold
            'finalWinningBid': Bid(**final_winning_bid).model_dump(mode='json') if final_winning_bid else None,
            'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants]
        }, room=f"auction:{auction_id}")
        
        # Emit league status changed event
        league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
        if league:
            # Get room size for debugging
            room_sockets = sio.manager.rooms.get(f"league:{auction['leagueId']}", set())
            room_size = len(room_sockets)
            
            # JSON log for debugging
            logger.info(json.dumps({
                "event": "league_status_changed",
                "leagueId": auction['leagueId'],
                "status": "auction_complete",
                "auctionId": None,
                "roomSize": room_size,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            
            await sio.emit('league_status_changed', {
                'leagueId': auction["leagueId"],
                'status': 'auction_complete'
            }, room=f"league:{auction['leagueId']}")
            
            # Create initial standings if not exists
            existing_standing = await db.standings.find_one({"leagueId": auction["leagueId"]}, {"_id": 0})
            if not existing_standing:
                table = []
                for participant in participants:
                    table.append({
                        "userId": participant["userId"],
                        "displayName": participant["userName"],
                        "points": 0.0,
                        "assetsOwned": participant.get("clubsWon", []),
                        "tiebreakers": {"goals": 0, "wins": 0, "runs": 0, "wickets": 0, "catches": 0, "stumpings": 0, "runOuts": 0}
                    })
                
                standing_obj = Standing(
                    leagueId=auction["leagueId"],
                    sportKey=league["sportKey"],
                    table=table
                )
                
                await db.standings.insert_one(standing_obj.model_dump())
                logger.info(f"Created initial standings for league {auction['leagueId']}")
        
        logger.info(f"✅ AUCTION COMPLETED: {auction_id} - {total_clubs_sold} sold, {total_unsold} unsold. Reason: {completion_reason}")
    else:
        logger.info(f"❌ Auction NOT completing: should_complete={should_complete}")

@api_router.post("/auction/{auction_id}/pause")
async def pause_auction(auction_id: str, commissioner_id: str = None):
    """Pause an active auction - only commissioner can do this"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify commissioner permissions (for now, skip verification - would need user auth)
    
    if auction["status"] != "active":
        raise HTTPException(status_code=400, detail="Can only pause active auctions")
    
    # Cancel active timer
    if auction_id in active_timers:
        active_timers[auction_id].cancel()
        del active_timers[auction_id]
    
    # Store remaining time when paused
    remaining_time = 0
    if auction.get("timerEndsAt"):
        timer_end = auction["timerEndsAt"]
        if timer_end.tzinfo is None:
            timer_end = timer_end.replace(tzinfo=timezone.utc)
        remaining_time = max(0, (timer_end - datetime.now(timezone.utc)).total_seconds())
    
    # Update auction status
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "paused",
            "pausedRemainingTime": remaining_time,  # Store remaining time
            "pausedAt": datetime.now(timezone.utc)
        }}
    )
    
    # Notify all participants
    await sio.emit('auction_paused', {
        'message': 'Auction has been paused by the commissioner',
        'remainingTime': remaining_time
    }, room=f"auction:{auction_id}")
    
    logger.info(f"Auction {auction_id} paused with {remaining_time}s remaining")
    
    return {"message": "Auction paused successfully", "remainingTime": remaining_time}


@api_router.post("/auction/{auction_id}/resume")
async def resume_auction(auction_id: str, commissioner_id: str = None):
    """Resume a paused auction - only commissioner can do this"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify commissioner permissions (for now, skip verification)
    
    if auction["status"] != "paused":
        raise HTTPException(status_code=400, detail="Can only resume paused auctions")
    
    # Calculate new end time based on stored remaining time
    remaining_time = auction.get("pausedRemainingTime", auction.get("bidTimer", 60))
    new_end_time = datetime.now(timezone.utc) + timedelta(seconds=remaining_time)
    
    # Update auction status
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "timerEndsAt": new_end_time
        },
        "$unset": {
            "pausedRemainingTime": "",
            "pausedAt": ""
        }}
    )
    
    # Restart timer
    current_lot_id = auction.get("currentLotId")
    if not current_lot_id:
        current_lot_id = f"{auction_id}-lot-{auction.get('currentLot', 1)}"
    
    asyncio.create_task(countdown_timer(auction_id, new_end_time, current_lot_id))
    
    # Notify all participants
    await sio.emit('auction_resumed', {
        'message': 'Auction has been resumed by the commissioner',
        'newEndTime': new_end_time.isoformat(),
        'remainingTime': remaining_time
    }, room=f"auction:{auction_id}")
    
    logger.info(f"Auction {auction_id} resumed with {remaining_time}s remaining")
    
    return {"message": "Auction resumed successfully", "remainingTime": remaining_time}


@api_router.delete("/auction/{auction_id}")
async def delete_auction(auction_id: str, commissioner_id: str = None):
    """Delete an auction and all associated bids - only commissioner can do this"""
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify commissioner permissions (for now, skip verification if not provided)
    # if commissioner_id and league["commissionerId"] != commissioner_id:
    #     raise HTTPException(status_code=403, detail="Only the commissioner can delete this auction")
    
    # Cancel any active timers
    if auction_id in active_timers:
        active_timers[auction_id].cancel()
        del active_timers[auction_id]
    
    # Delete all bids for this auction
    bid_result = await db.bids.delete_many({"auctionId": auction_id})
    
    # Reset participant budgets and clubs won (since auction is being deleted)
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
    for participant in participants:
        await db.league_participants.update_one(
            {"id": participant["id"]},
            {"$set": {
                "budgetRemaining": league["budget"],  # Reset to full budget
                "totalSpent": 0.0,
                "clubsWon": []
            }}
        )
    
    # Delete auction
    auction_result = await db.auctions.delete_one({"id": auction_id})
    
    # Update league status back to 'active' (ready for new auction)
    await db.leagues.update_one(
        {"id": auction["leagueId"]},
        {"$set": {"status": "active"}}
    )
    
    delete_results = {
        "auction": auction_result.deleted_count,
        "bids": bid_result.deleted_count,
        "participants_reset": len(participants)
    }
    
    logger.info(f"Deleted auction {auction_id}: {delete_results}")
    
    return {
        "message": "Auction deleted successfully",
        "deletedData": delete_results
    }

# ===== TIMER COUNTDOWN =====
async def countdown_timer(auction_id: str, end_time: datetime, lot_id: str):
    """Countdown timer with standardized events"""
    
    # Store this timer to prevent duplicates
    if auction_id in active_timers:
        # Cancel existing timer
        active_timers[auction_id].cancel()
    
    # Create current task handle
    current_task = asyncio.current_task()
    active_timers[auction_id] = current_task
    
    try:
        logger.info(f"Starting countdown timer for auction {auction_id}, lot {lot_id}")
        
        # Convert end_time to epoch milliseconds
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        ends_at_ms = int(end_time.timestamp() * 1000)
        
        while True:
            await asyncio.sleep(0.5)  # 500ms tick interval
            
            # Check if we should stop (cancelled or auction ended)
            if auction_id not in active_timers or active_timers[auction_id] != current_task:
                logger.info(f"Timer for auction {auction_id} was cancelled")
                break
            
            # Check if auction still exists and is active
            auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
            if not auction or auction["status"] != "active":
                logger.info(f"Auction {auction_id} no longer active, stopping timer")
                break
            
            # Get updated end time (in case of anti-snipe)
            current_end_time = auction.get("timerEndsAt")
            if not current_end_time:
                logger.info(f"No timer end time for auction {auction_id}, stopping timer")
                break
            
            # Update ends_at_ms if it changed (anti-snipe)
            if current_end_time.tzinfo is None:
                current_end_time = current_end_time.replace(tzinfo=timezone.utc)
            new_ends_at_ms = int(current_end_time.timestamp() * 1000)
            
            if new_ends_at_ms != ends_at_ms:
                # Anti-snipe occurred, update end time
                ends_at_ms = new_ends_at_ms
                logger.info(f"Anti-snipe detected for auction {auction_id}, new end time: {ends_at_ms}")
            
            # Check if timer expired
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            if now_ms >= ends_at_ms:
                # Timer expired, complete the lot
                logger.info(f"Timer expired for auction {auction_id}, completing lot")
                await complete_lot(auction_id)
                break
            
            # Emit timer tick
            timer_data = create_timer_event(lot_id, ends_at_ms)
            logger.debug(f"Emitting tick for lot {lot_id}: seq={timer_data['seq']}")
            
            # Metrics: Track timer ticks
            metrics.increment_timer_tick(auction_id)
            
            await sio.emit('tick', timer_data, room=f"auction:{auction_id}")  # Broadcast to auction room only
    
    except asyncio.CancelledError:
        logger.info(f"Timer for auction {auction_id} was cancelled")
    except Exception as e:
        logger.error(f"Timer error for auction {auction_id}: {str(e)}")
    finally:
        # Clean up timer reference
        if auction_id in active_timers and active_timers[auction_id] == current_task:
            del active_timers[auction_id]
        logger.info(f"Timer cleanup completed for auction {auction_id}")

# ===== SOCKET.IO EVENTS =====
@sio.event
async def connect(sid, environ):
    logger.info(f"🟢 Client connected: {sid}")
    
    # Send connection confirmation
    await sio.emit('connected', {'sid': sid}, room=sid)
    
    # NOTE: Client will emit 'rejoin_rooms' with user context to rejoin their active rooms

@sio.event
async def rejoin_rooms(sid, data):
    """Handle reconnection - rejoin user's active rooms"""
    user_id = data.get('userId')
    if not user_id:
        return
    
    logger.info(f"🔄 Rejoining rooms for user {user_id} (socket {sid})")
    
    # Find all leagues this user participates in
    participants = await db.league_participants.find({"userId": user_id}, {"_id": 0}).to_list(100)
    
    for participant in participants:
        league_id = participant["leagueId"]
        room_name = f"league:{league_id}"
        await sio.enter_room(sid, room_name)
        logger.info(f"  ✅ Rejoined league room: {room_name}")
    
    # Find all active auctions for user's leagues
    league_ids = [p["leagueId"] for p in participants]
    if league_ids:
        auctions = await db.auctions.find({
            "leagueId": {"$in": league_ids},
            "status": "active"
        }).to_list(100)
        
        for auction in auctions:
            auction_id = auction["id"]
            room_name = f"auction:{auction_id}"
            await sio.enter_room(sid, room_name)
            logger.info(f"  ✅ Rejoined auction room: {room_name}")
    
    logger.info(f"🔄 Rejoin complete for user {user_id}")

@sio.event
async def disconnect(sid):
    logger.info(f"🔴 Client disconnected: {sid}")
    metrics.increment_socket_disconnection()

@sio.event
async def join_auction(sid, data):
    """
    Prompt D: Join an auction room - used by AuctionRoom page
    Sends one-shot auction_snapshot to late joiners
    Returns ack with {ok:true, room, roomSize}
    """
    auction_id = data.get('auctionId')
    if not auction_id:
        return {'ok': False, 'error': 'auctionId required'}
    
    # Get user ID from session if available
    try:
        session = await sio.get_session(sid)
        user_id = session.get('userId') if session else None
    except:
        user_id = None
    
    room_name = f"auction:{auction_id}"
    await sio.enter_room(sid, room_name)
    
    # Get room size after join
    room_sockets = sio.manager.rooms.get(f"auction:{auction_id}", set())
    room_size = len(room_sockets)
    
    # JSON log for debugging
    logger.info(json.dumps({
        "event": "join_auction_room",
        "sid": sid,
        "auctionId": auction_id,
        "userId": user_id,
        "roomSize": room_size,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    # Prompt D: Send auction_snapshot for late joiners (one-shot, read-only)
    auction = await db.auctions.find_one({"id": auction_id}, {"_id": 0})
    if auction:
        
        # Get league to determine sport
        league = await db.leagues.find_one({"id": auction["leagueId"]}, {"_id": 0})
        sport_key = league.get("sportKey", "football") if league else "football"
        
        # Get current club if exists
        current_club = None
        if auction.get("currentClubId"):
            if sport_key == "football":
                club = await db.clubs.find_one({"id": auction["currentClubId"]}, {"_id": 0})
            else:
                club = await db.assets.find_one({"id": auction["currentClubId"], "sportKey": sport_key}, {"_id": 0})
            
            if club:
                club.pop('_id', None)
                current_club = Club(**club).model_dump() if sport_key == "football" else club
        
        # Get all bids for current club
        current_bids = []
        if auction.get("currentClubId"):
            bids = await db.bids.find({
                "auctionId": auction_id,
                "clubId": auction["currentClubId"]
            }, {"_id": 0}).to_list(100)
            current_bids = [Bid(**b).model_dump(mode='json') for b in bids]
        
        # Create timer data if timer is active
        timer_data = None
        if auction.get("timerEndsAt") and auction.get("status") == "active":
            timer_end = auction["timerEndsAt"]
            if timer_end.tzinfo is None:
                timer_end = timer_end.replace(tzinfo=timezone.utc)
            ends_at_ms = int(timer_end.timestamp() * 1000)
            
            # Get or create lot ID
            lot_id = auction.get("currentLotId")
            if not lot_id and auction.get("currentLot"):
                lot_id = f"{auction_id}-lot-{auction['currentLot']}"
            
            if lot_id:
                timer_data = create_timer_event(lot_id, ends_at_ms)
                logger.info(f"Auction snapshot timer data - seq: {timer_data['seq']}, endsAt: {timer_data['endsAt']}")
        
        # Get participants
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}, {"_id": 0}).to_list(100)
        
        # Remove MongoDB _id field
        for p in participants:
            p.pop('_id', None)
        
        # Get sold/unsold lists for snapshot
        sold_clubs = []
        unsold_clubs = auction.get("unsoldClubs", [])
        
        # Calculate sold clubs (all bids with winners)
        all_bids = await db.bids.find({"auctionId": auction_id}, {"_id": 0}).to_list(1000)
        sold_club_ids = set()
        for bid in all_bids:
            if bid.get("clubId"):
                sold_club_ids.add(bid["clubId"])
        sold_clubs = list(sold_club_ids)
        
        # Prompt D: Send auction_snapshot with: status, currentLot, currentClubId, currentBid, timerEndsAt, sold/unsold lists
        snapshot_data = {
            'status': auction.get("status"),
            'currentLot': auction.get("currentLot", 0),
            'currentClubId': auction.get("currentClubId"),
            'currentClub': current_club,
            'currentBid': auction.get("currentBid"),
            'currentBidder': auction.get("currentBidder"),
            'timerEndsAt': auction.get("timerEndsAt").isoformat() if auction.get("timerEndsAt") else None,
            'soldClubs': sold_clubs,
            'unsoldClubs': unsold_clubs,
            'seq': auction.get("bidSequence", 0),
            'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants],
            'currentBids': current_bids
        }
        
        # Add timer data if available
        if timer_data:
            snapshot_data['timer'] = timer_data
        
        # Send one-shot snapshot to this client only
        await sio.emit('auction_snapshot', snapshot_data, room=sid)
        logger.info(f"Sent auction_snapshot to {sid} - status: {auction.get('status')}, lot: {auction.get('currentLot')}")
    
    # Prompt D: Return ack
    return {'ok': True, 'room': room_name, 'roomSize': room_size}

@sio.event
async def leave_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        await sio.leave_room(sid, f"auction:{auction_id}")
        logger.info(f"Client {sid} left auction:{auction_id}")

@sio.event
async def join_league(sid, data):
    """
    Prompt D: Join a league room - used by Lobby/LeagueDetail pages
    Returns ack with {ok:true, room, roomSize}
    """
    league_id = data.get('leagueId')
    if not league_id:
        return {'ok': False, 'error': 'leagueId required'}
    
    # Get user ID from session if available
    try:
        session = await sio.get_session(sid)
        user_id = session.get('userId') if session else None
    except:
        user_id = None
    
    room_name = f"league:{league_id}"
    await sio.enter_room(sid, room_name)
    
    # Get room size after join
    room_sockets = sio.manager.rooms.get(f"league:{league_id}", set())
    room_size = len(room_sockets)
    
    # JSON log for debugging
    logger.info(json.dumps({
        "event": "join_league_room",
        "sid": sid,
        "leagueId": league_id,
        "userId": user_id,
        "roomSize": room_size,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    # Get all participants for sync
    participants = await db.league_participants.find({"leagueId": league_id}, {"_id": 0}).to_list(100)
    members = []
    for p in participants:
        members.append({
            'userId': p['userId'],
            'displayName': p['userName'],
            'joinedAt': p['joinedAt'].isoformat() if isinstance(p['joinedAt'], datetime) else p['joinedAt']
        })
    
    # Broadcast to ALL users in league room
    await sio.emit('sync_members', {
        'leagueId': league_id,
        'members': members
    }, room=f"league:{league_id}")
    
    # Send confirmation to the joining user
    await sio.emit('room_joined', {
        'leagueId': league_id,
        'memberCount': len(members)
    }, room=sid)
    
    # Prompt D: Return ack
    return {'ok': True, 'room': room_name, 'roomSize': room_size}

@sio.event
async def leave_league(sid, data):
    """Leave a league room"""
    league_id = data.get('leagueId')
    if not league_id:
        return
    
    room_name = f"league:{league_id}"
    await sio.leave_room(sid, room_name)
    logger.info(f"🟦 Socket {sid} left league room: {room_name}")

# ===== ROOT ENDPOINT =====
@api_router.get("/")
async def root():
    return {"message": "Friends of Pifa API"}

# Debug endpoint to inspect Socket.IO room membership (dev only)
@api_router.get("/debug/rooms/{scope}/{room_id}")
async def debug_room_membership(scope: str, room_id: str):
    """
    Debug endpoint to inspect Socket.IO room membership
    Returns member counts and socket IDs for a given room
    
    **Only available in development environment**
    
    scope: 'league' or 'auction'
    room_id: The ID of the league or auction
    """
    # Guard: Only allow in development environment
    env = os.environ.get('ENV', 'production')
    if env != 'development':
        raise HTTPException(
            status_code=404, 
            detail="Not Found"
        )
    
    room_name = f"{scope}:{room_id}"
    
    # Get all sockets in the room
    room_sockets = sio.manager.rooms.get(room_name, set())
    socket_ids = list(room_sockets)
    
    # Try to get user info for each socket (if session data is available)
    socket_info = []
    for sid in socket_ids:
        user_id = None
        if hasattr(sio, 'get_session'):
            try:
                session = await sio.get_session(sid)
                user_id = session.get('userId') if session else None
            except Exception:
                pass
        
        socket_info.append({
            "sid": sid,
            "userId": user_id
        })
    
    return {
        "room": room_name,
        "scope": scope,
        "id": room_id,
        "memberCount": len(socket_ids),
        "sockets": socket_info,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": env
    }

# Add CORS middleware to main app with production-ready configuration
# Get CORS origins from environment, default to localhost for dev
cors_origins_str = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    allow_credentials=True,
    max_age=600,  # Cache preflight for 10 minutes
)

# Include the router in the main app
app.include_router(api_router)

# Mount Socket.IO - restore original working configuration
# Note: Using 'api/socket.io' to match Kubernetes ingress routing rules
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='api/socket.io'
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()