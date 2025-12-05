# Operations Playbook
## Production Hardening - Days 12-13

## Overview
Comprehensive operational procedures for managing the multi-sport auction platform during the 150-user pilot. Quick reference for troubleshooting, monitoring, and incident response.

---

## Quick Reference

### Service Management

**Check Status**:
```bash
sudo supervisorctl status
```

**Restart Services**:
```bash
# Restart all
sudo supervisorctl restart all

# Restart individual
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart mongodb
```

**View Logs**:
```bash
# Backend logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/backend.err.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log

# MongoDB logs
tail -f /var/log/supervisor/mongodb.out.log
```

### Health Checks

**API Health**:
```bash
curl https://sport-predictor-9.preview.emergentagent.com/api/health
```

**Expected Response** (Healthy):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T00:00:00Z",
  "services": {
    "database": "healthy",
    "api": "healthy"
  }
}
```

**Frontend Status**:
```bash
curl -I https://sport-predictor-9.preview.emergentagent.com
# Should return 200 OK
```

---

## Common Issues & Solutions

### Issue 1: Backend Not Responding

**Symptoms**:
- API calls return 502/503
- Health check fails
- Frontend shows connection errors

**Diagnosis**:
```bash
# Check if backend is running
sudo supervisorctl status backend

# Check backend logs
tail -50 /var/log/supervisor/backend.err.log
```

**Solutions**:
1. **Restart backend**:
   ```bash
   sudo supervisorctl restart backend
   sleep 3
   curl https://sport-predictor-9.preview.emergentagent.com/api/health
   ```

2. **If restart fails**, check for:
   - Syntax errors in code
   - Missing dependencies
   - Port conflicts
   - Database connection issues

3. **Check MongoDB**:
   ```bash
   sudo supervisorctl status mongodb
   # If not running
   sudo supervisorctl start mongodb
   ```

### Issue 2: Frontend Not Loading

**Symptoms**:
- Blank page
- Build errors in console
- 404 errors

**Diagnosis**:
```bash
sudo supervisorctl status frontend
tail -50 /var/log/supervisor/frontend.err.log
```

**Solutions**:
1. **Restart frontend**:
   ```bash
   sudo supervisorctl restart frontend
   ```

2. **Clear browser cache**:
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
   - Or clear cache in browser settings

3. **Check for build errors**:
   ```bash
   cd /app/frontend
   yarn build
   # Look for compilation errors
   ```

### Issue 3: Database Connection Issues

**Symptoms**:
- Health check shows database: "unhealthy"
- API returns 503 errors
- Auctions/leagues not loading

**Diagnosis**:
```bash
# Check MongoDB status
sudo supervisorctl status mongodb

# Check MongoDB logs
tail -50 /var/log/supervisor/mongodb.out.log

# Try connecting directly
mongo mongodb://localhost:27017/test_database --eval "db.users.countDocuments({})"
```

**Solutions**:
1. **Restart MongoDB**:
   ```bash
   sudo supervisorctl restart mongodb
   sleep 5
   mongo mongodb://localhost:27017/test_database --eval "db.stats()"
   ```

2. **Check disk space**:
   ```bash
   df -h /app
   # If > 90% full, cleanup needed
   ```

3. **Restore from backup if corrupted**:
   ```bash
   /app/scripts/restore_mongodb.sh latest
   ```

### Issue 4: Socket.IO Connection Issues

**Symptoms**:
- Real-time updates not working
- Auction bidding frozen
- Users see "Connection lost" toast

**Diagnosis**:
- Check browser console for WebSocket errors
- Check backend logs for Socket.IO errors
- Verify `/api/socket.io` path is accessible

**Solutions**:
1. **Users**: Wait 30 seconds for auto-reconnect
2. **If persistent**, restart backend:
   ```bash
   sudo supervisorctl restart backend
   ```

3. **Check firewall/proxy** settings for WebSocket support

### Issue 5: Slow Performance

**Symptoms**:
- API calls taking > 1 second
- Page loads slowly
- Auction updates laggy

**Diagnosis**:
```bash
# Check system resources
top
# Look for high CPU/memory usage

# Check database performance
mongo mongodb://localhost:27017/test_database --eval "db.currentOp()"

# Check API response times
curl -w "@-" -o /dev/null -s https://sport-predictor-9.preview.emergentagent.com/api/sports <<< "time_total: %{time_total}s"
```

**Solutions**:
1. **Check indexes**:
   ```bash
   python3 /app/scripts/optimize_database_indexes.py
   ```

2. **Restart services** (clears memory):
   ```bash
   sudo supervisorctl restart all
   ```

3. **Check concurrent users** (via logs or monitoring)

### Issue 6: Authentication Problems

**Symptoms**:
- Magic links not working
- Users can't sign in
- JWT token errors

**Diagnosis**:
```bash
# Check backend logs for auth errors
grep -i "auth\|jwt" /var/log/supervisor/backend.err.log | tail -20

# Test magic link generation
curl -X POST https://sport-predictor-9.preview.emergentagent.com/api/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

**Solutions**:
1. **Check JWT_SECRET_KEY** in /app/backend/.env
2. **Verify magic_links collection**:
   ```bash
   mongo mongodb://localhost:27017/test_database --eval "db.magic_links.countDocuments({})"
   ```

3. **Clear old magic links**:
   ```bash
   mongo mongodb://localhost:27017/test_database --eval "db.magic_links.deleteMany({used: true})"
   ```

---

## Monitoring

### Daily Health Checks

