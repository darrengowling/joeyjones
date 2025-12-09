# Load Testing Scenarios for Multi-Sport Auction Platform

## Quick Start

### Scenario 1: 150 Users, Single Auction (Worst Case)
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --users=150 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=/app/tests/load/reports/scenario1_150users.html \
  --csv=/app/tests/load/reports/scenario1_150users \
  --headless
```

### Scenario 2: 50 Users per Auction, 3 Concurrent Auctions (Realistic)
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --users=150 \
  --spawn-rate=15 \
  --run-time=15m \
  --html=/app/tests/load/reports/scenario2_concurrent.html \
  --csv=/app/tests/load/reports/scenario2_concurrent \
  --headless
```

### Scenario 3: 2-Hour Endurance Test (Stability)
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --users=100 \
  --spawn-rate=5 \
  --run-time=2h \
  --html=/app/tests/load/reports/scenario3_endurance.html \
  --csv=/app/tests/load/reports/scenario3_endurance \
  --headless
```

### Scenario 4: Gradual Ramp-Up (Performance Profiling)
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --users=200 \
  --spawn-rate=2 \
  --run-time=30m \
  --html=/app/tests/load/reports/scenario4_rampup.html \
  --csv=/app/tests/load/reports/scenario4_rampup \
  --headless
```

### Scenario 5: Spike Test (Sudden Load)
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --users=300 \
  --spawn-rate=50 \
  --run-time=5m \
  --html=/app/tests/load/reports/scenario5_spike.html \
  --csv=/app/tests/load/reports/scenario5_spike \
  --headless
```

## Interactive Mode (with Web UI)

Start Locust web interface:
```bash
locust -f /app/tests/load/locustfile.py \
  --host=https://livebid-2.preview.emergentagent.com \
  --web-host=0.0.0.0 \
  --web-port=8089
```

Then access: http://localhost:8089

## Key Metrics to Monitor

### Response Time Targets
- **P50 (Median)**: < 200ms
- **P95**: < 500ms
- **P99**: < 1000ms
- **Max**: < 3000ms

### Throughput Targets
- **Requests/sec**: > 100 RPS
- **Concurrent users**: 150+
- **Success rate**: > 99%

### Critical Endpoints to Watch
1. `/api/auth/verify-magic-link` - Authentication bottleneck?
2. `/api/auction/:id/bid` - Real-time bidding performance
3. `/api/leagues` - List queries with indexes
4. `/api/assets` - Asset queries with sportKey index

## Results Analysis

After each test, check:
1. HTML report: `/app/tests/load/reports/scenario_X.html`
2. CSV data: `/app/tests/load/reports/scenario_X_stats.csv`
3. Backend logs: `tail -f /var/log/supervisor/backend.out.log`
4. Database performance: Monitor MongoDB slow queries

## Interpreting Results

### Good Performance
- P95 response time < 500ms
- Failure rate < 1%
- No connection errors
- Stable throughput

### Performance Issues
- P95 > 1000ms - Investigate slow queries
- Failure rate > 5% - Check error logs
- Increasing response times - Memory leak?
- Connection timeouts - Scale database?

### Common Bottlenecks
1. **Database**: Missing indexes, slow aggregations
2. **Authentication**: JWT verification overhead
3. **Socket.IO**: Too many concurrent connections
4. **API**: Unoptimized queries, N+1 problems

## Next Steps After Load Testing

1. **Identify bottlenecks** from reports
2. **Optimize slow endpoints** (add indexes, cache, optimize queries)
3. **Re-test** to validate improvements
4. **Document** performance characteristics
5. **Set up monitoring** (Prometheus, Grafana) for production
