import random
import asyncio
from datetime import datetime, time as dt_time
from typing import Optional
from config import Config


def should_respond() -> bool:
    return random.random() < Config.RESPONSE_CHANCE


def is_dnd_active() -> bool:
    if not Config.DND_START or not Config.DND_END:
        return False

    now = datetime.now().time()
    start = datetime.strptime(Config.DND_START, "%H:%M").time()
    end = datetime.strptime(Config.DND_END, "%H:%M").time()

    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end


async def simulate_typing_delay() -> None:
    delay = random.uniform(Config.TYPING_MIN_DELAY, Config.TYPING_MAX_DELAY)
    await asyncio.sleep(delay)


def add_typo(text: str) -> str:
    if not text or random.random() > Config.TYPO_CHANCE:
        return text

    words = text.split()
    if not words:
        return text

    word_index = random.randint(0, len(words) - 1)
    word = words[word_index]

    if len(word) <= 2:
        return text

    typo_type = random.choice(["swap", "duplicate", "omit"])

    if typo_type == "swap" and len(word) > 2:
        pos = random.randint(0, len(word) - 2)
        word = word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]
    elif typo_type == "duplicate":
        pos = random.randint(0, len(word) - 1)
        word = word[:pos] + word[pos] + word[pos:]
    elif typo_type == "omit" and len(word) > 3:
        pos = random.randint(1, len(word) - 2)
        word = word[:pos] + word[pos + 1:]

    words[word_index] = word
    return " ".join(words)


def add_casual_suffix(text: str) -> str:
    if random.random() > Config.CASUAL_SUFFIX_CHANCE:
        return text

    suffixes = [
        "lol",
        "haha",
        "😂",
        "😅",
        "👍",
        "btw",
        "tho",
        "tbh",
        "ngl",
    ]

    suffix = random.choice(suffixes)

    if suffix in ["lol", "haha", "btw", "tho", "tbh", "ngl"]:
        return f"{text} {suffix}"
    else:
        return f"{text} {suffix}"


def truncate_message(text: str, max_length: Optional[int] = None) -> str:
    if max_length is None:
        max_length = Config.MAX_MESSAGE_LENGTH

    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def select_random_photo(photos_dir) -> Optional[str]:
    try:
        photos = list(photos_dir.glob("*.jpg")) + list(photos_dir.glob("*.png")) + list(photos_dir.glob("*.jpeg"))
        if not photos:
            return None
        return str(random.choice(photos))
    except Exception:
        return None


def select_random_video_note(video_notes_dir) -> Optional[str]:
    try:
        video_notes = list(video_notes_dir.glob("*.mp4")) + list(video_notes_dir.glob("*.mov"))
        if not video_notes:
            return None
        return str(random.choice(video_notes))
    except Exception:
        return None


def select_random_sticker(stickers_data: list) -> Optional[str]:
    if not stickers_data:
        return None
    return random.choice(stickers_data)


def calculate_response_delay(message_length: int) -> float:
    base_delay = 2.0
    reading_speed = 0.05
    delay = base_delay + (message_length * reading_speed)
    jitter = random.uniform(-0.5, 1.0)
    return max(1.0, delay + jitter)


def should_send_media() -> str:
    media_types = ["text", "text", "text", "text", "photo", "video_note", "sticker", "reaction"]
    weights = [0.70, 0.10, 0.10, 0.05, 0.05]
    return random.choices(["text", "photo", "video_note", "sticker", "reaction"], weights=weights)[0]
