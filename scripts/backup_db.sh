#!/bin/bash

# Extract ONLY the DATABASE_URL line to avoid executing other .env lines
export DATABASE_URL=$(grep '^DATABASE_URL=' /home/deploy/wallex/.env | cut -d '=' -f2-)

# Replace asyncpg with standard postgresql for pg_dump
DB_URL=${DATABASE_URL/postgresql+asyncpg/postgresql}

BACKUP_DIR="/var/backups/wallex"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
FILENAME="$BACKUP_DIR/wallex_db_$TIMESTAMP.sql.gz"

echo "Starting backup to $FILENAME..."
pg_dump "$DB_URL" | gzip > "$FILENAME"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "✅ Backup successful: $FILENAME"
    find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +7 -delete
    echo "🧹 Old backups cleaned up."
else
    echo "❌ Backup FAILED!"
    rm -f "$FILENAME"
    exit 1
fi
