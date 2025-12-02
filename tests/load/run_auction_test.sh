#!/bin/bash
#
# Socket.IO Auction Load Test Setup & Runner
# Production Hardening - Load Testing
#

echo "======================================"
echo "Socket.IO Auction Load Test"
echo "======================================"
echo ""

# Check if TEST_AUCTION_ID is set
if [ -z "$TEST_AUCTION_ID" ]; then
    echo "⚠️  TEST_AUCTION_ID environment variable not set"
    echo ""
    echo "You need to create a test auction first:"
    echo ""
    echo "1. Go to: https://bat-and-ball-18.preview.emergentagent.com"
    echo "2. Create a test league (or use existing)"
    echo "3. Start an auction"
    echo "4. Copy the auction ID from the URL"
    echo ""
    echo "Then run:"
    echo "  export TEST_AUCTION_ID=your-auction-id-here"
    echo "  $0"
    echo ""
    exit 1
fi

echo "✅ Test Auction ID: $TEST_AUCTION_ID"
echo ""

# Test scenarios
echo "Available test scenarios:"
echo ""
echo "1. Small test (10 bidders, 2 minutes)"
echo "2. Medium test (30 bidders, 5 minutes)"
echo "3. Large test (50 bidders, 10 minutes)"
echo "4. Extreme test (100 bidders, 15 minutes)"
echo "5. Custom"
echo ""

read -p "Select scenario (1-5): " SCENARIO

case $SCENARIO in
    1)
        USERS=10
        SPAWN_RATE=2
        RUN_TIME="2m"
        ;;
    2)
        USERS=30
        SPAWN_RATE=5
        RUN_TIME="5m"
        ;;
    3)
        USERS=50
        SPAWN_RATE=10
        RUN_TIME="10m"
        ;;
    4)
        USERS=100
        SPAWN_RATE=15
        RUN_TIME="15m"
        ;;
    5)
        read -p "Number of users: " USERS
        read -p "Spawn rate (users/sec): " SPAWN_RATE
        read -p "Run time (e.g., 10m): " RUN_TIME
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Test Configuration"
echo "======================================"
echo "Auction ID: $TEST_AUCTION_ID"
echo "Users: $USERS concurrent bidders"
echo "Spawn rate: $SPAWN_RATE users/second"
echo "Duration: $RUN_TIME"
echo ""
read -p "Press Enter to start test (Ctrl+C to cancel)..."

# Create reports directory
mkdir -p /app/tests/load/reports

# Run test
REPORT_NAME="auction_socketio_${USERS}users_$(date +%Y%m%d_%H%M%S)"

echo ""
echo "🚀 Starting auction load test..."
echo ""

cd /app/tests/load

locust -f auction_socketio_test.py \
    --host=https://bat-and-ball-18.preview.emergentagent.com \
    --users=$USERS \
    --spawn-rate=$SPAWN_RATE \
    --run-time=$RUN_TIME \
    --html=reports/${REPORT_NAME}.html \
    --csv=reports/${REPORT_NAME} \
    --headless

EXIT_CODE=$?

echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test completed successfully"
    echo ""
    echo "Reports generated:"
    echo "  HTML: /app/tests/load/reports/${REPORT_NAME}.html"
    echo "  CSV:  /app/tests/load/reports/${REPORT_NAME}_stats.csv"
    echo ""
    
    # Show quick summary
    echo "Quick Summary:"
    tail -1 /app/tests/load/reports/${REPORT_NAME}_stats.csv
else
    echo "❌ Test failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs for errors"
fi

echo ""
echo "======================================"
