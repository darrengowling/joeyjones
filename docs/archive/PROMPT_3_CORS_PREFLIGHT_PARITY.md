# Prompt 3: CORS/Preflight Parity for Production

**Date:** December 8, 2025  
**Objective:** Ensure CORS preflight requests are properly handled and logged  
**Status:** ✅ IMPLEMENTED

---

## Changes Implemented

### 1. Added `x-user-id` to Allowed Headers

**File:** `/app/backend/server.py` - Line 5699

**Before:**
```python
allow_headers=["Authorization", "Content-Type", "Accept"]
```

**After:**
```python
allow_headers=["Authorization", "Content-Type", "Accept", "x-user-id"]
```

**Purpose:** Ensures custom headers used by the frontend are allowed in CORS requests.

---

### 2. Added Global Preflight Logging Middleware

**File:** `/app/backend/server.py` - Lines 5690-5702

**New Middleware:**
```python
@app.middleware("http")
async def log_preflight_requests(request, call_next):
    if request.method == "OPTIONS":
        # Log all OPTIONS requests for CORS preflight diagnostics
        logger.info(json.dumps({
            "evt": "cors:preflight",
            "path": request.url.path,
            "method": "OPTIONS",
            "origin": request.headers.get("origin", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
    
    response = await call_next(request)
    return response
```

**Purpose:**
- Logs ALL OPTIONS (preflight) requests across the entire API
- Captures origin header to see where requests come from
- Provides visibility into CORS preflight flow

**Log Format:**
```json
{
  "evt": "cors:preflight",
  "path": "/api/auction/abc123/bid",
  "method": "OPTIONS",
  "origin": "https://draft-kings-mobile.emergent.host",
  "timestamp": "2025-12-08T02:00:00.000000+00:00"
}
```

---

### 3. Added Explicit OPTIONS Handler for Bid Endpoint

**File:** `/app/backend/server.py` - Lines 4511-4528

**New Endpoint:**
```python
@api_router.options("/auction/{auction_id}/bid")
async def bid_preflight(auction_id: str):
    """
    Explicit OPTIONS handler for bid endpoint to handle CORS preflight requests.
    Logs preflight requests for diagnostics.
    """
    logger.info(json.dumps({
        "evt": "cors:preflight",
        "path": f"/auction/{auction_id}/bid",
        "method": "OPTIONS",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    return {
        "message": "Preflight OK",
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Authorization", "Content-Type", "Accept", "x-user-id"]
    }
```

**Purpose:**
- Provides explicit OPTIONS endpoint for the bid route
- Returns information about allowed methods and headers
- Additional logging specific to bid endpoint

---

### 4. Added CORS Configuration Logging on Startup

**File:** `/app/backend/server.py` - Line 5707

**New Log:**
```python
logger.info(f"🌐 CORS Origins configured: {cors_origins}")
```

**Output:**
```
INFO:server:🌐 CORS Origins configured: ['*']
```

**Purpose:** Confirms CORS configuration on application startup for diagnostics.

---

## Current CORS Configuration

### Environment Variables
**File:** `/app/backend/.env` - Line 3
```
CORS_ORIGINS="*"
```

**Interpretation:**
- Wildcard `*` allows requests from ANY origin
- Safe for Socket.IO and production use
- Simplifies debugging (no origin rejection issues)

### Middleware Settings
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],                    # All origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "x-user-id"],
    allow_credentials=True,                 # Allow cookies/auth
    max_age=600,                           # Cache preflight for 10 minutes
)
```

---

## CORS Preflight Flow

### What is a Preflight Request?

When a browser makes a cross-origin request with:
- Custom headers (like `x-user-id`)
- Methods other than GET/HEAD/POST
- Content-Type other than basic types

The browser **first** sends an OPTIONS request (preflight) to check if the actual request is allowed.

### Expected Flow for Bid Request

```
Step 1: Browser sends OPTIONS request
   → Method: OPTIONS
   → Path: /api/auction/abc123/bid
   → Headers: Origin, Access-Control-Request-Method, Access-Control-Request-Headers

Step 2: Backend processes preflight
   → Middleware logs: {"evt": "cors:preflight", ...}
   → CORSMiddleware adds CORS headers
   → Returns 200 OK

Step 3: Browser sends actual POST request
   → Method: POST
   → Path: /api/auction/abc123/bid
   → Body: {userId, clubId, amount}
   → Backend logs: {"evt": "bid:incoming", ...}
   → Returns 200 with bid response
