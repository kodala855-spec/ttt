import re
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def calculate_typing_delay(text: str, min_delay: float = 1.0, max_delay: float = 5.0) -> float:
    base_delay = min(len(text) / 50, max_delay)
    noise = random.uniform(-0.5, 0.5)
    return max(min_delay, min(base_delay + noise, max_delay))


def introduce_typo(text: str, probability: float = 0.05) -> str:
    if random.random() > probability or len(text) < 3:
        return text
    
    words = text.split()
    if not words:
        return text
    
    typo_index = random.randint(0, len(words) - 1)
    word = words[typo_index]
    
    if len(word) > 2:
        char_index = random.randint(1, len(word) - 1)
        word_list = list(word)
        
        if char_index < len(word) - 1 and random.random() > 0.5:
            word_list[char_index], word_list[char_index + 1] = word_list[char_index + 1], word_list[char_index]
        else:
            word_list.pop(char_index)
        
        words[typo_index] = ''.join(word_list)
    
    return ' '.join(words)


def casualize_text(text: str) -> str:
    casual_replacements = {
        r'\bI am\b': 'im',
        r'\byou are\b': 'youre',
        r'\bthey are\b': 'theyre',
        r'\bwe are\b': 'were',
        r'\bcannot\b': 'cant',
        r'\bdo not\b': 'dont',
        r'\bdoes not\b': 'doesnt',
        r'\bwill not\b': 'wont',
        r'\bshould not\b': 'shouldnt',
        r'\bwould not\b': 'wouldnt',
        r'\bI will\b': 'ill',
        r'\byou will\b': 'youll',
    }
    
    result = text
    for pattern, replacement in casual_replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    result = re.sub(r'\.{3,}', '...', result)
    result = re.sub(r'\?{2,}', '??', result)
    result = re.sub(r'!{2,}', '!!', result)
    
    return result


def is_circadian_sleep_time(dnd_start: str, dnd_end: str) -> bool:
    try:
        now = datetime.now().time()
        start_time = datetime.strptime(dnd_start, "%H:%M").time()
        end_time = datetime.strptime(dnd_end, "%H:%M").time()
        
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time
    except Exception as e:
        logger.error(f"Error checking circadian sleep time: {e}")
        return False


def get_sleepy_response() -> str:
    sleepy_responses = [
        "zzzz...",
        "too tired rn",
        "sleeping, talk later",
        "💤",
        "not now, need sleep",
        "zzz",
    ]
    return random.choice(sleepy_responses)


def parse_media_tag(text: str) -> tuple:
    media_tags = {
        'photo': None,
        'video_note': None,
        'sticker': None,
    }
    
    clean_text = text
    
    photo_match = re.search(r'\[photo:([^\]]+)\]', text)
    if photo_match:
        media_tags['photo'] = photo_match.group(1)
        clean_text = clean_text.replace(photo_match.group(0), '')
    
    video_match = re.search(r'\[video_note:([^\]]+)\]', text)
    if video_match:
        media_tags['video_note'] = video_match.group(1)
        clean_text = clean_text.replace(video_match.group(0), '')
    
    sticker_match = re.search(r'\[sticker:([^\]]+)\]', text)
    if sticker_match:
        media_tags['sticker'] = sticker_match.group(1)
        clean_text = clean_text.replace(sticker_match.group(0), '')
    
    clean_text = clean_text.strip()
    
    return clean_text, media_tags


def parse_reaction_tag(text: str) -> tuple:
    reaction = None
    
    reaction_match = re.search(r'\[reaction:([^\]]+)\]', text)
    if reaction_match:
        reaction = reaction_match.group(1)
        text = text.replace(reaction_match.group(0), '').strip()
    
    return text, reaction


def extract_learning_data(text: str) -> dict:
    learning_data = {
        'topics': [],
        'preferences': [],
        'facts': []
    }
    
    topic_match = re.search(r'\[learn_topic:([^\]]+)\]', text)
    if topic_match:
        learning_data['topics'].append(topic_match.group(1))
        text = text.replace(topic_match.group(0), '').strip()
    
    pref_match = re.search(r'\[learn_pref:([^\]]+)\]', text)
    if pref_match:
        learning_data['preferences'].append(pref_match.group(1))
        text = text.replace(pref_match.group(0), '').strip()
    
    fact_match = re.search(r'\[learn_fact:([^\]]+)\]', text)
    if fact_match:
        learning_data['facts'].append(fact_match.group(1))
        text = text.replace(fact_match.group(0), '').strip()
    
    return text, learning_data


def clean_response_text(text: str) -> str:
    text = re.sub(r'\[\w+:[^\]]*\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def format_message_for_history(message_text: str, user_id: int, timestamp: float) -> dict:
    return {
        'role': 'user',
        'content': message_text,
        'user_id': user_id,
        'timestamp': timestamp
    }


def format_bot_message_for_history(response_text: str, timestamp: float) -> dict:
    return {
        'role': 'assistant',
        'content': response_text,
        'timestamp': timestamp
    }
