// Backfill leagues
db.leagues.updateMany({ sportKey: { $exists: false } }, { $set: { sportKey: "football" } });

// Upsert sports: football + cricket
db.sports.updateOne(
  { key: "football" },
  { $set: {
    key: "football",
    name: "Football",
    assetType: "CLUB",
    uiHints: { assetLabel: "Club", assetPlural: "Clubs" },
    auctionTemplate: { bidTimerSeconds: 20, antiSnipeSeconds: 5, minIncrement: 1 },
    scoringSchema: { type: "match", rules: { win: 3, draw: 1, goal: 1 } }
  }}, { upsert: true }
);

db.sports.updateOne(
  { key: "cricket" },
  { $set: {
    key: "cricket",
    name: "Cricket",
    assetType: "PLAYER",
    uiHints: { assetLabel: "Player", assetPlural: "Players" },
    auctionTemplate: { bidTimerSeconds: 20, antiSnipeSeconds: 5, minIncrement: 1 },
    scoringSchema: {
      type: "perPlayerMatch",
      rules: { run: 1, wicket: 25, catch: 10, stumping: 15, runOut: 10 },
      milestones: {
        halfCentury: { enabled: true, threshold: 50, points: 10 },
        century: { enabled: true, threshold: 100, points: 25 },
        fiveWicketHaul: { enabled: true, threshold: 5, points: 25 }
      }
    }
  }}, { upsert: true }
);

// Assets index (per sport)
db.assets.createIndex({ sportKey: 1, externalId: 1 }, { unique: true });