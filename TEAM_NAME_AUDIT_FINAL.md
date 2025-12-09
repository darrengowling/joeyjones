# Team Name Audit - Final Report
**Date:** December 9, 2025  
**Database:** test_database (verified)  
**Audit Method:** Dual-run verification against Football-Data.org API

---

## Executive Summary

**Current State:**
- **Champions League:** 14/36 teams exact match, 22/36 fuzzy only
- **Premier League:** 2/20 teams exact match, 16/20 fuzzy only, 2/20 missing

**Impact:**
- **Fixture Import:** Works for 54/56 teams (fuzzy matching)
- **Score Calculation:** Works for 16/56 teams (exact matching required)
- **Result:** Scoring is broken for 40 teams

---

## The Three ID Requirements

### 1. External ID (externalId)
- **Purpose:** Links our database team to Football-Data.org API team
- **Used By:** Fixture import, score updates
- **Status:** ✅ ALL CORRECT (verified via dual audit)

### 2. Team Name Matching
- **Purpose:** Scoring service matches fixtures to teams by name
- **Current Method:** Exact string match in MongoDB query
- **Status:** ❌ BROKEN for 40/56 teams

### 3. League Association
- **Purpose:** Calculate points only for teams in a specific league
- **Recent Fix:** Added `leagueId` filter to scoring query
- **Status:** ✅ FIXED

---

## Detailed Breakdown

### Champions League (36 teams)

**✅ Exact Match (14 teams) - Everything works:**
- Atalanta BC
- Athletic Club
- Borussia Dortmund
- Chelsea FC
- Club Atlético de Madrid
- FC København
- FK Kairat
- Manchester City FC
- PAE Olympiakos SFP
- PSV
- Paphos FC
- Royale Union Saint-Gilloise
- Sport Lisboa e Benfica
- Sporting Clube de Portugal

**🟡 Fuzzy Match (22 teams) - Fixtures work, Scoring broken:**
| Our Database Name | API Name Required |
|-------------------|-------------------|
| Ajax | AFC Ajax |
| Monaco | AS Monaco FC |
| Arsenal | Arsenal FC |
| Leverkusen | Bayer 04 Leverkusen |
| Club Brugge | Club Brugge KV |
| Frankfurt | Eintracht Frankfurt |
| Barcelona | FC Barcelona |
| Bayern München | FC Bayern München |
| Inter | FC Internazionale Milano |
| Bodø/Glimt | FK Bodø/Glimt |
| Galatasaray | Galatasaray SK |
| Juventus | Juventus FC |
| Liverpool | Liverpool FC |
| Newcastle | Newcastle United FC |
| Marseille | Olympique de Marseille |
| Paris | Paris Saint-Germain FC |
| Qarabağ | Qarabağ Ağdam FK |
| Real Madrid | Real Madrid CF |
| Slavia Praha | SK Slavia Praha |
| Napoli | SSC Napoli |
| Tottenham | Tottenham Hotspur FC |
| Villarreal | Villarreal CF |

---

### Premier League (20 teams)

**✅ Exact Match (2 teams) - Everything works:**
- Chelsea FC
- Manchester City FC

**🟡 Fuzzy Match (16 teams) - Fixtures work, Scoring broken:**
| Our Database Name | API Name Required |
|-------------------|-------------------|
| Bournemouth | AFC Bournemouth |
| Arsenal | Arsenal FC |
| Aston Villa | Aston Villa FC |
| Brentford | Brentford FC |
| Brighton & Hove Albion | Brighton & Hove Albion FC |
| Burnley | Burnley FC |
| Crystal Palace | Crystal Palace FC |
| Everton | Everton FC |
| Fulham | Fulham FC |
| Leeds United | Leeds United FC |
| Liverpool | Liverpool FC |
| Manchester United | Manchester United FC |
| Newcastle | Newcastle United FC |
| Nottingham Forest | Nottingham Forest FC |
| Tottenham | Tottenham Hotspur FC |
| West Ham United | West Ham United FC |

**🔴 Missing (2 teams) - Everything broken:**
- Sunderland AFC (ID: 71) - Database has "Sunderland" with wrong externalId (355)
- Wolverhampton Wanderers FC (ID: 76) - Database has "Wolverhampton Wanderers" with wrong externalId (39)

---

## How Each Process Works

### Fixture Import
```python
# Uses fuzzy substring matching (line 2931 in server.py)
if db_team_name in api_team_name or api_team_name in db_team_name:
    match_found = True
```
**Works for:** 54/56 teams ✅

### Score Update (from API to fixtures collection)
```python
# Uses externalId to find fixtures
fixtures = db.fixtures.find({'footballDataId': api_fixture_id})
```
**Works for:** All teams with correct externalId ✅

### Score Calculation (from fixtures to league_points)
```python
# Uses EXACT name matching (line 327-333 in scoring_service.py)
fixtures = db.fixtures.find({
    "leagueId": league_id,
    "$or": [
        {"homeTeam": {"$in": team_names}},  # EXACT match required
        {"awayTeam": {"$in": team_names}}
    ]
})
```
**Works for:** 16/56 teams only ❌

---

## Required Action

**Option A: Update all 38 team names + fix 2 missing teams (40 total)**
- Ensures scoring works correctly
- Consistent with updates already done (Chelsea FC, Atalanta BC, etc.)
- One-time fix

**Option B: Modify scoring service to use fuzzy matching**
- Change scoring_service.py line 327-333
- More complex, potential edge cases
- Doesn't fix the 2 missing teams

---

## Recommendation

**Update all 40 teams** to match API names exactly.

This is consistent with the approach taken for the 6 teams already updated (Chelsea FC, Atalanta BC, Club Atlético de Madrid, FC København, Paphos FC, FK Kairat).

**Benefits:**
- Clean, predictable matching
- Aligns database with authoritative source (API)
- Fixes scoring permanently
- No code complexity

---

## Testing Requirements

After updates:
1. Recompute scores for MYCL 7 (preview)
2. Verify all teams show correct points
3. Create new PL league and test scoring
4. Redeploy to production
5. Test MYCL 8 scoring in production

---

**End of Report**
