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

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else "*",
    ping_interval=20,
    ping_timeout=25,
    client_manager=mgr,            # enables pub/sub fanout across pods
    json=None,                     # default
    logger=True,                   # Enable for diagnostics
    engineio_logger=True,          # Enable for diagnostics
    allow_upgrades=True,
    namespaces=None,
    always_connect=True
)

logger.info(f"🚀 Socket.IO server initialized with {'Redis scaling' if mgr else 'single replica'} mode")