# Human-Style Telegram Userbot

A Telegram user-mode bot powered by Pyrogram and OpenAI. It replies like a human with casual language, typing delays, occasional typo corrections, and optional media, reactions, and learning tags.

## Features

- **User-mode client** (API_ID/API_HASH only)
- **OpenAI responses** with configurable system prompt
- **SQLite history** with async ThreadPoolExecutor wrapper
- **Do Not Disturb** with silent or sleepy reply modes
- **Safety auto-pause** when the owner starts typing manually
- **Owner commands** for pause/resume/status/history/blacklist/whitelist
- **Media tags** for photos, video notes, and stickers
- **Reaction tags** for emoji reactions
- **Learning tags** for storing profile notes
- **Rotating logs** to keep log size under control

## Installation

```bash
pip install -r requirements.txt
```

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

## Configuration

Key `.env` values:

```env
API_ID=123456
API_HASH=your_api_hash_here
OWNER_ID=123456789
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
SYSTEM_PROMPT=You are a casual, friendly Telegram user. Keep replies short, natural, and human.
AI_TIMEOUT=30
DND_START=23:00
DND_END=08:00
DND_MODE=sleepy
SAFETY_AUTO_PAUSE=true
```

## Running the Bot

```bash
python main.py
```

On first run, Pyrogram will prompt for your phone number and login code.

## Owner Commands

All commands must be sent by the owner (`OWNER_ID`) using a slash prefix:

- `/pause` — Stop responses
- `/resume` — Resume responses
- `/status` — Show bot status
- `/history` — Show recent history in the current chat
- `/blacklist <user_id>` — Ignore a user
- `/blacklist remove <user_id>` — Remove from blacklist
- `/whitelist <user_id>` — Only respond to whitelisted users

## AI Response Tags

The AI can embed tags in its response:

- `[photo:filename.jpg]` or `[photo:random]`
- `[video_note:filename.mp4]` or `[video_note:random]`
- `[sticker:key]` (from `stickers.json`)
- `[reaction:👍]`
- `[learn:prefers cold brew]`

Example:

```
all good here! [reaction:🔥] [photo:random] [learn:likes synthwave]
```

## Project Structure

```
.
├── ai_handler.py
├── behavior.py
├── config.py
├── history.py
├── main.py
├── requirements.txt
├── .env.example
├── stickers.json
└── media/
    ├── photos/
    │   └── .gitkeep
    └── video_notes/
        └── .gitkeep
```

## Development

Run a syntax check on all modules:

```bash
python -m py_compile main.py
python -m py_compile config.py
python -m py_compile behavior.py
python -m py_compile history.py
python -m py_compile ai_handler.py
```

## Notes

- Keep your `.env` file private.
- Use `/pause` when you want to take over a conversation manually.
- The bot writes rotating logs to `userbot.log` by default.
