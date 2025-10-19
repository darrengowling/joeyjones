from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

# Validation helpers for assetsSelected field
def validate_assets_selected(assets: Optional[List[str]]) -> Optional[List[str]]:
    """
    Validate and clean assetsSelected field.
    - Deduplicate while preserving order
    - Trim whitespace from IDs
    - Enforce max size (200)
    - Return None if empty list
    """
    if assets is None:
        return None
    
    if not isinstance(assets, list):
        raise ValueError("assetsSelected must be a list")
    
    # Trim whitespace and deduplicate while preserving order
    seen = set()
    cleaned = []
    for asset_id in assets:
        if not isinstance(asset_id, str):
            raise ValueError("Asset IDs must be strings")
        
        trimmed = asset_id.strip()
        if trimmed and trimmed not in seen:
            seen.add(trimmed)
            cleaned.append(trimmed)
    
    # Enforce max size
    if len(cleaned) > 200:
        raise ValueError("Cannot select more than 200 assets")
    
    # Return None if empty (treat as "include all")
    return cleaned if cleaned else None

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: str

# Sport Models
class Sport(BaseModel):
    key: str
    name: str
    assetType: str
    uiHints: Dict[str, Any]
    auctionTemplate: Dict[str, Any]
    scoringSchema: Dict[str, Any]

# Club Models
class Club(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    uefaId: str
    country: str
    logo: Optional[str] = None

# League Models
class League(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    commissionerId: str
    budget: float
    minManagers: int
    maxManagers: int
    clubSlots: int
    sportKey: str = "football"  # Default to football for backward compatibility
    status: str = "pending"  # pending, active, completed
    inviteToken: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])  # Short token
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scoringOverrides: Optional[Dict[str, Any]] = None  # Custom scoring rules for cricket leagues
    # Prompt D: Timer configuration
    timerSeconds: int = 30  # Default 30s (reduced from 60s)
    antiSnipeSeconds: int = 10  # Default 10s (reduced from 30s)
    # Prompt E: Team management
    assetsSelected: Optional[List[str]] = None  # If null, use sport default; else restrict to selected IDs

# My Competitions Models - Prompt 1
class Fixture(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    sportKey: str
    externalMatchId: Optional[str] = None
    homeAssetId: str  # clubId or playerId depending on sport
    awayAssetId: Optional[str] = None  # null for cricket or BYE fixtures
    startsAt: datetime
    venue: Optional[str] = None
    round: Optional[str] = None
    status: str = "scheduled"  # scheduled|live|final
    source: str = "manual"  # csv|provider|manual
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StandingEntry(BaseModel):
    userId: str
    displayName: str
    points: float = 0.0
    assetsOwned: List[str] = []
    tiebreakers: Dict[str, float] = Field(default_factory=lambda: {
        "goals": 0, "wins": 0, "runs": 0, "wickets": 0
    })

class Standing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    sportKey: str
    table: List[StandingEntry] = []
    lastComputedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FixtureImport(BaseModel):
    startsAt: str
    homeAssetExternalId: str
    awayAssetExternalId: Optional[str] = None
    venue: Optional[str] = None
    round: Optional[str] = None
    externalMatchId: Optional[str] = None

class LeagueCreate(BaseModel):
    name: str
    commissionerId: str
    budget: float = 500000000.0  # Default £500m budget
    minManagers: int = 2
    maxManagers: int = 8
    clubSlots: int = 3
    sportKey: str = "football"  # Default to football
    # Prompt D: Timer configuration in league creation
    timerSeconds: int = 30  # Default 30s
    antiSnipeSeconds: int = 10  # Default 10s

# League Participant Models
class LeagueParticipant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    userId: str
    userName: str
    userEmail: str
    budgetRemaining: float
    clubsWon: List[str] = []
    totalSpent: float = 0.0
    joinedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueParticipantCreate(BaseModel):
    userId: str
    inviteToken: str

# Auction Models
class Auction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    status: str = "pending"  # pending, active, paused, completed
    currentLot: int = 0
    currentClubId: Optional[str] = None
    currentLotId: Optional[str] = None  # Track lot ID for timer events
    bidTimer: int = 60  # seconds
    antiSnipeSeconds: int = 30
    timerEndsAt: Optional[datetime] = None
    clubQueue: List[str] = []  # Queue of club IDs to auction
    unsoldClubs: List[str] = []  # Clubs that went unsold, will be re-offered
    minimumBudget: float = 1000000.0  # £1m minimum budget per user
    pausedRemainingTime: Optional[float] = None  # Stored time when paused
    pausedAt: Optional[datetime] = None  # When auction was paused
    currentBid: Optional[float] = None  # Current highest bid amount
    currentBidder: Optional[Dict[str, Any]] = None  # Current bidder info {userId, displayName}
    bidSequence: int = 0  # Monotonic sequence number for bid updates
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuctionCreate(BaseModel):
    leagueId: str
    bidTimer: int = 30  # Default 30s (Prompt D)
    antiSnipeSeconds: int = 10  # Default 10s (Prompt D)

# Bid Models
class Bid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    auctionId: str
    userId: str
    clubId: str
    amount: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    userName: Optional[str] = None
    userEmail: Optional[str] = None

class BidCreate(BaseModel):
    userId: str
    amount: float

# League Points Models (for scoring)
class LeaguePoints(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    clubId: str
    clubName: str
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goalsScored: int = 0
    goalsConceded: int = 0
    totalPoints: int = 0  # Calculated: (wins * 3) + (draws * 1) + (goalsScored * 1)
    lastUpdated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
