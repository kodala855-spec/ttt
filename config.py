import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    pass


class Config:
    API_ID: int
    API_HASH: str
    PHONE_NUMBER: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    RESPONSE_CHANCE: float
    TYPING_MIN_DELAY: float
    TYPING_MAX_DELAY: float
    TYPO_CHANCE: float
    CASUAL_SUFFIX_CHANCE: float
    DND_START: Optional[str]
    DND_END: Optional[str]
    PHOTOS_DIR: Path
    VIDEO_NOTES_DIR: Path
    STICKERS_FILE: Path
    MAX_MESSAGE_LENGTH: int
    RATE_LIMIT_MESSAGES: int
    RATE_LIMIT_WINDOW: int
    MIN_RESPONSE_INTERVAL: int
    LOG_LEVEL: str
    LOG_FILE: str
    DB_FILE: Path

    @classmethod
    def validate(cls) -> None:
        errors = []

        try:
            cls.API_ID = int(os.getenv("API_ID", "0"))
            if cls.API_ID == 0:
                errors.append("API_ID is required and must be a valid integer")
        except ValueError:
            errors.append("API_ID must be a valid integer")

        cls.API_HASH = os.getenv("API_HASH", "")
        if not cls.API_HASH:
            errors.append("API_HASH is required")

        cls.PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
        if not cls.PHONE_NUMBER:
            errors.append("PHONE_NUMBER is required")

        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        try:
            cls.RESPONSE_CHANCE = float(os.getenv("RESPONSE_CHANCE", "0.15"))
            if not 0 <= cls.RESPONSE_CHANCE <= 1:
                errors.append("RESPONSE_CHANCE must be between 0 and 1")
        except ValueError:
            errors.append("RESPONSE_CHANCE must be a valid float")

        try:
            cls.TYPING_MIN_DELAY = float(os.getenv("TYPING_MIN_DELAY", "1.0"))
            if cls.TYPING_MIN_DELAY < 0:
                errors.append("TYPING_MIN_DELAY must be non-negative")
        except ValueError:
            errors.append("TYPING_MIN_DELAY must be a valid float")

        try:
            cls.TYPING_MAX_DELAY = float(os.getenv("TYPING_MAX_DELAY", "3.0"))
            if cls.TYPING_MAX_DELAY < cls.TYPING_MIN_DELAY:
                errors.append("TYPING_MAX_DELAY must be greater than or equal to TYPING_MIN_DELAY")
        except ValueError:
            errors.append("TYPING_MAX_DELAY must be a valid float")

        try:
            cls.TYPO_CHANCE = float(os.getenv("TYPO_CHANCE", "0.10"))
            if not 0 <= cls.TYPO_CHANCE <= 1:
                errors.append("TYPO_CHANCE must be between 0 and 1")
        except ValueError:
            errors.append("TYPO_CHANCE must be a valid float")

        try:
            cls.CASUAL_SUFFIX_CHANCE = float(os.getenv("CASUAL_SUFFIX_CHANCE", "0.20"))
            if not 0 <= cls.CASUAL_SUFFIX_CHANCE <= 1:
                errors.append("CASUAL_SUFFIX_CHANCE must be between 0 and 1")
        except ValueError:
            errors.append("CASUAL_SUFFIX_CHANCE must be a valid float")

        cls.DND_START = os.getenv("DND_START") or None
        cls.DND_END = os.getenv("DND_END") or None

        if cls.DND_START or cls.DND_END:
            if not (cls.DND_START and cls.DND_END):
                errors.append("Both DND_START and DND_END must be set if DND is enabled")
            else:
                if not cls._validate_time_format(cls.DND_START):
                    errors.append("DND_START must be in HH:MM format")
                if not cls._validate_time_format(cls.DND_END):
                    errors.append("DND_END must be in HH:MM format")

        base_dir = Path(__file__).parent
        cls.PHOTOS_DIR = base_dir / os.getenv("PHOTOS_DIR", "media/photos")
        cls.VIDEO_NOTES_DIR = base_dir / os.getenv("VIDEO_NOTES_DIR", "media/video_notes")
        cls.STICKERS_FILE = base_dir / os.getenv("STICKERS_FILE", "stickers.json")

        cls.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VIDEO_NOTES_DIR.mkdir(parents=True, exist_ok=True)

        try:
            cls.MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
            if cls.MAX_MESSAGE_LENGTH <= 0:
                errors.append("MAX_MESSAGE_LENGTH must be positive")
        except ValueError:
            errors.append("MAX_MESSAGE_LENGTH must be a valid integer")

        try:
            cls.RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "5"))
            if cls.RATE_LIMIT_MESSAGES <= 0:
                errors.append("RATE_LIMIT_MESSAGES must be positive")
        except ValueError:
            errors.append("RATE_LIMIT_MESSAGES must be a valid integer")

        try:
            cls.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
            if cls.RATE_LIMIT_WINDOW <= 0:
                errors.append("RATE_LIMIT_WINDOW must be positive")
        except ValueError:
            errors.append("RATE_LIMIT_WINDOW must be a valid integer")

        try:
            cls.MIN_RESPONSE_INTERVAL = int(os.getenv("MIN_RESPONSE_INTERVAL", "30"))
            if cls.MIN_RESPONSE_INTERVAL < 0:
                errors.append("MIN_RESPONSE_INTERVAL must be non-negative")
        except ValueError:
            errors.append("MIN_RESPONSE_INTERVAL must be a valid integer")

        cls.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        if cls.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

        cls.LOG_FILE = os.getenv("LOG_FILE", "userbot.log")

        cls.DB_FILE = base_dir / os.getenv("DB_FILE", "history.db")

        if errors:
            raise ConfigurationError("\n".join(errors))

        logger.info("Configuration validated successfully")

    @staticmethod
    def _validate_time_format(time_str: str) -> bool:
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hours, minutes = int(parts[0]), int(parts[1])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, AttributeError):
            return False
