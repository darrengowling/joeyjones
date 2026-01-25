#!/usr/bin/env python3
"""
Seed IPL 2026 Players from Cricbuzz API
"""

import httpx
import uuid
import json
from typing import List, Dict

RAPIDAPI_KEY = "62431ad8damshcc26bf0bb67d862p12ab40jsn9710a0c8967c"
IPL_2026_SERIES_ID = 9241

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}

# IPL Team IDs from API
IPL_TEAMS = {
    99705: "Chennai Super Kings",
    99716: "Delhi Capitals", 
    99727: "Gujarat Titans",
    99738: "Royal Challengers Bengaluru",
    99749: "Punjab Kings",
    99760: "Kolkata Knight Riders",
    99771: "Sunrisers Hyderabad",
    99782: "Rajasthan Royals",
    99793: "Lucknow Super Giants",
    99804: "Mumbai Indians"
}


def fetch_squad(squad_id: int) -> List[Dict]:
    """Fetch squad from Cricbuzz API"""
    response = httpx.get(
        f"https://cricbuzz-cricket.p.rapidapi.com/series/v1/{IPL_2026_SERIES_ID}/squads/{squad_id}",
        headers=HEADERS,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"  Error fetching squad {squad_id}: {response.status_code}")
        return []
    
    data = response.json()
    return data.get("player", [])


def create_asset(player: Dict, team_name: str) -> Dict:
    """Convert Cricbuzz player to our asset format"""
    return {
        "id": str(uuid.uuid4()),
        "sportKey": "cricket",
        "externalId": str(player.get("id")),
        "name": player.get("name"),
        "type": "player",
        "meta": {
            "role": player.get("role", "Unknown"),
            "franchise": team_name,    # For IPL team filtering
            "iplTeam": team_name       # Keep for backwards compat
        },
        "competitions": ["IPL 2026"],
        "competitionShort": "IPL"
    }


def fetch_all_ipl_players() -> List[Dict]:
    """Fetch all IPL 2026 players from all teams"""
    all_players = []
    
    for squad_id, team_name in IPL_TEAMS.items():
        print(f"Fetching {team_name}...")
        
        squad = fetch_squad(squad_id)
        team_players = []
        
        for player in squad:
            # Skip header rows (e.g., "BATTERS", "ALL ROUNDERS")
            if player.get("isHeader"):
                continue
            
            # Skip if no player ID
            if not player.get("id"):
                continue
                
            asset = create_asset(player, team_name)
            team_players.append(asset)
        
        print(f"  Found {len(team_players)} players")
        all_players.extend(team_players)
    
    return all_players


if __name__ == "__main__":
    print("=== IPL 2026 Player Seed Script ===\n")
    
    players = fetch_all_ipl_players()
    
    print(f"\n=== Summary ===")
    print(f"Total players: {len(players)}")
    
    # Group by team
    by_team = {}
    for p in players:
        team = p["meta"]["iplTeam"]
        by_team[team] = by_team.get(team, 0) + 1
    
    print("\nPlayers per team:")
    for team, count in sorted(by_team.items()):
        print(f"  {team}: {count}")
    
    # Save to file for review
    with open("/app/scripts/ipl_2026_players.json", "w") as f:
        json.dump(players, f, indent=2)
    
    print(f"\nSaved to /app/scripts/ipl_2026_players.json")
    print("\nSample player:")
    print(json.dumps(players[0], indent=2))
