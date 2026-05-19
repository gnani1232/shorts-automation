import os
import time
import random

from yt_dlp import YoutubeDL

from moviepy import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip
)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("SCRIPT STARTED")

# ==========================================
# GOOGLE TOKEN FROM RAILWAY VARIABLE
# ==========================================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/youtube.upload'
]

if os.getenv("GOOGLE_TOKEN"):
    with open("/tmp/token.json", "w") as f:
        f.write(os.getenv("GOOGLE_TOKEN"))

print("TOKEN FILE CREATED")

creds = Credentials.from_authorized_user_file(
    "/tmp/token.json",
    SCOPES
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    print("TOKEN REFRESHED")

print("GOOGLE LOGIN SUCCESS")

# ==========================================
# GOOGLE SHEETS CONFIG
# ==========================================

SPREADSHEET_ID = "1tUIsTtA8ZzvXNCFSXzOuCIqV8iofKvIRvPguJyjdHLM"
RANGE_NAME = "Sheet1!A2:C"

# ==========================================
# DOWNLOAD FOLDER
# ==========================================

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ==========================================
# GOOGLE SERVICES
# ==========================================

sheet_service = build('sheets', 'v4', credentials=creds)
youtube = build('youtube', 'v3', credentials=creds)

sheet = sheet_service.spreadsheets()

print("GOOGLE SERVICES READY")

# ==========================================
# AUTO CAPTIONS
# ==========================================

caption_templates = [
    "I wish they stay together forever 😍🔥",
    "Best couple on internet ❤️✨",
    "Tell your wishes in comments 🔥",
    "This moment feels magical 😍",
    "Internet favorite pair ❤️",
    "Pure happiness together 🥺❤️",
    "Couple goals literally 😍",
    "Their chemistry is unreal 🔥",
    "Manifesting this love forever ❤️",
    "Most wholesome video today 😭❤️"
]

hashtags_pool = [
    "#shorts",
    "#viral",
    "#couple",
    "#love",
    "#trending",
    "#instagram",
    "#reels",
    "#ytshorts",
    "#romantic",
    "#viralshorts"
]

# ==========================================
# MAIN LOOP
# ==========================================

while True:

    print("CHECKING GOOGLE SHEET...")

    try:

        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])

        if not values:
            print("NO DATA FOUND")
            time.sleep(1500)
            continue

        # ==========================================
        # PROCESS ROWS
        # ==========================================

        for index, row in enumerate(values, start=2):

            try:

                reel_url = row[0]
                title = row[1]
                status = row[2]

                print(f"PROCESSING: {title}")

                if status.upper() == "DONE":
                    print("ALREADY DONE")
                    continue

                # ==========================================
                # DOWNLOAD VIDEO
                # ==========================================

                safe_title = title.replace("/", "_").replace("\\", "_")

                original_video = f"{DOWNLOAD_FOLDER}/{safe_title}.mp4"

                ydl_opts = {
                    'outtmpl': original_video,
                    'format': 'mp4'
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([reel_url])

                print("VIDEO DOWNLOADED")

                # ==========================================
                # GENERATE AUTO TEXT
                # ==========================================

                random_caption = random.choice(caption_templates)

                random_hashtags = " ".join(
                    random.sample(hashtags_pool, 5)
                )

                full_caption = f"{random_caption}\n\n{random_hashtags}"

                # ==========================================
                # ADD TEXT TO VIDEO
                # ==========================================

                clip = VideoFileClip(original_video)

                text_clip = TextClip(
                    text=random_caption,
                    font_size=60,
                    color='yellow',
                    stroke_color='black',
                    stroke_width=3,
                    method='caption',
                    size=(900, None)
                )

                text_clip = (
                    text_clip
                    .with_position(("center", 900))
                    .with_duration(clip.duration)
                )

                final_video = CompositeVideoClip([
                    clip,
                    text_clip
                ])

                edited_video = f"{DOWNLOAD_FOLDER}/edited_{safe_title}.mp4"

                final_video.write_videofile(
                    edited_video,
                    codec="libx264",
                    audio_codec="aac"
                )

                print("TEXT ADDED TO VIDEO")

                # ==========================================
                # UPLOAD TO YOUTUBE
                # ==========================================

                request_body = {
                    "snippet": {
                        "title": title,
                        "description": full_caption,
                        "tags": hashtags_pool,
                        "categoryId": "24"
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False
                    }
                }

                media = MediaFileUpload(edited_video)

                youtube.videos().insert(
                    part="snippet,status",
                    body=request_body,
                    media_body=media
                ).execute()

                print("UPLOADED TO YOUTUBE")

                # ==========================================
                # MARK DONE
                # ==========================================

                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Sheet1!C{index}",
                    valueInputOption="RAW",
                    body={
                        "values": [["DONE"]]
                    }
                ).execute()

                print("MARKED DONE")

                # ==========================================
                # DELETE FILES
                # ==========================================

                os.remove(original_video)
                os.remove(edited_video)

                print("FILES DELETED")

                time.sleep(5)

            except Exception as e:
                print(f"ERROR IN ROW {index}: {e}")

        print("ALL ROWS COMPLETED")
        print("WAITING 25 MINUTES...")

        time.sleep(1500)

    except Exception as main_error:
        print(f"MAIN ERROR: {main_error}")
        time.sleep(300)