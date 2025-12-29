# Prompt 4: Ingress/WAF Sanity Check for POST /bid

**Date:** December 8, 2025  
**Objective:** Verify production ingress configuration supports frequent JSON POSTs  
**Status:** ✅ DOCUMENTED - REQUIRES EMERGENT PLATFORM VERIFICATION

---

## Environment Context

### Preview Environment (Current Container)
- **Local nginx** present at `/etc/nginx/`
- **Purpose:** Code-server and local development only
- **NOT USED** for application traffic (supervisor manages FastAPI/React directly)

### Production Environment (Kubernetes)
- **Managed by:** Emergent's native deployment platform
- **Ingress Controller:** Kubernetes Ingress (likely nginx-ingress or similar)
- **Configuration:** Managed by platform, not directly accessible from code
- **URL:** `https://draft-kings-mobile.emergent.host`

---

## Critical Ingress Settings for Bid Endpoint

### 1. Proxy Timeouts

**Setting:** `proxy_read_timeout` and `proxy_send_timeout`

**Requirement for `/api/auction/*/bid`:**
```nginx
proxy_read_timeout 30s;      # Time to wait for backend response
proxy_send_timeout 30s;      # Time to send request to backend
```

**Why It Matters:**
- Bid requests should complete in <1 second normally
- Frontend has 10s timeout (Prompt 1)
- Backend processing is fast (~50-200ms)
- 30s is reasonable safety margin

**If Too Low (e.g., 10s):**
- ❌ Requests might timeout at ingress before reaching backend
- ❌ Frontend sees timeout, backend never gets request
- ❌ No `bid:incoming` logs

**Recommended:** At least 30 seconds

---

### 2. Request Body Size

**Setting:** `client_max_body_size`

**Requirement for `/api/auction/*/bid`:**
```nginx
client_max_body_size 1m;     # 1MB should be sufficient
```

**Current Bid Request Size:**
```json
{
  "userId": "uuid-string-36-chars",
  "clubId": "uuid-string-36-chars", 
  "amount": 5000000
}
```
**Approximate size:** ~150-200 bytes

**Why It Matters:**
- Bid requests are tiny (under 1KB)
- 1MB limit is more than sufficient
- Default nginx is usually 1MB

**If Too Low (e.g., 100 bytes):**
- ❌ 413 Request Entity Too Large
- ❌ Bid rejected before reaching backend

**Recommended:** 1MB minimum (default is usually fine)

---

### 3. Request Buffering

**Setting:** `proxy_buffering` and `proxy_request_buffering`

**Requirement for `/api/auction/*/bid`:**
```nginx
# For /api endpoints
proxy_buffering off;              # Don't buffer backend responses
proxy_request_buffering off;      # Don't buffer client requests
```

**Why It Matters:**
- Bid requests are small, buffering adds latency
- Backend processes quickly, no need to buffer response
- Reduces time-to-first-byte for user

**If Buffering Enabled:**
- ⚠️ Added latency (10-50ms)
- ⚠️ Delayed response to user
- Not a blocker, but suboptimal

**Recommended:** Disable for `/api` paths

---

### 4. Connection Limits

**Settings:** Rate limiting and connection limits

**Requirement:**
```nginx
# Don't rate-limit authenticated auction traffic
limit_req_zone off;              # Or set high limit
limit_conn off;                  # Or allow multiple connections per IP
```

**Why It Matters:**
- Multiple users in same office/network share IP
- Rapid bidding is legitimate behavior
- Rate limiting can reject valid bids

**If Too Strict:**
- ❌ 429 Too Many Requests
- ❌ Valid bids rejected
- ❌ Users in same network can't bid

**Recommended:** No rate limiting for `/api/auction/*/bid`, or very high limit (e.g., 100/second per IP)

---

### 5. WebSocket Support (for Socket.IO)

**Settings:** WebSocket upgrade headers

**Requirement for `/api/socket.io`:**
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_read_timeout 3600s;        # Long timeout for persistent connections
```

**Current Status:**
- ✅ Socket.IO working via polling transport (Prompt 1)
- ⚠️ WebSocket upgrade returns 403 (ingress blocking)
- Not critical since polling works

**If Not Configured:**
- ❌ WebSocket connections fail (seen in user screenshots)
- ✅ Polling fallback works (current state)

**Recommended:** Configure for optimal performance, but not blocking

---

## Current Configuration Analysis

### What We Know

**From User Reports:**
1. ✅ Some bids work (4-6 per auction)
2. ❌ Many bids fail silently
3. ✅ Timer works (Socket.IO polling functional)
4. ❌ WebSocket upgrade fails with 403

**From Logs:**
1. ✅ Backend starts successfully
2. ✅ CORS configured: `['*']`
3. ⚠️ No `bid:incoming` logs for failed bids
4. ✅ Successful bids show complete log chain

**Inference:**
- Ingress is allowing SOME requests through
- Likely NOT a blanket 413/timeout issue
- May be rate limiting or connection pooling issue
- May be request buffering causing delays

---

## Recommended Kubernetes Ingress Annotation

If using nginx-ingress controller, these annotations should be applied:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: draft-kings-auction
  annotations:
    # Timeout settings
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
    
    # Body size
    nginx.ingress.kubernetes.io/proxy-body-size: "1m"
    
    # Disable buffering for real-time responses
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-request-buffering: "off"
    
    # WebSocket support for Socket.IO
    nginx.ingress.kubernetes.io/websocket-services: "backend"
    
    # Disable rate limiting for auction endpoints
    nginx.ingress.kubernetes.io/limit-rps: "100"
    
    # CORS (if not handled by app)
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
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
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

---

## How to Verify Production Ingress Settings

Since we don't have direct access to Kubernetes ingress configuration, here are ways to verify:

### Method 1: Contact Emergent Support

**Email:** `support@emergent.sh`

**Request:**
```
Subject: Ingress Configuration Verification - Job ID: [YOUR_JOB_ID]

