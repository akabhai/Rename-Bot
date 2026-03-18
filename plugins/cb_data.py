import os
import json
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from helper.database import find, dateupdate, find_one
from config import *

# ADD THIS LINE - It fixes the ImportError
app = Client("PremiumClient", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION) if STRING_SESSION else None

# GitHub Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
        await update.message.reply_to_message.delete()
    except:
        await update.message.delete()

@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    chat_id = update.message.chat.id
    msg_id = update.message.reply_to_message_id
    await update.message.delete()
    await update.message.reply_text(
        "__Please Enter The New Filename...__\n\n**Note :** Extension Not Required",
        reply_to_message_id=msg_id,
        reply_markup=ForceReply(True)
    )

@Client.on_callback_query(filters.regex("upload_document|upload_video|upload_audio"))
async def trigger_worker(bot, update):
    user_id = update.from_user.id
    chat_id = update.message.chat.id
    file_msg = update.message.reply_to_message
    
    # Extract name from "Select Output Type\n\nFile Name :- name.mkv"
    try:
        new_name = update.message.text.split(":-")[-1].strip()
    except:
        new_name = "renamed_file"
        
    media_type = update.data.split("_")[1] 

    user_data = find(user_id)
    thumb_id = user_data[0]
    caption = user_data[1]
    metadata_status = user_data[2]
    metadata_text = user_data[3]

    if not GITHUB_TOKEN or not GITHUB_REPO:
        return await update.message.edit("<b>❌ Admin Error:</b> `GITHUB_TOKEN` or `GITHUB_REPO` missing!")

    await update.message.edit("<b>⏳ Signaling Cloud Worker (GitHub)...</b>")

    payload_data = {
        "chat_id": chat_id,
        "user_id": user_id,
        "message_id": file_msg.id,
        "new_name": new_name,
        "media_type": media_type,
        "thumb_id": thumb_id,
        "caption": caption,
        "metadata_status": metadata_status,
        "metadata_text": metadata_text,
        "log_channel": LOG_CHANNEL
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    json_body = {
        "event_type": "start_rename",
        "client_payload": {"data": payload_data}
    }

    try:
        response = requests.post(dispatch_url, headers=headers, json=json_body)
        if response.status_code == 204:
            await update.message.edit(f"<b>🚀 Worker Assigned!</b>\n\n<b>📁 File:</b> `{new_name}`\n<b>⚡ Status:</b> Processing on GitHub...")
        else:
            await update.message.edit(f"<b>❌ GitHub Error:</b> {response.status_code}")
    except Exception as e:
        await update.message.edit(f"<b>❌ Request Failed:</b> {str(e)}")
