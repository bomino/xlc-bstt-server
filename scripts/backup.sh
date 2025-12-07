#!/bin/bash
#
# BSTT Compliance Dashboard - Database Backup Script
#
# Usage:
#   ./scripts/backup.sh              # Create a backup
#   ./scripts/backup.sh --restore    # Restore from latest backup
#   ./scripts/backup.sh --list       # List available backups
#
# Crontab example (daily backup at 2am):
#   0 2 * * * /path/to/bstt-web/scripts/backup.sh >> /var/log/bstt-backup.log 2>&1
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
CONTAINER="${CONTAINER:-bstt-backend-prod}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

show_help() {
    echo "BSTT Database Backup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no option)    Create a new backup"
    echo "  --restore      Restore from the latest backup"
    echo "  --list         List available backups"
    echo "  --help         Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  BACKUP_DIR      Backup directory (default: ./backups)"
    echo "  CONTAINER       Docker container name (default: bstt-backend-prod)"
    echo "  RETENTION_DAYS  Days to keep backups (default: 7)"
}

create_backup() {
    echo "$(date): Starting backup..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "Error: Container $CONTAINER is not running"
        exit 1
    fi

    # Create backup filename
    BACKUP_FILE="$BACKUP_DIR/bstt_${DATE}.sqlite3"

    # Copy database from container
    docker cp "$CONTAINER:/app/data/db.sqlite3" "$BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_FILE"

    echo "$(date): Backup created: ${BACKUP_FILE}.gz"

    # Calculate size
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "$(date): Backup size: $SIZE"

    # Clean up old backups
    echo "$(date): Removing backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "bstt_*.sqlite3.gz" -mtime +$RETENTION_DAYS -delete

    # List remaining backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/bstt_*.sqlite3.gz 2>/dev/null | wc -l)
    echo "$(date): Backup complete. $BACKUP_COUNT backup(s) available."
}

restore_backup() {
    # Find the latest backup
    LATEST=$(ls -t "$BACKUP_DIR"/bstt_*.sqlite3.gz 2>/dev/null | head -n1)

    if [ -z "$LATEST" ]; then
        echo "Error: No backups found in $BACKUP_DIR"
        exit 1
    fi

    echo "Latest backup: $LATEST"
    read -p "Restore from this backup? This will overwrite the current database. (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "Error: Container $CONTAINER is not running"
        exit 1
    fi

    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    TEMP_FILE="$TEMP_DIR/db.sqlite3"

    # Decompress backup
    gunzip -c "$LATEST" > "$TEMP_FILE"

    # Copy to container
    docker cp "$TEMP_FILE" "$CONTAINER:/app/data/db.sqlite3"

    # Clean up
    rm -rf "$TEMP_DIR"

    echo "$(date): Database restored from $LATEST"
    echo "Note: You may need to restart the backend container for changes to take effect."
    echo "  docker-compose -f docker-compose.prod.yml restart backend"
}

list_backups() {
    echo "Available backups in $BACKUP_DIR:"
    echo ""

    if ls "$BACKUP_DIR"/bstt_*.sqlite3.gz 1> /dev/null 2>&1; then
        ls -lh "$BACKUP_DIR"/bstt_*.sqlite3.gz | awk '{print $NF, $5}'
    else
        echo "No backups found."
    fi
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --restore)
        restore_backup
        ;;
    --list)
        list_backups
        ;;
    *)
        create_backup
        ;;
esac
