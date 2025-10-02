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
import uuid
from datetime import datetime, timedelta, timezone

from models import (
    User, UserCreate,
    Club,
    League, LeagueCreate,
    LeagueParticipant, LeagueParticipantCreate,
    Auction, AuctionCreate,
    Bid, BidCreate,
    LeaguePoints
)
from uefa_clubs import UEFA_CL_CLUBS
from scoring_service import recompute_league_scores, get_league_standings

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
@api_router.post("/leagues", response_model=League)
async def create_league(input: LeagueCreate):
    league_obj = League(**input.model_dump())
    await db.leagues.insert_one(league_obj.model_dump())
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

@api_router.post("/leagues/{league_id}/join")
async def join_league(league_id: str, participant_input: LeagueParticipantCreate):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify invite token
    if league["inviteToken"] != participant_input.inviteToken:
        raise HTTPException(status_code=403, detail="Invalid invite token")
    
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
    
    return {"message": "Joined league successfully", "participant": participant}

@api_router.get("/leagues/{league_id}/participants")
async def get_league_participants(league_id: str):
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    return [LeagueParticipant(**p) for p in participants]

@api_router.delete("/leagues/{league_id}")
async def delete_league(league_id: str, user_id: str):
    # Verify league exists
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify user is commissioner
    if league["commissionerId"] != user_id:
        raise HTTPException(status_code=403, detail="Only the commissioner can delete this league")
    
    # Delete league
    await db.leagues.delete_one({"id": league_id})
    
    # Delete all participants
    await db.league_participants.delete_many({"leagueId": league_id})
    
    # Delete league points
    await db.league_points.delete_many({"leagueId": league_id})
    
    # Find and delete associated auction
    auction = await db.auctions.find_one({"leagueId": league_id})
    if auction:
        # Delete all bids for this auction
        await db.bids.delete_many({"auctionId": auction["id"]})
        # Delete auction
        await db.auctions.delete_one({"id": auction["id"]})
    
    return {"message": "League deleted successfully"}

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
    auction_obj = Auction(**auction_create.model_dump())
    await db.auctions.insert_one(auction_obj.model_dump())
    
    # Update league status
    await db.leagues.update_one(
        {"id": league_id},
        {"$set": {"status": "active"}}
    )
    
    # Get all clubs and randomize order
    import random
    all_clubs = await db.clubs.find().to_list(100)
    random.shuffle(all_clubs)
    
    # Auto-start first club
    if all_clubs:
        first_club_id = all_clubs[0]["id"]
        timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction_obj.bidTimer)
        await db.auctions.update_one(
            {"id": auction_obj.id},
            {"$set": {
                "status": "active",
                "currentClubId": first_club_id,
                "currentLot": 1,
                "timerEndsAt": timer_end
            }}
        )
        
        # Emit lot start via Socket.IO
        await sio.emit('lot_started', {
            'club': Club(**all_clubs[0]).model_dump(),
            'lotNumber': 1,
            'timerEndsAt': timer_end.isoformat()
        }, room=f"auction:{auction_obj.id}")
        
        # Start timer countdown
        asyncio.create_task(countdown_timer(auction_obj.id, timer_end))
    
    return {"message": "Auction created and started", "auctionId": auction_obj.id}

@api_router.get("/leagues/{league_id}/auction")
async def get_league_auction(league_id: str):
    """Get the auction for a specific league"""
    auction = await db.auctions.find_one({"leagueId": league_id})
    if not auction:
        raise HTTPException(status_code=404, detail="No auction found for this league")
    return {"auctionId": auction["id"], "status": auction["status"]}

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
    
    # Check if user has enough budget
    if bid_input.amount > participant["budgetRemaining"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient budget. You have ${participant['budgetRemaining']} remaining"
        )
    
    # Create bid
    bid_obj = Bid(
        auctionId=auction_id,
        **bid_input.model_dump(),
        userName=user["name"],
        userEmail=user["email"]
    )
    await db.bids.insert_one(bid_obj.model_dump())
    
    # Emit bid via Socket.IO
    await sio.emit('bid_placed', {
        'bid': bid_obj.model_dump(mode='json'),
        'auctionId': auction_id,
        'clubId': bid_input.clubId
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
    timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
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
        'club': Club(**club).model_dump(),
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
        
        # Remove MongoDB _id from winning bid
        if winning_bid:
            winning_bid.pop('_id', None)
        
        # If there's a winner, update their budget and clubs won
        if winning_bid:
            participant = await db.league_participants.find_one({
                "leagueId": auction["leagueId"],
                "userId": winning_bid["userId"]
            })
            
            if participant:
                # Get all previous winning bids for this user to calculate total spent
                user_winning_clubs = participant.get("clubsWon", [])
                user_total_spent = participant.get("totalSpent", 0.0)
                
                # Add this club and amount
                user_winning_clubs.append(auction["currentClubId"])
                user_total_spent += winning_bid["amount"]
                
                # Get league to calculate remaining budget
                league = await db.leagues.find_one({"id": auction["leagueId"]})
                budget_remaining = league["budget"] - user_total_spent
                
                # Update participant
                await db.league_participants.update_one(
                    {
                        "leagueId": auction["leagueId"],
                        "userId": winning_bid["userId"]
                    },
                    {"$set": {
                        "clubsWon": user_winning_clubs,
                        "totalSpent": user_total_spent,
                        "budgetRemaining": budget_remaining
                    }}
                )
        
        # Get updated participants for broadcast
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
        
        # Remove MongoDB _id field from participants
        for p in participants:
            p.pop('_id', None)
        
        # Emit lot complete
        await sio.emit('lot_complete', {
            'clubId': auction["currentClubId"],
            'winningBid': Bid(**winning_bid).model_dump(mode='json') if winning_bid else None,
            'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants]
        }, room=f"auction:{auction_id}")
        
        # Auto-start next club
        # Get all clubs
        all_clubs = await db.clubs.find().to_list(100)
        
        # Get clubs already auctioned (have bids)
        all_bids = await db.bids.find({"auctionId": auction_id}).to_list(1000)
        auctioned_club_ids = set(bid["clubId"] for bid in all_bids)
        
        # Find next club that hasn't been auctioned
        next_club = None
        for club in all_clubs:
            if club["id"] not in auctioned_club_ids:
                next_club = club
                break
        
        if next_club:
            # Start next lot
            timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction["bidTimer"])
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "currentClubId": next_club["id"],
                    "currentLot": auction["currentLot"] + 1,
                    "timerEndsAt": timer_end
                }}
            )
            
            # Remove _id for serialization
            next_club.pop('_id', None)
            
            # Emit lot start
            await sio.emit('lot_started', {
                'club': Club(**next_club).model_dump(),
                'lotNumber': auction["currentLot"] + 1,
                'timerEndsAt': timer_end.isoformat()
            }, room=f"auction:{auction_id}")
            
            # Start timer countdown
            asyncio.create_task(countdown_timer(auction_id, timer_end))
        else:
            # No more clubs, auction complete
            await db.auctions.update_one(
                {"id": auction_id},
                {"$set": {
                    "status": "completed",
                    "currentClubId": None,
                    "timerEndsAt": None
                }}
            )
            
            await sio.emit('auction_complete', {
                'message': 'All clubs have been auctioned!'
            }, room=f"auction:{auction_id}")
        
        return {"message": "Lot completed", "winningBid": winning_bid}
    
    return {"message": "No active lot"}

