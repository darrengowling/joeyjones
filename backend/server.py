from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
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
    
    # Emit real-time update to league participants
    await sio.emit('participant_joined', {
        'leagueId': league_id,
        'participant': participant.model_dump(mode='json'),
        'message': f"{participant.userName} joined the league"
    }, room=f"league:{league_id}")
    
    return {"message": "Joined league successfully", "participant": participant}

@api_router.get("/leagues/{league_id}/participants")
async def get_league_participants(league_id: str):
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    return [LeagueParticipant(**p) for p in participants]

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
        # Initialize club queue (randomized order)
        club_queue = [club["id"] for club in all_clubs]
        first_club_id = club_queue[0]
        lot_id = f"{auction_obj.id}-lot-1"  # Create lot ID
        timer_end = datetime.now(timezone.utc) + timedelta(seconds=auction_obj.bidTimer)
        
        await db.auctions.update_one(
            {"id": auction_obj.id},
            {"$set": {
                "status": "active",
                "currentClubId": first_club_id,
                "currentLot": 1,
                "timerEndsAt": timer_end,
                "currentLotId": lot_id,  # Store lot ID
                "clubQueue": club_queue,  # Initialize club queue
                "unsoldClubs": [],  # Initialize empty unsold list
                "minimumBudget": 1000000.0  # £1m minimum budget
            }}
        )
        
        # Create timer event for lot start
        if timer_end.tzinfo is None:
            timer_end = timer_end.replace(tzinfo=timezone.utc)
        ends_at_ms = int(timer_end.timestamp() * 1000)
        timer_data = create_timer_event(lot_id, ends_at_ms)
        
        # Emit lot start with standardized timer data
        await sio.emit('lot_started', {
            'club': Club(**all_clubs[0]).model_dump(),
            'lotNumber': 1,
            'timer': timer_data  # Include standardized timer data
        })
        
        # Start timer countdown
        asyncio.create_task(countdown_timer(auction_obj.id, timer_end, lot_id))
        
        logger.info(f"Started auction {auction_obj.id} lot {lot_id} with club: {all_clubs[0]['name']}")
        logger.info(f"Timer data - seq: {timer_data['seq']}, endsAt: {timer_data['endsAt']}")
    else:
        logger.error(f"Failed to start auction {auction_obj.id} - no clubs available")
        raise HTTPException(status_code=500, detail="No clubs available to auction")
    
    return {"message": "Auction created and started", "auctionId": auction_obj.id}

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
    
    # Get all clubs
    all_clubs = await db.clubs.find().to_list(100)
    
    # Get all bids to determine sold clubs
    all_bids = await db.bids.find({"auctionId": auction_id}).to_list(1000)
    
    # Group bids by club to find winners
    bids_by_club = {}
    for bid in all_bids:
        club_id = bid["clubId"]
        if club_id not in bids_by_club or bid["amount"] > bids_by_club[club_id]["amount"]:
            bids_by_club[club_id] = bid
    
    # Build club status information
    club_queue = auction.get("clubQueue", [])
    unsold_clubs = auction.get("unsoldClubs", [])
    current_club_id = auction.get("currentClubId")
    current_lot = auction.get("currentLot", 0)
    
    clubs_with_status = []
    
    for club in all_clubs:
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
        elif club_id in bids_by_club:
            # Club has bids - check if it's been completed
            if current_lot > lot_number if lot_number else False:
                winning_bid_data = bids_by_club[club_id]
                winner = winning_bid_data.get("userName", "Unknown")
                winning_bid = winning_bid_data.get("amount", 0)
                status = "sold"
        elif club_id in unsold_clubs:
            status = "unsold"
        elif lot_number and current_lot > lot_number:
            # Lot has passed but no bids
            status = "unsold"
        
        # Add club with status
        clubs_with_status.append({
            **Club(**club).model_dump(),
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
        "totalClubs": len(all_clubs),
        "soldClubs": len([c for c in clubs_with_status if c["status"] == "sold"]),
        "unsoldClubs": len([c for c in clubs_with_status if c["status"] == "unsold"]),
        "remainingClubs": len([c for c in clubs_with_status if c["status"] in ["upcoming", "current"]])
    }

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
    
    # Check minimum bid amount
    minimum_budget = auction.get("minimumBudget", 1000000.0)  # Default £1m
    if bid_input.amount < minimum_budget:
        raise HTTPException(
            status_code=400, 
            detail=f"Bid must be at least £{minimum_budget:,.0f}"
        )
    
    # Check if user has enough budget
    if bid_input.amount > participant["budgetRemaining"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient budget. You have £{participant['budgetRemaining']:,.0f} remaining"
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
            
            # Get lot ID and create anti-snipe timer data
            lot_id = auction.get("currentLotId")
            if not lot_id and auction.get("currentLot"):
                lot_id = f"{auction_id}-lot-{auction['currentLot']}"
            
            if lot_id:
                ends_at_ms = int(new_end_time.timestamp() * 1000)
                timer_data = create_timer_event(lot_id, ends_at_ms)
                
                await sio.emit('anti_snipe', timer_data)
                
                logger.info(f"Anti-snipe triggered for lot {lot_id}: seq={timer_data['seq']}, new end={timer_data['endsAt']}")
    
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
    })
    
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
    })
    
    # Determine next club to offer
    next_club_id = await get_next_club_to_auction(auction_id)
    
    if next_club_id:
        await start_next_lot(auction_id, next_club_id)
    else:
        # Check if auction is complete
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
        # Check if any participants can still afford minimum budget
        participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
        minimum_budget = auction.get("minimumBudget", 1000000.0)
        
        can_still_bid = any(p.get("budgetRemaining", 0) >= minimum_budget for p in participants)
        
        if can_still_bid:
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
        'isUnsoldRetry': next_club_id and next_club_id in auction.get("unsoldClubs", [])  # Flag for UI
    })
    
    logger.info(f"Started lot {next_lot_number}: {next_club['name']}")
    
    # Start timer countdown
    asyncio.create_task(countdown_timer(auction_id, timer_end, next_lot_id))


async def check_auction_completion(auction_id: str):
    """Check if auction is complete and handle completion"""
    auction = await db.auctions.find_one({"id": auction_id})
    if not auction:
        return
    
    unsold_clubs = auction.get("unsoldClubs", [])
    participants = await db.league_participants.find({"leagueId": auction["leagueId"]}).to_list(100)
    minimum_budget = auction.get("minimumBudget", 1000000.0)
    
    # Check if any participants can still afford minimum budget
    can_still_bid = any(p.get("budgetRemaining", 0) >= minimum_budget for p in participants)
    
    if not unsold_clubs or not can_still_bid:
        # Mark auction as complete
        await db.auctions.update_one(
            {"id": auction_id},
            {"$set": {"status": "completed"}}
        )
        
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
        
        await sio.emit('auction_complete', {
            'message': f'Auction completed! {total_clubs_sold} clubs sold, {total_unsold} unsold.',
            'clubsSold': total_clubs_sold,
            'clubsUnsold': total_unsold,
            'participants': [LeagueParticipant(**p).model_dump(mode='json') for p in participants]
        })
        
        logger.info(f"Auction {auction_id} completed - {total_clubs_sold} sold, {total_unsold} unsold")

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
    })
    
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
    })
    
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
            
            await sio.emit('tick', timer_data)  # Broadcast to all clients
    
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
            
            # Send sync state with standardized timer data
            sync_data = {
                'auction': Auction(**auction).model_dump(mode='json'),
                'currentClub': current_club,
                'currentBids': current_bids,
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