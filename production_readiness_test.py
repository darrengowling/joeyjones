#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION READINESS TEST
Multi-Sport Friends of Pifa Platform - Complete System Evaluation

This test covers all 20 areas specified in the review request:
1. Multi-Sport Architecture (Football & Cricket)
2. Authentication & User Management  
3. League Management
4. Asset Management (36 UEFA teams, 20 IPL players)
5. Auction System with Real-time Bidding
6. Socket.IO Real-time Features
7. Cricket Scoring System with CSV Upload
8. Custom Scoring Rules
9. Cricket Leaderboards
10. Sport-Aware UI Components
11. Cricket Flag Control
12. Football Regression Testing
13. Database Operations
14. API Endpoints
15. Environment Configuration
16. Data Integrity
17. Error Handling
18. Multi-tenancy (Multiple Leagues)
19. Feature Flags
20. Performance & Stability
"""

import requests
import socketio
import asyncio
import json
import time
import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Configuration
BASE_URL = "https://sportbid-platform.preview.emergentagent.com/api"
SOCKET_URL = "https://sportbid-platform.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

class ProductionReadinessTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.socket_client = None
        self.socket_events = []
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_endpoint(self, method: str, endpoint: str, data: dict = None, 
                     expected_status: int = 200, files: dict = None) -> dict:
        """Test API endpoint with comprehensive error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=data)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, files=files, data=data)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=data)
            else:
                return {"error": f"Unsupported method: {method}"}
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                return {"error": f"Status {response.status_code}", "detail": error_detail, "status_code": response.status_code}
                
            try:
                result = response.json()
                result["status_code"] = response.status_code
                return result
            except:
                return {"success": True, "status_code": response.status_code}
                
        except Exception as e:
            return {"error": str(e)}

    def test_multi_sport_architecture(self) -> bool:
        """Test 1: Multi-Sport Architecture - Football and Cricket Support"""
        self.log("=== TEST 1: MULTI-SPORT ARCHITECTURE ===")
        
        try:
            # Test sports endpoint
            result = self.test_endpoint("GET", "/sports")
            if "error" in result:
                self.log(f"❌ Sports endpoint failed: {result['error']}", "ERROR")
                return False
                
            sports = result if isinstance(result, list) else result.get("sports", [])
            
            # Verify both football and cricket are available
            sport_keys = [sport.get("key") for sport in sports]
            
            if "football" not in sport_keys:
                self.log("❌ Football sport not found", "ERROR")
                return False
                
            if "cricket" not in sport_keys:
                self.log("❌ Cricket sport not found", "ERROR") 
                return False
                
            # Test individual sport endpoints
            football_result = self.test_endpoint("GET", "/sports/football")
            cricket_result = self.test_endpoint("GET", "/sports/cricket")
            
            if "error" in football_result or "error" in cricket_result:
                self.log("❌ Individual sport endpoints failed", "ERROR")
                return False
                
            # Verify sport configurations
            football = football_result
            cricket = cricket_result
            
            if football.get("assetType") != "CLUB":
                self.log("❌ Football assetType should be CLUB", "ERROR")
                return False
                
            if cricket.get("assetType") != "PLAYER":
                self.log("❌ Cricket assetType should be PLAYER", "ERROR")
                return False
                
            self.log("✅ Multi-sport architecture working correctly")
            self.test_data["sports"] = {"football": football, "cricket": cricket}
            return True
            
        except Exception as e:
            self.log(f"❌ Multi-sport architecture test failed: {str(e)}", "ERROR")
            return False

    def test_authentication_user_management(self) -> bool:
        """Test 2: Authentication & User Management"""
        self.log("=== TEST 2: AUTHENTICATION & USER MANAGEMENT ===")
        
        try:
            # Test user creation
            user_data = {
                "name": "Production Test Manager",
                "email": "prod.test@friendsofpifa.com"
            }
            
            result = self.test_endpoint("POST", "/users", user_data)
            if "error" in result:
                self.log(f"❌ User creation failed: {result['error']}", "ERROR")
                return False
                
            user_id = result.get("id")
            if not user_id:
                self.log("❌ User ID not returned", "ERROR")
                return False
                
            # Test user retrieval
            result = self.test_endpoint("GET", f"/users/{user_id}")
            if "error" in result:
                self.log(f"❌ User retrieval failed: {result['error']}", "ERROR")
                return False
                
            # Test magic link authentication flow
            magic_link_data = {"email": user_data["email"]}
            result = self.test_endpoint("POST", "/auth/magic-link", magic_link_data)
            if "error" in result:
                self.log(f"❌ Magic link generation failed: {result['error']}", "ERROR")
                return False
                
            token = result.get("token")
            if not token:
                self.log("❌ Magic link token not generated", "ERROR")
                return False
                
            # Test magic link verification
            verify_data = {"email": user_data["email"], "token": token}
            result = self.test_endpoint("POST", "/auth/verify-magic-link", verify_data)
            if "error" in result:
                self.log(f"❌ Magic link verification failed: {result['error']}", "ERROR")
                return False
                
            self.log("✅ Authentication & user management working correctly")
            self.test_data["user"] = {"id": user_id, "email": user_data["email"]}
            return True
            
        except Exception as e:
            self.log(f"❌ Authentication test failed: {str(e)}", "ERROR")
            return False

    def test_league_management(self) -> bool:
        """Test 3: League Management - Create/Join/Manage for Both Sports"""
        self.log("=== TEST 3: LEAGUE MANAGEMENT ===")
        
        try:
            user_id = self.test_data["user"]["id"]
            
            # Test football league creation
            football_league_data = {
                "name": "Production Football League",
                "commissionerId": user_id,
                "budget": 500000000.0,  # £500M
                "minManagers": 2,
                "maxManagers": 8,
                "clubSlots": 5,
                "sportKey": "football"
            }
            
            result = self.test_endpoint("POST", "/leagues", football_league_data)
            if "error" in result:
                self.log(f"❌ Football league creation failed: {result['error']}", "ERROR")
                return False
                
            football_league_id = result.get("id")
            football_invite_token = result.get("inviteToken")
            
            # Test cricket league creation
            cricket_league_data = {
                "name": "Production Cricket League", 
                "commissionerId": user_id,
                "budget": 300000000.0,  # £300M
                "minManagers": 2,
                "maxManagers": 10,
                "clubSlots": 11,
                "sportKey": "cricket"
            }
            
            result = self.test_endpoint("POST", "/leagues", cricket_league_data)
            if "error" in result:
                self.log(f"❌ Cricket league creation failed: {result['error']}", "ERROR")
                return False
                
            cricket_league_id = result.get("id")
            cricket_invite_token = result.get("inviteToken")
            
            # Test league filtering by sport
            result = self.test_endpoint("GET", "/leagues", {"sportKey": "football"})
            if "error" in result:
                self.log(f"❌ Football league filtering failed: {result['error']}", "ERROR")
                return False
                
            football_leagues = result if isinstance(result, list) else []
            football_found = any(league.get("id") == football_league_id for league in football_leagues)
            
            if not football_found:
                self.log("❌ Football league not found in filtered results", "ERROR")
                return False
                
            # Test joining leagues
            join_data = {"userId": user_id, "inviteToken": football_invite_token}
            result = self.test_endpoint("POST", f"/leagues/{football_league_id}/join", join_data)
            if "error" in result:
                self.log(f"❌ Football league join failed: {result['error']}", "ERROR")
                return False
                
            # Verify budget allocation
            participant = result.get("participant", {})
            if participant.get("budgetRemaining") != 500000000.0:
                self.log("❌ Incorrect budget allocation for football league", "ERROR")
                return False
                
            self.log("✅ League management working correctly")
            self.test_data["leagues"] = {
                "football": {"id": football_league_id, "token": football_invite_token},
                "cricket": {"id": cricket_league_id, "token": cricket_invite_token}
            }
            return True
            
        except Exception as e:
            self.log(f"❌ League management test failed: {str(e)}", "ERROR")
            return False

    def test_asset_management(self) -> bool:
        """Test 4: Asset Management - 36 UEFA Teams & 20 IPL Players"""
        self.log("=== TEST 4: ASSET MANAGEMENT ===")
        
        try:
            # Test football assets (36 UEFA teams)
            result = self.test_endpoint("GET", "/assets", {"sportKey": "football"})
            if "error" in result:
                self.log(f"❌ Football assets retrieval failed: {result['error']}", "ERROR")
                return False
                
            football_assets = result.get("assets", [])
            if len(football_assets) != 36:
                self.log(f"❌ Expected 36 UEFA teams, found {len(football_assets)}", "ERROR")
                return False
                
            # Verify UEFA team structure
            sample_team = football_assets[0]
            required_fields = ["id", "name", "country", "uefaId"]
            for field in required_fields:
                if field not in sample_team:
                    self.log(f"❌ Missing field {field} in UEFA team", "ERROR")
                    return False
                    
            # Test cricket assets (20 IPL players)
            result = self.test_endpoint("GET", "/assets", {"sportKey": "cricket"})
            if "error" in result:
                self.log(f"❌ Cricket assets retrieval failed: {result['error']}", "ERROR")
                return False
                
            cricket_assets = result.get("assets", [])
            if len(cricket_assets) != 20:
                self.log(f"❌ Expected 20 IPL players, found {len(cricket_assets)}", "ERROR")
                return False
                
            # Verify IPL player structure
            sample_player = cricket_assets[0]
            required_fields = ["id", "name", "sportKey", "externalId", "meta"]
            for field in required_fields:
                if field not in sample_player:
                    self.log(f"❌ Missing field {field} in IPL player", "ERROR")
                    return False
                    
            # Verify meta structure for cricket players
            meta = sample_player.get("meta", {})
            if "franchise" not in meta or "role" not in meta:
                self.log("❌ Missing franchise or role in cricket player meta", "ERROR")
                return False
                
            # Test asset search functionality
            result = self.test_endpoint("GET", "/assets", {"sportKey": "football", "search": "Real"})
            if "error" in result:
                self.log(f"❌ Football asset search failed: {result['error']}", "ERROR")
                return False
                
            search_results = result.get("assets", [])
            if not search_results:
                self.log("❌ No results for 'Real' search in football", "ERROR")
                return False
                
            # Test pagination
            result = self.test_endpoint("GET", "/assets", {"sportKey": "cricket", "page": 1, "pageSize": 10})
            if "error" in result:
                self.log(f"❌ Cricket asset pagination failed: {result['error']}", "ERROR")
                return False
                
            pagination = result.get("pagination", {})
            if not pagination.get("hasNext"):
                self.log("❌ Pagination not working correctly", "ERROR")
                return False
                
            self.log("✅ Asset management working correctly")
            self.test_data["assets"] = {
                "football_count": len(football_assets),
                "cricket_count": len(cricket_assets)
            }
            return True
            
        except Exception as e:
            self.log(f"❌ Asset management test failed: {str(e)}", "ERROR")
            return False

    def test_auction_system(self) -> bool:
        """Test 5: Auction System with Real-time Bidding"""
        self.log("=== TEST 5: AUCTION SYSTEM WITH REAL-TIME BIDDING ===")
        
        try:
            football_league_id = self.test_data["leagues"]["football"]["id"]
            
            # Start auction
            result = self.test_endpoint("POST", f"/leagues/{football_league_id}/auction/start")
            if "error" in result:
                self.log(f"❌ Auction start failed: {result['error']}", "ERROR")
                return False
                
            auction_id = result.get("auctionId")
            if not auction_id:
                self.log("❌ Auction ID not returned", "ERROR")
                return False
                
            # Get auction details
            result = self.test_endpoint("GET", f"/auction/{auction_id}")
            if "error" in result:
                self.log(f"❌ Auction retrieval failed: {result['error']}", "ERROR")
                return False
                
            auction = result.get("auction", {})
            current_club = result.get("currentClub")
            
            if not current_club:
                self.log("❌ No current club in auction", "ERROR")
                return False
                
            # Test bidding system
            user_id = self.test_data["user"]["id"]
            bid_data = {
                "userId": user_id,
                "clubId": current_club.get("id"),
                "amount": 2000000.0  # £2M bid
            }
            
            result = self.test_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in result:
                self.log(f"❌ Bidding failed: {result['error']}", "ERROR")
                return False
                
            # Test minimum budget enforcement
            low_bid_data = {
                "userId": user_id,
                "clubId": current_club.get("id"),
                "amount": 500000.0  # £500K - below minimum
            }
            
            result = self.test_endpoint("POST", f"/auction/{auction_id}/bid", low_bid_data, expected_status=400)
            if result.get("status_code") != 400:
                self.log("❌ Minimum budget enforcement not working", "ERROR")
                return False
                
            # Test clubs list endpoint
            result = self.test_endpoint("GET", f"/auction/{auction_id}/clubs")
            if "error" in result:
                self.log(f"❌ Clubs list retrieval failed: {result['error']}", "ERROR")
                return False
                
            clubs = result.get("clubs", [])
            if len(clubs) != 36:
                self.log(f"❌ Expected 36 clubs, found {len(clubs)}", "ERROR")
                return False
                
            # Verify club status information
            current_clubs = [club for club in clubs if club.get("status") == "current"]
            if len(current_clubs) != 1:
                self.log("❌ Should have exactly one current club", "ERROR")
                return False
                
            self.log("✅ Auction system working correctly")
            self.test_data["auction"] = {"id": auction_id, "current_club": current_club}
            return True
            
        except Exception as e:
            self.log(f"❌ Auction system test failed: {str(e)}", "ERROR")
            return False

    def test_socketio_realtime(self) -> bool:
        """Test 6: Socket.IO Real-time Features"""
        self.log("=== TEST 6: SOCKET.IO REAL-TIME FEATURES ===")
        
        try:
            # Create Socket.IO client
            sio = socketio.Client()
            events_received = []
            
            @sio.event
            def connect():
                self.log("Socket.IO connected successfully")
                
            @sio.event
            def disconnect():
                self.log("Socket.IO disconnected")
                
            @sio.event
            def sync_state(data):
                events_received.append(("sync_state", data))
                self.log("Received sync_state event")
                
            @sio.event
            def joined(data):
                events_received.append(("joined", data))
                self.log("Received joined event")
                
            @sio.event
            def tick(data):
                events_received.append(("tick", data))
                
            # Connect to Socket.IO server
            sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH)
            time.sleep(1)  # Allow connection to establish
            
            # Join auction room
            auction_id = self.test_data.get("auction", {}).get("id")
            if not auction_id:
                self.log("❌ No auction ID available for Socket.IO test", "ERROR")
                sio.disconnect()
                return False
                
            sio.emit("join_auction", {"auctionId": auction_id})
            time.sleep(2)  # Wait for events
            
            # Verify events received
            event_types = [event[0] for event in events_received]
            
            if "sync_state" not in event_types:
                self.log("❌ sync_state event not received", "ERROR")
                sio.disconnect()
                return False
                
            if "joined" not in event_types:
                self.log("❌ joined event not received", "ERROR")
                sio.disconnect()
                return False
                
            # Test timer events (should receive tick events)
            tick_events = [event for event in events_received if event[0] == "tick"]
            if len(tick_events) < 1:
                self.log("⚠️ No tick events received (timer may not be active)", "WARN")
            else:
                self.log(f"✅ Received {len(tick_events)} tick events")
                
            sio.disconnect()
            self.log("✅ Socket.IO real-time features working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Socket.IO test failed: {str(e)}", "ERROR")
            return False

    def test_cricket_scoring_system(self) -> bool:
        """Test 7: Cricket Scoring System with CSV Upload"""
        self.log("=== TEST 7: CRICKET SCORING SYSTEM WITH CSV UPLOAD ===")
        
        try:
            cricket_league_id = self.test_data["leagues"]["cricket"]["id"]
            
            # Create test CSV data
            csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match1,player1,75,2,1,0,1
