import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from app.config import settings


def get_db_path() -> str:
    path = settings.sqlite_db_path
    # Ensure directory exists if not empty
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        try:
            os.makedirs(dirname, exist_ok=True)
        except OSError:
            # Fallback to local app.db if system directory /data is not writeable
            path = os.path.abspath("app.db")
    return path


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages (session_id, id);
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                system_prompt TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
    finally:
        conn.close()


def check_health() -> bool:
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            return row is not None and row[0] == 1
        finally:
            conn.close()
    except Exception:
        return False


def get_session_system_prompt(session_id: str) -> Optional[str]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT system_prompt FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row and row["system_prompt"] is not None:
            return row["system_prompt"]
        return None
    finally:
        conn.close()


def session_exists(session_id: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM messages WHERE session_id = ? LIMIT 1", (session_id,))
        if cursor.fetchone() is not None:
            return True
        cursor.execute("SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1", (session_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_messages_for_session(session_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, metadata FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        result: List[Dict[str, Any]] = []
        for r in rows:
            meta = None
            if r["metadata"]:
                try:
                    meta = json.loads(r["metadata"])
                except Exception:
                    meta = None
            item: Dict[str, Any] = {
                "role": r["role"],
                "content": r["content"],
            }
            if meta is not None:
                item["metadata"] = meta
            result.append(item)
        return result
    finally:
        conn.close()


def save_turn(
    session_id: str,
    user_content: str,
    assistant_content: str,
    metadata: Dict[str, Any],
    system_prompt: Optional[str] = None,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    meta_json = json.dumps(metadata)
    conn = get_connection()
    try:
        with conn:
            # Upsert session record
            if system_prompt is not None:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, system_prompt, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        system_prompt = excluded.system_prompt,
                        updated_at = excluded.updated_at
                    """,
                    (session_id, system_prompt, now_iso, now_iso),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, system_prompt, created_at, updated_at)
                    VALUES (?, NULL, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        updated_at = excluded.updated_at
                    """,
                    (session_id, now_iso, now_iso),
                )

            # Insert user message
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, 'user', ?, NULL, ?)
                """,
                (session_id, user_content, now_iso),
            )

            # Insert assistant message with metadata
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, 'assistant', ?, ?, ?)
                """,
                (session_id, assistant_content, meta_json, now_iso),
            )
    finally:
        conn.close()
