# AFCON 2025/26 User Guide for Commissioners

## Overview
The Africa Cup of Nations (AFCON) 2025/26 is now supported in the fantasy platform. Since AFCON is not covered by the free API tier, fixtures and scores are managed manually via CSV upload or manual entry.

**Tournament Details:**
- **Host:** Morocco
- **Dates:** December 21, 2025 - January 18, 2026
- **Teams:** 24 teams in 6 groups
- **Group Stage:** 36 matches (December 21-31, 2025)

---

## Creating an AFCON League

1. **Click "Create League"**
2. **Select Competition:** Choose "🌍 AFCON" from the dropdown
3. **Select Teams:** Choose from 24 AFCON national teams
4. **Configure Settings:** Set budget, team slots, auction settings as usual
5. **Create & Start Auction**

---

## Importing Fixtures

### Option 1: Upload Pre-Populated CSV (Recommended)

**Download Template:**
- `/app/public/templates/afcon_2025_group_stage_fixtures.csv`
- Contains all 36 group stage matches with dates, venues, and teams

**Steps:**
1. Navigate to your AFCON league page
2. Click **"Import Fixtures"** or **"Upload CSV"** button
3. Select the `afcon_2025_group_stage_fixtures.csv` file
4. Fixtures will be imported automatically

### Option 2: Create Custom CSV

**CSV Format:**
```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId,goalsHome,goalsAway,status
2025-12-21T19:00:00Z,AFCON_001,AFCON_004,Stadium Name,Group A MD1,MATCH_001,,,scheduled
```

**Required Columns:**
- `startsAt`: Match start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
- `homeAssetExternalId`: Home team ID (e.g., AFCON_001 for Morocco)
- `awayAssetExternalId`: Away team ID (e.g., AFCON_002 for Mali)

**Optional Columns:**
- `venue`: Stadium name
- `round`: Match round (e.g., "Group A MD1", "Quarter Final")
- `externalMatchId`: Unique match identifier (for updates)
- `goalsHome`: Home team goals (for score updates)
- `goalsAway`: Away team goals (for score updates)
- `status`: Match status ("scheduled", "in_progress", "completed")

---

## Team IDs Reference

| ID | Team | Group |
|----|------|-------|
| AFCON_001 | Morocco | A |
| AFCON_002 | Mali | A |
| AFCON_003 | Zambia | A |
| AFCON_004 | Comoros | A |
| AFCON_005 | Egypt | B |
| AFCON_006 | South Africa | B |
| AFCON_007 | Angola | B |
| AFCON_008 | Zimbabwe | B |
| AFCON_009 | Nigeria | C |
| AFCON_010 | Tunisia | C |
| AFCON_011 | Uganda | C |
| AFCON_012 | Tanzania | C |
| AFCON_013 | Senegal | D |
| AFCON_014 | DR Congo | D |
| AFCON_015 | Benin | D |
| AFCON_016 | Botswana | D |
| AFCON_017 | Algeria | E |
| AFCON_018 | Burkina Faso | E |
| AFCON_019 | Equatorial Guinea | E |
| AFCON_020 | Sudan | E |
| AFCON_021 | Ivory Coast | F |
| AFCON_022 | Cameroon | F |
| AFCON_023 | Gabon | F |
| AFCON_024 | Mozambique | F |

---

## Updating Scores

### Method 1: CSV Upload (Bulk Updates)

**Update the same CSV** with score columns filled in:

```csv
startsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId,goalsHome,goalsAway,status
2025-12-21T19:00:00Z,AFCON_001,AFCON_004,Stadium,Group A MD1,AFCON_M001,2,0,completed
```

**Steps:**
1. Download your original CSV or create a new one
2. Fill in `goalsHome`, `goalsAway`, and `status` columns
3. Upload the CSV (it will update existing fixtures by `externalMatchId`)

### Method 2: Manual Entry (Individual Updates)

**Backend API Endpoint:**
```
PATCH /api/fixtures/{fixture_id}/score?commissionerId={your_id}
```

**Request Body:**
```json
{
  "goalsHome": 2,
  "goalsAway": 1,
  "status": "completed"
}
```

**Note:** UI for manual editing will be added in a future update.

---

## Tips for Commissioners

1. **Import fixtures BEFORE starting auction** - participants can see upcoming matches
2. **Use `externalMatchId`** - ensures updates don't create duplicate fixtures
3. **Update scores promptly** - fantasy points depend on match results
4. **Backup your CSV** - keep a copy for reference and easy updates

---

## Troubleshooting

**Problem:** Fixtures not appearing after upload

**Solution:** Check CSV format, ensure:
- Date format is ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- Team IDs match exactly (AFCON_001 to AFCON_024)
- File is UTF-8 encoded

**Problem:** Duplicate fixtures created

**Solution:** Use `externalMatchId` column with unique values (e.g., AFCON_M001, AFCON_M002)

**Problem:** Scores not updating

**Solution:** Ensure:
- `externalMatchId` matches the original fixture
- `goalsHome` and `goalsAway` are integers
- You are logged in as the league commissioner

---

## Support

For issues or questions, contact the platform administrator or refer to the main user documentation.

**Happy AFCON Fantasy Gaming! 🌍🏆**