Please verify the following ingress settings for:
https://draft-kings-mobile.emergent.host

1. proxy_read_timeout: Should be >= 30s
2. proxy_send_timeout: Should be >= 30s  
3. client_max_body_size: Should be >= 1MB
4. proxy_buffering: Should be "off" for /api paths
5. Rate limiting: Should allow high request rate for /api/auction/*/bid
6. WebSocket support: Enable upgrade headers for /api/socket.io

Issue: Bid requests intermittently failing to reach backend.
```

---

### Method 2: Test from Production

**Test timeout settings:**
```bash
# Test with slow backend response simulation
time curl -X POST https://draft-kings-mobile.emergent.host/api/auction/test/bid \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","clubId":"test","amount":5000000}' \
  --max-time 35
```

**Test body size:**
```bash
# Send large payload (should still work if limit is reasonable)
curl -X POST https://draft-kings-mobile.emergent.host/api/auction/test/bid \
  -H "Content-Type: application/json" \
  -d @large_payload.json \
  -v
```

**Check response headers:**
```bash
curl -I https://draft-kings-mobile.emergent.host/api/auction/test/bid
# Look for: X-Request-ID, Server version, timeouts in headers
```

---

### Method 3: Production Log Analysis

**With new logging (Prompts 1-3), monitor for patterns:**

```json
// Pattern 1: Request reaches ingress but not backend
Frontend: {"evt": "bid:sent"}
Backend:  (nothing)
→ Indicates ingress blocking or timeout

// Pattern 2: Request reaches backend but response lost  
Frontend: {"evt": "bid:sent"}
Backend:  {"evt": "bid:incoming"}
Backend:  {"evt": "bid_update"}
Frontend: {"evt": "bid:error", "code": "ECONNABORTED"}
→ Indicates response timeout at ingress

// Pattern 3: Preflight succeeds but POST fails
Backend:  {"evt": "cors:preflight"}
Frontend: {"evt": "bid:sent"}
Backend:  (no bid:incoming)
→ Indicates ingress treating POST differently than OPTIONS
```

---

## Application-Level Optimizations (Already Implemented)

While waiting for ingress verification, we've already optimized the application:

### ✅ Frontend (Prompt 1)
- 10-second axios timeout
- Retry logic for timeouts
- Clear error messages
- Request logging

### ✅ Backend (Prompts 2 & 3)
- Entry point logging (`bid:incoming`)
- CORS preflight logging
- Clear validation errors
- Fast processing (<200ms typical)

### ✅ Infrastructure Assumptions
- CORS: Wildcard `*` (matching Socket.IO)
- No authentication on preflight (OPTIONS)
- Standard HTTP methods allowed

---

## Suspected Issues Based on Symptoms

### Most Likely: Rate Limiting or Connection Pooling

**Evidence:**
- Some bids work (4-6 per auction)
- Pattern suggests quota/limit being hit
- Multiple users from same network/IP

**If This Is The Issue:**
- First few bids succeed (under limit)
- Subsequent bids rejected (limit reached)
- Limit resets after time window
- Next auction starts clean

**Fix Required:**
- Increase rate limit for `/api/auction/*/bid`
- Or disable rate limiting for authenticated users
- Or increase per-IP connection limit

---

### Less Likely: Request Timeout

**Evidence:**
- Would affect all bids consistently
- We see some succeeding, some failing
- Backend processing is fast

**If This Is The Issue:**
- All bids would timeout
- Or none would timeout
- Not intermittent pattern

---

### Less Likely: Body Size Limit

**Evidence:**
- Bid payloads are tiny (~200 bytes)
- Would be consistent error
- Would show 413 status

---

## Recommended Next Steps

### Immediate (During Next Auction):

1. **Monitor production logs** for:
   ```
   - Count: {"evt": "bid:incoming"} 
   - Count: {"evt": "bid:sent"} from frontend console
   - Gap = requests not reaching backend
   ```

2. **Check frontend Network tab**:
   ```
   - Any 429 (rate limit) responses?
   - Any 413 (body too large) responses?
   - Any timeout errors?
   - Request/response sizes
   ```

3. **Note timing**:
   ```
   - Do failures cluster together?
   - Do they happen after X requests?
   - Do they reset between lots/auctions?
   ```

---

### Follow-up (After Data Collection):

1. **Contact Emergent Support** with:
   - Job ID
   - Specific timestamps of failed bids
   - Request counts (sent vs received)
   - Any error codes observed

2. **Request ingress logs** showing:
   - Rejected requests
   - Rate limit triggers
   - Timeout events
   - WebSocket upgrade attempts

3. **Verify/adjust ingress settings** based on findings

---

## Summary

### Current State:
- ✅ Application code optimized (Prompts 1-3)
- ✅ Logging comprehensive
- ⚠️ Ingress configuration unknown
- ❌ Some bids not reaching backend

### Required Verification:
- ✅ `proxy_read_timeout` >= 30s
- ✅ `proxy_send_timeout` >= 30s
- ✅ `client_max_body_size` >= 1MB
- ✅ `proxy_buffering` off for /api
- ✅ Rate limiting disabled or high limit
- ✅ WebSocket support for Socket.IO (optional)

### Action Required:
- Contact Emergent Support for ingress verification
- Monitor next auction with enhanced logging
- Correlate frontend and backend logs to identify where requests are lost

---

**Status:** ✅ DOCUMENTED  
**Risk:** N/A (No code changes)  
**Owner:** Emergent Platform Team (for ingress configuration)  
**User Action:** Contact support with this document and job ID
