# Troubleshooting Guide

**Last Updated:** December 28, 2025  
**Purpose:** Common issues and solutions

---

## Quick Diagnostics

### Check System Health

```bash
curl -s https://draft-kings-mobile.emergent.host/api/health | python3 -m json.tool
```

### Check Backend Logs

```bash
tail -100 /var/log/supervisor/backend.err.log
```

### Check Frontend Logs

```bash
tail -100 /var/log/supervisor/frontend.err.log
```

### Restart Services

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

---

## Common Issues

### "Database not connected"

**Symptoms:** Health check shows `"database": "disconnected"`

**Solutions:**
1. Check `MONGO_URL` is set correctly
2. Verify MongoDB is running (local) or Atlas cluster is active
3. Check network connectivity

```bash
# Test MongoDB connection
mongosh "$MONGO_URL" --eval "db.serverStatus()"
```

---

### "Socket.IO not syncing across users"

**Symptoms:** Bids not appearing for other users

**Solutions:**
1. Check `REDIS_URL` is configured (production)
2. Verify health shows `"socketio": {"mode": "redis"}`
3. Check Redis connection

```bash
# Check health endpoint
curl https://your-app.com/api/health | jq '.socketio'
```

---

### "Points not calculating"

**Symptoms:** Standings show 0 points after fixtures complete

**Causes:**
1. Fixture status is not `"ft"` (must be "ft" not "completed")
2. Score recompute not triggered

**Solutions:**
```bash
# Check fixture status
mongosh --eval "db.fixtures.find({leagueId: 'YOUR_LEAGUE_ID'}, {status:1, _id:0})"

# Trigger recompute
curl -X POST "https://your-app.com/api/leagues/{league_id}/score/recompute" \
  -H "Authorization: Bearer $TOKEN"
```

---

### "Teams not showing in selection"

**Symptoms:** Manage Clubs shows empty or wrong teams

**Causes:**
1. Wrong competition filter
2. `assetsSelected` not populated

**Solutions:**
1. Check league's `competitionCode`
2. Verify assets exist for that competition

```bash
# Check assets for competition
mongosh --eval "db.assets.find({competitionShort: 'PL'}).count()"
```

---

### "Can't place bid"

**Symptoms:** Bid button doesn't work or shows error

**Causes:**
1. Budget exhausted
2. Roster full
3. Already highest bidder (self-outbid)
4. Bid not higher than current

**Solutions:**
1. Check participant's `budgetRemaining`
2. Check `clubsWon.length` vs `league.clubSlots`
3. Check `currentBidderId` vs user ID

---

### "Auction frozen"

**Symptoms:** Timer stuck, no updates

**Solutions:**
1. Check if auction is paused (`status: "paused"`)
2. Refresh page to reconnect Socket.IO
3. Commissioner can use "Complete Lot" button

---

### "500 Internal Server Error"

**Symptoms:** API returns 500 error

**Solutions:**
1. Check backend logs for stack trace
2. Common causes:
   - MongoDB ObjectId serialization (missing `{"_id": 0}`)
   - None/null handling in Pydantic models
   - Missing required fields

```bash
tail -50 /var/log/supervisor/backend.err.log | grep -A 10 "Error"
```

---

### "CORS Error"

**Symptoms:** Browser console shows CORS error

**Solutions:**
1. Check `CORS_ORIGINS` includes frontend URL
2. Ensure no trailing slashes in URLs
3. Protocol must match (http vs https)

```bash
# Check current CORS config
grep CORS_ORIGINS /app/backend/.env
```

---

## Debug Endpoints

### View Auction State

```bash
curl "https://your-app.com/api/debug/auction-state/{auction_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### View Bid Logs

```bash
curl "https://your-app.com/api/debug/bid-logs/{auction_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Submit Debug Report

Frontend has "Report Issue" button that captures:
- Socket.IO events
- Bid attempts
- Server state
- Error summary

---

## Environment-Specific Issues

### Preview vs Production

| Issue | Preview | Production |
|-------|---------|------------|
| Database | localhost:27017 | Atlas cluster |
| Redis | Not configured | Redis Cloud |
| CORS | localhost:3000 | Production domain |

**Common mistake:** Testing against wrong environment.

---

## Getting Help

1. Check this guide first
2. Check `/app/docs/` documentation
3. Review recent git commits for changes
4. Check `MASTER_TODO_LIST.md` for known issues

---

**Document Version:** 1.0
