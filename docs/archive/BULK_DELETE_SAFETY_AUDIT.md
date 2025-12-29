# Bulk Delete Safety Audit

## 🔍 Database Relationship Analysis

### Collections That Reference Leagues

1. **league_participants** (via `leagueId`)
   - Stores which users are participating in which leagues
   - **Action**: CASCADE DELETE

2. **auctions** (via `leagueId`)
   - One auction per league
   - **Action**: CASCADE DELETE
   
3. **standings** (via `leagueId`)
   - League standings/leaderboard
   - **Action**: CASCADE DELETE

4. **fixtures** (via `leagueId`)
   - League-specific fixtures
   - **Note**: Some fixtures have NO leagueId (shared fixtures)
   - **Action**: DELETE only fixtures with matching leagueId

### Collections That Reference Auctions

1. **bids** (via `auctionId`)
   - Individual bid records from the auction
   - **Action**: CASCADE DELETE (when auction is deleted)

---

## ✅ SAFE TO DELETE

### Cascade Chain
```
League (deleted)
  ├─> league_participants (deleted)
  ├─> auctions (deleted)
  │     └─> bids (deleted)
  ├─> standings (deleted)
  └─> fixtures with leagueId (deleted)
```

### What's NOT Affected
- ✅ **users**: User accounts preserved
- ✅ **assets**: Clubs/players remain in database
- ✅ **Shared fixtures**: Fixtures without leagueId remain
- ✅ **Other leagues**: No cross-league references

---

## 🛡️ SAFETY RULES

### Rule 1: Status Check
**Block deletion if league status = "active"**
```javascript
if (league.status === "active") {
  throw Error("Cannot delete league with auction in progress")
}
```
**Reason**: Users might be actively bidding

### Rule 2: Authorization
**Only commissioner can delete their own leagues**
```javascript
if (league.commissionerId !== user.id) {
  throw Error("Unauthorized - only commissioner can delete")
}
```
**Reason**: Prevent users from deleting others' leagues

### Rule 3: Confirmation
**Require explicit confirmation from user**
- UI must show warning
- User must confirm deletion
- Show what will be deleted (participants, bids, etc.)

### Rule 4: Cascade Delete
**Delete in this order:**
```
1. bids (via auctionId)
2. auctions (via leagueId)
3. league_participants (via leagueId)
4. standings (via leagueId)
5. fixtures where leagueId = league.id
6. league (main record)
```
**Reason**: Avoid orphaned records

---

## 🎯 IMPLEMENTATION PLAN

### Backend Endpoint
```
DELETE /api/leagues/bulk
Body: { leagueIds: string[] }
Authorization: JWT token (user.id)
```

### Validation Steps
1. ✅ Verify user is authenticated
2. ✅ For each league:
   - Verify league exists
   - Verify user is commissioner
   - Verify status is NOT "active"
3. ✅ Return errors for any leagues that can't be deleted

### Deletion Steps
```python
for league_id in league_ids:
    # 1. Get auction IDs
    auctions = await db.auctions.find({'leagueId': league_id}).to_list(100)
    auction_ids = [a['id'] for a in auctions]
    
    # 2. Delete bids
    for auction_id in auction_ids:
        await db.bids.delete_many({'auctionId': auction_id})
    
    # 3. Delete auctions
    await db.auctions.delete_many({'leagueId': league_id})
    
    # 4. Delete participants
    await db.league_participants.delete_many({'leagueId': league_id})
    
    # 5. Delete standings
    await db.standings.delete_many({'leagueId': league_id})
    
    # 6. Delete fixtures
    await db.fixtures.delete_many({'leagueId': league_id})
    
    # 7. Delete league
    await db.leagues.delete_one({'id': league_id})
```

---

## 🖼️ Frontend UI

### My Competitions Page
```
[ ] Select All
[ ] League 1 (pending) - 2 participants
[ ] League 2 (completed) - 4 participants, 150 bids
[X] League 3 (pending) - 1 participant
[ ] League 4 (active) - LOCKED (auction in progress)

[Delete Selected (1)]
```

### Confirmation Modal
```
⚠️ Delete 1 League?

This will permanently delete:
- 1 league
- 1 participant
- 0 auctions
- 0 bids

This action cannot be undone.

[Cancel] [Delete Forever]
```

---

## 🧪 TESTING CHECKLIST

### Test Cases
- [ ] Delete pending league (should work)
- [ ] Delete completed league (should work)
- [ ] Try to delete active league (should be blocked)
- [ ] Try to delete another user's league (should be blocked)
- [ ] Delete multiple leagues at once
- [ ] Verify cascade delete (all related records removed)
- [ ] Verify shared fixtures NOT deleted
- [ ] Verify user account NOT affected

---

## ✅ CONCLUSION

**Bulk delete is SAFE to implement** with the following safeguards:

1. ✅ Block deletion of active leagues
2. ✅ Verify commissioner authorization
3. ✅ Cascade delete all related records
4. ✅ Require user confirmation
5. ✅ Return detailed feedback (what was deleted)

**No risk of:**
- ❌ Affecting other users' data
- ❌ Breaking shared resources (assets, shared fixtures)
- ❌ Leaving orphaned records (cascade delete handles this)
- ❌ Accidentally deleting active auctions (blocked)

**Estimated Implementation Time: 30 minutes**
