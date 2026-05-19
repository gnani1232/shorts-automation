import os
import time
import random

from yt_dlp import YoutubeDL

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from moviepy import *
from PIL import Image, ImageDraw, ImageFont

print("SCRIPT STARTED")

# =========================
# GOOGLE TOKEN FROM RAILWAY
# =========================

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

print("CREDENTIALS LOADED")

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
# MAIN LOOP
# =========================

while True:

    try:

        print("CHECKING SHEET FOR NEW VIDEOS...")

        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])

        print(values)

        if not values:
            print("NO DATA FOUND")
            time.sleep(300)
            continue

        # =========================
        # PROCESS ROWS
        # =========================

        for index, row in enumerate(values, start=2):

            try:

                print(f"PROCESSING ROW {index}")

                if len(row) < 3:
                    print("ROW INCOMPLETE")
                    continue

                reel_url = row[0]
                title = row[1]
                status = row[2]

                print(f"TITLE: {title}")
                print(f"STATUS: {status}")

                if status.upper() == "DONE":
                    print("SKIPPED DONE ROW")
                    continue

                safe_title = title.replace("/", "_").replace("\\", "_")

                original_video = f"{DOWNLOAD_FOLDER}/{safe_title}.mp4"

                print("DOWNLOADING VIDEO...")

                # =========================
                # INSTAGRAM DOWNLOAD
                # =========================

                ydl_opts = {
                    'outtmpl': original_video,
                    'format': 'mp4',
                    'cookiefile': 'cookies.txt'
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([reel_url])

                print("VIDEO DOWNLOADED")

                # =========================
                # SKIP LARGE VIDEOS
                # =========================

                if os.path.getsize(original_video) > 50000000:
                    print("VIDEO TOO LARGE, SKIPPING")
                    continue

                # =========================
                # VIDEO EDITING
                # =========================

                clip = VideoFileClip(original_video)

                w, h = clip.size

                title_lower = title.lower()

                text_options = []

                if "prabhas" in title_lower:
                    text_options = [
                        "REBEL STAR PRABHAS 🔥",
                        "BAHUBALI HERO 😍",
                        "BOX OFFICE KING 💥"
                    ]

                elif "ram charan" in title_lower:
                    text_options = [
                        "GLOBAL STAR RAM CHARAN 🔥",
                        "MEGA POWER HERO 😍",
                        "PEDDI BLOCKBUSTER 💥"
                    ]

                elif "mahesh" in title_lower:
                    text_options = [
                        "SUPER STAR MAHESH BABU 🔥",
                        "TELUGU KING 😍",
                        "GOOSEBUMPS ENTRY 💥"
                    ]

                elif "ntr" in title_lower:
                    text_options = [
                        "MAN OF MASSES NTR 🔥",
                        "RRR HERO 😍",
                        "BOX OFFICE BLAST 💥"
                    ]

                elif "allu arjun" in title_lower:
                    text_options = [
                        "ICON STAR ALLU ARJUN 🔥",
                        "PUSHPA RULE 😍",
                        "NATIONAL CRUSH HERO 💥"
                    ]

                else:
                    text_options = [
                        title.upper(),
                        "BLOCKBUSTER FEEL 🔥",
                        "FANS CELEBRATION 😍"
                    ]

                final_text = "\n".join(text_options)

                # =========================
                # CREATE YELLOW TEXT BOX
                # =========================

                img = Image.new("RGBA", (w, 220), (255, 230, 0, 235))

                draw = ImageDraw.Draw(img)

                font = ImageFont.load_default()

                bbox = draw.multiline_textbbox(
                    (0, 0),
                    final_text,
                    font=font
                )

                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                x = (w - text_width) / 2
                y = (220 - text_height) / 2

                draw.multiline_text(
                    (x, y),
                    final_text,
                    font=font,
                    fill="black",
                    align="center",
                    spacing=10
                )

                yellow_box_path = f"{DOWNLOAD_FOLDER}/textbox.png"

                img.save(yellow_box_path)

                # =========================
                # ADD TEXT BOX TO VIDEO
                # =========================

                text_clip = (
                    ImageClip(yellow_box_path)
                    .set_duration(clip.duration)
                    .set_position(("center", h * 0.35))
                )

                final_video = CompositeVideoClip([
                    clip,
                    text_clip
                ])

                edited_video = f"{DOWNLOAD_FOLDER}/edited_{safe_title}.mp4"

                print("RENDERING VIDEO...")

                final_video.write_videofile(
                    edited_video,
                    codec="libx264",
                    audio_codec="aac",
                    preset="ultrafast",
                    threads=2,
                    bitrate="2000k",
                    fps=24
                )

                print("TEXT ADDED SUCCESSFULLY")

                # =========================
                # YOUTUBE UPLOAD
                # =========================

                hashtags = "#shorts #viral #trending #tollywood"

                request_body = {
                    "snippet": {
                        "title": title,
                        "description": hashtags,
                        "tags": [
                            "shorts",
                            "viral",
                            "tollywood",
                            "trending"
                        ],
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
                # MARK DONE
                # =========================

                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Sheet1!C{index}",
                    valueInputOption="RAW",
                    body={
                        "values": [["DONE"]]
                    }
                ).execute()

                print("MARKED DONE")

                # =========================
                # DELETE FILES
                # =========================

                try:
                    os.remove(original_video)
                    os.remove(edited_video)
                    os.remove(yellow_box_path)
                    print("FILES DELETED")
                except:
                    pass

                # =========================
                # WAIT 10 MINUTES
                # =========================

                print("WAITING 10 MINUTES BEFORE NEXT VIDEO...")
                time.sleep(600)

            except Exception as e:
                print(f"ERROR PROCESSING ROW {index}: {e}")

        print("ALL ROWS COMPLETED")
        print("WAITING 5 MINUTES...")

        time.sleep(300)

    except Exception as e:
        print(f"MAIN LOOP ERROR: {e}")
        time.sleep(300)