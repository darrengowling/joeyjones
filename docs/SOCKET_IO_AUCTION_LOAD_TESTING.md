# Socket.IO Auction Load Testing Guide
## Testing Real-Time Bidding Performance

## Overview
This guide covers load testing the most critical path in the system: real-time auction bidding with Socket.IO. Tests concurrent users bidding simultaneously and measures broadcast performance.

---

## Quick Start

### Prerequisites

**1. Create a Test Auction**:
```bash
# Go to your app
https://cricket-fantasy-app-2.preview.emergentagent.com

# Steps:
1. Sign in
2. Create a test league (or use existing NZ vs ENG league)
3. Start an auction
4. Copy the auction ID from URL (e.g., /auction/abc-123-def)
```

**2. Set Environment Variable**:
```bash
export TEST_AUCTION_ID=your-auction-id-here
# Example: export TEST_AUCTION_ID=abc-123-def-456
```

**3. Run Test**:
```bash
/app/tests/load/run_auction_test.sh
```

---

## Test Scenarios

### Scenario 1: Small Test (10 bidders, 2 min)
**Purpose**: Quick validation that Socket.IO works under load
**Usage**: Pre-demo smoke test
```bash
export TEST_AUCTION_ID=your-id
/app/tests/load/run_auction_test.sh
# Select option 1
```

### Scenario 2: Medium Test (30 bidders, 5 min)
**Purpose**: Realistic pilot scenario
**Usage**: Most common auction size
```bash
export TEST_AUCTION_ID=your-id
/app/tests/load/run_auction_test.sh
# Select option 2
```

### Scenario 3: Large Test (50 bidders, 10 min)
**Purpose**: Large pilot auction
**Usage**: Stress test for popular auctions
```bash
export TEST_AUCTION_ID=your-id
/app/tests/load/run_auction_test.sh
# Select option 3
```

### Scenario 4: Extreme Test (100 bidders, 15 min)
**Purpose**: Find breaking point
**Usage**: Understand system limits
```bash
export TEST_AUCTION_ID=your-id
/app/tests/load/run_auction_test.sh
# Select option 4
```

---

## What Gets Tested

### Socket.IO Performance
- Connection establishment time
- Room join latency
- Bid broadcast latency (critical!)
- Timer update handling
- Reconnection resilience

### Concurrent Bidding
- Multiple users bidding on same lot
- Database write contention
- Bid validation under load
- Race condition handling

### Real-Time Updates
- Broadcast performance (1 bid → 150 clients)
- Message queue handling
- Client update latency
- UI responsiveness

---

## Reading Results

### Key Metrics

**Connection Time**:
- Good: < 500ms
- Acceptable: < 1000ms
- Poor: > 2000ms

**Bid Placement**:
- Good: < 200ms
- Acceptable: < 500ms
- Poor: > 1000ms

**Bid Broadcast (Critical!)**:
- Good: < 100ms (users see bids immediately)
- Acceptable: < 300ms (slight delay)
- Poor: > 500ms (noticeable lag)

**Success Rate**:
- Excellent: > 99%
- Good: > 95%
- Problematic: < 90%

### Example Output

```
📊 SUMMARY STATISTICS:
Total requests: 5,432
Total failures: 54
Average response time: 125ms
Max response time: 890ms
Requests/sec: 18.5

📡 SOCKET.IO METRICS:
  Connect & Join Room:
    Requests: 50
    Failures: 0
    Avg: 450ms
    P95: 650ms
  
  Event: bid_placed:
    Requests: 2,500
    Failures: 0
    Avg: 85ms    ← Broadcast latency
    P95: 150ms   ← 95% of bids arrive within 150ms

🎯 AUCTION PERFORMANCE:
  Total bids: 2,500
  Failed bids: 25
  Success rate: 99.0%
  Avg bid time: 120ms
```

---

## Interpreting Results

### ✅ Excellent Performance

**Indicators**:
- Bid broadcast < 100ms (P95)
- Success rate > 99%
- No connection failures
- Smooth concurrent bidding

**Action**: System ready for pilot

### ⚠️ Acceptable Performance

**Indicators**:
- Bid broadcast 100-300ms (P95)
- Success rate 95-99%
- Few connection timeouts
- Occasional bid conflicts

**Action**: 
- Monitor closely during pilot
- Limit concurrent users per auction to tested level
- Document any workarounds

### ❌ Poor Performance

**Indicators**:
- Bid broadcast > 500ms (P95)
- Success rate < 95%
- Many connection failures
- Frequent bid errors

**Action**:
- Reduce max users per auction
- Investigate bottlenecks (see below)
- Consider infrastructure upgrades

---

