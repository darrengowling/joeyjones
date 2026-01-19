# Master TODO List - Sport X Platform

**Last Updated:** January 17, 2026  
**Purpose:** Single source of truth for all work items organized by deployment phase  
**Current Status:** Pre-Migration to Railway (EU-West)

---

## 📍 CURRENT SITUATION SUMMARY

| Aspect | Status |
|--------|--------|
| **Platform** | Emergent (US-hosted) |
| **Core Issue** | UK users face ~700ms latency due to transatlantic network overhead |
| **Pilot Target** | 400 UK users |
| **Decision** | Migrate to Railway (EU-West/London) for optimal UK latency |
| **Migration Timeline** | Starting in a few days |

---

## 🚦 TASK PHASES OVERVIEW

| Phase | Focus | Timeline |
|-------|-------|----------|
| **🔴 PRE-MIGRATION** | Prep work before Railway migration | Now |
| **🟡 PRE-PILOT** | Work after migration, before 400-user pilot | After migration |
| **🟢 POST-PILOT** | Enhancements after successful pilot | After pilot success |
| **🔵 FUTURE** | Long-term roadmap items | TBD |

---

## 🔴 PRE-MIGRATION TASKS

*Tasks to complete before or during Railway migration*

### Infrastructure Decisions (USER ACTION REQUIRED)

| # | Item | What's Needed | Status |
|---|------|---------------|--------|
| 1 | **Railway Account** | Create account at railway.app | ❓ Pending |
| 2 | **MongoDB Atlas Cluster** | Create M10 in `europe-west2` (London) ~£45/mo | ❓ Pending |
| 3 | **Redis Cloud** | Confirm existing Essentials account is portable | ✅ Ready (256 connections) |
| 4 | **Custom Domain** | Purchase domain if desired (e.g., sportx.app) | ❓ Pending |
| 5 | **Apple Developer Account** | ~£79/year (needed for mobile apps later) | ❓ Optional for now |
| 6 | **Data Migration Approach** | Fresh start vs export/import existing data? | ❓ Decision needed |

### Code Changes Before Migration

| # | Task | Effort | Risk | Can Do in Emergent? | Notes |
|---|------|--------|------|---------------------|-------|
| 1 | **Add `/health` endpoint** | 5 min | 🟢 Low | ✅ Yes - High confidence | ✅ Already done |
| 2 | **Environment variable audit** | 30 min | 🟢 Low | ✅ Yes - High confidence | ✅ Done (Jan 16) - No hardcoded URLs, ready for Railway |
| 3 | **Update CORS config** | 15 min | 🟢 Low | ✅ Yes - High confidence | Do during Railway setup - update FRONTEND_ORIGIN, CORS_ORIGINS |

---

### 🔐 AUTHENTICATION HARDENING (PRE-PILOT CRITICAL)

**Current State:** Magic-link infrastructure exists but token returned in API response (dev mode)  
**Required State:** Real email delivery + production security

**What EXISTS (Good Foundation):**
- ✅ JWT token generation and validation
- ✅ Magic link tokens stored in MongoDB with expiry
- ✅ Token hashing (secure storage)
- ✅ Session management structure
- ✅ Rate limiting infrastructure exists

**⏸️ DEFERRED UNTIL SENDGRID SETUP**

All auth hardening items grouped together - implement as a single piece of work once SendGrid account and API key are available:

| # | Item | Current | Required | Effort | Risk |
|---|------|---------|----------|--------|------|
| 1 | **Email delivery** | Token returned in response | Send via email (SendGrid/Resend) | 2-4 hrs | 🟢 Low |
| 2 | **Remove dev token exposure** | `"token": magic_token` in response | Remove - only send via email | 5 min | 🟢 Low |
| 3 | **Rate limiting on auth** | Not applied | Limit magic link requests (e.g., 3/hour/email) | 1 hr | 🟢 Low |
| 4 | **Single-use tokens** | May allow reuse | Ensure token deleted after use | 30 min | 🟢 Low |
| 5 | **Shorter token expiry** | 15 min (OK) | Verify appropriate for email delivery | Config | 🟢 Low |

