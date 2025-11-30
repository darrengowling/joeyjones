"""
API-FOOTBALL Client for fetching live scores and fixture data
Based on integration playbook recommendations
"""
import httpx
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class APIFootballClient:
    """Client for API-FOOTBALL API integration"""
    
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY", "")
        self.base_url = "https://v3.football.api-sports.io"
        self.request_count = 0
        self.daily_limit = 100  # Free tier limit
        
        if not self.api_key:
            logger.warning("API_FOOTBALL_KEY not configured - API calls will fail")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        if self.request_count >= self.daily_limit:
            logger.warning(f"Daily rate limit reached: {self.request_count}/{self.daily_limit}")
            return False
        return True
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to API-FOOTBALL"""
        if not self.api_key:
            logger.error("API_FOOTBALL_KEY not configured")
            return None
        
        if not self._check_rate_limit():
            logger.error("Rate limit exceeded")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"API-FOOTBALL request: {endpoint} with params {params}")
                response = await client.get(url, headers=self._get_headers(), params=params)
                self.request_count += 1
                
                if response.status_code == 429:
                    logger.warning("Rate limited by API (429)")
                    return None
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"API-FOOTBALL response received: {len(data.get('response', []))} results")
                return data
        
        except httpx.HTTPError as e:
            logger.error(f"API-FOOTBALL request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            return None
    
    async def get_fixture_by_ids(self, fixture_ids: List[int]) -> List[Dict]:
        """
        Fetch fixture data for multiple fixtures by their API-FOOTBALL IDs
        This is efficient for batch updates
        """
        if not fixture_ids:
            return []
        
        # API-FOOTBALL allows fetching specific fixtures by ID
        # We can batch multiple IDs in one request
        results = []
        
        # Process in batches of 20 to avoid URL length issues
        for i in range(0, len(fixture_ids), 20):
            batch = fixture_ids[i:i+20]
            params = {"ids": "-".join(map(str, batch))}
            
            response = await self._make_request("fixtures", params)
            if response and response.get("response"):
                results.extend(response["response"])
        
        return results
    
    async def get_fixtures_by_date(self, date: str, league_id: int = 39) -> List[Dict]:
        """
        Fetch all fixtures for a specific date and league
        Date format: YYYY-MM-DD
        League ID 39 = English Premier League
        
        Note: Free tier doesn't support league+season filters for current season.
        We fetch all fixtures for the date and filter client-side.
        """
        params = {
            "date": date
        }
        
        response = await self._make_request("fixtures", params)
        all_fixtures = response.get("response", []) if response else []
        
        # Filter for requested league in Python
        filtered = [f for f in all_fixtures if f.get("league", {}).get("id") == league_id]
        
        logger.info(f"Filtered {len(filtered)} fixtures for league {league_id} from {len(all_fixtures)} total")
        
        return filtered
    
    async def get_live_fixtures(self, league_id: int = 39) -> List[Dict]:
        """
        Fetch currently live fixtures for a league
        """
        params = {
            "league": league_id,
            "live": "all"
        }
        
        response = await self._make_request("fixtures", params)
        return response.get("response", []) if response else []
    
    def get_requests_remaining(self) -> int:
        """Get remaining API requests for today"""
        return max(0, self.daily_limit - self.request_count)
    
    def reset_request_count(self):
        """Reset request counter (should be called daily)"""
        self.request_count = 0
        logger.info("API request counter reset")


async def update_fixtures_from_api(db, fixture_ids: List[str] = None):
    """
    Update fixtures in database with latest data from API-FOOTBALL
    If fixture_ids provided, update only those fixtures
    Otherwise, update all fixtures for Nov 29-30, 2025
    """
    client = APIFootballClient()
    
    # Get fixtures from database that need updating
    query = {"sportKey": "football"}
    if fixture_ids:
        query["id"] = {"$in": fixture_ids}
    else:
        # Get fixtures for Nov 29-30, 2025
        query["matchDate"] = {
            "$gte": "2025-11-29T00:00:00Z",
            "$lte": "2025-11-30T23:59:59Z"
        }
    
    fixtures = await db.fixtures.find(query).to_list(length=None)
    
    if not fixtures:
        logger.info("No fixtures found to update")
        return {"updated": 0, "errors": []}
    
    logger.info(f"Found {len(fixtures)} fixtures to update")
    
    # Group by date for efficient API calls
    dates = set()
    for fixture in fixtures:
        match_date = fixture.get("matchDate", "")
        if match_date:
            dates.add(match_date[:10])  # Extract YYYY-MM-DD
    
    updated_count = 0
    errors = []
    
    # Fetch data for each date
    for date in dates:
        api_fixtures = await client.get_fixtures_by_date(date)
        
        if not api_fixtures:
            logger.warning(f"No API data returned for {date}")
            continue
        
        # Create lookup by team external IDs
        api_lookup = {}
        for api_fixture in api_fixtures:
            home_id = str(api_fixture["teams"]["home"]["id"])
            away_id = str(api_fixture["teams"]["away"]["id"])
            key = f"{home_id}-{away_id}"
            api_lookup[key] = api_fixture
        
        # Update each fixture
        for fixture in fixtures:
            fixture_date = fixture.get("matchDate", "")[:10]
            if fixture_date != date:
                continue
            
            home_ext_id = fixture.get("homeExternalId")
            away_ext_id = fixture.get("awayExternalId")
            
            if not home_ext_id or not away_ext_id:
                logger.warning(f"Fixture {fixture['id']} missing external IDs")
                continue
            
            key = f"{home_ext_id}-{away_ext_id}"
            api_data = api_lookup.get(key)
            
            if not api_data:
                logger.warning(f"No API data for {fixture['homeTeam']} vs {fixture['awayTeam']}")
                continue
            
            # Extract score data
            goals = api_data.get("goals", {})
            status = api_data["fixture"]["status"]["short"]
            
            update_data = {
                "goalsHome": goals.get("home"),
                "goalsAway": goals.get("away"),
                "status": status.lower(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            # Determine winner
            if status in ["FT", "AET", "PEN"] and goals.get("home") is not None and goals.get("away") is not None:
                if goals["home"] > goals["away"]:
                    update_data["winner"] = fixture["homeTeam"]
                elif goals["away"] > goals["home"]:
                    update_data["winner"] = fixture["awayTeam"]
                else:
                    update_data["winner"] = "draw"
            
            # Update in database
            result = await db.fixtures.update_one(
                {"id": fixture["id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                logger.info(f"✓ Updated: {fixture['homeTeam']} {update_data.get('goalsHome', '-')} - {update_data.get('goalsAway', '-')} {fixture['awayTeam']}")
            else:
                logger.debug(f"No changes for {fixture['homeTeam']} vs {fixture['awayTeam']}")
    
    logger.info(f"Update complete: {updated_count} fixtures updated")
    logger.info(f"API requests remaining: {client.get_requests_remaining()}")
    
    return {
        "updated": updated_count,
        "errors": errors,
        "requests_remaining": client.get_requests_remaining()
    }
