import sys, os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_file(file_path, timestamp):
    # Load Google credentials from the key file
    credentials = service_account.Credentials.from_service_account_file(
        "/tmp/service_account.json",
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    # Connect to Google Drive API
    drive = build("drive", "v3", credentials=credentials)

    # Get folder ID from environment variable
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

    # Upload the backup file
    file_name = f"mongo_backup_{timestamp}.gz"
    metadata = { "name": file_name, "parents": [folder_id] }
    media = MediaFileUpload(file_path, mimetype="application/gzip")

    result = drive.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, createdTime"
    ).execute()

    print(f"Uploaded: {result['name']} (ID: {result['id']})")

    # Delete backups older than 30 days
    cleanup_old_backups(drive, folder_id)

def cleanup_old_backups(drive, folder_id):
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Find all backup files older than 30 days in your folder
    results = drive.files().list(
        q=f"'{folder_id}' in parents and createdTime < '{thirty_days_ago}' and name contains 'mongo_backup'",
        fields="files(id, name, createdTime)"
    ).execute()

    files = results.get("files", [])
    for f in files:
        drive.files().delete(fileId=f["id"]).execute()
        print(f"Deleted old backup: {f['name']}")

    print(f"Cleaned up {len(files)} old backup(s)")

if __name__ == "__main__":
    upload_file(sys.argv[1], sys.argv[2])
