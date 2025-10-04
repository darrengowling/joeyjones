# Friends of Pifa Documentation

Welcome to the Friends of Pifa multi-sport auction platform documentation.

## 📚 Available Documentation

### Cricket Features
- **[Cricket Scoring System](cricket_scoring.md)** - Complete guide to cricket scoring, CSV format, custom rules, and API reference

### Multi-Sport Management  
- **[Multi-Sport Rollout Guide](multisport_rollout.md)** - Feature flag management, instant cricket disable/enable, and rollback procedures

## 🏏 Quick Start - Cricket

### For Commissioners
1. **Create Cricket League**: Select "Cricket" from sport dropdown
2. **Upload Scores**: Use CSV format from [cricket_scoring.md](cricket_scoring.md)  
3. **Customize Rules**: Use League Settings > Advanced: Scoring (Cricket)

### For Administrators
1. **Enable Cricket**: Set `SPORTS_CRICKET_ENABLED=true` in backend/.env
2. **Disable Cricket**: Set `SPORTS_CRICKET_ENABLED=false` and restart backend
3. **Seed Players**: Run `python scripts/seed_cricket_players.py`

## ⚽ Football Features

Football functionality is always available and includes:
- UEFA Champions League clubs
- Real-time auctions with anti-snipe protection
- Comprehensive scoring system
- League management and standings

## ✅ Setup & Verification Checklist

### Enable Cricket (Optional)
```bash
# Enable cricket (optional)
SPORTS_CRICKET_ENABLED=true

# Seed players
python scripts/seed_cricket_players.py

# API sanity
curl /api/sports
curl "/api/assets?sportKey=cricket&page=1&pageSize=20"

# Manual smoke
# 1) Create Football league → run quick auction (unchanged)
# 2) Create Cricket league → auction lists players  
# 3) Upload sample CSV → leaderboard = 74, 97, 136

# Sample CSV for step 3 (creates fresh match data):
# matchId,playerExternalId,runs,wickets,catches,stumpings,runOuts
# M1,P001,54,0,1,0,0
# M1,P002,12,3,0,0,1  
# M1,P003,101,0,0,0,0
#
# Expected individual match points: P001=74, P002=97, P003=136
# (Note: Total leaderboard may show higher if previous matches exist)
```

**Expected Results:**
- Both sports work correctly
- Football unchanged by default (36 clubs, "Club" labels)  
- Cricket available when enabled (20 players, "Player" labels)
- /api/sports returns both Football (CLUB) and Cricket (PLAYER) when enabled

## 🚨 Emergency Procedures

**Instantly Disable Cricket:**
```bash
# 1. Edit backend/.env
SPORTS_CRICKET_ENABLED=false

# 2. Restart
sudo supervisorctl restart backend

# 3. Verify - cricket should not appear
curl /api/sports
```

## 📞 Support

- **Cricket Scoring Issues**: See [cricket_scoring.md](cricket_scoring.md) troubleshooting
- **Feature Flag Problems**: See [multisport_rollout.md](multisport_rollout.md) 
- **General Platform**: Contact your system administrator

---

*For technical implementation details, see the source code and API documentation.*