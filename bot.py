import logging
import asyncio
from pyrogram import Client, idle, errors
from plugins.cb_data import app as Client2
from config import *
import pyromod
import pyrogram.utils

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for newer Telegram IDs
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

logger.info("--- INITIALIZING BOT ---")

bot = Client(
    "Renamer", 
    bot_token=BOT_TOKEN, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    plugins=dict(root='plugins')
)

async def start_services():
    try:
        # Start the main bot
        await bot.start()
        logger.info("✅ BOT STARTED SUCCESSFULLY")
        
        # Start Premium Client if session exists
        if STRING_SESSION:
            try:
                await Client2.start()
                logger.info("✅ PREMIUM CLIENT STARTED")
            except Exception as e:
                logger.error(f"❌ PREMIUM CLIENT ERROR: {e}")
        
        # Keep the bot running
        await idle()
        
    except errors.FloodWait as e:
        # If Telegram tells us to wait, we sleep instead of crashing
        logger.warning(f"⚠️ Telegram FloodWait: Must wait for {e.value} seconds. Sleeping...")
        await asyncio.sleep(e.value + 2) 
        # After sleeping, try starting again
        await start_services()
        
    except Exception as e:
        logger.error(f"❌ FATAL ERROR ON START: {e}")
        
    finally:
        # Safety: Only stop if the client was successfully connected
        if bot.is_connected:
            await bot.stop()
        if STRING_SESSION and Client2.is_connected:
            await Client2.stop()

if __name__ == "__main__":
    # Standard way to run the async loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
