from config import *
from pyrogram import Client, filters
from pyrogram.types import ( InlineKeyboardButton, InlineKeyboardMarkup)
from helper.database import botdata, find_one, total_user, getid

token = BOT_TOKEN
botid = token.split(':')[0]

# Added locally to prevent Circular Import Crash
def humanbytes(size):
    if not size: return "0 B"
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

@Client.on_message(filters.private & filters.user(ADMIN)  & filters.command(["users"]))
async def users(client,message):
    botdata(int(botid))
    data = find_one(int(botid))
    total_rename = data.get("total_rename", 0)
    total_size = data.get("total_size", 0)
    
    await message.reply_text(f"<b>⚡️ Total User :</b> {total_user()}\n\n<b>⚡️ Total Renamed File :</b> {total_rename}\n<b>⚡ Total Size Renamed :</b> {humanbytes(int(total_size))}", quote=True, reply_markup= InlineKeyboardMarkup([
        [InlineKeyboardButton("🦋 Close 🦋", callback_data="cancel")]]))
    
@Client.on_message(filters.private & filters.user(ADMIN)  & filters.command(["allids"]))
async def allids(client,message):
    botdata(int(botid))
    data = find_one(int(botid))
    total_rename = data.get("total_rename", 0)
    total_size = data.get("total_size", 0)
    id = str(getid())
    ids = id.split(',')
    
    await message.reply_text(f"<b>⚡️ All IDs :</b> {ids}\n\n<b>⚡️ Total User :</b> {total_user()}\n\n<b>⚡️ Total Renamed File :</b> {total_rename}\n<b>⚡ Total Size Renamed :</b> {humanbytes(int(total_size))}", quote=True, reply_markup= InlineKeyboardMarkup([
        [InlineKeyboardButton("🦋 Close 🦋", callback_data="cancel")]]))
