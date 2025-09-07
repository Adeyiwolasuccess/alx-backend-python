#!/usr/bin/python3
"""
2-lazy_paginate.py

Objective:
Simulate fetching paginated data from the users database using a generator
that lazily loads each page on demand.

- lazy_paginate(page_size): generator yielding pages (lists of rows) from user_data
- paginate_users(page_size, offset, conn): fetch a single page (no looping here)

Constraints:
- Use yield
- Use only one loop (inside lazy_paginate)
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


def paginate_users(page_size: int, offset: int, conn: mysql.connector.MySQLConnection
                   ) -> List[Dict[str, object]]:
    """
    Fetch one page from user_data using LIMIT/OFFSET. No loops here.
    Returns a list of dict-rows; empty list means no more data.
    """
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT user_id, name, email, age FROM user_data ORDER BY name LIMIT %s OFFSET %s;",
            (page_size, offset),
        )
        rows = cur.fetchall()  # no explicit loops; DB driver does the paging
        return rows
    finally:
        cur.close()


def lazy_paginate(page_size: int) -> Generator[List[Dict[str, object]], None, None]:
    """
    Lazily yield pages (lists of rows) from user_data.
    Uses only ONE loop to advance offset and fetch the next page on demand.

    Prototype: def lazy_paginate(page_size)
    """
    if page_size is None or page_size < 1:
        raise ValueError("page_size must be a positive integer")

    conn = _connect_to_prodev()
    if conn is None:
        return

    try:
        offset = 0
        # SINGLE loop controlling pagination
        while True:
            page = paginate_users(page_size, offset, conn)
            if not page:
                break
            yield page
            offset += page_size
    finally:
        try:
            conn.close()
        except Exception:
            pass
