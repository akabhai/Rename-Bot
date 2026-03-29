import os, time, humanize
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import find_one, insert, botdata, total_rename, total_size
from config import *

# Replace with your actual GitHub link
GITHUB_SITE_URL = "https://akapass.github.io"

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def send_doc(client, message):
    user_id = message.from_user.id    
    insert(int(user_id))

    # 1. Fetch data using your existing helper
    user_deta = find_one(user_id)
    
    # 2. Get unlimited_expiry (defaults to 0 if not found)
    unlimited_expiry = user_deta.get("unlimited_expiry", 0)
    
    # 3. Check Access
    if time.time() < unlimited_expiry:
        # --- ACCESS GRANTED ---
        media = message.document or message.video or message.audio
        time_left = int((unlimited_expiry - time.time()) / 60)
        
        return await message.reply_text(
            f"✅ **Access Granted!** (Unlimited Mode)\n"
            f"⏳ **Expires in:** `{time_left} min`\n\n"
            f"**File:** `{media.file_name}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Rename", callback_data="rename"),
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ])
        )
    
    else:
        # --- ACCESS DENIED ---
        # Passing 'api' parameter so GitHub knows where to send success signal
        verify_link = f"{GITHUB_SITE_URL}/?uid={user_id}&api={RENDER_URL}"
        
        button = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔓 Unlock 6h Access (Watch Ads)", url=verify_link)
        ]])
        
        return await message.reply_photo(
            photo=START_PIC,
            caption=(
                f"❌ **Access Denied!**\n\n"
                f"To use the renaming service, please complete the short verification.\n"
                f"This will unlock **6 Hours of Unlimited Access**.\n\n"
                f"**User ID:** <code>{user_id}</code>"
            ),
            reply_markup=button
        )
