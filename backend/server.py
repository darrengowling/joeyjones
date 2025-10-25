from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Depends, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

from models import (
    User, UserCreate,
    Club,
    Sport,
    League, LeagueCreate,
    LeagueParticipant, LeagueParticipantCreate,
    Auction, AuctionCreate,
    Bid, BidCreate,
    LeaguePoints,
    Fixture, Standing, StandingEntry
)
from services.sport_service import SportService
from services.asset_service import AssetService
from services.scoring.cricket import get_cricket_points
from uefa_clubs import UEFA_CL_CLUBS
from scoring_service import recompute_league_scores, get_league_standings

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Standings indexes  
        await db.standings.create_index([("leagueId", 1)], unique=True)
        
        logger.info("✅ My Competitions database indexes created")
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
    existing = await db.users.find_one({"email": input.email})
    if existing:
        return User(**existing)
    
    user_obj = User(**input.model_dump())
    await db.users.insert_one(user_obj.model_dump())
    return user_obj

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/auth/magic-link")
async def send_magic_link(email_input: dict):
    """
    Placeholder for magic-link authentication
    In production: Generate token, send email with link
    For pilot: Just return the token
    """
    email = email_input.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Check if user exists, create if not
    user = await db.users.find_one({"email": email})
    if not user:
        # For pilot, create user with email as name
        user_create = UserCreate(name=email.split("@")[0], email=email)
        user_obj = User(**user_create.model_dump())
        await db.users.insert_one(user_obj.model_dump())
        user = user_obj.model_dump()
    
    # Generate magic token (in production, store and send via email)
    magic_token = str(uuid.uuid4())[:12]
    
    # For pilot: Return token directly
    return {
        "message": "Magic link generated (pilot mode)",
        "email": email,
        "token": magic_token,
        "user": User(**user),
        "note": "In production, this would be sent via email"
    }

@api_router.post("/auth/verify-magic-link")
async def verify_magic_link(token_input: dict):
    """
    Placeholder for magic-link verification
    For pilot: Just validate email and return user
    """
    email = token_input.get("email")
    token = token_input.get("token")
    
    if not email or not token:
        raise HTTPException(status_code=400, detail="Email and token required")
    
    # For pilot: Just find user by email
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "Magic link verified (pilot mode)",
        "user": User(**user)
    }

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
async def get_league_assets(league_id: str, search: Optional[str] = None, page: int = 1, pageSize: int = 50):
    """Get assets for a specific league based on its sportKey"""
    # Get league to determine sportKey
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")  # Default to football for backward compatibility
    return await asset_service.list_assets(sport_key, search, page, pageSize)

# ===== CLUB ENDPOINTS =====
@api_router.get("/clubs", response_model=List[Club])
async def get_clubs():
    clubs = await db.clubs.find().to_list(100)
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
@api_router.post("/leagues", response_model=League, dependencies=[get_rate_limiter(times=5, seconds=300)])
async def create_league(input: LeagueCreate):
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
        raise HTTPException(status_code=400, detail=str(e))
    
    league_obj = League(**input.model_dump())
    await db.leagues.insert_one(league_obj.model_dump())
    
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

@api_router.get("/leagues/{league_id}", response_model=League)
async def get_league(league_id: str):
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return League(**league)

@api_router.post("/leagues/{league_id}/join")
async def join_league(league_id: str, participant_input: LeagueParticipantCreate):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id})
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
    })
    if existing:
        return {"message": "Already joined", "participant": LeagueParticipant(**existing)}
    
    # Check max managers limit
    participant_count = await db.league_participants.count_documents({"leagueId": league_id})
    if participant_count >= league["maxManagers"]:
        raise HTTPException(status_code=400, detail="League is full")
    
    # Get user details
    user = await db.users.find_one({"id": participant_input.userId})
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
    all_participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
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
    
    return {"message": "Joined league successfully", "participant": participant}

@api_router.get("/leagues/{league_id}/participants")
async def get_league_participants(league_id: str):
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    return [LeagueParticipant(**p) for p in participants]