## Troubleshooting

### High Bid Broadcast Latency (> 500ms)

**Possible Causes**:
1. Too many Socket.IO connections
2. Inefficient broadcast implementation
3. Network bottleneck
4. CPU overload

**Solutions**:
```bash
# Check system resources during test
top

# Check Socket.IO connections
# (In browser devtools during test)
socket.io.engine.transport.ws.bufferedAmount

# Reduce concurrent users
# Test with 30 → 50 → 80 to find breaking point
```

### High Bid Failure Rate (> 5%)

**Possible Causes**:
1. Database write contention
2. Validation errors
3. Race conditions
4. Budget conflicts

**Solutions**:
```bash
# Check database performance
mongo mongodb://localhost:27017/test_database \
  --eval "db.currentOp()"

# Check backend logs for errors
tail -f /var/log/supervisor/backend.err.log | grep -i bid

# Review bid validation logic
```

### Socket.IO Connection Failures

**Possible Causes**:
1. Connection pool exhaustion
2. WebSocket issues
3. Firewall/proxy blocking
4. Memory leaks

**Solutions**:
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.out.log | grep -i socket

# Restart backend
sudo supervisorctl restart backend

# Test WebSocket connectivity
wscat -c wss://cricket-bid-arena.preview.emergentagent.com/api/socket.io/
```

---

## Best Practices

### Before Running Tests

1. **Create dedicated test auction**
   - Don't use production auctions
   - Use test data only

2. **Clear test data after**
   - Remove test users
   - Clean up test bids

3. **Monitor during test**
   - Watch system resources (top)
   - Monitor backend logs
   - Check health endpoint

### During Pilot

1. **Start small**
   - First auctions: Max 30 users
   - Monitor performance
   - Scale up gradually

2. **Monitor actively**
   - Watch first 5-10 minutes closely
   - Check for lag or errors
   - Have ops playbook ready

3. **Communicate limits**
   - Document tested capacity
   - Set expectations with users
   - Have backup plan

---

## Advanced: Manual Testing

If automated load test doesn't work or you need real user behavior:

### Setup Team Test

**Requirements**:
- 10-20 team members
- 15-30 minutes
- Test auction with real assets

**Procedure**:
1. Create test auction
2. Share link with team
3. Everyone joins at same time
4. Bid actively for 10 minutes
5. Monitor:
   - UI responsiveness
   - Bid latency
   - Any crashes
   - System resources

**Metrics to Track**:
- Time from bid click to UI update
- Any errors in browser console
- Number of concurrent users handled
- Subjective: "Does it feel smooth?"

---

## Comparison: API vs Auction Load

**API Load Test** (Already run):
- ✅ Tests API endpoints
- ✅ Tests authentication
- ✅ Tests database queries
- ❌ Doesn't test Socket.IO
- ❌ Doesn't test real-time bidding

**Auction Load Test** (New):
- ✅ Tests Socket.IO connections
- ✅ Tests concurrent bidding
- ✅ Tests real-time broadcasts
- ✅ Tests most vulnerable path
- 🎯 Critical for pilot confidence

---

## Pilot Rollout Strategy

Based on load test results:

### Phase 1: Small Auctions (Week 1)
- **Max users**: 30 per auction
- **Rationale**: Safely below tested limit
- **Monitoring**: Close observation
- **Success criteria**: No issues, smooth experience

### Phase 2: Medium Auctions (Week 2)
- **Max users**: 50 per auction
- **Rationale**: Scale up if Phase 1 successful
- **Monitoring**: Active monitoring
- **Success criteria**: Acceptable latency (< 300ms)

### Phase 3: Large Auctions (Week 3)
- **Max users**: 80-100 per auction
- **Rationale**: Approach tested limits
- **Monitoring**: Very close monitoring
- **Success criteria**: No degradation from Phase 2

### Scaling Decision Points
- ✅ If all smooth → Scale to next phase
- ⚠️ If minor issues → Fix, then scale
- ❌ If major issues → Stay at current level, optimize

---

## Support

**Documentation**: `/app/docs/SOCKET_IO_AUCTION_LOAD_TESTING.md`
**Test Script**: `/app/tests/load/auction_socketio_test.py`
**Runner**: `/app/tests/load/run_auction_test.sh`

**Common Commands**:
```bash
# Set test auction
export TEST_AUCTION_ID=your-auction-id

# Run test
/app/tests/load/run_auction_test.sh

# View results
ls -lh /app/tests/load/reports/

# Check if test running
ps aux | grep locust
```

**Getting Help**:
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Check system resources: `top`
- Review operations playbook: `/app/docs/OPERATIONS_PLAYBOOK.md`
