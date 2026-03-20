import math
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    
    # SPEED OPTIMIZATION: Updated from 5.0 to 15.0 seconds.
    # Reducing the frequency of message edits prevents Telegram from throttling 
    # your connection, allowing the speed to jump from 2MB/s to 15MB/s+.
    if round(diff % 15.0) == 0 or current == total:
        if diff <= 0:
            return

        percentage = current * 100 / total
        speed = current / diff # bytes per second
        elapsed_time = round(diff) * 1000 # milliseconds
        
        if speed > 0:
            time_to_completion = round((total - current) / speed) * 1000
        else:
            time_to_completion = 0
            
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time)

        # Create Visual Progress Bar (20 blocks)
        filled_blocks = math.floor(percentage / 5)
        empty_blocks = 20 - filled_blocks
        progress_bar = "■" * filled_blocks + "□" * empty_blocks

        # Build the Status Message
        status_text = (
            f"<b>{ud_type}...</b>\n"
            f"<code>{progress_bar}</code>\n\n"
            f"<b>📊 Percentage:</b> {round(percentage, 2)}%\n"
            f"<b>📁 Done:</b> {humanbytes(current)} / {humanbytes(total)}\n"
            f"<b>🚀 Speed:</b> {humanbytes(speed)}/s\n"
            f"<b>⏰ ETA:</b> {estimated_total_time_str if estimated_total_time_str != '' else '0 s'}\n"
            f"<b>⏱️ Elapsed:</b> {elapsed_time_str}"
        )
        
        try:
            await message.edit(text=status_text)
        except Exception:
            # Safety for deleted messages or identical content
            pass

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

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        (str(days) + "d, ") if days else ""
    ) + (
        (str(hours) + "h, ") if hours else ""
    ) + (
        (str(minutes) + "m, ") if minutes else ""
    ) + (
        (str(seconds) + "s, ") if seconds else ""
    )
    return tmp[:-2] if tmp else "0s"
