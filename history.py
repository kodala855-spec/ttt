import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
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
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_timestamp 
                    ON messages(chat_id, timestamp DESC)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_outgoing 
                    ON messages(chat_id, is_outgoing, timestamp DESC)
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS response_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        response_timestamp DATETIME NOT NULL
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_response_chat_time 
                    ON response_log(chat_id, response_timestamp DESC)
                """)

                await db.commit()
                self._initialized = True
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def store_message(
        self,
        chat_id: int,
        message_id: int,
        user_id: Optional[int],
        username: Optional[str],
        text: Optional[str],
        timestamp: datetime,
        is_outgoing: bool = False
    ) -> None:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO messages 
                    (chat_id, message_id, user_id, username, text, timestamp, is_outgoing)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (chat_id, message_id, user_id, username, text, timestamp, is_outgoing))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to store message: {e}")

    async def get_recent_messages(
        self,
        chat_id: int,
        limit: int = 20,
        include_outgoing: bool = True
    ) -> List[Dict]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                if include_outgoing:
                    cursor = await db.execute("""
                        SELECT * FROM messages 
                        WHERE chat_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (chat_id, limit))
                else:
                    cursor = await db.execute("""
                        SELECT * FROM messages 
                        WHERE chat_id = ? AND is_outgoing = 0 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (chat_id, limit))

                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []

    async def get_context_for_ai(self, chat_id: int, max_messages: int = 10) -> str:
        messages = await self.get_recent_messages(chat_id, limit=max_messages)

        if not messages:
            return ""

        context_lines = []
        for msg in messages:
            sender = "You" if msg["is_outgoing"] else (msg["username"] or f"User{msg['user_id']}")
            text = msg["text"] or "[media]"
            context_lines.append(f"{sender}: {text}")

        return "\n".join(context_lines)

    async def log_response(self, chat_id: int) -> None:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO response_log (chat_id, response_timestamp)
                    VALUES (?, ?)
                """, (chat_id, datetime.now()))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log response: {e}")

    async def can_respond(self, chat_id: int) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT response_timestamp FROM response_log
                    WHERE chat_id = ?
                    ORDER BY response_timestamp DESC
                    LIMIT 1
                """, (chat_id,))

                row = await cursor.fetchone()
                if not row:
                    return True

                last_response = datetime.fromisoformat(row[0])
                time_since = (datetime.now() - last_response).total_seconds()
                return time_since >= Config.MIN_RESPONSE_INTERVAL
        except Exception as e:
            logger.error(f"Failed to check response eligibility: {e}")
            return True

    async def get_message_stats(self, chat_id: int, days: int = 7) -> Dict:
        try:
            since = datetime.now() - timedelta(days=days)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_outgoing = 1 THEN 1 ELSE 0 END) as outgoing,
                        SUM(CASE WHEN is_outgoing = 0 THEN 1 ELSE 0 END) as incoming
                    FROM messages
                    WHERE chat_id = ? AND timestamp > ?
                """, (chat_id, since))

                row = await cursor.fetchone()
                return {
                    "total": row[0] or 0,
                    "outgoing": row[1] or 0,
                    "incoming": row[2] or 0
                }
        except Exception as e:
            logger.error(f"Failed to get message stats: {e}")
            return {"total": 0, "outgoing": 0, "incoming": 0}

    async def cleanup_old_messages(self, days: int = 30) -> int:
        try:
            cutoff = datetime.now() - timedelta(days=days)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM messages WHERE timestamp < ?
                """, (cutoff,))
                await db.commit()
                deleted = cursor.rowcount
                logger.info(f"Cleaned up {deleted} old messages")
                return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            return 0

    async def close(self) -> None:
        self.executor.shutdown(wait=True)
        logger.info("HistoryManager closed")
