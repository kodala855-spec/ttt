import asyncio
import logging
import time
import random
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, BadRequest

from config import Config
from history import HistoryManager
from ai_handler import AIHandler
from behavior import (
    calculate_typing_delay,
    introduce_typo,
    casualize_text,
    is_circadian_sleep_time,
    get_sleepy_response,
    parse_media_tag,
    parse_reaction_tag,
    extract_learning_data,
    clean_response_text,
    format_message_for_history,
    format_bot_message_for_history
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
            api_hash=Config.API_HASH
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
        @self.app.on_message(filters.command("pause", prefixes="/") & filters.user(self.owner_id))
        async def pause_handler(client: Client, message: Message):
            self.paused = True
            await message.reply("🔇 Bot paused")
            logger.info("Bot paused by owner")
        
        @self.app.on_message(filters.command("resume", prefixes="/") & filters.user(self.owner_id))
        async def resume_handler(client: Client, message: Message):
            self.paused = False
            await message.reply("🔊 Bot resumed")
            logger.info("Bot resumed by owner")
        
        @self.app.on_message(filters.command("status", prefixes="/") & filters.user(self.owner_id))
        async def status_handler(client: Client, message: Message):
            status_text = f"""
📊 Bot Status
State: {'Paused' if self.paused else 'Active'}
DND: {Config.DND_START} - {Config.DND_END}
Safety: {'Enabled' if Config.SAFETY_SWITCH else 'Disabled'}
            """.strip()
            await message.reply(status_text)
        
        @self.app.on_message(filters.command("history", prefixes="/") & filters.user(self.owner_id))
        async def history_handler(client: Client, message: Message):
            chat_id = message.chat.id
            history = await self.history.get_history(chat_id, limit=5)
            
            if not history:
                await message.reply("No history for this chat.")
                return
            
            history_text = "📜 Recent History:\n\n"
            for entry in history:
                role = "👤" if entry['role'] == 'user' else "🤖"
                content = entry['content'][:50] + "..." if len(entry['content']) > 50 else entry['content']
                history_text += f"{role} {content}\n"
            
            await message.reply(history_text)
        
        @self.app.on_message(filters.command("blacklist", prefixes="/") & filters.user(self.owner_id))
        async def blacklist_handler(client: Client, message: Message):
            if not message.reply_to_message:
                await message.reply("Reply to a user's message to blacklist them.")
                return
            
            target_id = message.reply_to_message.from_user.id
            reason = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
            
            await self.history.add_blacklist(target_id, reason)
            await message.reply(f"🚫 User {target_id} added to blacklist.")
        
        @self.app.on_message(filters.command("whitelist", prefixes="/") & filters.user(self.owner_id))
        async def whitelist_handler(client: Client, message: Message):
            if not message.reply_to_message:
                await message.reply("Reply to a user's message to whitelist them.")
                return
            
            target_id = message.reply_to_message.from_user.id
            await self.history.add_whitelist(target_id)
            await message.reply(f"✅ User {target_id} added to whitelist.")
        
        @self.app.on_message(filters.incoming & ~filters.me & ~filters.bot)
        async def message_handler(client: Client, message: Message):
            if self.paused:
                logger.debug("Bot is paused, ignoring message")
                return
            
            user_id = message.from_user.id if message.from_user else None
            
            if user_id == self.owner_id and Config.SAFETY_SWITCH:
                self.paused = True
                logger.info("Safety auto-pause triggered by owner message")
                await client.send_message(self.owner_id, "🔒 Auto-paused due to owner activity")
                return
            
            if user_id and await self.history.is_blacklisted(user_id):
                logger.debug(f"Ignoring blacklisted user {user_id}")
                return
            
            chat_id = message.chat.id
            message_text = message.text or message.caption or ""
            
            await self.history.add_message(
                chat_id=chat_id,
                message_id=message.id,
                role="user",
                content=message_text,
                timestamp=time.time()
            )
            
            if is_circadian_sleep_time(Config.DND_START, Config.DND_END):
                logger.debug("DND active, sending sleepy response")
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await message.reply(get_sleepy_response())
                return
            
            if not message_text:
                logger.debug("No text content, skipping")
                return
            
            try:
                await self.process_and_respond(client, message, chat_id)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def process_and_respond(self, client: Client, message: Message, chat_id: int):
        history_entries = await self.history.get_history(chat_id, Config.HISTORY_LIMIT)
        
        formatted_history = []
        for entry in history_entries:
            formatted_history.append({
                'role': entry['role'],
                'content': entry['content']
            })
        
        ai_response = await self.ai.get_response_with_retry(formatted_history)
        
        if not ai_response:
            logger.warning("No AI response received")
            return
        
        clean_text, learning_data = extract_learning_data(ai_response)
        clean_text, media_tags = parse_media_tag(clean_text)
        clean_text, reaction = parse_reaction_tag(clean_text)
        clean_text = clean_response_text(clean_text)
        
        if learning_data.get('topics') or learning_data.get('preferences') or learning_data.get('facts'):
            user_id = message.from_user.id if message.from_user else None
            if user_id:
                await self.history.save_profile(
                    user_id=user_id,
                    topics=learning_data.get('topics'),
                    preferences=learning_data.get('preferences'),
                    facts=learning_data.get('facts')
                )
        
        typing_delay = calculate_typing_delay(clean_text)
        await asyncio.sleep(typing_delay)
        
        if reaction:
            try:
                await message.react(reaction)
                logger.info(f"Sent reaction: {reaction}")
            except Exception as e:
                logger.error(f"Error sending reaction: {e}")
        
        if clean_text:
            casual_text = casualize_text(clean_text)
            typo_text = introduce_typo(casual_text, probability=0.05)
            
            await client.send_chat_action(chat_id, "typing")
            await asyncio.sleep(min(len(typo_text) / 20, 5))
            
            try:
                if typo_text != casual_text:
                    sent_message = await message.reply_text(typo_text)
                    await asyncio.sleep(random.uniform(3, 8))
                    await sent_message.edit(casual_text)
                    logger.info(f"Sent typo correction in chat {chat_id}")
                    final_text = casual_text
                else:
                    sent_message = await message.reply_text(casual_text)
                    final_text = casual_text
                
                await self.history.add_message(
                    chat_id=chat_id,
                    message_id=sent_message.id,
                    role="assistant",
                    content=final_text,
                    timestamp=time.time()
                )
                
                logger.info(f"Sent reply to chat {chat_id}")
            except FloodWait as e:
                logger.warning(f"FloodWait: sleeping for {e.value}s")
                await asyncio.sleep(e.value)
            except BadRequest as e:
                logger.error(f"BadRequest: {e}")
        
        if media_tags.get('photo'):
            await self.send_photo(client, message, media_tags['photo'])
        
        if media_tags.get('video_note'):
            await self.send_video_note(client, message, media_tags['video_note'])
        
        if media_tags.get('sticker'):
            await self.send_sticker(client, message, media_tags['sticker'])
    
    async def send_photo(self, client: Client, message: Message, photo_identifier: str):
        try:
            if photo_identifier == "random":
                files = [f for f in Config.PHOTOS_DIR.iterdir() if f.is_file() and f.name != '.gitkeep']
                if not files:
                    logger.warning("No photos available")
                    return
                photo_path = random.choice(files)
            else:
                photo_path = Config.PHOTOS_DIR / photo_identifier
                if not photo_path.exists():
                    logger.warning(f"Photo not found: {photo_path}")
                    return
            
            await message.reply_photo(str(photo_path))
            logger.info(f"Sent photo: {photo_path}")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
    
    async def send_video_note(self, client: Client, message: Message, video_identifier: str):
        try:
            if video_identifier == "random":
                files = [f for f in Config.VIDEO_NOTES_DIR.iterdir() if f.is_file() and f.name != '.gitkeep']
                if not files:
                    logger.warning("No video notes available")
                    return
                video_path = random.choice(files)
            else:
                video_path = Config.VIDEO_NOTES_DIR / video_identifier
                if not video_path.exists():
                    logger.warning(f"Video note not found: {video_path}")
                    return
            
            await message.reply_video_note(str(video_path))
            logger.info(f"Sent video note: {video_path}")
        except Exception as e:
            logger.error(f"Error sending video note: {e}")
    
    async def send_sticker(self, client: Client, message: Message, sticker_key: str):
        try:
            sticker_id = self.stickers.get(sticker_key)
            if sticker_id:
                await message.reply_sticker(sticker_id)
                logger.info(f"Sent sticker: {sticker_key}")
            else:
                logger.warning(f"Sticker key not found: {sticker_key}")
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
