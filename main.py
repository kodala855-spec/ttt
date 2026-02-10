import asyncio
import logging
import random
from pathlib import Path
from typing import Optional

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from ai_handler import AIHandler
from behavior import (
    calculate_typing_delay,
    casualize_text,
    clean_response_text,
    extract_learning_data,
    format_bot_message_for_history,
    format_message_for_history,
    get_sleepy_response,
    introduce_typo,
    is_circadian_sleep_time,
    parse_media_tag,
    parse_reaction_tag,
)
from config import Config
from history import HistoryManager

Config.configure_logging()
logger = logging.getLogger(__name__)


class HumanUserBot:
    def __init__(self) -> None:
        Config.validate()
        self.app = Client(
            "human_userbot",
            api_id=int(Config.API_ID),
            api_hash=Config.API_HASH,
        )
        self.history = HistoryManager(Config.DB_PATH)
        self.ai = AIHandler(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            system_prompt=Config.SYSTEM_PROMPT,
            timeout=Config.AI_TIMEOUT,
        )
        self.stickers = Config.load_stickers()
        self.owner_id = int(Config.OWNER_ID)
        self.paused = False
        self.whitelist_only = False
        self.register_handlers()
        logger.info("HumanUserBot initialized")

    def register_handlers(self) -> None:
        command_filter = filters.command(
            ["pause", "resume", "status", "history", "blacklist", "whitelist"],
            prefixes="/",
        )

        @self.app.on_message(filters.user(self.owner_id) & command_filter)
        async def owner_commands(_: Client, message: Message) -> None:
            if not message.command:
                return
            command = message.command[0].lower()
            if command == "pause":
                self.paused = True
                await message.reply_text("🔇 Bot paused.")
                return
            if command == "resume":
                self.paused = False
                await message.reply_text("🔊 Bot resumed.")
                return
            if command == "status":
                await message.reply_text(self._build_status())
                return
            if command == "history":
                await self._send_history(message)
                return
            if command == "blacklist":
                await self._handle_blacklist(message)
                return
            if command == "whitelist":
                await self._handle_whitelist(message)
                return

        @self.app.on_message(filters.outgoing & filters.user(self.owner_id) & ~command_filter)
        async def owner_safety_handler(_: Client, message: Message) -> None:
            if not Config.SAFETY_AUTO_PAUSE:
                return
            if self.paused:
                return
            if message.chat and message.chat.is_self:
                return
            self.paused = True
            logger.warning("Safety auto-pause engaged by owner message")
            await self._notify_admin("Safety auto-pause engaged after owner activity.")

        @self.app.on_message(filters.incoming & ~filters.bot)
        async def message_handler(client: Client, message: Message) -> None:
            if self.paused:
                return

            if not message.from_user:
                return

            user_id = message.from_user.id
            if await self.history.is_blacklisted(user_id):
                return

            if self.whitelist_only and not await self.history.is_whitelisted(user_id):
                return

            chat_id = message.chat.id
            message_text = message.text or message.caption or ""
            if not message_text:
                return

            await self.history.add_message(
                chat_id=chat_id,
                message_id=message.id,
                role="user",
                content=format_message_for_history(
                    message_text,
                    message.from_user.first_name or "User",
                    user_id == self.owner_id,
                ),
            )

            if is_circadian_sleep_time(Config.DND_START, Config.DND_END):
                if Config.DND_MODE == "silent":
                    return
                await self._send_sleepy_reply(message, chat_id)
                return

            try:
                await self._process_message(client, message, chat_id)
            except Exception as exc:
                logger.error("Failed to process message: %s", exc)
                await self._notify_admin("⚠️ Failed to process a message. Check logs.")

    async def _process_message(self, client: Client, message: Message, chat_id: int) -> None:
        history_entries = await self.history.get_history(chat_id, Config.HISTORY_LIMIT)
        ai_messages = [
            {"role": entry["role"], "content": entry["content"]}
            for entry in history_entries
        ]

        ai_response = await self.ai.get_response(ai_messages)
        if not ai_response:
            await self._notify_admin("⚠️ AI response empty. Pausing replies.")
            return

        response_text, media_tags = parse_media_tag(ai_response)
        response_text, reaction = parse_reaction_tag(response_text)
        response_text, learning_items = extract_learning_data(response_text)
        response_text = clean_response_text(response_text)
        response_text = casualize_text(response_text)

        if learning_items:
            await self._update_learning(chat_id, learning_items)

        if reaction:
            await self._send_reaction(message, reaction)

        if response_text:
            await self._send_text_reply(message, chat_id, response_text)

        await self._send_media(message, media_tags)

    async def _send_text_reply(self, message: Message, chat_id: int, response_text: str) -> None:
        delay = calculate_typing_delay(
            response_text,
            Config.TYPING_MIN_DELAY,
            Config.TYPING_MAX_DELAY,
        )
        await self.app.send_chat_action(chat_id, "typing")
        await asyncio.sleep(delay)

        typo_text, corrected_text = introduce_typo(response_text, Config.TYPO_PROBABILITY)
        try:
            sent = await message.reply_text(typo_text)
        except FloodWait as exc:
            await asyncio.sleep(exc.value)
            sent = await message.reply_text(typo_text)
        except RPCError as exc:
            logger.error("Failed to send message: %s", exc)
            return

        if typo_text != corrected_text:
            await asyncio.sleep(min(1.4, delay))
            try:
                await sent.edit_text(corrected_text)
            except RPCError as exc:
                logger.warning("Failed to edit typo: %s", exc)

        await self.history.add_message(
            chat_id=chat_id,
            message_id=sent.id,
            role="assistant",
            content=format_bot_message_for_history(corrected_text),
        )

    async def _send_sleepy_reply(self, message: Message, chat_id: int) -> None:
        sleepy_text = get_sleepy_response()
        await self.app.send_chat_action(chat_id, "typing")
        await asyncio.sleep(calculate_typing_delay(sleepy_text, 0.4, 2.2))
        sent = await message.reply_text(sleepy_text)
        await self.history.add_message(
            chat_id=chat_id,
            message_id=sent.id,
            role="assistant",
            content=format_bot_message_for_history(sleepy_text),
        )

    async def _send_reaction(self, message: Message, reaction: str) -> None:
        try:
            await message.react(reaction)
        except RPCError as exc:
            logger.warning("Failed to send reaction: %s", exc)

    async def _send_media(self, message: Message, media_tags: dict) -> None:
        if media_tags.get("photo"):
            await self._send_photo(message, media_tags["photo"])
        if media_tags.get("video_note"):
            await self._send_video_note(message, media_tags["video_note"])
        if media_tags.get("sticker"):
            await self._send_sticker(message, media_tags["sticker"])

    async def _send_photo(self, message: Message, identifier: str) -> None:
        path = self._resolve_media_path(Config.PHOTOS_DIR, identifier)
        if not path:
            return
        await message.reply_photo(str(path))

    async def _send_video_note(self, message: Message, identifier: str) -> None:
        path = self._resolve_media_path(Config.VIDEO_NOTES_DIR, identifier)
        if not path:
            return
        await message.reply_video_note(str(path))

    async def _send_sticker(self, message: Message, key: str) -> None:
        sticker_id = self.stickers.get(key)
        if not sticker_id:
            await self._notify_admin(f"⚠️ Unknown sticker key: {key}")
            return
        await message.reply_sticker(sticker_id)

    def _resolve_media_path(self, directory: Path, identifier: str) -> Optional[Path]:
        if identifier == "random":
            files = [item for item in directory.iterdir() if item.is_file()]
            if not files:
                return None
            return random.choice(files)
        candidate = directory / identifier
        return candidate if candidate.exists() else None

    async def _update_learning(self, chat_id: int, items: list) -> None:
        profile = await self.history.get_profile(chat_id)
        notes = profile.get("notes", [])
        notes.extend(items)
        profile["notes"] = notes[-50:]
        await self.history.save_profile(chat_id, profile)

    async def _notify_admin(self, text: str) -> None:
        try:
            await self.app.send_message("me", text)
        except RPCError as exc:
            logger.error("Failed to notify admin: %s", exc)

    async def _send_history(self, message: Message) -> None:
        chat_id = message.chat.id
        history_entries = await self.history.get_history(chat_id, 10)
        if not history_entries:
            await message.reply_text("No history yet.")
            return
        lines = [f"{entry['role']}: {entry['content']}" for entry in history_entries]
        await message.reply_text("\n".join(lines))

    async def _handle_blacklist(self, message: Message) -> None:
        target_id = self._extract_target_user(message)
        if target_id is None:
            await message.reply_text("Provide a user ID or reply to a user to blacklist.")
            return
        if len(message.command) > 1 and message.command[1].lower() == "remove":
            await self.history.remove_blacklist(target_id)
            await message.reply_text(f"Removed {target_id} from blacklist.")
            return
        await self.history.add_blacklist(target_id)
        await message.reply_text(f"Blacklisted {target_id}.")

    async def _handle_whitelist(self, message: Message) -> None:
        target_id = self._extract_target_user(message)
        if target_id is None:
            await message.reply_text("Provide a user ID or reply to a user to whitelist.")
            return
        await self.history.add_whitelist(target_id)
        self.whitelist_only = True
        await message.reply_text(f"Whitelisted {target_id}.")

    def _extract_target_user(self, message: Message) -> Optional[int]:
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user.id
        if len(message.command) > 1:
            if message.command[1].lower() == "remove" and len(message.command) > 2:
                try:
                    return int(message.command[2])
                except ValueError:
                    return None
            try:
                return int(message.command[1])
            except ValueError:
                return None
        return None

    def _build_status(self) -> str:
        return (
            "🤖 Bot Status\n"
            f"Paused: {self.paused}\n"
            f"DND: {Config.DND_START}-{Config.DND_END} ({Config.DND_MODE})\n"
            f"Safety Auto-Pause: {Config.SAFETY_AUTO_PAUSE}\n"
            f"History Limit: {Config.HISTORY_LIMIT}"
        )

    def run(self) -> None:
        logger.info("Starting HumanUserBot")
        self.app.run()

    def __del__(self) -> None:
        if hasattr(self, "history"):
            self.history.close()


def main() -> None:
    try:
        bot = HumanUserBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as exc:
        logger.error("Fatal error: %s", exc)


if __name__ == "__main__":
    main()
