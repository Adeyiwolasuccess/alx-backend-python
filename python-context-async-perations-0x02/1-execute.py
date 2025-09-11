#!/usr/bin/python3
"""
1-execute.py

Reusable class-based context manager that executes a provided SQL query with
parameters and returns the result on __enter__. Manages connection lifecycle
and commits/rolls back as appropriate.
"""

import sqlite3
from typing import Any, Iterable, List, Optional, Tuple


class ExecuteQuery:
    """
    Context manager that:
      - opens an SQLite connection
      - executes the given query with parameters
      - returns the result rows on __enter__
      - commits on success, rolls back on error
      - always closes the connection
    """

    def __init__(self, query: str, params: Iterable[Any] = ()):
        self.query = query
        self.params = tuple(params)
        self.conn: Optional[sqlite3.Connection] = None
        self.cur: Optional[sqlite3.Cursor] = None
        self._result: Optional[List[Tuple[Any, ...]]] = None

    def __enter__(self) -> List[Tuple[Any, ...]]:
        self.conn = sqlite3.connect("users.db")
        self.cur = self.conn.cursor()
        self.cur.execute(self.query, self.params)
        # For a SELECT we fetch results
        self._result = self.cur.fetchall()
        return self._result

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.conn is not None:
            try:
                if exc_type is None:
                    # Safe to commit; SELECTs are no-ops for commit
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                try:
                    if self.cur is not None:
                        self.cur.close()
                finally:
                    self.conn.close()
        # Do not suppress exceptions
        return False


# --- Demo usage per spec ---
if __name__ == "__main__":
    query = "SELECT * FROM users WHERE age > ?"
    with ExecuteQuery(query, (25,)) as rows:
        print(rows)
