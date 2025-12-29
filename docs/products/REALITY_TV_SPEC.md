# Reality TV Technical Specification

**Created:** December 28, 2025  
**Purpose:** Technical specification for extending the platform to support Reality TV and entertainment competitions  
**Status:** PLANNING

---

## Executive Summary

This specification outlines the technical changes required to support Reality TV shows and entertainment competitions as a new "sport" type on the platform. The auction engine and core mechanics remain unchanged - we extend the data model, scoring system, and UI to accommodate elimination-based entertainment formats.

### Key Differences from Sports

| Aspect | Sports (Football/Cricket) | Reality TV |
|--------|---------------------------|------------|
| **Assets** | Clubs or Players | Contestants |
| **Events** | Matches with scores | Episodes with outcomes |
| **Scoring** | Goals, runs, wickets | Survival, wins, eliminations |
| **Data Source** | Live APIs | Manual entry (no API) |
| **Duration** | Season (months) | Show run (weeks) |
| **Frequency** | Multiple matches/week | 1-2 episodes/week |

---

## Supported Show Types

### Tier 1: Elimination Shows (Primary Target)

| Show Type | Example Shows | Assets | Events | Scoring Model |
|-----------|---------------|--------|--------|---------------|
| **Survival** | Survivor, I'm a Celebrity | Contestants | Episodes, Tribal Council | Survival + Challenge wins |
| **Competition** | Bake Off, MasterChef | Contestants | Episodes, Challenges | Star Baker, Technical wins |
| **Talent** | X Factor, The Voice | Acts/Contestants | Live shows | Survival + Public vote % |

### Tier 2: Voting/Ranking Shows

| Show Type | Example Shows | Assets | Events | Scoring Model |
|-----------|---------------|--------|--------|---------------|
| **Eurovision** | Eurovision Song Contest | Countries | Semi-finals, Final | Points from jury + public |
| **Awards** | BAFTAs, Oscars | Films/Nominees | Ceremony | Nominations + Wins |
| **Reality Dating** | Love Island | Couples | Episodes | Survival, coupling, final |

---

## Data Model Extensions

### New Sport Configuration

```javascript
// Add to sports collection
{
  "key": "reality_tv",
  "name": "Reality TV",
  "description": "Auction-based competitions for reality TV shows",
  "active": true,
  "assetType": "CONTESTANT",
  "scoringSchema": {
    "type": "elimination",
    "rules": {
      "survives_episode": 5,
      "wins_challenge": 10,
      "wins_immunity": 15,
      "makes_merge": 20,
      "makes_final": 50,
      "wins_show": 100,
      "fan_favorite": 25
    },
    "negative": {
      "eliminated": 0,
      "quit": -10
    }
  },
  "auctionTemplate": {
    "bidTimerSeconds": 30,
    "antiSnipeSeconds": 10,
    "minIncrement": 1
  },
  "uiHints": {
    "assetLabel": "Contestant",
    "assetPlural": "Contestants",
    "currencySymbol": "⭐",
    "currencyName": "Stars",
    "budgetLabel": "Star Power",
    "eventLabel": "Episode",
    "eventPlural": "Episodes"
  }
}
```

### Extended Asset Model

```python
# models.py - Extended Asset for Reality TV

class ContestantMeta(BaseModel):
    """Metadata specific to Reality TV contestants"""
    age: Optional[int] = None
    occupation: Optional[str] = None
    hometown: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None  # {"instagram": "@handle", "twitter": "@handle"}
    tribe: Optional[str] = None  # For Survivor-style shows
    team: Optional[str] = None   # For team-based shows
    status: str = "active"       # active, eliminated, quit, winner

class Asset(BaseModel):
    """Extended asset model supporting contestants"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    sportKey: str              # "reality_tv"
    assetType: str             # "CONTESTANT"
    externalId: Optional[str] = None
    country: Optional[str] = None
    competitions: List[str] = []  # ["Survivor 47", "I'm a Celebrity 2025"]
    competitionShort: Optional[str] = None  # "SURVIVOR47"
    meta: Optional[Dict[str, Any]] = None   # ContestantMeta as dict
    
    # Reality TV specific
    showName: Optional[str] = None      # "Survivor"
    seasonNumber: Optional[int] = None  # 47
    seasonName: Optional[str] = None    # "Survivor 47: Heroes vs Villains"
    originalTribe: Optional[str] = None # Starting tribe/team
    currentStatus: str = "active"       # active, eliminated, quit, winner
    eliminationEpisode: Optional[int] = None
    finalPlacement: Optional[int] = None  # 1 = winner, 2 = runner-up, etc.
```

