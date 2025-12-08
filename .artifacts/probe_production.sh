#!/bin/bash
PROD_URL="https://draft-kings-mobile.emergent.host"

echo "=== CORS OPTIONS Probe ===" > /app/.artifacts/cors_probe_prod.txt
curl -X OPTIONS "${PROD_URL}/api/auction/test/bid" \
  -H "Origin: ${PROD_URL}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,X-User-ID" \
  -v -s 2>&1 >> /app/.artifacts/cors_probe_prod.txt

echo "=== POST Bid Probe ===" >> /app/.artifacts/cors_probe_prod.txt
curl -X POST "${PROD_URL}/api/auction/test-uuid-12345/bid" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: probe-user" \
  -d '{"userId":"probe-user","amount":1000000}' \
  -v -s --max-time 10 2>&1 >> /app/.artifacts/cors_probe_prod.txt

echo "=== Socket.IO Handshake ===" > /app/.artifacts/socket_probe_prod.txt
curl -s "${PROD_URL}/api/socket.io/?EIO=4&transport=polling" \
  -v 2>&1 >> /app/.artifacts/socket_probe_prod.txt

echo "=== Ingress Snapshot ===" > /app/.artifacts/prod_ingress_snapshot.txt
curl -I "${PROD_URL}/api/health" 2>&1 >> /app/.artifacts/prod_ingress_snapshot.txt
curl -I "${PROD_URL}/" 2>&1 >> /app/.artifacts/prod_ingress_snapshot.txt

echo "=== Bid Probe Timing (5 attempts) ===" > /app/.artifacts/bid_attempt_trace_prod.ndjson
for i in {1..5}; do
  RESULT=$(curl -X POST "${PROD_URL}/api/auction/probe-${i}/bid" \
    -H "Content-Type: application/json" \
    -H "X-User-ID: probe-user" \
    -d '{"userId":"probe-user","amount":1000000}' \
    -w '{"ts":"%{time_iso8601}","method":"POST","url":"%{url}","status":%{http_code},"ttfb_ms":%{time_starttransfer},"total_ms":%{time_total},"size":%{size_download}}' \
    -s --max-time 10 -o /dev/null)
  echo "$RESULT" >> /app/.artifacts/bid_attempt_trace_prod.ndjson
  sleep 0.2
done
