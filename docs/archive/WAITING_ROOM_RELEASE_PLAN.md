# Waiting Room Feature - Release Plan & Rollback Strategy

**Feature**: Commissioner-controlled auction start with waiting room
**Feature Flag**: `FEATURE_WAITING_ROOM`
**Version**: Prompt G Implementation
**Date**: 2025-10-25

---

## 🎯 Feature Overview

The waiting room feature allows commissioners to control when auctions start, replacing the previous behavior where auctions started immediately upon creation.

### Key Changes:
- **NEW**: Auctions created in "waiting" state by default
- **NEW**: `/auction/{id}/begin` endpoint for commissioner-controlled start
- **NEW**: Waiting room UI with participant list and "Begin Auction" button
- **PRESERVED**: All previous auction functionality (bidding, timers, completion)

---

## 🚦 Feature Flag Configuration

### Environment Variable:
```bash
FEATURE_WAITING_ROOM=true   # Enable waiting room (new behavior)
FEATURE_WAITING_ROOM=false  # Disable waiting room (legacy behavior)
```

### Behavior Matrix:

| Flag Value | `/leagues/{id}/auction/start` | `/auction/{id}/begin` | Auction Status |
|------------|-------------------------------|----------------------|----------------|
| `true`     | Creates in "waiting" state    | Available (200 OK)   | "waiting" → "active" |
| `false`    | Creates in "active" state     | Returns 404          | "active" immediately |

---

## 📊 Structured Logging

All critical events are logged with structured JSON for monitoring:

### Log Events:

**1. auction.created**
```json
{
  "event": "auction.created",
  "leagueId": "...",
  "auctionId": "...",
  "status": "waiting" | "active",
  "assetCount": 36,
  "sportKey": "football",
  "feature": "waiting_room_enabled" | "waiting_room_disabled_legacy_behavior"
}
```

**2. begin_auction.called**
```json
{
  "event": "begin_auction.called",
  "auctionId": "...",
  "leagueId": "...",
  "userId": "...",
  "commissionerId": "...",
  "auctionRoomSize": 5
}
```

**3. lot_started.emitted**
```json
{
  "event": "lot_started.emitted",
  "auctionId": "...",
  "leagueId": "...",
  "lotNumber": 1,
  "assetId": "...",
  "room": "auction:...",
  "roomSize": 5
}
```

**4. league_status_changed.emitted**
```json
{
  "event": "league_status_changed.emitted",
  "leagueId": "...",
  "auctionId": "...",
  "status": "auction_created" | "auction_started",
  "room": "league:...",
  "roomSize": 3
}
```

---

## 🚀 Release Strategy

### Phase 1: Staging Validation (Day 1)
**Environment**: Staging
**Flag**: `FEATURE_WAITING_ROOM=true`
**Duration**: Full test cycle (~2 hours)

**Actions**:
1. Deploy to staging with feature enabled
2. Run E2E smoke tests (Prompt F)
   - `01_waiting_room.spec.ts` - Core flow
   - `02_non_commissioner_forbidden.spec.ts` - Authorization
   - `03_concurrent_auctions_isolation.spec.ts` - Socket.IO isolation
   - `04_late_joiner.spec.ts` - Late joiner sync
3. Manual QA testing:
   - Create league → Start auction → See waiting room
   - Non-commissioner sees waiting message
   - Commissioner clicks "Begin" → Auction starts
   - Bidding works normally
4. Monitor logs for any errors

**Success Criteria**:
- ✅ All 4 E2E tests pass
- ✅ No errors in backend logs
- ✅ Socket.IO events delivered correctly
- ✅ Auction completes successfully with winning bids

**Rollback**: If tests fail, set `FEATURE_WAITING_ROOM=false` and redeploy

---

### Phase 2: Production Canary (Day 2)
**Environment**: Production
**Flag**: `FEATURE_WAITING_ROOM=true`
**Traffic**: 10% (via load balancer or A/B testing)
**Duration**: 1 hour

