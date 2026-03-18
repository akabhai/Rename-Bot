import os, json, time, asyncio, logging, subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from datetime import timedelta
import pyrogram.utils

# High-Speed Settings
CHUNK_SIZE = 1024 * 1024 * 10 # 10MB Chunks
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from helper.database import find, used_limit, total_rename, total_size, find_one
from helper.ffmpeg import take_screen_shot, fix_thumb, add_metadata
from helper.progress import progress_for_pyrogram, humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *

PAYLOAD_RAW = os.environ.get("PAYLOAD", "{}")
payload = json.loads(PAYLOAD_RAW)

CHAT_ID = int(payload.get("chat_id", 0))
USER_ID = int(payload.get("user_id", 0))
MSG_ID = int(payload.get("message_id", 0))
NEW_NAME = payload.get("new_name", "renamed_file")
MEDIA_TYPE = payload.get("media_type", "document")
THUMB_ID = payload.get("thumb_id")
CUSTOM_CAPTION = payload.get("caption")
METADATA_STATUS = payload.get("metadata_status", False)
METADATA_TEXT = payload.get("metadata_text", "By @TechifyBots")

bot = Client("GitHubWorker", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, in_memory=True)
app = Client("PremiumGitHubWorker", session_string=STRING_SESSION, api_id=API_ID, api_hash=API_HASH, in_memory=True) if STRING_SESSION else None

def get_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        duration = subprocess.check_output(cmd, shell=True).decode().strip()
        return int(float(duration))
    except:
        return 0

async def run_worker():
    await bot.start()
    if app: await app.start()
    
    try:
        msg = await bot.get_messages(CHAT_ID, MSG_ID)
        file = msg.document or msg.video or msg.audio
        
        status_msg = await bot.send_message(CHAT_ID, "<b>🚀 High-Speed Download Started...</b>")
        
        if not os.path.isdir("downloads"): os.mkdir("downloads")
        download_path = f"downloads/{file.file_name if file.file_name else 'file'}"
        final_path = f"downloads/{NEW_NAME}"
        
        # 1. Faster Download
        c_time = time.time()
        path = await bot.download_media(
            message=file,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading at Cloud Speed", status_msg, c_time)
        )

        # 2. Faster Processing
        await status_msg.edit("<b>⚙️ Applying Metadata (Fast Mode)...</b>")
        if METADATA_STATUS:
            metadata_path = f"downloads/meta_{NEW_NAME}"
            # Modified add_metadata should use -preset ultrafast
            processed_path = await add_metadata(path, metadata_path, METADATA_TEXT, status_msg)
            if not processed_path:
                os.rename(path, final_path)
                processed_path = final_path
        else:
            os.rename(path, final_path)
            processed_path = final_path

        # 3. Handle Thumbnail
        ph_path = None
        if THUMB_ID:
            ph_path = await bot.download_media(THUMB_ID)

        # 4. Prepare Caption
        caption = f"**{NEW_NAME}**"
        if CUSTOM_CAPTION:
            caption = escape_invalid_curly_brackets(CUSTOM_CAPTION, ["filename", "filesize"]).format(
                filename=NEW_NAME, filesize=humanbytes(file.file_size))

        # 5. Faster Upload
        await status_msg.edit("<b>📤 Uploading at Cloud Speed...</b>")
        c_time = time.time()
        
        target_client = app if (file.file_size > 2000000000 and app) else bot
        destination = CHAT_ID if target_client == bot else LOG_CHANNEL
        
        if MEDIA_TYPE == "video":
            duration = get_duration(processed_path)
            sent_file = await target_client.send_video(
                destination, video=processed_path, caption=caption, thumb=ph_path,
                duration=duration, progress=progress_for_pyrogram,
                progress_args=("🚀 Uploading...", status_msg, c_time)
            )
        else:
            sent_file = await target_client.send_document(
                destination, document=processed_path, caption=caption, thumb=ph_path,
                progress=progress_for_pyrogram, progress_args=("🚀 Uploading...", status_msg, c_time)
            )

        if target_client == app:
            await bot.copy_message(CHAT_ID, LOG_CHANNEL, sent_file.id)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error: {e}")
        await bot.send_message(CHAT_ID, f"❌ Error: `{e}`")
    
    finally:
        await bot.stop()
        if app: await app.stop()

if __name__ == "__main__":
    asyncio.run(run_worker())
