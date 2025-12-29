# Session Affinity for Socket.IO Optimization

**Status:** Requires Emergent Support Configuration

---

## Why Session Affinity Matters

**Current Production Setup:**
- Multiple backend pods behind load balancer
- Each HTTP/WebSocket request load-balanced independently
- Socket.IO connection to Pod A, API calls may go to Pod B
- Requires Redis pub/sub for cross-pod synchronization

**With Session Affinity:**
- Same client always routed to same backend pod
- Reduces cross-pod communication (even with Redis)
- Better Socket.IO connection stability
- Lower Redis pub/sub overhead

---

## Benefits

### Performance
- **Reduced latency:** Events delivered locally (no Redis roundtrip)
- **Lower overhead:** Fewer Redis pub/sub messages
- **Better throughput:** Local room operations are faster

### Reliability
- **Connection stability:** Client stays on same pod
- **Simpler debugging:** All client requests on one pod
- **Graceful degradation:** Redis becomes backup, not primary path

### Resource Efficiency
- **Less Redis traffic:** Only needed when client spans pods
- **Lower network usage:** Local event delivery
- **Reduced CPU:** Fewer serialization/deserialization cycles

---

## Implementation Options

### Option 1: Cookie-Based Affinity (Preferred)
**How it works:**
- Load balancer sets a cookie (e.g., `SERVERID=pod-abc`)
- Future requests from same client include cookie
- Load balancer routes to matching pod

**Advantages:**
- ✅ Works across network changes (mobile/WiFi switching)
- ✅ Survives IP address changes
- ✅ Compatible with WebSocket upgrades
- ✅ Industry standard for session persistence

**Configuration needed:**
```yaml
# Example Kubernetes Ingress annotation
nginx.ingress.kubernetes.io/affinity: "cookie"
nginx.ingress.kubernetes.io/affinity-mode: "persistent"
nginx.ingress.kubernetes.io/session-cookie-name: "socket-io-route"
```

### Option 2: IP-Based Affinity (Fallback)
**How it works:**
- Load balancer tracks client IP address
- Same IP always routed to same pod

**Advantages:**
- ✅ Simpler configuration
- ✅ No cookies required

**Disadvantages:**
- ❌ Breaks when client IP changes (mobile networks)
- ❌ Issues with NAT/proxies (multiple clients, same IP)
- ❌ Less reliable for real-world scenarios

---

## Emergent Support Request

**Contact Emergent Support:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

**Information to Provide:**

1. **Job ID:** `bid-fixer`

2. **Request:**
   "Enable cookie-based session affinity for backend service in production"

3. **Technical Details:**
   - Application: FastAPI backend with Socket.IO
   - Current: Multiple backend pods, load balanced
   - Goal: Route same client to same pod for Socket.IO stability
   - Preferred: Cookie-based affinity (e.g., `SERVERID` cookie)
   - Alternative: IP-based affinity if cookies not supported

4. **Environment:**
   - Production only (preview is single pod, doesn't need affinity)
   - Backend service path: `/api/*`
   - Socket.IO path: `/api/socket.io/*`

5. **Questions:**
   - Does Emergent's ingress/load balancer support session affinity?
   - If yes, how to configure (annotations, settings, etc.)?
   - Cookie name and duration settings?
   - Compatible with WebSocket upgrades?
   - Behavior when target pod is unavailable?

---

## Expected Configuration

### Kubernetes Ingress (Example)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  annotations:
    # Session affinity
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/affinity-mode: "persistent"
    nginx.ingress.kubernetes.io/session-cookie-name: "route"
    nginx.ingress.kubernetes.io/session-cookie-expires: "172800"  # 2 days
    nginx.ingress.kubernetes.io/session-cookie-max-age: "172800"
    
    # WebSocket support (should already be enabled)
    nginx.ingress.kubernetes.io/websocket-services: "backend"
spec:
  rules:
  - host: draft-kings-mobile.emergent.host
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8001
```

---

## Verification After Configuration

### 1. Check Cookie is Set
Open browser DevTools → Network → Check response headers:
```
Set-Cookie: route=...; Path=/api; Max-Age=172800
```

### 2. Test Persistence
- Connect to auction
- Refresh page multiple times
- Check backend logs: Should see same `10.64.x.x` IP consistently
- Before affinity: Different IPs each request
- After affinity: Same IP for all requests from that client

### 3. Monitor Room Sizes
```bash
tail -f /var/log/supervisor/backend.out.log | grep roomSize
```

Should see consistent `roomSize > 0` even with fewer Redis messages.

### 4. Redis Metrics
In Redis Cloud dashboard:
- Before: High operations/sec during auctions
- After: Lower ops/sec (most events delivered locally)

---

## Compatibility Considerations

### Works With:
- ✅ Redis pub/sub (complementary, not replaced)
- ✅ Auto-scaling (new pods get new clients)
- ✅ Rolling deployments (clients reconnect to new pods)
- ✅ WebSocket connections
- ✅ Long-polling fallback

### Considerations:
- ⚠️ Pod removal: Clients on removed pod must reconnect
- ⚠️ Cookie expiry: After expiry, client may route to different pod
- ⚠️ Cookie clearing: User clears cookies → may get different pod

---

## Architecture Diagram

### Current (No Affinity):
```
Client A ──┐
           ├──> Load Balancer ──┬──> Pod 1 ──┐
Client B ──┘                    │            │
                                ├──> Pod 2 ──┼──> Redis ──> Event Distribution
Client C ──┐                    │            │
           ├──> Load Balancer ──┴──> Pod 3 ──┘
Client D ──┘

Problem: Client A connects to Pod 1, but API call goes to Pod 2
         → Event must go: Pod 2 → Redis → Pod 1 → Client A
```

### With Session Affinity:
```
Client A ────> Load Balancer ──> Pod 1 (sticky)
                                  ↓
                            All Client A requests → Pod 1
                            Events delivered locally ✅

Client B ────> Load Balancer ──> Pod 2 (sticky)
                                  ↓
                            All Client B requests → Pod 2
                            Events delivered locally ✅

Redis: Only used if pod goes down (failover)
```

---

## Recommendation Priority

**Immediate:**
1. ✅ Configure Redis (required for multi-pod)
2. ✅ Deploy and verify production works

**Optimization (Contact Support):**
3. ⚡ Enable session affinity
4. ⚡ Reduces Redis overhead
5. ⚡ Improves connection stability

---

## Summary

**Current State:**
- Code ready for Redis
- Redis needed for basic functionality
- Session affinity = performance optimization

**Action Items:**
1. Set up Redis (Redis Cloud free tier)
2. Configure `REDIS_URL` in production
3. Test and verify auction works
4. Contact Emergent support for session affinity
5. Further optimize after affinity enabled

**Expected Improvement with Affinity:**
- Faster event delivery (local vs Redis)
- Lower Redis traffic (50-90% reduction)
- Better connection stability
- Simpler debugging

---

**Last Updated:** December 8, 2025  
**Status:** Awaiting Emergent support configuration
