#!/bin/bash
# Quick Start Script for Shadow Testing
# Run this tomorrow when the match starts!

echo "=============================================="
echo "🏏 NZ vs ENGLAND ODI 1 - SHADOW TESTING"
echo "=============================================="
echo ""

cd /app/scripts

echo "Step 1: Finding NZ vs England match..."
echo ""
/root/.venv/bin/python3 test_cricketdata_api.py --find-match

echo ""
echo "=============================================="
echo "📋 NEXT STEPS:"
echo "=============================================="
echo ""
echo "If a match was found above, you'll see:"
echo "  ✅ FOUND POTENTIAL MATCH:"
echo "     ID: <some-long-id>"
echo ""
echo "Copy that ID and run:"
echo "  /root/.venv/bin/python3 test_cricketdata_api.py --match-id <paste-id-here> --monitor"
echo ""
echo "Or just come back here and ask the AI to help!"
echo ""
