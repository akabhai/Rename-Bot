import os, json, time, asyncio, logging, subprocess
from pyrogram import Client, errors
import pyrogram.utils

# 1. High-Stability Config
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from helper.database import find, used_limit, total_rename, total_size, find_one
from helper.ffmpeg import fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

# Load Payload
PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
payload = json.loads(PAYLOAD_RAW)

# STRICT INTEGER CONVERSION
CHAT_ID = int(payload.get("chat_id", 0))
USER_ID = int(payload.get("user_id", 0))
MSG_ID = int(payload.get("message_id", 0))
LOG_CHANNEL_ID = int(LOG_CHANNEL) # Force config value to int

NEW_NAME = payload.get("new_name", "renamed_file")
MEDIA_TYPE = payload.get("media_type", "document")
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status", False)
METADATA_TEXT = payload.get("metadata_text", "By @TechifyBots")

# 2. Setup Clients
bot = Client("BotWork", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, in_memory=True)
app = Client("PremWork", session_string=STRING_SESSION, api_id=API_ID, api_hash=API_HASH, in_memory=True) if STRING_SESSION else None

def get_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        duration = subprocess.check_output(cmd, shell=True).decode().strip()
        return int(float(duration))
    except: return 0

async def run_worker():
    # Start Clients
    await bot.start()
    if app: await app.start()
    
    processed_path = None
    ph_path = None
    
    try:
        # 3. Fetch File
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        if not file:
            await bot.send_message(CHAT_ID, "❌ Error: File not found.")
            return

        status_msg = await bot.send_message(CHAT_ID, "<b>🚀 Cloud Worker Started...</b>")
        
        # 4. Download
        if not os.path.isdir("downloads"): os.mkdir("downloads")
        download_path = f"downloads/{int(time.time())}_{file.file_name if file.file_name else 'file'}"
        
        c_time = time.time()
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", status_msg, c_time)
        )

        # 5. Processing
        await status_msg.edit("<b>⚙️ Processing...</b>")
        if METADATA_STATUS:
            processed_path = f"downloads/meta_{NEW_NAME}"
            res = await add_metadata(path, processed_path, METADATA_TEXT, status_msg)
            if not res: processed_path = path
        else:
            processed_path = f"downloads/{NEW_NAME}"
            os.rename(path, processed_path)

        # 6. Thumbnail & Caption
        if THUMB_ID:
            ph_path = await bot.download_media(THUMB_ID)
            
        caption = f"**{NEW_NAME}**"
        if CUSTOM_CAPTION:
            caption = escape_invalid_curly_brackets(CUSTOM_CAPTION, ["filename", "filesize"]).format(
                filename=NEW_NAME, filesize=humanbytes(file.file_size))

        # 7. Upload
        await status_msg.edit("<b>📤 Uploading...</b>")
        
        # Select Client & Destination
        # If > 2GB AND app exists, use app. Otherwise use bot.
        use_premium = (file.file_size > 2000000000 and app is not None)
        target = app if use_premium else bot
        dest = LOG_CHANNEL_ID if use_premium else CHAT_ID
        
        c_time = time.time()
        if MEDIA_TYPE == "video":
            sent_file = await target.send_video(
                chat_id=dest, video=processed_path, caption=caption, thumb=ph_path,
                duration=get_duration(processed_path), supports_streaming=True,
                progress=progress_for_pyrogram, progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        else:
            sent_file = await target_client.send_document(
                chat_id=dest, document=processed_path, caption=caption, thumb=ph_path,
                progress=progress_for_pyrogram, progress_args=("🚀 Uploading...", status_msg, c_time)
            )

        if use_premium:
            await bot.copy_message(CHAT_ID, LOG_CHANNEL_ID, sent_file.id)
            
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error: {e}")
        await bot.send_message(CHAT_ID, f"❌ **Error:** `{str(e)}`")
    
    finally:
        # Cleanup
        if processed_path and os.path.exists(processed_path): os.remove(processed_path)
        if ph_path and os.path.exists(ph_path): os.remove(ph_path)
        if 'path' in locals() and os.path.exists(path): os.remove(path)
        
        # SAFE STOP
        if app: await app.stop(block=False)
        await bot.stop(block=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_worker())
