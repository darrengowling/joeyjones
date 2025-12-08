# backend/socketio_init.py
import os
import socketio
import logging

logger = logging.getLogger(__name__)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
REDIS_URL = os.getenv("REDIS_URL", "").strip()  # e.g. redis://:PASSWORD@host:6379/0 or rediss:// for TLS

# Use AsyncRedisManager if REDIS_URL set; else in-memory manager
mgr = None
if REDIS_URL:
    try:
        logger.info(f"🔧 Initializing Redis manager: {REDIS_URL[:30]}...")
        mgr = socketio.AsyncRedisManager(REDIS_URL)
        logger.info(f"✅ Socket.IO Redis pub/sub enabled for multi-pod scaling")
    except Exception as e:
        logger.error(f"❌ Redis manager initialization failed, falling back to in-memory: {e}")
        mgr = None
else:
    logger.info("📝 Socket.IO using in-memory manager (single replica only)")

# Configure CORS origins - use wildcard for production compatibility
cors_origins = "*"
logger.info(f"🌐 Socket.IO CORS configured: {cors_origins}")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    ping_interval=20,
    ping_timeout=25,
    client_manager=mgr,            # Redis pub/sub for multi-pod or in-memory for single pod
    json=None,                     # default
    logger=False,                  # Disable verbose Socket.IO logging
    engineio_logger=False,         # Disable verbose EngineIO logging (heartbeats)
    allow_upgrades=True,
    namespaces=None,
    always_connect=True
)

logger.info(f"🚀 Socket.IO server initialized with {'Redis adapter (multi-pod)' if mgr else 'in-memory (single-pod)'} mode")