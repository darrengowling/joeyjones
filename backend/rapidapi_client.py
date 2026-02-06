"""
RapidAPI Client for Football and Cricket Data
Supports multiple providers on RapidAPI platform
"""
import os
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RapidAPIFootballClient:
    """
    Football data client for RapidAPI providers
    Supports: FootAPI, API-Football, and similar providers
    """
    
    def __init__(self):
        self.api_key = os.environ.get('RAPIDAPI_KEY')
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not configured")
        
        # Try to detect which football API is being used
        # FootAPI uses different base URL than API-Football
        self.base_url = "https://footapi7.p.rapidapi.com/api"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "footapi7.p.rapidapi.com"
        }
        
        self.request_count = 0
        self.daily_limit = 50  # Free tier for FootAPI
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to RapidAPI"""
        if not self.api_key:
            logger.error("RAPIDAPI_KEY not configured - API calls will fail")
            return None
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params or {})
                self.request_count += 1
                
                logger.info(f"RapidAPI Football request to {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"RapidAPI error: {response.status_code} - {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.error(f"RapidAPI request failed: {e}")
            return None
    
    async def get_recent_fixtures(self, league_id: int = 39, page: int = 0) -> List[Dict]:
        """
        Get recent fixtures (last 30 matches)
        
        Args:
            league_id: League ID (39 = EPL)
            page: Page number for pagination
        
        Returns:
            List of fixture dictionaries
        """
        # FootAPI uses tournament ID structure
        # EPL = tournament 17 (Premier League)
        # Season 61627 = 2024-25
        tournament_id = 17 if league_id == 39 else league_id
        season_id = 61627  # Current EPL season 2024-25
        
        endpoint = f"tournament/{tournament_id}/season/{season_id}/matches/last/{page}"
        response = await self._make_request(endpoint)
        
        if not response:
            return []
        
        # Parse FootAPI response structure
        fixtures = []
        events = response.get("events", [])
        
        for event in events:
            try:
                # Convert timestamp to ISO format
                start_timestamp = event.get("startTimestamp")
                if start_timestamp:
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(start_timestamp).isoformat()
                else:
                    date_str = None
                
                fixture = {
                    "fixture": {
                        "id": event.get("id"),
                        "date": date_str,
                        "timestamp": start_timestamp,
                        "status": {
                            "short": self._map_status(event.get("status", {}).get("type"))
                        },
                        "venue": {
                            "name": event.get("venue", {}).get("stadium", {}).get("name", "") if event.get("venue") else ""
                        }
                    },
                    "teams": {
                        "home": {
                            "id": event.get("homeTeam", {}).get("id"),
                            "name": event.get("homeTeam", {}).get("name")
                        },
                        "away": {
                            "id": event.get("awayTeam", {}).get("id"),
                            "name": event.get("awayTeam", {}).get("name")
                        }
                    },
                    "goals": {
                        "home": event.get("homeScore", {}).get("current"),
                        "away": event.get("awayScore", {}).get("current")
                    },
                    "league": {
                        "id": tournament_id,
                        "name": event.get("tournament", {}).get("name", "Premier League")
                    }
                }
                fixtures.append(fixture)
            except Exception as e:
                logger.error(f"Error parsing fixture: {e}")
                continue
        
        logger.info(f"Found {len(fixtures)} recent fixtures")
        return fixtures
    
    async def get_fixtures_by_date(self, date_str: str, league_id: int = 39) -> List[Dict]:
        """
        Get fixtures for a specific date (filters recent fixtures by date)
        
        Args:
            date_str: Date in YYYY-MM-DD format  
            league_id: League ID (39 = EPL)
        
        Returns:
            List of fixture dictionaries
        """
        
        # Get recent fixtures and filter by date
        all_fixtures = await self.get_recent_fixtures(league_id)
        
        # Parse target date
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Filter fixtures for the target date
        filtered = []
        for fixture in all_fixtures:
            if fixture["fixture"]["date"]:
                fixture_date = datetime.fromisoformat(fixture["fixture"]["date"]).date()
                if fixture_date == target_date:
                    filtered.append(fixture)
        
        logger.info(f"Found {len(filtered)} fixtures for date {date_str}")
        return filtered
    
    def _map_status(self, status_type: str) -> str:
        """Map FootAPI status to standard format"""
        status_map = {
            "finished": "ft",
            "inprogress": "live",
            "notstarted": "ns",
            "postponed": "pst",
            "cancelled": "canc"
        }
        return status_map.get(status_type, "ns")
    
    async def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict]:
        """Get single fixture details by ID"""
        response = await self._make_request(f"match/{fixture_id}")
        
        if not response:
            return None
        
        event = response.get("event", {})
        
        return {
            "fixture": {
                "id": event.get("id"),
                "date": event.get("startTimestamp"),
                "status": {
                    "short": self._map_status(event.get("status", {}).get("type"))
                }
            },
            "teams": {
                "home": {
                    "id": event.get("homeTeam", {}).get("id"),
                    "name": event.get("homeTeam", {}).get("name")
                },
                "away": {
                    "id": event.get("awayTeam", {}).get("id"),
                    "name": event.get("awayTeam", {}).get("name")
                }
            },
            "goals": {
                "home": event.get("homeScore", {}).get("current"),
                "away": event.get("awayScore", {}).get("current")
            }
        }
    
    def get_requests_remaining(self) -> int:
        """Get remaining API requests for the day"""
        return max(0, self.daily_limit - self.request_count)


class RapidAPICricketClient:
    """
    Cricket data client for Cricbuzz via RapidAPI
    """
    
    def __init__(self):
        self.api_key = os.environ.get('RAPIDAPI_KEY')
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not configured")
        
        self.base_url = "https://cricbuzz-cricket.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }
        
        self.request_count = 0
        self.daily_limit = 100  # Free tier for Cricbuzz
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to RapidAPI"""
        if not self.api_key:
            logger.error("RAPIDAPI_KEY not configured - API calls will fail")
            return None
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params or {})
                self.request_count += 1
                
                logger.info(f"RapidAPI Cricket request to {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"RapidAPI error: {response.status_code} - {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.error(f"RapidAPI request failed: {e}")
            return None
    
    async def get_recent_matches(self) -> List[Dict]:
        """
        Get recent, live, AND upcoming cricket matches
        Combines all three sources to get complete picture
        
        Returns:
            List of match dictionaries
        """
        # Get recent, live, and upcoming matches
        recent_response = await self._make_request("matches/v1/recent")
        live_response = await self._make_request("matches/v1/live")
        upcoming_response = await self._make_request("matches/v1/upcoming")
        
        matches = []
        
        # Process recent matches
        if recent_response:
            type_matches = recent_response.get("typeMatches", [])
        
        for type_match in type_matches:
            series_matches = type_match.get("seriesMatches", [])
            for series in series_matches:
                series_match_list = series.get("seriesAdWrapper", {}).get("matches", [])
                for match in series_match_list:
                    match_info = match.get("matchInfo", {})
                    match_score = match.get("matchScore", {})
                    
                    matches.append({
                        "matchId": match_info.get("matchId"),
                        "seriesName": match_info.get("seriesName"),
                        "matchDesc": match_info.get("matchDesc"),
                        "matchFormat": match_info.get("matchFormat"),
                        "team1": match_info.get("team1", {}).get("teamName"),
                        "team2": match_info.get("team2", {}).get("teamName"),
                        "status": match_info.get("status"),
                        "state": match_info.get("state"),
                        "venue": match_info.get("venueInfo", {}).get("ground"),
                        "startDate": match_info.get("startDate")
                    })
        
        # Process live matches (same structure)
        if live_response:
            type_matches = live_response.get("typeMatches", [])
            for type_match in type_matches:
                series_matches = type_match.get("seriesMatches", [])
                for series in series_matches:
                    series_match_list = series.get("seriesAdWrapper", {}).get("matches", [])
                    for match in series_match_list:
                        match_info = match.get("matchInfo", {})
                        
                        # Avoid duplicates
                        match_id = match_info.get("matchId")
                        if any(m.get("matchId") == match_id for m in matches):
                            continue
                        
                        matches.append({
                            "matchId": match_id,
                            "seriesName": match_info.get("seriesName"),
                            "matchDesc": match_info.get("matchDesc"),
                            "matchFormat": match_info.get("matchFormat"),
                            "team1": match_info.get("team1", {}).get("teamName"),
                            "team2": match_info.get("team2", {}).get("teamName"),
                            "status": match_info.get("status"),
                            "state": match_info.get("state"),
                            "venue": match_info.get("venueInfo", {}).get("ground"),
                            "startDate": match_info.get("startDate")
                        })
        
        # Process upcoming matches (same structure)
        if upcoming_response:
            type_matches = upcoming_response.get("typeMatches", [])
            for type_match in type_matches:
                series_matches = type_match.get("seriesMatches", [])
                for series in series_matches:
                    series_match_list = series.get("seriesAdWrapper", {}).get("matches", [])
                    for match in series_match_list:
                        match_info = match.get("matchInfo", {})
                        
                        # Avoid duplicates
                        match_id = match_info.get("matchId")
                        if any(m.get("matchId") == match_id for m in matches):
                            continue
                        
                        matches.append({
                            "matchId": match_id,
                            "seriesName": match_info.get("seriesName"),
                            "matchDesc": match_info.get("matchDesc"),
                            "matchFormat": match_info.get("matchFormat"),
                            "team1": match_info.get("team1", {}).get("teamName"),
                            "team2": match_info.get("team2", {}).get("teamName"),
                            "status": match_info.get("status"),
                            "state": match_info.get("state"),
                            "venue": match_info.get("venueInfo", {}).get("ground"),
                            "startDate": match_info.get("startDate")
                        })
        
        logger.info(f"Found {len(matches)} cricket matches (recent + live + upcoming)")
        return matches
    
    async def get_match_scorecard(self, match_id: int) -> Optional[Dict]:
        """
        Get detailed scorecard for a match
        
        Args:
            match_id: Cricbuzz match ID
        
        Returns:
            Match scorecard data
        """
        response = await self._make_request(f"mcenter/v1/{match_id}/scard")
        
        if not response:
            return None
        
        return response
    
    def get_requests_remaining(self) -> int:
        """Get remaining API requests for the day"""
        return max(0, self.daily_limit - self.request_count)
