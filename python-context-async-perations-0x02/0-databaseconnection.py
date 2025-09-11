#!/usr/bin/python3
"""
0-databaseconnection.py

Custom class-based context manager for managing an SQLite database connection.
- Opens the connection on __enter__
- Commits on successful exit, rolls back on exception
- Always closes the connection
- Demonstrates usage by querying: SELECT * FROM users
"""

import sqlite3
from typing import Optional


class DatabaseConnection:
    """Class-based context manager for an SQLite connection."""

    def __init__(self, db_path: str = "users.db") -> None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.conn is not None:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()
        # Return False so any exception is not suppressed
        return False


# --- Demo usage ---
if __name__ == "__main__":
    with DatabaseConnection("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        print(rows)