**Why deferred:**
- Rate limiting could inadvertently block stress testing (unique emails per test, but still a risk)
- All items should be implemented together once email delivery is working
- No security risk pre-pilot as only team is using the system

**Dependencies:**
- SendGrid account (free tier: 100 emails/day) OR Resend account
- API key added to environment

**Implementation Plan (do all at once):**
```
Step 1: Set up SendGrid/Resend account, get API key
Step 2: Integrate email service, create magic link email template
Step 3: Update /auth/magic-link endpoint:
        - Send email with link instead of returning token
        - Return only { "message": "Check your email" }
Step 4: Add rate limiting (3 requests/hour/email)
Step 5: Verify single-use token enforcement
Step 6: Test full flow end-to-end
```

**Estimated Total Effort:** 1 day  
**When:** After stress testing complete, before pilot invites go out

### Documentation to Prepare

| # | Doc | Status |
|---|-----|--------|
| 1 | Railway deployment guide | See `/app/MIGRATION_PLAN.md` |
| 2 | Environment variables list | In MIGRATION_PLAN.md |
| 3 | Rollback procedure | In MIGRATION_PLAN.md |

---

## 🟡 PRE-PILOT TASKS

*Tasks to complete after migration, before inviting 400 users*

### Critical - Must Have for Pilot

| # | Task | Effort | Risk | Confidence | Why Critical |
|---|------|--------|------|------------|--------------|
| 1 | **Stress test on Railway** | 2 hrs | 🟢 Low | ✅ High | Validate migration fixed latency |
| 2 | **Authentication hardening** | 1 day | 🟢 Low | ✅ High | Real email delivery, no token exposure |
| 3 | **Sentry monitoring** | 30 min | 🟢 Low | ✅ High | Need error visibility at scale |
| 4 | **Database backup verification** | 1 hr | 🟢 Low | ✅ High | MongoDB Atlas M10 has backups - verify configured |
| 5 | **Verify all core flows** | 2 hrs | 🟢 Low | ✅ High | Create league, auction, scoring |
| 6 | **Update Operations Playbook** | 1 hr | 🟢 Low | ✅ High | Update `/app/docs/OPERATIONS_PLAYBOOK.md` for Railway |

**Target metrics after migration:**

| Scale | Target Success Rate | Target p50 | Target p99 |
|-------|--------------------:|----------:|----------:|
| 20 leagues (160 users) | ≥95% | ≤200ms | ≤1000ms |
| 50 leagues (400 users) | ≥90% | ≤300ms | ≤1500ms |

### High Priority - Should Have

| # | Task | Effort | Risk | Confidence | Benefit |
|---|------|--------|------|------------|---------|
| 1 | **DB Call Caching** | 2 hrs | 🟡 Med | ⚠️ Medium | ⏸️ Attempted Jan 16 - reverted due to bug. Needs more careful implementation |
| 2 | **DB Call Optimization #2** - Combine update+find | 30 min | 🟢 Low | ✅ High | -100ms per bid (find_one_and_update) |
| 3 | **DB Call Optimization #3** - Remove league query | 1-2 hrs | 🟢 Low | ⚠️ Medium | Part of caching approach above |
| 4 | **Commissioner auth checks** | 1 hr | 🟡 Med | ✅ High | Security - prevent unauthorized actions |
| 5 | **Frontend performance audit** | 2 days | 🟢 Low | ✅ High | React.memo for heavy components, debounce socket updates |
| 6 | **Error recovery patterns** | 2-3 days | 🟡 Med | ⚠️ Medium | Retry logic for transient failures, graceful degradation |

### Medium Priority - Nice to Have

| # | Task | Effort | Risk | Confidence | Benefit |
|---|------|--------|------|------------|---------|
| 1 | ~~**Bidder status indicator**~~ | 2 hrs | 🟢 Low | ✅ High | ❌ Considered - not needed. Current bidder name next to bid is sufficient |
| 2 | ~~**Current bid label**~~ | 30 min | 🟢 Low | ✅ High | ⏸️ Review - already visible in main bid display |