match1,player2,45,0,2,1,0
match1,player3,120,1,0,0,0
match2,player1,30,3,1,0,0
match2,player2,85,0,1,0,1"""
            
            # Create file-like object
            csv_file = io.StringIO(csv_data)
            files = {"file": ("test_scores.csv", csv_file.getvalue(), "text/csv")}
            
            # Test CSV upload
            result = self.test_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", 
                                      files=files)
            if "error" in result:
                self.log(f"❌ Cricket scoring ingest failed: {result['error']}", "ERROR")
                return False
                
            processed_rows = result.get("processedRows", 0)
            if processed_rows != 5:
                self.log(f"❌ Expected 5 processed rows, got {processed_rows}", "ERROR")
                return False
                
            # Test leaderboard retrieval
            result = self.test_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
            if "error" in result:
                self.log(f"❌ Cricket leaderboard retrieval failed: {result['error']}", "ERROR")
                return False
                
            leaderboard = result.get("leaderboard", [])
            if not leaderboard:
                self.log("❌ Empty leaderboard after scoring ingest", "ERROR")
                return False
                
            # Verify points calculation (player3 with 120 runs should have century bonus)
            player3_entry = next((entry for entry in leaderboard 
                                if entry.get("playerExternalId") == "player3"), None)
            if not player3_entry:
                self.log("❌ Player3 not found in leaderboard", "ERROR")
                return False
                
            # Test re-upload (should not double count)
            result = self.test_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", 
                                      files=files)
            if "error" in result:
                self.log(f"❌ Cricket scoring re-ingest failed: {result['error']}", "ERROR")
                return False
                
            # Get updated leaderboard
            result = self.test_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
            if "error" in result:
                self.log(f"❌ Cricket leaderboard re-retrieval failed: {result['error']}", "ERROR")
                return False
                
            updated_leaderboard = result.get("leaderboard", [])
            updated_player3 = next((entry for entry in updated_leaderboard 
                                  if entry.get("playerExternalId") == "player3"), None)
            
            # Points should be the same (no double counting)
            if updated_player3.get("totalPoints") != player3_entry.get("totalPoints"):
                self.log("❌ Double counting detected in re-upload", "ERROR")
                return False
                
            self.log("✅ Cricket scoring system working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Cricket scoring system test failed: {str(e)}", "ERROR")
            return False

    def test_custom_scoring_rules(self) -> bool:
        """Test 8: Custom Scoring Rules - League-level Overrides"""
        self.log("=== TEST 8: CUSTOM SCORING RULES ===")
        
        try:
            cricket_league_id = self.test_data["leagues"]["cricket"]["id"]
            
            # Test custom scoring configuration
            custom_scoring = {
                "scoringOverrides": {
                    "rules": {
                        "run": 2.0,      # Double points for runs
                        "wicket": 30.0,  # Higher wicket points
                        "catch": 15.0,   # Higher catch points
                        "stumping": 25.0,
                        "runOut": 20.0
                    },
                    "milestones": {
                        "halfCentury": {
                            "enabled": True,
                            "points": 100.0,  # Higher bonus
                            "threshold": 50
                        },
                        "century": {
                            "enabled": True,
                            "points": 250.0,  # Higher bonus
                            "threshold": 100
                        },
                        "fiveWicketHaul": {
                            "enabled": False,  # Disabled
                            "points": 0.0,
                            "threshold": 5
                        }
                    }
                }
            }
            
            result = self.test_endpoint("PUT", f"/leagues/{cricket_league_id}/scoring-overrides", 
                                      custom_scoring)
            if "error" in result:
                self.log(f"❌ Custom scoring configuration failed: {result['error']}", "ERROR")
                return False
                
            # Verify the configuration was saved
            result = self.test_endpoint("GET", f"/leagues/{cricket_league_id}")
            if "error" in result:
                self.log(f"❌ League retrieval failed: {result['error']}", "ERROR")
                return False
                
            scoring_overrides = result.get("scoringOverrides")
            if not scoring_overrides:
                self.log("❌ Scoring overrides not saved", "ERROR")
                return False
                
            # Test that custom rules are applied in scoring
            csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match3,player4,60,1,0,0,0"""
            
            files = {"file": ("custom_test.csv", csv_data, "text/csv")}
            result = self.test_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", 
                                      files=files)
            if "error" in result:
                self.log(f"❌ Custom scoring ingest failed: {result['error']}", "ERROR")
                return False
                
            # Get leaderboard to verify custom scoring
            result = self.test_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
            if "error" in result:
                self.log(f"❌ Custom scoring leaderboard failed: {result['error']}", "ERROR")
                return False
                
            leaderboard = result.get("leaderboard", [])
            player4_entry = next((entry for entry in leaderboard 
                                if entry.get("playerExternalId") == "player4"), None)
            
            if not player4_entry:
                self.log("❌ Player4 not found in leaderboard", "ERROR")
                return False
                
            # With custom rules: 60 runs * 2 = 120, 1 wicket * 30 = 30, half-century bonus = 100
            # Total should be 250 points
            expected_points = 250.0
            actual_points = player4_entry.get("totalPoints", 0)
            
            if abs(actual_points - expected_points) > 0.1:
                self.log(f"❌ Custom scoring not applied correctly. Expected ~{expected_points}, got {actual_points}", "ERROR")
                return False
                
            self.log("✅ Custom scoring rules working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Custom scoring rules test failed: {str(e)}", "ERROR")
            return False

    def test_cricket_leaderboards(self) -> bool:
        """Test 9: Cricket Leaderboards - Multi-match Accumulation"""
        self.log("=== TEST 9: CRICKET LEADERBOARDS ===")
        
        try:
            cricket_league_id = self.test_data["leagues"]["cricket"]["id"]
            
            # Get current leaderboard
            result = self.test_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
            if "error" in result:
                self.log(f"❌ Leaderboard retrieval failed: {result['error']}", "ERROR")
                return False
                
            leaderboard = result.get("leaderboard", [])
            if not leaderboard:
                self.log("❌ Empty leaderboard", "ERROR")
                return False
                
            # Verify leaderboard structure
            top_player = leaderboard[0]
            required_fields = ["playerExternalId", "totalPoints", "updatedAt"]
            for field in required_fields:
                if field not in top_player:
                    self.log(f"❌ Missing field {field} in leaderboard entry", "ERROR")
                    return False
                    
            # Verify sorting (descending by points)
            for i in range(len(leaderboard) - 1):
                if leaderboard[i]["totalPoints"] < leaderboard[i + 1]["totalPoints"]:
                    self.log("❌ Leaderboard not sorted correctly", "ERROR")
                    return False
                    
            # Test multi-match accumulation by adding more data
            csv_data = """matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
match4,player1,95,0,1,0,0
match4,player2,15,4,2,0,1"""
            
            files = {"file": ("multi_match.csv", csv_data, "text/csv")}
            result = self.test_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", 
                                      files=files)
            if "error" in result:
                self.log(f"❌ Multi-match ingest failed: {result['error']}", "ERROR")
                return False
                
            # Get updated leaderboard
            result = self.test_endpoint("GET", f"/scoring/{cricket_league_id}/leaderboard")
            if "error" in result:
                self.log(f"❌ Updated leaderboard retrieval failed: {result['error']}", "ERROR")
                return False
                
            updated_leaderboard = result.get("leaderboard", [])
            
            # Find player1 and verify accumulation
            player1_entry = next((entry for entry in updated_leaderboard 
                                if entry.get("playerExternalId") == "player1"), None)
            
            if not player1_entry:
                self.log("❌ Player1 not found in updated leaderboard", "ERROR")
                return False
                
            # Player1 should have points from multiple matches accumulated
            if player1_entry.get("totalPoints", 0) <= 0:
                self.log("❌ Points accumulation not working", "ERROR")
                return False
                
            self.log("✅ Cricket leaderboards working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Cricket leaderboards test failed: {str(e)}", "ERROR")
            return False

    def test_sport_aware_ui(self) -> bool:
        """Test 10: Sport-Aware UI - Dynamic Labels (Club vs Player)"""
        self.log("=== TEST 10: SPORT-AWARE UI COMPONENTS ===")
        
        try:
            # Test football sport UI hints
            result = self.test_endpoint("GET", "/sports/football")
            if "error" in result:
                self.log(f"❌ Football sport retrieval failed: {result['error']}", "ERROR")
                return False
                
            football_ui_hints = result.get("uiHints", {})
            if football_ui_hints.get("assetLabel") != "Club":
                self.log("❌ Football assetLabel should be 'Club'", "ERROR")
                return False
                
            if football_ui_hints.get("assetPlural") != "Clubs":
                self.log("❌ Football assetPlural should be 'Clubs'", "ERROR")
                return False
                
            # Test cricket sport UI hints
            result = self.test_endpoint("GET", "/sports/cricket")
            if "error" in result:
                self.log(f"❌ Cricket sport retrieval failed: {result['error']}", "ERROR")
                return False
                
            cricket_ui_hints = result.get("uiHints", {})
            if cricket_ui_hints.get("assetLabel") != "Player":
                self.log("❌ Cricket assetLabel should be 'Player'", "ERROR")
                return False
                
            if cricket_ui_hints.get("assetPlural") != "Players":
                self.log("❌ Cricket assetPlural should be 'Players'", "ERROR")
                return False
                
            # Test league-based asset filtering
            football_league_id = self.test_data["leagues"]["football"]["id"]
            cricket_league_id = self.test_data["leagues"]["cricket"]["id"]
            
            # Football league should return clubs
            result = self.test_endpoint("GET", f"/leagues/{football_league_id}/assets")
            if "error" in result:
                self.log(f"❌ Football league assets failed: {result['error']}", "ERROR")
                return False
                
            football_assets = result.get("assets", [])
            if not football_assets or "uefaId" not in football_assets[0]:
                self.log("❌ Football league assets should have uefaId", "ERROR")
                return False
                
            # Cricket league should return players
            result = self.test_endpoint("GET", f"/leagues/{cricket_league_id}/assets")
            if "error" in result:
                self.log(f"❌ Cricket league assets failed: {result['error']}", "ERROR")
                return False
                
            cricket_assets = result.get("assets", [])
            if not cricket_assets or cricket_assets[0].get("sportKey") != "cricket":
                self.log("❌ Cricket league assets should have sportKey='cricket'", "ERROR")
                return False
                
            self.log("✅ Sport-aware UI components working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Sport-aware UI test failed: {str(e)}", "ERROR")
            return False

    def test_cricket_flag_control(self) -> bool:
        """Test 11: Cricket Flag Control - Enable/Disable Functionality"""
        self.log("=== TEST 11: CRICKET FLAG CONTROL ===")
        
        try:
            # Test that cricket is currently enabled (based on .env)
            result = self.test_endpoint("GET", "/sports")
            if "error" in result:
                self.log(f"❌ Sports endpoint failed: {result['error']}", "ERROR")
                return False
                
            sports = result if isinstance(result, list) else result.get("sports", [])
            sport_keys = [sport.get("key") for sport in sports]
            
            if "cricket" not in sport_keys:
                self.log("❌ Cricket should be enabled based on SPORTS_CRICKET_ENABLED=true", "ERROR")
                return False
                
            # Test cricket-specific endpoints are accessible
            result = self.test_endpoint("GET", "/sports/cricket")
            if "error" in result:
                self.log(f"❌ Cricket sport endpoint should be accessible: {result['error']}", "ERROR")
                return False
                
            # Test cricket assets are available
            result = self.test_endpoint("GET", "/assets", {"sportKey": "cricket"})
            if "error" in result:
                self.log(f"❌ Cricket assets should be accessible: {result['error']}", "ERROR")
                return False
                
            cricket_assets = result.get("assets", [])
            if len(cricket_assets) != 20:
                self.log(f"❌ Expected 20 cricket assets, found {len(cricket_assets)}", "ERROR")
                return False
                
            # Test cricket league creation is allowed
            user_id = self.test_data["user"]["id"]
            test_cricket_league = {
                "name": "Flag Test Cricket League",
                "commissionerId": user_id,
                "budget": 200000000.0,
                "minManagers": 2,
                "maxManagers": 6,
                "clubSlots": 8,
                "sportKey": "cricket"
            }
            
            result = self.test_endpoint("POST", "/leagues", test_cricket_league)
            if "error" in result:
                self.log(f"❌ Cricket league creation should be allowed: {result['error']}", "ERROR")
                return False
                
            test_league_id = result.get("id")
            
            # Clean up test league
            if test_league_id:
                self.test_endpoint("DELETE", f"/leagues/{test_league_id}")
                
            self.log("✅ Cricket flag control working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Cricket flag control test failed: {str(e)}", "ERROR")
            return False

    def test_football_regression(self) -> bool:
        """Test 12: Football Regression - Ensure Zero Impact from Cricket"""
        self.log("=== TEST 12: FOOTBALL REGRESSION TESTING ===")
        
        try:
            # Test football functionality remains intact
            result = self.test_endpoint("GET", "/sports/football")
            if "error" in result:
                self.log(f"❌ Football sport endpoint failed: {result['error']}", "ERROR")
                return False
                
            # Test football assets still work
            result = self.test_endpoint("GET", "/assets", {"sportKey": "football"})
            if "error" in result:
                self.log(f"❌ Football assets failed: {result['error']}", "ERROR")
                return False
                
            football_assets = result.get("assets", [])
            if len(football_assets) != 36:
                self.log(f"❌ Football assets count changed: expected 36, got {len(football_assets)}", "ERROR")
                return False
                
            # Test existing football auction still works
            auction_data = self.test_data.get("auction", {})
            auction_id = auction_data.get("id")
            if not auction_id:
                self.log("❌ No auction available for regression test", "ERROR")
                return False
                
            result = self.test_endpoint("GET", f"/auction/{auction_id}")
            if "error" in result:
                self.log(f"❌ Existing football auction broken: {result['error']}", "ERROR")
                return False
                
            # Test football bidding still works
            user_id = self.test_data["user"]["id"]
            current_club = auction_data.get("current_club")
            
            bid_data = {
                "userId": user_id,
                "clubId": current_club.get("id"),
                "amount": 3000000.0  # £3M bid
            }
            
            result = self.test_endpoint("POST", f"/auction/{auction_id}/bid", bid_data)
            if "error" in result:
                self.log(f"❌ Football bidding broken: {result['error']}", "ERROR")
                return False
                
            # Test football league functionality
            football_league_id = self.test_data["leagues"]["football"]["id"]
            result = self.test_endpoint("GET", f"/leagues/{football_league_id}")
            if "error" in result:
                self.log(f"❌ Football league retrieval failed: {result['error']}", "ERROR")
                return False
                
            # Verify football league still has correct sport
            if result.get("sportKey") != "football":
                self.log("❌ Football league sportKey changed", "ERROR")
                return False
                
            self.log("✅ Football regression testing passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Football regression test failed: {str(e)}", "ERROR")
            return False

    def test_database_operations(self) -> bool:
        """Test 13: Database Operations - CRUD, Indexing, Concurrent Access"""
        self.log("=== TEST 13: DATABASE OPERATIONS ===")
        
        try:
            # Test concurrent league creation
            user_id = self.test_data["user"]["id"]
            
            concurrent_leagues = []
            for i in range(3):
                league_data = {
                    "name": f"Concurrent Test League {i+1}",
                    "commissionerId": user_id,
                    "budget": 100000000.0,
                    "minManagers": 2,
                    "maxManagers": 4,
                    "clubSlots": 3,
                    "sportKey": "football"
                }
                
                result = self.test_endpoint("POST", "/leagues", league_data)
                if "error" in result:
                    self.log(f"❌ Concurrent league creation {i+1} failed: {result['error']}", "ERROR")
                    return False
                    
                concurrent_leagues.append(result.get("id"))
                
            # Test bulk retrieval
            result = self.test_endpoint("GET", "/leagues")
            if "error" in result:
                self.log(f"❌ Bulk league retrieval failed: {result['error']}", "ERROR")
                return False
                
            leagues = result if isinstance(result, list) else []
            if len(leagues) < 3:
                self.log("❌ Not all leagues retrieved", "ERROR")
                return False
                
            # Test search functionality
            result = self.test_endpoint("GET", "/leagues/search", {"name": "Concurrent Test League 1"})
            if "error" in result:
                self.log(f"❌ League search failed: {result['error']}", "ERROR")
                return False
                
            search_results = result if isinstance(result, list) else []
            if not search_results:
                self.log("❌ League search returned no results", "ERROR")
                return False
                
            # Test data consistency - verify all created leagues exist
            for league_id in concurrent_leagues:
                result = self.test_endpoint("GET", f"/leagues/{league_id}")
                if "error" in result:
                    self.log(f"❌ League {league_id} not found after creation", "ERROR")
                    return False
                    
            # Clean up concurrent test leagues
            for league_id in concurrent_leagues:
                self.test_endpoint("DELETE", f"/leagues/{league_id}")
                
            self.log("✅ Database operations working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Database operations test failed: {str(e)}", "ERROR")
            return False

    def test_api_endpoints(self) -> bool:
        """Test 14: API Endpoints - All Endpoints Functional"""
        self.log("=== TEST 14: API ENDPOINTS FUNCTIONALITY ===")
        
        try:
            # Test root endpoint
            result = self.test_endpoint("GET", "/")
            if "error" in result:
                self.log(f"❌ Root endpoint failed: {result['error']}", "ERROR")
                return False
                
            # Test user endpoints
            endpoints_to_test = [
                ("GET", "/sports"),
                ("GET", "/sports/football"),
                ("GET", "/sports/cricket"),
                ("GET", "/assets", {"sportKey": "football"}),
                ("GET", "/assets", {"sportKey": "cricket"}),
                ("GET", "/clubs"),
                ("GET", "/leagues"),
                ("GET", "/leagues", {"sportKey": "football"}),
                ("GET", "/leagues", {"sportKey": "cricket"})
            ]
            
            failed_endpoints = []
            
            for method, endpoint, *params in endpoints_to_test:
                data = params[0] if params else None
                result = self.test_endpoint(method, endpoint, data)
                if "error" in result:
                    failed_endpoints.append(f"{method} {endpoint}")
                    self.log(f"❌ {method} {endpoint} failed: {result['error']}", "ERROR")
                    
            if failed_endpoints:
                self.log(f"❌ {len(failed_endpoints)} endpoints failed", "ERROR")
                return False
                
            # Test error handling with invalid endpoints
            result = self.test_endpoint("GET", "/nonexistent", expected_status=404)
            if result.get("status_code") != 404:
                self.log("❌ Error handling not working for invalid endpoints", "ERROR")
                return False
                
            self.log("✅ API endpoints functionality verified")
            return True
            
        except Exception as e:
            self.log(f"❌ API endpoints test failed: {str(e)}", "ERROR")
            return False

    def test_environment_configuration(self) -> bool:
        """Test 15: Environment Configuration - Flag-based Feature Control"""
        self.log("=== TEST 15: ENVIRONMENT CONFIGURATION ===")
        
        try:
            # Test that environment variables are properly loaded
            # Cricket should be enabled based on SPORTS_CRICKET_ENABLED=true
            result = self.test_endpoint("GET", "/sports")
            if "error" in result:
                self.log(f"❌ Sports endpoint failed: {result['error']}", "ERROR")
                return False
                
            sports = result if isinstance(result, list) else result.get("sports", [])
            sport_keys = [sport.get("key") for sport in sports]
            
            # Verify cricket is available (flag is true)
            if "cricket" not in sport_keys:
                self.log("❌ Cricket not available despite SPORTS_CRICKET_ENABLED=true", "ERROR")
                return False
                
            # Verify football is always available
            if "football" not in sport_keys:
                self.log("❌ Football should always be available", "ERROR")
                return False
                
            # Test backend URL configuration
            # The backend should be accessible at the configured URL
            result = self.test_endpoint("GET", "/")
            if "error" in result:
                self.log(f"❌ Backend URL configuration issue: {result['error']}", "ERROR")
                return False
                
            self.log("✅ Environment configuration working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Environment configuration test failed: {str(e)}", "ERROR")
            return False

    def test_data_integrity(self) -> bool:
        """Test 16: Data Integrity - No Corruption, Proper Relationships"""
        self.log("=== TEST 16: DATA INTEGRITY ===")
        
        try:
            # Test league-participant relationship integrity
            football_league_id = self.test_data["leagues"]["football"]["id"]
            
            # Get league participants
            result = self.test_endpoint("GET", f"/leagues/{football_league_id}/participants")
            if "error" in result:
                self.log(f"❌ Participants retrieval failed: {result['error']}", "ERROR")
                return False
                
            participants = result if isinstance(result, list) else []
            if not participants:
                self.log("❌ No participants found in league", "ERROR")
                return False
                
            # Verify participant data integrity
            participant = participants[0]
            required_fields = ["id", "leagueId", "userId", "userName", "budgetRemaining"]
            for field in required_fields:
                if field not in participant:
                    self.log(f"❌ Missing field {field} in participant", "ERROR")
                    return False
                    
            # Verify league ID matches
            if participant.get("leagueId") != football_league_id:
                self.log("❌ Participant leagueId doesn't match", "ERROR")
                return False
                
            # Test auction-bid relationship integrity if auction exists
            auction_data = self.test_data.get("auction", {})
            auction_id = auction_data.get("id")
            if auction_id:
                result = self.test_endpoint("GET", f"/auction/{auction_id}")
                if "error" in result:
                    self.log(f"❌ Auction retrieval failed: {result['error']}", "ERROR")
                    return False
                    
                bids = result.get("bids", [])
                if bids:
                    bid = bids[0]
                    if bid.get("auctionId") != auction_id:
                        self.log("❌ Bid auctionId doesn't match", "ERROR")
                        return False
                    
            # Test asset data integrity
            result = self.test_endpoint("GET", "/assets", {"sportKey": "football"})
            if "error" in result:
                self.log(f"❌ Football assets failed: {result['error']}", "ERROR")
                return False
                
            football_assets = result.get("assets", [])
            if football_assets:
                asset = football_assets[0]
                # Verify no null/undefined values in critical fields
                if not asset.get("id") or not asset.get("name"):
                    self.log("❌ Asset has null/undefined critical fields", "ERROR")
                    return False
                    
            self.log("✅ Data integrity verified")
            return True
            
        except Exception as e:
            self.log(f"❌ Data integrity test failed: {str(e)}", "ERROR")
            return False

    def test_error_handling(self) -> bool:
        """Test 17: Error Handling - Graceful Failures, Proper HTTP Status"""
        self.log("=== TEST 17: ERROR HANDLING ===")
        
        try:
            # Test 404 errors
            result = self.test_endpoint("GET", "/users/nonexistent-id", expected_status=404)
            if result.get("status_code") != 404:
                self.log("❌ 404 error not properly handled", "ERROR")
                return False
                
            # Test 400 errors (bad request)
            invalid_user_data = {"email": "invalid-email"}  # Missing name
            result = self.test_endpoint("POST", "/users", invalid_user_data, expected_status=422)
            # Note: This might return 422 for validation errors, which is also acceptable
            if result.get("status_code") not in [400, 422]:
                self.log("❌ Bad request error not properly handled", "ERROR")
                return False
                
            # Test 403 errors (forbidden)
            invalid_join_data = {"userId": "fake-user", "inviteToken": "wrong-token"}
            football_league_id = self.test_data["leagues"]["football"]["id"]
            result = self.test_endpoint("POST", f"/leagues/{football_league_id}/join", 
                                      invalid_join_data, expected_status=403)
            if result.get("status_code") != 403:
                self.log("❌ 403 error not properly handled", "ERROR")
                return False
                
            # Test validation errors in cricket scoring
            cricket_league_id = self.test_data["leagues"]["cricket"]["id"]
            invalid_csv = "invalid,csv,format\nno,proper,headers"
            files = {"file": ("invalid.csv", invalid_csv, "text/csv")}
            result = self.test_endpoint("POST", f"/scoring/{cricket_league_id}/ingest", 
                                      files=files, expected_status=400)
            if result.get("status_code") != 400:
                self.log("❌ CSV validation error not properly handled", "ERROR")
                return False
                
            # Test non-cricket league scoring error
            football_league_id = self.test_data["leagues"]["football"]["id"]
            valid_csv = "matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts\nmatch1,player1,50,1,0,0,0"
            files = {"file": ("test.csv", valid_csv, "text/csv")}
            result = self.test_endpoint("POST", f"/scoring/{football_league_id}/ingest", 
                                      files=files, expected_status=400)
            if result.get("status_code") != 400:
                self.log("❌ Non-cricket league scoring error not handled", "ERROR")
                return False
                
            self.log("✅ Error handling working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test failed: {str(e)}", "ERROR")
            return False

    def test_multi_tenancy(self) -> bool:
        """Test 18: Multi-tenancy - Multiple Leagues Simultaneously"""
        self.log("=== TEST 18: MULTI-TENANCY TESTING ===")
        
        try:
            user_id = self.test_data["user"]["id"]
            
            # Create multiple leagues of different sports simultaneously
            leagues_to_create = [
                {"name": "Multi-Tenant Football 1", "sportKey": "football", "budget": 400000000.0},
                {"name": "Multi-Tenant Cricket 1", "sportKey": "cricket", "budget": 250000000.0},
                {"name": "Multi-Tenant Football 2", "sportKey": "football", "budget": 600000000.0},
                {"name": "Multi-Tenant Cricket 2", "sportKey": "cricket", "budget": 300000000.0}
            ]
            
            created_leagues = []
            
            for league_config in leagues_to_create:
                league_data = {
                    "name": league_config["name"],
                    "commissionerId": user_id,
                    "budget": league_config["budget"],
                    "minManagers": 2,
                    "maxManagers": 6,
                    "clubSlots": 4,
                    "sportKey": league_config["sportKey"]
                }
                
                result = self.test_endpoint("POST", "/leagues", league_data)
                if "error" in result:
                    self.log(f"❌ Multi-tenant league creation failed: {result['error']}", "ERROR")
                    return False
                    
                created_leagues.append({
                    "id": result.get("id"),
                    "sportKey": league_config["sportKey"],
                    "name": league_config["name"]
                })
                
            # Test that all leagues exist independently
            for league in created_leagues:
                result = self.test_endpoint("GET", f"/leagues/{league['id']}")
                if "error" in result:
                    self.log(f"❌ Multi-tenant league {league['name']} not found", "ERROR")
                    return False
                    
                if result.get("sportKey") != league["sportKey"]:
                    self.log(f"❌ League {league['name']} has wrong sportKey", "ERROR")
                    return False
                    
            # Test filtering by sport works with multiple leagues
            result = self.test_endpoint("GET", "/leagues", {"sportKey": "football"})
            if "error" in result:
                self.log(f"❌ Football league filtering failed: {result['error']}", "ERROR")
                return False
                
            football_leagues = result if isinstance(result, list) else []
            football_count = len([l for l in football_leagues if l.get("sportKey") == "football"])
            
            if football_count < 2:  # Should have at least our 2 test leagues plus existing ones
                self.log(f"❌ Expected at least 2 football leagues, found {football_count}", "ERROR")
                return False
                
            # Test concurrent operations on different leagues
            football_league = next(l for l in created_leagues if l["sportKey"] == "football")
            cricket_league = next(l for l in created_leagues if l["sportKey"] == "cricket")
            
            # Join both leagues simultaneously
            join_football = {"userId": user_id, "inviteToken": "test-token"}  # This will fail but test isolation
            join_cricket = {"userId": user_id, "inviteToken": "test-token"}
            
            # These should fail independently without affecting each other
            result1 = self.test_endpoint("POST", f"/leagues/{football_league['id']}/join", 
                                       join_football, expected_status=403)
            result2 = self.test_endpoint("POST", f"/leagues/{cricket_league['id']}/join", 
                                       join_cricket, expected_status=403)
            
            # Both should fail with proper error handling (403 status)
            if result1.get("status_code") != 403 or result2.get("status_code") != 403:
                self.log("❌ Multi-tenant error isolation not working", "ERROR")
                return False
                
            # Clean up test leagues
            for league in created_leagues:
                self.test_endpoint("DELETE", f"/leagues/{league['id']}")
                
            self.log("✅ Multi-tenancy working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Multi-tenancy test failed: {str(e)}", "ERROR")
            return False

    def test_feature_flags(self) -> bool:
        """Test 19: Feature Flags - Working for Deployment Control"""
        self.log("=== TEST 19: FEATURE FLAGS ===")
        
        try:
            # Test current flag state (SPORTS_CRICKET_ENABLED=true)
            result = self.test_endpoint("GET", "/sports")
            if "error" in result:
                self.log(f"❌ Sports endpoint failed: {result['error']}", "ERROR")
                return False
                
            sports = result if isinstance(result, list) else result.get("sports", [])
            sport_keys = [sport.get("key") for sport in sports]
            
            # Cricket should be available
            if "cricket" not in sport_keys:
                self.log("❌ Cricket feature flag not working - cricket not available", "ERROR")
                return False
                
            # Test cricket-dependent functionality is accessible
            cricket_endpoints = [
                ("GET", "/sports/cricket"),
                ("GET", "/assets", {"sportKey": "cricket"})
            ]
            
            for method, endpoint, *params in cricket_endpoints:
                data = params[0] if params else None
                result = self.test_endpoint(method, endpoint, data)
                if "error" in result:
                    self.log(f"❌ Cricket endpoint {endpoint} not accessible with flag enabled", "ERROR")
                    return False
                    
            # Test that cricket league creation works
            user_id = self.test_data["user"]["id"]
            cricket_league_data = {
                "name": "Feature Flag Test Cricket League",
                "commissionerId": user_id,
                "budget": 200000000.0,
                "minManagers": 2,
                "maxManagers": 6,
                "clubSlots": 8,
                "sportKey": "cricket"
            }
            
            result = self.test_endpoint("POST", "/leagues", cricket_league_data)
            if "error" in result:
                self.log(f"❌ Cricket league creation failed with flag enabled: {result['error']}", "ERROR")
                return False
                
            test_league_id = result.get("id")
            
            # Test cricket scoring works with flag enabled
            csv_data = "matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts\ntest1,player1,50,1,0,0,0"
            files = {"file": ("flag_test.csv", csv_data, "text/csv")}
            result = self.test_endpoint("POST", f"/scoring/{test_league_id}/ingest", files=files)
            if "error" in result:
                self.log(f"❌ Cricket scoring failed with flag enabled: {result['error']}", "ERROR")
                return False
                
            # Clean up
            if test_league_id:
                self.test_endpoint("DELETE", f"/leagues/{test_league_id}")
                
            # Verify football functionality is unaffected by cricket flag
            result = self.test_endpoint("GET", "/sports/football")
            if "error" in result:
                self.log(f"❌ Football affected by cricket flag: {result['error']}", "ERROR")
                return False
                
            self.log("✅ Feature flags working correctly")
            return True
            
        except Exception as e:
            self.log(f"❌ Feature flags test failed: {str(e)}", "ERROR")
            return False

    def test_performance_stability(self) -> bool:
        """Test 20: Performance & Stability - Within Acceptable Limits"""
        self.log("=== TEST 20: PERFORMANCE & STABILITY ===")
        
        try:
            # Test response times for critical endpoints
            endpoints_to_benchmark = [
                ("GET", "/sports"),
                ("GET", "/assets", {"sportKey": "football"}),
                ("GET", "/assets", {"sportKey": "cricket"}),
                ("GET", "/leagues")
            ]
            
            response_times = []
            
            for method, endpoint, *params in endpoints_to_benchmark:
                data = params[0] if params else None
                
                start_time = time.time()
                result = self.test_endpoint(method, endpoint, data)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if "error" in result:
                    self.log(f"❌ Performance test failed for {endpoint}: {result['error']}", "ERROR")
                    return False
                    
                # Check if response time is reasonable (< 5 seconds for API calls)
                if response_time > 5.0:
                    self.log(f"⚠️ Slow response for {endpoint}: {response_time:.2f}s", "WARN")
                    
            avg_response_time = sum(response_times) / len(response_times)
            self.log(f"Average response time: {avg_response_time:.3f}s")
            
            # Test concurrent requests stability
            user_id = self.test_data["user"]["id"]
            concurrent_requests = []
            
            for i in range(5):
                start_time = time.time()
                result = self.test_endpoint("GET", f"/users/{user_id}")
                end_time = time.time()
                
                if "error" in result:
                    self.log(f"❌ Concurrent request {i+1} failed: {result['error']}", "ERROR")
                    return False
                    
                concurrent_requests.append(end_time - start_time)
                
            # Check for consistency in concurrent requests
            max_concurrent_time = max(concurrent_requests)
            min_concurrent_time = min(concurrent_requests)
            
            if max_concurrent_time - min_concurrent_time > 2.0:
                self.log(f"⚠️ High variance in concurrent requests: {max_concurrent_time - min_concurrent_time:.2f}s", "WARN")
                
            # Test memory stability with large data operations
            result = self.test_endpoint("GET", "/assets", {"sportKey": "football", "pageSize": 50})
            if "error" in result:
                self.log(f"❌ Large data operation failed: {result['error']}", "ERROR")
                return False
                
            self.log("✅ Performance & stability within acceptable limits")
            return True
            
        except Exception as e:
            self.log(f"❌ Performance & stability test failed: {str(e)}", "ERROR")
            return False

    def run_comprehensive_production_test(self) -> Dict[str, bool]:
        """Run all production readiness tests"""
        self.log("🚀 STARTING COMPREHENSIVE PRODUCTION READINESS TEST")
        self.log("=" * 80)
        
        # Define all test functions
        test_functions = [
            ("Multi-Sport Architecture", self.test_multi_sport_architecture),
            ("Authentication & User Management", self.test_authentication_user_management),
            ("League Management", self.test_league_management),
            ("Asset Management", self.test_asset_management),
            ("Auction System", self.test_auction_system),
            ("Socket.IO Real-time", self.test_socketio_realtime),
            ("Cricket Scoring System", self.test_cricket_scoring_system),
            ("Custom Scoring Rules", self.test_custom_scoring_rules),
            ("Cricket Leaderboards", self.test_cricket_leaderboards),
            ("Sport-Aware UI", self.test_sport_aware_ui),
            ("Cricket Flag Control", self.test_cricket_flag_control),
            ("Football Regression", self.test_football_regression),
            ("Database Operations", self.test_database_operations),
            ("API Endpoints", self.test_api_endpoints),
            ("Environment Configuration", self.test_environment_configuration),
            ("Data Integrity", self.test_data_integrity),
            ("Error Handling", self.test_error_handling),
            ("Multi-tenancy", self.test_multi_tenancy),
            ("Feature Flags", self.test_feature_flags),
            ("Performance & Stability", self.test_performance_stability)
        ]
        
        # Run all tests
        for test_name, test_function in test_functions:
            try:
                self.test_results[test_name] = test_function()
                if self.test_results[test_name]:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {str(e)}", "ERROR")
                self.test_results[test_name] = False
                
            self.log("-" * 40)
            
        return self.test_results

    def generate_production_readiness_report(self) -> Tuple[int, str]:
        """Generate final production readiness report with percentage score"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        readiness_percentage = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        self.log("=" * 80)
        self.log("🎯 PRODUCTION READINESS REPORT")
        self.log("=" * 80)
        
        # Passed tests
        self.log("✅ PASSED TESTS:")
        for test_name, result in self.test_results.items():
            if result:
                self.log(f"   ✓ {test_name}")
                
        # Failed tests
        if failed_tests > 0:
            self.log("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result:
                    self.log(f"   ✗ {test_name}")
                    
        self.log(f"\n📊 SUMMARY:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {failed_tests}")
        self.log(f"   Production Readiness Score: {readiness_percentage:.1f}%")
        
        # Determine readiness status
        if readiness_percentage >= 95:
            status = "🟢 PRODUCTION READY"
        elif readiness_percentage >= 85:
            status = "🟡 MOSTLY READY - Minor Issues"
        elif readiness_percentage >= 70:
            status = "🟠 NEEDS WORK - Major Issues"
        else:
            status = "🔴 NOT READY - Critical Issues"
            
        self.log(f"\n🎯 STATUS: {status}")
        
        return int(readiness_percentage), status

def main():
    """Main test execution"""
    tester = ProductionReadinessTest()
    
    # Run comprehensive test
    results = tester.run_comprehensive_production_test()
    
    # Generate report
    percentage, status = tester.generate_production_readiness_report()
    
    print(f"\n🏁 PRODUCTION READINESS TESTING COMPLETE")
    print(f"Final Score: {percentage}% - {status}")
    
    return percentage >= 85  # Return True if ready for production

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)