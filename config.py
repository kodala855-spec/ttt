import os
import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()


def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = RotatingFileHandler(
        'userbot.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


class Config:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OWNER_ID = os.getenv("OWNER_ID")
    
    DND_START = os.getenv("DND_START", "23:00")
    DND_END = os.getenv("DND_END", "08:00")
    
    SYSTEM_PROMPT = os.getenv(
        "SYSTEM_PROMPT",
        "You are a helpful assistant having a casual conversation. Keep responses natural, concise, and friendly."
    )
    
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))
    HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))
    SAFETY_SWITCH = os.getenv("SAFETY_SWITCH", "true").lower() == "true"
    
    DB_PATH = os.getenv("DB_PATH", "chat_history.db")
    STICKERS_FILE = os.getenv("STICKERS_FILE", "stickers.json")
    
    PHOTOS_DIR = Path(os.getenv("PHOTOS_DIR", "media/photos"))
    VIDEO_NOTES_DIR = Path(os.getenv("VIDEO_NOTES_DIR", "media/video_notes"))
    
    @classmethod
    def validate(cls):
        errors = []
        
        if not cls.API_ID:
            errors.append("API_ID is required")
        else:
            try:
                int(cls.API_ID)
            except ValueError:
                errors.append("API_ID must be a valid integer")
        
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
                errors.append("OWNER_ID must be a valid integer")
        
        if cls.AI_TIMEOUT <= 0:
            errors.append("AI_TIMEOUT must be positive")
        
        if cls.HISTORY_LIMIT <= 0:
            errors.append("HISTORY_LIMIT must be positive")
        
        if not cls._validate_time_format(cls.DND_START):
            errors.append("DND_START must be in HH:MM format")
        
        if not cls._validate_time_format(cls.DND_END):
            errors.append("DND_END must be in HH:MM format")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        cls._ensure_directories()
        logger.info("Configuration validated successfully")
    
    @staticmethod
    def _validate_time_format(time_str):
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
    
    @classmethod
    def _ensure_directories(cls):
        cls.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VIDEO_NOTES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directories: {cls.PHOTOS_DIR}, {cls.VIDEO_NOTES_DIR}")
    
    @classmethod
    def load_stickers(cls):
        try:
            with open(cls.STICKERS_FILE, 'r') as f:
                stickers = json.load(f)
                if not isinstance(stickers, dict):
                    logger.warning(f"Stickers file should contain a dict, got {type(stickers)}")
                    return {}
                logger.info(f"Loaded {len(stickers)} sticker mappings")
                return stickers
        except FileNotFoundError:
            logger.warning(f"Stickers file not found: {cls.STICKERS_FILE}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in stickers file: {e}")
            return {}
