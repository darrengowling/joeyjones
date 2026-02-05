# MongoDB Backup & Restore Guide
## Production Hardening - Day 8

## Overview
Automated backup system for MongoDB with daily backups, 7-day retention, and quick restore capabilities. Essential for data protection during the 150-user pilot.

---

## Quick Commands

### Manual Backup
```bash
/app/scripts/backup_mongodb.sh
```

### List Backups
```bash
/app/scripts/restore_mongodb.sh list
```

### Restore Latest Backup
```bash
/app/scripts/restore_mongodb.sh latest
```

### Restore Specific Backup
```bash
/app/scripts/restore_mongodb.sh backup_test_database_20251122_234902
```

---

## Setup Automated Backups

### Option 1: Automated Daily Backups (Recommended)
```bash
/app/scripts/setup_backup_cron.sh
```

This creates a cron job that runs daily at 2 AM.

### Option 2: Manual Scheduling
Edit crontab manually:
```bash
crontab -e
```

Add this line:
```
0 2 * * * cd /app && MONGO_URL=mongodb://localhost:27017 DB_NAME=test_database /app/scripts/backup_mongodb.sh >> /app/backups/mongodb/cron.log 2>&1
```

---

## Backup Strategy

### What Gets Backed Up
- **Full database dump** of `test_database`
- All collections (users, leagues, auctions, bids, fixtures, assets, etc.)
- Indexes
- Configuration

### Backup Location
```
/app/backups/mongodb/
├── backup_test_database_20251122_234902.tar.gz  (compressed)
├── backup_test_database_20251123_020000.tar.gz  (compressed)
├── backup.log                                    (backup logs)
└── cron.log                                      (automated backup logs)
```

### Retention Policy
- **Keeps**: Last 7 days of backups
- **Removes**: Backups older than 7 days (automatic rotation)
- **Storage**: ~50KB per backup (compressed)

### Backup Schedule
- **Frequency**: Daily
- **Time**: 2:00 AM (default, configurable)
- **Duration**: ~2-5 seconds for current database size

---

## Restore Procedures

### Standard Restore (Non-Emergency)

1. **List available backups**:
   ```bash
   /app/scripts/restore_mongodb.sh list
   ```

2. **Restore from latest backup**:
   ```bash
   /app/scripts/restore_mongodb.sh latest
   ```
   
   When prompted, type `yes` to confirm.

3. **Verify restoration**:
   ```bash
   # Check if data is restored
   mongo mongodb://localhost:27017/test_database --eval "db.users.countDocuments({})"
   ```

### Emergency Restore (Data Loss)

**If database is corrupted or data lost:**

```bash
# 1. Stop backend to prevent new writes
sudo supervisorctl stop backend

# 2. Restore from latest backup
/app/scripts/restore_mongodb.sh latest

# 3. Restart backend
sudo supervisorctl start backend

# 4. Verify application is working
curl https://sportauction.preview.emergentagent.com/api/sports
```

### Selective Restore (Specific Backup)

```bash
# Restore from a specific date/time
/app/scripts/restore_mongodb.sh backup_test_database_20251122_143000
```

---

## Monitoring & Maintenance

### Check Backup Status
```bash
# View backup log
tail -50 /app/backups/mongodb/backup.log

# View cron execution log
tail -50 /app/backups/mongodb/cron.log

# List all backups with sizes
ls -lh /app/backups/mongodb/
```

### Verify Backups Are Running
```bash
# Check if cron job exists
crontab -l | grep backup_mongodb

# Check recent backups
ls -lt /app/backups/mongodb/ | head -10
```

### Manual Backup Before Critical Operations
```bash
# Before major changes (schema updates, data migrations)
/app/scripts/backup_mongodb.sh

# Document the backup name
/app/scripts/restore_mongodb.sh list
```

---

## Backup Testing

### Test Restore Process (Recommended Monthly)

1. **Create test backup**:
   ```bash
   /app/scripts/backup_mongodb.sh
   ```

