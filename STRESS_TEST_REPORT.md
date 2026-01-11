# Auction Platform Stress Test Report

**Date:** January 11, 2026  
**Prepared for:** Internal Review  
**Purpose:** Document stress testing findings and recommendations for pilot readiness

---

## Executive Summary

We built an automated stress testing script to validate the auction platform's performance ahead of a 400-user pilot. Testing revealed two infrastructure bottlenecks affecting performance:

1. **Redis connection limit** - Causing bid failures under load (free tier limit: 30 connections)
2. **MongoDB network latency** - Adding ~600ms baseline delay per database query (shared Atlas cluster)

**Current State:** The platform functions correctly but performance degrades under load.  
**Recommendation:** Upgrade Redis (~£5/month) and consider dedicated MongoDB (~£45/month) before pilot.

---

## 1. What We Built

### Automated Stress Test Script

**Location:** `/app/tests/multi_league_stress_test.py`

**Capabilities:**
- Creates test users, leagues, and auctions automatically
- Simulates multiple concurrent auctions with configurable parameters
- Measures bid latency, success rates, and Socket.IO performance
- Outputs detailed JSON and text reports

**Usage:**
```bash
# Install dependencies
pip install "python-socketio[asyncio_client]" aiohttp

# Run test
python multi_league_stress_test.py --leagues 20 --users 8 --teams 4 --url https://YOUR-PRODUCTION-URL
```

