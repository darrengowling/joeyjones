#!/bin/bash
# Helper script to upload match scores
# Usage: ./upload_match_scores.sh <league_id> <csv_file>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <league_id> <csv_file>"
    echo "Example: $0 abc123 match_1_scores.csv"
    exit 1
fi

LEAGUE_ID=$1
CSV_FILE=$2
API_URL="https://leaguepilot.preview.emergentagent.com/api"

echo "📊 Uploading match scores..."
echo "League ID: $LEAGUE_ID"
echo "CSV File: $CSV_FILE"
echo ""

curl -X POST "$API_URL/scoring/$LEAGUE_ID/ingest" \
  -F "file=@$CSV_FILE" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "✅ Upload complete!"
echo ""
echo "View leaderboard at:"
echo "$API_URL/scoring/$LEAGUE_ID/leaderboard"