### Monitoring Items (Watch During Pilot)

| Issue ID | Summary | Watch For |
|----------|---------|-----------|
| ISSUE-016 | Roster not updating | Race conditions at 7+ concurrent users |
| ISSUE-019 | "Couldn't place bid" | False reports (actually roster full) |
| ISSUE-020 | Team offered twice | Socket duplication |
| ISSUE-022 | "Unknown" manager names | Missing userName data |

---

## 🟢 POST-PILOT TASKS

*Enhancements after successful 400-user pilot*

### Mobile App Strategy 📱

**Decision:** Capacitor (wrap existing React app) → App Store/Play Store presence

| Phase | Approach | When | Trigger to Advance |
|-------|----------|------|-------------------|
| **Current** | Mobile-responsive web | Now | ✅ Already done |
| **Post-Pilot** | **Capacitor** | After successful pilot | Users want "real" app |
| **Scale** | React Native | If mobile is 70%+ of usage | Capacitor hitting performance limits |

**Capacitor Implementation (Post-Pilot)**

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1 | Add Capacitor to React project | 2 hrs | `npm install @capacitor/core @capacitor/cli` |
| 2 | Configure iOS project | 2 hrs | Requires macOS + Xcode |
| 3 | Configure Android project | 2 hrs | Requires Android Studio |
| 4 | Add push notification plugin | 4 hrs | For "Auction starting!", "You've been outbid!" |
| 5 | Handle deep links | 2 hrs | Open app from invite links |
| 6 | App Store submission | 4 hrs | Apple review: 1-3 days |
| 7 | Play Store submission | 2 hrs | Google review: hours to 1 day |

**Estimated total:** 1-2 weeks

**Costs:**
- Apple Developer: ~£79/year
- Google Play: ~£20 one-time

**Signs you'd need React Native later:**
- Users complaining about "laggy" mobile feel
- Need complex animations/gestures
- App Store rejections for performance
- Mobile becomes 80%+ of traffic

### Technical Debt

| # | Issue ID | Task | Effort | Risk | Benefit |
|---|----------|------|--------|------|---------|
| 1 | ISSUE-008 | **Refactor server.py** (5,900+ lines) | 1-2 weeks | 🟡 Med | Maintainability |
| 2 | ISSUE-009 | **Fixture import** - Use externalId not fuzzy matching | 4 hrs | 🟡 Med | Reliability |
| 3 | ISSUE-017.4 | **Consolidate socket events** | 4 hrs | 🟡 Med | Simpler client code |
| 4 | ISSUE-017.5 | **Socket.IO bidding** (replace HTTP POST) | 1 week | 🔴 High | Faster mobile bidding |
| 5 | STRESS-TEST | **Competitive bidding test mode** | 4 hrs | 🟡 Med | Realistic load testing |
| 6 | - | **E2E test suite expansion** | 4-5 days | 🟡 Med | Regression coverage, confidence |

### New Features

| # | Issue ID | Feature | Effort | Risk | Benefit |
|---|----------|---------|--------|------|---------|
| 1 | ISSUE-001 | **Manual score entry UI** | 4 hrs | 🟢 Low | Commissioners can fix scores |
| 2 | ISSUE-011 | **Auction history tab** | 4 hrs | 🟢 Low | Review all bids post-auction |
| 3 | ISSUE-010 | **Custom scoring rules** | 1 week | 🟡 Med | Flexibility per tournament |
| 4 | ISSUE-012 | **Email notifications** | 1 week | 🟡 Med | Invites, reminders, results |
| 5 | ISSUE-024 | **Auto-import fixtures** | 2 hrs | 🟢 Low | Removes manual step |
| 6 | ISSUE-026 | **Fixture template management** | 1 week | 🟢 Low | No redeploy for fixture updates |
| 7 | - | **Payment integration** (Stripe) | 2 weeks | 🟡 Med | Entry fees, charity donations |

### UI/UX Improvements

