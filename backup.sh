#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_DIR="/tmp/mongo_backup/$TIMESTAMP"
BACKUP_FILE="/tmp/mongo_backup/backup_${TIMESTAMP}.gz"

mkdir -p /tmp/mongo_backup

echo "Backup started at $TIMESTAMP"

# --- STEP 1: Dump production DB (compressed) ---
mongodump \
  --uri "$PROD_MONGO_URI" \
  --db "$DB_NAME" \
  --gzip \
  --archive="$BACKUP_FILE"

if [ $? -ne 0 ]; then
  echo "DUMP FAILED"
  exit 1
fi
echo "Dump successful — size: $(du -h $BACKUP_FILE | cut -f1)"

# --- STEP 2: Restore into backup MongoDB ---
mongorestore \
  --uri "$BACKUP_MONGO_URI" \
  --db "${DB_NAME}_backup" \
  --drop \
  --gzip \
  --archive="$BACKUP_FILE"

if [ $? -ne 0 ]; then
  echo "RESTORE FAILED"
  exit 1
fi
echo "Restore to backup DB successful"

# --- STEP 3: Upload .gz file to Google Drive ---
echo "$GOOGLE_SERVICE_ACCOUNT_KEY" > /tmp/service_account.json

pip install google-api-python-client google-auth --quiet

python3 upload_to_drive.py "$BACKUP_FILE" "$TIMESTAMP"

if [ $? -ne 0 ]; then
  echo "GOOGLE DRIVE UPLOAD FAILED (backup itself is fine)"
else
  echo "Uploaded to Google Drive successfully"
fi

# --- STEP 4: Cleanup temp files ---
rm -f "$BACKUP_FILE"
rm -f /tmp/service_account.json

echo "Backup completed at $(date)"
