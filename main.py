import os
import time

from yt_dlp import YoutubeDL

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from moviepy import *
from PIL import Image, ImageDraw, ImageFont

print("SCRIPT STARTED")

# =========================
# GOOGLE TOKEN
# =========================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/youtube.upload'
]

if os.getenv("GOOGLE_TOKEN"):
    with open("/tmp/token.json", "w") as f:
        f.write(os.getenv("GOOGLE_TOKEN"))

creds = Credentials.from_authorized_user_file(
    "/tmp/token.json",
    SCOPES
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())

print("GOOGLE AUTH READY")

# =========================
# SHEET CONFIG
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

sheet_service = build(
    'sheets',
    'v4',
    credentials=creds
)

youtube = build(
    'youtube',
    'v3',
    credentials=creds
)

sheet = sheet_service.spreadsheets()

print("GOOGLE SERVICES CONNECTED")

# =========================
# TEXT GENERATOR
# =========================

def get_text_from_title(title):

    title_lower = title.lower()

    if "prabhas" in title_lower:

        return [
            "REBEL STAR PRABHAS !!",
            "BAHUBALI HERO !!",
            "BOX OFFICE KING !!"
        ]

    elif "ram charan" in title_lower:

        return [
            "GLOBAL STAR RAM CHARAN !!",
            "MEGA POWER HERO !!",
            "PEDDI BLOCKBUSTER !!"
        ]

    elif "allu arjun" in title_lower:

        return [
            "ICON STAR ALLU ARJUN !!",
            "PUSHPA RULE !!",
            "NATIONAL CRUSH HERO !!"
        ]

    elif "ntr" in title_lower:

        return [
            "MAN OF MASSES NTR !!",
            "RRR HERO !!",
            "BOX OFFICE BLAST !!"
        ]

    elif "mahesh" in title_lower:

        return [
            "SUPER STAR MAHESH BABU !!",
            "TELUGU KING !!",
            "GOOSEBUMPS ENTRY !!"
        ]

    else:

        return [
            title.upper() + " !!",
            "BLOCKBUSTER FEEL !!",
            "FANS CELEBRATION !!"
        ]

# =========================
# CREATE YELLOW STRIP
# =========================

def create_yellow_strip(text_lines, width):

    final_text = "\n".join(text_lines)

    # YELLOW STRIP HEIGHT

    box_height = 300

    img = Image.new(
        "RGBA",
        (width, box_height),
        (255, 230, 0, 230)
    )

    draw = ImageDraw.Draw(img)

    # BIG BOLD FONT

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        85
    )

    bbox = draw.multiline_textbbox(
        (0, 0),
        final_text,
        font=font,
        spacing=18
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (box_height - text_height) / 2

    draw.multiline_text(
        (x, y),
        final_text,
        font=font,
        fill="black",
        align="center",
        spacing=18
    )

    yellow_strip_path = (
        f"{DOWNLOAD_FOLDER}/textbox.png"
    )

    img.save(yellow_strip_path)

    return yellow_strip_path

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
                    print("INVALID ROW")
                    continue

                reel_url = row[0]
                title = row[1]
                status = row[2]

                print(f"TITLE: {title}")
                print(f"STATUS: {status}")

                if status.upper() == "DONE":
                    print("SKIPPED DONE ROW")
                    continue

                safe_title = (
                    title
                    .replace("/", "_")
                    .replace("\\", "_")
                )

                original_video = (
                    f"{DOWNLOAD_FOLDER}/{safe_title}.mp4"
                )

                # =========================
                # DOWNLOAD VIDEO
                # =========================

                print("DOWNLOADING VIDEO...")

                ydl_opts = {
                    'outtmpl': original_video,
                    'format': 'mp4',
                    'cookiefile': 'cookies.txt'
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([reel_url])

                print("VIDEO DOWNLOADED")

                # =========================
                # VIDEO EDITING
                # =========================

                clip = VideoFileClip(original_video)

                # ONLY FIRST 18 SECONDS

                if clip.duration > 18:
                    clip = clip.subclipped(0, 18)

                w, h = clip.size

                # =========================
                # AUTO GENERATED TEXT
                # =========================

                text_lines = get_text_from_title(title)

                # =========================
                # CREATE TEXT STRIP
                # =========================

                yellow_strip_path = create_yellow_strip(
                    text_lines,
                    w
                )

                # =========================
                # ADD TEXT TO VIDEO
                # =========================

                text_clip = ImageClip(
                    yellow_strip_path
                )

                text_clip = text_clip.with_duration(
                    clip.duration
                )

                # LEVEL 3-4 FROM BOTTOM

                text_clip = text_clip.with_position(
                    ("center", int(h * 0.68))
                )

                final_video = CompositeVideoClip([
                    clip,
                    text_clip
                ])

                edited_video = (
                    f"{DOWNLOAD_FOLDER}/edited_{safe_title}.mp4"
                )

                print("RENDERING VIDEO...")

                final_video.write_videofile(
                    edited_video,
                    codec="libx264",
                    audio_codec="aac",
                    preset="ultrafast",
                    threads=2,
                    bitrate="2500k",
                    fps=24
                )

                print("TEXT ADDED SUCCESSFULLY")

                # =========================
                # HASHTAGS
                # =========================

                hashtags = """
#shorts
#viral
#trending
#tollywood
#ramcharan
#prabhas
#alluarjun
#ntr
#maheshbabu
"""

                # =========================
                # UPLOAD TO YOUTUBE
                # =========================

                request_body = {
                    "snippet": {
                        "title": title,
                        "description": hashtags,
                        "tags": [
                            "shorts",
                            "viral",
                            "trending",
                            "tollywood"
                        ],
                        "categoryId": "24"
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False
                    }
                }

                media = MediaFileUpload(
                    edited_video
                )

                youtube.videos().insert(
                    part="snippet,status",
                    body=request_body,
                    media_body=media
                ).execute()

                print("VIDEO UPLOADED")

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

                print("MARKED AS DONE")

                # =========================
                # DELETE FILES
                # =========================

                try:
                    os.remove(original_video)
                    os.remove(edited_video)
                    os.remove(yellow_strip_path)
                except:
                    pass

                print("FILES DELETED")

                # =========================
                # WAIT 10 MINUTES
                # =========================

                print("WAITING 10 MINUTES...")
                time.sleep(600)

            except Exception as e:

                print(
                    f"ERROR PROCESSING ROW {index}: {e}"
                )

        print("ALL ROWS COMPLETED")
        print("WAITING 5 MINUTES...")

        time.sleep(300)

    except Exception as e:

        print(f"MAIN LOOP ERROR: {e}")

        time.sleep(300)