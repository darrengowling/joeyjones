# User Testing Script: Fantasy Football Auction App

## Overview
This is a fantasy football app where you compete against friends by bidding on real football teams in a live auction, then your teams earn points based on real match results.

---

## Test Group Setup

**Participants:** 2-4 users (one will be the "Commissioner")
**Time needed:** 30-45 minutes
**What you'll need:** Email addresses for each tester

---

## Pre-Test Briefing (Read to testers)

> "You're testing a fantasy football app. One of you will create a competition, and you'll all join and bid on teams in a live auction. The person who creates the competition controls when the auction starts. Be vocal about anything confusing or broken - we need honest feedback!"

---

## PHASE 1: Sign Up & Navigation (5 min)

### Commissioner (Tester 1):
1. **Go to:** https://bidflowfix.preview.emergentagent.com
2. **Click:** "Create Competition" or similar button
3. **Enter your email** when prompted
4. **Note:** You'll see a magic link or auto-login (auth is simplified for testing)

**✅ CHECK:** Did you get logged in without issues?
**❌ FLAG:** Any errors or confusion?

### Other Testers (2-4):
1. **Go to:** https://bidflowfix.preview.emergentagent.com
2. **Click:** "Join Competition" or similar
3. **Enter your email**

**✅ CHECK:** Can you see the main page?
**❌ FLAG:** Any login issues?

---

## PHASE 2: Create Competition (Commissioner Only - 5 min)

### Commissioner:
1. **Click:** "Create Competition" or "New League"
2. **Fill in details:**
   - Competition name: "Test League [Your Name]"
   - Sport: Football (default)
   - Budget: £500m (default is fine)
   - Managers: Min 2, Max 4 (or adjust to your group size)
   - Slots per manager: 3 (keep it short for testing)

3. **IMPORTANT - Team Selection:**
   - You should see an option to "Select teams for auction"
   - **Choose:** "Select specific teams"
   - **Select:** Pick 9 teams from the list (any 9 you like)
   - This limits the auction to just these teams for faster testing

4. **Click:** "Create" or "Create League"

**✅ CHECK:**
- Did the league create successfully?
- Can you see a screen with league details?
- Do you see an "Invite Token" or link to share?

**❌ FLAG:**
- Any errors during creation?
- Unclear what any field means?
- Team selection confusing or broken?

### Share Invite:
**Commissioner:** Copy the invite code/link and share it with other testers (via chat, email, etc.)

---

## PHASE 3: Join Competition (Other Testers - 5 min)

### All Non-Commissioners:
1. **Get the invite code** from Commissioner
2. **Click:** "Join Competition" or "Join League"
3. **Enter/paste the invite code**
4. **Click:** Join

**✅ CHECK:**
- Did you successfully join?
- Can you see the league details?
- Can you see other participants?
- Do you see how many teams you need to fill (should say 3)?

**❌ FLAG:**
- Invite code didn't work?
- Joined but can't see details?
- Confusing what to do next?

---

## PHASE 4: Wait for Auction (All Testers - 2 min)

### Commissioner:
- **Wait** until all testers have joined
- **Look for:** A button like "Start Auction"
- **Check:** Does it show "2/2 managers joined" or similar?

**✅ CHECK:** Button enabled when enough people joined?
**❌ FLAG:** Button not appearing? Can't tell if people joined?

### Other Testers:
- **Wait** on the league page
- **Look for:** List of participants
- Should see your name and others who joined

**✅ CHECK:** Can you see everyone in the league?
**❌ FLAG:** Only seeing yourself? Missing participants?

---

## PHASE 5: Start Auction (Commissioner - 1 min)

### Commissioner:
1. **Click:** "Start Auction" button
2. **Wait** for screen to change

**✅ CHECK:** 
- Did auction room load?
- Can you see a team being offered?
- See a timer counting down?

**❌ FLAG:**
- Button didn't work?
- Auction started but looks broken?
- Error messages?

---

## PHASE 6: Live Auction (All Testers - 15-20 min)

### Everyone:
This is the main feature to test! You should now be in a live auction room.

**What you should see:**
- **Current team** being auctioned (with logo/name)
- **Timer** counting down (30 seconds default)
- **Your budget** remaining (starts at £500m)
- **Bid button** or input to place bids
- **Sidebar** showing all 9 teams (if team selection worked)
- **Other participants** and their budgets

### How to bid:
1. **Look at** the current team being offered
2. **Enter a bid amount** (e.g., £5m, £10m)
3. **Click** "Place Bid" or "Bid"
4. **Watch** timer extend if someone bids late (anti-snipe)

### What to test:
- **Place bids** on teams you want
- **Try to outbid** each other
- **Watch what happens** when timer runs out
- **See if** you get teams you won
- **Keep going** until auction completes (when everyone has 3 teams)

**✅ CHECK:**
- Bids showing up immediately?
- Timer working correctly?
- Teams marked as "sold" after winning?
- Budget updating when you win?
- Sidebar showing only 9 teams (not all 36)?
- Auction completes when all rosters full?

