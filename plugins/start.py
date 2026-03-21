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

# Local humanbytes to fix Circular Import
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
    
    loading_sticker_message = await message.reply_sticker("CAACAgUAAxkBAAJ93Wb23tu2uAf_XIY2qORqOoURNsPTAAIoEQACQVaxV35FIcz8xQdgNgQ")
    await asyncio.sleep(2)
    await loading_sticker_message.delete()
    
    text = f"""{message.from_user.mention} \nɪ  ᴀᴍ  ᴀɴ  ᴀᴅᴠᴀɴᴄᴇ  ꜰɪʟᴇ  ʀᴇɴᴀᴍᴇʀ  ᴀɴᴅ  ᴄᴏɴᴠᴇʀᴛᴇʀ  ʙᴏᴛ  ᴡɪᴛʜ  ᴘᴇʀᴍᴀɴᴇɴᴛ  ᴀɴᴅ  ᴄᴜsᴛᴏᴍ  ᴛʜᴜᴍʙɴᴀɪʟ  sᴜᴘᴘᴏʀᴛ.\n\nᴊᴜsᴛ  sᴇɴᴅ  ᴍᴇ  ᴀɴʏ  ᴠɪᴅᴇᴏ  ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ !!\nᴏᴡɴᴇʀ @TechifyBots</b>"""
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url="https://telegram.me/TechifyBots"),
        InlineKeyboardButton("💬 Support", url="https://telegram.me/TechifySupport")],
        [InlineKeyboardButton("🛠️ Help", callback_data='help'),
        InlineKeyboardButton("❤️‍🩹 About", callback_data='about')],
        [InlineKeyboardButton("🧑‍💻 Developer 🧑‍💻", url="https://telegram.me/TechifyBots")]
        ])
    
    await message.reply_photo(photo=START_PIC, caption=text, reply_markup=button, quote=True)
    return    

@Client.on_message((filters.private & (filters.document | filters.audio | filters.video)) | filters.channel & (filters.document | filters.audio | filters.video))
async def send_doc(client, message):
    user_id = message.from_user.id    
    insert(int(user_id))
        
    if FORCE_SUBS:
        try:
            await client.get_chat_member(FORCE_SUBS, user_id)
        except UserNotParticipant:
            _newus = find_one(user_id)
            user = _newus["usertype"]
            await message.reply_text("<b>Hello Dear \n\nYou Need To Join In My Channel To Use Me\n\nKindly Please Join Channel</b>",
                reply_to_message_id=message.id,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔺 Update Channel 🔺", url=f"https://t.me/{FORCE_SUBS}")]]))
            return
		
    botdata(int(botid))
    bot_data = find_one(int(botid))
    prrename = bot_data.get('total_rename', 0)
    prsize = bot_data.get('total_size', 0)
    user_deta = find_one(user_id)
    
    # --- NEW: ADS SYSTEM CHECK ---
    unlimited_expiry = user_deta.get("unlimited_expiry", 0)
    is_unlimited = time.time() < unlimited_expiry
    # -----------------------------

    used_date = user_deta["date"]
    buy_date = user_deta["prexdate"]
    daily = user_deta["daily"]
    user_type = user_deta["usertype"]

    c_time = time.time()

    # Skip flood control for unlimited users
    if not is_unlimited:
        if user_type == "Free":
            LIMIT = 120
        else:
            LIMIT = 10
        then = used_date + LIMIT
        left = round(then - c_time)
        if left > 0:
            conversion = datetime.timedelta(seconds=left)
            return await message.reply_text(f"<b>Flood Control Is Active. Please Wait For {str(conversion)} </b>", reply_to_message_id=message.id)

    media = message.document or message.video or message.audio
    dcid = FileId.decode(media.file_id).dc_id
    filename = media.file_name
    used = user_deta["used_limit"]
    limit = user_deta["uploadlimit"]

    # 1. Logic for UNLIMITED users (Ads watched)
    if is_unlimited:
        time_left = int((unlimited_expiry - time.time()) / 60)
        total_rename(int(botid), prrename)
        total_size(int(botid), prsize, media.file_size)
        return await message.reply_text(
            f"🚀 **Unlimited Mode Active!**\nAccess expires in: `{time_left} min`\n\n**File:** `{filename}`\n**Size:** {humanize.naturalsize(media.file_size)}",
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Rename", callback_data="rename"), InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]])
        )

    # 2. Logic for Standard users (Limit checks)
    expi = daily - int(time.mktime(time.strptime(str(date_.today()), '%Y-%m-%d')))
    if expi != 0:
        daily_(user_id, int(time.mktime(time.strptime(str(date_.today()), '%Y-%m-%d'))))
        used_limit(user_id, 0)
        used = 0

    remain = limit - used
    if remain < int(media.file_size):
        # Provide both Upgrade and Ad-Watch option
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Upgrade Plan", callback_data="upgrade")],
            [InlineKeyboardButton("🔓 Watch Ads to Unlock 6h", web_app=WebAppInfo(url=f"https://my-renamer-bot.onrender.com/{user_id}"))]
        ])
        return await message.reply_text(f"Daily Quota Exhausted.\n\n<b>Used:</b> {humanbytes(used)}\n<b>Limit:</b> {humanbytes(limit)}\n\nWatch 3 ads to unlock 6 hours of unlimited processing!", reply_markup=button)

    if media.file_size > 2147483648 and not STRING_SESSION:
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Upgrade Plan", callback_data="upgrade")],
            [InlineKeyboardButton("🔓 Watch Ads to Unlock 6h", web_app=WebAppInfo(url=f"https://my-renamer-bot.onrender.com/{user_id}"))]
        ])
        return await message.reply_text("You Can't Upload More Than 2GB on Free Plan.\n\nWatch ads to bypass this limit for 6 hours!", reply_markup=button)

    # Check Plan Expiry
    if buy_date:
        if not check_expi(buy_date):
            uploadlimit(user_id, 2147483648)
            usertype(user_id, "Free")
    
    total_rename(int(botid), prrename)
    total_size(int(botid), prsize, media.file_size)
    
    await message.reply_text(
        f"__What Do You Want Me To Do With This File ?__\n\n**File Name :** `{filename}`\n**File Size :** {humanize.naturalsize(media.file_size)}\n**DC ID :** {dcid}",
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Rename", callback_data="rename"), InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]])
    )
