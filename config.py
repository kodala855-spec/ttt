import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OWNER_ID = os.getenv("OWNER_ID")

    SYSTEM_PROMPT = os.getenv(
        "SYSTEM_PROMPT",
        "You are a casual, friendly Telegram user. Keep replies short, natural, and human.",
    )

    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))
    HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "14"))

    DND_START = os.getenv("DND_START", "23:00")
    DND_END = os.getenv("DND_END", "08:00")
    DND_MODE = os.getenv("DND_MODE", "sleepy").lower()

    SAFETY_AUTO_PAUSE = os.getenv("SAFETY_AUTO_PAUSE", "true").lower() == "true"

    LOG_FILE = os.getenv("LOG_FILE", "userbot.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "1048576"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))

    DB_PATH = os.getenv("DB_PATH", "chat_history.db")
    STICKERS_FILE = os.getenv("STICKERS_FILE", "stickers.json")

    PHOTOS_DIR = Path(os.getenv("PHOTOS_DIR", "media/photos"))
    VIDEO_NOTES_DIR = Path(os.getenv("VIDEO_NOTES_DIR", "media/video_notes"))

    TYPING_MIN_DELAY = float(os.getenv("TYPING_MIN_DELAY", "0.6"))
    TYPING_MAX_DELAY = float(os.getenv("TYPING_MAX_DELAY", "4.5"))
    TYPO_PROBABILITY = float(os.getenv("TYPO_PROBABILITY", "0.08"))

    @classmethod
    def configure_logging(cls):
        level = getattr(logging, cls.LOG_LEVEL, logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT,
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logging.basicConfig(level=level, handlers=[file_handler, console_handler])

    @classmethod
    def validate(cls):
        errors = []

        if not cls.API_ID:
            errors.append("API_ID is required")
        else:
            try:
                int(cls.API_ID)
            except ValueError:
                errors.append("API_ID must be an integer")

        if not cls.API_HASH:
            errors.append("API_HASH is required")

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        if not cls.OWNER_ID:
            errors.append("OWNER_ID is required")
        else:
            try:
                int(cls.OWNER_ID)
            except ValueError:
                errors.append("OWNER_ID must be an integer")

        if cls.AI_TIMEOUT <= 0:
            errors.append("AI_TIMEOUT must be positive")

        if cls.HISTORY_LIMIT <= 0:
            errors.append("HISTORY_LIMIT must be positive")

        if not cls._valid_time_format(cls.DND_START):
            errors.append("DND_START must be HH:MM")

        if not cls._valid_time_format(cls.DND_END):
            errors.append("DND_END must be HH:MM")

        if cls.DND_MODE not in {"silent", "sleepy"}:
            errors.append("DND_MODE must be 'silent' or 'sleepy'")

        if cls.TYPING_MIN_DELAY < 0 or cls.TYPING_MAX_DELAY < 0:
            errors.append("Typing delays must be non-negative")

        if cls.TYPING_MAX_DELAY < cls.TYPING_MIN_DELAY:
            errors.append("TYPING_MAX_DELAY must be >= TYPING_MIN_DELAY")

        if cls.TYPO_PROBABILITY < 0 or cls.TYPO_PROBABILITY > 1:
            errors.append("TYPO_PROBABILITY must be between 0 and 1")

        if errors:
            for error in errors:
                logging.getLogger(__name__).error("Configuration error: %s", error)
            raise ValueError("Configuration validation failed")

        cls._ensure_media_dirs()

    @staticmethod
    def _valid_time_format(time_value: str) -> bool:
        try:
            parts = time_value.split(":")
            if len(parts) != 2:
                return False
            hour = int(parts[0])
            minute = int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False

    @classmethod
    def _ensure_media_dirs(cls):
        cls.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VIDEO_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_stickers(cls) -> dict:
        logger = logging.getLogger(__name__)
        if not Path(cls.STICKERS_FILE).exists():
            logger.warning("Stickers file not found: %s", cls.STICKERS_FILE)
            return {}

        try:
            with open(cls.STICKERS_FILE, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
            logger.warning("Stickers file must contain a JSON object")
        except json.JSONDecodeError as exc:
            logger.error("Invalid stickers JSON: %s", exc)
        return {}