**Morning Checklist** (5 minutes):
- [ ] Check all services running: `sudo supervisorctl status`
- [ ] Test API health: `curl /api/health`
- [ ] Check disk space: `df -h /app`
- [ ] Review error logs: `grep ERROR /var/log/supervisor/*.log | tail -20`
- [ ] Verify last backup: `ls -lt /app/backups/mongodb/ | head -3`

### During Pilot (Every 2 hours):
- [ ] Check health endpoint
- [ ] Monitor active users (if analytics available)
- [ ] Review error rates (Sentry dashboard if configured)
- [ ] Check system resources: `top`

### Key Metrics to Watch

**System**:
- CPU usage: Should be < 70%
- Memory: Should be < 80%
- Disk space: Should be < 85%

**Application**:
- API response time: < 500ms (P95)
- Error rate: < 1%
- Active Socket.IO connections: Monitor for leaks

---

## Backup & Recovery

### Manual Backup Before Critical Operations

```bash
# Before major changes
/app/scripts/backup_mongodb.sh

# Verify backup
/app/scripts/restore_mongodb.sh list
```

### Emergency Recovery

**If database corrupted**:
```bash
# Stop backend
sudo supervisorctl stop backend

# Restore latest backup
/app/scripts/restore_mongodb.sh latest

# Start backend
sudo supervisorctl start backend

# Verify
curl https://sport-predictor-9.preview.emergentagent.com/api/health
```

---

## Incident Response

### Severity Levels

**P0 - Critical (< 15 min response)**:
- Platform completely down
- Database data loss
- Security breach

**P1 - High (< 1 hour response)**:
- Major feature broken (auctions, auth)
- Affecting > 50% of users
- Performance degradation > 5x normal

**P2 - Medium (< 4 hours)**:
- Minor feature broken
- Affecting < 50% of users
- Workaround available

**P3 - Low (< 24 hours)**:
- UI issues
- Minor bugs
- Enhancement requests

### Incident Response Steps

1. **Acknowledge**: Confirm incident and notify team
2. **Assess**: Determine severity and impact
3. **Diagnose**: Use this playbook to identify root cause
4. **Mitigate**: Apply immediate fix or workaround
5. **Communicate**: Update users if needed
6. **Resolve**: Fully fix the issue
7. **Document**: Record what happened and how it was fixed
8. **Post-Mortem**: Learn and improve (for P0/P1)

---

## Deployment Procedures

### Code Updates

1. **Test locally** or in staging
2. **Backup database**:
   ```bash
   /app/scripts/backup_mongodb.sh
   ```

3. **Deploy changes** (via git or file upload)

4. **Restart affected services**:
   ```bash
   # Backend changes
   sudo supervisorctl restart backend

   # Frontend changes
   sudo supervisorctl restart frontend

   # Both
   sudo supervisorctl restart all
   ```

5. **Verify deployment**:
   ```bash
   curl /api/health
   # Test key functionality
   ```

6. **Monitor** for 10-15 minutes after deployment

### Database Migrations

1. **Backup first** (critical!)
2. **Test migration script** on copy of data
3. **Run during low-traffic period**
4. **Monitor closely**
5. **Have rollback plan** ready

---

## Stakeholder Demo Preparation

### 1 Day Before Demo

- [ ] Run full backup: `/app/scripts/backup_mongodb.sh`
- [ ] Test all key features
- [ ] Check all services running
- [ ] Review error logs (clean slate)
- [ ] Prepare test data if needed
- [ ] Test on different browsers/devices

### Demo Day Checklist

**1 Hour Before**:
- [ ] Restart all services (fresh state)
- [ ] Verify health endpoint
- [ ] Test authentication flow
- [ ] Test auction flow end-to-end
- [ ] Check frontend loads quickly
- [ ] Clear browser cache on demo machine

**During Demo**:
- Keep terminal open with health checks
- Have backup plan if demo breaks
- Monitor system resources

**After Demo**:
- Review logs for any errors
- Document any issues found
- Backup database with demo data

---

## Contact Information

**Emergency Contacts**: [Add team contacts]
**Escalation Path**: [Define escalation]

**Key Resources**:
- Documentation: `/app/docs/`
- Scripts: `/app/scripts/`
- Logs: `/var/log/supervisor/`
- Backups: `/app/backups/mongodb/`

**External Services**:
- Sentry (if configured): [Add URL]
- Monitoring: [Add URLs]
- Status Page: [Add URL if exists]

---

## Appendix: Useful Commands

### System Information
```bash
# System resources
top
htop  # if available
free -h  # Memory
df -h   # Disk space

# Network
netstat -tulpn | grep LISTEN  # Open ports
ss -tulpn  # Alternative

# Processes
ps aux | grep python  # Python processes
ps aux | grep node    # Node processes
```

### Database Commands
```bash
# MongoDB shell
mongo mongodb://localhost:27017/test_database

# Count documents
db.users.countDocuments({})
db.leagues.countDocuments({})
db.auctions.countDocuments({})

# Find recent records
db.bids.find().sort({createdAt: -1}).limit(5)

# Check indexes
db.bids.getIndexes()
```

### Log Analysis
```bash
# Find errors
grep -i error /var/log/supervisor/*.log

# Count errors by type
grep ERROR /var/log/supervisor/backend.err.log | cut -d' ' -f4- | sort | uniq -c | sort -rn

# Monitor logs in real-time
tail -f /var/log/supervisor/backend.out.log | grep -i error
```

---

**Last Updated**: 2025-11-23  
**Version**: 1.0  
**Maintainer**: Operations Team
