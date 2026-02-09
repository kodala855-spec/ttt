# Human-like Telegram Userbot

A sophisticated Telegram userbot powered by Pyrogram and OpenAI that mimics human conversation behavior with realistic typing patterns, typos, reactions, and media sending capabilities.

## Features

### Core Functionality
- **AI-Powered Responses**: Uses OpenAI GPT for natural conversation
- **Conversation History**: SQLite database with async operations
- **Human-like Behavior**: Realistic typing delays, typos, casual language
- **Smart Reply Logic**: Contextual decision-making for when to respond
- **Do Not Disturb**: Configurable quiet hours

### Advanced Features
- **Owner Commands**: Pause/resume, status check, history clearing
- **Media Support**: Send photos, video notes, and stickers
- **Reaction Support**: React to messages with emojis
- **Tag Parsing**: Extract media/reaction commands from AI responses
- **Safety Pause**: Manual control to prevent unwanted responses
- **Async Architecture**: Non-blocking operations with ThreadPoolExecutor

## Installation

### Prerequisites
- Python 3.8 or higher
- Telegram account
- OpenAI API key
- Telegram API credentials (API_ID and API_HASH)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd <repository-directory>
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Get Telegram API credentials**
   - Visit https://my.telegram.org
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy API_ID and API_HASH to .env

5. **Get OpenAI API key**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy to OPENAI_API_KEY in .env

6. **Get your Telegram User ID**
   - Message @userinfobot on Telegram
   - Copy your ID to OWNER_ID in .env

7. **Add media files (optional)**
```bash
# Add photos to media/photos/
# Add video notes to media/video_notes/
```

8. **Configure stickers (optional)**
   - Send a sticker in Telegram
   - Forward it to @JsonDumpBot
   - Copy the file_id from the sticker object
   - Add to stickers.json with a memorable key

## Usage

### Starting the Bot
```bash
python main.py
```

On first run, you'll be prompted to enter the verification code sent to your Telegram account.

### Owner Commands

All owner commands start with a dot (`.`) and only work for messages sent by you:

- `.pause` - Pause bot responses
- `.resume` - Resume bot responses
- `.status` - Show bot status and statistics
- `.clear` - Clear conversation history for current chat

### Configuration

Edit `.env` to customize behavior:

```env
# Do Not Disturb hours (24-hour format)
DND_START=23:00
DND_END=08:00

# AI response timeout (seconds)
AI_TIMEOUT=30

# Number of messages to include in context
HISTORY_LIMIT=10

# Custom AI personality
SYSTEM_PROMPT=You are a helpful assistant...
```

### AI Response Tags

The AI can include special tags in responses to trigger actions:

- `[photo:filename.jpg]` - Send specific photo from media/photos/
- `[photo:random]` - Send random photo
- `[video_note:filename.mp4]` - Send specific video note
- `[video_note:random]` - Send random video note
- `[sticker:key]` - Send sticker by key from stickers.json
- `[reaction:👍]` - React to the message with emoji

Example AI response:
```
That's awesome! [reaction:🔥] Here's what I was talking about [photo:random]
```

## Project Structure

```
.
├── main.py              # Main application and message handling
├── config.py            # Configuration and validation
├── behavior.py          # Human-like behavior functions (11 functions)
├── history.py           # SQLite history manager with async wrapper
├── ai_handler.py        # OpenAI API integration
├── requirements.txt     # Python dependencies (pinned versions)
├── .env.example         # Environment variables template
├── stickers.json        # Sticker file_id mappings
├── README.md            # This file
└── media/
    ├── photos/          # Photo files for sending
    │   └── .gitkeep
    └── video_notes/     # Video note files for sending
        └── .gitkeep
```

## Behavior Functions

The bot includes 11 behavior functions for human-like interaction:

1. `add_typos()` - Randomly introduce realistic typos
2. `add_delays()` - Calculate typing delays
3. `casualize_text()` - Convert formal to casual language
4. `should_reply()` - Decide whether to respond
5. `parse_tags()` - Extract media/reaction tags
6. `select_random_file()` - Pick random media file
7. `get_sticker_id()` - Retrieve sticker file_id
8. `format_history_for_ai()` - Format chat history for API
9. `is_dnd_active()` - Check Do Not Disturb status
10. `sanitize_filename()` - Clean filenames for safety
11. `validate_reaction_emoji()` - Verify emoji validity

## Database Schema

SQLite database with async operations via ThreadPoolExecutor:

```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_timestamp ON chat_history(chat_id, timestamp DESC);
```

## Logging

Logs are written to:
- `userbot.log` - File log with all events
- Console - Real-time output

Log levels can be adjusted in `main.py`:
```python
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for verbose logs
```

## Safety Features

- **Manual Pause**: Use `.pause` to stop all responses
- **DND Mode**: Automatic quiet hours
- **Owner-only Commands**: Control commands restricted to owner
- **Validation**: Configuration validation on startup
- **Error Handling**: Graceful handling of API errors and rate limits
- **FloodWait**: Automatic handling of Telegram rate limits

## Troubleshooting

### Bot not responding
1. Check if paused: Send `.status` from your account
2. Verify DND hours in `.env`
3. Check logs in `userbot.log`

### Authentication errors
1. Verify API_ID and API_HASH are correct
2. Delete `human_userbot.session` and restart
3. Ensure phone number includes country code (+1234567890)

### OpenAI errors
1. Verify API key is valid and has credits
2. Check AI_TIMEOUT setting (increase if slow)
3. Monitor rate limits in logs

### Media not sending
1. Verify files exist in media/photos/ or media/video_notes/
2. Check file permissions
3. Ensure filenames are sanitized (no special characters)

## Development

### Running syntax checks
```bash
python -m py_compile main.py
python -m py_compile config.py
python -m py_compile behavior.py
python -m py_compile history.py
python -m py_compile ai_handler.py
```

### Testing database
```bash
python -c "from history import HistoryManager; h = HistoryManager('test.db'); print('OK')"
```

### Testing AI handler
```bash
python -c "from ai_handler import AIHandler; print('OK')"
```

## Dependencies

All dependencies are pinned to specific versions in `requirements.txt`:

- `pyrogram==2.0.106` - Telegram MTProto API framework
- `tgcrypto==1.2.5` - Cryptography for Pyrogram (performance)
- `openai==1.12.0` - OpenAI API client
- `python-dotenv==1.0.1` - Environment variable management
- `aiosqlite==0.19.0` - Async SQLite operations

## Security Notes

- Never commit `.env` file with real credentials
- Keep your session file (`human_userbot.session`) private
- Rotate OpenAI API keys periodically
- Review bot responses regularly to ensure appropriate behavior
- Use `.pause` when not actively monitoring the bot

## License

This project is provided as-is for educational and personal use.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style conventions
- All functions include error handling
- Logging is comprehensive
- Configuration is validated

## Support

For issues or questions:
1. Check the logs in `userbot.log`
2. Review the troubleshooting section
3. Verify configuration in `.env`
4. Test individual components (config, behavior, history, ai_handler)