### Extended Fixture/Event Model

```python
# models.py - Extended for Episodes/Events

class EpisodeResult(BaseModel):
    """Results for a single contestant in an episode"""
    contestantId: str
    survived: bool = True
    eliminated: bool = False
    quit: bool = False
    wonChallenge: bool = False
    wonImmunity: bool = False
    receivedVotes: int = 0       # Votes to eliminate (Survivor)
    publicVotePercent: Optional[float] = None  # For voting shows
    judgeScore: Optional[float] = None   # For scored shows (Bake Off)
    isStarBaker: bool = False    # Bake Off specific
    wonTechnical: bool = False   # Bake Off specific
    notes: Optional[str] = None

class Fixture(BaseModel):
    """Extended fixture model for episodes"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    leagueId: str
    externalMatchId: Optional[str] = None  # "SURVIVOR47_EP01"
    
    # Standard fields (sports compatibility)
    homeTeam: Optional[str] = None
    awayTeam: Optional[str] = None
    homeAssetExternalId: Optional[str] = None
    awayAssetExternalId: Optional[str] = None
    goalsHome: Optional[int] = None
    goalsAway: Optional[int] = None
    winner: Optional[str] = None  # "home"|"away"|"draw"
    
    # Reality TV specific
    episodeNumber: Optional[int] = None
    episodeTitle: Optional[str] = None
    airDate: Optional[datetime] = None
    eventType: str = "episode"    # episode, finale, reunion, special
    
    # Episode results
    results: List[EpisodeResult] = []
    eliminatedContestants: List[str] = []  # Contestant IDs eliminated this episode
    challengeWinners: List[str] = []       # Contestant IDs who won challenges
    immunityWinners: List[str] = []        # Contestant IDs with immunity
    
    # Metadata
    status: str = "scheduled"     # scheduled, aired, ft (completed)
    startsAt: Optional[datetime] = None
    venue: Optional[str] = None   # Location/set
    round: Optional[str] = None   # "Episode 1", "Finale", etc.
```

---

## Scoring Service Extension

### New Scoring Type: "elimination"

