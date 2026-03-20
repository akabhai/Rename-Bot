import os, json, time, asyncio, logging, subprocess
from pyrogram import Client, errors
import pyrogram.utils

# 1. High-Stability & Safe-Speed Config
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999
WORKERS = 30 # Safe worker limit as discussed

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
payload = json.loads(PAYLOAD_RAW)

# IDs AND SETTINGS
CHAT_ID = int(payload.get("chat_id", 0))
USER_ID = int(payload.get("user_id", 0))
MSG_ID = int(payload.get("message_id", 0))
LOG_CHANNEL_ID = int(LOG_CHANNEL or 0) 

NEW_NAME = payload.get("new_name", "renamed_file")
MEDIA_TYPE = payload.get("media_type", "document")
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status", False)
METADATA_TEXT = payload.get("metadata_text", "By @TechifyBots")

# 2. Setup Client (Optimized for Session Caching)
bot = Client(
    "BotWorkerSession", 
    bot_token=BOT_TOKEN, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    workers=WORKERS
)

app = None # String session not used as per your request

def get_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        duration = subprocess.check_output(cmd, shell=True).decode().strip()
        return int(float(duration))
    except: return 0

async def run_worker():
    # Start Client
    try:
        await bot.start()
    except errors.FloodWait as e:
        logger.error(f"Telegram login blocked! Wait {e.value} seconds.")
        return

    processed_path = None
    ph_path = None
    path = None
    
    try:
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        if not file: return

        status_msg = await bot.send_message(CHAT_ID, "<b>🚀 High-Speed Worker Started...</b>")
        
        # 4. Download Phase
        if not os.path.isdir("downloads"): os.mkdir("downloads")
        download_path = f"downloads/{int(time.time())}_{file.file_name if file.file_name else 'file'}"
        
        c_time = time.time()
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 DOWNLOADING", status_msg, c_time)
        )

        # 5. Processing
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
        await status_msg.edit("<b>📤 Preparing High-Speed Upload...</b>")
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

    except Exception as e:
        logger.error(f"Error: {e}")
        try: await bot.send_message(CHAT_ID, f"❌ **Error:** `{str(e)}`")
        except: pass
    
    finally:
        # Cleanup local files
        if processed_path and os.path.exists(processed_path): os.remove(processed_path)
        if ph_path and os.path.exists(ph_path): os.remove(ph_path)
        if path and os.path.exists(path): os.remove(path)
        
        # --- NEW: UNLOCK USER STATUS IN DATABASE ---
        try:
            dbcol.update_one({"_id": USER_ID}, {"$set": {"is_processing": False}})
            logger.info(f"User {USER_ID} has been unlocked.")
        except Exception as db_err:
            logger.error(f"Database Reset Error: {db_err}")
        # --------------------------------------------

        await bot.stop(block=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_worker())
