from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
import socketio
import asyncio
from datetime import datetime, timedelta

from models import (
    User, UserCreate,
    Club,
    League, LeagueCreate,
    LeagueParticipant, LeagueParticipantCreate,
    Auction, AuctionCreate,
    Bid, BidCreate
)
from uefa_clubs import UEFA_CL_CLUBS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Store active timers
active_timers = {}

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
    
    user_obj = User(**input.dict())
    await db.users.insert_one(user_obj.dict())
    return user_obj

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

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
        clubs.append(club.dict())
    
    if clubs:
        await db.clubs.insert_many(clubs)
    
    return {"message": f"Seeded {len(clubs)} UEFA Champions League clubs"}

# ===== LEAGUE ENDPOINTS =====
@api_router.post("/leagues", response_model=League)
async def create_league(input: LeagueCreate):
    league_obj = League(**input.dict())
    await db.leagues.insert_one(league_obj.dict())
    return league_obj

@api_router.get("/leagues", response_model=List[League])
async def get_leagues():
    leagues = await db.leagues.find().to_list(100)
    return [League(**league) for league in leagues]

@api_router.get("/leagues/{league_id}", response_model=League)
async def get_league(league_id: str):
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return League(**league)

# ===== AUCTION ENDPOINTS =====
@api_router.post("/leagues/{league_id}/auction/start")
async def start_auction(league_id: str):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if auction already exists
    existing_auction = await db.auctions.find_one({"leagueId": league_id})
    if existing_auction:
        return {"message": "Auction already exists", "auctionId": existing_auction["id"]}
    
    # Create auction
    auction_create = AuctionCreate(leagueId=league_id)
    auction_obj = Auction(**auction_create.dict())
    await db.auctions.insert_one(auction_obj.dict())
    
    # Update league status
    await db.leagues.update_one(
        {"id": league_id},
        {"$set": {"status": "active"}}
    )
    
    return {"message": "Auction created", "auctionId": auction_obj.id}

@api_router.get("/auction/{auction_id}")
async def get_auction(auction_id: str):
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get all bids for this auction
    bids = await db.bids.find({"auctionId": auction_id}).to_list(1000)
    
    # Get current club if exists
    current_club = None
    if auction.get("currentClubId"):
        club = await db.clubs.find_one({"id": auction["currentClubId"]})
        if club:
            current_club = Club(**club)
    
    return {
        "auction": Auction(**auction),
        "bids": [Bid(**bid) for bid in bids],
        "currentClub": current_club
    }

@api_router.post("/auction/{auction_id}/bid")
async def place_bid(auction_id: str, bid_input: BidCreate):
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
    
    # Create bid
    bid_obj = Bid(
        **bid_input.dict(),
        userName=user["name"],
        userEmail=user["email"]
    )
    await db.bids.insert_one(bid_obj.dict())
    
    # Emit bid via Socket.IO
    await sio.emit('bid_placed', {
        'bid': bid_obj.dict(mode='json'),
        'auctionId': auction_id,
        'clubId': bid_input.clubId
    }, room=f"auction:{auction_id}")
    
    # Check for anti-snipe
    if auction.get("timerEndsAt"):
        time_remaining = (auction["timerEndsAt"] - datetime.utcnow()).total_seconds()
        if time_remaining <= auction["antiSnipeSeconds"] and time_remaining > 0:
            # Extend timer
            new_end_time = datetime.utcnow() + timedelta(seconds=auction["antiSnipeSeconds"])
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {"timerEndsAt": new_end_time}}
            )
            
            await sio.emit('anti_snipe_triggered', {
                'newEndTime': new_end_time.isoformat(),
                'extensionSeconds': auction["antiSnipeSeconds"]
            }, room=f"auction:{auction_id}")
    
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
    
    # Update auction with current lot
    timer_end = datetime.utcnow() + timedelta(seconds=auction["bidTimer"])
    await db.auctions.update_one(
        {"id": auction_id},
        {"$set": {
            "status": "active",
            "currentClubId": club_id,
            "currentLot": auction["currentLot"] + 1,
            "timerEndsAt": timer_end
        }}
    )
    
    # Emit lot start
    await sio.emit('lot_started', {
        'club': Club(**club).dict(),
        'lotNumber': auction["currentLot"] + 1,
        'timerEndsAt': timer_end.isoformat()
    }, room=f"auction:{auction_id}")
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end))
    
    return {"message": "Lot started", "club": Club(**club)}

@api_router.post("/auction/{auction_id}/complete-lot")
async def complete_lot(auction_id: str):
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get winning bid for current club
    if auction.get("currentClubId"):
        bids = await db.bids.find({
            "auctionId": auction_id,
            "clubId": auction["currentClubId"]
        }).sort("amount", -1).to_list(1)
        
        winning_bid = bids[0] if bids else None
        
        # Update auction
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {
                "currentClubId": None,
                "timerEndsAt": None
            }}
        )
        
        # Emit lot complete
        await sio.emit('lot_complete', {
            'clubId': auction["currentClubId"],
            'winningBid': Bid(**winning_bid).dict() if winning_bid else None
        }, room=f"auction:{auction_id}")
        
        return {"message": "Lot completed", "winningBid": winning_bid}
    
    return {"message": "No active lot"}

# ===== TIMER COUNTDOWN =====
async def countdown_timer(auction_id: str, end_time: datetime):
    while True:
        await asyncio.sleep(1)
        
        # Check if auction still exists and is active
        auction = await db.auctions.find_one({"id": auction_id})
        if not auction or auction["status"] != "active":
            break
        
        # Get updated end time (in case of anti-snipe)
        current_end_time = auction.get("timerEndsAt")
        if not current_end_time:
            break
        
        time_remaining = (current_end_time - datetime.utcnow()).total_seconds()
        
        if time_remaining <= 0:
            # Timer expired, complete the lot
            await complete_lot(auction_id)
            break
        
        # Emit timer update
        await sio.emit('timer_update', {
            'timeRemaining': max(0, int(time_remaining))
        }, room=f"auction:{auction_id}")

# ===== SOCKET.IO EVENTS =====
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        sio.enter_room(sid, f"auction:{auction_id}")
        logger.info(f"Client {sid} joined auction:{auction_id}")
        await sio.emit('joined', {'auctionId': auction_id}, room=sid)

@sio.event
async def leave_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        sio.leave_room(sid, f"auction:{auction_id}")
        logger.info(f"Client {sid} left auction:{auction_id}")

@sio.event
async def join_league(sid, data):
    league_id = data.get('leagueId')
    if league_id:
        sio.enter_room(sid, f"league:{league_id}")
        logger.info(f"Client {sid} joined league:{league_id}")

@sio.event
async def leave_league(sid, data):
    league_id = data.get('leagueId')
    if league_id:
        sio.leave_room(sid, f"league:{league_id}")

# ===== ROOT ENDPOINT =====
@api_router.get("/")
async def root():
    return {"message": "UEFA Club Auction API"}

# Include the router in the main app
app.include_router(api_router)

# Mount Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='/socket.io'
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()