```python
# scoring_service.py - Add elimination scoring

async def calculate_elimination_scores(
    league_id: str,
    episode: Fixture,
    db: AsyncIOMotorDatabase
) -> Dict[str, float]:
    """
    Calculate points for elimination-based shows
    
    Scoring rules:
    - survives_episode: Points for surviving an episode
    - wins_challenge: Points for winning a challenge
    - wins_immunity: Points for winning immunity
    - makes_merge: Bonus for reaching merge (Survivor)
    - makes_final: Bonus for reaching finale
    - wins_show: Bonus for winning the show
    - eliminated: Points when eliminated (usually 0)
    """
    
    # Get league and sport config
    league = await db.leagues.find_one({"id": league_id})
    sport = await db.sports.find_one({"key": league.get("sportKey")})
    scoring_rules = sport.get("scoringSchema", {}).get("rules", {})
    
    # Get all participants with their owned contestants
    participants = await db.league_participants.find({"leagueId": league_id}).to_list(100)
    
    points_by_user = {}
    
    for participant in participants:
        user_id = participant.get("userId")
        owned_contestants = participant.get("clubsWon", [])  # Asset IDs
        user_points = 0
        
        for contestant_id in owned_contestants:
            # Find this contestant's result in the episode
            result = next(
                (r for r in episode.results if r.contestantId == contestant_id),
                None
            )
            
            if not result:
                continue
            
            # Calculate points
            if result.survived:
                user_points += scoring_rules.get("survives_episode", 5)
            
            if result.wonChallenge:
                user_points += scoring_rules.get("wins_challenge", 10)
            
            if result.wonImmunity:
                user_points += scoring_rules.get("wins_immunity", 15)
            
            if result.eliminated:
                user_points += scoring_rules.get("eliminated", 0)
            
            if result.quit:
                user_points += scoring_rules.get("quit", -10)
            
            # Show-specific bonuses (check contestant status)
            contestant = await db.assets.find_one({"id": contestant_id})
            if contestant:
                status = contestant.get("currentStatus")
                if status == "winner":
                    user_points += scoring_rules.get("wins_show", 100)
                elif contestant.get("finalPlacement") and contestant.get("finalPlacement") <= 3:
                    user_points += scoring_rules.get("makes_final", 50)
        
        points_by_user[user_id] = user_points
    
    return points_by_user


async def update_contestant_status(
    contestant_id: str,
    episode_number: int,
    status: str,
    final_placement: Optional[int],
    db: AsyncIOMotorDatabase
):
    """
    Update contestant status after an episode
    
    Args:
        contestant_id: Asset ID
        episode_number: Episode where status changed
        status: "active", "eliminated", "quit", "winner"
        final_placement: Final placement (1 = winner)
    """
    update = {
        "currentStatus": status,
        "updatedAt": datetime.now(timezone.utc)
    }
    
    if status == "eliminated":
        update["eliminationEpisode"] = episode_number
    
    if final_placement:
        update["finalPlacement"] = final_placement
    
    await db.assets.update_one(
        {"id": contestant_id},
        {"$set": update}
    )
```

### Scoring Configuration by Show Type

```javascript
// Survivor-style scoring
{
  "type": "elimination",
  "rules": {
    "survives_episode": 5,
    "wins_immunity": 20,
    "wins_reward": 10,
    "finds_idol": 15,
    "plays_idol": 10,
    "makes_merge": 25,
    "makes_final_3": 50,
    "wins_firemaking": 20,
    "wins_show": 100,
    "fan_favorite": 25
  },
  "negative": {
    "eliminated": 0,
    "quit": -20,
    "medevac": 0
  }
}

// Bake Off-style scoring
{
  "type": "elimination",
  "rules": {
    "survives_episode": 5,
    "star_baker": 20,
    "wins_technical": 15,
    "technical_top_3": 5,
    "makes_final": 50,
    "wins_show": 100
  },
  "negative": {
    "eliminated": 0
  }
}

// Eurovision-style scoring
{
  "type": "voting",
  "rules": {
    "qualifies_semi": 20,
    "points_final": 0.5,      // 0.5 points per Eurovision point received
    "top_10": 30,
    "top_5": 50,
    "wins_show": 100
  }
}

// Awards show scoring (BAFTAs, Oscars)
{
  "type": "nomination",
  "rules": {
    "nomination": 10,          // Per nomination
    "wins_category": 50,       // Per win
    "wins_major": 75,          // Best Picture, Best Actor/Actress
    "clean_sweep": 100         // Wins all nominated categories
  }
}
```

---

## API Endpoints

### New Endpoints Required

