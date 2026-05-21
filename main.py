import os
import time

from yt_dlp import YoutubeDL

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/youtube.upload"
]

SPREADSHEET_ID = "1tUIsTtA8ZzvXNCFSXzOuCIqV8iofKvIRvPguJyjdHLM"
RANGE_NAME = "Sheet1!A2:C"

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

creds = None

# LOAD EXISTING TOKEN
if os.path.exists("token.json"):

    creds = Credentials.from_authorized_user_file(
        "token.json",
        SCOPES
    )

# LOGIN IF TOKEN DOES NOT EXIST
if creds is None:

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

# REFRESH TOKEN IF EXPIRED
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

# GOOGLE SERVICES
sheet_service = build(
    "sheets",
    "v4",
    credentials=creds
)

youtube = build(
    "youtube",
    "v3",
    credentials=creds
)

sheet = sheet_service.spreadsheets()

# GET DATA
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME
).execute()

values = result.get("values", [])

if not values:
    print("No data found.")
    exit()

# LOOP
for index, row in enumerate(values, start=2):

    try:

        reel_url = row[0]
        title = row[1]
        status = row[2]

        if status.upper() == "DONE":
            continue

        print(f"Downloading: {title}")

        video_path = f"{DOWNLOAD_FOLDER}/{title}.mp4"

        ydl_opts = {
            "outtmpl": video_path,
            "format": "mp4"
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])

        print(f"Downloaded: {title}")

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

        media = MediaFileUpload(video_path)

        youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()

        print(f"Uploaded: {title}")

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

        print(f"Error: {e}")