"""
Asset Service - Business logic for asset operations (clubs, players, etc.)
"""
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import Club
import logging
import math

logger = logging.getLogger(__name__)

class AssetService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def list_assets(self, sport_key: str, search: Optional[str] = None, 
                         page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        List assets for a specific sport with pagination and optional search
        
        Args:
            sport_key: Sport key ('football', 'cricket', etc.)
            search: Optional search term to filter assets
            page: Page number (1-based)
            page_size: Number of items per page
        """
        # Validate page parameters
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # Cap at 100 items per page
        
        skip = (page - 1) * page_size
        
        if sport_key == 'football':
            # For football, return clubs
            return await self._list_clubs(search, page, page_size, skip)
        elif sport_key == 'cricket':
            # For cricket, return empty until players are seeded
            return {
                "assets": [],
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "total": 0,
                    "totalPages": 0,
                    "hasNext": False,
                    "hasPrev": False
                }
            }
        else:
            logger.warning(f"Unknown sport key: {sport_key}")
            return {
                "assets": [],
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "total": 0,
                    "totalPages": 0,
                    "hasNext": False,
                    "hasPrev": False
                }
            }
    
    async def _list_clubs(self, search: Optional[str], page: int, page_size: int, skip: int) -> Dict[str, Any]:
        """List football clubs with pagination and search"""
        # Build query
        query = {}
        if search:
            # Case-insensitive search in name and country
            query = {
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"country": {"$regex": search, "$options": "i"}}
                ]
            }
        
        # Get total count for pagination
        total = await self.db.clubs.count_documents(query)
        
        # Get clubs for current page
        clubs_data = await self.db.clubs.find(query).skip(skip).limit(page_size).to_list(page_size)
        clubs = [Club(**club) for club in clubs_data]
        
        # Calculate pagination info
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "assets": [club.model_dump() for club in clubs],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasNext": has_next,
                "hasPrev": has_prev
            }
        }