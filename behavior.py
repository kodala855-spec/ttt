import logging
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def calculate_typing_delay(text: str, min_delay: float, max_delay: float) -> float:
    if not text:
        return min_delay
    per_char = 0.045
    base = min_delay + len(text) * per_char
    return max(min_delay, min(max_delay, base))


def introduce_typo(text: str, probability: float = 0.08) -> Tuple[str, str]:
    if not text or random.random() > probability:
        return text, text

    words = text.split()
    if not words:
        return text, text

    typo_index = random.randint(0, len(words) - 1)
    word = words[typo_index]
    if len(word) < 3:
        return text, text

    char_index = random.randint(1, len(word) - 2)
    word_list = list(word)
    if random.random() < 0.5:
        word_list[char_index], word_list[char_index + 1] = word_list[char_index + 1], word_list[char_index]
    else:
        word_list.pop(char_index)

    words[typo_index] = "".join(word_list)
    typo_text = " ".join(words)
    return typo_text, text


def casualize_text(text: str) -> str:
    replacements = {
        r"\bI am\b": "I'm",
        r"\bI will\b": "I'll",
        r"\bdo not\b": "don't",
        r"\bdoes not\b": "doesn't",
        r"\bcannot\b": "can't",
        r"\bthat is\b": "that's",
        r"\byou are\b": "you're",
        r"\bwe are\b": "we're",
        r"\bthey are\b": "they're",
    }

    result = text
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    result = re.sub(r"\s+", " ", result).strip()
    return result


def is_circadian_sleep_time(dnd_start: str, dnd_end: str, now: Optional[datetime] = None) -> bool:
    now_time = (now or datetime.now()).time()
    start_time = datetime.strptime(dnd_start, "%H:%M").time()
    end_time = datetime.strptime(dnd_end, "%H:%M").time()

    if start_time < end_time:
        return start_time <= now_time <= end_time
    return now_time >= start_time or now_time <= end_time


def get_sleepy_response() -> str:
    responses = [
        "half asleep rn, i'll reply later",
        "pretty sleepy atm, can we talk tomorrow?",
        "im out for the night, ttyl",
        "its late here, i'll catch up later",
    ]
    return random.choice(responses)


def parse_media_tag(text: str) -> Tuple[str, Dict[str, Optional[str]]]:
    tags = {
        "photo": None,
        "video_note": None,
        "sticker": None,
    }

    clean_text = text
    for key in tags.keys():
        match = re.search(rf"\[{key}:([^\]]+)\]", clean_text, flags=re.IGNORECASE)
        if match:
            tags[key] = match.group(1).strip()
            clean_text = clean_text.replace(match.group(0), "")

    return clean_text.strip(), tags


def parse_reaction_tag(text: str) -> Tuple[str, Optional[str]]:
    match = re.search(r"\[reaction:([^\]]+)\]", text, flags=re.IGNORECASE)
    if not match:
        return text, None
    cleaned = text.replace(match.group(0), "").strip()
    return cleaned, match.group(1).strip()


def extract_learning_data(text: str) -> Tuple[str, List[str]]:
    matches = re.findall(r"\[learn:([^\]]+)\]", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[learn:[^\]]+\]", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    return cleaned, [item.strip() for item in matches if item.strip()]


def clean_response_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    return text.strip()


def format_message_for_history(message_text: str, sender_name: str, is_owner: bool) -> str:
    if not message_text:
        return ""
    name = "Owner" if is_owner else (sender_name or "User")
    return f"{name}: {message_text.strip()}"


def format_bot_message_for_history(message_text: str) -> str:
    if not message_text:
        return ""
    return f"Assistant: {message_text.strip()}"
