from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

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
    bidTimer: int = 60
    antiSnipeSeconds: int = 30

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
