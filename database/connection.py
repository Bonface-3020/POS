import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from config import DB_PATH, SCHEMA_PATH


class DatabaseManager:
    """Manages SQLite database connections and transactions safely."""

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls, db_path: Optional[str or Path] = None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = Path(db_path) if db_path else DB_PATH
            cls._instance.initialize_db()
        elif db_path and Path(db_path) != cls._instance.db_path:
            # Allow pointing to a different DB (e.g. for testing)
            cls._instance.db_path = Path(db_path)
            cls._instance.initialize_db()
        return cls._instance

    def initialize_db(self):
        """Initializes database schema if tables do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='products'"
            )
            table_exists = cursor.fetchone()[0] > 0
            if not table_exists and SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()

    @contextmanager
    def get_connection(self):
        """Yields a database connection with foreign keys enabled and row_factory set."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=20.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Provides an atomic transaction block. Rolls back automatically on exception."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=20.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_db(db_path: Optional[str or Path] = None) -> DatabaseManager:
    return DatabaseManager(db_path)