**❌ FLAG:**
- Bids not appearing?
- Teams showing as "sold" while still being bid on?
- Timer glitching?
- Seeing more than 9 teams (should only be your selected 9)?
- Auction doesn't end when rosters full?
- Can bid more than budget allows?
- Can't see other people's bids?

---

## PHASE 7: After Auction (All Testers - 5 min)

### Everyone:
After auction completes, explore what you can see:

1. **Check "My Competitions"** (if there's a link)
   - Can you see your teams?
   - Do they show the team names (not "Team 1, Team 2")?
   - Do they show how much you paid?

2. **Go to Competition Dashboard** (click on the league name)
   - **Summary Tab:** See your roster with team names and prices?
   - **League Tab:** See all participants (all 2-4 of you)?
   - **Check:** Do all participants show up, not just one?

**✅ CHECK:**
- Your roster displays correctly with team names?
- All participants visible in league table?
- Everyone starts at 0 points?
- Budget remaining shown correctly?

**❌ FLAG:**
- Roster showing "Team 1, Team 2" instead of real names?
- Only seeing one participant in league table?
- Missing information?
- Anything confusing?

---

## PHASE 8: General Feedback (5 min)

### Questions for All Testers:

**Usability:**
1. Was anything confusing or unclear?
2. Did you ever get stuck not knowing what to do next?
3. Any features you expected but couldn't find?

**Bugs:**
4. Did anything break or show errors?
5. Any features not working as expected?
6. Did the app feel slow or laggy?

**Design:**
7. Was the layout easy to navigate?
8. Could you read everything clearly?
9. Did anything look broken or ugly?

**Auction Experience:**
10. Was bidding exciting or stressful?
11. Could you tell what was happening?
12. Did the timer feel fair?

**Overall:**
13. Would you use this with friends?
14. What would make it better?
15. What did you like most?

---

## Key Things to Watch For

### Critical Issues:
- ❌ Auction doesn't start
- ❌ Bids don't register
- ❌ Auction doesn't end when it should
- ❌ Wrong number of teams in auction (should be 9)
- ❌ Users can't join the league

### Important Issues:
- ⚠️ Confusing navigation
- ⚠️ Roster shows "Team 1, Team 2" instead of names
- ⚠️ League table missing participants
- ⚠️ Timer behaving strangely
- ⚠️ Can bid more than budget

### Nice to Fix:
- 💡 Unclear instructions
- 💡 Layout issues
- 💡 Missing helpful hints
- 💡 Slow performance

---

## After Testing: What to Report

### For each issue found, note:
1. **What happened?** (the bug/issue)
2. **What were you doing?** (steps to reproduce)
3. **What did you expect?** (intended behavior)
4. **How bad is it?** (Critical / Important / Minor)
5. **Screenshot?** (if possible)

### Example Bug Report:
> **Issue:** Roster shows "Team 1, Team 2" instead of club names
> **Steps:** Complete auction → Go to Dashboard → Summary tab
> **Expected:** See "Manchester United £14m", "Liverpool £5m" etc.
> **Severity:** Important - confusing but doesn't block usage
> **Screenshot:** [attach if possible]

---

## Tips for Smooth Testing

**For Commissioner:**
- Don't start auction until everyone has joined
- Communicate with testers via chat/call during auction
- Keep testing session to 45 min max

**For All Testers:**
- Be vocal about issues as they happen
- Don't just say "it's broken" - describe what you see
- Try to break things! That's helpful!
- Remember this is a test - bugs are expected

**Best Practice:**
- Have someone (not a tester) take notes during the session
- Record screen if possible (with permission)
- Do a quick debrief right after while fresh

---

## Success Criteria

The test is successful if:
✅ All users can create accounts
✅ All users can join a league
✅ Auction starts and runs without crashing
✅ Bids register and display correctly
✅ Only selected 9 teams appear (not all 36)
✅ Auction completes when rosters are full
✅ Final roster shows team names (not "Team 1")
✅ League table shows all participants (not just one)

Even if there are bugs, if you complete the flow, that's good data!

---

## Emergency Contacts

**If testing completely breaks:**
- [Your contact email/phone]
- Screenshot the error
- Note what you were doing
- We can debug later

**Questions during test:**
- Have testers ask each other first
- If totally stuck, [your contact method]

---

## Post-Test: Clean Up

After testing, you may want to:
1. Delete test leagues (Commissioner can do this)
2. Clear test data
3. Or leave it for review/debugging

**Note:** Test data visible to you for debugging purposes.

---

## Variations for Different Group Sizes

### 2 Testers:
- Set minManagers: 2, clubSlots: 3
- Pick 6-9 teams for auction
- Each person gets 3 teams

### 3 Testers:
- Set minManagers: 3, clubSlots: 3
- Pick 9-12 teams for auction
- Each person gets 3 teams

### 4 Testers:
- Set minManagers: 4, clubSlots: 3
- Pick 12-15 teams for auction
- Each person gets 3 teams

**Keep slots at 3** - faster testing, easier to complete.

---

## Thank You!

Thank you for testing! Your feedback helps make the app better for everyone.

**Remember:** Be honest, be thorough, and have fun! 🎉
