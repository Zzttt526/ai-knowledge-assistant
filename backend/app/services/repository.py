"""SQLite persistence for documents and local chat history."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class ApplicationRepository:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    text_length INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                );
                """
            )
            for table in ("documents", "conversations"):
                columns=[row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
                if "user_id" not in columns: connection.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT NOT NULL DEFAULT 'system'")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def add_document(self, document_id: str, filename: str, stored_path: str, text_length: int, user_id: str = "system") -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO documents (document_id,filename,stored_path,text_length,created_at,user_id) VALUES (?, ?, ?, ?, ?, ?)",
                (document_id, filename, stored_path, text_length, self._now(), user_id),
            )

    def create_user(self,email:str,password_hash:str)->str:
        user_id=str(uuid4())
        try:
            with self._connection() as c:c.execute("INSERT INTO users VALUES(?,?,?,?)",(user_id,email,password_hash,self._now()))
        except sqlite3.IntegrityError as exc: raise ValueError("duplicate") from exc
        return user_id
    def get_user_by_email(self,email:str)->dict[str,object]|None:
        with self._connection() as c:r=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        return dict(r) if r else None

    def list_documents(self, user_id: str = "system") -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT document_id, filename, text_length, created_at FROM documents WHERE user_id=? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: str, user_id: str = "system") -> dict[str, object] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM documents WHERE document_id = ? AND user_id=?", (document_id,user_id)).fetchone()
        return dict(row) if row else None

    def delete_document(self, document_id: str) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))

    def ensure_conversation(self, conversation_id: str | None, question: str, user_id: str = "system") -> str:
        if conversation_id:
            with self._connection() as connection:
                exists = connection.execute(
                    "SELECT 1 FROM conversations WHERE conversation_id = ? AND user_id=?", (conversation_id,user_id)
                ).fetchone()
            if exists:
                return conversation_id
        new_id = str(uuid4())
        now = self._now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO conversations (conversation_id,title,created_at,updated_at,user_id) VALUES (?, ?, ?, ?, ?)",
                (new_id, question[:60], now, now,user_id),
            )
        return new_id

    def add_message(self, conversation_id: str, role: str, content: str, sources_json: str | None = None) -> None:
        now = self._now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), conversation_id, role, content, sources_json, now),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now, conversation_id)
            )

    def list_conversations(self,user_id: str = "system") -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT conversation_id, title, created_at, updated_at FROM conversations WHERE user_id=? ORDER BY updated_at DESC",(user_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_messages(self, conversation_id: str, user_id: str = "system") -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT m.role,m.content,m.sources_json,m.created_at FROM messages m JOIN conversations c ON c.conversation_id=m.conversation_id WHERE m.conversation_id=? AND c.user_id=? ORDER BY m.created_at",
                (conversation_id,user_id),
            ).fetchall()
        return [dict(row) for row in rows]
