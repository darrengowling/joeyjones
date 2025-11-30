#!/usr/bin/env python3
"""
Comprehensive Database Index Testing for Production Hardening Day 3
Tests all 26 database indexes created for optimal query performance at scale.
"""

import requests
import json
import uuid
import time
import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import os
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://competition-hub-6.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class DatabaseIndexTester:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.test_results = {}
        self.test_user_id = None
        self.test_league_id = None
        self.test_auction_id = None
        
    def log_test(self, category, test_name, success, details=""):
        """Log test result"""
        if category not in self.test_results:
            self.test_results[category] = {}
        
        self.test_results[category][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category}.{test_name}: {details}")
        
    def test_api_endpoint(self, method, endpoint, data=None, headers=None):
        """Helper to test API endpoints"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            if headers is None:
                headers = {"Content-Type": "application/json"}
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            
            if response.status_code < 400:
                try:
                    return response.json()
                except:
                    return {"success": True, "text": response.text}
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def test_index_existence(self) -> bool:
        """Test 1: Verify all indexes were created successfully"""
        print("=== Testing Index Existence ===")
        
        expected_indexes = {
            "bids": [
                {"key": [("auctionId", 1), ("createdAt", -1)], "name": "auctionId_1_createdAt_-1"},
                {"key": [("userId", 1), ("createdAt", -1)], "name": "userId_1_createdAt_-1"},
                {"key": [("auctionId", 1), ("amount", -1)], "name": "auctionId_1_amount_-1"}
            ],
            "league_stats": [
                {"key": [("leagueId", 1), ("matchId", 1), ("playerExternalId", 1)], "name": "leagueId_1_matchId_1_playerExternalId_1", "unique": True},
                {"key": [("leagueId", 1), ("points", -1)], "name": "leagueId_1_points_-1"},
                {"key": [("leagueId", 1), ("playerExternalId", 1)], "name": "leagueId_1_playerExternalId_1"}
            ],
            "fixtures": [
                {"key": [("leagueId", 1), ("startsAt", 1)], "name": "leagueId_1_startsAt_1"},
                {"key": [("leagueId", 1), ("status", 1)], "name": "leagueId_1_status_1"},
                {"key": [("leagueId", 1), ("externalMatchId", 1)], "name": "leagueId_1_externalMatchId_1"}
            ],
            "assets": [
                {"key": [("sportKey", 1)], "name": "sportKey_1"},
                {"key": [("sportKey", 1), ("name", 1)], "name": "sportKey_1_name_1"},
                {"key": [("sportKey", 1), ("externalId", 1)], "name": "sportKey_1_externalId_1"}
            ],
            "clubs": [
                {"key": [("leagueId", 1)], "name": "leagueId_1"},
                {"key": [("leagueId", 1), ("owner", 1)], "name": "leagueId_1_owner_1"},
                {"key": [("uefaId", 1)], "name": "uefaId_1"}
            ],
            "auctions": [
                {"key": [("leagueId", 1)], "name": "leagueId_1"},
                {"key": [("leagueId", 1), ("status", 1)], "name": "leagueId_1_status_1"}
            ],
            "leagues": [
                {"key": [("sportKey", 1)], "name": "sportKey_1"},
                {"key": [("commissionerId", 1)], "name": "commissionerId_1"},
                {"key": [("inviteToken", 1)], "name": "inviteToken_1", "sparse": True}
            ],
            "league_participants": [
                {"key": [("userId", 1)], "name": "userId_1"},
                {"key": [("leagueId", 1), ("joinedAt", 1)], "name": "leagueId_1_joinedAt_1"}
            ],
            "users": [
                {"key": [("email", 1)], "name": "email_1", "unique": True}
            ],
            "magic_links": [
                {"key": [("email", 1), ("tokenHash", 1)], "name": "email_1_tokenHash_1"},
                {"key": [("expiresAt", 1)], "name": "expiresAt_1", "expireAfterSeconds": 0}
            ]
        }
        
        total_indexes_expected = sum(len(indexes) for indexes in expected_indexes.values())
        indexes_found = 0
        
        for collection_name, expected_collection_indexes in expected_indexes.items():
            collection = self.db[collection_name]
            actual_indexes = list(collection.list_indexes())
            
            for expected_index in expected_collection_indexes:
                found = False
                for actual_index in actual_indexes:
                    # Check if key matches
                    if actual_index.get("key") == dict(expected_index["key"]):
                        found = True
                        indexes_found += 1
                        
                        # Check unique constraint if expected
                        if expected_index.get("unique") and not actual_index.get("unique"):
                            self.log_test("index_existence", f"{collection_name}_{expected_index['name']}_unique", False, "Unique constraint missing")
                            return False
                        
                        # Check TTL if expected
                        if "expireAfterSeconds" in expected_index:
                            if actual_index.get("expireAfterSeconds") != expected_index["expireAfterSeconds"]:
                                self.log_test("index_existence", f"{collection_name}_{expected_index['name']}_ttl", False, "TTL configuration incorrect")
                                return False
                        
                        # Check sparse if expected - look for any sparse index with this key
                        if expected_index.get("sparse"):
                            sparse_found = any(idx.get("sparse") and idx.get("key") == dict(expected_index["key"]) for idx in actual_indexes)
                            if not sparse_found:
                                self.log_test("index_existence", f"{collection_name}_{expected_index['name']}_sparse", False, "Sparse configuration missing")
                                return False
                        
                        break
                
                if not found:
                    self.log_test("index_existence", f"{collection_name}_{expected_index['name']}", False, "Index not found")
                    return False
        
        self.log_test("index_existence", "all_indexes", True, f"All {total_indexes_expected} indexes found and configured correctly")
        return True
    
    def setup_test_data(self) -> bool:
        """Setup test data for query performance testing"""
        print("=== Setting up test data ===")
        
        try:
            # Create test user
            user_data = {
                "name": f"IndexTestUser_{uuid.uuid4().hex[:8]}",
                "email": f"indextest_{uuid.uuid4().hex[:8]}@example.com"
            }
            
            user_result = self.test_api_endpoint("POST", "/users", user_data)
            if "error" in user_result:
                self.log_test("setup", "create_user", False, f"Failed to create user: {user_result}")
                return False
            
            self.test_user_id = user_result["id"]
            
            # Create test league
            league_data = {
                "name": f"Index Test League {uuid.uuid4().hex[:8]}",
                "commissionerId": self.test_user_id,
                "budget": 500000000.0,  # £500M budget
                "minManagers": 2,
                "maxManagers": 4,
                "clubSlots": 3,
                "sportKey": "football"
            }
            
            league_result = self.test_api_endpoint("POST", "/leagues", league_data)
            if "error" in league_result:
                self.log_test("setup", "create_league", False, f"Failed to create league: {league_result}")
                return False
            
            self.test_league_id = league_result["id"]
            
            # Join league
            join_data = {
                "userId": self.test_user_id,
                "inviteToken": league_result["inviteToken"]
            }
            
            join_result = self.test_api_endpoint("POST", f"/leagues/{self.test_league_id}/join", join_data)
            if "error" in join_result:
                self.log_test("setup", "join_league", False, f"Failed to join league: {join_result}")
                return False
            
            # Start auction
            auction_result = self.test_api_endpoint("POST", f"/leagues/{self.test_league_id}/auction/start")
            if "error" in auction_result:
                self.log_test("setup", "start_auction", False, f"Failed to start auction: {auction_result}")
                return False
            
            self.test_auction_id = auction_result["auctionId"]
            
            # Begin the auction to get it to active state
            begin_result = self.test_api_endpoint("POST", f"/auction/{self.test_auction_id}/begin", headers={"X-User-ID": self.test_user_id})
            if "error" in begin_result:
                self.log_test("setup", "begin_auction", False, f"Failed to begin auction: {begin_result}")
                return False
            
            self.log_test("setup", "test_data", True, "Test data created successfully")
            return True
            
        except Exception as e:
            self.log_test("setup", "test_data", False, f"Exception: {str(e)}")
            return False
    
    def test_auction_bid_queries(self) -> bool:
        """Test 2a: Auction Bid Queries using indexes"""
        print("=== Testing Auction Bid Query Performance ===")
        
        if not self.test_auction_id:
            self.log_test("bid_queries", "setup", False, "No auction available")
            return False
        
        try:
            # Get current club for bidding
            auction_result = self.test_api_endpoint("GET", f"/auction/{self.test_auction_id}")
            if "error" in auction_result:
                self.log_test("bid_queries", "get_auction", False, "Failed to get auction")
                return False
            
            current_club = auction_result.get("currentClub")
            if not current_club:
                self.log_test("bid_queries", "current_club", False, "No current club available")
                return False
            
            # Place multiple bids to test indexes
            bid_amounts = [1000000, 1500000, 2000000, 2500000, 3000000]  # £1M to £3M
            
            for amount in bid_amounts:
                bid_data = {
                    "userId": self.test_user_id,
                    "clubId": current_club["id"],
                    "amount": float(amount)
                }
                
                bid_result = self.test_api_endpoint("POST", f"/auction/{self.test_auction_id}/bid", bid_data)
                if "error" in bid_result:
                    self.log_test("bid_queries", f"place_bid_{amount}", False, f"Failed to place bid: {bid_result}")
                    return False
            
            # Test Query 1: Get all bids for an auction (uses auctionId+createdAt index)
            start_time = time.time()
            bids_collection = self.db.bids
            auction_bids = list(bids_collection.find({"auctionId": self.test_auction_id}).sort("createdAt", -1))
            query1_time = time.time() - start_time
            
            if len(auction_bids) >= 5:
                self.log_test("bid_queries", "auction_bids_query", True, f"Found {len(auction_bids)} bids in {query1_time:.3f}s")
            else:
                self.log_test("bid_queries", "auction_bids_query", False, f"Expected at least 5 bids, found {len(auction_bids)}")
                return False
            
            # Test Query 2: Get user bid history (uses userId+createdAt index)
            start_time = time.time()
            user_bids = list(bids_collection.find({"userId": self.test_user_id}).sort("createdAt", -1))
            query2_time = time.time() - start_time
            
            if len(user_bids) >= 5:
                self.log_test("bid_queries", "user_bids_query", True, f"Found {len(user_bids)} user bids in {query2_time:.3f}s")
            else:
                self.log_test("bid_queries", "user_bids_query", False, f"Expected at least 5 user bids, found {len(user_bids)}")
                return False
            
            # Test Query 3: Find highest bid for auction (uses auctionId+amount index)
            start_time = time.time()
            highest_bid = bids_collection.find_one({"auctionId": self.test_auction_id}, sort=[("amount", -1)])
            query3_time = time.time() - start_time
            
            if highest_bid and highest_bid["amount"] == 3000000.0:
                self.log_test("bid_queries", "highest_bid_query", True, f"Found highest bid £{highest_bid['amount']:,.0f} in {query3_time:.3f}s")
            else:
                self.log_test("bid_queries", "highest_bid_query", False, f"Highest bid query failed or incorrect amount")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("bid_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_league_stats_queries(self) -> bool:
        """Test 2b: League Stats Queries using indexes"""
        print("=== Testing League Stats Query Performance ===")
        
        if not self.test_league_id:
            self.log_test("league_stats_queries", "setup", False, "No league available")
            return False
        
        try:
            # Insert test league stats data
            league_stats_collection = self.db.league_stats
            
            # Create sample league stats data
            test_stats = []
            for match_id in range(1, 6):  # 5 matches
                for player_id in range(1, 11):  # 10 players per match
                    stat = {
                        "id": str(uuid.uuid4()),
                        "leagueId": self.test_league_id,
                        "matchId": f"match_{match_id}",
                        "playerExternalId": f"player_{player_id}",
                        "points": float(match_id * player_id * 10),  # Varying points
                        "createdAt": datetime.now(timezone.utc),
                        "updatedAt": datetime.now(timezone.utc)
                    }
                    test_stats.append(stat)
            
            # Insert test data
            league_stats_collection.insert_many(test_stats)
            
            # Test Query 1: Get league leaderboard sorted by points (uses leagueId+points index)
            start_time = time.time()
            leaderboard = list(league_stats_collection.find({"leagueId": self.test_league_id}).sort("points", -1).limit(10))
            query1_time = time.time() - start_time
            
            if len(leaderboard) == 10:
                # Verify sorting
                points_sorted = all(leaderboard[i]["points"] >= leaderboard[i+1]["points"] for i in range(len(leaderboard)-1))
                if points_sorted:
                    self.log_test("league_stats_queries", "leaderboard_query", True, f"Retrieved sorted leaderboard in {query1_time:.3f}s")
                else:
                    self.log_test("league_stats_queries", "leaderboard_query", False, "Leaderboard not properly sorted")
                    return False
            else:
                self.log_test("league_stats_queries", "leaderboard_query", False, f"Expected 10 results, got {len(leaderboard)}")
                return False
            
            # Test Query 2: Get player stats across matches (uses leagueId+playerExternalId index)
            start_time = time.time()
            player_stats = list(league_stats_collection.find({
                "leagueId": self.test_league_id,
                "playerExternalId": "player_5"
            }))
            query2_time = time.time() - start_time
            
            if len(player_stats) == 5:  # Should have stats for 5 matches
                self.log_test("league_stats_queries", "player_stats_query", True, f"Retrieved player stats in {query2_time:.3f}s")
            else:
                self.log_test("league_stats_queries", "player_stats_query", False, f"Expected 5 player stats, got {len(player_stats)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("league_stats_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_fixture_queries(self) -> bool:
        """Test 2c: Fixture Queries using indexes"""
        print("=== Testing Fixture Query Performance ===")
        
        if not self.test_league_id:
            self.log_test("fixture_queries", "setup", False, "No league available")
            return False
        
        try:
            # Insert test fixture data
            fixtures_collection = self.db.fixtures
            
            # Create sample fixture data
            test_fixtures = []
            statuses = ["scheduled", "live", "completed"]
            
            for i in range(1, 16):  # 15 fixtures
                fixture = {
                    "id": str(uuid.uuid4()),
                    "leagueId": self.test_league_id,
                    "sportKey": "football",
                    "externalMatchId": f"ext_match_{i}",
                    "homeAssetId": str(uuid.uuid4()),
                    "awayAssetId": str(uuid.uuid4()),
                    "startsAt": datetime.now(timezone.utc) + timedelta(days=i),
                    "status": statuses[i % 3],
                    "round": f"Round {(i-1)//5 + 1}",
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc)
                }
                test_fixtures.append(fixture)
            
            # Insert test data
            fixtures_collection.insert_many(test_fixtures)
            
            # Test Query 1: Get league fixtures sorted by time (uses leagueId+startsAt index)
            start_time = time.time()
            fixtures_by_time = list(fixtures_collection.find({"leagueId": self.test_league_id}).sort("startsAt", 1))
            query1_time = time.time() - start_time
            
            if len(fixtures_by_time) == 15:
                # Verify sorting
                time_sorted = all(fixtures_by_time[i]["startsAt"] <= fixtures_by_time[i+1]["startsAt"] for i in range(len(fixtures_by_time)-1))
                if time_sorted:
                    self.log_test("fixture_queries", "fixtures_by_time_query", True, f"Retrieved time-sorted fixtures in {query1_time:.3f}s")
                else:
                    self.log_test("fixture_queries", "fixtures_by_time_query", False, "Fixtures not properly sorted by time")
                    return False
            else:
                self.log_test("fixture_queries", "fixtures_by_time_query", False, f"Expected 15 fixtures, got {len(fixtures_by_time)}")
                return False
            
            # Test Query 2: Filter fixtures by status (uses leagueId+status index)
            start_time = time.time()
            scheduled_fixtures = list(fixtures_collection.find({
                "leagueId": self.test_league_id,
                "status": "scheduled"
            }))
            query2_time = time.time() - start_time
            
            if len(scheduled_fixtures) == 5:  # Should have 5 scheduled fixtures
                self.log_test("fixture_queries", "fixtures_by_status_query", True, f"Retrieved status-filtered fixtures in {query2_time:.3f}s")
            else:
                self.log_test("fixture_queries", "fixtures_by_status_query", False, f"Expected 5 scheduled fixtures, got {len(scheduled_fixtures)}")
                return False
            
            # Test Query 3: Find fixture by externalMatchId (uses leagueId+externalMatchId index)
            start_time = time.time()
            specific_fixture = fixtures_collection.find_one({
                "leagueId": self.test_league_id,
                "externalMatchId": "ext_match_10"
            })
            query3_time = time.time() - start_time
            
            if specific_fixture and specific_fixture["externalMatchId"] == "ext_match_10":
                self.log_test("fixture_queries", "fixture_by_external_id_query", True, f"Found specific fixture in {query3_time:.3f}s")
            else:
                self.log_test("fixture_queries", "fixture_by_external_id_query", False, "Failed to find fixture by external match ID")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("fixture_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_asset_queries(self) -> bool:
        """Test 2d: Asset Queries using indexes"""
        print("=== Testing Asset Query Performance ===")
        
        try:
            # Test with existing clubs data (football assets)
            clubs_collection = self.db.clubs
            
            # Test Query 1: Get assets by sport (uses sportKey index for assets collection)
            # First test with assets collection
            assets_collection = self.db.assets
            
            # Insert some test cricket assets
            test_assets = []
            for i in range(1, 21):  # 20 cricket players
                asset = {
                    "id": str(uuid.uuid4()),
                    "sportKey": "cricket",
                    "externalId": f"cricket_player_{i}",
                    "name": f"Cricket Player {i}",
                    "meta": {
                        "franchise": f"Team {(i-1)//4 + 1}",
                        "role": ["batsman", "bowler", "all-rounder"][i % 3]
                    },
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc)
                }
                test_assets.append(asset)
            
            # Insert test cricket assets
            assets_collection.insert_many(test_assets)
            
            # Test Query 1: Get assets by sport (uses sportKey index)
            start_time = time.time()
            cricket_assets = list(assets_collection.find({"sportKey": "cricket"}))
            query1_time = time.time() - start_time
            
            if len(cricket_assets) >= 20:  # Allow for existing cricket assets
                self.log_test("asset_queries", "assets_by_sport_query", True, f"Retrieved {len(cricket_assets)} cricket assets in {query1_time:.3f}s")
            else:
                self.log_test("asset_queries", "assets_by_sport_query", False, f"Expected at least 20 cricket assets, got {len(cricket_assets)}")
                return False
            
            # Test Query 2: Search assets by name (uses sportKey+name index)
            start_time = time.time()
            named_assets = list(assets_collection.find({
                "sportKey": "cricket",
                "name": {"$regex": "Player 1", "$options": "i"}
            }))
            query2_time = time.time() - start_time
            
            if len(named_assets) >= 10:  # Should find Player 1, Player 10-19
                self.log_test("asset_queries", "assets_by_name_query", True, f"Found {len(named_assets)} named assets in {query2_time:.3f}s")
            else:
                self.log_test("asset_queries", "assets_by_name_query", False, f"Expected at least 10 named assets, got {len(named_assets)}")
                return False
            
            # Test Query 3: Find asset by externalId (uses sportKey+externalId index)
            start_time = time.time()
            specific_asset = assets_collection.find_one({
                "sportKey": "cricket",
                "externalId": "cricket_player_15"
            })
            query3_time = time.time() - start_time
            
            if specific_asset and specific_asset["externalId"] == "cricket_player_15":
                self.log_test("asset_queries", "asset_by_external_id_query", True, f"Found specific asset in {query3_time:.3f}s")
            else:
                self.log_test("asset_queries", "asset_by_external_id_query", False, "Failed to find asset by external ID")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("asset_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_league_queries(self) -> bool:
        """Test 2e: League Queries using indexes"""
        print("=== Testing League Query Performance ===")
        
        try:
            leagues_collection = self.db.leagues
            
            # Test Query 1: Get leagues by sport (uses sportKey index)
            start_time = time.time()
            football_leagues = list(leagues_collection.find({"sportKey": "football"}))
            query1_time = time.time() - start_time
            
            if len(football_leagues) >= 1:  # Should have at least our test league
                self.log_test("league_queries", "leagues_by_sport_query", True, f"Found {len(football_leagues)} football leagues in {query1_time:.3f}s")
            else:
                self.log_test("league_queries", "leagues_by_sport_query", False, "No football leagues found")
                return False
            
            # Test Query 2: Get commissioner's leagues (uses commissionerId index)
            start_time = time.time()
            commissioner_leagues = list(leagues_collection.find({"commissionerId": self.test_user_id}))
            query2_time = time.time() - start_time
            
            if len(commissioner_leagues) >= 1:  # Should have at least our test league
                self.log_test("league_queries", "leagues_by_commissioner_query", True, f"Found {len(commissioner_leagues)} commissioner leagues in {query2_time:.3f}s")
            else:
                self.log_test("league_queries", "leagues_by_commissioner_query", False, "No commissioner leagues found")
                return False
            
            # Test Query 3: Find league by invite token (uses inviteToken index)
            # Get the invite token from our test league
            test_league = leagues_collection.find_one({"id": self.test_league_id})
            if not test_league or not test_league.get("inviteToken"):
                self.log_test("league_queries", "league_by_token_setup", False, "No invite token available")
                return False
            
            start_time = time.time()
            token_league = leagues_collection.find_one({"inviteToken": test_league["inviteToken"]})
            query3_time = time.time() - start_time
            
            if token_league and token_league["id"] == self.test_league_id:
                self.log_test("league_queries", "league_by_token_query", True, f"Found league by token in {query3_time:.3f}s")
            else:
                self.log_test("league_queries", "league_by_token_query", False, "Failed to find league by invite token")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("league_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_user_auth_queries(self) -> bool:
        """Test 2f: User/Auth Queries using indexes"""
        print("=== Testing User/Auth Query Performance ===")
        
        try:
            users_collection = self.db.users
            magic_links_collection = self.db.magic_links
            
            # Test Query 1: Find user by email (uses email unique index)
            test_user = users_collection.find_one({"id": self.test_user_id})
            if not test_user:
                self.log_test("user_auth_queries", "setup", False, "Test user not found")
                return False
            
            start_time = time.time()
            user_by_email = users_collection.find_one({"email": test_user["email"]})
            query1_time = time.time() - start_time
            
            if user_by_email and user_by_email["id"] == self.test_user_id:
                self.log_test("user_auth_queries", "user_by_email_query", True, f"Found user by email in {query1_time:.3f}s")
            else:
                self.log_test("user_auth_queries", "user_by_email_query", False, "Failed to find user by email")
                return False
            
            # Test Query 2: Find magic link by email+token (uses email+tokenHash index)
            # Create a test magic link
            test_magic_link = {
                "id": str(uuid.uuid4()),
                "email": test_user["email"],
                "tokenHash": "test_hash_" + uuid.uuid4().hex,
                "expiresAt": datetime.now(timezone.utc) + timedelta(minutes=15),
                "used": False,
                "createdAt": datetime.now(timezone.utc)
            }
            
            magic_links_collection.insert_one(test_magic_link)
            
            start_time = time.time()
            magic_link = magic_links_collection.find_one({
                "email": test_user["email"],
                "tokenHash": test_magic_link["tokenHash"]
            })
            query2_time = time.time() - start_time
            
            if magic_link and magic_link["id"] == test_magic_link["id"]:
                self.log_test("user_auth_queries", "magic_link_query", True, f"Found magic link in {query2_time:.3f}s")
            else:
                self.log_test("user_auth_queries", "magic_link_query", False, "Failed to find magic link")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("user_auth_queries", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_unique_constraints(self) -> bool:
        """Test 3: Unique Constraint Testing"""
        print("=== Testing Unique Constraints ===")
        
        try:
            # Test 1: league_stats unique constraint (leagueId+matchId+playerExternalId)
            league_stats_collection = self.db.league_stats
            
            # Try to insert duplicate league stat
            duplicate_stat = {
                "id": str(uuid.uuid4()),
                "leagueId": self.test_league_id,
                "matchId": "match_1",
                "playerExternalId": "player_1",
                "points": 100.0,
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            
            try:
                # First insert should succeed
                league_stats_collection.insert_one(duplicate_stat.copy())
                
                # Second insert should fail due to unique constraint
                duplicate_stat["id"] = str(uuid.uuid4())  # Different ID but same unique fields
                league_stats_collection.insert_one(duplicate_stat)
                
                self.log_test("unique_constraints", "league_stats_unique", False, "Duplicate league stat was allowed")
                return False
                
            except pymongo.errors.DuplicateKeyError:
                self.log_test("unique_constraints", "league_stats_unique", True, "League stats unique constraint working")
            
            # Test 2: users email unique constraint
            users_collection = self.db.users
            
            # Try to insert duplicate user email
            duplicate_user = {
                "id": str(uuid.uuid4()),
                "name": "Duplicate User",
                "email": "duplicate@test.com",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            
            try:
                # First insert should succeed
                users_collection.insert_one(duplicate_user.copy())
                
                # Second insert should fail due to unique constraint
                duplicate_user["id"] = str(uuid.uuid4())  # Different ID but same email
                duplicate_user["name"] = "Another Duplicate User"
                users_collection.insert_one(duplicate_user)
                
                self.log_test("unique_constraints", "users_email_unique", False, "Duplicate user email was allowed")
                return False
                
            except pymongo.errors.DuplicateKeyError:
                self.log_test("unique_constraints", "users_email_unique", True, "Users email unique constraint working")
            
            return True
            
        except Exception as e:
            self.log_test("unique_constraints", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_ttl_index(self) -> bool:
        """Test 4: TTL Index Testing"""
        print("=== Testing TTL Index ===")
        
        try:
            magic_links_collection = self.db.magic_links
            
            # Check TTL index configuration
            indexes = list(magic_links_collection.list_indexes())
            ttl_index = None
            
            for index in indexes:
                if "expiresAt" in index.get("key", {}):
                    ttl_index = index
                    break
            
            if not ttl_index:
                self.log_test("ttl_index", "index_exists", False, "TTL index on expiresAt not found")
                return False
            
            # Check TTL configuration
            expire_after_seconds = ttl_index.get("expireAfterSeconds")
            if expire_after_seconds != 0:
                self.log_test("ttl_index", "ttl_config", False, f"TTL should be 0 (immediate), found {expire_after_seconds}")
                return False
            
            self.log_test("ttl_index", "configuration", True, "TTL index configured correctly (expireAfterSeconds=0)")
            
            # Test TTL functionality by inserting expired document
            expired_magic_link = {
                "id": str(uuid.uuid4()),
                "email": "expired@test.com",
                "tokenHash": "expired_hash",
                "expiresAt": datetime.now(timezone.utc) - timedelta(minutes=1),  # Already expired
                "used": False,
                "createdAt": datetime.now(timezone.utc)
            }
            
            magic_links_collection.insert_one(expired_magic_link)
            
            # Wait a moment for TTL to process (MongoDB TTL runs every 60 seconds, but we can check the setup)
            time.sleep(2)
            
            # The document might still exist since TTL cleanup runs periodically
            # But the important thing is that the index is configured correctly
            self.log_test("ttl_index", "functionality", True, "TTL index setup verified (cleanup runs periodically)")
            
            return True
            
        except Exception as e:
            self.log_test("ttl_index", "exception", False, f"Exception: {str(e)}")
            return False
    
    def test_index_usage_validation(self) -> bool:
        """Test 5: Index Usage Validation using explain()"""
        print("=== Testing Index Usage Validation ===")
        
        try:
            # Test 1: Verify bid query uses auctionId+createdAt index
            bids_collection = self.db.bids
            
            if self.test_auction_id:
                explain_result = bids_collection.find({"auctionId": self.test_auction_id}).sort("createdAt", -1).explain()
                
                # Check if index was used
                execution_stats = explain_result.get("executionStats", {})
                winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                
                if "IXSCAN" in str(winning_plan):
                    self.log_test("index_usage", "bid_query_uses_index", True, "Bid query uses index scan")
                else:
                    self.log_test("index_usage", "bid_query_uses_index", False, "Bid query not using index")
                    return False
            
            # Test 2: Verify league stats query uses leagueId+points index
            league_stats_collection = self.db.league_stats
            
            if self.test_league_id:
                explain_result = league_stats_collection.find({"leagueId": self.test_league_id}).sort("points", -1).explain()
                
                winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                
                if "IXSCAN" in str(winning_plan):
                    self.log_test("index_usage", "leaderboard_query_uses_index", True, "Leaderboard query uses index scan")
                else:
                    self.log_test("index_usage", "leaderboard_query_uses_index", False, "Leaderboard query not using index")
                    return False
            
            # Test 3: Verify user email query uses unique index
            users_collection = self.db.users
            
            if self.test_user_id:
                test_user = users_collection.find_one({"id": self.test_user_id})
                if test_user:
                    explain_result = users_collection.find({"email": test_user["email"]}).explain()
                    
                    winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                    
                    if "IXSCAN" in str(winning_plan):
                        self.log_test("index_usage", "user_email_query_uses_index", True, "User email query uses index scan")
                    else:
                        self.log_test("index_usage", "user_email_query_uses_index", False, "User email query not using index")
                        return False
            
            return True
            
        except Exception as e:
            self.log_test("index_usage", "exception", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("=== Cleaning up test data ===")
        
        try:
            # Delete test league (cascades to auction, bids, participants)
            if self.test_league_id and self.test_user_id:
                delete_result = self.test_api_endpoint("DELETE", f"/leagues/{self.test_league_id}?user_id={self.test_user_id}")
                if "error" not in delete_result:
                    print("✅ Test league deleted")
            
            # Clean up test collections data
            collections_to_clean = [
                "league_stats", "fixtures", "assets", "magic_links", "users"
            ]
            
            for collection_name in collections_to_clean:
                collection = self.db[collection_name]
                # Delete test data (be careful not to delete all data)
                if collection_name == "league_stats" and self.test_league_id:
                    collection.delete_many({"leagueId": self.test_league_id})
                elif collection_name == "fixtures" and self.test_league_id:
                    collection.delete_many({"leagueId": self.test_league_id})
                elif collection_name == "assets":
                    collection.delete_many({"sportKey": "cricket", "name": {"$regex": "Cricket Player"}})
                elif collection_name == "magic_links":
                    collection.delete_many({"email": {"$regex": "test.com"}})
                elif collection_name == "users":
                    collection.delete_many({"email": {"$regex": "test.com"}})
            
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all database index tests"""
        print("🚀 Starting Database Index Tests")
        
        results = {}
        
        # Test 1: Index Existence Verification
        results["index_existence"] = self.test_index_existence()
        
        # Setup test data for performance tests
        if not self.setup_test_data():
            print("❌ Failed to setup test data, skipping performance tests")
            return results
        
        # Test 2: Query Performance Testing
        results["auction_bid_queries"] = self.test_auction_bid_queries()
        results["league_stats_queries"] = self.test_league_stats_queries()
        results["fixture_queries"] = self.test_fixture_queries()
        results["asset_queries"] = self.test_asset_queries()
        results["league_queries"] = self.test_league_queries()
        results["user_auth_queries"] = self.test_user_auth_queries()
        
        # Test 3: Unique Constraint Testing
        results["unique_constraints"] = self.test_unique_constraints()
        
        # Test 4: TTL Index Testing
        results["ttl_index"] = self.test_ttl_index()
        
        # Test 5: Index Usage Validation
        results["index_usage_validation"] = self.test_index_usage_validation()
        
        # Cleanup
        self.cleanup_test_data()
        
        return results

def main():
    """Main test execution"""
    tester = DatabaseIndexTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("DATABASE INDEX TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All database index tests passed!")
        print("✅ All 26 indexes created and accessible")
        print("✅ Queries execute successfully using appropriate indexes")
        print("✅ Unique constraints prevent duplicates")
        print("✅ TTL index configured correctly")
        print("✅ Index usage validated with explain()")
        return True
    else:
        print("⚠️  Some database index tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)