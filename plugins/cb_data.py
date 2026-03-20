import os, json, requests, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.errors import MessageNotModified
from helper.database import find, find_one, dbcol
from config import *

# Premium Client Definition
app = Client("PremiumClient", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION) if STRING_SESSION else None

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        if update.message:
            await update.message.delete()
    except:
        pass

@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    if not update.message: return
    msg_id = update.message.reply_to_message_id
    await update.message.delete()
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="__Please Enter The New Filename...__\n\n**Note :** Extension Not Required",
        reply_to_message_id=msg_id,
        reply_markup=ForceReply(True)
    )

@Client.on_callback_query(filters.regex("upload_document|upload_video|upload_audio"))
async def trigger_worker(bot, update):
    # 1. Answer callback to prevent Telegram retries
    await update.answer()
    
    if not update.message or not update.message.reply_to_message:
        return await update.message.edit("❌ Error: Message expired.")

    user_id = update.from_user.id
    chat_id = update.message.chat.id
    file_msg = update.message.reply_to_message

    # 2. PER-USER QUEUE CHECK (Check if user is already processing)
    user_info = find_one(user_id)
    if user_info and user_info.get("is_processing"):
        return await update.message.edit("❌ **Wait!** Your one file is already in processing. Please wait for it to finish before starting another.")

    # 3. MARK USER AS BUSY
    dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": True}})

    try:
        raw_text = update.message.text
        new_name = raw_text.split(":-")[-1].replace("`", "").strip()
    except:
        new_name = "renamed_file.mkv"
        
    media_type = update.data.split("_")[1] 

    try:
        await update.message.edit("<b>⏳ Signaling Cloud Worker (GitHub)...</b>")
    except MessageNotModified:
        pass 

    user_data = find(user_id)
    if not user_data: user_data = [None, None, False, "By @TechifyBots"]

    payload_data = {
        "chat_id": int(chat_id), 
        "user_id": int(user_id), 
        "message_id": int(file_msg.id),
        "new_name": new_name, 
        "media_type": media_type,
        "thumb_id": user_data[0], 
        "caption": user_data[1],
        "metadata_status": user_data[2], 
        "metadata_text": user_data[3],
        "log_channel": int(LOG_CHANNEL)
    }

    if not GITHUB_TOKEN or not GITHUB_REPO:
        dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
        return await update.message.edit("<b>❌ Error: GITHUB_TOKEN or REPO not set!</b>")

    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    
    try:
        response = requests.post(dispatch_url, headers=headers, json={"event_type": "start_rename", "client_payload": {"data": payload_data}})
        if response.status_code == 204:
            await update.message.edit(f"<b>🚀 Worker Assigned!</b>\n\n<b>📁 Name:</b> `{new_name}`\n<b>⚡ Status:</b> Processing on GitHub...")
        else:
            # RESET BUSY STATUS IF GITHUB FAILS TO START
            dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
            await update.message.edit(f"<b>❌ GitHub Error:</b> {response.status_code}")
    except Exception as e:
        # RESET BUSY STATUS ON CRASH
        dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
        await update.message.edit(f"<b>❌ Request Failed:</b> {str(e)}")
