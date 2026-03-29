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

# --- 1. RESET STATUS HANDLER ---
@Client.on_callback_query(filters.regex("reset_status"))
async def reset_status(bot, update):
    user_id = update.from_user.id
    dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
    await update.message.edit("✅ **Processing status has been reset!**\nYou can now start renaming a new file.")

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        if update.message:
            await update.message.delete()
    except:
        pass

# --- 2. RENAME BUTTON CLICKED ---
@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    if not update.message: return
    msg_id = update.message.reply_to_message_id
    await update.message.delete()
    
    # Send ForceReply to ask for the new name
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="__Please Enter The New Filename...__\n\n**Note :** Extension Not Required",
        reply_to_message_id=msg_id,
        reply_markup=ForceReply(True)
    )

# --- 3. THIS CATCHES THE NEW NAME YOU TYPE (CRITICAL FIX) ---
@Client.on_message(filters.private & filters.reply & filters.text)
async def catch_new_name(bot, message):
    # Check if user is replying to the exact prompt
    if message.reply_to_message.text and "Please Enter The New Filename" in message.reply_to_message.text:
        new_name = message.text
        original_msg_id = message.reply_to_message.reply_to_message_id
        
        # Clean up the chat history
        await message.delete()
        await message.reply_to_message.delete()
        
        # Show media type buttons and store the new name in the text
        buttons = [
            [InlineKeyboardButton("📁 Document", callback_data="upload_document"),
             InlineKeyboardButton("🎥 Video", callback_data="upload_video")],
            [InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")]
        ]
        
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"**New Name:** `{new_name}`\n\nSelect the output format:",
            reply_to_message_id=original_msg_id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- 4. TRIGGER WORKER AFTER SELECTING FORMAT ---
@Client.on_callback_query(filters.regex("upload_document|upload_video|upload_audio"))
async def trigger_worker(bot, update):
    await update.answer()
    
    if not update.message or not update.message.reply_to_message:
        return await update.message.edit("❌ Error: Message expired.")

    user_id = update.from_user.id
    chat_id = update.message.chat.id
    file_msg = update.message.reply_to_message

    # QUEUE CHECK
    user_info = find_one(user_id)
    if user_info and user_info.get("is_processing"):
        return await update.message.edit(
            "❌ **Wait!** Your one file is already in processing.\n\nIf you think this is a mistake, click the button below to reset.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Reset Processing Status", callback_data="reset_status")
            ]])
        )

    # MARK USER AS BUSY
    dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": True}})

    # CRITICAL FIX: Extract the typed name from the message text
    try:
        raw_text = update.message.text
        # Extracts "design" from "**New Name:** `design`"
        new_name = raw_text.split("**New Name:** ")[1].split("\n")[0].replace("`", "").strip()
    except Exception as e:
        print(f"Error parsing name: {e}")
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
            await update.message.edit(f"<b>🚀 Worker Assigned!</b>\n\n<b>📁 Name:</b> `{new_name}`\n<b>⚡ Status:</b> Processing on Server...")
        else:
            dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
            await update.message.edit(f"<b>❌ GitHub Error:</b> {response.status_code}")
    except Exception as e:
        dbcol.update_one({"_id": user_id}, {"$set": {"is_processing": False}})
        await update.message.edit(f"<b>❌ Request Failed:</b> {str(e)}")