```python
# server.py - Reality TV specific endpoints

# ===== EPISODE MANAGEMENT =====

@api_router.post("/leagues/{league_id}/episodes")
async def create_episode(league_id: str, episode: EpisodeCreate):
    """Create a new episode for a Reality TV league"""
    pass

@api_router.put("/leagues/{league_id}/episodes/{episode_id}/results")
async def update_episode_results(
    league_id: str, 
    episode_id: str, 
    results: List[EpisodeResult]
):
    """
    Update results for an episode
    - Mark contestants as survived/eliminated
    - Record challenge/immunity wins
    - Trigger score recalculation
    """
    pass

@api_router.post("/leagues/{league_id}/episodes/{episode_id}/eliminate")
async def eliminate_contestant(
    league_id: str,
    episode_id: str,
    contestant_id: str,
    reason: str = "voted_out"  # voted_out, quit, medevac
):
    """Mark a contestant as eliminated"""
    pass

# ===== CONTESTANT MANAGEMENT =====

@api_router.get("/leagues/{league_id}/contestants")
async def get_league_contestants(league_id: str, status: str = None):
    """
    Get all contestants for a league
    - Filter by status: active, eliminated, all
    """
    pass

@api_router.put("/contestants/{contestant_id}/status")
async def update_contestant_status(
    contestant_id: str,
    status: str,
    episode_number: int = None,
    final_placement: int = None
):
    """Update a contestant's status"""
    pass

# ===== SHOW TEMPLATES =====

@api_router.get("/reality-tv/templates")
async def get_show_templates():
    """Get pre-configured show templates (Survivor, Bake Off, etc.)"""
    pass

@api_router.post("/reality-tv/shows")
async def create_show(show: ShowCreate):
    """Create a new show with contestants"""
    pass
```

---

## Frontend Changes

### New Components Required

```
/app/frontend/src/
├── components/
│   ├── reality-tv/
│   │   ├── ContestantCard.js       # Display contestant info
│   │   ├── ContestantGrid.js       # Grid of contestants
│   │   ├── EpisodeResultsForm.js   # Enter episode results
│   │   ├── EliminationTracker.js   # Visual elimination order
│   │   ├── ScoringBreakdown.js     # Show points calculation
│   │   └── ShowSelector.js         # Select show type
│   └── ...
├── pages/
│   ├── RealityTVDashboard.js       # Commissioner view for Reality TV
│   └── ...
```

### UI Modifications

#### AuctionRoom.js Changes

```javascript
// Conditional rendering for Reality TV assets
{sport?.key === "reality_tv" && currentClub && (
  <div className="text-center">
    {/* Contestant photo */}
    {currentClub.meta?.photo_url && (
      <img 
        src={currentClub.meta.photo_url} 
        alt={currentClub.name}
        className="w-32 h-32 rounded-full mx-auto mb-4 object-cover"
      />
    )}
    
    {/* Contestant name */}
    <h2 className="text-2xl font-bold">{currentClub.name}</h2>
    
    {/* Contestant details */}
    {currentClub.meta?.occupation && (
      <p className="text-gray-600">{currentClub.meta.occupation}</p>
    )}
    {currentClub.meta?.hometown && (
      <p className="text-gray-500">{currentClub.meta.hometown}</p>
    )}
    {currentClub.meta?.tribe && (
      <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm mt-2">
        {currentClub.meta.tribe}
      </span>
    )}
    
    {/* Status badge */}
    {currentClub.currentStatus === "eliminated" && (
      <span className="inline-block px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm mt-2">
        Eliminated (Episode {currentClub.eliminationEpisode})
      </span>
    )}
  </div>
)}
```

#### Episode Results Entry UI

```javascript
// EpisodeResultsForm.js
const EpisodeResultsForm = ({ episode, contestants, onSave }) => {
  const [results, setResults] = useState(
    contestants.map(c => ({
      contestantId: c.id,
      survived: true,
      eliminated: false,
      wonChallenge: false,
      wonImmunity: false
    }))
  );

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold">Episode {episode.episodeNumber} Results</h3>
      
      {contestants.filter(c => c.currentStatus === "active").map(contestant => (
        <div key={contestant.id} className="p-4 border rounded-lg">
          <div className="flex items-center gap-4">
            <img 
              src={contestant.meta?.photo_url} 
              className="w-12 h-12 rounded-full"
            />
            <div className="flex-1">
              <p className="font-medium">{contestant.name}</p>
              <p className="text-sm text-gray-500">{contestant.meta?.tribe}</p>
            </div>
            
            <div className="flex gap-2">
              <label className="flex items-center gap-1">
                <input 
                  type="checkbox"
                  checked={results.find(r => r.contestantId === contestant.id)?.wonImmunity}
                  onChange={(e) => updateResult(contestant.id, 'wonImmunity', e.target.checked)}
                />
                🛡️ Immunity
              </label>
              
              <label className="flex items-center gap-1">
                <input 
                  type="checkbox"
                  checked={results.find(r => r.contestantId === contestant.id)?.wonChallenge}
                  onChange={(e) => updateResult(contestant.id, 'wonChallenge', e.target.checked)}
                />
                🏆 Challenge
              </label>
              
              <label className="flex items-center gap-1 text-red-600">
                <input 
                  type="checkbox"
                  checked={results.find(r => r.contestantId === contestant.id)?.eliminated}
                  onChange={(e) => updateResult(contestant.id, 'eliminated', e.target.checked)}
                />
                ❌ Eliminated
              </label>
            </div>
          </div>
        </div>
      ))}
      
      <button 
        onClick={() => onSave(results)}
        className="w-full py-3 bg-purple-600 text-white rounded-lg"
      >
        Save Episode Results
      </button>
    </div>
  );
};
```

