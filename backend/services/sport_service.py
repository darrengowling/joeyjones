"""
Sport Service - Business logic for sport operations
"""
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import Sport
import os
import logging

logger = logging.getLogger(__name__)

class SportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def list_sports(self, enabled_only: bool = True) -> List[Sport]:
        """
        List available sports, optionally filtering by enabled status
        
        Args:
            enabled_only: If True, filter cricket based on SPORTS_CRICKET_ENABLED flag
        """
        # Get all sports from database
        sports_data = await self.db.sports.find().to_list(100)
        sports = [Sport(**sport) for sport in sports_data]
        
        if not enabled_only:
            return sports
        
        # Filter cricket based on environment flag if enabled_only is True
        cricket_enabled = os.environ.get('SPORTS_CRICKET_ENABLED', 'false').lower() == 'true'
        
        if cricket_enabled:
            logger.info("Cricket enabled - returning all sports")
            return sports
        else:
            # Filter out cricket if not enabled
            filtered_sports = [sport for sport in sports if sport.key != 'cricket']
            logger.info(f"Cricket disabled - returning {len(filtered_sports)} sports (filtered out cricket)")
            return filtered_sports
    
    async def get_sport(self, key: str) -> Optional[Sport]:
        """
        Get a specific sport by key
        
        Args:
            key: Sport key (e.g., 'football', 'cricket')
        """
        sport_data = await self.db.sports.find_one({"key": key})
        if not sport_data:
            return None
        
        return Sport(**sport_data)
    
    async def ui_hints(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get UI hints for a specific sport
        
        Args:
            key: Sport key (e.g., 'football', 'cricket')
        """
        sport = await self.get_sport(key)
        if not sport:
            return None
        
        return sport.uiHints