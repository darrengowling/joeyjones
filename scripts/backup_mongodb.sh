#!/bin/bash
#
# MongoDB Backup Script - Production Hardening Day 8
# Performs full database backup using mongodump
# Implements rotation policy (keeps last 7 days)
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="/app/backups/mongodb"
MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
DB_NAME="${DB_NAME:-test_database}"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DB_NAME}_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

log "=========================================="
log "MongoDB Backup Started"
log "=========================================="
log "Database: $DB_NAME"
log "Backup Directory: $BACKUP_DIR"
log "Retention: $RETENTION_DAYS days"

# Check if mongodump is available
if ! command -v mongodump &> /dev/null; then
    log_error "mongodump command not found. Installing mongodb-database-tools..."
    
    # Install mongodb-database-tools
    if command -v apt-get &> /dev/null; then
        wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        sudo apt-get update
        sudo apt-get install -y mongodb-database-tools
    else
        log_error "Cannot install mongodb-database-tools automatically. Please install manually."
        exit 1
    fi
fi

# Perform backup
log "Creating backup: $BACKUP_NAME"

if mongodump --uri="$MONGO_URL" --db="$DB_NAME" --out="$BACKUP_PATH" --quiet; then
    log_success "Database dump completed successfully"
    
    # Get backup size
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    log "Backup size: $BACKUP_SIZE"
    
    # Compress backup
    log "Compressing backup..."
    if tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME" 2>/dev/null; then
        # Remove uncompressed backup
        rm -rf "$BACKUP_PATH"
        
        COMPRESSED_SIZE=$(du -sh "${BACKUP_PATH}.tar.gz" | cut -f1)
        log_success "Backup compressed: ${BACKUP_PATH}.tar.gz"
        log "Compressed size: $COMPRESSED_SIZE"
    else
        log_warning "Compression failed, keeping uncompressed backup"
    fi
    
else
    log_error "Database dump failed!"
    exit 1
fi

# Rotation - Remove old backups
log "Applying rotation policy (keeping last $RETENTION_DAYS days)..."

# Count backups before rotation
BEFORE_COUNT=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -o -name "backup_*" -type d | wc -l)

# Remove backups older than retention period
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "backup_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

# Count backups after rotation
AFTER_COUNT=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -o -name "backup_*" -type d | wc -l)
REMOVED=$((BEFORE_COUNT - AFTER_COUNT))

if [ $REMOVED -gt 0 ]; then
    log "Removed $REMOVED old backup(s)"
fi

log_success "Rotation completed. Current backup count: $AFTER_COUNT"

# List current backups
log "Current backups:"
ls -lh "$BACKUP_DIR" | grep backup_ | awk '{print "  " $9 " (" $5 ")"}' | tee -a "$LOG_FILE"

# Calculate total backup storage
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Total backup storage: $TOTAL_SIZE"

log "=========================================="
log_success "Backup completed successfully!"
log "=========================================="

# Exit with success
exit 0
