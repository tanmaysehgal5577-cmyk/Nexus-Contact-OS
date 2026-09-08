"""
database.py
Handles all direct interaction with the SQLite database: connecting,
schema creation, and providing a context-managed connection so the
rest of the application never has to deal with raw sqlite3 calls.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from src.exceptions import DatabaseConnectionError

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "contacts.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT NOT NULL,
    address     TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


class Database:
    """Thin wrapper around sqlite3 that manages connection lifecycle and schema."""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _initialize_schema(self):
        try:
            with self.get_connection() as conn:
                conn.execute(SCHEMA)
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(
                f"Failed to initialize database at '{self.db_path}': {exc}"
            ) from exc

    @contextmanager
    def get_connection(self):
        """Yield a sqlite3 connection, ensuring it is always closed properly.

        Only connection-establishment failures are wrapped as
        DatabaseConnectionError here. Errors raised *while the caller uses*
        the connection (e.g. IntegrityError on a duplicate key) are left to
        propagate untouched, so calling code can catch specific sqlite3
        exceptions such as IntegrityError.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Could not connect to database: {exc}") from exc

        try:
            yield conn
        finally:
            conn.close()
