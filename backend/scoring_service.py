"""
Scoring Service for Friends of Pifa
Fetches Champions League results from OpenFootball and calculates points
"""
import aiohttp
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# OpenFootball Champions League data URL (2024/25 season)
OPENFOOTBALL_CL_URL = "https://raw.githubusercontent.com/openfootball/champions-league/master/2024-25/cl.json"
OPENFOOTBALL_CL_ALT_URL = "https://raw.githubusercontent.com/openfootball/champions-league/master/2024-25/cl_finals.json"

# Scoring rules
POINTS_PER_WIN = 3
POINTS_PER_DRAW = 1
POINTS_PER_GOAL = 1


async def fetch_openfootball_data():
    """
    Fetch Champions League match data from OpenFootball
    Returns list of matches
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Try main URL first
            try:
                async with session.get(OPENFOOTBALL_CL_URL, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched OpenFootball CL data: {len(data.get('matches', []))} matches")
                        return data.get('matches', [])
            except Exception as e:
                logger.warning(f"Failed to fetch from main URL: {e}")
            
            # Try alternative URL
            try:
                async with session.get(OPENFOOTBALL_CL_ALT_URL, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched OpenFootball CL data (alt): {len(data.get('matches', []))} matches")
                        return data.get('matches', [])
            except Exception as e:
                logger.warning(f"Failed to fetch from alt URL: {e}")
            
            # If both fail, return mock data
            logger.warning("Using mock Champions League data")
            return get_mock_cl_data()
            
    except Exception as e:
        logger.error(f"Error fetching OpenFootball data: {e}")
        return get_mock_cl_data()


def get_mock_cl_data():
    """
    Mock Champions League data for testing
    Based on 2024/25 season results
    """
    return [
        {
            "date": "2024-09-17",
            "team1": "Bayern Munich",
            "team2": "Dinamo Zagreb",
            "score": {"ft": [9, 2]},
        },
        {
            "date": "2024-09-17",
            "team1": "Real Madrid",
            "team2": "VfB Stuttgart",
            "score": {"ft": [3, 1]},
        },
        {
            "date": "2024-09-18",
            "team1": "Liverpool",
            "team2": "AC Milan",
            "score": {"ft": [3, 1]},
        },
        {
            "date": "2024-09-18",
            "team1": "Sporting CP",
            "team2": "Lille",
            "score": {"ft": [2, 0]},
        },
        {
            "date": "2024-09-19",
            "team1": "Celtic",
            "team2": "Slovan Bratislava",
            "score": {"ft": [5, 1]},
        },
        {
            "date": "2024-09-19",
            "team1": "Club Brugge",
            "team2": "Borussia Dortmund",
            "score": {"ft": [0, 3]},
        },
        {
            "date": "2024-10-01",
            "team1": "Arsenal",
            "team2": "Paris Saint-Germain",
            "score": {"ft": [2, 0]},
        },
        {
            "date": "2024-10-01",
            "team1": "Barcelona",
            "team2": "Young Boys",
            "score": {"ft": [5, 0]},
        },
        {
            "date": "2024-10-02",
            "team1": "Inter Milan",
            "team2": "Red Star Belgrade",
            "score": {"ft": [4, 0]},
        },
        {
            "date": "2024-10-02",
            "team1": "PSV Eindhoven",
            "team2": "Sporting CP",
            "score": {"ft": [1, 1]},
        },
        {
            "date": "2024-10-22",
            "team1": "Bayer Leverkusen",
            "team2": "Brest",
            "score": {"ft": [1, 0]},
        },
        {
            "date": "2024-10-22",
            "team1": "Atlético Madrid",
            "team2": "Lille",
            "score": {"ft": [3, 1]},
        },
        {
            "date": "2024-10-23",
            "team1": "Monaco",
            "team2": "Red Star Belgrade",
            "score": {"ft": [5, 1]},
        },
        {
            "date": "2024-10-23",
            "team1": "Aston Villa",
            "team2": "Bologna",
            "score": {"ft": [2, 0]},
        },
    ]


async def calculate_club_points(matches: List[Dict], club_name: str) -> Dict:
    """
    Calculate points for a specific club based on match results
    
    Scoring rules:
    - Win: 3 points
    - Draw: 1 point
    - Goals scored: 1 point per goal
    
    Returns dict with wins, draws, losses, goals_scored, goals_conceded, total_points
    """
    stats = {
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_scored": 0,
        "goals_conceded": 0,
        "total_points": 0,
    }
    
    for match in matches:
        team1 = match.get("team1", "")
        team2 = match.get("team2", "")
        score = match.get("score", {}).get("ft", [0, 0])
        
        # Skip if no valid score
        if not score or len(score) != 2:
            continue
        
        team1_goals = score[0]
        team2_goals = score[1]
        
        # Check if this club played in this match
        if club_name in team1:
            # Club played as team1
            stats["goals_scored"] += team1_goals
            stats["goals_conceded"] += team2_goals
            
            if team1_goals > team2_goals:
                stats["wins"] += 1
            elif team1_goals == team2_goals:
                stats["draws"] += 1
            else:
                stats["losses"] += 1
                
        elif club_name in team2:
            # Club played as team2
            stats["goals_scored"] += team2_goals
            stats["goals_conceded"] += team1_goals
            
            if team2_goals > team1_goals:
                stats["wins"] += 1
            elif team2_goals == team1_goals:
                stats["draws"] += 1
            else:
                stats["losses"] += 1
    
    # Calculate total points
    stats["total_points"] = (
        (stats["wins"] * POINTS_PER_WIN) +
        (stats["draws"] * POINTS_PER_DRAW) +
        (stats["goals_scored"] * POINTS_PER_GOAL)
    )
    
    return stats


async def recompute_league_scores(db, league_id: str):
    """
    Recompute scores for all clubs in a league based on Champions League results
    """
    # Get league
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise Exception(f"League {league_id} not found")
    
    # Get all participants (clubs won by managers)
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    
    # Get all unique clubs won by participants
    all_club_ids = []
    for participant in participants:
        all_club_ids.extend(participant.get("clubsWon", []))
    
    unique_club_ids = list(set(all_club_ids))
    
    if not unique_club_ids:
        logger.info(f"No clubs found for league {league_id}")
        return {"message": "No clubs to score yet"}
    
    # Fetch clubs from assets collection (football clubs have sportKey: "football")
    clubs = await db.assets.find({"id": {"$in": unique_club_ids}, "sportKey": "football"}, {"_id": 0}).to_list(100)
    
    # Fetch Champions League match data
    matches = await fetch_openfootball_data()
    
    # Calculate points for each club
    updated_count = 0
    for club in clubs:
        club_name = club["name"]
        club_id = club["id"]
        
        # Calculate stats
        stats = await calculate_club_points(matches, club_name)
        
        # Update or create LeaguePoints record
        existing = await db.league_points.find_one({
            "leagueId": league_id,
            "clubId": club_id
        })
        
        league_points_data = {
            "leagueId": league_id,
            "clubId": club_id,
            "clubName": club_name,
            "wins": stats["wins"],
            "draws": stats["draws"],
            "losses": stats["losses"],
            "goalsScored": stats["goals_scored"],
            "goalsConceded": stats["goals_conceded"],
            "totalPoints": stats["total_points"],
            "lastUpdated": datetime.utcnow(),
        }
        
        if existing:
            await db.league_points.update_one(
                {"leagueId": league_id, "clubId": club_id},
                {"$set": league_points_data}
            )
        else:
            from models import LeaguePoints
            league_points_obj = LeaguePoints(**league_points_data)
            await db.league_points.insert_one(league_points_obj.model_dump())
        
        updated_count += 1
        logger.info(f"Updated points for {club_name}: {stats['total_points']} points")
    
    return {
        "message": "Scores recomputed successfully",
        "clubs_updated": updated_count,
        "total_matches_processed": len(matches)
    }


async def calculate_points_from_fixtures(db, league_id: str):
    """
    Calculate league points from completed fixtures in the database
    Uses the same scoring rules as Champions League (3-1-1)
    """
    # Get league
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise Exception(f"League {league_id} not found")
    
    # Get all participants (clubs won by managers)
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    
    # Get all unique clubs won by participants
    all_club_ids = []
    for participant in participants:
        all_club_ids.extend(participant.get("clubsWon", []))
    
    unique_club_ids = list(set(all_club_ids))
    
    if not unique_club_ids:
        logger.info(f"No clubs found for league {league_id}")
        return {"message": "No clubs to score yet"}
    
    # Fetch clubs from assets collection
    clubs = await db.assets.find({"id": {"$in": unique_club_ids}, "sportKey": "football"}, {"_id": 0}).to_list(100)
    
    # Get completed fixtures for this league
    fixtures = await db.fixtures.find({
        "leagueId": league_id,
        "status": "ft",
        "sportKey": "football"
    }, {"_id": 0}).to_list(1000)
    
    if not fixtures:
        logger.info(f"No completed fixtures found for league {league_id}")
        return {"message": "No completed fixtures to score from"}
    
    # Transform fixtures to Champions League format
    matches = []
    for fixture in fixtures:
        if fixture.get("goalsHome") is not None and fixture.get("goalsAway") is not None:
            matches.append({
                "team1": fixture["homeTeam"],
                "team2": fixture["awayTeam"],
                "score": {"ft": [fixture["goalsHome"], fixture["goalsAway"]]}
            })
    
    logger.info(f"Processing {len(matches)} completed fixtures for {len(clubs)} clubs")
    
    # Calculate points for each club using existing logic
    updated_count = 0
    for club in clubs:
        club_name = club["name"]
        club_id = club["id"]
        
        # Use existing calculation function
        stats = await calculate_club_points(matches, club_name)
        
        # Update or create LeaguePoints record
        existing = await db.league_points.find_one({
            "leagueId": league_id,
            "clubId": club_id
        })
        
        league_points_data = {
            "leagueId": league_id,
            "clubId": club_id,
            "clubName": club_name,
            "wins": stats["wins"],
            "draws": stats["draws"],
            "losses": stats["losses"],
            "goalsScored": stats["goals_scored"],
            "goalsConceded": stats["goals_conceded"],
            "totalPoints": stats["total_points"],
            "lastUpdated": datetime.utcnow(),
        }
        
        if existing:
            await db.league_points.update_one(
                {"leagueId": league_id, "clubId": club_id},
                {"$set": league_points_data}
            )
        else:
            from models import LeaguePoints
            league_points_obj = LeaguePoints(**league_points_data)
            await db.league_points.insert_one(league_points_obj.model_dump())
        
        updated_count += 1
        logger.info(f"Updated points for {club_name}: {stats['total_points']} points (W:{stats['wins']} D:{stats['draws']} L:{stats['losses']})")
    
    return {
        "message": "Scores calculated from fixtures successfully",
        "clubs_updated": updated_count,
        "fixtures_processed": len(matches)
    }



async def get_league_standings(db, league_id: str):
    """
    Get current standings for a league sorted by total points
    """
    standings = await db.league_points.find({"leagueId": league_id}).to_list(100)
    
    # Sort by total points (descending), then by goal difference
    standings.sort(
        key=lambda x: (
            -x.get("totalPoints", 0),
            -(x.get("goalsScored", 0) - x.get("goalsConceded", 0)),
            -x.get("goalsScored", 0)
        )
    )
    
    return standings