---

## Data Entry Workflow

Since Reality TV has no automated API, results must be entered manually.

### Commissioner Workflow

```
1. BEFORE SHOW AIRS
   └── Create league with show (e.g., "Survivor 47")
   └── Contestants auto-seeded from template OR manually added
   └── Run auction - users bid on contestants

2. AFTER EACH EPISODE AIRS
   └── Commissioner opens Episode Results form
   └── Marks: who survived, who won challenges, who was eliminated
   └── Saves results → Points auto-calculated
   └── Standings update immediately

3. AFTER FINALE
   └── Mark winner and runner-ups
   └── Final bonuses applied
   └── League completes
```

### Episode Result Entry Time

| Scenario | Recommended Entry Time |
|----------|----------------------|
| US Shows (Survivor, etc.) | Within 2 hours of East Coast airing |
| UK Shows (Bake Off, etc.) | Within 1 hour of airing |
| Live Events (Eurovision) | Real-time during show |
| Awards (BAFTAs, Oscars) | Real-time during ceremony |

---

## Sample Data: Survivor Configuration

### Show Template

```javascript
{
  "showKey": "survivor",
  "showName": "Survivor",
  "network": "CBS",
  "country": "US",
  "assetType": "CONTESTANT",
  "typicalContestants": 18,
  "typicalEpisodes": 13,
  "scoringPreset": "survivor_standard",
  "defaultBudget": 100,
  "uiTheme": {
    "primaryColor": "#8B4513",
    "secondaryColor": "#228B22",
    "icon": "🏝️"
  }
}
```

### Sample Contestants (Survivor 47)

```javascript
[
  {
    "name": "Sam Phalen",
    "externalId": "SURVIVOR47_01",
    "competitionShort": "SURVIVOR47",
    "meta": {
      "age": 28,
      "occupation": "Sports Reporter",
      "hometown": "Nashville, TN",
      "tribe": "Gata",
      "photo_url": "https://..."
    },
    "currentStatus": "active"
  },
  {
    "name": "Rachel LaMont",
    "externalId": "SURVIVOR47_02",
    "competitionShort": "SURVIVOR47",
    "meta": {
      "age": 34,
      "occupation": "Graphic Designer",
      "hometown": "Southfield, MI",
      "tribe": "Lavo",
      "photo_url": "https://..."
    },
    "currentStatus": "active"
  }
  // ... more contestants
]
```

### Sample Episode

