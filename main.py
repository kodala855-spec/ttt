import asyncio
import logging
import time
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, BadRequest

from config import Config
from history import HistoryManager
from ai_handler import AIHandler
from behavior import (
    add_typos,
    add_delays,
    casualize_text,
    should_reply,
    parse_tags,
    select_random_file,
    get_sticker_id,
    format_history_for_ai,
    is_dnd_active,
    sanitize_filename,
    validate_reaction_emoji
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('userbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HumanUserBot:
    def __init__(self):
        Config.validate()
        
        self.app = Client(
            "human_userbot",
            api_id=int(Config.API_ID),
            api_hash=Config.API_HASH,
            phone_number=Config.PHONE_NUMBER
        )
        
        self.history = HistoryManager(Config.DB_PATH)
        self.ai = AIHandler(
            api_key=Config.OPENAI_API_KEY,
            system_prompt=Config.SYSTEM_PROMPT,
            timeout=Config.AI_TIMEOUT
        )
        
        self.stickers = Config.load_stickers()
        self.owner_id = int(Config.OWNER_ID)
        self.paused = False
        
        self.register_handlers()
        logger.info("HumanUserBot initialized")
    
    def register_handlers(self):
        @self.app.on_message(filters.command("pause", prefixes=".") & filters.me)
        async def pause_handler(client: Client, message: Message):
            self.paused = True
            await message.edit("🔇 Bot paused")
            logger.info("Bot paused by owner")
        
        @self.app.on_message(filters.command("resume", prefixes=".") & filters.me)
        async def resume_handler(client: Client, message: Message):
            self.paused = False
            await message.edit("🔊 Bot resumed")
            logger.info("Bot resumed by owner")
        
        @self.app.on_message(filters.command("status", prefixes=".") & filters.me)
        async def status_handler(client: Client, message: Message):
            stats = await self.history.get_stats()
            status_text = f"""
📊 Bot Status
State: {'Paused' if self.paused else 'Active'}
DND: {Config.DND_START} - {Config.DND_END}
Messages: {stats['total_messages']}
Chats: {stats['total_chats']}
            """.strip()
            await message.edit(status_text)
        
        @self.app.on_message(filters.command("clear", prefixes=".") & filters.me)
        async def clear_handler(client: Client, message: Message):
            chat_id = message.chat.id
            await self.history.clear_chat_history(chat_id)
            await message.edit("🗑️ Chat history cleared")
            logger.info(f"Cleared history for chat {chat_id}")
        
        @self.app.on_message(filters.incoming & ~filters.me & ~filters.bot)
        async def message_handler(client: Client, message: Message):
            if self.paused:
                logger.debug("Bot is paused, ignoring message")
                return
            
            if is_dnd_active(Config.DND_START, Config.DND_END):
                logger.debug("DND active, ignoring message")
                return
            
            chat_id = message.chat.id
            message_text = message.text or message.caption or ""
            
            if not message_text:
                logger.debug("No text content, skipping")
                return
            
            await self.history.add_message(
                chat_id=chat_id,
                message_id=message.id,
                role="user",
                content=message_text,
                timestamp=time.time()
            )
            
            me = await client.get_me()
            username = me.username if me else None
            
            if not should_reply(message_text, username):
                logger.debug("Decided not to reply")
                return
            
            try:
                await self.process_and_respond(client, message, chat_id)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def process_and_respond(self, client: Client, message: Message, chat_id: int):
        history_entries = await self.history.get_recent_history(chat_id, Config.HISTORY_LIMIT)
        formatted_history = format_history_for_ai(history_entries)
        
        ai_response = await self.ai.get_response_with_retry(formatted_history)
        
        if not ai_response:
            logger.warning("No AI response received")
            return
        
        clean_text, tags = parse_tags(ai_response)
        
        await asyncio.sleep(add_delays())
        
        if tags['reaction']:
            await self.send_reaction(message, tags['reaction'])
        
        if clean_text:
            clean_text = casualize_text(clean_text)
            clean_text = add_typos(clean_text, probability=0.05)
            
            await client.send_chat_action(chat_id, "typing")
            await asyncio.sleep(min(len(clean_text) / 20, 5))
            
            try:
                sent_message = await message.reply_text(clean_text)
                
                await self.history.add_message(
                    chat_id=chat_id,
                    message_id=sent_message.id,
                    role="assistant",
                    content=clean_text,
                    timestamp=time.time()
                )
                
                logger.info(f"Sent reply to chat {chat_id}")
            except FloodWait as e:
                logger.warning(f"FloodWait: sleeping for {e.value}s")
                await asyncio.sleep(e.value)
            except BadRequest as e:
                logger.error(f"BadRequest: {e}")
        
        if tags['photo']:
            await self.send_photo(client, message, tags['photo'])
        
        if tags['video_note']:
            await self.send_video_note(client, message, tags['video_note'])
        
        if tags['sticker']:
            await self.send_sticker(client, message, tags['sticker'])
    
    async def send_reaction(self, message: Message, emoji: str):
        try:
            if validate_reaction_emoji(emoji):
                await message.react(emoji)
                logger.info(f"Sent reaction: {emoji}")
            else:
                logger.warning(f"Invalid reaction emoji: {emoji}")
        except Exception as e:
            logger.error(f"Error sending reaction: {e}")
    
    async def send_photo(self, client: Client, message: Message, photo_identifier: str):
        try:
            if photo_identifier == "random":
                photo_path = select_random_file(Config.PHOTOS_DIR)
            else:
                photo_path = Config.PHOTOS_DIR / sanitize_filename(photo_identifier)
                if not photo_path.exists():
                    logger.warning(f"Photo not found: {photo_path}")
                    return
                photo_path = str(photo_path)
            
            if photo_path:
                await message.reply_photo(photo_path)
                logger.info(f"Sent photo: {photo_path}")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
    
    async def send_video_note(self, client: Client, message: Message, video_identifier: str):
        try:
            if video_identifier == "random":
                video_path = select_random_file(Config.VIDEO_NOTES_DIR)
            else:
                video_path = Config.VIDEO_NOTES_DIR / sanitize_filename(video_identifier)
                if not video_path.exists():
                    logger.warning(f"Video note not found: {video_path}")
                    return
                video_path = str(video_path)
            
            if video_path:
                await message.reply_video_note(video_path)
                logger.info(f"Sent video note: {video_path}")
        except Exception as e:
            logger.error(f"Error sending video note: {e}")
    
    async def send_sticker(self, client: Client, message: Message, sticker_key: str):
        try:
            sticker_id = get_sticker_id(self.stickers, sticker_key)
            if sticker_id:
                await message.reply_sticker(sticker_id)
                logger.info(f"Sent sticker: {sticker_key}")
        except Exception as e:
            logger.error(f"Error sending sticker: {e}")
    
    def run(self):
        logger.info("Starting HumanUserBot...")
        self.app.run()
    
    def __del__(self):
        if hasattr(self, 'history'):
            self.history.close()


def main():
    try:
        bot = HumanUserBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