2. **Note current data count**:
   ```bash
   mongo mongodb://localhost:27017/test_database --eval "db.users.countDocuments({})"
   ```

3. **Perform test restore**:
   ```bash
   /app/scripts/restore_mongodb.sh latest
   ```

4. **Verify data count matches**:
   ```bash
   mongo mongodb://localhost:27017/test_database --eval "db.users.countDocuments({})"
   ```

---

## Troubleshooting

### Problem: Backup script fails

**Check MongoDB is running**:
```bash
sudo supervisorctl status mongodb
```

**Check disk space**:
```bash
df -h /app
```

**Check permissions**:
```bash
ls -la /app/backups/mongodb/
```

### Problem: Restore fails

**Verify backup file exists**:
```bash
ls -l /app/backups/mongodb/backup_*.tar.gz
```

**Check if backup is corrupted**:
```bash
tar -tzf /app/backups/mongodb/backup_test_database_XXXXXX.tar.gz
```

**Try uncompressed restore**:
```bash
# Extract manually first
cd /app/backups/mongodb
tar -xzf backup_test_database_XXXXXX.tar.gz
mongorestore --uri=mongodb://localhost:27017 --db=test_database --drop backup_test_database_XXXXXX/test_database
```

### Problem: Cron job not running

**Check cron service**:
```bash
sudo service cron status
```

**Check cron logs**:
```bash
grep CRON /var/log/syslog | tail -20
```

**Verify cron job syntax**:
```bash
crontab -l
```

---

## Storage Management

### Current Storage Usage
```bash
# Check backup directory size
du -sh /app/backups/mongodb

# Check individual backup sizes
du -h /app/backups/mongodb/backup_*
```

### Adjust Retention Policy
Edit `/app/scripts/backup_mongodb.sh`:
```bash
# Change this line (default is 7 days)
RETENTION_DAYS=14  # Keep 14 days instead
```

### Manual Cleanup
```bash
# Remove backups older than 30 days
find /app/backups/mongodb -name "backup_*.tar.gz" -mtime +30 -delete
```

---

## External Backup Storage (Production)

For the 150-user pilot and beyond, consider external storage:

### AWS S3 Backup
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Sync backups to S3
aws s3 sync /app/backups/mongodb/ s3://your-bucket/mongodb-backups/
```

### Google Cloud Storage
```bash
# Install gsutil
pip install gsutil

# Sync backups to GCS
gsutil -m rsync -r /app/backups/mongodb/ gs://your-bucket/mongodb-backups/
```

### Add to Cron
```bash
# After local backup, sync to cloud
0 3 * * * aws s3 sync /app/backups/mongodb/ s3://your-bucket/mongodb-backups/ >> /app/backups/mongodb/s3sync.log 2>&1
```

---

## Backup Checklist (Before Pilot Launch)

- [ ] Run manual backup successfully
- [ ] Test restore process
- [ ] Verify automated daily backups are configured
- [ ] Check cron job is active
- [ ] Document backup schedule for team
- [ ] Set up external storage (optional but recommended)
- [ ] Test emergency restore procedure
- [ ] Verify retention policy (7 days)
- [ ] Ensure team knows restore commands

---

## Recovery Time Objectives (RTO)

**Current Setup**:
- **Backup Time**: ~5 seconds
- **Restore Time**: ~10 seconds
- **Data Loss Window**: Maximum 24 hours (daily backups)

**For Production**:
- Consider hourly backups
- Point-in-time recovery
- Replica sets for high availability

---

## Contact & Support

**Documentation**: `/app/docs/MONGODB_BACKUP_RESTORE.md`
**Scripts Location**: `/app/scripts/`
- `backup_mongodb.sh` - Manual/automated backup
- `restore_mongodb.sh` - Restore from backup
- `setup_backup_cron.sh` - Configure automated backups

**Logs**:
- Backup log: `/app/backups/mongodb/backup.log`
- Cron log: `/app/backups/mongodb/cron.log`
