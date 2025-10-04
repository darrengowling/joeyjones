#!/usr/bin/env python3
"""
Test script for cricket points calculator
Tests the function with representative inputs to verify expected outputs
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

from services.scoring.cricket import get_cricket_points

def test_cricket_points():
    """Test cricket points calculator with representative inputs"""
    
    # Test schema based on the cricket sport configuration
    schema = {
        "type": "perPlayerMatch",
        "rules": {
            "run": 1,
            "wicket": 25,
            "catch": 10,
            "stumping": 15,
            "runOut": 10
        },
        "milestones": {
            "halfCentury": {
                "enabled": True,
                "threshold": 50,
                "points": 10
            },
            "century": {
                "enabled": True,
                "threshold": 100,
                "points": 25
            },
            "fiveWicketHaul": {
                "enabled": True,
                "threshold": 5,
                "points": 25
            }
        }
    }
    
    test_cases = [
        # Test Case 1: Basic batting performance (no milestones)
        {
            "name": "Basic batting (30 runs, 1 catch)",
            "line": {"runs": 30, "wickets": 0, "catches": 1, "stumpings": 0, "runOuts": 0},
            "expected": 30 * 1 + 1 * 10,  # 30 + 10 = 40
        },
        
        # Test Case 2: Bowling performance with wickets
        {
            "name": "Good bowling (2 wickets, 1 catch)",
            "line": {"runs": 15, "wickets": 2, "catches": 1, "stumpings": 0, "runOuts": 0},
            "expected": 15 * 1 + 2 * 25 + 1 * 10,  # 15 + 50 + 10 = 75
        },
        
        # Test Case 3: Half-century milestone
        {
            "name": "Half-century (65 runs)",
            "line": {"runs": 65, "wickets": 0, "catches": 0, "stumpings": 0, "runOuts": 0},
            "expected": 65 * 1 + 10,  # 65 + 10 (half-century bonus) = 75
        },
        
        # Test Case 4: Century milestone (includes half-century)
        {
            "name": "Century (120 runs)",
            "line": {"runs": 120, "wickets": 0, "catches": 0, "stumpings": 0, "runOuts": 0},
            "expected": 120 * 1 + 10 + 25,  # 120 + 10 (half-century) + 25 (century) = 155
        },
        
        # Test Case 5: Five-wicket haul
        {
            "name": "Five-wicket haul (6 wickets)",
            "line": {"runs": 8, "wickets": 6, "catches": 0, "stumpings": 0, "runOuts": 0},
            "expected": 8 * 1 + 6 * 25 + 25,  # 8 + 150 + 25 (fifer bonus) = 183
        },
        
        # Test Case 6: All-rounder performance
        {
            "name": "All-rounder (45 runs, 3 wickets, 2 catches)",
            "line": {"runs": 45, "wickets": 3, "catches": 2, "stumpings": 0, "runOuts": 0},
            "expected": 45 * 1 + 3 * 25 + 2 * 10,  # 45 + 75 + 20 = 140
        },
        
        # Test Case 7: Wicket-keeper performance
        {
            "name": "Wicket-keeper (25 runs, 0 wickets, 1 catch, 2 stumpings)",
            "line": {"runs": 25, "wickets": 0, "catches": 1, "stumpings": 2, "runOuts": 0},
            "expected": 25 * 1 + 1 * 10 + 2 * 15,  # 25 + 10 + 30 = 65
        },
        
        # Test Case 8: Fielding specialist
        {
            "name": "Great fielder (5 runs, 0 wickets, 3 catches, 0 stumpings, 2 runOuts)",
            "line": {"runs": 5, "wickets": 0, "catches": 3, "stumpings": 0, "runOuts": 2},
            "expected": 5 * 1 + 3 * 10 + 2 * 10,  # 5 + 30 + 20 = 55
        },
        
        # Test Case 9: Zero performance
        {
            "name": "No contribution",
            "line": {"runs": 0, "wickets": 0, "catches": 0, "stumpings": 0, "runOuts": 0},
            "expected": 0,
        },
        
        # Test Case 10: Missing fields (should default to 0)
        {
            "name": "Missing fields",
            "line": {"runs": 20},  # Only runs provided
            "expected": 20 * 1,  # 20
        }
    ]
    
    print("🏏 Testing Cricket Points Calculator")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            result = get_cricket_points(test_case["line"], schema)
            expected = test_case["expected"]
            
            if result == expected:
                print(f"✅ {test_case['name']}: {result} points (expected {expected})")
                passed += 1
            else:
                print(f"❌ {test_case['name']}: {result} points (expected {expected})")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_case['name']}: ERROR - {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Cricket points calculator is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = test_cricket_points()
    sys.exit(0 if success else 1)