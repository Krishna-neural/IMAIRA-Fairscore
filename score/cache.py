"""Persistent SHA-256 disk cache and exponential backoff utility for judges."""

import hashlib
import json
import logging
import random
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Normalize text for consistent cache key generation."""
    if not text:
        return ""
    # Strip whitespace, lower case, normalize multi-spaces
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    return cleaned

class SQLiteDiskCache:
    """Persistent SHA-256 disk cache backed by SQLite in WAL mode."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS judge_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload FROM judge_cache WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, cache_key: str, payload: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO judge_cache (cache_key, payload) VALUES (?, ?)",
                (cache_key, json.dumps(payload, sort_keys=True))
            )
            conn.commit()

def execute_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
    retry_exceptions: tuple = (Exception,)
) -> Any:
    """Execute a callable with exponential backoff and full jitter."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return func()
        except retry_exceptions as e:
            last_exc = e
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise e
            # Full jitter: random sleep between 0 and min(max_delay, base_delay * 2^attempt)
            ceiling = min(max_delay, base_delay * (2 ** attempt))
            sleep_duration = random.uniform(0.5 * ceiling, ceiling)
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed with {type(e).__name__}: {e}. "
                f"Retrying in {sleep_duration:.2f}s..."
            )
            time.sleep(sleep_duration)
    if last_exc:
        raise last_exc