| # | Task | Effort | Risk | Benefit |
|---|------|--------|------|---------|
| 1 | ~~Demote/remove "Explore" button~~ | 30 min | 🟢 Low | ⏸️ Keep for now - useful for browsing, may expand for team stats later |
| 2 | ~~Team count preview on create~~ | 1 hr | 🟢 Low | ❌ Considered - not needed. Users see teams on LeagueDetail page |
| 3 | ~~Sticky tabs on mobile~~ | 1 hr | 🟢 Low | ✅ Done (Jan 17) - CompetitionDashboard tabs now sticky on scroll |
| 4 | Collapsible sections in LeagueDetail | 2 hrs | 🟢 Low | Less scrolling |
| 5 | ~~Cricket bat icons for football teams~~ | 15 min | 🟢 Low | ✅ Fixed (Jan 17) - Removed fallback icons; teams now show flag if available, otherwise just country name |

### Infrastructure

| # | Task | Effort | Risk | Benefit |
|---|------|--------|------|---------|
| 1 | Google Analytics | 1 hr | 🟢 Low | Usage insights |
| 2 | MongoDB Atlas backups | Config | 🟢 Low | Data protection (M10 includes) |
| 3 | ESLint warnings cleanup | 1 hr | 🟢 Low | Cleaner builds |

### Code Cleanup Pass

*Lint errors and code quality issues found during development - fix in a dedicated cleanup session*

✅ **COMPLETED January 17, 2026**

| File | Line | Error Code | Issue | Fix | Status |
|------|------|------------|-------|-----|--------|
| server.py | 198 | F541 | f-string without placeholders | Removed `f` prefix | ✅ Done |
| server.py | 427 | E722 | Bare `except:` clause | Changed to `except Exception:` | ✅ Done |
| server.py | 1398 | F841 | Unused variable `asset_names` | Deleted the line | ✅ Done |
| server.py | 6178 | E722 | Bare `except:` clause | Changed to `except Exception:` | ✅ Done |

**Effort:** 30 min  
**Risk:** 🟢 Low  
**When:** During a dedicated cleanup session, not mid-feature

---

## 🔵 FUTURE / BACKLOG

*Long-term roadmap items*

### Multi-Region Expansion

When significant user bases develop in other regions:

| Region | Trigger | Action |
|--------|---------|--------|
| US | 100+ active US users | Consider US Railway deployment |
| India | 100+ active India users | Consider Asia deployment |
| Europe | Already covered | EU-West serves all of Europe |

### Advanced Features

| Feature | Effort | Notes |
|---------|--------|-------|
| Native mobile apps (React Native) | 2-3 months | Only if Capacitor insufficient |
| Real-time leaderboards | 1 week | Live standings during matches |
| Social features | 2 weeks | Chat, trash talk, league forums |
| Tournament brackets | 2 weeks | Knockout-style competitions |
| API for third parties | 2 weeks | Let others build on platform |

---

## 📊 EMERGENT vs RAILWAY COMPARISON

### What Can Be Done in Emergent (Current Platform)

| Task | Confidence | Risk | Notes |
|------|------------|------|-------|
| Bug fixes | ✅ High | 🟢 Low | Full code access |
| UI changes | ✅ High | 🟢 Low | Hot reload works |
| Backend logic | ✅ High | 🟢 Low | Full code access |
| DB schema changes | ✅ High | 🟢 Low | MongoDB flexible |
| New API endpoints | ✅ High | 🟢 Low | FastAPI routing |
| Socket.IO changes | ✅ High | 🟡 Med | Need careful testing |
| Environment config | ✅ High | 🟢 Low | Via dashboard |

### What CANNOT Be Fixed in Emergent

| Issue | Why | Solution |
|-------|-----|----------|
| **UK user latency** | App hosted in US, can't change | Railway EU-West |
| **More than 2 pods** | Platform limitation | Railway (scalable) |
| **Regional hosting** | US-only | Railway (choose region) |
| **Custom server config** | Managed platform | Railway (full control) |

### Risk Assessment for Emergent Work

