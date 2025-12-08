# backend/socketio_init.py
import os
import socketio
import logging

logger = logging.getLogger(__name__)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
REDIS_URL = os.getenv("REDIS_URL")  # e.g. redis://:PASSWORD@host:6379/0

# Use AsyncRedisManager if REDIS_URL set; else in-memory manager
mgr = None
if REDIS_URL and REDIS_URL.strip():
    try:
        mgr = socketio.AsyncRedisManager(REDIS_URL)
        logger.info(f"✅ Socket.IO Redis manager initialized: {REDIS_URL[:20]}...")
    except Exception as e:
        logger.error(f"❌ Redis manager failed, falling back to memory: {e}")
        mgr = None
else:
    logger.info("📝 Socket.IO using in-memory manager (single replica)")

# Configure CORS origins - use wildcard for production compatibility
cors_origins = "*"
logger.info(f"🌐 Socket.IO CORS configured: {cors_origins}")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    ping_interval=25,              # Increased from 20 to handle proxy delays
    ping_timeout=60,               # Increased from 25 to 60 for nginx/proxy compatibility
    client_manager=mgr,            # enables pub/sub fanout across pods
    json=None,                     # default
    logger=True,                   # Enable Socket.IO logging for debugging
    engineio_logger=True,          # Enable EngineIO logging to track connections
    allow_upgrades=True,
    namespaces=None,
    always_connect=True
)

logger.info(f"🚀 Socket.IO server initialized with {'Redis scaling' if mgr else 'single replica'} mode")