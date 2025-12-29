# Real-Time Sync (Socket.IO + Redis)

**Last Updated:** December 28, 2025  
**Purpose:** Socket.IO and Redis configuration for real-time auction updates

---

## Overview

The auction system uses Socket.IO for real-time bidding updates, with Redis pub/sub for multi-pod scaling.

## Configuration

### Single Pod (Development)

```python
# No Redis - in-memory mode
sio = socketio.AsyncServer(async_mode='asgi')
```

### Multi-Pod (Production)

```python
# Redis adapter for cross-pod communication
redis_url = os.getenv("REDIS_URL")
mgr = socketio.AsyncRedisManager(redis_url)
sio = socketio.AsyncServer(client_manager=mgr)
```

## Health Check

```bash
curl https://your-app.com/api/health | jq '.socketio'
```

**Expected (Production):**
```json
{
  "mode": "redis",
  "redis_configured": true,
  "multi_pod_ready": true
}
```

## Events

See [AUCTION_ENGINE.md](./AUCTION_ENGINE.md) for full event documentation.

---

**Related:** [AUCTION_ENGINE.md](./AUCTION_ENGINE.md), [../ENV_VARIABLES.md](../ENV_VARIABLES.md)