# ===== TIMER COUNTDOWN =====
async def countdown_timer(auction_id: str, end_time: datetime):
    """Countdown timer with proper cleanup and debugging"""
    
    # Store this timer to prevent duplicates
    if auction_id in active_timers:
        # Cancel existing timer
        active_timers[auction_id].cancel()
    
    # Create current task handle
    current_task = asyncio.current_task()
    active_timers[auction_id] = current_task
    
    try:
        logger.info(f"Starting countdown timer for auction {auction_id}")
        
        while True:
            await asyncio.sleep(1)
            
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
            
            # Ensure timezone awareness
            if current_end_time.tzinfo is None:
                current_end_time = current_end_time.replace(tzinfo=timezone.utc)
            
            time_remaining = (current_end_time - datetime.now(timezone.utc)).total_seconds()
            
            if time_remaining <= 0:
                # Timer expired, complete the lot
                logger.info(f"Timer expired for auction {auction_id}, completing lot")
                await complete_lot(auction_id)
                break
            
            # Emit timer update
            room_name = f"auction:{auction_id}"
            logger.debug(f"Emitting timer_update to room '{room_name}': {int(time_remaining)}s remaining")
            
            # Get clients in room for debugging
            try:
                room_clients = sio.manager.get_participants(sio.namespace, room_name)
                logger.info(f"Room '{room_name}' has {len(room_clients)} clients: {list(room_clients)}")
            except:
                logger.info(f"Could not get room client count for '{room_name}'")
            
            await sio.emit('timer_update', {
                'timeRemaining': max(0, int(time_remaining))
            }, room=room_name)
    
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
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        room_name = f"auction:{auction_id}"
        sio.enter_room(sid, room_name)
        logger.info(f"Client {sid} joined auction room: {room_name}")
        
        # Test immediate emission to verify room membership
        await sio.emit('test_room_message', {
            'message': f'You have joined room {room_name}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=sid)  # Send to specific client first
        
        logger.info(f"Sent test message to client {sid}")
        
        # Send current auction state for reconnection
        auction = await db.auctions.find_one({"id": auction_id})
        if auction:
            logger.info(f"Sending sync_state to client {sid} for auction {auction_id}")
            
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
            
            # Calculate time remaining
            time_remaining = 0
            if auction.get("timerEndsAt"):
                timer_end = auction["timerEndsAt"]
                if timer_end.tzinfo is None:
                    timer_end = timer_end.replace(tzinfo=timezone.utc)
                time_remaining = max(0, int((timer_end - datetime.now(timezone.utc)).total_seconds()))
                logger.info(f"Calculated time remaining for {auction_id}: {time_remaining}s")
            
            # Get participants
            participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
            
            # Remove MongoDB _id field
            for p in participants:
                p.pop('_id', None)
            
            # Send sync state
            await sio.emit('sync_state', {
                'auction': Auction(**auction).model_dump(mode='json'),
                'currentClub': current_club,
                'currentBids': current_bids,
                'timeRemaining': time_remaining,
                'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants]
            }, room=sid)
        
        await sio.emit('joined', {'auctionId': auction_id}, room=sid)

@sio.event
async def leave_auction(sid, data):
    auction_id = data.get('auctionId')
    if auction_id:
        sio.leave_room(sid, f"auction:{auction_id}")
        logger.info(f"Client {sid} left auction:{auction_id}")

@sio.event
async def join_league_room(sid, data):
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
    return {"message": "Friends of Pifa API"}

# Add CORS middleware to main app
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router in the main app
app.include_router(api_router)

# Mount Socket.IO - this wraps the FastAPI app
# Note: Using 'api/socket.io' to match Kubernetes ingress routing rules
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='api/socket.io'
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()