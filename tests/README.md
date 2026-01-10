# Auction Stress Test Suite

Load testing tool for the Sport X auction system.

## Quick Start

### 1. Install Dependencies
```bash
pip install "python-socketio[asyncio_client]" aiohttp
```

### 2. Run Against Production

```bash
# Single test mode
python auction_stress_test.py \
  --mode hot-lot \
  --invite-token YOUR_LEAGUE_TOKEN \
  --commissioner-email commissioner@email.com \
  --url https://your-app.emergent.sh \
  --use-existing-members \
  --users 10

# Run ALL test modes (race-condition → hot-lot → full-auction)
python auction_stress_test.py \
  --mode all \
  --invite-token YOUR_LEAGUE_TOKEN \
  --commissioner-email commissioner@email.com \
  --url https://your-app.emergent.sh \
  --use-existing-members \
  --users 10
```

### 3. Run Against Local/Preview
```bash
python auction_stress_test.py \
  --mode hot-lot \
  --invite-token YOUR_LEAGUE_TOKEN \
  --commissioner-email commissioner@email.com \
  --use-existing-members
```

## Test Modes

| Mode | Description | Duration | Best For |
|------|-------------|----------|----------|
| `hot-lot` | 7+ users bid aggressively on one team | ~5 min | Bid throughput, anti-snipe |
| `race-condition` | All users bid simultaneously | ~30 sec | Conflict resolution |
| `full-auction` | Complete 32-team auction | 45-60 min | Sustained load, stability |
| `all` | Runs all 3 modes sequentially | ~1 hour | Full validation |

## CLI Options

| Option | Required | Description |
|--------|----------|-------------|
| `--mode` | Yes | Test mode: `hot-lot`, `full-auction`, `race-condition`, or `all` |
| `--invite-token` | Yes | League invite token |
| `--url` | No | Production URL (default: localhost:8001) |
| `--commissioner-email` | No | Commissioner's email for privileged operations |
| `--users` | No | Number of test users (default: 7) |
| `--use-existing-members` | No | Use existing league members (for full leagues) |

## Interpreting Results

### Key Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Bid Success Rate | >50% | 30-50% | <30% |
| HTTP Latency p99 | <100ms | 100-500ms | >500ms |
| Socket Latency p99 | <50ms | 50-200ms | >200ms |
| Disconnects | 0 | 1-5 | >5 |

### Expected Behavior

- **Low success rate in hot-lot** is normal - users are racing for the same bid
- **Race condition test** should show only 1 bid accepted at the same price
- **Disconnects at test end** are normal (cleanup)

## Scaling for 400-User Pilot

### Pre-Pilot Checklist

1. **Create dedicated test league** with 400+ max managers
2. **Redis adapter** must be configured for multi-pod Socket.IO
3. **Run tests in waves**: 50 → 100 → 200 → 400 users
4. **Monitor server resources** during test (CPU, memory, connections)

### Running Large-Scale Test

```bash
# Wave 1: 50 users
python auction_stress_test.py --mode hot-lot --url https://prod.app.com \
  --invite-token TOKEN --commissioner-email EMAIL --users 50

# Wave 2: 100 users  
python auction_stress_test.py --mode hot-lot --url https://prod.app.com \
  --invite-token TOKEN --commissioner-email EMAIL --users 100

# Wave 3: Full scale
python auction_stress_test.py --mode all --url https://prod.app.com \
  --invite-token TOKEN --commissioner-email EMAIL --users 200
```

### Expected Bottlenecks at Scale

| Users | Likely Bottleneck | Mitigation |
|-------|-------------------|------------|
| 50-100 | None expected | - |
| 100-200 | Socket.IO broadcasts | Enable Redis adapter |
| 200-400 | MongoDB writes | Add write concern tuning |
| 400+ | Single auction instance | Consider sharding by league |

## Troubleshooting

### "User is not a participant in this league"
- League is full, use `--use-existing-members`
- Or create a new league with higher `maxManagers`

### "Only commissioner can begin auction"
- Add `--commissioner-email` with the league commissioner's email

### High failure rate (>70%)
- Check if auction is in "active" state
- Verify users are league members
- Check bid amounts vs budget limits

### Connection timeouts
- Production may have different Socket.IO path
- Check firewall/CORS settings
- Verify WebSocket upgrade is allowed

## Sample Output

```
============================================================
STRESS TEST REPORT
============================================================
Test Mode:      HOT-LOT
Duration:       48.1 seconds
Users:          7
League:         TestLeague

BID LATENCY (HTTP POST)
p50:  8ms
p95:  11ms
p99:  13ms

SOCKET BROADCAST LATENCY
p50:  6ms
p95:  8ms

RECOMMENDATIONS
✅ Bid latency acceptable (<1s p99)
✅ Error count acceptable
```
