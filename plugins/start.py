from datetime import date as date_
import os, re, datetime, random, asyncio, time, humanize, requests  # Added requests
from script import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram import Client, filters, enums
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo)
from helper.database import botdata, find_one, total_user
from helper.database import insert, find_one, used_limit, usertype, uploadlimit, addpredata, total_rename, total_size
from pyrogram.file_id import FileId
from helper.database import daily as daily_
from helper.date import check_expi
from config import *

# --- CONFIGURATION FOR TBC BOT ---
# 1. Replace with your TBC Webhook URL (The 'api_status' command link)
TBC_API_WEBHOOK = "https://api.telebotcreator.com/v1/webhook/YOUR_CHECK_URL_HERE"
# 2. Replace with your Central Verify Bot Username (without @)
VERIFY_BOT_USERNAME = "YourVerifyBotUsername"
# ---------------------------------

token = BOT_TOKEN
botid = token.split(':')[0]
NEW_START_PIC = "https://i.ibb.co/yc631jGC/Generated-Image-March-21-2026-8-18-PM.png"

def check_tbc_verify_status(user_id):
    """Asks the TBC Verify Bot if the user has access"""
    try:
        # We send the UID and the BID (Bot ID) to the Hub
        payload = {"uid": user_id, "bid": "renamer_bot"}
        response = requests.post(TBC_API_WEBHOOK, json=payload, timeout=5)
        data = response.json()
        return data.get("access", False) # Returns True if verified, False otherwise
    except Exception as e:
        print(f"API Error: {e}")
        return False

def humanbytes(size):
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

@Client.on_message(filters.private & filters.command(["start"]))
async def start(client, message):
    user_id = message.chat.id
    insert(int(user_id))
    
    text = f"""{message.from_user.mention} \nɪ  ᴀᴍ  ᴀɴ  ᴀᴅᴠᴀɴᴄᴇ  ꜰɪʟᴇ  ʀᴇɴᴀᴍᴇʀ  ᴀɴᴅ  ᴄᴏɴᴠᴇʀᴛᴇʀ  ʙᴏᴛ  ᴡɪᴛʜ  ᴘᴇʀᴍᴀɴᴇɴᴛ  ᴀɴᴅ  ᴄᴜsᴛᴏᴍ  ᴛʜᴜᴍʙɴᴀɪʟ  sᴜᴘᴘᴏʀᴛ.\n\nᴊᴜsᴛ  sᴇɴᴅ  ᴍᴇ  ᴀɴʏ  ᴠɪᴅᴇᴏ  ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ !!\n\n<b>Coded By & Owned By : @tgbots_bynexa</b>"""
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://t.me/tgbots_bynexa"),
        InlineKeyboardButton("💬 Support", url="https://t.me/feedbackprozbot")],
        [InlineKeyboardButton("🛠️ Help", callback_data='help')]
        ])
    
    await message.reply_photo(photo=NEW_START_PIC, caption=text, reply_markup=button, quote=True)
    return    

@Client.on_message((filters.private & (filters.document | filters.audio | filters.video)) | filters.channel & (filters.document | filters.audio | filters.video))
async def send_doc(client, message):
    user_id = message.from_user.id    
    insert(int(user_id))
        
    if FORCE_SUBS:
        try:
            await client.get_chat_member(FORCE_SUBS, user_id)
        except UserNotParticipant:
            return await message.reply_text(
                "<b>Kindly Join My Channel to use me!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔺 Update Channel 🔺", url=f"https://t.me/{FORCE_SUBS}")]]))

    # --- UPDATED: ASK TBC BOT FOR ACCESS ---
    is_verified = check_tbc_verify_status(user_id)
    
    # 1. ACCESS GRANTED (Verified via Hub Bot)
    if is_verified:
        media = message.document or message.video or message.audio
        dcid = FileId.decode(media.file_id).dc_id
        filename = media.file_name

        botdata(int(botid))
        bot_info = find_one(int(botid))
        total_rename(int(botid), bot_info.get('total_rename', 0))
        total_size(int(botid), bot_info.get('total_size', 0), media.file_size)

        return await message.reply_text(
            f"✅ **Access Verified!**\n"
            f"Your 6-hour session is currently active.\n\n"
            f"**File Name :** `{filename}`\n"
            f"**File Size :** {humanize.naturalsize(media.file_size)}\n"
            f"**DC ID :** {dcid}\n\n<b>By : @tgbots_bynexa</b>",
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Rename", callback_data="rename"),
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ])
        )
    
    # 2. ACCESS DENIED (Redirect to Central Verify Bot)
    else:
        # Link to your Central Verify Bot on TBC
        verify_link = f"https://t.me/{VERIFY_BOT_USERNAME}?start=verify"
        
        button = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Get 6h Access (Watch Ads)", url=verify_link)
        ]])
        
        return await message.reply_photo(
            photo=NEW_START_PIC,
            caption=(
                f"❌ **Access Denied!**\n\n"
                f"To use the renaming service, you must verify in our **Central Hub**.\n"
                f"Verification gives you **6 Hours of Unlimited Access** to all our bots.\n\n"
                f"**User ID:** <code>{user_id}</code>\n"
                f"<b>Owned By : @tgbots_bynexa</b>"
            ),
            reply_markup=button
        )
