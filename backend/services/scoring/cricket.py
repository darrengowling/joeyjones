"""
Cricket Points Calculator - Pure, reusable scoring function
"""

def get_cricket_points(line: dict, schema: dict) -> int:
    """
    Calculate cricket points for a player based on performance data and scoring schema.
    
    Args:
        line: Dictionary containing player performance data
            Expected keys: runs, wickets, catches, stumpings, runOuts
        schema: Dictionary containing scoring rules and milestones
            Expected structure: {"rules": {...}, "milestones": {...}}
    
    Returns:
        int: Total points calculated for the performance
    """
    rules = schema["rules"]
    ms = schema.get("milestones", {})
    
    runs = int(line.get("runs", 0))
    wkts = int(line.get("wickets", 0))
    
    pts = (
        rules["run"] * runs +
        rules["wicket"] * wkts +
        rules["catch"] * int(line.get("catches", 0)) +
        rules["stumping"] * int(line.get("stumpings", 0)) +
        rules["runOut"] * int(line.get("runOuts", 0))
    )
    
    if ms.get("halfCentury", {}).get("enabled") and runs >= ms["halfCentury"]["threshold"]:
        pts += ms["halfCentury"]["points"]
    
    if ms.get("century", {}).get("enabled") and runs >= ms["century"]["threshold"]:
        pts += ms["century"]["points"]
    
    if ms.get("fiveWicketHaul", {}).get("enabled") and wkts >= ms["fiveWicketHaul"]["threshold"]:
        pts += ms["fiveWicketHaul"]["points"]
    
    return int(pts)