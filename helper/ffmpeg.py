import time
import os
import asyncio
from PIL import Image

async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb is not None:
            img = Image.open(thumb).convert("RGB")
            width, height = img.size
            img.resize((320, height))
            img.save(thumb, "JPEG")
    except Exception as e:
        print(f"Thumb fix error: {e}")
        thumb = None 
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_generator_command = [
        "ffmpeg", "-ss", str(ttl), "-i", video_file, 
        "-vframes", "1", out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None

async def add_metadata(input_path, output_path, metadata, ms):
    try:
        await ms.edit("<i>⚡ Adding Metadata (High Speed Mode)...</i>")
        
        # We use '-c copy' to skip re-encoding. This makes it 100x faster.
        command = [
            'ffmpeg', '-y', '-i', input_path, 
            '-map', '0', 
            '-c', 'copy', 
            '-metadata', f'title={metadata}', 
            '-metadata', f'author={metadata}', 
            '-metadata', f'artist={metadata}', 
            '-metadata', f'comment={metadata}',
            '-metadata:s:s', f'title={metadata}', 
            '-metadata:s:a', f'title={metadata}', 
            '-metadata:s:v', f'title={metadata}', 
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if os.path.exists(output_path):
            await ms.edit("<i>✅ Metadata Added Successfully!</i>")
            return output_path
        else:
            print(f"FFmpeg Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Error occurred while adding metadata: {str(e)}")
        return None
