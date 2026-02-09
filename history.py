import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, db_path: str, max_workers: int = 5):
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.init_db()
    
    def init_db(self):
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
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        preferences TEXT,
                        topics TEXT,
                        facts TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS blacklist (
                        user_id INTEGER PRIMARY KEY,
                        reason TEXT,
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS whitelist (
                        user_id INTEGER PRIMARY KEY,
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    
    def _execute_sync(self, query: str, params: tuple = ()) -> List[tuple]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database execution error: {e}")
            raise
    
    async def add_message(self, chat_id: int, message_id: int, role: str, content: str, timestamp: float):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._execute_sync,
            """
                INSERT INTO chat_history (chat_id, message_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, message_id, role, content, timestamp)
        )
        logger.debug(f"Added message to history: chat_id={chat_id}, role={role}")
    
    async def get_history(self, chat_id: int, limit: int = 10) -> List[Dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp, message_id
                    FROM chat_history
                    WHERE chat_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (chat_id, limit))
                
                rows = cursor.fetchall()
                return [
                    {
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2],
                        'message_id': row[3]
                    }
                    for row in reversed(rows)
                ]
        
        result = await loop.run_in_executor(self.executor, _get)
        logger.debug(f"Retrieved {len(result)} messages for chat_id={chat_id}")
        return result
    
    async def save_profile(self, user_id: int, username: str = None, first_name: str = None, 
                           last_name: str = None, preferences: List[str] = None, 
                           topics: List[str] = None, facts: List[str] = None):
        import asyncio
        loop = asyncio.get_event_loop()
        
        prefs_json = json.dumps(preferences) if preferences else '[]'
        topics_json = json.dumps(topics) if topics else '[]'
        facts_json = json.dumps(facts) if facts else '[]'
        
        def _save():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profiles 
                    (user_id, username, first_name, last_name, preferences, topics, facts, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, prefs_json, topics_json, facts_json, datetime.now()))
                conn.commit()
        
        await loop.run_in_executor(self.executor, _save)
        logger.debug(f"Saved profile for user_id={user_id}")
    
    async def get_profile(self, user_id: int) -> Optional[Dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, first_name, last_name, preferences, topics, facts
                    FROM user_profiles WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'user_id': user_id,
                        'username': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'preferences': json.loads(row[3]) if row[3] else [],
                        'topics': json.loads(row[4]) if row[4] else [],
                        'facts': json.loads(row[5]) if row[5] else []
                    }
                return None
        
        result = await loop.run_in_executor(self.executor, _get)
        return result
    
    async def add_blacklist(self, user_id: int, reason: str = None):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._execute_sync,
            "INSERT OR REPLACE INTO blacklist (user_id, reason) VALUES (?, ?)",
            (user_id, reason)
        )
        logger.info(f"Added user {user_id} to blacklist")
    
    async def remove_blacklist(self, user_id: int):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._execute_sync,
            "DELETE FROM blacklist WHERE user_id = ?",
            (user_id,)
        )
        logger.info(f"Removed user {user_id} from blacklist")
    
    async def is_blacklisted(self, user_id: int) -> bool:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _check():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,))
                return cursor.fetchone() is not None
        
        return await loop.run_in_executor(self.executor, _check)
    
    async def add_whitelist(self, user_id: int):
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._execute_sync,
            "INSERT OR REPLACE INTO whitelist (user_id) VALUES (?)",
            (user_id,)
        )
        logger.info(f"Added user {user_id} to whitelist")
    
    async def is_whitelisted(self, user_id: int) -> bool:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _check():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM whitelist WHERE user_id = ?", (user_id,))
                return cursor.fetchone() is not None
        
        return await loop.run_in_executor(self.executor, _check)
    
    async def clear_history(self, chat_id: int):
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _clear():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        
        deleted = await loop.run_in_executor(self.executor, _clear)
        logger.info(f"Cleared {deleted} messages from chat_id={chat_id}")
    
    async def cleanup_old_messages(self, days: int = 30):
        import asyncio
        loop = asyncio.get_event_loop()
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        def _cleanup():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE timestamp < ?", (cutoff_time,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        
        deleted = await loop.run_in_executor(self.executor, _cleanup)
        logger.info(f"Cleaned up {deleted} old messages")
    
    def close(self):
        self.executor.shutdown(wait=True)
        logger.info("HistoryManager executor shutdown")
