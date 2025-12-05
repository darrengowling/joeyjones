# AFCON Commissioner Guide: How to Upload Match Scores

## Overview
As an AFCON commissioner, you'll need to upload match scores using a CSV file. This guide walks you through the simple process.

---

## Step-by-Step Instructions

### Step 1: Download the Template
1. Download the AFCON fixtures template: [afcon_2025_fixtures_with_names.csv](/templates/afcon_2025_fixtures_with_names.csv)
2. Save it to your computer

**Note:** This file includes team names (Morocco, Egypt, etc.) to make it easy to identify matches!

### Step 2: Open the File
Open the downloaded file in one of these programs:
- **Microsoft Excel** (Windows/Mac)
- **Google Sheets** (online - File → Import → Upload)
- **Apple Numbers** (Mac)
- **LibreOffice Calc** (free, all platforms)

### Step 3: Fill in the Scores
The file already contains all 36 AFCON group stage fixtures. You just need to add scores:

**What you'll see in the file:**
- `homeTeam` - Home team name (e.g., "Morocco")
- `awayTeam` - Away team name (e.g., "Comoros")
- `goalsHome` - **YOU FILL THIS** - Goals scored by home team
- `goalsAway` - **YOU FILL THIS** - Goals scored by away team

**Example:**
```
Row shows: Morocco, Comoros
Morocco scored 1, Comoros scored 2
Fill in: goalsHome = 1, goalsAway = 2
```

**Important:**
- Leave score columns **empty** for matches that haven't been played yet
- Only fill in scores for completed matches
- The system will automatically mark matches as "Finished" when scores are present

### Step 4: Save the File
1. Click **File → Save** (or Ctrl+S / Cmd+S)
2. **Important:** Keep it as a CSV file format
3. If Excel asks "Do you want to save as CSV?", click **Yes**

### Step 5: Upload to Your Competition
1. Log in to your Sport X account
2. Go to **My Competitions**
3. Click on your AFCON competition
4. Click the **Fixtures** tab
5. Scroll down to the **"Import Fixtures (CSV)"** section
6. Click **Choose File** and select your edited CSV file
7. Click to upload
8. You should see a success message: "✅ Successfully imported 36 fixtures"

### Step 6: Verify
Check the fixtures list - completed matches should now show:
- ✅ **Finished** badge (green)
- Final scores displayed
- Scheduled matches show ⏱️ **Scheduled** badge (yellow)

---

## Tips & Troubleshooting

### ✅ Do's
- **Re-upload** the same file multiple times as more matches complete
- Fill in scores as matches happen (you don't need to wait for all matches)
- Double-check your scores before uploading

### ❌ Don'ts
- Don't delete or rename columns in the CSV
- Don't change the `externalMatchId` values
- Don't use the green "Upload Match Scores" button (that's for cricket only)

### Common Issues

**Q: I see an error page after uploading**
A: Make sure you're using the blue "Import Fixtures (CSV)" button, NOT the green "Upload Match Scores" button

**Q: Scores aren't showing up**
A: Check that you filled in BOTH `goalsHome` and `goalsAway` columns, and saved the file as CSV format

**Q: Excel is changing my data**
A: If Excel is auto-formatting dates/times, use Google Sheets instead - it preserves CSV formatting better

**Q: I made a mistake in the scores**
A: Simply edit the CSV file with corrected scores and re-upload it. The system will update the existing fixtures.

---

## Example Workflow

**Before Match Day:**
1. Download template (has all fixtures pre-filled)
2. Upload it immediately to create all scheduled fixtures

**After Each Match Day:**
1. Open your saved CSV file
2. Fill in the scores for completed matches
3. Save the file
4. Re-upload to update the scores
5. Repeat after each match day

---

## Need Help?

If you encounter issues:
1. Make sure you're logged in as the commissioner
2. Check you're on the Fixtures tab
3. Verify you're using the correct CSV file
4. Contact support if problems persist

---

## Quick Reference

**File Location:** `/public/templates/afcon_2025_fixtures_with_names.csv`

**Required Columns (already in template):**
- startsAt, homeAssetExternalId, awayAssetExternalId, venue, round, externalMatchId

**Optional Columns (you fill in):**
- goalsHome, goalsAway

**Upload Button:** Fixtures tab → "Import Fixtures (CSV)" (blue button)

**Format:** CSV (Comma-Separated Values)

**File Size:** Small (~5KB)

**Upload Time:** < 5 seconds
