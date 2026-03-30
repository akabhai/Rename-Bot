from datetime import date as date_
import os, re, datetime, random, asyncio, time, humanize
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

token = BOT_TOKEN
botid = token.split(':')[0]
NEW_START_PIC = "https://i.ibb.co/yc631jGC/Generated-Image-March-21-2026-8-18-PM.png"

# --- YOUR GITHUB SITE URL ---
GITHUB_SITE_URL = "https://akapass.github.io"

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
        except Exception:
            pass

    # Fetch User data safely
    user_deta = find_one(user_id)
    if user_deta:
        unlimited_expiry = user_deta.get("unlimited_expiry", 0)
    else:
        unlimited_expiry = 0
    
    # 1. ACCESS GRANTED
    if time.time() < unlimited_expiry:
        media = message.document or message.video or message.audio
        dcid = FileId.decode(media.file_id).dc_id
        filename = media.file_name
        time_left = int((unlimited_expiry - time.time()) / 60)

        try:
            botdata(int(botid))
            bot_info = find_one(int(botid))
            total_rename(int(botid), bot_info.get('total_rename', 0))
            total_size(int(botid), bot_info.get('total_size', 0), media.file_size)
        except:
            pass

        return await message.reply_text(
            f"✅ **Access Granted!** (Unlimited Mode)\n"
            f"⏳ **Expires in:** `{time_left} min`\n\n"
            f"**File Name :** `{filename}`\n"
            f"**File Size :** {humanize.naturalsize(media.file_size)}\n"
            f"**DC ID :** {dcid}\n\n<b>By : @tgbots_bynexa</b>",
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Rename", callback_data="rename"),
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ])
        )
    
    # 2. ACCESS DENIED (Watch Ads via GitHub Site)
    else:
        # --- NEW DYNAMIC LINK ---
        # Includes bot=Renamer%20Bot to customize the website's title dynamically
        import urllib.parse
        bot_name_encoded = urllib.parse.quote("Renamer Bot")
        verify_link = f"{GITHUB_SITE_URL}/?uid={user_id}&api={RENDER_URL}&bot={bot_name_encoded}"
        
        button = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Watch Ads to Unlock 6h", url=verify_link)
        ]])
        
        return await message.reply_photo(
            photo=NEW_START_PIC,
            caption=(
                f"❌ **Access Denied!**\n\n"
                f"To use the renaming service, please complete the verification to unlock **6 Hours of Unlimited Access**.\n\n"
                f"**User ID:** <code>{user_id}</code>\n"
                f"<b>Owned By : @tgbots_bynexa</b>"
            ),
            reply_markup=button
        )
