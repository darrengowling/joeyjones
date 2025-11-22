#!/bin/bash
#
# MongoDB Restore Script - Production Hardening Day 8
# Restores database from a backup created by backup_mongodb.sh
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="/app/backups/mongodb"
MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
DB_NAME="${DB_NAME:-test_database}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if mongorestore is available
if ! command -v mongorestore &> /dev/null; then
    log_error "mongorestore command not found. Please install mongodb-database-tools."
    exit 1
fi

# Show usage
usage() {
    echo "Usage: $0 [backup_name|latest]"
    echo ""
    echo "Examples:"
    echo "  $0 latest                                    # Restore from most recent backup"
    echo "  $0 backup_test_database_20250122_143000     # Restore from specific backup"
    echo "  $0 list                                      # List available backups"
    echo ""
    exit 1
}

# List available backups
list_backups() {
    echo "=========================================="
    echo "Available Backups"
    echo "=========================================="
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/backup_* 2>/dev/null)" ]; then
        log_warning "No backups found in $BACKUP_DIR"
        exit 0
    fi
    
    echo ""
    echo "Compressed backups (.tar.gz):"
    ls -lht "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | awk '{print "  " $9 " - " $6 " " $7 " " $8 " (" $5 ")"}'
    
    echo ""
    echo "Uncompressed backups:"
    find "$BACKUP_DIR" -name "backup_*" -type d | sort -r | while read dir; do
        SIZE=$(du -sh "$dir" | cut -f1)
        DATE=$(stat -c %y "$dir" | cut -d'.' -f1)
        echo "  $(basename $dir) - $DATE ($SIZE)"
    done
    
    echo ""
    exit 0
}

# Check arguments
if [ $# -eq 0 ]; then
    usage
fi

if [ "$1" == "list" ]; then
    list_backups
fi

BACKUP_NAME="$1"

# If "latest", find the most recent backup
if [ "$BACKUP_NAME" == "latest" ]; then
    # Check for compressed backups first
    LATEST_COMPRESSED=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
    LATEST_DIR=$(find "$BACKUP_DIR" -name "backup_*" -type d | sort -r | head -1)
    
    if [ -n "$LATEST_COMPRESSED" ]; then
        BACKUP_PATH="$LATEST_COMPRESSED"
        log_info "Latest backup found: $(basename $BACKUP_PATH)"
    elif [ -n "$LATEST_DIR" ]; then
        BACKUP_PATH="$LATEST_DIR"
        log_info "Latest backup found: $(basename $BACKUP_PATH)"
    else
        log_error "No backups found in $BACKUP_DIR"
        exit 1
    fi
else
    # Check if backup exists
    if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
        BACKUP_PATH="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    elif [ -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
        BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    else
        log_error "Backup not found: $BACKUP_NAME"
        echo ""
        echo "Run '$0 list' to see available backups"
        exit 1
    fi
fi

echo "=========================================="
echo "MongoDB Restore"
echo "=========================================="
echo "Backup: $(basename $BACKUP_PATH)"
echo "Database: $DB_NAME"
echo "MongoDB URL: $MONGO_URL"
echo ""

# Confirmation prompt
log_warning "This will REPLACE the current database: $DB_NAME"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Restore cancelled"
    exit 0
fi

echo ""
log_info "Starting restore..."

# Extract if compressed
RESTORE_DIR="$BACKUP_PATH"
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    log_info "Extracting compressed backup..."
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"
    RESTORE_DIR="$TEMP_DIR/$(basename $BACKUP_PATH .tar.gz)"
fi

# Perform restore
if mongorestore --uri="$MONGO_URL" --db="$DB_NAME" --drop "$RESTORE_DIR/$DB_NAME" --quiet; then
    log_success "Database restored successfully!"
else
    log_error "Restore failed!"
    
    # Cleanup temp directory
    if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
        rm -rf "$TEMP_DIR"
    fi
    
    exit 1
fi

# Cleanup temp directory
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    rm -rf "$TEMP_DIR"
    log_info "Cleaned up temporary files"
fi

echo ""
log_success "Restore completed successfully!"
echo "=========================================="

exit 0
