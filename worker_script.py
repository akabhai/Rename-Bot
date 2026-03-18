import os
import json
import time
import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from datetime import timedelta

# Import your existing helpers
from helper.database import find, used_limit, total_rename, total_size, find_one
from helper.ffmpeg import take_screen_shot, fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

# Load Payload from GitHub Environment
PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
payload = json.loads(PAYLOAD_RAW)

# Extract Data from Payload
CHAT_ID = int(payload.get("chat_id"))
USER_ID = int(payload.get("user_id"))
MSG_ID = int(payload.get("message_id"))
NEW_NAME = payload.get("new_name")
MEDIA_TYPE = payload.get("media_type") # document, video, or audio
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status")
METADATA_TEXT = payload.get("metadata_text")

# Initialize Clients
bot = Client("BotWorker", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
# Premium Client for 4GB
app = Client("PremiumWorker", session_string=STRING_SESSION, api_id=API_ID, api_hash=API_HASH) if STRING_SESSION else None

async def run_worker():
    await bot.start()
    if app: await app.start()
    
    # 1. Get the File Message
    try:
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        if not file:
            await bot.send_message(CHAT_ID, "❌ Error: Original file not found.")
            return
    except Exception as e:
        print(f"Error fetching message: {e}")
        return

    status_msg = await bot.send_message(CHAT_ID, "<b>📥 Worker started downloading from Telegram...</b>")
    
    # 2. Setup Paths
    if not os.path.isdir("downloads"): os.mkdir("downloads")
    if not os.path.isdir("Metadata"): os.mkdir("Metadata")
    
    download_path = f"downloads/{file.file_name}"
    final_path = f"downloads/{NEW_NAME}"
    metadata_path = f"Metadata/{NEW_NAME}"
    
    # 3. Download
    c_time = time.time()
    try:
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", status_msg, c_time)
        )
    except Exception as e:
        await status_msg.edit(f"❌ Download Error: {e}")
        return

    # 4. Processing (Metadata / Rename)
    await status_msg.edit("<b>⚙️ Processing File (FFmpeg)...</b>")
    
    if METADATA_STATUS and METADATA_TEXT:
        processed_path = await add_metadata(path, metadata_path, METADATA_TEXT, status_msg)
        if not processed_path:
            processed_path = path # Fallback if metadata fails
            os.rename(path, final_path)
            processed_path = final_path
    else:
        os.rename(path, final_path)
        processed_path = final_path

    # 5. Handle Thumbnail
    ph_path = None
    if THUMB_ID:
        ph_path = await bot.download_media(THUMB_ID)
        # Fix thumbnail size for Telegram
        img = Image.open(ph_path).convert("RGB")
        img.resize((320, 320))
        img.save(ph_path, "JPEG")
    
    # 6. Prepare Caption
    if CUSTOM_CAPTION:
        cap_list = ["filename", "filesize"]
        clean_cap = escape_invalid_curly_brackets(CUSTOM_CAPTION, cap_list)
        caption = clean_cap.format(filename=NEW_NAME, filesize=humanbytes(file.file_size))
    else:
        caption = f"**{NEW_NAME}**"

    # 7. Uploading
    await status_msg.edit("<b>📤 Uploading to Telegram Cloud...</b>")
    c_time = time.time()
    
    try:
        target_client = app if (file.file_size > 2097152000 and app) else bot
        
        if MEDIA_TYPE == "video":
            # Get duration
            duration = 0
            metadata = extractMetadata(createParser(processed_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds

            sent_file = await target_client.send_video(
                CHAT_ID if target_client == bot else LOG_CHANNEL,
                video=processed_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        elif MEDIA_TYPE == "audio":
            sent_file = await target_client.send_audio(
                CHAT_ID if target_client == bot else LOG_CHANNEL,
                audio=processed_path,
                caption=caption,
                thumb=ph_path,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        else:
            sent_file = await target_client.send_document(
                CHAT_ID if target_client == bot else LOG_CHANNEL,
                document=processed_path,
                caption=caption,
                thumb=ph_path,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )

        # If uploaded via Premium Client to Log Channel, copy it to User
        if target_client == app:
            await bot.copy_message(CHAT_ID, LOG_CHANNEL, sent_file.id)

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Upload Error: {e}")
    
    # 8. Stats Update & Cleanup
    total_rename(int(USER_ID), find_one(int(USER_ID))['total_rename'])
    total_size(int(USER_ID), find_one(int(USER_ID))['total_size'], file.file_size)
    used_limit(USER_ID, (find_one(USER_ID)['used_limit'] + file.file_size))

    # Cleanup files
    if os.path.exists(processed_path): os.remove(processed_path)
    if ph_path and os.path.exists(ph_path): os.remove(ph_path)
    if os.path.exists(download_path): os.remove(download_path)

    await bot.stop()
    if app: await app.stop()

if __name__ == "__main__":
    asyncio.run(run_worker())
