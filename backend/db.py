"""
Database Connection Helper
Centralises SQLite connection creation and table initialisation
so all route modules can import without circular dependencies.
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Open and return a SQLite connection with Row factory and WAL mode."""
    db_path = os.getenv("DATABASE_PATH", "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads without blocking writes
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def create_table():
    """Ensure the core `logs` table exists on startup."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            login_time TEXT,
            location TEXT,
            downloads INTEGER,
            failed_attempts INTEGER,
            status TEXT DEFAULT 'Active',
            ip_address TEXT,
            device_fingerprint TEXT
        )
    """)
    conn.commit()
    conn.close()
