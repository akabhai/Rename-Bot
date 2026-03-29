import os, json, requests, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.errors import MessageNotModified
from helper.database import find, find_one, dbcol
from config import *

# --- RESTORE THIS LINE (The one bot.py is looking for) ---
app = Client("PremiumClient", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION) if STRING_SESSION else None
# ---------------------------------------------------------

@Client.on_callback_query(filters.regex("reset_status"))
async def reset_status(bot, update):
    user_id = update.from_user.id
    dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
    await update.message.edit("✅ **Processing status has been reset!**")

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
    except:
        pass

@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    if not update.message: return
    # This asks the user for the new name using ForceReply
    await update.message.delete()
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="__Please Enter The New Filename...__\n\n**Note :** Extension Not Required",
        reply_to_message_id=update.message.reply_to_message.id,
        reply_markup=ForceReply(True)
    )

# --- THIS HANDLES THE FILENAME TEXT RESPONSE ---
@Client.on_message(filters.private & filters.reply & filters.text)
async def filename_handler(bot, message):
    if message.reply_to_message.text and "Please Enter The New Filename" in message.reply_to_message.text:
        new_name = message.text
        
        buttons = [[
            InlineKeyboardButton("📁 Document", callback_data="upload_document"),
            InlineKeyboardButton("🎥 Video", callback_data="upload_video")
        ]]
        
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"**New Name:** `{new_name}`\n\nSelect the media type:",
            reply_to_message_id=message.reply_to_message.reply_to_message_id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- TRIGGER WORKER ---
@Client.on_callback_query(filters.regex("upload_document|upload_video"))
async def trigger_worker(bot, update):
    await update.answer()
    user_id = update.from_user.id
    
    user_info = find_one(user_id)
    if user_info and user_info.get("is_processing"):
        return await update.message.edit(
            "❌ **Wait!** Your one file is already in processing.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Reset Status", callback_data="reset_status")]])
        )

    # Extract name from the message text
    try:
        new_name = update.message.text.split("**New Name:** `")[1].split("`")[0].strip()
    except:
        new_name = "renamed_file.mkv"

    dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": True}})
    media_type = update.data.split("_")[1] 
    file_msg = update.message.reply_to_message

    await update.message.edit("<b>⏳ Signaling Cloud Worker...</b>")

    user_data = find(user_id)
    payload_data = {
        "chat_id": int(update.message.chat.id), 
        "user_id": int(user_id), 
        "message_id": int(file_msg.id),
        "new_name": new_name, 
        "media_type": media_type,
        "thumb_id": user_data[0], 
        "log_channel": int(LOG_CHANNEL)
    }

    # Dispatch to GitHub
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    
    try:
        requests.post(dispatch_url, headers=headers, json={"event_type": "start_rename", "client_payload": {"data": payload_data}})
        await update.message.edit(f"<b>🚀 Worker Assigned!</b>\n\n<b>📁 Name:</b> `{new_name}`")
    except:
        dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
        await update.message.edit("❌ Failed to contact worker.")
