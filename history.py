import asyncio
import json
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HistoryManager:
    def __init__(self, db_path: str, max_workers: int = 4) -> None:
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.init_db()

    def init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_history
                ON chat_history(chat_id, created_at DESC)
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    chat_id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS blacklist (
                    user_id INTEGER PRIMARY KEY,
                    added_at REAL NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS whitelist (
                    user_id INTEGER PRIMARY KEY,
                    added_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    async def _execute_sync(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    async def add_message(
        self,
        chat_id: int,
        role: str,
        content: str,
        message_id: Optional[int] = None,
        created_at: Optional[float] = None,
    ) -> None:
        created_at = created_at or datetime.utcnow().timestamp()

        def _add() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO chat_history (chat_id, message_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chat_id, message_id, role, content, created_at),
                )
                conn.commit()

        await self._execute_sync(_add)

    async def get_history(self, chat_id: int, limit: int) -> List[Dict[str, Any]]:
        def _fetch() -> List[Dict[str, Any]]:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT role, content, created_at
                    FROM chat_history
                    WHERE chat_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (chat_id, limit),
                )
                rows = cursor.fetchall()
                return [
                    {"role": row[0], "content": row[1], "created_at": row[2]}
                    for row in reversed(rows)
                ]

        return await self._execute_sync(_fetch)

    async def save_profile(self, chat_id: int, data: Dict[str, Any]) -> None:
        payload = json.dumps(data)
        timestamp = datetime.utcnow().timestamp()

        def _save() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO profiles (chat_id, data, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(chat_id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
                    """,
                    (chat_id, payload, timestamp),
                )
                conn.commit()

        await self._execute_sync(_save)

    async def get_profile(self, chat_id: int) -> Dict[str, Any]:
        def _fetch() -> Dict[str, Any]:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM profiles WHERE chat_id = ?", (chat_id,))
                row = cursor.fetchone()
                if not row:
                    return {}
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    logger.warning("Invalid profile JSON for chat %s", chat_id)
                    return {}

        return await self._execute_sync(_fetch)

    async def add_blacklist(self, user_id: int) -> None:
        timestamp = datetime.utcnow().timestamp()

        def _add() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO blacklist (user_id, added_at) VALUES (?, ?)",
                    (user_id, timestamp),
                )
                conn.commit()

        await self._execute_sync(_add)

    async def remove_blacklist(self, user_id: int) -> None:
        def _remove() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))
                conn.commit()

        await self._execute_sync(_remove)

    async def is_blacklisted(self, user_id: int) -> bool:
        def _check() -> bool:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,))
                return cursor.fetchone() is not None

        return await self._execute_sync(_check)

    async def add_whitelist(self, user_id: int) -> None:
        timestamp = datetime.utcnow().timestamp()

        def _add() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO whitelist (user_id, added_at) VALUES (?, ?)",
                    (user_id, timestamp),
                )
                conn.commit()

        await self._execute_sync(_add)

    async def is_whitelisted(self, user_id: int) -> bool:
        def _check() -> bool:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM whitelist WHERE user_id = ?", (user_id,))
                return cursor.fetchone() is not None

        return await self._execute_sync(_check)

    async def clear_history(self, chat_id: int) -> None:
        def _clear() -> None:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
                conn.commit()

        await self._execute_sync(_clear)

    async def cleanup_old_messages(self, max_age_days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        cutoff_ts = cutoff.timestamp()

        def _cleanup() -> int:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE created_at < ?", (cutoff_ts,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted

        return await self._execute_sync(_cleanup)

    def close(self) -> None:
        self.executor.shutdown(wait=True)
