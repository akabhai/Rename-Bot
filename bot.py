import logging
import logging.config

# Standard logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from pyrogram import Client, idle
from plugins.cb_data import app as Client2
from config import *
import pyromod
import pyrogram.utils

# For newer Telegram IDs
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

logger.info("Initializing Bot...")

bot = Client(
    "Renamer", 
    bot_token=BOT_TOKEN, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    plugins=dict(root='plugins')
)

def run_bot():
    if STRING_SESSION:
        logger.info("Starting with Premium String Session...")
        apps = [Client2, bot]
        for app in apps:
            app.start()
        logger.info("Bot & Premium Client Started Successfully!")
        idle()
        for app in apps:
            app.stop()
    else:
        logger.info("Starting Bot only (No String Session)...")
        bot.run()
        logger.info("Bot Started Successfully!")

if __name__ == "__main__":
    try:
        run_bot()
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
