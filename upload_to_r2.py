import sys, os
from datetime import datetime, timedelta
import boto3
from botocore.client import Config

def upload_file(file_path, timestamp):
    # Retrieve environment variables
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    # Updated: Use separate variables for Access Key and Secret Key
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket     = os.environ.get("R2_BUCKET_NAME")

    # Connect to Cloudflare R2
    # FIX: The endpoint must be 'r2.cloudflarestorage.com'
    s3 = boto3.client(
        "s3",
        region_name="auto",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4")
    )

    # Upload the backup file
    file_name = f"mongo_backup_{timestamp}.gz"
    try:
        s3.upload_file(file_path, bucket, file_name)
        print(f"Uploaded: {file_name}")
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

    # Delete backups older than 30 days
    cleanup_old_backups(s3, bucket)

def cleanup_old_backups(s3, bucket):
    cutoff = datetime.utcnow() - timedelta(days=30)

    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix="mongo_backup_")
        files = response.get("Contents", [])

        deleted = 0
        for f in files:
            # Ensure timezone-aware comparison if necessary, 
            # or strip tzinfo from LastModified
            if f["LastModified"].replace(tzinfo=None) < cutoff:
                s3.delete_object(Bucket=bucket, Key=f["Key"])
                print(f"Deleted old backup: {f['Key']}")
                deleted += 1

        print(f"Cleaned up {deleted} old backup(s)")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 upload_to_r2.py <file_path> <timestamp>")
        sys.exit(1)
    upload_file(sys.argv[1], sys.argv[2])
