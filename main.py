import asyncio
import logging
import json
import random
import signal
from datetime import datetime
from typing import Optional, Dict
from collections import deque
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError

from config import Config, ConfigurationError
from behavior import (
    should_respond,
    is_dnd_active,
    simulate_typing_delay,
    add_typo,
    add_casual_suffix,
    truncate_message,
    select_random_photo,
    select_random_video_note,
    select_random_sticker,
    calculate_response_delay,
    should_send_media
)
from history import HistoryManager
from ai_handler import AIHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("userbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_messages: int, window: int):
        self.max_messages = max_messages
        self.window = window
        self.messages: Dict[int, deque] = {}

    def can_send(self, chat_id: int) -> bool:
        now = datetime.now().timestamp()
        if chat_id not in self.messages:
            self.messages[chat_id] = deque()

        queue = self.messages[chat_id]

        while queue and queue[0] < now - self.window:
            queue.popleft()

        return len(queue) < self.max_messages

    def record_message(self, chat_id: int) -> None:
        now = datetime.now().timestamp()
        if chat_id not in self.messages:
            self.messages[chat_id] = deque()
        self.messages[chat_id].append(now)


class HumanUserBot:
    def __init__(self):
        self.app: Optional[Client] = None
        self.history: Optional[HistoryManager] = None
        self.ai: Optional[AIHandler] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.stickers: list = []
        self.running = False

    async def initialize(self) -> None:
        try:
            Config.validate()
        except ConfigurationError as e:
            logger.error(f"Configuration error:\n{e}")
            raise

        log_level = getattr(logging, Config.LOG_LEVEL)
        logging.getLogger().setLevel(log_level)

        self.app = Client(
            name="human_userbot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            phone_number=Config.PHONE_NUMBER
        )

        self.history = HistoryManager(Config.DB_FILE)
        await self.history.initialize()

        self.ai = AIHandler()

        self.rate_limiter = RateLimiter(
            Config.RATE_LIMIT_MESSAGES,
            Config.RATE_LIMIT_WINDOW
        )

        try:
            with open(Config.STICKERS_FILE, 'r') as f:
                self.stickers = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load stickers: {e}")
            self.stickers = ["👍", "❤️", "😂"]

        self._setup_handlers()
        logger.info("HumanUserBot initialized successfully")

    def _setup_handlers(self) -> None:
        @self.app.on_message(filters.private | filters.group)
        async def handle_message(client: Client, message: Message):
            await self._process_message(message)

    async def _process_message(self, message: Message) -> None:
        try:
            if message.outgoing:
                await self._store_outgoing_message(message)
                return

            await self._store_incoming_message(message)

            if not self._should_process_message(message):
                return

            if is_dnd_active():
                logger.info("DND active, skipping response")
                return

            if not await self.history.can_respond(message.chat.id):
                logger.info("Response interval not met, skipping")
                return

            if not self.rate_limiter.can_send(message.chat.id):
                logger.warning(f"Rate limit reached for chat {message.chat.id}")
                return

            if not should_respond():
                logger.info("Random chance: not responding")
                return

            await self._handle_response(message)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _should_process_message(self, message: Message) -> bool:
        if message.empty:
            return False

        if message.service:
            return False

        if message.via_bot:
            return False

        return True

    async def _store_incoming_message(self, message: Message) -> None:
        try:
            text = message.text or message.caption or ""
            await self.history.store_message(
                chat_id=message.chat.id,
                message_id=message.id,
                user_id=message.from_user.id if message.from_user else None,
                username=message.from_user.first_name if message.from_user else None,
                text=text,
                timestamp=message.date,
                is_outgoing=False
            )
        except Exception as e:
            logger.error(f"Failed to store incoming message: {e}")

    async def _store_outgoing_message(self, message: Message) -> None:
        try:
            text = message.text or message.caption or ""
            await self.history.store_message(
                chat_id=message.chat.id,
                message_id=message.id,
                user_id=None,
                username="You",
                text=text,
                timestamp=message.date,
                is_outgoing=True
            )
        except Exception as e:
            logger.error(f"Failed to store outgoing message: {e}")

    async def _handle_response(self, message: Message) -> None:
        try:
            chat_title = None
            if message.chat:
                chat_title = message.chat.title or message.chat.first_name

            context = await self.history.get_context_for_ai(message.chat.id, max_messages=10)

            message_text = message.text or message.caption or ""
            response_delay = calculate_response_delay(len(message_text))
            await asyncio.sleep(response_delay)

            media_type = should_send_media()

            if media_type == "reaction":
                await self._send_reaction(message)
            elif media_type == "photo":
                await self._send_photo_response(message, context, chat_title)
            elif media_type == "video_note":
                await self._send_video_note_response(message)
            elif media_type == "sticker":
                await self._send_sticker_response(message)
            else:
                await self._send_text_response(message, context, chat_title)

            await self.history.log_response(message.chat.id)
            self.rate_limiter.record_message(message.chat.id)

        except FloodWait as e:
            logger.warning(f"FloodWait: sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
        except RPCError as e:
            logger.error(f"RPC Error: {e}")
        except Exception as e:
            logger.error(f"Error handling response: {e}", exc_info=True)

    async def _send_text_response(
        self,
        message: Message,
        context: str,
        chat_title: Optional[str]
    ) -> None:
        try:
            message_text = message.text or message.caption or ""
            response = await self.ai.generate_response(message_text, context, chat_title)

            if not response:
                logger.warning("No response generated by AI")
                return

            response = truncate_message(response)
            response = add_typo(response)
            response = add_casual_suffix(response)

            await simulate_typing_delay()
            await self.app.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(1)

            await message.reply(response)
            logger.info(f"Sent text response to chat {message.chat.id}")

        except Exception as e:
            logger.error(f"Error sending text response: {e}")

    async def _send_reaction(self, message: Message) -> None:
        try:
            reactions = ["👍", "❤️", "🔥", "😂", "😮", "🤔", "👌"]
            reaction = random.choice(reactions)

            await asyncio.sleep(random.uniform(0.5, 2.0))
            await message.react(reaction)
            logger.info(f"Sent reaction {reaction} to chat {message.chat.id}")

        except Exception as e:
            logger.error(f"Error sending reaction: {e}")

    async def _send_photo_response(
        self,
        message: Message,
        context: str,
        chat_title: Optional[str]
    ) -> None:
        try:
            photo_path = select_random_photo(Config.PHOTOS_DIR)
            if not photo_path:
                logger.warning("No photos available, falling back to text")
                await self._send_text_response(message, context, chat_title)
                return

            message_text = message.text or message.caption or ""
            caption = await self.ai.generate_response(message_text, context, chat_title)

            if caption:
                caption = truncate_message(caption, 1024)
                caption = add_typo(caption)
                caption = add_casual_suffix(caption)

            await simulate_typing_delay()
            await self.app.send_chat_action(message.chat.id, "upload_photo")
            await asyncio.sleep(1)

            await message.reply_photo(photo_path, caption=caption or "")
            logger.info(f"Sent photo response to chat {message.chat.id}")

        except Exception as e:
            logger.error(f"Error sending photo: {e}")

    async def _send_video_note_response(self, message: Message) -> None:
        try:
            video_path = select_random_video_note(Config.VIDEO_NOTES_DIR)
            if not video_path:
                logger.warning("No video notes available, falling back to reaction")
                await self._send_reaction(message)
                return

            await simulate_typing_delay()
            await self.app.send_chat_action(message.chat.id, "upload_video")
            await asyncio.sleep(1)

            await message.reply_video_note(video_path)
            logger.info(f"Sent video note to chat {message.chat.id}")

        except Exception as e:
            logger.error(f"Error sending video note: {e}")

    async def _send_sticker_response(self, message: Message) -> None:
        try:
            sticker = select_random_sticker(self.stickers)
            if not sticker:
                logger.warning("No stickers available, falling back to reaction")
                await self._send_reaction(message)
                return

            await asyncio.sleep(random.uniform(0.5, 2.0))

            if sticker.startswith("👍") or sticker.startswith("❤") or len(sticker) <= 2:
                await message.react(sticker)
                logger.info(f"Sent sticker/emoji {sticker} as reaction")
            else:
                await message.reply(sticker)
                logger.info(f"Sent sticker {sticker}")

        except Exception as e:
            logger.error(f"Error sending sticker: {e}")

    async def start(self) -> None:
        self.running = True
        logger.info("Starting HumanUserBot...")

        try:
            await self.app.start()
            logger.info("HumanUserBot started successfully")
            logger.info(f"Logged in as: {self.app.me.first_name} (@{self.app.me.username})")

            await asyncio.Event().wait()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self) -> None:
        if not self.running:
            return

        logger.info("Stopping HumanUserBot...")
        self.running = False

        try:
            if self.app and self.app.is_connected:
                await self.app.stop()

            if self.ai:
                await self.ai.close()

            if self.history:
                await self.history.close()

            logger.info("HumanUserBot stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


async def main():
    bot = HumanUserBot()

    loop = asyncio.get_event_loop()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        loop.create_task(bot.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await bot.initialize()
        await bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