```javascript
{
  "episodeNumber": 1,
  "episodeTitle": "The Marooning",
  "airDate": "2025-09-18T20:00:00Z",
  "eventType": "episode",
  "status": "ft",
  "results": [
    {
      "contestantId": "uuid-sam",
      "survived": true,
      "wonChallenge": false,
      "wonImmunity": false
    },
    {
      "contestantId": "uuid-rachel",
      "survived": true,
      "wonChallenge": true,
      "wonImmunity": false
    },
    {
      "contestantId": "uuid-eliminated",
      "survived": false,
      "eliminated": true,
      "receivedVotes": 5
    }
  ],
  "eliminatedContestants": ["uuid-eliminated"],
  "challengeWinners": ["uuid-rachel"]
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (2 weeks)

| Task | Effort | Priority |
|------|--------|----------|
| Add `reality_tv` sport config | 2 hours | High |
| Extend Asset model for contestants | 4 hours | High |
| Extend Fixture model for episodes | 4 hours | High |
| Create elimination scoring service | 8 hours | High |
| Basic episode results API | 8 hours | High |
| **Total Phase 1** | **~26 hours** | |

### Phase 2: Frontend (1.5 weeks)

| Task | Effort | Priority |
|------|--------|----------|
| ContestantCard component | 4 hours | High |
| Episode results entry form | 8 hours | High |
| Elimination tracker visualization | 6 hours | Medium |
| Auction room contestant display | 4 hours | High |
| Standings with elimination status | 4 hours | High |
| **Total Phase 2** | **~26 hours** | |

### Phase 3: Show Templates & Polish (1 week)

| Task | Effort | Priority |
|------|--------|----------|
| Survivor template + sample data | 4 hours | High |
| Bake Off template | 2 hours | Medium |
| Eurovision template | 2 hours | Medium |
| Commissioner guide/documentation | 4 hours | Medium |
| Testing full flow | 8 hours | High |
| **Total Phase 3** | **~20 hours** | |

### Total Estimated Effort

| Phase | Hours | Duration |
|-------|-------|----------|
| Phase 1: Core | 26 hours | 2 weeks |
| Phase 2: Frontend | 26 hours | 1.5 weeks |
| Phase 3: Templates | 20 hours | 1 week |
| **Total** | **~72 hours** | **~4.5 weeks** |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Manual data entry burden | High | Medium | Pre-built show templates, easy entry UI |
| Spoiler timing issues | Medium | Low | Allow delayed entry, timezone handling |
| IP/licensing concerns | Medium | High | User-generated leagues (like fantasy sports) |
| Scoring complexity varies by show | Medium | Medium | Configurable scoring schemas |
| Low user engagement between episodes | Medium | Medium | Notifications, weekly recaps |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Time to create a new show league | < 5 minutes |
| Time to enter episode results | < 3 minutes |
| Scoring accuracy | 100% (manual entry) |
| User satisfaction with contestant display | > 4/5 stars |
| Commissioner satisfaction with entry UI | > 4/5 stars |

---

## Future Enhancements

### Post-MVP Features

| Feature | Description | Effort |
|---------|-------------|--------|
| Prediction markets | Bet on who gets eliminated | High |
| Social integrations | Share picks on Twitter/Instagram | Medium |
| Live episode chat | Real-time discussion during airing | High |
| Automated spoiler detection | Scrape social media for results | High |
| Multi-language support | For international shows | Medium |
| Mobile push notifications | Episode reminders, results | Medium |

### API Integrations (If Available)

| Show | Potential Data Source |
|------|----------------------|
| Survivor | CBS API (if available) |
| Eurovision | Eurovision API (official) |
| UK Shows | BBC/ITV APIs (limited) |
| US Shows | Network APIs (limited) |

---

## Appendix: Database Schema Summary

### Collections

| Collection | Purpose | New/Modified |
|------------|---------|--------------|
| `sports` | Sport configurations | Modified (add reality_tv) |
| `assets` | Contestants | Modified (add fields) |
| `fixtures` | Episodes | Modified (add fields) |
| `leagues` | Leagues/Competitions | No change |
| `league_participants` | User participation | No change |
| `league_points` | Points per contestant | Modified (for episodes) |
| `show_templates` | Pre-built show configs | **New** |

### Indexes Required

```javascript
// New indexes for Reality TV queries
db.assets.createIndex({ "sportKey": 1, "competitionShort": 1, "currentStatus": 1 })
db.fixtures.createIndex({ "leagueId": 1, "episodeNumber": 1 })
db.fixtures.createIndex({ "leagueId": 1, "airDate": 1 })
```

---

**Document Version:** 1.0  
**Last Updated:** December 28, 2025  
**Status:** TECHNICAL SPECIFICATION
