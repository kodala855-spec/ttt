# Telegram Human Userbot

A production-ready Telegram userbot built with Pyrogram that simulates natural human behavior, including realistic typing delays, occasional typos, casual language, and AI-powered contextual responses.

## Features

### 🤖 Human-like Behavior
- **Realistic typing delays** based on message length
- **Occasional typos** to mimic human typing errors
- **Casual suffixes** like "lol", "haha", emoji for natural conversation
- **Variable response timing** with jitter and reading speed simulation
- **Random response probability** to avoid responding to every message

### 🧠 AI-Powered Responses
- **OpenAI GPT integration** for contextual, natural responses
- **Conversation history tracking** for context-aware replies
- **Personality customization** via system prompts
- **Multiple response types**: text, photos, video notes, stickers, reactions

### 🛡️ Safety & Rate Limiting
- **Do Not Disturb (DND) mode** with configurable hours
- **Rate limiting** per chat to prevent spam
- **Minimum response interval** to avoid appearing too eager
- **Flood protection** with automatic backoff
- **Message length limits** to prevent token overflow

### 📊 Data Management
- **Async SQLite** database for message history
- **ThreadPoolExecutor** for efficient I/O operations
- **Message statistics** tracking per chat
- **Automatic cleanup** of old messages
- **Response logging** for interval tracking

### 🎯 Flexible Response Types
- **Text responses** with AI generation
- **Photo sharing** from local directory
- **Video notes** for quick reactions
- **Sticker/emoji reactions** for casual acknowledgment
- **Smart media selection** based on context

## Project Structure

```
.
├── main.py              # Main bot implementation with HumanUserBot class
├── config.py            # Configuration management and validation
├── behavior.py          # Human behavior simulation (11 functions)
├── history.py           # Async SQLite database manager
├── ai_handler.py        # OpenAI API integration
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment configuration
├── stickers.json        # Sticker/emoji database
├── README.md            # This file
└── media/
    ├── photos/          # Directory for photos to share
    │   └── .gitkeep
    └── video_notes/     # Directory for video notes
        └── .gitkeep
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Telegram API credentials (API ID and API Hash)
- OpenAI API key
- Active Telegram account

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram-userbot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get Telegram API credentials**
   - Go to https://my.telegram.org
   - Log in with your phone number
   - Navigate to "API Development Tools"
   - Create a new application to get `API_ID` and `API_HASH`

5. **Get OpenAI API key**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key

6. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

7. **Add media (optional)**
   - Add photos to `media/photos/` (jpg, png, jpeg)
   - Add video notes to `media/video_notes/` (mp4, mov)

## Configuration

Edit `.env` file with your settings:

### Required Settings

```env
# Telegram credentials
API_ID=12345678
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890

# OpenAI configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Optional Settings

```env
# Behavior customization
RESPONSE_CHANCE=0.15              # 15% chance to respond
TYPING_MIN_DELAY=1.0              # Min typing delay in seconds
TYPING_MAX_DELAY=3.0              # Max typing delay in seconds
TYPO_CHANCE=0.10                  # 10% chance of typo
CASUAL_SUFFIX_CHANCE=0.20         # 20% chance of casual suffix

# Do Not Disturb
DND_START=23:00                   # Start DND at 11 PM
DND_END=08:00                     # End DND at 8 AM

# Rate limiting
MAX_MESSAGE_LENGTH=4096           # Max message length
RATE_LIMIT_MESSAGES=5             # Max messages per window
RATE_LIMIT_WINDOW=60              # Window in seconds
MIN_RESPONSE_INTERVAL=30          # Min seconds between responses

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=userbot.log              # Log file path
```

## Usage

### Start the bot

```bash
python main.py
```

On first run, you'll need to:
1. Enter the verification code sent to your Telegram account
2. Enter 2FA password if enabled

The bot will then run in the background, monitoring messages and responding based on configured behavior.

### Stop the bot

Press `Ctrl+C` or send `SIGTERM` signal. The bot will gracefully shut down, closing all connections and saving state.

## Behavior Functions

The `behavior.py` module contains 11 functions for human-like behavior:

