#!/usr/bin/python3
"""
4-stream_ages.py

Objective:
- Use a generator to compute a memory-efficient aggregate (average age) from
  a large dataset without using SQL AVG.

Requirements met:
- stream_user_ages(): yields ages one by one (1 loop here)
- Another function computes the average by consuming the generator (1 loop here)
- Total loops in script: 2
- Prints: "Average age of users: <average>"
"""

import os
from typing import Generator, Optional
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


def stream_user_ages() -> Generator[int, None, None]:
    """
    Generator that yields user ages one by one from user_data.
    (Uses exactly ONE loop.)
    """
    conn = _connect_to_prodev()
    if conn is None:
        return
    cur = conn.cursor()  # tuple rows => age at index 0

    try:
        # Keep the query simple and explicit
        cur.execute("SELECT age FROM user_data;")
        for row in cur:  # single loop
            age = row[0]
            try:
                yield int(age)
            except Exception:
                # Skip rows with non-coercible ages (defensive)
                continue
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def average_age() -> float:
    """
    Consume stream_user_ages() to compute average without loading all rows.
    (Uses exactly ONE loop.)
    """
    total = 0
    count = 0
    for age in stream_user_ages():  # second (and last) loop
        total += age
        count += 1
    return (total / count) if count else 0.0


if __name__ == "__main__":
    avg = average_age()
    print(f"Average age of users: {avg}")
