import os, json, time, asyncio, logging, subprocess
from pyrogram import Client, errors, enums
import pyrogram.utils

# 1. High-Stability Config
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999
WORKERS = 30 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from helper.database import find, used_limit, total_rename, total_size, find_one, dbcol
from helper.ffmpeg import fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

# Load Payload with deep safety
PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
try:
    payload = json.loads(PAYLOAD_RAW)
except:
    try: payload = eval(PAYLOAD_RAW)
    except: payload = {}

# --- TYPE-SAFE VARIABLE EXTRACTION ---
# Force everything to the correct type immediately
try:
    CHAT_ID = int(str(payload.get("chat_id")).strip())
    USER_ID = int(str(payload.get("user_id")).strip())
    MSG_ID = int(str(payload.get("message_id")).strip())
except (ValueError, TypeError) as e:
    logger.error(f"Failed to parse IDs: {e}")
    CHAT_ID = USER_ID = MSG_ID = 0

NEW_NAME = str(payload.get("new_name", "file.mkv"))
MEDIA_TYPE = str(payload.get("media_type", "document"))
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = bool(payload.get("metadata_status", False))
METADATA_TEXT = str(payload.get("metadata_text", "By @TechifyBots"))

# 2. Setup Client
bot = Client(
    "BotWorkerSession", 
    api_id=int(API_ID), 
    api_hash=str(API_HASH),
    bot_token=str(BOT_TOKEN), 
    workers=WORKERS
)

def get_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        duration = subprocess.check_output(cmd, shell=True).decode().strip()
        return int(float(duration))
    except: return 0

async def run_worker():
    # Variables initialized to None for safety in finally block
    path = processed_path = ph_path = status_msg = None

    try:
        # Start Client
        await bot.start()
        logger.info(f"STEP 1: Bot Started for Chat {CHAT_ID}")

        # 3. Fetch Message (Using Positional Arguments for maximum compatibility)
        try:
            msg = await bot.get_messages(CHAT_ID, MSG_ID)
            file = msg.document or msg.video or msg.audio
        except Exception as e:
            logger.error(f"STEP 2 ERROR: Fetching failed: {e}")
            return

        if not file:
            await bot.send_message(CHAT_ID, "❌ **Error:** File not found.")
            return

        # 4. Progress Message
        status_msg = await bot.send_message(CHAT_ID, "<b>🚀 Cloud Worker Started...</b>")
        logger.info("STEP 3: Progress Message Sent")

        os.makedirs("downloads", exist_ok=True)
        download_path = f"downloads/{int(time.time())}_{file.file_name if file.file_name else 'file'}"
        
        # 5. Download
        c_time = time.time()
        path = await bot.download_media(
            message=file, file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 DOWNLOADING", status_msg, c_time)
        )
        logger.info("STEP 4: Download Complete")

        # 6. Processing
        if METADATA_STATUS:
            meta_path = f"downloads/meta_{NEW_NAME}"
            res = await add_metadata(path, meta_path, METADATA_TEXT, status_msg)
            processed_path = res if res and os.path.exists(res) else path
        else:
            processed_path = f"downloads/{NEW_NAME}"
            os.rename(path, processed_path)
        logger.info("STEP 5: Processing Complete")

        # 7. Thumbnail & Caption
        if THUMB_ID:
            try: ph_path = await bot.download_media(THUMB_ID)
            except: ph_path = None
            
        caption = f"**{NEW_NAME}**"
        if CUSTOM_CAPTION:
            try:
                caption = escape_invalid_curly_brackets(CUSTOM_CAPTION, ["filename", "filesize"]).format(
                    filename=NEW_NAME, filesize=humanbytes(file.file_size))
            except: pass

        # 8. Upload
        logger.info("STEP 6: Upload Starting")
        c_time = time.time()
        
        if MEDIA_TYPE == "video":
            await bot.send_video(
                CHAT_ID, video=processed_path, caption=caption, thumb=ph_path,
                duration=get_duration(processed_path), supports_streaming=True,
                progress=progress_for_pyrogram, progress_args=("📤 UPLOADING", status_msg, c_time)
            )
        else:
            await bot.send_document(
                CHAT_ID, document=processed_path, caption=caption, thumb=ph_path,
                progress=progress_for_pyrogram, progress_args=("📤 UPLOADING", status_msg, c_time)
            )
            
        if status_msg: await status_msg.delete()
        logger.info("STEP 7: Task Success")

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        try:
            # Send message to user about the specific error
            await bot.send_message(CHAT_ID, f"❌ **Notification:** Processing failed.\n\n**Reason:** `{str(e)}`")
        except: pass
    
    finally:
        # Cleanup
        for p in [processed_path, ph_path, path]:
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass
        
        # 9. Always Reset database status
        try:
            dbcol.update_one({"_id": USER_ID}, {"$set": {"is_processing": False}})
        except: pass

        await bot.stop(block=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_worker())
