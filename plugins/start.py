from datetime import date as date_
import os, re, datetime, random, asyncio, time, humanize
from pyrogram import Client, filters, enums
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)
from helper.database import insert, find_one, botdata, total_rename, total_size
from pyrogram.file_id import FileId
from config import *

# Replace with your actual GitHub link
GITHUB_SITE_URL = "https://akapass.github.io"

@Client.on_message(filters.private & filters.command(["start"]))
async def start(client, message):
    user_id = message.chat.id
    insert(int(user_id))
    
    text = f"👋 Hello {message.from_user.mention}!\n\nɪ  ᴀᴍ  ᴀɴ  ᴀᴅᴠᴀɴᴄᴇ  ꜰɪʟᴇ  ʀᴇɴᴀᴍᴇʀ  ᴀɴᴅ  ᴄᴏɴᴠᴇʀᴛᴇʀ  ʙᴏᴛ.\n\nᴊᴜsᴛ  sᴇɴᴅ  ᴍᴇ  ᴀɴʏ  ᴠɪᴅᴇᴏ  ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ !!\n\n<b>Owned By : @tgbots_bynexa</b>"
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/tgbots_bynexa"),
         InlineKeyboardButton("💬 Support", url="https://t.me/feedbackprozbot")]
    ])
    
    await message.reply_photo(photo=START_PIC, caption=text, reply_markup=button)

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def send_doc(client, message):
    user_id = message.from_user.id    
    insert(int(user_id))

    # 1. Fetch data from MongoDB
    user_deta = find_one(user_id)
    # Get the field updated by the Flask app
    unlimited_expiry = user_deta.get("unlimited_expiry", 0)
    
    # 2. Check if current time is less than expiry
    if time.time() < unlimited_expiry:
        # --- ACCESS GRANTED ---
        media = message.document or message.video or message.audio
        dcid = FileId.decode(media.file_id).dc_id
        
        # Logic for bot stats
        bot_token = BOT_TOKEN
        botid = bot_token.split(':')[0]
        botdata(int(botid))
        bot_info = find_one(int(botid))
        total_rename(int(botid), bot_info.get('total_rename', 0))
        total_size(int(botid), bot_info.get('total_size', 0), media.file_size)

        return await message.reply_text(
            f"✅ **Access Granted!** (Unlimited Mode)\n"
            f"⏳ **Expires in:** `{int((unlimited_expiry - time.time()) / 60)} min`\n\n"
            f"**File Name :** `{media.file_name}`\n"
            f"**File Size :** {humanize.naturalsize(media.file_size)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Rename", callback_data="rename"),
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ])
        )
    
    else:
        # --- ACCESS DENIED ---
        # Generate the dynamic link
        # api={RENDER_URL} tells the GitHub site where to send the verify request
        verify_link = f"{GITHUB_SITE_URL}/?uid={user_id}&api={RENDER_URL}"
        
        button = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Unlock 6h Access (Watch Ads)", url=verify_link)
        ]])
        
        return await message.reply_photo(
            photo=START_PIC,
            caption=(
                f"❌ **Access Denied!**\n\n"
                f"To use the renaming service, please complete the short verification.\n"
                f"Verification gives you **6 Hours of Unlimited Access**.\n\n"
                f"**User ID:** <code>{user_id}</code>"
            ),
            reply_markup=button
        )