| Risk Level | Meaning | Examples |
|------------|---------|----------|
| 🟢 **Low** | Safe to do, easy to test/rollback | Config changes, UI tweaks, simple fixes |
| 🟡 **Medium** | Needs careful testing, some dependencies | Schema changes, socket logic, auth changes |
| 🔴 **High** | Could break production, hard to rollback | Major refactors, core flow changes |

**Recommendation:** Do 🟢 Low risk tasks in Emergent now. Save 🟡 Medium for post-migration when you have better monitoring. Avoid 🔴 High risk until after pilot.

---

## ✅ RECENTLY RESOLVED

| # | Issue | Summary | Solution | Date |
|---|-------|---------|----------|------|
| 1 | Redis limits | Connection exhaustion at scale | Upgraded to Essentials (256 conn) | Jan 2026 |
| 2 | Performance diagnosis | Identified US hosting as root cause | Stress testing + Emergent support | Jan 2026 |
| 3 | AFCON Data Fix | Kenya→Cameroon, fixtures corrected | Admin endpoints + CSV upload | Dec 2025 |
| 4 | ISSUE-023 | Bid input race condition | Read-only input + increment buttons | Dec 2025 |
| 5 | ISSUE-018 | Team selection showing all 74 clubs | Backend filter by competitionCode | Dec 2025 |
| 6 | Debug reports | Client-only → Server upload with IDs | MongoDB storage + query endpoint | Dec 2025 |
| 7 | Self-outbid | Users could raise own winning bid | Backend validation | Dec 2025 |
| 8 | Multi-pod Socket.IO | Sockets didn't sync across pods | Redis Cloud pub/sub | Dec 2025 |

---

## ❌ FAILED APPROACHES (Lessons Learned)

| Attempt | Result | Lesson |
|---------|--------|--------|
| MongoDB pool size increase | No improvement | Pool size wasn't the bottleneck |
| Remove diagnostic query (prod) | Made latency worse | Preview != Production behavior |
| Hybrid DB approach | Ruled out | App in US = UK users still have latency |
| Agent-created Atlas cluster | Unnecessary | Emergent provides managed MongoDB |

---

## 📁 RELATED DOCUMENTATION

**⚠️ AGENTS: READ THESE BEFORE WORKING ON THIS PROJECT**

| Document | Purpose | Critical Items |
|----------|---------|----------------|
| `/app/docs/archive/COMPREHENSIVE_PILOT_READINESS_ASSESSMENT.md` | Full pilot readiness analysis | Auth, backups, load testing, error tracking |
| `/app/docs/archive/ROLLBACK_AND_READINESS_REPORT.md` | Production readiness gaps | Auth security, Redis config, Sentry |
| `/app/docs/archive/CURRENT_BUILD_READINESS_REPORT.md` | Build validation | Known limitations section |
| `/app/docs/OPERATIONS_PLAYBOOK.md` | Operational procedures | Incident response, monitoring |
| `/app/MIGRATION_PLAN.md` | Railway migration details | Infrastructure setup |
| `/app/STRESS_TEST_REPORT.md` | Full performance analysis | Latency findings |
| `/app/AGENT_ONBOARDING_PROMPT.md` | System architecture reference | Database schema, endpoints |
| `/app/tests/multi_league_stress_test.py` | Load testing script | Usage instructions |

**Lesson from previous sessions:** Critical items were documented but forgotten between agent handoffs. If you're a new agent, READ the archive docs above - don't rediscover known issues.

---

## 🎯 IMMEDIATE NEXT ACTIONS

1. **User:** Finalize Railway migration timeline
2. **User:** Create MongoDB Atlas M10 in `europe-west2`
3. **User:** Confirm data migration approach (fresh vs import)
4. **After migration:** Run stress test to validate latency improvement
5. **After validation:** Proceed to pilot

---

**Document Version:** 3.0  
**Last Updated:** January 14, 2026

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Jan 16, 2026 | Complete reorganization by phase; Added mobile strategy; Added Emergent confidence/risk ratings |
| 2.1 | Dec 21, 2025 | Added stress test findings |
| 2.0 | Dec 2025 | Initial comprehensive list |
