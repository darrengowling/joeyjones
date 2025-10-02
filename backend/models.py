from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    email: str

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
    status: str = "pending"  # pending, active, completed
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class LeagueCreate(BaseModel):
    name: str
    commissionerId: str
    budget: float
    minManagers: int = 2
    maxManagers: int = 12
    clubSlots: int = 3

# Auction Models
class Auction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leagueId: str
    status: str = "pending"  # pending, active, paused, completed
    currentLot: int = 0
    currentClubId: Optional[str] = None
    bidTimer: int = 60  # seconds
    antiSnipeSeconds: int = 30
    timerEndsAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    userName: Optional[str] = None
    userEmail: Optional[str] = None

class BidCreate(BaseModel):
    userId: str
    clubId: str
    amount: float
