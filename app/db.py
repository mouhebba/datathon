# app/db.py
import sqlite3
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            authority TEXT NOT NULL,
            title TEXT,
            url TEXT NOT NULL,
            file_path TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            translated_text TEXT,
            analysis_summary TEXT,
            matched_keywords TEXT,
            last_notified_at TEXT
        );
        """
    )

    conn.commit()
    conn.close()
    