1. **`should_respond()`** - Random chance decision
2. **`is_dnd_active()`** - Check Do Not Disturb status
3. **`simulate_typing_delay()`** - Async typing delay
4. **`add_typo()`** - Add realistic typos to text
5. **`add_casual_suffix()`** - Add casual endings
6. **`truncate_message()`** - Limit message length
7. **`select_random_photo()`** - Pick random photo
8. **`select_random_video_note()`** - Pick random video
9. **`select_random_sticker()`** - Pick random sticker
10. **`calculate_response_delay()`** - Calculate reading time
11. **`should_send_media()`** - Decide response type

## Safety Features

### Rate Limiting
- Prevents sending too many messages in a short time
- Configurable per-chat limits
- Automatic message counting and window management

### DND Mode
- Automatically skip responses during configured hours
- Timezone-aware (uses system timezone)
- Configurable start/end times

### Flood Protection
- Automatic handling of Telegram FloodWait errors
- Exponential backoff on repeated errors
- Graceful degradation under heavy load

### Error Handling
- Comprehensive try-catch blocks
- Logging of all errors
- Graceful fallbacks for failed operations

## Database Schema

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    user_id INTEGER,
    username TEXT,
    text TEXT,
    timestamp DATETIME NOT NULL,
    is_outgoing BOOLEAN NOT NULL DEFAULT 0,
    UNIQUE(chat_id, message_id)
)
```

### Response Log Table
```sql
CREATE TABLE response_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    response_timestamp DATETIME NOT NULL
)
```

## Architecture

### Main Components

1. **HumanUserBot** - Main bot class orchestrating all functionality
2. **HistoryManager** - Async database operations with connection pooling
3. **AIHandler** - OpenAI API integration with error handling
4. **RateLimiter** - Per-chat rate limiting with sliding window
5. **Config** - Centralized configuration with validation

### Message Flow

```
Incoming Message
    ↓
Store in Database
    ↓
Check Filters (outgoing, service, bot)
    ↓
Check DND Status
    ↓
Check Response Interval
    ↓
Check Rate Limit
    ↓
Random Response Decision
    ↓
Calculate Response Delay
    ↓
Select Media Type
    ↓
Generate AI Response (if text)
    ↓
Add Typos & Casual Elements
    ↓
Simulate Typing
    ↓
Send Response
    ↓
Log Response & Update Rate Limit
```

## Development

### Running Tests

```bash
# Syntax check all Python files
python -m py_compile main.py config.py behavior.py history.py ai_handler.py
```

### Adding Custom Behavior

Edit `behavior.py` to customize:
- Typo patterns
- Casual suffixes
- Response delays
- Media selection logic

### Customizing AI Personality

Edit the system prompt in `ai_handler.py`:
```python
def _build_system_prompt(self, chat_title: Optional[str] = None) -> str:
    prompt = """Your custom personality here..."""
    return prompt
```

## Troubleshooting

### Bot not responding

1. Check `LOG_LEVEL=DEBUG` in `.env`
2. Review `userbot.log` for errors
3. Verify `RESPONSE_CHANCE` is not too low
4. Check DND is not active
5. Verify rate limits not exceeded

### API Errors

**OpenAI Rate Limit**: Reduce `RESPONSE_CHANCE` or upgrade plan  
**Telegram FloodWait**: Bot automatically handles this  
**Invalid Credentials**: Verify API_ID, API_HASH, and PHONE_NUMBER

### Session Issues

Delete `*.session` files and restart to create new session:
```bash
rm *.session
python main.py
```

## Best Practices

1. **Start with low RESPONSE_CHANCE** (0.10-0.15) to avoid spam
2. **Enable DND during sleep hours** to maintain realism
3. **Use appropriate LOG_LEVEL** (INFO for production, DEBUG for development)
4. **Regular cleanup** of old messages to keep database small
5. **Monitor rate limits** and adjust as needed
6. **Keep media diverse** for more natural responses
7. **Review logs regularly** for errors or unusual patterns

## Security Considerations

- **Never commit `.env` file** - Contains sensitive credentials
- **Protect session files** - Allow account access
- **Use strong 2FA** on Telegram account
- **Monitor API usage** - Prevent unexpected charges
- **Review message logs** - Ensure appropriate responses
- **Limit permissions** - Run with minimal required access

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on the repository.

## Disclaimer

This userbot is for educational purposes. Ensure compliance with Telegram's Terms of Service. The authors are not responsible for misuse or violations of platform policies. Use responsibly and ethically.
