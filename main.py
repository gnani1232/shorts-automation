import os
import time
import random

from yt_dlp import YoutubeDL

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from moviepy.editor import *

print("SCRIPT STARTED")

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

print("TOKEN FILE CREATED")

# Load credentials
creds = Credentials.from_authorized_user_file(
    "/tmp/token.json",
    SCOPES
)

print("CREDENTIALS LOADED")

# Refresh token if expired
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    print("TOKEN REFRESHED")

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

print("DOWNLOAD FOLDER READY")

# =========================
# GOOGLE SERVICES
# =========================

sheet_service = build('sheets', 'v4', credentials=creds)
youtube = build('youtube', 'v3', credentials=creds)

sheet = sheet_service.spreadsheets()

print("GOOGLE SERVICES CONNECTED")

# =========================
# AUTO TEXT GENERATOR
# =========================

def generate_hook(title):

    hooks = [
        f"{title} 😍",
        f"Can't stop watching this ❤️",
        f"Beautiful moments forever ✨",
        f"Fans are loving this 🔥",
        f"Pure happiness 🥺❤️",
        f"This looks straight out of a movie 😍",
        f"Couple goals forever 💕",
        f"Internet is obsessed with this ✨"
    ]

    return random.choice(hooks)

# =========================
# VIDEO TEXT OVERLAY
# =========================

def add_text_overlay(input_video, output_video, title):

    clip = VideoFileClip(input_video)

    hook_text = generate_hook(title)

    bottom_text = random.choice([
        "Comment your thoughts 🔥",
        "What do you think? ❤️",
        "Drop your reaction 😍",
        "Fans are going crazy 🔥",
        "Would you watch this again? 👀"
    ])

    # MAIN TEXT
    text1 = TextClip(
        hook_text,
        fontsize=60,
        color='yellow',
        stroke_color='black',
        stroke_width=3,
        font='Arial-Bold',
        method='caption',
        size=(900, None)
    )

    # Slightly below middle
    text1 = text1.set_position(("center", 850)).set_duration(clip.duration)

    # SECOND TEXT
    text2 = TextClip(
        bottom_text,
        fontsize=45,
        color='white',
        stroke_color='black',
        stroke_width=2,
        font='Arial-Bold',
        method='caption',
        size=(900, None)
    )

    text2 = text2.set_position(("center", 940)).set_duration(clip.duration)

    final = CompositeVideoClip([clip, text1, text2])

    final.write_videofile(
        output_video,
        codec="libx264",
        audio_codec="aac"
    )

# =========================
# MAIN BOT LOOP
# =========================

while True:

    try:

        print("CHECKING SHEET...")

        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])

        print("SHEET VALUES:")
        print(values)

        if not values:
            print("NO DATA FOUND")
            time.sleep(60)
            continue

        # =========================
        # PROCESS EACH ROW
        # =========================

        for index, row in enumerate(values, start=2):

            try:

                print(f"PROCESSING ROW {index}")

                if len(row) < 3:
                    print("ROW DOES NOT HAVE REQUIRED COLUMNS")
                    continue

                reel_url = row[0]
                title = row[1]
                status = row[2]

                print(f"TITLE: {title}")
                print(f"STATUS: {status}")

                # Skip completed rows
                if status.upper() == "DONE":
                    print("SKIPPED DONE ROW")
                    continue

                # =========================
                # AUTO HASHTAGS
                # =========================

                hashtags = title.lower().split()

                hashtags = [
                    tag.replace("#", "").strip()
                    for tag in hashtags
                ]

                extra_tags = [
                    "shorts",
                    "viral",
                    "trending",
                    "fyp",
                    "youtubeShorts"
                ]

                hashtags.extend(extra_tags)

                hashtags = list(set(hashtags))

                hashtags = hashtags[:15]

                print(f"HASHTAGS: {hashtags}")

                print(f"DOWNLOADING: {title}")

                # =========================
                # SAFE FILE NAME
                # =========================

                safe_title = (
                    title.replace("/", "_")
                    .replace("\\", "_")
                    .replace(":", "_")
                    .replace("*", "_")
                    .replace("?", "_")
                    .replace('"', "_")
                    .replace("<", "_")
                    .replace(">", "_")
                    .replace("|", "_")
                )

                video_file = f"{DOWNLOAD_FOLDER}/{safe_title}.mp4"

                # =========================
                # DOWNLOAD VIDEO
                # =========================

                ydl_opts = {
                    'outtmpl': video_file,
                    'format': 'mp4'
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([reel_url])

                print(f"DOWNLOADED: {title}")

                # =========================
                # ADD TEXT OVERLAY
                # =========================

                edited_video = f"{DOWNLOAD_FOLDER}/edited_{safe_title}.mp4"

                add_text_overlay(
                    video_file,
                    edited_video,
                    title
                )

                print("TEXT OVERLAY ADDED")

                # =========================
                # YOUTUBE UPLOAD
                # =========================

                request_body = {
                    "snippet": {
                        "title": title,
                        "description": "#shorts",
                        "tags": hashtags,
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

                print(f"UPLOADED TO YOUTUBE: {title}")

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

                print(f"MARKED DONE: {title}")

                # =========================
                # DELETE FILES
                # =========================

                if os.path.exists(video_file):
                    os.remove(video_file)

                if os.path.exists(edited_video):
                    os.remove(edited_video)

                print("VIDEO FILES DELETED")

                time.sleep(5)

            except Exception as e:
                print(f"ERROR PROCESSING ROW {index}: {e}")

        print("ALL ROWS COMPLETED")

    except Exception as e:
        print(f"MAIN LOOP ERROR: {e}")

    print("WAITING 25 MINUTES...")
    time.sleep(1500)