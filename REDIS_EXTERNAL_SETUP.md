# External Redis Setup for Production

**Status:** Emergent does not provide managed Redis - External provider needed

---

## Recommended Solution: Redis Cloud (Free Tier)

**Redis Cloud** offers a free tier that's perfect for your needs:
- ✅ 30MB free (sufficient for Socket.IO pub/sub)
- ✅ No credit card required
- ✅ TLS support
- ✅ Easy setup (5 minutes)

### Setup Instructions:

#### 1. Create Redis Cloud Account
- Go to: https://redis.io/try-free/
- Sign up (no credit card needed)
- Verify email

#### 2. Create Database
- Click "Create database"
- Select: **Free** plan
- Region: Choose closest to your production deployment
- Database name: `socketio-pubsub`
- **Important:** Uncheck "Data persistence" (not needed for pub/sub)
- Click "Create"

#### 3. Get Connection Details
After creation, you'll see:
```
Endpoint: redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
Password: your-password-here
```

#### 4. Build Connection URL
Format:
```
rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT
```

Example:
```
rediss://default:abc123xyz@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
```

**Note:** Use `rediss://` (with double 's') for TLS

---

## Configure in Emergent Production

### Step 1: Set Environment Variable
In your Emergent production deployment settings:

**Variable:** `REDIS_URL`  
**Value:** `rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT`  
**Environment:** Production only

### Step 2: Keep Preview Without Redis
In preview deployment settings:

**Variable:** `REDIS_URL`  
**Value:** (leave empty or unset)

This keeps preview using in-memory mode (simple, single-pod).

---

## Alternative: DigitalOcean Managed Redis

If you prefer a paid option with more features:

**Cost:** ~$15/month for smallest instance (256MB)

**Setup:**
1. Go to: https://cloud.digitalocean.com/
2. Create → Databases → Redis
3. Choose: Basic plan, 256MB
4. Get connection string
5. Set in Emergent production as `REDIS_URL`

---

## Alternative: Railway (Developer-Friendly)

**Cost:** $5/month minimum

**Setup:**
1. Go to: https://railway.app/
2. New Project → Add Redis
3. Copy connection string
4. Set in Emergent production as `REDIS_URL`

---

## Verification After Setup

### 1. Deploy with Redis URL
After setting `REDIS_URL` in production and redeploying, check logs:

```bash
# Should see:
✅ Socket.IO Redis pub/sub enabled for multi-pod scaling
🚀 Socket.IO server initialized with Redis adapter (multi-pod) mode
```

### 2. Test Auction Flow
During an auction, backend logs should show:
```json
{
  "event": "bid_update",
  "roomSize": 2,  // NOT 0!
  ...
}
```

### 3. Monitor Redis (Optional)
In Redis Cloud dashboard:
- Check "Operations/sec" graph
- Should see activity during auctions

---

## Security Best Practices

### 1. Use Strong Password
If provider allows, generate a strong random password.

### 2. Connection String Security
- ✅ Store in environment variables (not code)
- ✅ Use Emergent's secure variable storage
- ❌ Never commit to git

### 3. TLS Required
Always use `rediss://` (TLS) for production connections.

---

## Troubleshooting

### Error: "Connection refused"
- Check Redis endpoint and port are correct
- Verify Redis instance is running
- Check firewall/IP allowlist (Redis Cloud allows all by default)

### Error: "Authentication failed"
- Verify password in connection URL
- Check URL format: `rediss://default:PASSWORD@host:port`

### Backend logs show: "falling back to in-memory"
- `REDIS_URL` environment variable not set correctly
- Check deployment environment settings
- Redeploy after setting

### Events still not received
- Verify `roomSize > 0` in logs
- Check Redis Cloud shows activity
- Restart all backend pods after Redis configuration

---

## Cost Comparison

| Provider | Free Tier | Paid Plan | Setup Time |
|----------|-----------|-----------|------------|
| **Redis Cloud** | 30MB (✅ Sufficient) | $7/mo for 100MB | 5 min |
| DigitalOcean | None | $15/mo for 256MB | 10 min |
| Railway | None | $5/mo minimum | 5 min |
| AWS ElastiCache | None | ~$15/mo | 20 min |

**Recommendation:** Start with **Redis Cloud Free Tier**

---

## Next Steps

1. ✅ Sign up for Redis Cloud (free)
2. ✅ Create database (no persistence)
3. ✅ Copy connection URL
4. ✅ Set `REDIS_URL` in Emergent production settings
5. ✅ Redeploy production
6. ✅ Test auction flow
7. ✅ Verify `roomSize > 0` in logs

---

**Support:**
- Redis Cloud: https://redis.io/docs/
- Emergent: support@emergent.sh or Discord

**Last Updated:** December 8, 2025
