import sys, os
from datetime import datetime, timedelta
import boto3
from botocore.client import Config

def upload_file(file_path, timestamp):
    # Retrieve environment variables
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket     = os.environ.get("R2_BUCKET_NAME")

    # ERROR CHECK: Ensure variables are actually loaded
    if not all([account_id, access_key, secret_key, bucket]):
        missing = [k for k, v in {
            "CLOUDFLARE_ACCOUNT_ID": account_id, 
            "R2_ACCESS_KEY_ID": access_key, 
            "R2_SECRET_ACCESS_KEY": secret_key, 
            "R2_BUCKET_NAME": bucket
        }.items() if not v]
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Connect to Cloudflare R2
    # NOTE: Use .cloudflarestorage.com for the S3 API
    s3 = boto3.client(
        "s3",
        region_name="auto",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4")
    )

    file_name = f"mongo_backup_{timestamp}.gz"
    
    try:
        print(f"Attempting to upload {file_name} to {bucket}...")
        s3.upload_file(file_path, bucket, file_name)
        print(f"✅ Upload successful!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

    cleanup_old_backups(s3, bucket)

def cleanup_old_backups(s3, bucket):
    cutoff = datetime.utcnow() - timedelta(days=30)
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix="mongo_backup_")
        files = response.get("Contents", [])
        for f in files:
            if f["LastModified"].replace(tzinfo=None) < cutoff:
                s3.delete_object(Bucket=bucket, Key=f["Key"])
                print(f"Deleted old backup: {f['Key']}")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 upload_to_r2.py <file_path> <timestamp>")
        sys.exit(1)
    upload_file(sys.argv[1], sys.argv[2])
