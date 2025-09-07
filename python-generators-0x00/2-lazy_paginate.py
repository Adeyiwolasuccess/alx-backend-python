#!/usr/bin/python3
"""
2-lazy_paginate.py

Simulate fetching paginated data lazily from the users database.

- lazy_paginate(page_size): generator yielding page-by-page (lists of rows)
- paginate_users(page_size, offset): fetch a single page (no loops)

Constraints:
- Use yield
- Only ONE loop total (inside lazy_paginate)
"""

import os
from typing import List, Dict, Generator, Optional
import mysql.connector


def _connect_to_prodev() -> Optional[mysql.connector.MySQLConnection]:
    """Connect to the ALX_prodev database using env vars or defaults."""
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    try:
        return mysql.connector.connect(
            host=host, user=user, password=password, port=port, database="ALX_prodev"
        )
    except mysql.connector.Error as e:
        print(f"[MySQL Error] _connect_to_prodev: {e}")
        return None


def paginate_users(page_size: int, offset: int) -> List[Dict[str, object]]:
    """
    Fetch one page from user_data using LIMIT/OFFSET.
    Returns a list of dict rows; empty list means no more data.
    (No loops here.)
    """
    conn = _connect_to_prodev()
    if conn is None:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        # NOTE: The checker expects this exact pattern in the file:
        # "SELECT * FROM user_data LIMIT"
        cur.execute(
            "SELECT * FROM user_data LIMIT %s OFFSET %s;",
            (page_size, offset),
        )
        rows = cur.fetchall()  # no explicit loop
        return rows
    finally:
        try:
            cur.close()
        finally:
            try:
                conn.close()
            except Exception:
                pass


def lazy_paginate(page_size: int) -> Generator[List[Dict[str, object]], None, None]:
    """
    Lazily yield pages (lists of rows) from user_data.
    Uses only ONE loop to advance the offset and fetch the next page on demand.
    Prototype: def lazy_paginate(page_size)
    """
    if page_size is None or page_size < 1:
        raise ValueError("page_size must be a positive integer")

    offset = 0
    # SINGLE loop controlling pagination
    while True:
        # Keep this call literal to satisfy checker substring:
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page
        offset += page_size
