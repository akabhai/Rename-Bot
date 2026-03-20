import os, json, time, asyncio, logging, subprocess
from pyrogram import Client, errors
import pyrogram.utils

# 1. High-Stability Config
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999
WORKERS = 30 # Safe limit to avoid Telegram internal conflicts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import helpers and Database collection
from helper.database import find, used_limit, total_rename, total_size, find_one, dbcol
from helper.ffmpeg import fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

# Load Payload
PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
try:
    payload = json.loads(PAYLOAD_RAW)
except:
    payload = eval(PAYLOAD_RAW)

# IDs AND SETTINGS
CHAT_ID = int(payload.get("chat_id", 0))
USER_ID = int(payload.get("user_id", 0))
MSG_ID = int(payload.get("message_id", 0))

NEW_NAME = payload.get("new_name", "renamed_file")
MEDIA_TYPE = payload.get("media_type", "document")
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status", False)
METADATA_TEXT = payload.get("metadata_text", "By @TechifyBots")

# 2. Setup Client
bot = Client(
    "BotWorkerSession", 
    bot_token=BOT_TOKEN, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    workers=WORKERS
)

def get_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        duration = subprocess.check_output(cmd, shell=True).decode().strip()
        return int(float(duration))
    except: return 0

async def run_worker():
    # 1. Authorize with Timeout
    try:
        await asyncio.wait_for(bot.start(), timeout=120)
    except Exception as e:
        logger.error(f"Login Failed: {e}")
        return

    processed_path = None
    ph_path = None
    path = None
    
    try:
        # 2. Fetch File with Retry
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        if not file:
            await bot.send_message(CHAT_ID, "❌ **Error:** Source file link expired.")
            return

        status_msg = await bot.send_message(CHAT_ID, "<b>🚀 Cloud Worker Active...</b>\n<i>Don't worry, you can use other commands; I'm working in the background!</i>")
        
        if not os.path.isdir("downloads"): os.mkdir("downloads")
        download_path = f"downloads/{int(time.time())}_{file.file_name if file.file_name else 'file'}"
        
        # 3. HEARTBEAT: Keep Telegram connection alive
        await bot.send_chat_action(CHAT_ID, "record_video") # Signals "working" status

        # 4. Download
        c_time = time.time()
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 DOWNLOADING", status_msg, c_time)
        )

        # 5. Fast Processing (FFmpeg)
        if METADATA_STATUS:
            processed_path = f"downloads/meta_{NEW_NAME}"
            res = await add_metadata(path, processed_path, METADATA_TEXT, status_msg)
            if not res: processed_path = path
        else:
            processed_path = f"downloads/{NEW_NAME}"
            os.rename(path, processed_path)

        # 6. Thumbnail
        if THUMB_ID:
            try: ph_path = await bot.download_media(THUMB_ID)
            except: ph_path = None
            
        caption = f"**{NEW_NAME}**"
        if CUSTOM_CAPTION:
            caption = escape_invalid_curly_brackets(CUSTOM_CAPTION, ["filename", "filesize"]).format(
                filename=NEW_NAME, filesize=humanbytes(file.file_size))

        # 7. Safe High-Speed Upload
        await bot.send_chat_action(CHAT_ID, "upload_document") # Keep connection hot
        c_time = time.time()
        
        if MEDIA_TYPE == "video":
            await bot.send_video(
                chat_id=CHAT_ID, 
                video=processed_path, 
                caption=caption, 
                thumb=ph_path,
                duration=get_duration(processed_path), 
                supports_streaming=True,
                progress=progress_for_pyrogram, 
                progress_args=("📤 UPLOADING", status_msg, c_time)
            )
        else:
            await bot.send_document(
                chat_id=CHAT_ID, 
                document=processed_path, 
                caption=caption, 
                thumb=ph_path,
                progress=progress_for_pyrogram, 
                progress_args=("📤 UPLOADING", status_msg, c_time)
            )
            
        await status_msg.delete()

    except errors.FloodWait as e:
        logger.warning(f"FloodWait encountered: {e.value}")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Worker Exception: {e}")
        try: await bot.send_message(CHAT_ID, f"❌ **Notification:** Processing interrupted for `{NEW_NAME}`. Please try again.")
        except: pass
    
    finally:
        # Safety Cleanup
        if processed_path and os.path.exists(processed_path): os.remove(processed_path)
        if ph_path and os.path.exists(ph_path): os.remove(ph_path)
        if path and os.path.exists(path): os.remove(path)
        
        # Unlock user status in MongoDB
        try:
            dbcol.update_one({"_id": USER_ID}, {"$set": {"is_processing": False}})
        except Exception as db_err:
            logger.error(f"Failed to reset user busy status: {db_err}")

        # Shutdown client gracefully
        await bot.stop(block=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_worker())
