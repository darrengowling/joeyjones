# Migration & Infrastructure Plan

**Last Updated:** January 12, 2026  
**Status:** Planning - Pending Decisions  
**Purpose:** Document infrastructure requirements and migration path for production readiness

---

## Executive Summary

Stress testing revealed that the current Emergent-hosted infrastructure cannot support the planned 400-user, 50-league pilot at acceptable performance levels. Two key bottlenecks have been identified:

1. **MongoDB latency** (~700ms baseline) - Emergent's shared Atlas cluster
2. **Redis connection limits** - Upgraded but still showing issues at scale

**Current Capacity:** 2-5 concurrent leagues at 100% reliability  
**Target Capacity:** 50 concurrent leagues at 99%+ reliability  
**Gap:** Significant infrastructure upgrades required

---

## Current Infrastructure

### Emergent-Hosted Stack

| Component | Current Setup | Limitation |
|-----------|---------------|------------|
| **Application** | Emergent Kubernetes (multi-pod) | Unknown pod count |
| **MongoDB** | Shared Atlas cluster (`customer-apps.oxfwhh.mongodb.net`) | ~700ms latency per query |
| **Redis** | Redis Cloud Essentials (256 connections) | Adequate for current scale |
| **Socket.IO** | Redis adapter for multi-pod | Working but errors at scale |

### Performance Baseline (January 2026)

| Scale | Bid Success | p50 Latency | p99 Latency | Verdict |
|-------|-------------|-------------|-------------|---------|
| 2 leagues (16 users) | 100% | 688ms | 1,517ms | ✅ Acceptable |
| 5 leagues (40 users) | 100% | ~700ms | ~2,000ms | ✅ Acceptable |
| 10 leagues (80 users) | ~90% | ~750ms | ~2,500ms | ⚠️ Marginal |
| 20 leagues (160 users) | 75-76% | ~800ms | 3,000-6,000ms | ❌ Not acceptable |
| 50 leagues (400 users) | Unknown | Unknown | Unknown | ❌ Likely worse |

---

## Identified Issues

### Issue 1: MongoDB Network Latency

**Problem:** Every bid requires 7-8 database queries. Each query adds ~50-100ms network round-trip to Emergent's shared MongoDB Atlas cluster.

**Evidence:**
- Preview (localhost MongoDB): 357ms average latency
- Production (remote Atlas): 713ms average latency
- Minimum latency floor: ~650ms (cannot go lower with current setup)

**Impact:**
- Poor user experience during bidding
- Requests queue up under load, causing timeouts
- Contributes to bid failures at scale

**Root Cause:** Emergent's shared MongoDB cluster (`customer-apps.oxfwhh.mongodb.net`) is:
- Shared across multiple Emergent customers
- Potentially in a different region than the application
- Not optimizable from application side

### Issue 2: Server Capacity at Scale

**Problem:** At 20 concurrent leagues, the server cannot process requests fast enough.

**Evidence:**
- "Semaphore timeout" errors (OS connection pool exhausted)
- "Namespace failed to connect" errors (Socket.IO overload)
- 75% bid success rate (25% failures)

**Impact:**
- Users experience failed bids
- Real-time updates delayed or missed
- Poor auction experience

**Root Cause:** Combination of:
- High baseline latency means requests take longer
- Requests queue up, causing cascading delays
- Possibly insufficient pod count for load

---

## Migration Options

### Option A: Optimize Within Emergent (Low Effort)

**Actions:**
1. Contact Emergent support to request:
   - Dedicated MongoDB cluster (or same-region placement)
   - Additional application pods
   - Information about infrastructure limits
