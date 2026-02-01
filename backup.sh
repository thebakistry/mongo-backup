#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_FILE="/tmp/mongo_backup/backup_${TIMESTAMP}.gz"

mkdir -p /tmp/mongo_backup

echo "Backup started at $TIMESTAMP"

# --- STEP 1: Dump production DB ---
mongodump \
  --uri "$PROD_MONGO_URI" \
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
  --drop \
  --gzip \
  --archive="$BACKUP_FILE"

if [ $? -ne 0 ]; then
  echo "RESTORE FAILED"
  exit 1
fi
echo "Restore to backup DB successful"

# --- STEP 3: Upload to Cloudflare R2 ---
pip install boto3 --quiet

python3 upload_to_r2.py "$BACKUP_FILE" "$TIMESTAMP"

if [ $? -ne 0 ]; then
  echo "R2 UPLOAD FAILED (backup itself is fine)"
  exit 1
else
  echo "Uploaded to Cloudflare R2 successfully"
fi

# --- STEP 4: Cleanup ---
rm -f "$BACKUP_FILE"

echo "Backup completed at $(date)"
