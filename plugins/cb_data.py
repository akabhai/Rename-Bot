import os
import json
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from helper.database import find, dateupdate, find_one
from config import *

# 1. Initialize the Premium Client for bot.py to import (Prevents ImportError)
if STRING_SESSION:
    app = Client("PremiumClient", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
else:
    app = None

# 2. GitHub Configuration (From Render Environment Variables)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
        if update.message.reply_to_message:
            await update.message.reply_to_message.delete()
    except Exception:
        pass

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
    
    # Get the original file message (the one that was replied to)
    file_msg = update.message.reply_to_message
    if not file_msg:
        return await update.message.edit("<b>❌ Error: Original file not found!</b>")
    
    # Extract the new name from the message text (Cleaned version)
    try:
        # Message text format: "**Select Output Type**\n\n**File Name :-** `new_name.mkv`"
        raw_text = update.message.text
        new_name = raw_text.split(":-")[-1].replace("`", "").strip()
    except Exception:
        new_name = "renamed_file.mkv"
        
    media_type = update.data.split("_")[1] # Extract: document, video, or audio

    # Fetch User data from Database
    user_data = find(user_id)
    thumb_id = user_data[0] if user_data else None
    caption = user_data[1] if user_data else None
    metadata_status = user_data[2] if user_data else False
    metadata_text = user_data[3] if user_data else "By @TechifyBots"

    # Security Check
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return await update.message.edit("<b>❌ Admin Error:</b> `GITHUB_TOKEN` or `GITHUB_REPO` is missing in Render Variables!")

    await update.message.edit("<b>⏳ Signaling Cloud Worker (GitHub)...</b>")

    # Prepare Data for GitHub
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

    # Trigger GitHub Action API
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    json_body = {
        "event_type": "start_rename", # This MUST match the 'types' in worker.yml
        "client_payload": {"data": payload_data}
    }

    try:
        response = requests.post(dispatch_url, headers=headers, json=json_body)
        if response.status_code == 204:
            await update.message.edit(
                f"<b>🚀 Worker Assigned Successfully!</b>\n\n"
                f"<b>📁 File:</b> `{new_name}`\n"
                f"<b>⚡ Status:</b> GitHub is processing your file...\n\n"
                "<i>Please wait, you will receive the file shortly.</i>"
            )
        else:
            await update.message.edit(f"<b>❌ GitHub API Error:</b> {response.status_code}\n`{response.text[:100]}`")
    except Exception as e:
        await update.message.edit(f"<b>❌ Request Failed:</b> {str(e)}")
