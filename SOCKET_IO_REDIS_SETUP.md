# Socket.IO Redis Adapter Setup

**Status:** ✅ Code Ready - Awaiting Redis Configuration

---

## Problem Summary

**Preview Environment:** Works perfectly (single backend instance, in-memory Socket.IO)  
**Production Environment:** Socket.IO events not reaching clients (multi-pod deployment, roomSize=0)

**Root Cause:** Production runs multiple backend pods behind a load balancer. Socket.IO room membership is NOT shared across pods without Redis pub/sub.

---

## Solution Implemented

### Backend Code Changes

Updated `/app/backend/socketio_init.py` to support Redis adapter:

```python
REDIS_URL = os.getenv("REDIS_URL", "").strip()

# Conditional initialization
if REDIS_URL:
    mgr = socketio.AsyncRedisManager(REDIS_URL)  # Multi-pod with Redis
    logger.info("✅ Socket.IO Redis pub/sub enabled")
else:
    mgr = None  # Single-pod with in-memory manager
    logger.info("📝 Socket.IO using in-memory manager")

sio = socketio.AsyncServer(
    client_manager=mgr,  # Redis or in-memory
    cors_allowed_origins="*",
    # ... other settings
)
```

**Features:**
- ✅ Supports both `redis://` and `rediss://` (TLS) URLs
- ✅ Graceful fallback to in-memory if Redis fails
- ✅ Clear logging for debugging
- ✅ No code changes needed when switching modes

---

## Production Deployment Steps

### Option 1: Enable Redis (Recommended)

**Contact Emergent Support** to provision Redis for your production deployment:
- Email: support@emergent.sh
- Discord: https://discord.gg/VzKfwCXC4A

**Request:**
- Redis instance for production environment
- Provide connection URL (e.g., `redis://...` or `rediss://...` for TLS)

**Configure Environment Variable:**
Set in production deployment settings:
```
REDIS_URL=redis://your-redis-host:6379
```
or for TLS:
```
REDIS_URL=rediss://your-redis-host:6380
```

**Redeploy** - Backend will automatically use Redis adapter.

---

### Option 2: Single Backend Instance

If Redis is not available, configure production to use only **1 backend replica**.

**Contact Emergent Support** to:
- Set production backend replicas to 1
- This matches preview environment configuration
- Socket.IO will work with in-memory manager

---

## Verification

### Check Redis Connection (After Configuration)

**Backend Logs:**
```bash
tail -f /var/log/supervisor/backend.err.log | grep Socket.IO
```

**Success Messages:**
```
✅ Socket.IO Redis pub/sub enabled for multi-pod scaling
🚀 Socket.IO server initialized with Redis adapter (multi-pod) mode
```

**Failure (Falls back to in-memory):**
```
❌ Redis manager initialization failed, falling back to in-memory: [error]
📝 Socket.IO using in-memory manager (single replica only)
```

### Test Socket.IO Rooms

After Redis is configured, check backend logs during auction:
```bash
tail -f /var/log/supervisor/backend.out.log | grep roomSize
```

**Before Redis:** `"roomSize": 0` ❌  
**After Redis:** `"roomSize": 2` (or more) ✅

---

## Technical Details

### Why Redis is Needed for Multi-Pod Deployments

**Without Redis:**
- Each backend pod has its own isolated Socket.IO server
- Client connects to Pod A
- Bid API call goes to Pod B (load balanced)
- Pod B emits events to its local rooms (empty)
- Client on Pod A never receives the event

**With Redis:**
- All backend pods share Redis pub/sub
- Client connects to Pod A (joins room in Pod A's memory + Redis)
- Bid API call goes to Pod B
- Pod B publishes event to Redis
- Redis broadcasts to all pods
- Pod A receives from Redis and sends to client ✅

### Supported Redis URLs

- **Standard:** `redis://host:6379`
- **With password:** `redis://:password@host:6379`
- **With database:** `redis://host:6379/0`
- **TLS:** `rediss://host:6380`
- **Full:** `rediss://:password@host:6380/0`

---

## Current Status

| Environment | Backend Instances | Redis | Socket.IO Status |
|-------------|------------------|-------|------------------|
| Preview | 1 | No (in-memory) | ✅ Working |
| Production | Multiple | **Not configured** | ❌ Events not delivered |

---

## Next Steps

1. **Contact Emergent Support** for Redis provisioning or single-instance configuration
2. **Set `REDIS_URL`** environment variable in production deployment settings
3. **Redeploy** production
4. **Test** auction flow to verify Socket.IO events are delivered

---

**Last Updated:** December 8, 2025  
**Status:** Code ready, awaiting infrastructure configuration