**Actions**:
1. Deploy to 10% of production traffic
2. Monitor metrics:
   - Auction creation success rate
   - `/auction/{id}/begin` success rate (should be ~90%+ for commissioners)
   - `/auction/{id}/begin` 403 rate (should be ~10% for non-commissioners trying)
   - Socket.IO event delivery latency
   - User complaints/support tickets
3. Monitor logs for:
   - `auction.created` events (status: "waiting")
   - `begin_auction.called` events
   - `lot_started.emitted` events
   - Any warnings or errors

**Success Criteria**:
- ✅ No increase in error rates
- ✅ `/auction/{id}/begin` 403s are expected (non-commissioners)
- ✅ Socket.IO events delivered within 500ms
- ✅ No user-reported issues
- ✅ Auction completion rate same as baseline

**Rollback**: If error rate > 5% or critical issues, set `FEATURE_WAITING_ROOM=false` and redeploy

---

### Phase 3: Production Full Rollout (Day 2)
**Environment**: Production
**Flag**: `FEATURE_WAITING_ROOM=true`
**Traffic**: 100%
**Duration**: Ongoing

**Actions**:
1. Promote to 100% traffic
2. Continue monitoring for 24 hours
3. Review user feedback
4. Monitor auction completion rates

**Success Criteria**:
- ✅ All metrics stable for 24 hours
- ✅ No regression in auction completion rates
- ✅ Positive user feedback on control feature

---

## 🔄 Rollback Strategy

### Instant Rollback Procedure

**When to Rollback**:
- Critical bugs preventing auctions from starting
- Socket.IO event delivery failures > 10%
- Authorization bypasses (non-commissioners starting auctions)
- User-reported confusion or UX issues
- Any data corruption in auction state

**Rollback Steps** (< 5 minutes):

1. **Set Feature Flag to False**:
   ```bash
   # In backend/.env
   FEATURE_WAITING_ROOM=false
   ```

2. **Redeploy Backend**:
   ```bash
   sudo supervisorctl restart backend
   # OR via deployment pipeline
   ```

3. **Verify Legacy Behavior**:
   - Create new league
   - Start auction
   - Verify auction starts immediately in "active" state
   - Verify `/auction/{id}/begin` returns 404

4. **Monitor Logs**:
   ```bash
   tail -f /var/log/supervisor/backend.*.log | grep "waiting_room_disabled_legacy_behavior"
   ```

5. **Notify Team**:
   - Post rollback notice in team channel
   - Document reason for rollback
   - Schedule post-mortem

### Impact of Rollback:

**Existing Auctions** (already in "waiting" state):
- ⚠️ Will remain in "waiting" state
- ⚠️ Commissioner cannot call `/auction/{id}/begin` (returns 404)
- ✅ Manual fix: Direct database update to set status="active" and start first lot

**New Auctions** (created after rollback):
- ✅ Start immediately in "active" state (legacy behavior)
- ✅ No waiting room shown
- ✅ All existing functionality works

**Recommendation**: 
- If rollback needed, manually transition any stuck "waiting" auctions to "active"
- Use admin script: `scripts/fix_waiting_auctions_after_rollback.py` (create if needed)

---

## 📈 Monitoring & Alerting

### Key Metrics to Monitor:

1. **Auction Creation Rate**
   - Metric: `auction.created` events per hour
   - Alert: If drops > 50% compared to baseline

2. **Begin Auction Success Rate**
   - Metric: `begin_auction.called` / `auction.created` (should be ~100%)
   - Alert: If < 80%

3. **Socket.IO Event Delivery**
   - Metric: `lot_started.emitted` events
   - Alert: If `roomSize = 0` (events not reaching clients)

4. **Authorization Errors**
   - Metric: `begin_auction.unauthorized` warnings
   - Expected: ~10-20% (non-commissioners trying)
   - Alert: If > 50% (indicates auth bug)

5. **Auction Completion Rate**
   - Metric: Auctions reaching "completed" status
   - Alert: If drops > 10% compared to baseline