```

---

## Production Log Examples

### Successful Bid with Preflight

**Logs:**
```json
{"evt": "cors:preflight", "path": "/api/auction/abc123/bid", "method": "OPTIONS", "origin": "https://draft-kings-mobile.emergent.host"}
{"evt": "bid:incoming", "auctionId": "abc123", "userId": "user1", "amount": 5000000}
{"event": "bid_update", "seq": 5, "amount": 5000000}
```

**User Experience:**
- Transparent (no visible delay)
- Bid succeeds normally

---

### Preflight Failure (Hypothetical)

If CORS was misconfigured:

**Logs:**
```json
{"evt": "cors:preflight", "path": "/api/auction/abc123/bid", "origin": "https://draft-kings-mobile.emergent.host"}
(No bid:incoming - preflight rejected, POST never sent)
```

**Frontend Console:**
```
❌ CORS error: Request blocked by CORS policy
```

**User Experience:**
- Red toast: "No response from server"
- Bid fails silently

---

## Testing & Verification

### 1. Check CORS Configuration on Startup

**Look for in backend logs:**
```
INFO:server:🌐 CORS Origins configured: ['*']
```

**Verify:**
- ✅ Origins include `*` or production domain
- ✅ Log appears on every backend restart

---

### 2. Monitor Preflight Requests

**During auction, look for:**
```json
{"evt": "cors:preflight", "path": "/api/auction/*/bid", "origin": "https://..."}
```

**What to check:**
- Are preflight requests being logged?
- Do they precede `bid:incoming` logs?
- Is the origin correct?

---

### 3. Verify Allowed Headers

**Test with curl:**
```bash
curl -X OPTIONS https://draft-kings-mobile.emergent.host/api/auction/test/bid \
  -H "Origin: https://draft-kings-mobile.emergent.host" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,x-user-id" \
  -v
```

**Expected response headers:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, Accept, x-user-id
Access-Control-Max-Age: 600
```

---

## Diagnostic Benefits

### Before Changes:
- No visibility into preflight requests
- Unclear if CORS was causing bid failures
- No way to see if OPTIONS requests were handled

### After Changes:
- Every preflight logged with `{"evt": "cors:preflight", ...}`
- Can correlate preflight with actual bid requests
- Can see which origins are making requests
- Explicit OPTIONS handler provides clear response

---

## Common CORS Issues Prevented

### 1. Missing Headers
**Problem:** Custom header `x-user-id` not in allowed list  
**Fix:** ✅ Added to `allow_headers`

### 2. Missing Methods
**Problem:** OPTIONS not in allowed methods  
**Fix:** ✅ Already included in `allow_methods`

### 3. Origin Mismatch
**Problem:** Production origin not in allowed list  
**Fix:** ✅ Using wildcard `*`

### 4. Credentials Issue
**Problem:** Cookies/auth headers not allowed  
**Fix:** ✅ `allow_credentials=True`

---

## Files Modified

1. `/app/backend/server.py`
   - Added preflight logging middleware (lines 5690-5702)
   - Added `x-user-id` to allowed headers (line 5699)
   - Added startup CORS logging (line 5707)
   - Added explicit OPTIONS handler for bid endpoint (lines 4511-4528)

---

## Environment Configuration

**Current:** `/app/backend/.env`
```
CORS_ORIGINS="*"
```

**Alternative (Stricter):**
```
CORS_ORIGINS="https://draft-kings-mobile.emergent.host,https://preview.emergent.host"
```

**Recommendation:** Keep wildcard `*` for now since:
- Socket.IO already uses wildcard CORS
- Simplifies production debugging
- Backend has authentication layer (magic links, JWT)
- Kubernetes ingress provides network-level security

---

## Next Steps

1. **Deploy to production** (backend restart required)
2. **Monitor logs** during auction for:
   - `{"evt": "cors:preflight", ...}` entries
   - Verify they appear before bid attempts
3. **Check frontend Network tab**:
   - Look for OPTIONS requests
   - Verify they return 200 OK
   - Check response headers include CORS headers
4. **Correlate logs**:
   - Each bid should have: preflight → bid:incoming → bid_update
   - Missing preflight might indicate caching (max_age=600)

---

## Coordination with Prompts 1 & 2

**Complete Bid Visibility:**

**Frontend (Prompt 1):**
```javascript
🔵 bid:attempt
📤 bid:sent
✅ bid:success / ❌ bid:error
```

**Backend (Prompts 2 & 3):**
```json
{"evt": "cors:preflight"}    // Prompt 3
{"evt": "bid:incoming"}       // Prompt 2
{"event": "bid_update"}       // Existing
```

**Result:** Full visibility from user click → preflight → request → response → broadcast

---

**Status:** ✅ READY FOR DEPLOYMENT  
**Risk:** LOW (standard CORS configuration, wildcard already used for Socket.IO)  
**Testing:** Monitor production logs for `cors:preflight` entries
