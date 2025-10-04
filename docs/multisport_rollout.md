# Multi-Sport Rollout Guide

## Overview

The Friends of Pifa platform supports multiple sports through a feature flag system. This document outlines how to manage sport availability and provides rollback procedures.

## Feature Flag System

### Environment Variable Control
Sports availability is controlled via environment variables:

```bash
# Enable/disable cricket functionality
SPORTS_CRICKET_ENABLED=true   # Enable cricket
SPORTS_CRICKET_ENABLED=false  # Disable cricket
```

### Current Supported Sports
- **Football** (UEFA Champions League clubs) - Always available
- **Cricket** (IPL players) - Controlled by `SPORTS_CRICKET_ENABLED` flag

---

## Instant Cricket Rollback

### Emergency Disable Procedure

If you need to immediately disable cricket functionality (e.g., due to issues, user feedback, or maintenance):

#### Step 1: Update Environment Variable
```bash
# In backend/.env file, change:
SPORTS_CRICKET_ENABLED=false
```

#### Step 2: Restart Backend Service
```bash
# Using supervisor (recommended)
sudo supervisorctl restart backend

# Or using systemctl (if applicable)
sudo systemctl restart your-backend-service
```

#### Step 3: Verify Cricket is Disabled
```bash
# Test sports endpoint - cricket should not appear
curl -s "https://your-domain/api/sports" | grep -i cricket
# Should return no results when disabled

# Test create league UI - cricket option should be hidden
# Visit /create-league and verify sport dropdown only shows Football
```

### Effects of Disabling Cricket

**Immediately Disabled:**
- ❌ Cricket option removed from league creation
- ❌ Cricket leagues cannot be created via API
- ❌ Cricket scoring uploads rejected
- ❌ Cricket-specific UI elements hidden

**Still Functional:**
- ✅ Existing cricket leagues remain accessible
- ✅ Existing cricket data preserved
- ✅ Cricket leaderboards still viewable
- ✅ Football functionality completely unaffected

**Re-enable Anytime:**
- Set `SPORTS_CRICKET_ENABLED=true` and restart
- All cricket functionality immediately restored
- No data loss or corruption

---

## Optional Cleanup (Advanced)

### Remove Cricket Assets (Optional)

If you want to completely remove cricket players from the database:

```javascript
// MongoDB cleanup script
// WARNING: This removes all cricket player data permanently

// Connect to your MongoDB instance
use your_database_name;

// Remove cricket assets
db.assets.deleteMany({ sportKey: "cricket" });

// Remove cricket scoring data (optional)
db.league_stats.deleteMany({ /* filter for cricket leagues */ });
db.cricket_leaderboard.deleteMany({});

// Verify cleanup
db.assets.countDocuments({ sportKey: "cricket" }); // Should return 0
```

### Keep Sports Configuration (Recommended)

**Do NOT remove the sports.cricket document:**
```javascript
// DON'T DO THIS (unless completely removing cricket forever)
db.sports.deleteOne({ key: "cricket" });
```

**Why keep it:**
- Harmless when cricket is disabled
- Contains valuable configuration (scoring rules, UI hints)
- Required for instant re-enabling
- Preserves custom league scoring overrides

---

## Rollout Best Practices

### Gradual Rollout Strategy

1. **Test Environment First**
   ```bash
   # Enable cricket in test/staging
   SPORTS_CRICKET_ENABLED=true
   ```

2. **Limited Production Rollout**
   ```bash
   # Enable for specific user groups or during off-peak hours
   SPORTS_CRICKET_ENABLED=true
   ```

3. **Monitor and Validate**
   - Check error logs for cricket-related issues
   - Verify scoring calculations with sample data
   - Monitor user feedback and support requests

4. **Full Rollout or Rollback**
   - Continue with full availability, or
   - Instant disable using procedure above

### Monitoring Cricket Health

**Key Metrics to Watch:**
- Cricket league creation rate vs. football
- Scoring upload success/failure rates
- User engagement with cricket features
- Error rates in cricket-specific endpoints

**Health Check Endpoints:**
```bash
# Verify cricket availability
GET /api/sports

# Test cricket league creation
POST /api/leagues (with sportKey: "cricket")

# Check cricket assets
GET /api/assets?sportKey=cricket

# Validate scoring system
POST /api/scoring/{cricketLeagueId}/ingest
```

---

## Communication Templates

### For Users (Cricket Disabled)

> **Notice: Cricket Temporarily Unavailable**
> 
> Cricket functionality is currently disabled for maintenance. 
> Football auctions continue to work normally.
> 
> We'll re-enable cricket soon. Thank you for your patience!

### For Commissioners (Cricket Issues)

> **Cricket League Management Notice**
> 
> If you're experiencing issues with cricket scoring or player data:
> 
> 1. Your existing cricket leagues remain safe
> 2. Scoring data is preserved
> 3. You can continue managing football leagues normally
> 4. Cricket will be restored shortly
> 
> Contact support for urgent cricket league needs.

---

## Troubleshooting

### Common Rollback Scenarios

**"Cricket leagues showing errors"**
- Disable cricket: `SPORTS_CRICKET_ENABLED=false`
- Restart backend
- Cricket leagues become read-only but remain accessible

**"Scoring uploads failing"**
- Check cricket flag is enabled
- Verify CSV format matches documentation
- Test with sample data first

**"UI showing mixed states"**
- Clear browser cache
- Restart frontend service
- Verify environment variable took effect

### Logs to Monitor

```bash
# Backend startup logs
tail -f /var/log/supervisor/backend.*.log | grep -i cricket

# Look for:
INFO:server:Cricket feature enabled: True/False
```

### Emergency Contacts

- **System Administrator**: For database/infrastructure issues
- **Development Team**: For cricket-specific bugs
- **Product Team**: For user communication and rollout decisions

---

*Last updated: November 2024*  
*Version: 1.0*