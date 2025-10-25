#!/usr/bin/env python3
"""
Cricket Scoring Configuration System Testing
Tests the complete cricket scoring configuration system including:
- PUT /api/leagues/{leagueId}/scoring-overrides endpoint
- Custom scoring rules validation and persistence
- Schema precedence (league overrides vs sport defaults)
- Custom milestone bonuses and disabled milestones
- Integration with scoring ingest system
"""

import requests
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://multisport-auction.preview.emergentagent.com/api"

class CricketScoringConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, files: dict = None, expected_status: int = 200) -> dict:
        """Test API endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                self.log(f"Expected {expected_status}, got {response.status_code}: {response.text}", "ERROR")
                return {"error": f"Status {response.status_code}", "text": response.text, "detail": response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else response.text}
                
            try:
                return response.json()
            except:
                return {"success": True, "text": response.text}
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return {"error": str(e)}
    
    def setup_test_data(self) -> bool:
        """Set up test user and cricket league"""
        self.log("=== Setting Up Test Data ===")
        
        # Create test user
        user_data = {
            "name": "Cricket Commissioner",
            "email": "cricket.commissioner@test.com"
        }
        
        result = self.test_api_endpoint("POST", "/users", user_data)
        if "error" in result:
            self.log("User creation failed", "ERROR")
            return False
            
        user_id = result.get("id")
        if not user_id:
            self.log("No user ID returned", "ERROR")
            return False
            
        self.test_data["user_id"] = user_id
        self.log(f"Created test user: {user_id}")
        
        # Create cricket league
        league_data = {
            "name": "Test Cricket League",
            "commissionerId": user_id,
            "budget": 50000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "cricket"  # Important: cricket league
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Cricket league creation failed", "ERROR")
            return False
            
        league_id = result.get("id")
        if not league_id:
            self.log("No league ID returned", "ERROR")
            return False
            
        self.test_data["league_id"] = league_id
        self.log(f"Created cricket league: {league_id}")
        
        # Join the league
        join_data = {
            "userId": user_id,
            "inviteToken": result.get("inviteToken")
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join cricket league", "ERROR")
            return False
        
        self.log("✅ Test data setup complete")
        return True
    
    def test_scoring_overrides_endpoint_validation(self) -> bool:
        """Test PUT /api/leagues/{leagueId}/scoring-overrides endpoint validation"""
        self.log("=== Testing Scoring Overrides Endpoint Validation ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for testing", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # Test 1: Valid scoring overrides
        self.log("Testing valid scoring overrides...")
        valid_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,
                    "wicket": 30,
                    "catch": 15,
                    "stumping": 20,
                    "runOut": 25
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": True,
                        "threshold": 50,
                        "points": 15
                    },
                    "century": {
                        "enabled": False,
                        "threshold": 100,
                        "points": 50
                    },
                    "fiveWicketHaul": {
                        "enabled": True,
                        "threshold": 5,
                        "points": 40
                    }
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", valid_overrides)
        if "error" in result:
            self.log(f"Valid scoring overrides failed: {result.get('text')}", "ERROR")
            return False
        
        # Verify the league was updated
        league_result = self.test_api_endpoint("GET", f"/leagues/{league_id}")
        if "error" in league_result:
            self.log("Failed to get updated league", "ERROR")
            return False
        
        scoring_overrides = league_result.get("scoringOverrides")
        if not scoring_overrides:
            self.log("Scoring overrides not saved to league", "ERROR")
            return False
        
        # Verify specific values
        rules = scoring_overrides.get("rules", {})
        if rules.get("run") != 2 or rules.get("wicket") != 30:
            self.log("Custom scoring rules not saved correctly", "ERROR")
            return False
        
        milestones = scoring_overrides.get("milestones", {})
        half_century = milestones.get("halfCentury", {})
        century = milestones.get("century", {})
        
        if half_century.get("enabled") != True or half_century.get("points") != 15:
            self.log("Half-century milestone not saved correctly", "ERROR")
            return False
        
        if century.get("enabled") != False or century.get("points") != 50:
            self.log("Century milestone not saved correctly", "ERROR")
            return False
        
        self.log("✅ Valid scoring overrides saved correctly")
        
        # Test 2: Missing required rules
        self.log("Testing missing required rules...")
        invalid_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,
                    "wicket": 30
                    # Missing catch, stumping, runOut
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", invalid_overrides, expected_status=400)
        detail = result.get("detail", "")
        if not detail or "Invalid or missing rule" not in detail:
            self.log(f"Missing rules validation failed. Expected error with 'Invalid or missing rule', got: {detail}", "ERROR")
            return False
        
        self.log("✅ Missing rules correctly rejected")
        
        # Test 3: Invalid rule values
        self.log("Testing invalid rule values...")
        invalid_values = {
            "scoringOverrides": {
                "rules": {
                    "run": "invalid",  # Should be numeric
                    "wicket": 30,
                    "catch": 15,
                    "stumping": 20,
                    "runOut": 25
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", invalid_values, expected_status=400)
        detail = result.get("detail", "")
        if not detail or "Invalid or missing rule" not in detail:
            self.log(f"Invalid rule values validation failed. Expected error with 'Invalid or missing rule', got: {detail}", "ERROR")
            return False
        
        self.log("✅ Invalid rule values correctly rejected")
        
        # Test 4: Invalid milestone structure
        self.log("Testing invalid milestone structure...")
        invalid_milestones = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,
                    "wicket": 30,
                    "catch": 15,
                    "stumping": 20,
                    "runOut": 25
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": "invalid",  # Should be boolean
                        "threshold": 50,
                        "points": 15
                    }
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", invalid_milestones, expected_status=400)
        detail = result.get("detail", "")
        if not detail or "must be boolean" not in detail:
            self.log(f"Invalid milestone structure validation failed. Expected error with 'must be boolean', got: {detail}", "ERROR")
            return False
        
        self.log("✅ Invalid milestone structure correctly rejected")
        
        self.log("✅ Scoring overrides endpoint validation working correctly")
        return True
    
    def test_non_cricket_league_rejection(self) -> bool:
        """Test that scoring overrides are rejected for non-cricket leagues"""
        self.log("=== Testing Non-Cricket League Rejection ===")
        
        if "user_id" not in self.test_data:
            self.log("No user available for testing", "ERROR")
            return False
        
        # Create a football league
        football_league_data = {
            "name": "Test Football League",
            "commissionerId": self.test_data["user_id"],
            "budget": 50000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "football"  # Football league
        }
        
        result = self.test_api_endpoint("POST", "/leagues", football_league_data)
        if "error" in result:
            self.log("Football league creation failed", "ERROR")
            return False
        
        football_league_id = result.get("id")
        
        # Try to set scoring overrides on football league
        scoring_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,
                    "wicket": 30,
                    "catch": 15,
                    "stumping": 20,
                    "runOut": 25
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{football_league_id}/scoring-overrides", scoring_overrides, expected_status=400)
        detail = result.get("detail", "")
        if not detail or "only supported for cricket leagues" not in detail:
            self.log(f"Non-cricket league rejection failed. Expected error with 'only supported for cricket leagues', got: {detail}", "ERROR")
            return False
        
        # Clean up football league
        self.test_api_endpoint("DELETE", f"/leagues/{football_league_id}")
        
        self.log("✅ Non-cricket league correctly rejected")
        return True
    
    def test_custom_scoring_application(self) -> bool:
        """Test that custom scoring rules are applied correctly in scoring ingest"""
        self.log("=== Testing Custom Scoring Application ===")
        
        if "user_id" not in self.test_data:
            self.log("No user available for testing", "ERROR")
            return False
        
        # Create a fresh league for this test to avoid interference
        league_data = {
            "name": "Custom Scoring Test League",
            "commissionerId": self.test_data["user_id"],
            "budget": 50000000.0,
            "minManagers": 2,
            "maxManagers": 4,
            "clubSlots": 3,
            "sportKey": "cricket"
        }
        
        result = self.test_api_endpoint("POST", "/leagues", league_data)
        if "error" in result:
            self.log("Failed to create custom scoring test league", "ERROR")
            return False
        
        league_id = result.get("id")
        
        # Join the league
        join_data = {
            "userId": self.test_data["user_id"],
            "inviteToken": result.get("inviteToken")
        }
        
        join_result = self.test_api_endpoint("POST", f"/leagues/{league_id}/join", join_data)
        if "error" in join_result:
            self.log("Failed to join custom scoring test league", "ERROR")
            return False
        
        # Set custom scoring overrides
        custom_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,      # 2 points per run (default is 1)
                    "wicket": 30,  # 30 points per wicket (default is 25)
                    "catch": 15,   # 15 points per catch (default is 10)
                    "stumping": 20,
                    "runOut": 25
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": True,
                        "points": 15   # 15 points for half-century (custom)
                    },
                    "century": {
                        "enabled": False,  # Disabled
                        "points": 50
                    },
                    "fiveWicketHaul": {
                        "enabled": True,
                        "points": 40
                    }
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", custom_overrides)
        if "error" in result:
            self.log("Failed to set custom scoring overrides", "ERROR")
            return False
        
        self.log("Custom scoring overrides set successfully")
        
        # Verify the overrides were saved correctly
        league_check = self.test_api_endpoint("GET", f"/leagues/{league_id}")
        saved_overrides = league_check.get("scoringOverrides")
        if not saved_overrides:
            self.log(f"Scoring overrides were not saved properly for league {league_id}", "ERROR")
            return False
        
        # Check that milestones have threshold fields
        milestones = saved_overrides.get("milestones", {})
        for milestone_name, milestone_data in milestones.items():
            if "threshold" not in milestone_data:
                self.log(f"Milestone {milestone_name} missing threshold field. Data: {milestone_data}", "ERROR")
                return False
        
        self.log(f"Scoring overrides verified successfully for league {league_id}")
        
        # Create test CSV data with custom scoring scenario
        csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match1,player1,25,1,1,0,0
match1,player2,75,0,2,1,0
match1,player3,100,2,0,0,1"""
        
        # Upload CSV for scoring ingest
        files = {
            'file': ('test_cricket_data.csv', csv_data, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log(f"Scoring ingest failed: {result.get('text')}", "ERROR")
            return False
        
        self.log("Scoring data ingested successfully")
        self.log(f"Ingest details: processedRows={result.get('processedRows')}, updatedRows={result.get('updatedRows')}, leaderboardUpdates={result.get('leaderboardUpdates')}")
        
        # Get leaderboard to verify custom scoring
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        if not leaderboard:
            # Try to get the ingest response to see what happened
            self.log(f"No leaderboard data returned. Full response: {leaderboard_result}", "ERROR")
            self.log(f"Ingest result was: {result}", "ERROR")
            return False
        
        # Verify custom scoring calculations
        # Player 1: 25 runs * 2 = 50, 1 wicket * 30 = 30, 1 catch * 15 = 15, no milestones = 95 total
        # Player 2: 75 runs * 2 = 150, 2 catches * 15 = 30, 1 stumping * 20 = 20, half-century bonus = 15, total = 215
        # Player 3: 100 runs * 2 = 200, 2 wickets * 30 = 60, 1 runOut * 25 = 25, NO century bonus (disabled), half-century bonus = 15, total = 300
        
        expected_scores = {
            "player1": 95,   # 25*2 + 1*30 + 1*15 = 50 + 30 + 15 = 95
            "player2": 215,  # 75*2 + 2*15 + 1*20 + 15(half-century) = 150 + 30 + 20 + 15 = 215
            "player3": 300   # 100*2 + 2*30 + 1*25 + 15(half-century, no century) = 200 + 60 + 25 + 15 = 300
        }
        
        for entry in leaderboard:
            player_id = entry.get("playerExternalId")
            total_points = entry.get("totalPoints")
            
            if player_id in expected_scores:
                expected = expected_scores[player_id]
                if total_points != expected:
                    self.log(f"Custom scoring failed for {player_id}: expected {expected}, got {total_points}", "ERROR")
                    return False
                else:
                    self.log(f"✅ Custom scoring correct for {player_id}: {total_points} points")
        
        # Verify that century milestone was disabled (player3 with 100 runs should not get century bonus)
        player3_entry = next((e for e in leaderboard if e.get("playerExternalId") == "player3"), None)
        if not player3_entry:
            self.log("Player3 not found in leaderboard", "ERROR")
            return False
        
        # Player3 should have 300 points (not 350 with century bonus)
        if player3_entry.get("totalPoints") != 300:
            self.log(f"Century milestone not properly disabled: player3 has {player3_entry.get('totalPoints')} points (should be 300)", "ERROR")
            return False
        
        self.log("✅ Disabled century milestone working correctly")
        
        self.log("✅ Custom scoring application working correctly")
        
        # Clean up the test league
        self.test_api_endpoint("DELETE", f"/leagues/{league_id}")
        
        return True
    
    def test_schema_precedence(self) -> bool:
        """Test that league scoring overrides take precedence over sport defaults"""
        self.log("=== Testing Schema Precedence ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for testing", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # First, test with sport default (no overrides)
        # Clear any existing overrides
        clear_overrides = {"scoringOverrides": None}
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", clear_overrides)
        if "error" in result:
            self.log("Failed to clear scoring overrides", "ERROR")
            return False
        
        # Upload test data with sport defaults
        csv_data_default = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match2,player4,50,1,1,0,0"""
        
        files = {
            'file': ('test_default_scoring.csv', csv_data_default, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log(f"Default scoring ingest failed: {result.get('text')}", "ERROR")
            return False
        
        # Get leaderboard with default scoring
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get default leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        player4_default = next((e for e in leaderboard if e.get("playerExternalId") == "player4"), None)
        
        if not player4_default:
            self.log("Player4 not found in default leaderboard", "ERROR")
            return False
        
        default_points = player4_default.get("totalPoints")
        self.log(f"Player4 with sport defaults: {default_points} points")
        
        # Now set custom overrides and test the same data
        custom_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 3,      # 3 points per run (higher than default)
                    "wicket": 40,  # 40 points per wicket (higher than default)
                    "catch": 20,   # 20 points per catch (higher than default)
                    "stumping": 25,
                    "runOut": 30
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": True,
                        "threshold": 50,
                        "points": 25   # 25 points for half-century (higher than default)
                    },
                    "century": {
                        "enabled": True,
                        "threshold": 100,
                        "points": 75
                    },
                    "fiveWicketHaul": {
                        "enabled": True,
                        "threshold": 5,
                        "points": 50
                    }
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", custom_overrides)
        if "error" in result:
            self.log("Failed to set custom overrides for precedence test", "ERROR")
            return False
        
        # Upload the same data again (should use custom scoring now)
        csv_data_custom = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match3,player5,50,1,1,0,0"""
        
        files = {
            'file': ('test_custom_scoring.csv', csv_data_custom, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log(f"Custom scoring ingest failed: {result.get('text')}", "ERROR")
            return False
        
        # Get updated leaderboard
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get custom leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        player5_custom = next((e for e in leaderboard if e.get("playerExternalId") == "player5"), None)
        
        if not player5_custom:
            self.log("Player5 not found in custom leaderboard", "ERROR")
            return False
        
        custom_points = player5_custom.get("totalPoints")
        self.log(f"Player5 with custom overrides: {custom_points} points")
        
        # Custom scoring should give higher points
        # Player5: 50 runs * 3 = 150, 1 wicket * 40 = 40, 1 catch * 20 = 20, half-century bonus = 25, total = 235
        expected_custom_points = 235
        
        if custom_points != expected_custom_points:
            self.log(f"Custom scoring calculation incorrect: expected {expected_custom_points}, got {custom_points}", "ERROR")
            return False
        
        if custom_points <= default_points:
            self.log(f"Schema precedence failed: custom points ({custom_points}) should be higher than default points ({default_points})", "ERROR")
            return False
        
        self.log("✅ Schema precedence working correctly (league overrides > sport defaults)")
        return True
    
    def test_disabled_milestone_scenario(self) -> bool:
        """Test specific scenario: 75 runs with disabled half-century should give 75 pts (no bonus)"""
        self.log("=== Testing Disabled Milestone Scenario ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for testing", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # Set scoring with disabled half-century milestone
        disabled_milestone_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 1,      # 1 point per run for easy calculation
                    "wicket": 25,
                    "catch": 10,
                    "stumping": 15,
                    "runOut": 20
                },
                "milestones": {
                    "halfCentury": {
                        "enabled": False,  # Disabled
                        "threshold": 50,
                        "points": 50
                    },
                    "century": {
                        "enabled": False,  # Also disabled
                        "threshold": 100,
                        "points": 100
                    },
                    "fiveWicketHaul": {
                        "enabled": True,
                        "threshold": 5,
                        "points": 40
                    }
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", disabled_milestone_overrides)
        if "error" in result:
            self.log("Failed to set disabled milestone overrides", "ERROR")
            return False
        
        # Test data: player with 75 runs (should qualify for half-century but milestone is disabled)
        csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match4,player6,75,0,0,0,0"""
        
        files = {
            'file': ('test_disabled_milestone.csv', csv_data, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log(f"Disabled milestone ingest failed: {result.get('text')}", "ERROR")
            return False
        
        # Get leaderboard
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get disabled milestone leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        player6_entry = next((e for e in leaderboard if e.get("playerExternalId") == "player6"), None)
        
        if not player6_entry:
            self.log("Player6 not found in leaderboard", "ERROR")
            return False
        
        points = player6_entry.get("totalPoints")
        
        # Should be exactly 75 points (75 runs * 1 point each, no milestone bonus)
        if points != 75:
            self.log(f"Disabled milestone test failed: expected 75 points, got {points}", "ERROR")
            return False
        
        self.log("✅ Disabled milestone scenario working correctly (75 runs = 75 pts, no bonus)")
        return True
    
    def test_integration_with_ingest_system(self) -> bool:
        """Test that custom rules apply immediately on next upload"""
        self.log("=== Testing Integration with Ingest System ===")
        
        if "league_id" not in self.test_data:
            self.log("No league available for testing", "ERROR")
            return False
        
        league_id = self.test_data["league_id"]
        
        # Upload data with one set of rules
        initial_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 1,
                    "wicket": 20,
                    "catch": 10,
                    "stumping": 15,
                    "runOut": 20
                },
                "milestones": {
                    "halfCentury": {"enabled": True, "threshold": 50, "points": 10},
                    "century": {"enabled": True, "threshold": 100, "points": 20},
                    "fiveWicketHaul": {"enabled": True, "threshold": 5, "points": 30}
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", initial_overrides)
        if "error" in result:
            self.log("Failed to set initial overrides", "ERROR")
            return False
        
        # Upload first batch of data
        csv_data1 = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match5,player7,60,1,0,0,0"""
        
        files = {
            'file': ('test_integration1.csv', csv_data1, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log("First integration ingest failed", "ERROR")
            return False
        
        # Get initial points
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get initial integration leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        player7_initial = next((e for e in leaderboard if e.get("playerExternalId") == "player7"), None)
        
        if not player7_initial:
            self.log("Player7 not found in initial leaderboard", "ERROR")
            return False
        
        initial_points = player7_initial.get("totalPoints")
        # Should be: 60 runs * 1 = 60, 1 wicket * 20 = 20, half-century bonus = 10, total = 90
        expected_initial = 90
        
        if initial_points != expected_initial:
            self.log(f"Initial integration points incorrect: expected {expected_initial}, got {initial_points}", "ERROR")
            return False
        
        self.log(f"Initial points with first rules: {initial_points}")
        
        # Change the scoring rules
        updated_overrides = {
            "scoringOverrides": {
                "rules": {
                    "run": 2,      # Doubled
                    "wicket": 40,  # Doubled
                    "catch": 20,   # Doubled
                    "stumping": 30,
                    "runOut": 40
                },
                "milestones": {
                    "halfCentury": {"enabled": True, "threshold": 50, "points": 20},  # Doubled
                    "century": {"enabled": True, "threshold": 100, "points": 40},
                    "fiveWicketHaul": {"enabled": True, "threshold": 5, "points": 60}
                }
            }
        }
        
        result = self.test_api_endpoint("PUT", f"/leagues/{league_id}/scoring-overrides", updated_overrides)
        if "error" in result:
            self.log("Failed to update overrides", "ERROR")
            return False
        
        self.log("Updated scoring rules")
        
        # Upload new data with same performance (should use new rules)
        csv_data2 = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match6,player8,60,1,0,0,0"""
        
        files = {
            'file': ('test_integration2.csv', csv_data2, 'text/csv')
        }
        
        result = self.test_api_endpoint("POST", f"/scoring/{league_id}/ingest", files=files)
        if "error" in result:
            self.log("Second integration ingest failed", "ERROR")
            return False
        
        # Get updated leaderboard
        leaderboard_result = self.test_api_endpoint("GET", f"/scoring/{league_id}/leaderboard")
        if "error" in leaderboard_result:
            self.log("Failed to get updated integration leaderboard", "ERROR")
            return False
        
        leaderboard = leaderboard_result.get("leaderboard", [])
        player8_updated = next((e for e in leaderboard if e.get("playerExternalId") == "player8"), None)
        
        if not player8_updated:
            self.log("Player8 not found in updated leaderboard", "ERROR")
            return False
        
        updated_points = player8_updated.get("totalPoints")
        # Should be: 60 runs * 2 = 120, 1 wicket * 40 = 40, half-century bonus = 20, total = 180
        expected_updated = 180
        
        if updated_points != expected_updated:
            self.log(f"Updated integration points incorrect: expected {expected_updated}, got {updated_points}", "ERROR")
            return False
        
        self.log(f"Updated points with new rules: {updated_points}")
        
        # Verify that new rules applied immediately
        if updated_points <= initial_points:
            self.log(f"Integration failed: updated points ({updated_points}) should be higher than initial ({initial_points})", "ERROR")
            return False
        
        self.log("✅ Integration with ingest system working correctly (custom rules apply immediately)")
        return True
    
    def cleanup(self):
        """Clean up test data"""
        self.log("=== Cleaning Up ===")
        
        if "league_id" in self.test_data:
            result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_data['league_id']}")
            if "error" not in result:
                self.log("Test league deleted")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all cricket scoring configuration tests"""
        self.log("🏏 Starting Cricket Scoring Configuration Tests")
        
        results = {}
        
        # Setup test data
        if not self.setup_test_data():
            self.log("❌ Test data setup failed", "ERROR")
            return {"setup": False}
        
        results["setup"] = True
        
        # Run all test suites
        test_suites = [
            ("scoring_overrides_endpoint_validation", self.test_scoring_overrides_endpoint_validation),
            ("non_cricket_league_rejection", self.test_non_cricket_league_rejection),
            ("custom_scoring_application", self.test_custom_scoring_application),
            ("schema_precedence", self.test_schema_precedence),
            ("disabled_milestone_scenario", self.test_disabled_milestone_scenario),
            ("integration_with_ingest_system", self.test_integration_with_ingest_system),
        ]
        
        for test_name, test_func in test_suites:
            try:
                results[test_name] = test_func()
                if not results[test_name]:
                    self.log(f"❌ {test_name} failed", "ERROR")
                else:
                    self.log(f"✅ {test_name} passed")
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {str(e)}", "ERROR")
                results[test_name] = False
        
        # Cleanup
        self.cleanup()
        
        return results

def main():
    """Main test execution"""
    tester = CricketScoringConfigTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("CRICKET SCORING CONFIGURATION TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:40} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cricket scoring configuration tests passed!")
        return True
    else:
        print("⚠️  Some cricket scoring configuration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)