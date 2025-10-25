#!/bin/bash
echo "=========================================="
echo "🏏 Waiting for NZ vs England Match"
echo "Checking every 15 minutes..."
echo "Current time: $(date -u)"
echo "Expected start: 01:00 UTC Oct 26"
echo "=========================================="
echo ""

cd /app/scripts

while true; do
    echo "Checking at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    python test_cricketdata_api.py --find-match 2>&1 | grep -A 5 "FOUND POTENTIAL MATCH\|NZ vs England match not found"
    
    if python test_cricketdata_api.py --find-match 2>&1 | grep -q "FOUND POTENTIAL MATCH"; then
        echo ""
        echo "✅ MATCH FOUND! Starting continuous monitoring..."
        break
    fi
    
    echo "⏰ Next check in 15 minutes..."
    echo ""
    sleep 900  # 15 minutes
done
