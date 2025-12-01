"""
Football-Data.org API Client
Provides football fixtures, scores, and standings data
"""
import os
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FootballDataClient:
    """
    Client for Football-Data.org API
    Free tier: 10 requests/minute
    Covers: 12 major competitions including Premier League
    """
    
    def __init__(self):
        self.api_token = os.environ.get('FOOTBALL_DATA_TOKEN')
        if not self.api_token:
            logger.warning("FOOTBALL_DATA_TOKEN not configured")
        
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            "X-Auth-Token": self.api_token
        }
        
        self.request_count = 0
        self.rate_limit = 10  # 10 requests per minute (free tier)
        
        # Competition IDs
        self.competitions = {
            "PL": 2021,   # Premier League
            "CL": 2001,   # Champions League
            "BL1": 2002,  # Bundesliga
            "SA": 2019,   # Serie A
            "PD": 2014,   # La Liga
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Football-Data.org"""
        if not self.api_token:
            logger.error("FOOTBALL_DATA_TOKEN not configured - API calls will fail")
            return None
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params or {})
                self.request_count += 1
                
                logger.info(f"Football-Data.org request to {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.error("Rate limit exceeded (10 req/min)")
                    return None
                else:
                    logger.error(f"Football-Data.org error: {response.status_code} - {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.error(f"Football-Data.org request failed: {e}")
            return None
    
    async def get_matches_by_date(self, date_from: str, date_to: str = None, competition: str = "PL") -> List[Dict]:
        """
        Get matches for a date range
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD), defaults to same as date_from
            competition: Competition code (PL, CL, etc.)
        
        Returns:
            List of match dictionaries in standard format
        """
        competition_id = self.competitions.get(competition, 2021)
        
        params = {
            "dateFrom": date_from,
            "dateTo": date_to or date_from
        }
        
        endpoint = f"competitions/{competition_id}/matches"
        response = await self._make_request(endpoint, params)
        
        if not response:
            return []
        
        # Convert to standard format
        matches = []
        for match in response.get("matches", []):
            try:
                # Map status
                status_map = {
                    "FINISHED": "ft",
                    "IN_PLAY": "live",
                    "PAUSED": "ht",
                    "SCHEDULED": "ns",
                    "POSTPONED": "pst",
                    "CANCELLED": "canc",
                    "SUSPENDED": "susp"
                }
                
                standard_match = {
                    "fixture": {
                        "id": match["id"],
                        "date": match["utcDate"],
                        "status": {
                            "short": status_map.get(match["status"], "ns"),
                            "long": match["status"]
                        },
                        "venue": {
                            "name": match.get("venue", "")
                        }
                    },
                    "teams": {
                        "home": {
                            "id": match["homeTeam"]["id"],
                            "name": match["homeTeam"]["name"]
                        },
                        "away": {
                            "id": match["awayTeam"]["id"],
                            "name": match["awayTeam"]["name"]
                        }
                    },
                    "goals": {
                        "home": match["score"]["fullTime"]["home"],
                        "away": match["score"]["fullTime"]["away"]
                    },
                    "league": {
                        "id": competition_id,
                        "name": match["competition"]["name"]
                    }
                }
                matches.append(standard_match)
            except Exception as e:
                logger.error(f"Error parsing match: {e}")
                continue
        
        logger.info(f"Found {len(matches)} matches for {date_from} to {date_to}")
        return matches
    
    async def get_match_by_id(self, match_id: int) -> Optional[Dict]:
        """Get single match details by ID"""
        response = await self._make_request(f"matches/{match_id}")
        
        if not response:
            return None
        
        match = response
        
        status_map = {
            "FINISHED": "ft",
            "IN_PLAY": "live",
            "PAUSED": "ht",
            "SCHEDULED": "ns",
            "POSTPONED": "pst",
            "CANCELLED": "canc"
        }
        
        return {
            "fixture": {
                "id": match["id"],
                "date": match["utcDate"],
                "status": {
                    "short": status_map.get(match["status"], "ns")
                }
            },
            "teams": {
                "home": {
                    "id": match["homeTeam"]["id"],
                    "name": match["homeTeam"]["name"]
                },
                "away": {
                    "id": match["awayTeam"]["id"],
                    "name": match["awayTeam"]["name"]
                }
            },
            "goals": {
                "home": match["score"]["fullTime"]["home"],
                "away": match["score"]["fullTime"]["away"]
            }
        }
    
    async def get_team_matches(self, team_id: int, date_from: str = None, date_to: str = None) -> List[Dict]:
        """
        Get matches for a specific team
        
        Args:
            team_id: Football-Data.org team ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            List of matches
        """
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        
        response = await self._make_request(f"teams/{team_id}/matches", params)
        
        if not response:
            return []
        
        # Convert to standard format (same as get_matches_by_date)
        matches = []
        for match in response.get("matches", []):
            try:
                status_map = {
                    "FINISHED": "ft",
                    "IN_PLAY": "live",
                    "PAUSED": "ht",
                    "SCHEDULED": "ns",
                    "POSTPONED": "pst",
                    "CANCELLED": "canc"
                }
                
                standard_match = {
                    "fixture": {
                        "id": match["id"],
                        "date": match["utcDate"],
                        "status": {
                            "short": status_map.get(match["status"], "ns")
                        }
                    },
                    "teams": {
                        "home": {
                            "id": match["homeTeam"]["id"],
                            "name": match["homeTeam"]["name"]
                        },
                        "away": {
                            "id": match["awayTeam"]["id"],
                            "name": match["awayTeam"]["name"]
                        }
                    },
                    "goals": {
                        "home": match["score"]["fullTime"]["home"],
                        "away": match["score"]["fullTime"]["away"]
                    },
                    "league": {
                        "id": match["competition"]["id"],
                        "name": match["competition"]["name"]
                    }
                }
                matches.append(standard_match)
            except Exception as e:
                logger.error(f"Error parsing match: {e}")
                continue
        
        return matches
    
    def get_requests_remaining(self) -> int:
        """Get remaining API requests for current minute"""
        return max(0, self.rate_limit - self.request_count)
