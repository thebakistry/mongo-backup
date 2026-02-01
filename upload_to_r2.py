import sys, os
from datetime import datetime, timedelta
import boto3
from botocore.client import Config

def upload_file(file_path, timestamp):
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    api_token  = os.environ.get("CLOUDFLARE_R2_TOKEN")
    bucket     = os.environ.get("R2_BUCKET_NAME")

    # Connect to Cloudflare R2
    s3 = boto3.client(
        "s3",
        region_name="auto",
        endpoint_url=f"https://{account_id}.r2.cloudzero.com",
        aws_access_key_id=api_token,
        aws_secret_access_key=api_token,
        config=Config(signature_version="s3v4")
    )

    # Upload the backup file
    file_name = f"mongo_backup_{timestamp}.gz"
    s3.upload_file(file_path, bucket, file_name)
    print(f"Uploaded: {file_name}")

    # Delete backups older than 30 days
    cleanup_old_backups(s3, bucket)

def cleanup_old_backups(s3, bucket):
    cutoff = datetime.utcnow() - timedelta(days=30)

    response = s3.list_objects_v2(Bucket=bucket, Prefix="mongo_backup_")
    files = response.get("Contents", [])

    deleted = 0
    for f in files:
        if f["LastModified"].replace(tzinfo=None) < cutoff:
            s3.delete_object(Bucket=bucket, Key=f["Key"])
            print(f"Deleted old backup: {f['Key']}")
            deleted += 1

    print(f"Cleaned up {deleted} old backup(s)")

if __name__ == "__main__":
    upload_file(sys.argv[1], sys.argv[2])
