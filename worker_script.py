import os
import json
import time
import asyncio
import requests
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from datetime import timedelta
import pyrogram.utils

# Fix for newer Telegram IDs (DC IDs)
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import your existing helpers
from helper.database import find, used_limit, total_rename, total_size, find_one
from helper.ffmpeg import take_screen_shot, fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

# 1. Robust Payload Loading
PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
try:
    # Try parsing JSON
    payload = json.loads(PAYLOAD_RAW)
    # If GitHub Action passed it as a double-stringified JSON
    if isinstance(payload, str):
        payload = json.loads(payload)
except Exception as e:
    logger.error(f"Failed to parse payload: {e}")
    # Fallback to eval if it's a string representation of a dict
    try:
        payload = eval(PAYLOAD_RAW)
    except:
        payload = {}

# Extract Data from Payload safely
CHAT_ID = int(payload.get("chat_id", 0))
USER_ID = int(payload.get("user_id", 0))
MSG_ID = int(payload.get("message_id", 0))
NEW_NAME = payload.get("new_name", "renamed_file")
MEDIA_TYPE = payload.get("media_type", "document")
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status", False)
METADATA_TEXT = payload.get("metadata_text", "By @TechifyBots")

# 2. Initialize Clients with unique session names for GitHub
bot = Client("GitHubWorker", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, in_memory=True)
app = Client("PremiumGitHubWorker", session_string=STRING_SESSION, api_id=API_ID, api_hash=API_HASH, in_memory=True) if STRING_SESSION else None

async def run_worker():
    if not CHAT_ID or not MSG_ID:
        logger.error("Invalid Payload Data. Exiting.")
        return

    await bot.start()
    if app: await app.start()
    
    logger.info(f"Processing started for User: {USER_ID} | File: {NEW_NAME}")

    try:
        # 3. Get the File Message
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        if not file:
            await bot.send_message(CHAT_ID, "❌ Error: Original file not found.")
            return

        status_msg = await bot.send_message(CHAT_ID, "<b>📥 Worker started downloading from Telegram...</b>")
        
        # 4. Setup Paths
        if not os.path.isdir("downloads"): os.mkdir("downloads")
        if not os.path.isdir("Metadata"): os.mkdir("Metadata")
        
        download_path = f"downloads/{file.file_name if file.file_name else 'temp_file'}"
        final_path = f"downloads/{NEW_NAME}"
        metadata_path = f"Metadata/{NEW_NAME}"
        
        # 5. Download
        c_time = time.time()
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", status_msg, c_time)
        )

        # 6. Metadata / Rename Processing
        await status_msg.edit("<b>⚙️ Processing File (FFmpeg)...</b>")
        
        if METADATA_STATUS:
            processed_path = await add_metadata(path, metadata_path, METADATA_TEXT, status_msg)
            if not processed_path or not os.path.exists(processed_path):
                processed_path = final_path
                os.rename(path, final_path)
        else:
            os.rename(path, final_path)
            processed_path = final_path

        # 7. Handle Thumbnail
        ph_path = None
        if THUMB_ID:
            try:
                ph_path = await bot.download_media(THUMB_ID)
                img = Image.open(ph_path).convert("RGB")
                img.resize((320, 320))
                img.save(ph_path, "JPEG")
            except:
                ph_path = None
        
        # 8. Prepare Caption
        if CUSTOM_CAPTION:
            cap_list = ["filename", "filesize"]
            clean_cap = escape_invalid_curly_brackets(CUSTOM_CAPTION, cap_list)
            caption = clean_cap.format(filename=NEW_NAME, filesize=humanbytes(file.file_size))
        else:
            caption = f"**{NEW_NAME}**"

        # 9. Uploading (Handling 4GB)
        await status_msg.edit("<b>📤 Uploading to Telegram Cloud...</b>")
        c_time = time.time()
        
        # Choose bot if < 2GB, else app (Premium)
        target_client = app if (file.file_size > 2000000000 and app) else bot
        # Destination: User ID if Bot, else LOG_CHANNEL if Premium
        destination = CHAT_ID if target_client == bot else LOG_CHANNEL
        
        if MEDIA_TYPE == "video":
            duration = 0
            metadata = extractMetadata(createParser(processed_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds

            sent_file = await target_client.send_video(
                destination,
                video=processed_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        elif MEDIA_TYPE == "audio":
            sent_file = await target_client.send_audio(
                destination,
                audio=processed_path,
                caption=caption,
                thumb=ph_path,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        else:
            sent_file = await target_client.send_document(
                destination,
                document=processed_path,
                caption=caption,
                thumb=ph_path,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )

        # If Premium was used, copy from log to user
        if target_client == app:
            await bot.copy_message(CHAT_ID, LOG_CHANNEL, sent_file.id)

        await status_msg.delete()

        # 10. Update DB Stats
        try:
            db_data = find_one(int(USER_ID))
            total_rename(int(USER_ID), db_data.get('total_rename', 0))
            total_size(int(USER_ID), db_data.get('total_size', 0), file.file_size)
            used_limit(USER_ID, (db_data.get('used_limit', 0) + file.file_size))
        except Exception as db_err:
            logger.error(f"Database update failed: {db_err}")

    except Exception as e:
        logger.error(f"Worker Error: {e}")
        await bot.send_message(CHAT_ID, f"❌ **Error occurred:** `{e}`")
    
    finally:
        # Cleanup
        for p in [processed_path, ph_path, download_path]:
            if p and os.path.exists(p): os.remove(p)
        
        await bot.stop()
        if app: await app.stop()

if __name__ == "__main__":
    asyncio.run(run_worker())
