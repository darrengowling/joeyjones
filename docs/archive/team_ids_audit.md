# Team IDs Audit for 2025/26 Season

## Premier League - Missing Teams

These 7 teams need to be ADDED to the database:

| Team | Football-Data.org ID | Status |
|------|---------------------|--------|
| Arsenal | 57 | MISSING |
| Brighton | 397 | MISSING (note: "Brighton & Hove Albion" with ID 397 exists but wrong name) |
| Chelsea | 61 | MISSING |
| Liverpool | 64 | MISSING |
| Manchester City | 65 | MISSING |
| Newcastle United | 67 | MISSING |
| Tottenham Hotspur | 73 | MISSING |

**Action Required:**
- Remove: "Brighton & Hove Albion" (ID: 397)
- Add: "Brighton" with ID 397

## Champions League - Current IDs (Need Verification)

All 36 teams are present. Current IDs in database:

| Team | Current externalId | Needs Verification |
|------|-------------------|-------------------|
| Ajax | 678 | ⚠️ Web search suggests 60 |
| Arsenal | 57 | ✅ Confirmed |
| Atalanta | 102 | ⚠️ Web search suggests 73 |
| Athletic Club | 77 | ❓ |
| Atlético de Madrid | 78 | ❓ |
| B Dortmund | 4 | ❓ |
| Barcelona | 81 | ✅ Confirmed |
| Bayern München | 5 | ✅ Confirmed |
| Benfica | 503 | ⚠️ Web search suggests 1938 |
| Bodø/Glimt | 5721 | ❓ |
| Chelsea | 61 | ✅ Confirmed |
| Club Brugge | 851 | ❓ |
| Copenhagen | 1030 | ❓ |
| Frankfurt | 19 | ❓ |
| Galatasaray | 610 | ⚠️ Web search suggests 159 |
| Inter | 108 | ❓ |
| Juventus | 109 | ✅ Confirmed |
| Kairat Almaty | 10601 | ❓ |
| Leverkusen | 3 | ❓ |
| Liverpool | 64 | ✅ Confirmed |
| Man City | 65 | ✅ Confirmed |
| Marseille | 516 | ⚠️ Web search suggests 529 |
| Monaco | 548 | ⚠️ Web search suggests 510 |
| Napoli | 113 | ⚠️ Web search suggests 81 |
| Newcastle | 67 | ✅ Confirmed |
| Olympiacos | 735 | ⚠️ Web search suggests 181 |
| PSV | 674 | ⚠️ Web search suggests 64 |
| Pafos | 2025 | ❓ |
| Paris | 524 | ❓ |
| Qarabağ | 611 | ❓ |
| Real Madrid | 86 | ✅ Confirmed |
| Slavia Praha | 930 | ❓ |
| Sporting CP | 498 | ⚠️ Web search suggests 1753 |
| Tottenham | 73 | ✅ Confirmed |
| Union SG | 3929 | ❓ |
| Villarreal | 94 | ❓ |

**Note:** Web search results are inconsistent and may be incorrect. Need to verify against actual Football-Data.org API endpoint: `https://api.football-data.org/v4/competitions/CL/teams`
