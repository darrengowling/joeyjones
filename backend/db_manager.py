"""
Database Connection Manager with Auto-Reconnection

Provides resilient MongoDB connection handling with:
- Automatic reconnection on connection loss
- Exponential backoff retry logic
- Health monitoring
- Graceful degradation

Created: February 2, 2026
Purpose: Prevent production outages from transient connection issues
"""

import asyncio
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB connection with automatic reconnection capabilities.
    
    Features:
    - Connection health monitoring
    - Automatic reconnection with exponential backoff
    - Connection state tracking
    - Graceful error handling
    """
    
    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        max_retry_attempts: int = 5,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        connection_timeout_ms: int = 10000,
        server_selection_timeout_ms: int = 10000
    ):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.max_retry_attempts = max_retry_attempts
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.connection_timeout_ms = connection_timeout_ms
        self.server_selection_timeout_ms = server_selection_timeout_ms
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected: bool = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Get the MongoDB client."""
        return self._client
    
    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get the database instance."""
        return self._db
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._is_connected
    
    async def connect(self) -> bool:
        """
        Establish connection to MongoDB with retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        async with self._lock:
            return await self._connect_with_retry()
    
    async def _connect_with_retry(self) -> bool:
        """Internal connection method with exponential backoff retry."""
        retry_delay = self.initial_retry_delay
        
        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                logger.info(f"🔌 MongoDB connection attempt {attempt}/{self.max_retry_attempts}...")
                
                # Create client with timeout settings
                self._client = AsyncIOMotorClient(
                    self.mongo_url,
                    connectTimeoutMS=self.connection_timeout_ms,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    retryWrites=True,
                    retryReads=True
                )
                
                # Get database reference
                self._db = self._client[self.db_name]
                
                # Verify connection with ping
                await self._db.command('ping')
                
                self._is_connected = True
                logger.info(f"✅ MongoDB connected successfully on attempt {attempt}")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
                logger.warning(f"⚠️ MongoDB connection attempt {attempt} failed: {e}")
                self._is_connected = False
                
                if attempt < self.max_retry_attempts:
                    logger.info(f"⏳ Retrying in {retry_delay:.1f} seconds...")
                    await asyncio.sleep(retry_delay)
                    # Exponential backoff with cap
                    retry_delay = min(retry_delay * 2, self.max_retry_delay)
                else:
                    logger.error(f"❌ MongoDB connection failed after {self.max_retry_attempts} attempts")
                    return False
            
            except Exception as e:
                logger.error(f"❌ Unexpected error during MongoDB connection: {e}")
                self._is_connected = False
                return False
        
        return False
    
    async def check_health(self) -> dict:
        """
        Check database connection health.
        
        Returns:
            dict: Health status with details
        """
        try:
            if not self._client or not self._db:
                return {
                    "status": "disconnected",
                    "error": "No database client initialized"
                }
            
            # Ping with short timeout
            await asyncio.wait_for(
                self._db.command('ping'),
                timeout=5.0
            )
            
            self._is_connected = True
            return {
                "status": "connected",
                "database": self.db_name
            }
            
        except asyncio.TimeoutError:
            self._is_connected = False
            return {
                "status": "timeout",
                "error": "Database ping timed out"
            }
        except Exception as e:
            self._is_connected = False
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def ensure_connected(self) -> bool:
        """
        Ensure database is connected, attempting reconnection if needed.
        
        Returns:
            bool: True if connected (or reconnected), False if unable to connect
        """
        # Quick check if already connected
        health = await self.check_health()
        if health["status"] == "connected":
            return True
        
        logger.warning("🔄 Database connection lost, attempting reconnection...")
        
        # Close existing client if any
        await self.close()
        
        # Attempt reconnection
        return await self.connect()
    
    async def close(self):
        """Close the database connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("🔌 MongoDB connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing MongoDB connection: {e}")
            finally:
                self._client = None
                self._db = None
                self._is_connected = False
    
    async def get_db_with_retry(self) -> Optional[AsyncIOMotorDatabase]:
        """
        Get database instance, ensuring connection is active.
        
        This method should be used for critical operations where
        we want to auto-recover from connection issues.
        
        Returns:
            AsyncIOMotorDatabase or None if unable to connect
        """
        if await self.ensure_connected():
            return self._db
        return None


# Singleton instance for global access
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> Optional[DatabaseManager]:
    """Get the global database manager instance."""
    return _db_manager


def init_db_manager(
    mongo_url: str,
    db_name: str,
    **kwargs
) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        mongo_url: MongoDB connection string
        db_name: Database name
        **kwargs: Additional options for DatabaseManager
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(mongo_url, db_name, **kwargs)
    return _db_manager


async def get_healthy_db() -> Optional[AsyncIOMotorDatabase]:
    """
    Convenience function to get a healthy database connection.
    
    Automatically attempts reconnection if needed.
    
    Returns:
        Database instance or None if unavailable
    """
    if _db_manager:
        return await _db_manager.get_db_with_retry()
    return None
