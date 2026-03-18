from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    
    # Check if the reply is to the bot's "Enter New Filename" message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        
        # Get the original file message
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        
        # 1. Safely identify the media object
        media = getattr(file, file.media.value)
        
        # 2. Safely get the file name as a string (handle NoneType)
        filename = getattr(media, 'file_name', None)
        
        # 3. Determine extension
        if not "." in new_name:
            # Check if filename exists AND is a string before checking for "."
            if isinstance(filename, str) and "." in filename:
                extn = filename.rsplit('.', 1)[-1]
            else:
                extn = "mkv" # Default fallback
            new_name = new_name + "." + extn
            
        await reply_message.delete()

        # 4. Create Buttons
        button = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
        
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])
            
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )
