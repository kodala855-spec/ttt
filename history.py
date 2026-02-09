import sqlite3
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, db_path: str, max_workers: int = 5):
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._init_db()
    
    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        message_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_timestamp 
                    ON chat_history(chat_id, timestamp DESC)
                """)
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _add_message_sync(self, chat_id: int, message_id: int, role: str, content: str, timestamp: float):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_history (chat_id, message_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (chat_id, message_id, role, content, timestamp))
                conn.commit()
                logger.debug(f"Added message to history: chat_id={chat_id}, role={role}")
        except sqlite3.Error as e:
            logger.error(f"Error adding message to history: {e}")
    
    async def add_message(self, chat_id: int, message_id: int, role: str, content: str, timestamp: float):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._add_message_sync,
            chat_id, message_id, role, content, timestamp
        )
    
    def _get_recent_history_sync(self, chat_id: int, limit: int) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp
                    FROM chat_history
                    WHERE chat_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (chat_id, limit))
                
                rows = cursor.fetchall()
                history = [
                    {
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    }
                    for row in reversed(rows)
                ]
                logger.debug(f"Retrieved {len(history)} messages for chat_id={chat_id}")
                return history
        except sqlite3.Error as e:
            logger.error(f"Error retrieving history: {e}")
            return []
    
    async def get_recent_history(self, chat_id: int, limit: int) -> List[Dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_recent_history_sync,
            chat_id, limit
        )
    
    def _clear_chat_history_sync(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Cleared {deleted} messages from chat_id={chat_id}")
        except sqlite3.Error as e:
            logger.error(f"Error clearing chat history: {e}")
    
    async def clear_chat_history(self, chat_id: int):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._clear_chat_history_sync,
            chat_id
        )
    
    def _get_stats_sync(self) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM chat_history")
                total_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM chat_history")
                total_chats = cursor.fetchone()[0]
                
                return {
                    'total_messages': total_messages,
                    'total_chats': total_chats
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {'total_messages': 0, 'total_chats': 0}
    
    async def get_stats(self) -> Dict:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._get_stats_sync)
    
    def close(self):
        self.executor.shutdown(wait=True)
        logger.info("HistoryManager executor shutdown")
