"""
Pure function for determining auction completion status.
No side effects - just calculation based on current state.
"""

def compute_auction_status(league, participants, auction_state):
    """
    Deterministic function to calculate if auction should be complete.
    
    Args:
        league: League document with rules/config
        participants: List of participant documents
        auction_state: Dict with {
            "lots_sold": int,
            "current_lot": int,
            "total_lots": int,
            "unsold_count": int
        }
    
    Returns:
        Dict with completion status and reasoning
    """
    # Extract configuration
    required_slots = league.get("clubSlots", 3)
    
    # Filter to actual managers (exclude commissioner-only, spectators, etc.)
    # Participants with clubsWon array are active managers
    managers = [p for p in participants if "clubsWon" in p]
    
    # Count managers who have filled their rosters
    filled_managers = []
    unfilled_managers = []
    
    for p in managers:
        clubs_won = len(p.get("clubsWon", []))
        budget_remaining = p.get("budgetRemaining", 0)
        
        if clubs_won >= required_slots:
            filled_managers.append({
                "userId": p.get("userId", "unknown")[:8],
                "clubs_won": clubs_won,
                "budget": budget_remaining
            })
        else:
            unfilled_managers.append({
                "userId": p.get("userId", "unknown")[:8],
                "clubs_won": clubs_won,
                "needs": required_slots - clubs_won,
                "budget": budget_remaining
            })
    
    # Calculate if all managers have filled rosters
    all_filled = len(managers) > 0 and len(filled_managers) == len(managers)
    
    # Calculate remaining demand (total slots still needed)
    remaining_demand = sum(max(0, required_slots - len(p.get("clubsWon", []))) for p in managers)
    
    # Determine if auction should complete
    reasons = []
    should_complete = False
    
    if all_filled:
        should_complete = True
        reasons.append("ALL_ROSTERS_FILLED")
    
    if remaining_demand == 0 and len(managers) > 0:
        should_complete = True
        reasons.append("ZERO_DEMAND")
    
    if auction_state.get("current_lot", 0) >= auction_state.get("total_lots", 0):
        if auction_state.get("unsold_count", 0) == 0:
            should_complete = True
            reasons.append("ALL_LOTS_EXHAUSTED")
    
    if len(managers) == 0:
        should_complete = False
        reasons.append("NO_MANAGERS")
    
    # Build result
    return {
        "should_complete": should_complete,
        "reasons": reasons if reasons else ["CONTINUE"],
        "all_filled": all_filled,
        "filled_count": len(filled_managers),
        "unfilled_count": len(unfilled_managers),
        "manager_count": len(managers),
        "required_slots": required_slots,
        "remaining_demand": remaining_demand,
        "lots_sold": auction_state.get("lots_sold", 0),
        "current_lot": auction_state.get("current_lot", 0),
        "total_lots": auction_state.get("total_lots", 0),
        "unsold_count": auction_state.get("unsold_count", 0),
        "filled_managers": filled_managers,
        "unfilled_managers": unfilled_managers
    }
