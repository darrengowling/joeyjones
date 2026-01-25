# Consolidated Project Status & Plan

**Created:** January 25, 2026  
**Purpose:** Single source of truth for current status and next steps

---

## ✅ MIGRATION STATUS: COMPLETE

The Railway migration is **functionally complete**. Both EPL and IPL are working.

| Component | Status | Notes |
|-----------|--------|-------|
| Railway Backend | ✅ Deployed | joeyjones-production |
| Railway Frontend | ✅ Deployed | energetic-victory-production |
| MongoDB Atlas | ✅ Connected | sport_x_poc (M0 free tier) |
| Redis Cloud | ✅ Connected | 250MB Essentials (London) |
| EPL Teams (20) | ✅ Seeded | All have externalId for fixture imports |
| IPL Players (125) | ✅ Seeded | Curated probable starters |
| EPL Fixture Import | ✅ Working | Tested successfully |
| Cricket Sport | ✅ Enabled | SPORTS_CRICKET_ENABLED=true |
| WebSocket-only | ✅ Working | No sticky sessions needed |

---

## 🧪 TESTING PHASE (Current)

**You are here:** Running test auctions on Railway to validate everything works.

**To test:**
- [ ] EPL auction end-to-end (create → invite → bid → complete)
- [ ] IPL auction end-to-end
- [ ] Fixture import and scoring flow
- [ ] Multiple concurrent users

---

## 📋 BACKLOG BY PRIORITY

### P0 - Pre-Pilot Critical

| # | Task | Effort | Source | Notes |
|---|------|--------|--------|-------|
| 1 | **Full auction flow testing** | 2 hrs | Testing now | On Railway |
| 2 | **Fixture scoring testing** | 30 min | MASTER_TODO | Verify scores update |
| 3 | **UI/UX redesign** | 1-2 weeks | User request | See DESIGN_SPEC.md |

### P1 - Pre-Pilot Important

| # | Task | Effort | Source | Notes |
|---|------|--------|--------|-------|
| 4 | **Auth hardening** | 1 day | MASTER_TODO | SendGrid email delivery |
| 5 | **Sticky tabs on mobile** | 1 hr | MASTER_TODO | UI bug |
| 6 | **Commissioner auth checks** | 1 hr | MASTER_TODO | Security |
| 7 | **DB Call Optimization** | 30 min | MASTER_TODO | find_one_and_update |

### P2 - Post-Pilot / Future

| # | Task | Effort | Source | Notes |
|---|------|--------|--------|-------|
| 8 | **WC2026 Teams** | 2 hrs | MASTER_TODO | After qualifiers complete |
| 9 | **IPL Cricbuzz Integration** | 2 hrs | MASTER_TODO | After IPL 2026 in API |
| 10 | **Refactor server.py** | 1-2 weeks | MASTER_TODO | 5,900+ lines |
| 11 | **Mobile app (Capacitor)** | 1-2 weeks | MASTER_TODO | After pilot |
| 12 | **Payment integration** | 2 weeks | MASTER_TODO | Stripe |

### Known Monitoring Items

| Issue ID | Summary | Watch For |
|----------|---------|-----------|
| ISSUE-016 | Roster not updating | Race conditions |
| ISSUE-019 | "Couldn't place bid" | False reports |
| ISSUE-020 | Team offered twice | Socket duplication |
| ISSUE-022 | "Unknown" manager names | Missing userName |

---

## 🎨 UI/UX REDESIGN

**Status:** Design spec exists at `/app/DESIGN_SPEC.md`

**Key changes planned:**
- Dark theme (navy background, cyan accents)
- Mobile-first (390px width base)
- Glassmorphism cards
- Bottom navigation bar
- Pill-shaped buttons

**When:** After migration testing complete, before pilot invites

---

## 🔐 AUTH HARDENING

**Current state:** Magic link token returned in API response (dev mode)

**Required for production:**
1. SendGrid/Resend account
2. Email delivery integration
3. Remove token from API response
4. Rate limiting (3 requests/hour/email)
5. Single-use token enforcement

**When:** After UI/UX redesign, before pilot invites

**Why deferred:** Could interfere with automated testing

---

## 📊 DATABASE COMPARISON

| Collection | Local | Railway | Notes |
|------------|-------|---------|-------|
| Football teams | 74 | 56 | Railway has EPL+UCL, missing AFCON |
| Cricket players | 252 | 125 | Railway has curated IPL only |
| Sports | 2 | 2 | ✅ Match |

**Decision pending:** Remove AFCON/UCL from Railway to simplify? Keep just EPL + IPL for pilot.

---

## 📁 KEY DOCUMENTATION

| Document | Purpose |
|----------|---------|
| `/app/MASTER_TODO_LIST.md` | Canonical task tracker |
| `/app/POC_RAILWAY_DEPLOYMENT.md` | Railway setup & results |
| `/app/DESIGN_SPEC.md` | UI redesign specification |
| `/app/SESSION_CHANGES.md` | Today's changes |
| `/app/memory/PRD.md` | Product requirements |

---

## ⚡ QUICK REFERENCE

### Railway URLs
- **Backend:** https://joeyjones-production.up.railway.app
- **Frontend:** https://energetic-victory-production.up.railway.app

### Railway MongoDB
```
mongodb+srv://darts_admin:Anniepip1315@cluster0.edjfwnl.mongodb.net/sport_x_poc
```

### Key Environment Variables (Railway)
```
SPORTS_CRICKET_ENABLED=true    # Enables cricket in app
FOOTBALL_DATA_TOKEN=eddf...    # EPL/UCL fixture imports
RAPIDAPI_KEY=62431...          # Cricket fixture imports
```

---

## 🎯 RECOMMENDED NEXT STEPS

1. **Now:** Complete test auctions (EPL + IPL) on Railway
2. **If tests pass:** Decide on simplifying DB (remove AFCON/UCL?)
3. **Then:** UI/UX redesign based on DESIGN_SPEC.md
4. **Before pilot:** Auth hardening with SendGrid
5. **Pilot launch:** Invite 400 UK users
