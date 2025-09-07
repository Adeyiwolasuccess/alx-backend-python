#!/usr/bin/python3
"""
1-batch_processing.py

Objective:
- stream_users_in_batches(batch_size): generator that yields rows from user_data
  in batches (memory-efficient).
- batch_processing(batch_size): generator that yields filtered batches
  (users with age > 25).

Constraints:
- Use Python generators (`yield`).
- Use no more than 3 loops total in this file.
    * We use:
        - 1 loop in stream_users_in_batches
        - 1 loop (plus one list-comprehension) in batch_processing
"""

import os
from typing import Dict, List, Generator, Optional
import mysql.connector


def _connect_to_prodev() -> Optional[mysql.connector.MySQLConnection]:
    """Connect to the ALX_prodev database using env vars or sensible defaults."""
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    try:
        return mysql.connector.connect(
            host=host, user=user, password=password, port=port, database="ALX_prodev"
        )
    except mysql.connector.Error as e:
        print(f"[MySQL Error] {_connect_to_prodev.__name__}: {e}")
        return None


def stream_users_in_batches(batch_size: int) -> Generator[List[Dict[str, object]], None, None]:
    """
    Yield rows from `user_data` in batches (lists of dicts), without loading everything into memory.

    Loops used: 1 (the `for` over iter(fetchmany,...))

    Args:
        batch_size: number of rows to fetch per batch (must be >= 1)
    Yields:
        List[Dict[str, object]] — each list is a batch of rows
    """
    if batch_size is None or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")

    conn = _connect_to_prodev()
    if conn is None:
        return

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id, name, email, age FROM user_data ORDER BY name;")

        # Single loop over fetchmany() batches; terminates when fetchmany returns []
        for batch in iter(lambda: cur.fetchmany(batch_size), []):
            yield batch

    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def batch_processing(batch_size: int) -> Generator[List[Dict[str, object]], None, None]:
    """
    Process each batch to filter users with age > 25, yielding the filtered batch.

    Loops used: 1 (for over batches) + 1 list-comprehension for filtering.

    Args:
        batch_size: number of rows to fetch per batch
    Yields:
        List[Dict[str, object]] — filtered batch (possibly empty)
    """
    for batch in stream_users_in_batches(batch_size):
        # list-comprehension counts as one additional loop (still within the 3-loop budget total)
        filtered = [
            row for row in batch
            if row.get("age") is not None and int(row["age"]) > 25
        ]
        yield filtered


if __name__ == "__main__":
    # Tiny demo: print sizes of first 2 filtered batches
    n = 0
    for fb in batch_processing(200):
        print(f"Filtered batch size: {len(fb)}")
        n += 1
        if n == 2:
            break
