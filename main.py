import os
import time

from yt_dlp import YoutubeDL

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =========================
# GOOGLE TOKEN FROM RAILWAY
# =========================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/youtube.upload'
]

# Create token file from Railway variable
if os.getenv("GOOGLE_TOKEN"):
    with open("/tmp/token.json", "w") as f:
        f.write(os.getenv("GOOGLE_TOKEN"))

# Load credentials
creds = Credentials.from_authorized_user_file(
    "/tmp/token.json",
    SCOPES
)

# Refresh token if expired
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

# =========================
# GOOGLE SHEET CONFIG
# =========================

SPREADSHEET_ID = "1tUIsTtA8ZzvXNCFSXzOuCIqV8iofKvIRvPguJyjdHLM"
RANGE_NAME = "Sheet1!A2:C"

# =========================
# DOWNLOAD FOLDER
# =========================

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# =========================
# GOOGLE SERVICES
# =========================

sheet_service = build('sheets', 'v4', credentials=creds)
youtube = build('youtube', 'v3', credentials=creds)

sheet = sheet_service.spreadsheets()

# =========================
# READ GOOGLE SHEET
# =========================

result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME
).execute()

values = result.get('values', [])

if not values:
    print("No data found.")
    exit()

# =========================
# PROCESS EACH ROW
# =========================

for index, row in enumerate(values, start=2):

    try:

        reel_url = row[0]
        title = row[1]
        status = row[2]

        # Skip completed rows
        if status.upper() == "DONE":
            continue

        print(f"Downloading: {title}")

        # =========================
        # DOWNLOAD VIDEO
        # =========================

        safe_title = title.replace("/", "_").replace("\\", "_")

        video_file = f"{DOWNLOAD_FOLDER}/{safe_title}.mp4"

        ydl_opts = {
            'outtmpl': video_file,
            'format': 'mp4'
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])

        print(f"Downloaded: {title}")

        # =========================
        # UPLOAD TO YOUTUBE
        # =========================

        request_body = {
            "snippet": {
                "title": title,
                "description": "#shorts",
                "tags": ["shorts"],
                "categoryId": "24"
            },
            "status": {
                "privacyStatus": "public"
            }
        }

        media = MediaFileUpload(video_file)

        youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()

        print(f"Uploaded to YouTube: {title}")

        # =========================
        # MARK DONE IN SHEET
        # =========================

        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Sheet1!C{index}",
            valueInputOption="RAW",
            body={
                "values": [["DONE"]]
            }
        ).execute()

        print(f"Marked DONE: {title}")

        time.sleep(3)

    except Exception as e:
        print(f"Error processing row {index}: {e}")