# Sport X – Issues & Actions Summary (Decision View)
**Updated: 21 December 2025**

| Category | Item | What Users Experience | What We're Doing | When | Risk | Why This Matters |
|---|---|---|---|---|---|---|
| ✅ **RESOLVED** | Team selection clarity (ISSUE-018) | Commissioners see too many teams | ~~Auto-filter teams by competition~~ **FIXED** - Backend now filters by competitionCode | **Done** | - | Prevents setup errors |
| ✅ **RESOLVED** | AFCON Data Error | Kenya shown instead of Cameroon, wrong fixtures | Admin endpoints created, asset updated in production, corrected fixtures CSV uploaded | **Done** | - | Live tournament data accuracy |
| ✅ **RESOLVED** | Bid input race condition (ISSUE-023) | Rapid bidding causes typed bids to append/inflate | Made input read-only, added +1m/+2m buttons | **Done** | - | Prevents accidental inflated bids |
| 🔍 **Monitoring** | Roster not updating correctly (ISSUE-016) | Winning teams but roster looks full or wrong | Monitoring in larger group tests before attempting fix | Observe | Low | Previous fix broke countdown - needs careful analysis |
| 🔍 **Monitoring** | Roster "lag" (ISSUE-021) | Roster slow or inconsistent during auctions | Same root cause as ISSUE-016 | Observe | Low | One root cause, multiple symptoms |
| 🔍 **Monitoring** | "Couldn't place bid" (ISSUE-019) | Button pressed, bid rejected | Likely expected behaviour (roster full) | Observe | Low | Avoid fixing expected behaviour unnecessarily |
| 🔍 **Monitoring** | Same team shown twice (ISSUE-020) | Team reappears in auction | No recurrence reported | Observe | Low | Reduce confusion without breaking auction logic |
| 🔍 **Monitoring** | "Unknown" manager names (ISSUE-022) | Some managers show as "Unknown" | Not recurring in recent tests | Observe | Low | Better user identification |
| 🟠 **Improve Soon** | Auction clarity (winning/outbid) | Hard to tell if you're currently winning | Add clear "Winning / Outbid" indicator | Soon | Low | Big UX win during fast bidding |
| 🟠 **Improve Soon** | Bid context | Users unsure of current bid | Show "Current bid" above input | Soon | Low | Fewer mistakes, clearer bidding |
| 🟠 **Improve Soon** | Mobile usability | Screens feel busy | Reduce button clutter, sticky tabs | Soon | Low | Better mobile experience |
| 🟠 **Improve Soon** | Error visibility (ISSUE-003) | Issues only found via user reports | Enable Sentry monitoring (code ready, needs DSN) | Soon | Low | Catch problems early |
| 🟠 **Improve Soon** | Commissioner auth checks (ISSUE-002) | Missing authorization on some endpoints | Add require_commissioner checks | Soon | Medium | Security improvement |
| 🔵 **Post-Pilot** | Performance tuning (ISSUE-017) | Slight bid delay at scale | Reduce backend DB round-trips | After pilot | Medium | Optimisation, not blocking |
| 🔵 **Post-Pilot** | Real-time bidding upgrade | Mobile bids rely on HTTP | Move bidding fully to sockets | After pilot | Higher | Faster, more robust bidding |
| 🔵 **Post-Pilot** | Codebase cleanup (ISSUE-008) | Large server file (5900+ lines) | Modularise backend | After pilot | Medium | Maintainability |
| 🔵 **Post-Pilot** | New features | Missing history, scoring UI, payments | Build once core UX proven | After pilot | Medium | Avoid feature creep |
| 🔵 **Post-Pilot** | Analytics & backups | Limited visibility & resilience | Add analytics & backups | After pilot | Low | Operational hygiene |

---

## Progress Summary (19 Dec → 21 Dec 2025)

### ✅ Resolved This Week
1. **ISSUE-018: Team Selection UX** - Premier League now shows exactly 20 teams, not 74
2. **AFCON Data Fix** - Kenya replaced with Cameroon in production, corrected fixtures uploaded (36 group matches)
3. **ISSUE-023: Bid Input Race Condition** - Input now read-only with +1m, +2m, +5m, +10m, +20m, +50m buttons

### 🔍 Moved to Monitoring
- ISSUE-022 (Unknown managers) - Not recurring in recent tests
- ISSUE-016, 019, 020, 021 - Awaiting larger group test data

### 📋 Upcoming
- AFCON knockout fixtures (after Dec 31 group stage completion)
- Sentry monitoring setup (needs DSN)
- UI improvements (winning/outbid indicator, bid context label)
