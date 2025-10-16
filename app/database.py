"""Database operations for conversation history."""
import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

DATABASE_PATH = "data/conversations.db"

async def init_db():
    """Initialize the database with required tables."""
    os.makedirs("data", exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL UNIQUE,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()

async def create_conversation(user_email: str, title: str = "New Conversation") -> int:
    """Create a new conversation."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO conversations (user_email, title) VALUES (?, ?)",
            (user_email, title)
        )
        await db.commit()
        return cursor.lastrowid

async def add_message(conversation_id: int, role: str, content: str):
    """Add a message to a conversation."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        await db.commit()

async def get_conversation_messages(conversation_id: int) -> List[Dict]:
    """Get all messages from a conversation."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_user_conversations(user_email: str) -> List[Dict]:
    """Get all conversations for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE user_email = ? ORDER BY updated_at DESC",
            (user_email,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_conversation(conversation_id: int, user_email: str):
    """Delete a conversation and its messages."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Verify ownership
        cursor = await db.execute(
            "SELECT user_email FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = await cursor.fetchone()
        if row and row[0] == user_email:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()

async def store_oauth_token(user_email: str, token_data: Dict):
    """Store or update OAuth token for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO oauth_tokens (user_email, access_token, refresh_token, token_type, expires_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_email) DO UPDATE SET
                access_token = excluded.access_token,
                refresh_token = COALESCE(excluded.refresh_token, refresh_token),
                token_type = excluded.token_type,
                expires_at = excluded.expires_at,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_email,
            token_data.get('access_token'),
            token_data.get('refresh_token'),
            token_data.get('token_type'),
            token_data.get('expires_at')
        ))
        await db.commit()

async def get_oauth_token(user_email: str) -> Optional[Dict]:
    """Get stored OAuth token for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT access_token, refresh_token, token_type, expires_at FROM oauth_tokens WHERE user_email = ?",
            (user_email,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