@api_router.get("/leagues/{league_id}/members")
async def get_league_members(league_id: str):
    """Prompt A: Get ordered league members for real-time updates"""
    participants = await db.league_participants.find({"leagueId": league_id}).sort("joinedAt", 1).to_list(100)
    
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
    participants = await db.league_participants.find({"userId": userId}).to_list(100)
    league_ids = [p["leagueId"] for p in participants]
    
    if not league_ids:
        return []
    
    # Get league details
    leagues = await db.leagues.find({"id": {"$in": league_ids}}).to_list(100)
    
    competitions = []
    for league in leagues:
        # Determine league status
        auction = await db.auctions.find_one({"leagueId": league["id"]})
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
            
            # Get asset details
            asset = await db.clubs.find_one({"id": asset_id})
            
            if asset:
                assets_owned.append({
                    "id": asset_id,
                    "name": asset.get("clubName") or asset.get("name", "Unknown Team"),
                    "price": winning_bid["amount"] if winning_bid else 0
                })
            else:
                # Fallback if asset not found
                assets_owned.append({
                    "id": asset_id,
                    "name": "Team",
                    "price": winning_bid["amount"] if winning_bid else 0
                })
        
        # Get manager count
        manager_count = await db.league_participants.count_documents({"leagueId": league["id"]})
        
        # Get next fixture
        next_fixture = await db.fixtures.find_one({
            "leagueId": league["id"],
            "startsAt": {"$gte": datetime.now(timezone.utc)},
            "status": "scheduled"
        }, sort=[("startsAt", 1)])
        
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
    
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get commissioner details
    commissioner = await db.users.find_one({"id": league["commissionerId"]})
    
    # Get user's roster with enriched details (name and price)
    participant = await db.league_participants.find_one({"leagueId": league_id, "userId": userId})
    asset_ids = participant.get("clubsWon", []) if participant else []
    
    # Enrich roster with asset names and prices
    user_roster = []
    auction = await db.auctions.find_one({"leagueId": league_id})
    
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
            asset = await db.clubs.find_one({"id": asset_id})
        else:
            asset = await db.assets.find_one({"id": asset_id, "sportKey": sport_key})
        
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
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
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
                asset = await db.clubs.find_one({"id": asset_id})
            else:
                asset = await db.assets.find_one({"id": asset_id, "sportKey": sport_key})
            
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
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Always get current participants to ensure standings reflect all members
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    
    # Check if standings exist
    standing = await db.standings.find_one({"leagueId": league_id})
    
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