**Configurable Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--leagues` | Number of concurrent leagues | 1 |
| `--users` | Users per league | 8 |
| `--teams` | Teams per user roster | 4 |
| `--url` | Target environment URL | localhost |

---

## 2. What We Tested

### Test Configurations

| Test | Leagues | Users | Total Bids | Purpose |
|------|---------|-------|------------|---------|
| Small scale | 2 | 6 | 48 | Baseline (under Redis limit) |
| Medium scale | 5 | 6 | 120 | Moderate load |
| Large scale | 10 | 8 | 320 | Higher concurrency |
| Pilot scale | 20 | 8 | 640 | Target pilot load |

### Test Environments

| Environment | MongoDB | Redis | Purpose |
|-------------|---------|-------|---------|
| Preview | localhost | N/A | Development testing |
| Production | Emergent shared Atlas | Redis Cloud (free) | Live environment |

---

## 3. Results Summary

### Performance by Scale

| Test Scale | p50 Latency | p99 Latency | Bid Success | Verdict |
|------------|-------------|-------------|-------------|---------|
| 2 leagues | 690ms | 1,995ms | 100% | ⚠️ Latency high |
| 5 leagues | 704ms | 1,209ms | 100% | ⚠️ Latency high |
| 10 leagues | 715ms | 1,591ms | 100% | ⚠️ Latency high |
| 20 leagues | 821ms | 5,254ms | 85% | ❌ Failures + latency |

### Preview vs Production (Same Code)

| Environment | p50 Latency | p99 Latency | Improvement |
|-------------|-------------|-------------|-------------|
| Preview | 357ms | 416ms | Baseline |
| Production | 713ms | 961ms | 2x slower |

---

## 4. Key Findings

### What's Working ✅

| Feature | Status | Evidence |
|---------|--------|----------|
| Auction logic | ✅ Working | 100% lots sold in all tests |
| Bid processing | ✅ Working | Bids recorded correctly |
| Socket.IO events | ✅ Working | Real-time updates flowing |
| Multi-league concurrency | ✅ Working | 20 leagues run simultaneously |
| User/league creation | ✅ Working | Automated setup successful |

### What Needs Fixing ❌

| Issue | Impact | Root Cause |
|-------|--------|------------|
| High baseline latency (~700ms) | Poor user experience | MongoDB network distance |
| Bid failures at scale (85% success) | Lost bids | Redis connection exhaustion |
| p99 spikes (5+ seconds) | Timeouts | Combined Redis + MongoDB |
| Socket connection errors | Missed updates | Redis pub/sub limit |

---

## 5. Root Cause Analysis

### Issue 1: MongoDB Latency

**Problem:** Every bid requires 7-8 database queries. Each query adds network round-trip time to Emergent's shared MongoDB Atlas cluster.

**Evidence:**
- Preview (localhost MongoDB): 357ms average latency
- Production (remote Atlas): 713ms average latency
- Difference: ~350-400ms per request (network overhead)

**Technical Details:**
```
Emergent's MongoDB: customer-apps.oxfwhh.mongodb.net
├── Shared cluster (multiple customers)
├── Unknown region (may differ from app location)
├── Cannot optimise from application side
└── ~50-100ms per database query (network)
```

### Issue 2: Redis Connection Limit

**Problem:** Redis Cloud free tier allows only 30 connections. Socket.IO requires connections for each user and pub/sub channel. At scale, connections exhaust.

**Evidence:**
- Alert received: "Database reached 86% of connection limit"
- 20 leagues × 8 users = 160+ connections needed
- Free tier limit: 30 connections
- Result: Connection failures, bid rejections

**Technical Details:**
```
Redis usage per auction:
├── Each connected user: 1-2 connections
├── Pub/sub channels: 1-2 per league
├── Internal Socket.IO: 2-3 connections
└── 20 leagues: 200-300 connections needed
```

---

## 6. Recommended Fixes

### Option A: Minimal Fix (Redis Only)

**Cost:** ~£5/month  
**Effort:** 30 minutes (configuration change)

| Metric | Current | Expected After |
|--------|---------|----------------|
| Bid success rate | 85% | 99%+ |
| p99 latency | 5,254ms | ~2,000ms |
| p50 latency | 821ms | ~700ms (unchanged) |

**What it fixes:**
- ✅ Connection failures
- ✅ p95/p99 spikes
- ❌ Baseline latency still ~700ms

**Verdict:** Acceptable for beta pilot with limited users.

---

### Option B: Full Fix (Redis + MongoDB)

**Cost:** ~£50/month (£5 Redis + £45 MongoDB M10)  
**Effort:** 2-4 hours (Redis config + MongoDB migration)

| Metric | Current | Expected After |
|--------|---------|----------------|
| Bid success rate | 85% | 99%+ |
| p99 latency | 5,254ms | ~500ms |
| p50 latency | 821ms | ~100-200ms |

**What it fixes:**
- ✅ Connection failures
- ✅ p95/p99 spikes
- ✅ Baseline latency (700ms → 100ms)

**Verdict:** Production-ready performance.

---

### Option C: Contact Emergent First

**Cost:** £0  
**Effort:** 1-2 days (await response)

**Action:** Contact Emergent support to request:
1. Dedicated MongoDB cluster (or same-region placement)
2. Information about their infrastructure limitations
3. Recommended settings for high-concurrency apps

**Potential outcome:** Emergent may offer solutions without additional cost.

---

## 7. Recommended Next Steps

### Immediate (This Week)

| Priority | Action | Cost | Time |
|----------|--------|------|------|
| 1 | Contact Emergent support with findings | £0 | 1 day |
| 2 | Upgrade Redis to Essentials tier | £5/month | 30 min |
| 3 | Rerun 20-league stress test | £0 | 1 hour |

### If Emergent Cannot Help (Next Week)

| Priority | Action | Cost | Time |
|----------|--------|------|------|
| 4 | Set up own MongoDB Atlas (M10, same region) | £45/month | 2 hours |
| 5 | Migrate production data | £0 | 1 hour |
| 6 | Rerun stress tests to validate | £0 | 1 hour |

### Before Pilot Launch

| Priority | Action | Success Criteria |
|----------|--------|------------------|
| 7 | Final stress test at pilot scale | p99 < 1s, 99%+ success |
| 8 | Implement competitive bidding test | Anti-snipe works under load |
| 9 | Load test with realistic user patterns | No degradation over time |

---

## 8. Expected Outcomes

### After Redis Upgrade Only

```
Pilot capacity: 20-30 concurrent leagues
Bid success: 99%+
User experience: Acceptable (some lag noticeable)
Risk: Medium - latency may frustrate users
```

### After Redis + MongoDB Upgrade

```
Pilot capacity: 50+ concurrent leagues
Bid success: 99.9%+
User experience: Good (real-time feel)
Risk: Low - production-ready performance
```

---

## 9. Test Artifacts

### Files Created

| File | Location | Purpose |
|------|----------|---------|
| Stress test script | `/app/tests/multi_league_stress_test.py` | Run load tests |
| Test README | `/app/tests/README.md` | Usage instructions |
| Results (JSON) | `stress_test_results_*.json` | Detailed metrics |
| Results (TXT) | `stress_test_results_*.txt` | Human-readable summary |

### Key Documentation Updated

| Document | Updates |
|----------|---------|
| `MASTER_TODO_LIST.md` | MongoDB/Redis investigation, schema management |
| `PRD.md` | Stress test usage, known limitations |

---

## 10. Appendix: Raw Test Data

### Small Scale Test (2 leagues, 6 users) - January 11, 2026

```
Latency:
  avg: 785.70ms
  p50: 689.66ms
  p95: 1,312.65ms
  p99: 1,994.87ms
  min: 651.91ms
  max: 1,994.87ms

Success:
  Bids: 48/48 (100%)
  Lots sold: 48/48 (100%)
  Socket events: 46

Verdict: NOT READY - High latency
```

### Large Scale Test (20 leagues, 8 users) - January 10, 2026

```
Latency:
  avg: 1,116.08ms
  p50: 821.33ms
  p95: 2,731.66ms
  p99: 5,253.67ms
  min: 320.21ms
  max: 7,260.07ms

Success:
  Bids: 617/724 (85.2%)
  Lots sold: 640/640 (100%)
  Socket events: 620

Verdict: NOT READY - Failures + high latency
```

---

## 11. Contacts

**For questions about this report:**
- Review the `MASTER_TODO_LIST.md` for detailed technical notes
- Test script includes `--help` for all options

**External support:**
- Emergent: support@emergent.sh or Discord (https://discord.gg/VzKfwCXC4A)
- MongoDB Atlas: mongodb.com/cloud/atlas
- Redis Cloud: redis.com/cloud

---

*Report generated from stress testing conducted January 10-11, 2026*
