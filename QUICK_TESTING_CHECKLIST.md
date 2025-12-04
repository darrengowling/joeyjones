# ⚡ Quick Testing Checklist
## Sport X - 15-Minute Colleague Test

**Use this for rapid validation before deployment**

---

## 🎯 **COMMISSIONER QUICK TEST** (8 minutes)

### Setup (1 min)
- [ ] Sign in: `darren.gowling@gmail.co.uk` or new email
- [ ] Create test league (any sport, defaults OK)
- [ ] Copy invite token

### Critical Path (5 min)
- [ ] ✅ **FIX TEST:** Import fixtures BEFORE auction (should work, no errors)
- [ ] Invite 1 participant (share token)
- [ ] Start auction (when 2 people joined)
- [ ] 📱 **MOBILE:** View auction room on phone/mobile viewport (375px)
  - Rate UX 1-5: ___
  - Issues: _______________
- [ ] Complete auction (let all teams sell)
- [ ] ✅ **FIX TEST:** Import MORE fixtures AFTER auction (should work)
  - Check toast shows correct count (not "100 fixtures")

### Navigation Test (2 min)
- [ ] Navigate: Auction → My Comps → Back to Auction (should work smoothly)
- [ ] ✅ **FIX TEST:** Bulk delete 2 test leagues (should see checkboxes)

---

## 👥 **PARTICIPANT QUICK TEST** (5 minutes)

### Setup (1 min)
- [ ] Use incognito/different browser
- [ ] Sign in with different email
- [ ] Join league with invite token from commissioner

### Critical Path (3 min)
- [ ] Wait for auction start (should see banner appear automatically)
- [ ] Join auction and place 1-2 bids
- [ ] 📱 **MOBILE:** Rate auction room UX: ___/5
- [ ] Win at least 1 team

### Navigation Test (1 min)
- [ ] Navigate away from auction
- [ ] Return to auction (should be easy to find button)
- [ ] After auction: View dashboard

---

## 🚨 **CRITICAL ITEMS - Must Work**

### Recent Fixes to Validate:
1. [ ] ✅ Fixture import PRE-auction works (no errors)
2. [ ] ✅ Fixture import POST-auction shows correct count
3. [ ] ✅ Navigation: No dead ends, can always get back
4. [ ] ✅ Bulk delete: Checkboxes appear for commissioners

### Mobile Auction Room:
- [ ] 📱 Usable on 375px width?
- [ ] 📱 Manager list: Scrollable/readable?
- [ ] 📱 Bid button: Easy to tap?
- [ ] 📱 **Rate overall mobile UX: ___/5**

---

## 🐛 **STOP & REPORT IF:**

- ❌ Fixture import errors (any)
- ❌ Navigation dead ends
- ❌ Auction doesn't start/complete
- ❌ Mobile auction room unusable (< 3/5 rating)
- ❌ Console shows red errors
- ❌ App crashes or freezes

---

## ✅ **PASS CRITERIA**

**Ready for deployment if:**
- All ✅ fixes work correctly
- Mobile auction room rated ≥ 3/5
- No critical bugs found
- Navigation works smoothly

**Needs work if:**
- Mobile auction room rated < 3/5 → Implement quick wins
- Any ✅ fixes broken → Fix before deployment
- Critical bugs → Fix immediately

---

## 📋 **QUICK FEEDBACK FORM**

**Tester:** _____________
**Date:** _____________
**Device:** _____________

**All recent fixes working?** Yes / No / Issues: __________

**Mobile auction room rating:** ___/5
**Specific mobile issues:** __________________________

**Critical bugs found:** 
- 

**Recommendation:** 
- [ ] ✅ Deploy now
- [ ] 🔧 Fix mobile UX first
- [ ] 🚨 Critical bugs - delay deployment

---

**Full details:** See `/app/PRE_DEPLOYMENT_USER_TESTING_GUIDE.md`
