#!/bin/bash
#
# Setup Automated MongoDB Backups
# Creates a cron job for daily backups at 2 AM
#

# Configuration
BACKUP_SCRIPT="/app/scripts/backup_mongodb.sh"
CRON_SCHEDULE="0 2 * * *"  # 2 AM every day
CRON_JOB="$CRON_SCHEDULE cd /app && MONGO_URL=mongodb://localhost:27017 DB_NAME=test_database $BACKUP_SCRIPT >> /app/backups/mongodb/cron.log 2>&1"

echo "=========================================="
echo "MongoDB Backup Automation Setup"
echo "=========================================="
echo ""
echo "This will create a cron job to run daily backups at 2 AM"
echo ""
echo "Cron schedule: $CRON_SCHEDULE (2 AM daily)"
echo "Backup script: $BACKUP_SCRIPT"
echo "Log file: /app/backups/mongodb/cron.log"
echo ""

# Check if cron is installed
if ! command -v crontab &> /dev/null; then
    echo "❌ cron is not installed. Cannot set up automated backups."
    echo "   Please install cron: apt-get install cron"
    exit 1
fi

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Backup script not found: $BACKUP_SCRIPT"
    exit 1
fi

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "⚠️  Cron job for MongoDB backup already exists"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "$BACKUP_SCRIPT"
    echo ""
    read -p "Do you want to replace it? (yes/no): " REPLACE
    
    if [ "$REPLACE" != "yes" ]; then
        echo "Setup cancelled"
        exit 0
    fi
    
    # Remove existing cron job
    crontab -l | grep -v "$BACKUP_SCRIPT" | crontab -
    echo "✅ Removed existing cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job created successfully!"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Daily backups will run at 2 AM"
echo "Manual backup: /app/scripts/backup_mongodb.sh"
echo "List backups: /app/scripts/restore_mongodb.sh list"
echo "Restore: /app/scripts/restore_mongodb.sh latest"
echo ""
