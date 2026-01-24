# Sentry Error Tracking Setup Guide
## Production Hardening - Day 6

## Overview
Sentry is configured for comprehensive error tracking across both backend (FastAPI) and frontend (React). This provides real-time error monitoring, performance tracking, and user session replay for the 150-user pilot.

## Quick Start

### 1. Get Sentry DSN

**Option A: Use Sentry.io (Recommended)**
1. Sign up at https://sentry.io (free tier: 5K errors/month)
2. Create a new project:
   - Backend: Select "Python" → "FastAPI"
   - Frontend: Select "JavaScript" → "React"
3. Copy the DSN from project settings

**Option B: Self-Hosted Sentry**
```bash
# Install Sentry using Docker
git clone https://github.com/getsentry/self-hosted.git
cd self-hosted
./install.sh
```

### 2. Configure Backend

Update `/app/backend/.env`:
```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=pilot  # or production, staging, etc.
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions for performance monitoring
```

### 3. Configure Frontend

Update `/app/frontend/.env`:
```bash
REACT_APP_SENTRY_DSN=https://your-dsn@sentry.io/project-id
REACT_APP_SENTRY_ENVIRONMENT=pilot
REACT_APP_SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 4. Restart Services

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### 5. Test Error Tracking

**Backend Test:**
```bash
# Trigger a test error
curl -X POST https://speedrail.preview.emergentagent.com/api/test-error
```

**Frontend Test:**
Open browser console and run:
```javascript
throw new Error("Test error for Sentry");
```

Check Sentry dashboard - errors should appear within seconds.

## Features Configured

### Backend (FastAPI)
✅ Automatic exception capture
✅ API endpoint monitoring
✅ MongoDB query tracking
✅ Performance tracing (10% sample rate)
✅ Request breadcrumbs
✅ Stack traces with context

### Frontend (React)
✅ JavaScript error capture
✅ Unhandled promise rejections
✅ API call tracking
✅ User session replay (10% sessions, 100% on error)
✅ Performance monitoring
✅ User context tracking (email, ID)
✅ Navigation breadcrumbs

## What Gets Tracked

### Automatically Captured
- Uncaught exceptions
- Unhandled promise rejections
- API errors (4xx, 5xx)
- Network failures
- React component errors

### Manual Tracking (using utilities)
```javascript
// In React components
import { captureException, addBreadcrumb } from './utils/sentry';

// Capture custom error
try {
  // risky operation
} catch (error) {
  captureException(error, { context: 'League creation' });
}

// Add navigation breadcrumb
addBreadcrumb('User clicked Create League button', { leagueType: 'cricket' }, 'ui');
```

### User Context
Automatically tracks:
- User ID
- Email (for authenticated users)
- Login/logout events
- User journey through breadcrumbs

## Privacy & Security

### PII (Personally Identifiable Information)
- ❌ `send_default_pii=False` - Passwords, tokens NOT sent
- ✅ Only user ID and email tracked (required for debugging)
- ✅ Session replay masks all text by default

### Data Retention
- Sentry.io free tier: 90 days
- Self-hosted: Configurable

## Monitoring Dashboard

### Key Metrics to Watch
1. **Error Rate**: Should be < 1% of total requests
2. **Response Time**: P95 should be < 500ms
3. **Unhandled Errors**: Should be 0 (all errors should be caught)
4. **User Impact**: How many users affected by each error

### Alerts
Configure in Sentry dashboard:
- **Critical**: Email on any error (during pilot)
- **Warning**: Slack notification for > 10 errors/hour
- **Performance**: Alert if P95 > 1000ms

## Common Issues

### Error: "Sentry DSN not configured"
- Check `.env` files have correct `SENTRY_DSN`
- Restart services after updating `.env`
- Verify DSN format: `https://key@sentry.io/project-id`

### Errors Not Appearing in Sentry
1. Check Sentry dashboard: Project Settings → Client Keys
2. Verify DSN is correct
3. Check network tab - should see POST to `sentry.io/api/`
4. Check Sentry quota (free tier limits)

### Too Many Errors
- Filter noisy errors in Sentry: Settings → Inbound Filters
- Adjust sample rates in `.env` files
- Add custom `beforeSend` filters (see `/app/frontend/src/index.js`)

## Testing Checklist

Before pilot launch:
- [ ] Backend errors captured (test with invalid API call)
- [ ] Frontend errors captured (test with console error)
- [ ] User context set correctly (check Sentry event details)
- [ ] Performance monitoring working (check transactions)
- [ ] Alerts configured (email/Slack)
- [ ] Team has access to Sentry dashboard

## Cost Considerations

### Sentry.io Free Tier
- 5,000 errors/month
- 10,000 performance units/month
- 1 project
- 90-day retention

**For 150-user pilot**: Free tier should be sufficient

### If You Exceed Free Tier
- **Option 1**: Upgrade to Team plan ($26/month)
- **Option 2**: Reduce sample rates (set to 0.01 = 1%)
- **Option 3**: Self-host Sentry (free but requires maintenance)

## Integration with Load Testing

During load tests, monitor Sentry for:
- Spike in errors → System overload
- Slow transactions → Performance bottlenecks
- Timeout errors → Database/API issues

## Production Readiness

✅ **Ready for 150-user pilot**:
- Error tracking: Active
- Performance monitoring: Active
- User context: Tracked
- Session replay: Configured
- Alerts: Ready to configure

🎯 **Next Steps**:
1. Configure alert rules in Sentry dashboard
2. Add team members to Sentry project
3. Document common errors and solutions
4. Set up weekly error review process

## Support

**Sentry Documentation**: https://docs.sentry.io
**Sentry Status**: https://status.sentry.io
**Community**: https://github.com/getsentry/sentry/discussions