### Log Queries:

**Check if feature is enabled**:
```bash
grep "Waiting Room feature enabled" /var/log/supervisor/backend.*.log
```

**Monitor auction creations**:
```bash
grep "auction.created" /var/log/supervisor/backend.*.log | tail -20
```

**Monitor begin_auction calls**:
```bash
grep "begin_auction.called" /var/log/supervisor/backend.*.log | tail -20
```

**Check for authorization issues**:
```bash
grep "begin_auction.unauthorized" /var/log/supervisor/backend.*.log
```

---

## 🧪 Testing Checklist

### Pre-Deployment:
- [ ] All E2E tests pass (Prompt F)
- [ ] Feature flag defaults to `true`
- [ ] Legacy behavior tested with flag set to `false`
- [ ] Logs include all required structured data

### During Canary:
- [ ] Monitor for 1 hour
- [ ] Check error rates every 15 minutes
- [ ] Verify Socket.IO events delivered
- [ ] No user-reported issues

### Post-Deployment:
- [ ] All metrics stable for 24 hours
- [ ] No regression in auction completion
- [ ] User feedback reviewed
- [ ] Documentation updated

---

## 📝 Rollback Decision Matrix

| Issue | Severity | Action | Rollback? |
|-------|----------|--------|-----------|
| E2E tests fail in staging | High | Fix bugs, re-test | Don't deploy |
| 403 errors for commissioners | Critical | Immediate rollback | Yes |
| Socket.IO events not delivered | Critical | Immediate rollback | Yes |
| Non-commissioners get 403 | Expected | No action needed | No |
| Waiting room UI confusing | Medium | UI iteration | No (fix forward) |
| Auction stuck in waiting | High | Manual fix + rollback | Yes |
| < 5% error rate increase | Low | Monitor closely | No |
| > 10% error rate increase | High | Rollback + investigate | Yes |

---

## 🎓 Training & Communication

### User Communication:
- [ ] Announce new "waiting room" feature in release notes
- [ ] Highlight commissioner control benefit
- [ ] Provide screenshot/video tutorial
- [ ] Update help documentation

### Team Training:
- [ ] Share this release plan with team
- [ ] Practice rollback procedure
- [ ] Assign on-call engineer for launch window
- [ ] Set up monitoring dashboard

---

## ✅ Launch Checklist

**Pre-Launch** (Day 1):
- [ ] Feature flag added to `.env`
- [ ] Comprehensive logging implemented
- [ ] E2E tests passing in staging
- [ ] Rollback procedure documented and practiced
- [ ] Monitoring dashboard configured
- [ ] On-call engineer assigned

**Launch Day** (Day 2):
- [ ] Deploy to canary (10%)
- [ ] Monitor for 1 hour
- [ ] Review logs and metrics
- [ ] Promote to 100% if clean
- [ ] Continue monitoring for 24 hours

**Post-Launch** (Day 3+):
- [ ] Review user feedback
- [ ] Analyze metrics vs baseline
- [ ] Document lessons learned
- [ ] Plan next iteration

---

## 📞 Emergency Contacts

- **On-Call Engineer**: [Your Name]
- **Product Owner**: [Product Owner]
- **DevOps Lead**: [DevOps Lead]
- **Rollback Authority**: [Engineering Manager]

---

## 🔗 Related Documents

- `WAITING_ROOM_REQUIREMENTS.md` - Original requirements
- `PROMPT_A_COMPLETION.md` through `PROMPT_E_COMPLETION.md` - Implementation docs
- `tests/e2e/01_waiting_room.spec.ts` - Core E2E test
- `tests/e2e/02_non_commissioner_forbidden.spec.ts` - Authorization test
- `tests/e2e/03_concurrent_auctions_isolation.spec.ts` - Socket.IO test
- `tests/e2e/04_late_joiner.spec.ts` - Late joiner test

---

**Last Updated**: 2025-10-25
**Status**: Ready for Staging Deployment