@api_router.get("/leagues/{league_id}/fixtures")
async def get_league_fixtures(league_id: str, status: Optional[str] = None, page: int = 1, limit: int = 50):
    """Get league fixtures with optional filtering - Prompt 6: Feature flag + Pagination"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    query = {"leagueId": league_id}
    if status:
        query["status"] = status
    
    # Prompt 6: Pagination with page support
    skip = (page - 1) * limit
    fixtures = await db.fixtures.find(query).sort("startsAt", 1).skip(skip).limit(limit).to_list(limit)
    
    return [Fixture(**fixture).model_dump(mode='json') for fixture in fixtures]

@api_router.post("/leagues/{league_id}/fixtures/import-csv")
async def import_fixtures_csv(league_id: str, file: UploadFile = File(...), commissionerId: str = None):
    """Import fixtures from CSV - Commissioner only - Prompt 6"""
    # Prompt 6: Feature flag check
    if not FEATURE_MY_COMPETITIONS:
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Verify league exists and get commissioner
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Prompt 6: Permissions - lock CSV import to commissioner; return 403 otherwise
    if not commissionerId or league["commissionerId"] != commissionerId:
        raise HTTPException(
            status_code=403, 
            detail="Only the league commissioner can import fixtures"
        )
    
    # Prompt 6: Validation - refuse import when auction is not auction_complete
    auction = await db.auctions.find_one({"leagueId": league_id})
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
            
            if not starts_at_str or not home_external_id:
                continue  # Skip invalid rows
            
            # Parse datetime
            try:
                starts_at = datetime.fromisoformat(starts_at_str.replace('Z', '+00:00'))
            except ValueError:
                continue  # Skip invalid dates
            
            # Look up asset IDs
            if sport_key == "football":
                home_asset = await db.clubs.find_one({"uefaId": home_external_id})
                away_asset = await db.clubs.find_one({"uefaId": away_external_id}) if away_external_id else None
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

@api_router.put("/leagues/{league_id}/assets")
async def update_league_assets(league_id: str, asset_ids: List[str]):
    """Prompt 1: Update selected assets for league (commissioner only)"""
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if auction has started (block edits after start)
    existing_auction = await db.auctions.find_one({"leagueId": league_id})
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
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    sport_key = league.get("sportKey", "football")
    
    if sport_key == "football":
        # Get all clubs
        assets = await db.clubs.find().to_list(100)
        return [{"id": asset["id"], "name": asset["name"], "country": asset.get("country")} for asset in assets]
    else:
        # Get assets for other sports
        assets = await db.assets.find({"sportKey": sport_key}).to_list(100)
        return [{"id": asset["id"], "name": asset["name"], "meta": asset.get("meta")} for asset in assets]

@api_router.delete("/leagues/{league_id}")
async def delete_league(league_id: str, commissioner_id: str = None):
    """Delete a league and all associated data - only commissioner can do this"""
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify commissioner permissions (for now, skip verification)
    # In production, you'd verify that commissioner_id matches league["commissionerId"]
    
    # Check if auction is active
    existing_auction = await db.auctions.find_one({"leagueId": league_id})
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
    league = await db.leagues.find_one({"id": league_id})
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
    updated_league = await db.leagues.find_one({"id": league_id})
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
    league = await db.leagues.find_one({"id": league_id})
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
        sport = await db.sports.find_one({"key": "cricket"})
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
        
        for row in csv_reader:
            try:
                match_id = row["matchId"].strip()
                player_external_id = row["playerExternalId"].strip()
                
                if not match_id or not player_external_id:
                    logger.warning(f"Skipping row with empty matchId or playerExternalId: {row}")
                    continue
                
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
            # Calculate total points for this player across all matches
            pipeline = [
                {"$match": {"leagueId": league_id, "playerExternalId": player_external_id}},
                {"$group": {"_id": None, "totalPoints": {"$sum": "$points"}}}
            ]
            
            result = await db.league_stats.aggregate(pipeline).to_list(1)
            total_points = result[0]["totalPoints"] if result else 0
            
            # Update or create leaderboard entry
            await db.cricket_leaderboard.update_one(
                {"leagueId": league_id, "playerExternalId": player_external_id},
                {
                    "$set": {
                        "leagueId": league_id,
                        "playerExternalId": player_external_id,
                        "totalPoints": total_points,
                        "updatedAt": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            leaderboard_results.append({"playerExternalId": player_external_id, "totalPoints": total_points})
        
        return {
            "message": "Cricket scoring data ingested successfully",
            "processedRows": processed_rows,
            "updatedRows": updated_rows,
            "leaderboardUpdates": len(leaderboard_updates),
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
    league = await db.leagues.find_one({"id": league_id})
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
    league = await db.leagues.find_one({"id": league_id})
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
    existing_auction = await db.auctions.find_one({"leagueId": league_id})
    if existing_auction:
        return {"message": "Auction already exists", "auctionId": existing_auction["id"]}
    
    # Create auction with league timer settings (Prompt D)
    auction_create = AuctionCreate(
        leagueId=league_id,
        bidTimer=league.get("timerSeconds", 30),
        antiSnipeSeconds=league.get("antiSnipeSeconds", 10)
    )
    auction_obj = Auction(**auction_create.model_dump())
    await db.auctions.insert_one(auction_obj.model_dump())
    
    # Update league status
    await db.leagues.update_one(
        {"id": league_id},
        {"$set": {"status": "active"}}
    )
    
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
            all_assets = await db.clubs.find().to_list(100)
        else:
            all_assets = await db.assets.find({"sportKey": sport_key}).to_list(100)
        
        logger.info("auction.seed_queue", extra={
            "leagueId": league_id,
            "mode": "all",
            "selected_count": len(all_assets),
            "sportKey": sport_key,
            "feature_enabled": FEATURE_ASSET_SELECTION
        })
    
    random.shuffle(all_assets)
    
    # Prompt B: Create auction in "waiting" state, prepare queue only (no lots yet)
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
        
        # Emit to LEAGUE room (not auction room - users haven't entered yet)
        await sio.emit('league_status_changed', {
            'leagueId': league_id,
            'status': 'auction_created',
            'auctionId': auction_obj.id
        }, room=f"league:{league_id}")
        
        logger.info(f"Created auction {auction_obj.id} in waiting state with {len(asset_queue)} assets queued")
    else:
        logger.error(f"Failed to create auction {auction_obj.id} - no assets available")
        raise HTTPException(status_code=500, detail="No assets available to auction")
    
    return {"auctionId": auction_obj.id, "status": "waiting"}

@api_router.get("/leagues/{league_id}/state")
async def get_league_state(league_id: str):
    """
    Prompt B: Lightweight endpoint to get league status and active auction
    Returns: {leagueId, status, activeAuctionId (if exists)}
    """
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check for active auction
    auction = await db.auctions.find_one({"leagueId": league_id})
    
    return {
        "leagueId": league_id,
        "status": league.get("status", "pending"),
        "activeAuctionId": auction["id"] if auction else None
    }

@api_router.post("/auction/{auction_id}/begin")
async def begin_auction(auction_id: str, commissionerId: str):
    """Everton Bug Fix: Commissioner manually starts the auction after all users have joined"""
    # Verify auction exists and is waiting
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction["status"] != "waiting":
        raise HTTPException(status_code=400, detail=f"Auction is not in waiting state (current: {auction['status']})")
    
    # Verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if league["commissionerId"] != commissionerId:
        raise HTTPException(status_code=403, detail="Only the commissioner can start the auction")
    
    # Get sport key for asset retrieval
    sport_key = league.get("sportKey", "football")
    
    # Get the club queue
    asset_queue = auction.get("clubQueue", [])
    if not asset_queue:
        raise HTTPException(status_code=400, detail="No assets in auction queue")
    
    # Get first asset details
    first_asset_id = asset_queue[0]
    if sport_key == "football":
        first_asset = await db.clubs.find_one({"id": first_asset_id})
    else:
        first_asset = await db.assets.find_one({"id": first_asset_id, "sportKey": sport_key})
    
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
    auction = await db.auctions.find_one({"leagueId": league_id})
    if not auction:
        raise HTTPException(status_code=404, detail="No auction found for this league")
    return {"auctionId": auction["id"], "status": auction["status"]}

@api_router.get("/auction/{auction_id}/clubs")
async def get_auction_clubs(auction_id: str):
    """Get all clubs in the auction with their status (upcoming/current/sold/unsold)"""
    auction = await db.auctions.find_one({"id": auction_id})
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
    league = await db.leagues.find_one({"id": auction["leagueId"]})
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
    all_bids = await db.bids.find({"auctionId": auction_id}).to_list(1000)
    
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get all bids for this auction
    bids = await db.bids.find({"auctionId": auction_id}).to_list(1000)
    
    # Get current asset if exists
    current_asset = None
    if auction.get("currentClubId"):
        # First get the league to determine sport
        league = await db.leagues.find_one({"id": auction["leagueId"]})
        sport_key = league.get("sportKey", "football") if league else "football"
        
        if sport_key == "football":
            # Get from clubs collection for football
            asset = await db.clubs.find_one({"id": auction["currentClubId"]})
            if asset:
                current_asset = Club(**asset)
        else:
            # Get from assets collection for other sports
            asset = await db.assets.find_one({"id": auction["currentClubId"]})
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

@api_router.post("/auction/{auction_id}/bid", dependencies=[get_rate_limiter(times=40, seconds=60)])
async def place_bid(auction_id: str, bid_input: BidCreate):
    # Metrics: Track bid processing time
    start_time = time.time()
    
    # Verify auction exists and is active
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction["status"] != "active":
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # Get user details
    user = await db.users.find_one({"id": bid_input.userId})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get league
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get participant to check budget
    participant = await db.league_participants.find_one({
        "leagueId": auction["leagueId"],
        "userId": bid_input.userId
    })
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
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
    auction_state = {
        "lots_sold": sum(1 for p in participants for c in p.get("clubsWon", [])),
        "current_lot": auction.get("currentLot", 0),
        "total_lots": len(auction.get("clubQueue", [])),
        "unsold_count": len(auction.get("unsoldClubs", []))
    }
    status = compute_auction_status(league, participants, auction_state)
    logger.info(f"🔍 AUCTION_STATUS after bid: {json.dumps(status)}")
    
    # CRITICAL FIX: Check if auction should complete after this bid
    # This handles the case where all rosters just became full
    await check_auction_completion(auction_id)
    
    return {"message": "Bid placed successfully", "bid": bid_obj}

@api_router.post("/auction/{auction_id}/start-lot/{club_id}")
async def start_lot(auction_id: str, club_id: str):
    # Verify auction and club exist
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    club = await db.clubs.find_one({"id": club_id})
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # DIAGNOSTIC: Check completion status before starting next lot
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    current_club_id = auction.get("currentClubId")
    if not current_club_id:
        raise HTTPException(status_code=400, detail="No current club to complete")
    
    # Get bids for current club
    bids = await db.bids.find({
        "auctionId": auction_id,
        "clubId": current_club_id
    }).sort("amount", -1).to_list(1)
    
    winning_bid = bids[0] if bids else None
    
    # Remove MongoDB _id from winning bid
    if winning_bid:
        winning_bid.pop('_id', None)
    
    # Handle sold vs unsold scenarios
    if winning_bid:
        # CLUB SOLD - Update winner's budget and clubs
        participant = await db.league_participants.find_one({
            "leagueId": auction["leagueId"],
            "userId": winning_bid["userId"]
        })
        
        if participant:
            user_winning_clubs = participant.get("clubsWon", [])
            user_total_spent = participant.get("totalSpent", 0.0)
            
            # Add this club and amount
            user_winning_clubs.append(current_club_id)
            user_total_spent += winning_bid["amount"]
            
            # Calculate remaining budget
            league = await db.leagues.find_one({"id": auction["leagueId"]})
            budget_remaining = league["budget"] - user_total_spent
            
            # Update participant
            await db.league_participants.update_one(
                {"leagueId": auction["leagueId"], "userId": winning_bid["userId"]},
                {"$set": {
                    "clubsWon": user_winning_clubs,
                    "totalSpent": user_total_spent,
                    "budgetRemaining": budget_remaining
                }}
            )
            
        logger.info(f"Club sold - {current_club_id} to {winning_bid['userId']} for £{winning_bid['amount']:,}")
    
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
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
    for p in participants:
        p.pop('_id', None)
    
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
        'winningBid': Bid(**winning_bid).model_dump(mode='json') if winning_bid else None,
        'unsold': not bool(winning_bid),  # Flag if club went unsold
        'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants],
        **sold_data
    }, room=f"auction:{auction_id}")
    
    # ALWAYS evaluate completion first (before considering next lot)
    # Pass final club info to ensure frontend gets complete state
    await check_auction_completion(
        auction_id, 
        final_club_id=current_club_id,
        final_winning_bid=winning_bid
    )
    
    # Re-read auction status idempotently (single source of truth)
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction or auction.get("status") != "active":
        # Auction already completed by check_auction_completion
        logger.info(f"auction.completion_halted", extra={
            "auction_id": auction_id,
            "status": auction.get("status") if auction else "not_found"
        })
        return  # Do NOT start another lot
    
    # Only now consider starting the next lot
    next_club_id = await get_next_club_to_auction(auction_id)
    
    logger.info(f"auction.next_lot_decision", extra={
        "auction_id": auction_id,
        "will_start_next": bool(next_club_id and auction.get('status') == 'active'),
        "next_club_id": next_club_id if next_club_id else None
    })
    
    if next_club_id:
        await start_next_lot(auction_id, next_club_id)
    else:
        # Also call completion here to handle "no more clubs" end case
        await check_auction_completion(auction_id)


async def get_next_club_to_auction(auction_id: str) -> Optional[str]:
    """Get the next club to auction, considering queue and unsold clubs"""
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        return None
    
    club_queue = auction.get("clubQueue", [])
    unsold_clubs = auction.get("unsoldClubs", [])
    current_lot = auction.get("currentLot", 0)
    
    # Check if we're still in the initial round
    if current_lot < len(club_queue):
        # Return next club in initial queue
        return club_queue[current_lot]  # currentLot is 1-indexed, but we want next club
    
    # Initial round complete - check for unsold clubs
    if unsold_clubs:
        # Check if any participants can still bid (budget + roster slots) - Prompt C
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
        league = await db.leagues.find_one({"id": auction["leagueId"]})
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        return
    
    # Get club details
    next_club = await db.clubs.find_one({"id": next_club_id})
    if not next_club:
        logger.error(f"Club not found: {next_club_id}")
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
            "timerEndsAt": timer_end
        }}
    )
    
    # Remove _id for serialization
    next_club.pop('_id', None)
    
    # Create timer data
    if timer_end.tzinfo is None:
        timer_end = timer_end.replace(tzinfo=timezone.utc)
    ends_at_ms = int(timer_end.timestamp() * 1000)
    timer_data = create_timer_event(next_lot_id, ends_at_ms)
    
    # Emit lot start
    await sio.emit('lot_started', {
        'club': Club(**next_club).model_dump(),
        'lotNumber': next_lot_number,
        'timer': timer_data,
        'isUnsoldRetry': next_club_id and next_club_id in (auction.get("unsoldClubs", []))  # Flag for UI
    }, room=f"auction:{auction_id}")
    
    logger.info(f"Started lot {next_lot_number}: {next_club['name']}")
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end, next_lot_id))


async def check_auction_completion(auction_id: str, final_club_id: str = None, final_winning_bid: dict = None):
    """Check if auction is complete and handle completion (idempotent)"""
    logger.info(f"🔍 check_auction_completion CALLED for {auction_id}")
    
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        logger.warning(f"❌ check_auction_completion: Auction {auction_id} not found")
        return
    
    # Idempotent: If already completed, do nothing (return fast)
    if auction.get("status") == "completed":
        logger.info(f"✅ Auction {auction_id} already completed - returning")
        return
    
    # Get league info for roster limits
    league = await db.leagues.find_one({"id": auction["leagueId"]})
    if not league:
        logger.warning(f"❌ check_auction_completion: League not found for auction {auction_id}")
        return
    
    unsold_clubs = auction.get("unsoldClubs", [])
    club_queue = auction.get("clubQueue", [])
    current_lot = auction.get("currentLot", 0)
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
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
    clubs_remaining = (current_lot < len(club_queue)) or len(unsold_clubs) > 0
    
    # Auction should end if: no clubs remaining, no eligible bidders, or all managers are full
    should_complete = not clubs_remaining or not eligible_bidders or all_managers_full
    
    # Structured logging
    logger.info("auction.completion_check", extra={
        "auction_id": auction_id,
        "remaining_demand": remaining_demand,
        "status": auction.get("status"),
        "all_managers_full": all_managers_full,
        "eligible_bidders": len(eligible_bidders),
        "clubs_remaining": clubs_remaining,
        "should_complete": should_complete
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
        league = await db.leagues.find_one({"id": auction["leagueId"]})
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
            existing_standing = await db.standings.find_one({"leagueId": auction["leagueId"]})
            if not existing_standing:
                table = []
                for participant in participants:
                    table.append({
                        "userId": participant["userId"],
                        "displayName": participant["userName"],
                        "points": 0.0,
                        "assetsOwned": participant.get("clubsWon", []),
                        "tiebreakers": {"goals": 0, "wins": 0, "runs": 0, "wickets": 0}
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]})
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]})
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
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get league to verify commissioner
    league = await db.leagues.find_one({"id": auction["leagueId"]})
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
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
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
            auction = await db.auctions.find_one({"id": auction_id})
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
    participants = await db.league_participants.find({"userId": user_id}).to_list(100)
    
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
    """Join an auction room - used by AuctionRoom page"""
    auction_id = data.get('auctionId')
    if not auction_id:
        return
    
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
    
    # Send current auction state for reconnection
    auction = await db.auctions.find_one({"id": auction_id})
    if auction:
        
        # Get current club if exists
        current_club = None
        if auction.get("currentClubId"):
            club = await db.clubs.find_one({"id": auction["currentClubId"]})
            if club:
                current_club = Club(**club).model_dump()
        
        # Get all bids for current club
        current_bids = []
        if auction.get("currentClubId"):
            bids = await db.bids.find({
                "auctionId": auction_id,
                "clubId": auction["currentClubId"]
            }).to_list(100)
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
                logger.info(f"Sync state timer data - seq: {timer_data['seq']}, endsAt: {timer_data['endsAt']}")
        
        # Get participants
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
        
        # Remove MongoDB _id field
        for p in participants:
            p.pop('_id', None)
        
        # Send sync state with standardized timer data (Prompt B: Include current bid info)
        sync_data = {
            'auction': Auction(**auction).model_dump(mode='json'),
            'currentClub': current_club,
            'currentBids': current_bids,
            'currentBid': auction.get("currentBid"),
            'currentBidder': auction.get("currentBidder"),
            'seq': auction.get("bidSequence", 0),
            'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants]
        }
        
        # Add timer data if available
        if timer_data:
            sync_data['timer'] = timer_data
        
        await sio.emit('sync_state', sync_data, room=sid)
    
    await sio.emit('joined', {'auctionId': auction_id}, room=sid)

@sio.event
async def leave_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        await sio.leave_room(sid, f"auction:{auction_id}")
        logger.info(f"Client {sid} left auction:{auction_id}")

@sio.event
async def join_league(sid, data):
    """Join a league room - used by Lobby/LeagueDetail pages"""
    league_id = data.get('leagueId')
    if not league_id:
        return
    
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
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
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