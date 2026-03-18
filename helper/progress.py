import math
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    
    # SPEED OPTIMIZATION: 
    # Only update the message every 12 seconds OR when it reaches 100%.
    # Updating more often causes Telegram to throttle your upload/download speed.
    if round(diff % 12.0) == 0 or current == total:
        percentage = current * 100 / total
        
        # Prevent division by zero error if the file just started
        if diff <= 0:
            return

        speed = current / diff
        elapsed_time = round(diff) * 1000
        
        # Prevent division by zero if speed is 0
        if speed > 0:
            time_to_completion = round((total - current) / speed) * 1000
        else:
            time_to_completion = 0
            
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time)

        filled_blocks = math.floor(percentage / 5)
        empty_blocks = 20 - filled_blocks
        progress_bar = "■" * filled_blocks + "□" * empty_blocks

        tmp = PROGRESS_BAR.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str != '' else '0 s',
            progress_bar
        )
        
        # We don't need a cancel button on the worker side to keep it faster
        try:
            await message.edit(
                text=f"<b>{ud_type}</b>\n\n{tmp}"
            )
        except Exception:
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
    return tmp[:-2]

PROGRESS_BAR = """\
{5}

<b>📁 Size</b> : {1} | {2}
<b>⏳️ Done</b> : {0}%
<b>🚀 Speed</b> : {3}/s
<b>⏰️ ETA</b> : {4} """
