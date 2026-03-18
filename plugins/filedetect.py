from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    
    # SAFETY: Check if the message is actually a reply
    if not reply_message:
        return

    # SAFETY: Check if the replied message has a "ForceReply" markup
    if reply_message.reply_markup and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        
        try:
            msg = await client.get_messages(message.chat.id, reply_message.id)
            file = msg.reply_to_message
            if not file:
                return
                
            media = getattr(file, file.media.value)
            filename = getattr(media, 'file_name', None)
            
            if not "." in new_name:
                if isinstance(filename, str) and "." in filename:
                    extn = filename.rsplit('.', 1)[-1]
                else:
                    extn = "mkv"
                new_name = new_name + "." + extn
                
            await reply_message.delete()

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
        except Exception as e:
            print(f"Error in filedetect: {e}")
