# Auction Stress Test Suite

Load testing tools for the Sport X auction system.

## Two Test Scripts

| Script | Purpose | Use When |
|--------|---------|----------|
| `auction_stress_test.py` | Single league, detailed metrics | Testing bid mechanics, latency |
| `multi_league_stress_test.py` | Multiple concurrent leagues | Pre-pilot infrastructure validation |

---

## Quick Start

### 1. Install Dependencies
```bash
pip install "python-socketio[asyncio_client]" aiohttp
```

### 2. Download Scripts
Copy these files to your local machine:
- `auction_stress_test.py` - Single league test
- `multi_league_stress_test.py` - Multi-league concurrent test
- `leagues_config_template.json` - Config template

---

## Single League Test (`auction_stress_test.py`)

Tests bid mechanics within ONE league (8 users, 32 teams).

```bash
# Against production
python auction_stress_test.py \
  --mode hot-lot \
  --invite-token YOUR_TOKEN \
  --commissioner-email YOUR_EMAIL \
  --url https://your-app.emergent.sh \
  --use-existing-members

# Run all 3 test modes
python auction_stress_test.py \
  --mode all \
  --invite-token YOUR_TOKEN \
  --commissioner-email YOUR_EMAIL \
  --url https://your-app.emergent.sh \
  --use-existing-members
```

### Test Modes
| Mode | What it Tests |
|------|---------------|
| `hot-lot` | Aggressive bidding on one team |
| `race-condition` | Simultaneous bids at same price |
| `full-auction` | Complete 32-team auction |
| `all` | Runs all 3 sequentially |

---

## Multi-League Test (`multi_league_stress_test.py`)

**This is the pilot readiness test.** Simulates 10-20 leagues running concurrently.

### Setup
1. Create test leagues in production (each with 8 user slots)
2. Get invite tokens and commissioner emails for each
3. Create config file:

```json
{
    "leagues": [
        {"invite_token": "abc123", "commissioner_email": "user1@example.com"},
        {"invite_token": "def456", "commissioner_email": "user2@example.com"},
        {"invite_token": "ghi789", "commissioner_email": "user3@example.com"}
    ],
    "stagger_seconds": 10
}
```

### Run
```bash
# Quick validation (single league)
python multi_league_stress_test.py \
  --quick-test \
  --invite-token YOUR_TOKEN \
  --commissioner-email YOUR_EMAIL \
  --url https://your-app.emergent.sh

# Full multi-league test (pilot simulation)
python multi_league_stress_test.py \
  --config leagues.json \
  --url https://your-app.emergent.sh \
  --stagger 10
```

### What It Tests
- MongoDB handling writes from 10-20 concurrent auctions
- Socket.IO managing separate rooms simultaneously
- Timer accuracy across multiple auctions
- Overall system stability

---

## Interpreting Results

### Key Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Leagues completed | 100% | 90-99% | <90% |
| Bid Latency p99 | <100ms | 100-500ms | >500ms |
| Lots sold per league | 32 | 20-31 | <20 |

### Winner Determination (Clarification)
- First bidder at a price **holds the high bid**
- They remain high bidder until someone bids **higher**
- 5 bids at £1M = first bidder wins (others needed to bid £6M+ to outbid)

---

## Pilot Readiness Checklist

Before running 400-user pilot:

- [ ] Run `multi_league_stress_test.py` with 10 concurrent leagues
- [ ] All leagues complete successfully
- [ ] p99 latency < 100ms
- [ ] No Socket.IO disconnection errors
- [ ] Run `auction_stress_test.py --mode all` for detailed single-league metrics

---

## Troubleshooting

### "League not found"
- Verify invite token is correct
- Check league exists in production

### "User is not a participant"
- League is full (8 users max)
- Use `--use-existing-members` for single league test

### High latency (>500ms)
- Check network connection to production
- May indicate database contention - review MongoDB metrics

### Socket disconnections
- Production may have WebSocket timeout settings
- Check if Redis adapter is configured for multi-pod
