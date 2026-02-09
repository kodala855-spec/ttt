import re
import random
import logging

logger = logging.getLogger(__name__)


def add_typos(text, probability=0.1):
    if random.random() > probability:
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


def add_delays(min_delay=1, max_delay=3):
    return random.uniform(min_delay, max_delay)


def casualize_text(text):
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


def should_reply(message_text, bot_username, reply_probability=0.7):
    if not message_text:
        return False
    
    text_lower = message_text.lower()
    
    if bot_username and bot_username.lower() in text_lower:
        return True
    
    question_words = ['who', 'what', 'when', 'where', 'why', 'how', 'is', 'are', 'can', 'could', 'would', 'should']
    if any(text_lower.startswith(word) for word in question_words):
        return random.random() < 0.8
    
    if '?' in message_text:
        return random.random() < 0.9
    
    return random.random() < reply_probability


def parse_tags(text):
    tags = {
        'photo': None,
        'video_note': None,
        'sticker': None,
        'reaction': None,
    }
    
    clean_text = text
    
    photo_match = re.search(r'\[photo:([^\]]+)\]', text)
    if photo_match:
        tags['photo'] = photo_match.group(1)
        clean_text = clean_text.replace(photo_match.group(0), '')
    
    video_match = re.search(r'\[video_note:([^\]]+)\]', text)
    if video_match:
        tags['video_note'] = video_match.group(1)
        clean_text = clean_text.replace(video_match.group(0), '')
    
    sticker_match = re.search(r'\[sticker:([^\]]+)\]', text)
    if sticker_match:
        tags['sticker'] = sticker_match.group(1)
        clean_text = clean_text.replace(sticker_match.group(0), '')
    
    reaction_match = re.search(r'\[reaction:([^\]]+)\]', text)
    if reaction_match:
        tags['reaction'] = reaction_match.group(1)
        clean_text = clean_text.replace(reaction_match.group(0), '')
    
    clean_text = clean_text.strip()
    
    return clean_text, tags


def select_random_file(directory):
    import os
    from pathlib import Path
    
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        logger.warning(f"Directory does not exist: {directory}")
        return None
    
    files = [f for f in dir_path.iterdir() if f.is_file()]
    if not files:
        logger.warning(f"No files found in directory: {directory}")
        return None
    
    selected = random.choice(files)
    logger.info(f"Selected random file: {selected}")
    return str(selected)


def get_sticker_id(stickers_dict, key):
    sticker_id = stickers_dict.get(key)
    if not sticker_id:
        logger.warning(f"Sticker key not found: {key}")
    return sticker_id


def format_history_for_ai(history_entries):
    formatted = []
    for entry in history_entries:
        role = entry.get('role', 'user')
        content = entry.get('content', '')
        formatted.append({'role': role, 'content': content})
    return formatted


def is_dnd_active(dnd_start, dnd_end):
    from datetime import datetime
    
    try:
        now = datetime.now().time()
        start_time = datetime.strptime(dnd_start, "%H:%M").time()
        end_time = datetime.strptime(dnd_end, "%H:%M").time()
        
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time
    except Exception as e:
        logger.error(f"Error checking DND status: {e}")
        return False


def sanitize_filename(filename):
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:255]


def validate_reaction_emoji(emoji):
    common_reactions = ['👍', '👎', '❤️', '🔥', '🥰', '👏', '😁', '🤔', '🤯', '😱', '🤬', '😢', '🎉', '🤩', '🤮', '💩', '🙏']
    return emoji in common_reactions
