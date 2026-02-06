# backend/socketio_init.py
import os
import socketio
import logging

logger = logging.getLogger(__name__)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
REDIS_URL = os.getenv("REDIS_URL", "").strip()  # e.g. redis://:PASSWORD@host:6379/0 or rediss:// for TLS

# Use AsyncRedisManager if REDIS_URL set; else in-memory manager
mgr = None
redis_enabled = False

if REDIS_URL:
    try:
        # python-socketio's AsyncRedisManager doesn't support rediss:// scheme directly
        # Convert rediss:// to redis:// for compatibility (TLS is handled at connection level)
        redis_url = REDIS_URL
        if redis_url.startswith("rediss://"):
            logger.info("🔧 Converting rediss:// to redis:// for AsyncRedisManager compatibility")
            redis_url = redis_url.replace("rediss://", "redis://", 1)
        
        # Check if URL has valid scheme
        if not redis_url.startswith("redis://"):
            # URL might be missing scheme entirely (e.g., "rediss-12232.c338...")
            logger.warning("⚠️ Redis URL missing scheme, adding redis:// prefix")
            redis_url = f"redis://{redis_url}"
        
        logger.info(f"🔧 Initializing Redis manager: {redis_url[:30]}...")
        
        # IMPORTANT: AsyncRedisManager creation succeeds even if Redis is unreachable
        # Connection failures only appear when trying to publish messages
        # This is why we see "Cannot publish to redis" errors in production
        mgr = socketio.AsyncRedisManager(redis_url)
        redis_enabled = True
        
        logger.info("✅ Socket.IO Redis manager created (connection will be verified on first publish)")
        logger.info("⚠️  If you see 'Cannot publish to redis' errors, Redis is unreachable")
        logger.info("⚠️  Check: 1) Redis URL is correct, 2) Network/firewall allows connection, 3) Redis credentials are valid")
    except Exception as e:
        logger.error(f"❌ Redis manager initialization failed, falling back to in-memory: {e}")
        logger.error(f"   Redis URL attempted: {redis_url[:50]}...")
        mgr = None
        redis_enabled = False
else:
    logger.info("📝 Socket.IO using in-memory manager (single replica only)")
    logger.info("💡 To enable multi-pod scaling, set REDIS_URL environment variable")

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

if redis_enabled and mgr:
    logger.info("🚀 Socket.IO server initialized with Redis adapter (multi-pod mode)")
    logger.warning("⚠️  Redis adapter created but actual connectivity will be tested on first message")
    logger.warning("⚠️  If deployment logs show 'Cannot publish to redis' errors:")
    logger.warning("   1. Verify Redis instance is running and accessible")
    logger.warning("   2. Check REDIS_URL format: redis://[user]:[password]@host:port")
    logger.warning("   3. Verify network/firewall allows connection from pods")
    logger.warning("   4. Test Redis connection: redis-cli -u $REDIS_URL ping")
    logger.warning("⚠️  Application will continue with degraded Socket.IO (events won't broadcast across pods)")
else:
    logger.info("🚀 Socket.IO server initialized with in-memory manager (single-pod mode)")
    logger.info("💡 For production multi-pod deployments, configure REDIS_URL")