2. Implement application-level caching (if Emergent can't help)

**Expected Outcome:**
- MongoDB latency: 700ms → 300-400ms (if same-region)
- Capacity: 20 leagues → 30-40 leagues
- Cost: £0-50/month additional

**Risk:** Emergent may not be able to accommodate requests

**Timeline:** 1-2 weeks (dependent on Emergent response)

---

### Option B: Bring Your Own MongoDB (Medium Effort)

**Actions:**
1. Create MongoDB Atlas account (mongodb.com)
2. Provision M10 dedicated cluster (~£45/month)
3. Choose region closest to Emergent's app servers
4. Export data from Emergent's MongoDB
5. Import to new cluster
6. Update `MONGO_URL` environment variable in Emergent
7. Redeploy

**Expected Outcome:**
- MongoDB latency: 700ms → 100-200ms
- Capacity: 20 leagues → 50+ leagues
- Cost: ~£45/month

**Risk:** Low - MongoDB is swappable via connection string

**Timeline:** 2-4 hours

**Data Migration Steps:**
```bash
# 1. Export from Emergent's MongoDB
mongodump --uri="mongodb+srv://...@customer-apps.oxfwhh.mongodb.net/bidding-tester"

# 2. Import to your new cluster
mongorestore --uri="mongodb+srv://...@your-cluster.mongodb.net/bidding-tester"

# 3. Update Emergent environment variable
MONGO_URL=mongodb+srv://...@your-cluster.mongodb.net/bidding-tester

# 4. Redeploy via Emergent
```

---

### Option C: Full Self-Hosting (High Effort)

**Actions:**
1. Set up infrastructure on Railway, Render, or AWS/GCP
2. Deploy application containers
3. Provision dedicated MongoDB (Atlas M10+)
4. Provision dedicated Redis
5. Configure DNS and SSL
6. Migrate data
7. Update DNS to point to new infrastructure

**Expected Outcome:**
- Full control over all infrastructure
- MongoDB latency: 50-100ms (co-located)
- Capacity: 100+ leagues
- Cost: £100-200/month

**Risk:** Medium - More DevOps responsibility, migration complexity

**Timeline:** 1-2 weeks

---

## Recommended Path

### Phase 1: Contact Emergent (This Week)

**Send this request to Emergent support:**

```
Subject: Infrastructure Support Request - High-Concurrency Application

We're preparing for a 400-user pilot and stress testing has revealed performance 
bottlenecks with the current infrastructure.

Current issues:
- MongoDB latency: ~700ms baseline (shared cluster: customer-apps.oxfwhh.mongodb.net)
- Bid success rate drops to 75% at 20 concurrent leagues
- Target: 50 concurrent leagues at 99%+ success rate

Questions:
1. Can we get a dedicated MongoDB cluster or same-region placement?
2. How many application pods are currently allocated?
3. Can we increase pod count for our deployment?
4. Are there any recommended configurations for high-concurrency real-time apps?

Test data available:
- 2 leagues: 100% success, 688ms p50, 1517ms p99
- 20 leagues: 76% success, 800ms p50, 3121ms p99

Timeline: Pilot launch in [X weeks]
```

### Phase 2: Based on Emergent Response

**If Emergent can help:**
- Work with them to implement improvements
- Retest at scale
- Proceed to pilot

**If Emergent cannot help:**
- Proceed with Option B (Bring Your Own MongoDB)
- Provision M10 cluster in same region as Emergent app
- Migrate data and retest
- Expected improvement: 700ms → 100-200ms latency

### Phase 3: Pre-Pilot Validation

**Success criteria before pilot:**
- [ ] 20-league test: 99%+ bid success rate
- [ ] p99 latency: < 2 seconds
- [ ] No Socket.IO connection failures
- [ ] Competitive bidding test (anti-snipe) passes

---

## Cost Summary

| Scenario | MongoDB | Redis | Total Monthly |
|----------|---------|-------|---------------|
| Current (Emergent managed) | £0 | £5 | £5 |
| Option B (Own MongoDB) | £45 | £5 | £50 |
| Option C (Full self-host) | £45-90 | £10-20 | £100-200 |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Emergent can't improve MongoDB | Medium | High | Proceed with Option B |
| Data migration causes issues | Low | Medium | Test migration on staging first |
| New MongoDB has different issues | Low | Medium | Choose well-reviewed Atlas region |
| Pilot overloads new infrastructure | Medium | High | Load test before pilot |

---

## Open Questions

1. **Emergent response** - What can they offer for MongoDB/pods?
2. **Region selection** - Where is Emergent's app hosted? (Need same region for MongoDB)
3. **Pilot timeline** - How much time do we have to implement fixes?
4. **Fallback plan** - If 50 leagues isn't achievable, what's minimum viable for pilot?

---

## Appendix: Test Results Archive

### Small Scale (2 leagues, 8 users) - Post Redis Upgrade
```
Date: January 12, 2026
p50: 688ms | p95: 993ms | p99: 1,517ms
Bid Success: 100%
Socket Errors: Minor (2 members)
Verdict: Acceptable
```

### Large Scale (20 leagues, 160 users) - Post Redis Upgrade
```
Date: January 12, 2026
p50: 800ms | p95: 1,858ms | p99: 3,121ms
Bid Success: 76.4%
Socket Errors: Many (namespace failures, timeouts)
Verdict: Not acceptable for production
```

### Preview Environment (localhost MongoDB)
```
Date: January 10, 2026
p50: 357ms | p95: 407ms | p99: 416ms
Bid Success: 100%
Verdict: Target performance level
```

---

## Document History

| Date | Change |
|------|--------|
| Jan 12, 2026 | Created based on stress test findings |
| Jan 11, 2026 | Redis upgraded to Essentials tier |
| Jan 10, 2026 | Initial stress testing completed |

